from typing import Dict, Any, List, Optional
import os
import re
from app.core.logging import logger
from app.infrastructure.clients import get_service_registry
from app.services.ocr.ingress import mask_photo_pii


def to_khmer_numeral(n: int) -> str:
    """Convert integer to Khmer numeral string (e.g. 1 -> ១, 2 -> ២)."""
    khmer_digits = "០១២៣៤៥៦៧៨៩"
    return "".join(khmer_digits[int(d)] if d.isdigit() else d for d in str(n))


def clean_exercise_statement(text: str, question_no: Optional[str] = None) -> str:
    """
    Strips leading question number labels and markers from exercise text.
    E.g.:
    - '1. 4 + 5 + 6 =' -> '4 + 5 + 6 ='
    - '1) 4 + 5 + 6 =' -> '4 + 5 + 6 ='
    - 'Q1: 4 + 5 + 6 =' -> '4 + 5 + 6 ='
    - 'Question 1: What is 4 + 5?' -> 'What is 4 + 5?'
    - 'លំហាត់ទី ១: 4 + 5 + 6 =' -> '4 + 5 + 6 ='
    - '1. a) Label the diagram' -> 'Label the diagram'
    Preserves valid decimal numbers like '1.4 + 5.6 =' (where no space follows the dot).
    """
    if not text or not isinstance(text, str):
        return ""
    cleaned = text.strip()
    if not cleaned:
        return ""

    if question_no:
        q_clean = str(question_no).strip().lstrip("Qq").rstrip(".:- ")
        if q_clean:
            cleaned = re.sub(
                rf"^(?:(?:[Qq]uestion|[Ee]xercise|[Pp]roblem|[Qq]|លំហាត់ទី?|សំណួរ)?\s*{re.escape(q_clean)}\s*[\.\)\:\-\s]+)+",
                "",
                cleaned,
                flags=re.IGNORECASE
            ).strip()

    marker_pattern = re.compile(
        r"^\s*(?:"
        r"(?:[Qq]uestion|[Ee]xercise|[Ee]x|[Pp]roblem|[Qq]|លំហាត់ទី?|សំណួរ)\s*[\d១-៩]+[\.\)\:\-\s]*|"
        r"\(?[\d១-៩]+[\.\)]\s*\(?[a-zA-Z]\)?\s*|"
        r"\(?[\d១-៩]+\s*[a-zA-Z]?\)\s*|"
        r"\(?[a-zA-Z]\)\s*|"
        r"[\d១-៩]+\s*[\:\-]\s*(?=[a-zA-Z\u1780-\u17FF])|"
        r"[\d១-៩]+\.\s+"
        r")\s*",
        flags=re.IGNORECASE
    )

    prev = None
    while prev != cleaned:
        prev = cleaned
        cleaned = marker_pattern.sub("", cleaned).strip()

    return cleaned or text.strip()


class OCRExtractor:
    """
    Worksheet OCR & Vision Extractor.
    Communicates with the Homework Scanner microservice with graceful
    zero-model mock fallback for resilient offline testing and local development.
    All incoming images/PDFs undergo server-side photo PII masking of student
    name/header fields before dispatch.
    """

    def __init__(self):
        self._processor = None

    def _get_processor(self):
        if self._processor is None:
            from app.services.ocr.pipeline.processor import HomeworkProcessor
            self._processor = HomeworkProcessor()
        return self._processor

    async def _clean_exercises_with_llm(self, exercises: List[Dict[str, Any]]) -> None:
        """
        Cleans exercises using LLM to ensure question numbers (e.g. '1. 4 + 5 + 6 =')
        are cleanly stripped from the exercise prompt before putting it ready to use.
        If LLM is offline or in mock mode, regex cleaning ensures instant fallback.
        """
        if not exercises:
            return

        from app.services.llm import llm_service, ModelTier

        for ex in exercises:
            raw_prompt = ex.get("prompt", "")
            # Fast regex cleaning first
            cleaned_prompt = clean_exercise_statement(raw_prompt, ex.get("number"))
            ex["prompt"] = cleaned_prompt
            ex["title"] = clean_exercise_statement(ex.get("title", ""), ex.get("number"))

            # If the prompt still has ambiguous leading numbers before an operator (e.g. "1. 4 + 5 + 6 =")
            if re.match(r"^\s*[\d១-៩]+[\.\)\:\-]\s*", raw_prompt):
                try:
                    llm_prompt = (
                        "You are an educational document cleaner for elementary school worksheets.\n"
                        "Extract ONLY the clean math equation or problem question text to solve.\n"
                        "Completely remove any question number prefixes like '1.', 'Q1:', '1)', 'សំណួរ ១:'.\n"
                        "For example, '1. 4 + 5 + 6 =' becomes '4 + 5 + 6 ='.\n"
                        "Do NOT solve the problem. Return ONLY the clean problem text.\n\n"
                        f"Problem: {raw_prompt}\n"
                        "Clean Problem:"
                    )
                    resp = await llm_service.generate_text_async(llm_prompt, model_tier=ModelTier.FAST)
                    if resp and resp.text:
                        cleaned_llm = resp.text.strip().strip('"\'')
                        if (
                            cleaned_llm
                            and getattr(resp, "provider", "") != "mock"
                            and "mock" not in cleaned_llm.lower()
                            and len(cleaned_llm) < len(raw_prompt) + 10
                        ):
                            ex["prompt"] = clean_exercise_statement(cleaned_llm, ex.get("number"))
                except Exception as e:
                    logger.debug(f"[OCR] LLM exercise cleaning fallback: {e}")

    async def extract_from_bytes(
        self,
        file_bytes: bytes,
        filename: str = "worksheet.png",
    ) -> Dict[str, Any]:
        """
        Extract question text and structure from worksheet photo/PDF bytes.
        Applies server-side PII masking to blank out student name/ID in header
        before passing to vision models.
        Executes in-process as part of the backend layer with graceful fallback.
        """
        # Server-side photo PII masking: redacts student names/ID in worksheet header
        masked_bytes, mask_info = mask_photo_pii(file_bytes=file_bytes, filename=filename)

        # 1. In-process direct execution (Backend layer, zero external microservices needed)
        try:
            import asyncio
            proc = self._get_processor()
            result = await asyncio.to_thread(proc.process, file_bytes=masked_bytes, filename=filename)
            raw_dict = result.model_dump() if hasattr(result, "model_dump") else result.dict()
            parsed = self._parse_scanner_response(raw_dict, mask_info=mask_info)
            await self._clean_exercises_with_llm(parsed.get("exercises", []))
            return parsed
        except Exception as in_proc_err:
            logger.info(f"[OCR] In-process execution note: {in_proc_err}")

        # 2. Fallback to external microservice if configured
        try:
            registry = get_service_registry()
            client = registry.get("HOMEWORK_SCANNER")
            if client is not None:
                response = await client.process_homework(
                    file_bytes=masked_bytes,
                    filename=filename,
                )
                parsed = self._parse_scanner_response(response, mask_info=mask_info)
                await self._clean_exercises_with_llm(parsed.get("exercises", []))
                return parsed
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
                        q_no = q.get("question_no") or f"{ex_counter}"
                        prompt = q.get("prompt") or ""
                        inst = q.get("instructions") or ""
                        sub_qs = q.get("sub_questions", [])
                        raw_title = prompt if prompt else inst

                        clean_num = str(q_no).strip().lstrip("Qq").rstrip(".:- ")
                        clean_title = clean_exercise_statement(raw_title, clean_num)
                        formatted_no = f"Q{clean_num}" if clean_num else f"Q{ex_counter}"

                        display_title = clean_title if clean_title else f"Exercise {clean_num or ex_counter}"

                        if sub_qs:
                            sub_prompts = [
                                f"{sq.get('question_no')}) {clean_exercise_statement(sq.get('prompt') or '', sq.get('question_no'))}"
                                for sq in sub_qs
                            ]
                            # Clean prompt body has NO question number prefix so downstream LLM/solver isn't confused
                            full_p = f"{display_title}\n" + (f"{inst}\n" if inst and inst != display_title else "") + "\n".join(sub_prompts)
                            preview_text = f"{formatted_no}: {display_title} (" + ", ".join(sub_prompts[:2]) + ")"
                            scanned_display = f"{formatted_no}: {display_title}\n" + "\n".join(sub_prompts)
                        else:
                            elems = [e.get("text", "") for e in q.get("elements", []) if isinstance(e, dict) and e.get("text")]
                            elem_str = " ".join(elems) if elems else ""
                            # Pure clean problem statement without Q1: or 1.
                            full_p = display_title
                            if inst and inst != display_title:
                                full_p += f"\n{inst}"
                            if elem_str:
                                full_p += f"\n{elem_str}"
                            preview_text = f"{formatted_no}: {display_title}" + (f": {elem_str[:60]}" if elem_str else "")
                            scanned_display = f"{formatted_no}: {display_title} {elem_str}".strip()

                        ex_id = f"ex_{ex_counter}"
                        exercises.append({
                            "exercise_id": ex_id,
                            "problem_index": ex_counter,
                            "tab_label": f"Scanned Problem {ex_counter}",
                            "tab_label_khmer": f"លំហាត់ទី {to_khmer_numeral(ex_counter)}",
                            "number": formatted_no,
                            "title": display_title,
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
                            "prompt": clean_exercise_statement(prompt, q_no),
                            "confidence": q.get("confidence", 0.9),
                            "answer_areas": q.get("answer_areas", []),
                        })

        if extracted_questions:
            clean_text = "\n".join(
                f"{q['question_no'] + '. ' if q['question_no'] else ''}{clean_exercise_statement(q['prompt'], q['question_no'])}"
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
