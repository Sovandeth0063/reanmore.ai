from typing import Dict, Any, List, Optional
import os
from app.core.logging import logger
from app.infrastructure.clients import get_service_registry


def to_khmer_numeral(n: int) -> str:
    """Convert integer to Khmer numeral string (e.g. 1 -> ១, 2 -> ២)."""
    khmer_digits = "០១២៣៤៥៦៧៨៩"
    return "".join(khmer_digits[int(d)] if d.isdigit() else d for d in str(n))


class OCRExtractor:
    """
    Worksheet OCR & Vision Extractor.
    Communicates with the Homework Scanner microservice with graceful
    zero-model mock fallback for resilient offline testing and local development.
    """

    def __init__(self):
        pass

    async def extract_from_bytes(
        self,
        file_bytes: bytes,
        filename: str = "worksheet.png",
        force_mock: bool = False,
    ) -> Dict[str, Any]:
        """
        Extract question text and structure from worksheet photo/PDF bytes.
        """
        if not force_mock:
            try:
                registry = get_service_registry()
                client = registry.get("HOMEWORK_SCANNER")
                if client is not None:
                    response = await client.process_homework(
                        file_bytes=file_bytes,
                        filename=filename,
                    )
                    return self._parse_scanner_response(response)
            except Exception as e:
                logger.warning(
                    f"Homework scanner service unavailable or failed ({e}). "
                    "Engaging zero-model fallback extraction."
                )

        return self._generate_mock_extraction(filename)

    def _parse_scanner_response(self, raw: Dict[str, Any]) -> Dict[str, Any]:
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
        }

    def _generate_mock_extraction(self, filename: str = "practice_worksheet.png") -> Dict[str, Any]:
        """Deterministic zero-model simulated fallback for fast development and testing."""
        lower_name = (filename or "practice_worksheet.png").lower()
        is_single_specific = any(k in lower_name for k in ["single", "cookie", "fraction", "sunlight", "melt_ice", "math", "science"])
        if not is_single_specific:
            # Simulate a multi-exercise worksheet (Q5 Adjusting Tens, Q6 Counting Money, Q7 Multiplication)
            exercises = [
                {
                    "exercise_id": "ex_1",
                    "problem_index": 1,
                    "tab_label": "Scanned Problem 1",
                    "tab_label_khmer": "លំហាត់ទី ១",
                    "number": "Q5",
                    "title": "Adjusting Tens",
                    "instructions": "Solve by adding/subtracting tens first and adjusting",
                    "scanned_text": "1. 35 + 9 = ___\n2. 58 + 11 = ___",
                    "prompt": "Solve by adding/subtracting tens first and adjusting: a) 35 + 9 = ___  b) 58 + 11 = ___",
                    "preview": "Adjusting Tens: a) 35 + 9 = ___, b) 58 + 11 = ___",
                    "sub_questions": [
                        {
                            "question_no": "a",
                            "type": "fill_blank",
                            "prompt": "35 + 9 = ___",
                            "answer": "44",
                            "expected_answer": "44",
                            "hint": "35 + 10 = 45, then 45 - 1 = 44",
                            "answer_areas": []
                        },
                        {
                            "question_no": "b",
                            "type": "fill_blank",
                            "prompt": "58 + 11 = ___",
                            "answer": "69",
                            "expected_answer": "69",
                            "hint": "58 + 10 = 68, then 68 + 1 = 69",
                            "answer_areas": []
                        },
                    ],
                    "confidence": 0.98,
                },
                {
                    "exercise_id": "ex_2",
                    "problem_index": 2,
                    "tab_label": "Scanned Problem 2",
                    "tab_label_khmer": "លំហាត់ទី ២",
                    "number": "Q6",
                    "title": "Counting Money & Division",
                    "instructions": "Calculate coin amounts and divisions",
                    "scanned_text": "1. What is the total value of eight 10p coins?\n2. How many 5p coins make 45p? (45 ÷ 5)",
                    "prompt": "a) What is the total value of eight 10p coins? b) How many 5p coins make 45p? (45 ÷ 5)",
                    "preview": "Counting Money & Division: Eight 10p coins, 5p coins in 45p",
                    "sub_questions": [
                        {
                            "question_no": "a",
                            "type": "fill_blank",
                            "prompt": "What is the total value of eight 10p coins?",
                            "answer": "80",
                            "expected_answer": "80",
                            "hint": "8 × 10 = 80",
                            "answer_areas": []
                        },
                        {
                            "question_no": "b",
                            "type": "fill_blank",
                            "prompt": "How many 5p coins make 45p? (45 ÷ 5)",
                            "answer": "9",
                            "expected_answer": "9",
                            "hint": "45 ÷ 5 = 9",
                            "answer_areas": []
                        },
                    ],
                    "confidence": 0.95,
                },
                {
                    "exercise_id": "ex_3",
                    "problem_index": 3,
                    "tab_label": "Scanned Problem 3",
                    "tab_label_khmer": "លំហាត់ទី ៣",
                    "number": "Q7",
                    "title": "Multiplication & Doubling",
                    "instructions": "Double each number to find the answer",
                    "scanned_text": "Double 24 = ___, Double 35 = ___",
                    "prompt": "Double 24 = ___, Double 35 = ___",
                    "preview": "Multiplication & Doubling: Double 24, Double 35",
                    "sub_questions": [
                        {
                            "question_no": "a",
                            "type": "fill_blank",
                            "prompt": "Double 24 = ___",
                            "answer": "48",
                            "expected_answer": "48",
                            "hint": "24 + 24 = 48",
                            "answer_areas": []
                        },
                        {
                            "question_no": "b",
                            "type": "fill_blank",
                            "prompt": "Double 35 = ___",
                            "answer": "70",
                            "expected_answer": "70",
                            "hint": "35 + 35 = 70",
                            "answer_areas": []
                        },
                    ],
                    "confidence": 0.93,
                },
            ]
            questions = [
                {"question_no": "5a", "type": "fill_blank", "prompt": "35 + 9 = ___", "confidence": 0.98, "answer_areas": []},
                {"question_no": "5b", "type": "fill_blank", "prompt": "58 + 11 = ___", "confidence": 0.98, "answer_areas": []},
                {"question_no": "6a", "type": "fill_blank", "prompt": "What is the total value of eight 10p coins?", "confidence": 0.95, "answer_areas": []},
                {"question_no": "6b", "type": "fill_blank", "prompt": "How many 5p coins make 45p? (45 ÷ 5)", "confidence": 0.95, "answer_areas": []},
            ]
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
                "default_selected_id": "ex_1",
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
            return {
                "success": True,
                "source": "zero_model_fallback",
                "clean_question_text": "Q5. Adjusting Tens: 35 + 9, 58 + 11\nQ6. Counting Money: 10p coins, 45 ÷ 5\nQ7. Multiplication & Doubling",
                "multiple_exercises": True,
                "exercise_count": len(exercises),
                "prompt_message": f"I found {len(exercises)} exercises on your worksheet! Which one would you like to solve first?",
                "ui_layout": ui_layout,
                "exercises": exercises,
                "questions": questions,
                "document_meta": {
                    "title": filename,
                    "language": ["English"],
                    "subject": "math",
                },
                "overall_confidence": 0.96,
                "warnings": ["Simulated multi-exercise fallback mode active."],
                "raw_payload": {},
            }

        # Single problem fallback
        if "science" in lower_name:
            question_text = "What happens to ice when it is left under warm sunlight?"
            subject = "science"
        elif "fraction" in lower_name:
            question_text = "What is 1/2 plus 1/4?"
            subject = "math"
        elif "cookie" in lower_name or "math" in lower_name:
            question_text = "Leo had 8 cookies and gave away 3 cookies to Sarah. How many cookies does Leo have left?"
            subject = "math"
        else:
            question_text = "Solve the problem shown on the worksheet: What is 5 + 3?"
            subject = "math"

        single_ex = {
            "exercise_id": "ex_1",
            "problem_index": 1,
            "tab_label": "Scanned Problem 1",
            "tab_label_khmer": "លំហាត់ទី ១",
            "number": "1",
            "title": "Exercise 1",
            "instructions": None,
            "scanned_text": question_text,
            "prompt": question_text,
            "preview": question_text[:80],
            "sub_questions": [],
            "confidence": 0.99,
        }
        ui_layout = {
            "header_title": "ស្កែនលំហាត់ (OCR + VLM)",
            "header_title_en": "Scan Homework (OCR + VLM)",
            "back_button_text": "ត្រឡប់",
            "back_button_text_en": "Back",
            "mascot_message": "ខ្ញុំឃើញលំហាត់របស់អ្នកហើយ! តោះដោះស្រាយវាជាមួយគ្នា!",
            "mascot_message_en": "I found your exercise! Let's solve it together!",
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
            "default_selected_id": "ex_1",
            "options": [
                {
                    "id": "ex_1",
                    "problem_index": 1,
                    "tab_label": "Scanned Problem 1",
                    "tab_label_khmer": "លំហាត់ទី ១",
                    "title": "Exercise 1",
                    "scanned_text": question_text,
                    "prompt": question_text,
                    "is_selected_default": True,
                }
            ]
        }

        return {
            "success": True,
            "source": "zero_model_fallback",
            "clean_question_text": question_text,
            "multiple_exercises": False,
            "exercise_count": 1,
            "prompt_message": "I found 1 exercise on your worksheet. Let's solve it together!",
            "ui_layout": ui_layout,
            "exercises": [single_ex],
            "questions": [
                {
                    "question_no": "1",
                    "type": "fill_blank",
                    "prompt": question_text,
                    "confidence": 0.99,
                    "answer_areas": [],
                }
            ],
            "document_meta": {
                "title": filename,
                "language": ["English"],
                "subject": subject,
            },
            "overall_confidence": 0.99,
            "warnings": ["Simulated fallback OCR mode active."],
            "raw_payload": {},
        }


ocr_extractor = OCRExtractor()
