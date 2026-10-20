from typing import Dict, Any, List, Optional
import os
from app.core.logging import logger
from app.infrastructure.clients import get_service_registry
from app.services.ocr.ingress import mask_photo_pii


def to_khmer_numeral(n: int) -> str:
    """Convert integer to Khmer numeral string (e.g. 1 -> ១, 2 -> ២)."""
    khmer_digits = "០១២៣៤៥៦៧៨៩"
    return "".join(khmer_digits[int(d)] if d.isdigit() else d for d in str(n))


class OCRExtractor:
    """
    Worksheet OCR & Vision Extractor.
    Communicates with the Homework Scanner microservice with graceful
    zero-model mock fallback for resilient offline testing and local development.
    All incoming images/PDFs undergo server-side photo PII masking of student
    name/header fields before dispatch.
    """

    def __init__(self):
        pass

    async def extract_from_bytes(
        self,
        file_bytes: bytes,
        filename: str = "worksheet.png",
    ) -> Dict[str, Any]:
        """
        Extract question text and structure from worksheet photo/PDF bytes.
        Applies server-side PII masking to blank out student name/ID in header
        before passing to vision models.
        Returns structured degraded response if scanner is offline or unavailable.
        """
        # Server-side photo PII masking: redacts student names/ID in worksheet header
        masked_bytes, mask_info = mask_photo_pii(file_bytes=file_bytes, filename=filename)

        try:
            registry = get_service_registry()
            client = registry.get("HOMEWORK_SCANNER")
            if client is not None:
                response = await client.process_homework(
                    file_bytes=masked_bytes,
                    filename=filename,
                )
                return self._parse_scanner_response(response, mask_info=mask_info)
        except Exception as e:
            logger.warning(
                f"Homework scanner service unavailable or failed ({e}). "
                "Returning honest degraded response."
            )

        return self._generate_degraded_response(
            error="Worksheet scanner is temporarily unavailable. Please type your problem into the chat.",
            mask_info=mask_info,
        )

    def _generate_degraded_response(
        self, error: str, mask_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Structured honest degraded response when OCR dependencies fail."""
        m_info = mask_info or {}
        return {
            "success": False,
            "source": "homework_scanner",
            "error": error,
            "clean_question_text": "",
            "multiple_exercises": False,
            "exercise_count": 0,
            "prompt_message": error,
            "ui_layout": {"style": "banner", "items": []},
            "exercises": [],
            "questions": [],
            "document_meta": {},
            "overall_confidence": 0.0,
            "warnings": [error],
            "raw_payload": {},
            "pii_masked": m_info.get("masked", False),
            "mask_info": m_info,
        }

    def _parse_scanner_response(
        self, raw: Dict[str, Any], mask_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Parse structured HomeworkResponse into clean question text, metadata, and selectable exercises."""
        pages = raw.get("pages", [])
        extracted_questions: List[Dict[str, Any]] = []
        exercises: List[Dict[str, Any]] = []
        ex_counter = 1

        for page in pages:
            for section in page.get("sections", []):
                sec_id = section.get("section_id") or ""
                sec_title = section.get("title") or ""
                sec_instructions = section.get("instructions") or ""
                sec_questions = section.get("questions", [])

                is_subparts_only = all(
                    str(q.get("question_no", "")).strip().lower() in ("a", "b", "c", "d", "e", "f")
                    and len(q.get("sub_questions", [])) == 0
                    for q in sec_questions
                ) and bool(sec_title) and not ("section" in str(sec_id).lower() or "mathematics" in str(sec_title).lower())

                if is_subparts_only and len(sec_questions) > 1:
                    sub_prompts = []
                    sub_q_list = []
                    for q in sec_questions:
                        p = q.get("prompt") or ""
                        q_no = q.get("question_no") or ""
                        sub_prompts.append(f"{q_no + ') ' if q_no else ''}{p}")
                        sub_q_list.append({
                            "question_no": q_no,
                            "type": q.get("type", "fill_blank"),
                            "prompt": p,
                            "answer_areas": q.get("answer_areas", []),
                        })

                    full_prompt = f"{sec_title}: {sec_instructions}\n" if sec_instructions else f"{sec_title}\n"
                    full_prompt += "\n".join(sub_prompts)

                    ex_id = f"ex_{ex_counter}"
                    scanned_display = "\n".join(sub_prompts) if sub_prompts else (sec_instructions or sec_title)
                    exercises.append({
                        "exercise_id": ex_id,
                        "problem_index": ex_counter,
                        "tab_label": f"Scanned Problem {ex_counter}",
                        "tab_label_khmer": f"លំហាត់ទី {to_khmer_numeral(ex_counter)}",
                        "number": sec_id or f"Q{ex_counter}",
                        "title": sec_title,
                        "instructions": sec_instructions,
                        "scanned_text": scanned_display,
                        "prompt": full_prompt.strip(),
                        "preview": (sec_title + " (" + ", ".join(sub_prompts[:2]) + ")")[:120],
                        "sub_questions": sub_q_list,
                        "confidence": section.get("confidence", 0.9),
                    })
                    ex_counter += 1
                else:
                    for q in sec_questions:
                        q_no = q.get("question_no") or f"Q{ex_counter}"
                        prompt = q.get("prompt") or ""
                        inst = q.get("instructions") or ""
                        sub_qs = q.get("sub_questions", [])
                        title = prompt if prompt else inst

                        if sub_qs:
                            sub_prompts = [f"{sq.get('question_no')}) {sq.get('prompt')}" for sq in sub_qs]
                            full_p = f"**{q_no}. {title}**\n" + (f"* {inst}\n" if inst else "") + "\n".join([f"* {sp}" for sp in sub_prompts])
                            preview_text = f"{q_no}. {title} (" + ", ".join(sub_prompts[:2]) + ")"
                            scanned_display = f"{q_no}. {title}\n" + "\n".join(sub_prompts)
                        else:
                            elems = [e.get("text", "") for e in q.get("elements", []) if isinstance(e, dict) and e.get("text")]
                            elem_str = " ".join(elems) if elems else ""
                            full_p = f"**{q_no}. {title}**\n" + (f"* {inst}\n" if inst else "") + elem_str
                            preview_text = f"{q_no}. {title}" + (f": {elem_str[:60]}" if elem_str else "")
                            scanned_display = f"{q_no}. {title} {elem_str}".strip()

                        ex_id = f"ex_{ex_counter}"
                        exercises.append({
                            "exercise_id": ex_id,
                            "problem_index": ex_counter,
                            "tab_label": f"Scanned Problem {ex_counter}",
                            "tab_label_khmer": f"លំហាត់ទី {to_khmer_numeral(ex_counter)}",
                            "number": q_no,
                            "title": title,
                            "instructions": inst,
                            "scanned_text": scanned_display,
                            "prompt": full_p.strip(),
                            "preview": preview_text[:120],
                            "sub_questions": sub_qs,
                            "confidence": q.get("confidence", 0.9),
                        })
                        ex_counter += 1

                for q in sec_questions:
                    prompt = q.get("prompt") or ""
                    q_no = q.get("question_no") or ""
                    q_type = q.get("type") or "question"
                    if prompt:
                        extracted_questions.append({
                            "question_no": q_no,
                            "type": q_type,
                            "prompt": prompt,
                            "confidence": q.get("confidence", 0.9),
                            "answer_areas": q.get("answer_areas", []),
                        })

        if extracted_questions:
            clean_text = "\n".join(
                f"{q['question_no'] + '. ' if q['question_no'] else ''}{q['prompt']}"
                for q in extracted_questions
            )
        else:
            clean_text = "Worksheet image processed, but no distinct question text detected."

        has_multiple = len(exercises) > 1
        if has_multiple:
            prompt_message = (
                f"I found {len(exercises)} exercises on your worksheet! "
                "Which one would you like to solve first?"
            )
        elif len(exercises) == 1:
            prompt_message = "I found 1 exercise on your worksheet. Let's solve it together!"
        else:
            prompt_message = "Worksheet image processed, but no distinct exercises were detected."

        ui_layout = {
            "header_title": "ស្កែនលំហាត់ (OCR + VLM)",
            "header_title_en": "Scan Homework (OCR + VLM)",
            "back_button_text": "ត្រឡប់",
            "back_button_text_en": "Back",
            "mascot_message": "ខ្ញុំឃើញលំហាត់របស់អ្នកហើយ! តោះដោះស្រាយវាជាមួយគ្នា!",
            "mascot_message_en": "I found your exercises! Let's solve them together!",
            "selector_title": "សំណួរដែលរកឃើញ (ជ្រើសរើសមួយ):",
            "selector_title_en": "Questions found (select one):",
            "scanned_box_label": "សំណួរដែលស្កេនបាន:",
            "scanned_box_label_en": "Scanned question:",
            "confirm_question": "តើសំណួរនេះត្រឹមត្រូវទេ?",
            "confirm_question_en": "Is this question correct?",
            "buttons": {
                "retake": {
                    "label": "ថតឡើងវិញ",
                    "label_en": "Retake",
                    "icon": "🔄"
                },
                "start": {
                    "label": "តោះចាប់ផ្តើម!",
                    "label_en": "Let's Start!",
                    "icon": "✔"
                }
            },
            "default_selected_id": exercises[0]["exercise_id"] if exercises else None,
            "options": [
                {
                    "id": ex["exercise_id"],
                    "problem_index": ex["problem_index"],
                    "tab_label": ex["tab_label"],
                    "tab_label_khmer": ex["tab_label_khmer"],
                    "title": ex["title"],
                    "scanned_text": ex["scanned_text"],
                    "prompt": ex["prompt"],
                    "is_selected_default": (i == 0)
                }
                for i, ex in enumerate(exercises)
            ]
        }

        doc = raw.get("document", {})
        m_info = mask_info or {}
        return {
            "success": True,
            "source": "homework_scanner",
            "clean_question_text": clean_text.strip(),
            "multiple_exercises": has_multiple,
            "exercise_count": len(exercises),
            "prompt_message": prompt_message,
            "ui_layout": ui_layout,
            "exercises": exercises,
            "questions": extracted_questions,
            "document_meta": doc,
            "overall_confidence": raw.get("confidence", 0.9),
            "warnings": raw.get("warnings", []),
            "raw_payload": raw,
            "pii_masked": m_info.get("masked", False),
            "mask_info": m_info,
        }



ocr_extractor = OCRExtractor()
