"""
File: orchestrator/app/services/socratic/graph.py
Description: LangGraph StateGraph orchestration pipeline for the Socratic elementary tutoring workflow.
             Handles intent routing, problem decomposition, step validation, 3-tier progressive hints,
             and dual-payload (JSON widget + Markdown) response compilation.
"""

import logging
import re
import json
from typing import Dict, Any, Optional, List, Tuple
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.services.socratic.card_schema import SocraticStep, StepWidgetPayload, SocraticResponse
from app.services.socratic.state import TutorState
from app.services.socratic.hint_engine import HintEngine
from app.services.socratic.clarify import SocraticClarifier
from app.services.socratic.prompts.controller import SocraticPromptController
from app.services.guardrails.safety_filter import SafetyFilter
from app.services.guardrails.educational_scope import EducationalScopeDeflector
from app.services.nlu.schema import StudentIntent

logger = logging.getLogger("orchestrator.socratic.graph")

hint_engine = HintEngine()
clarifier = SocraticClarifier()
controller = SocraticPromptController()
safety_filter = SafetyFilter()
scope_deflector = EducationalScopeDeflector()


# -------------------------------------------------------------------------
# Helper Functions & State Serializers
# -------------------------------------------------------------------------

def _get_widget_from_state(state: TutorState) -> Optional[StepWidgetPayload]:
    widget_dict = state.get("step_widget")
    if widget_dict:
        try:
            return StepWidgetPayload.model_validate(widget_dict)
        except Exception as e:
            logger.warning(f"Failed to validate StepWidgetPayload from state: {e}")
    return None


def _is_answer_equivalent(student_attempt: str, expected_answer: str) -> bool:
    """
    Elementary answer equivalence checker supporting numbers, fractions, word names,
    unit stripping, science conceptual synonyms, and Khmer-English cross-language equivalence.
    """
    if not student_attempt or not expected_answer:
        return False

    # Khmer digit conversion map
    khmer_digits = str.maketrans("០១២៣៤៥៦៧៨៩", "0123456789")

    s_clean = student_attempt.strip().lower().translate(khmer_digits)
    e_clean = expected_answer.strip().lower().translate(khmer_digits)

    # 1. Exact match
    if s_clean == e_clean:
        return True

    # 2. Khmer & English Affirmative / Negative Cross-Language Matching
    affirmative_synonyms = {
        "yes", "true", "correct", "y", "t", "has",
        "បាទ", "ចាស", "មាន", "ពិតជាមាន", "ត្រូវ", "ពិតមែន", "បាទ/ចាស", "បាទមាន", "ចាសមាន", "ពិត"
    }
    negative_synonyms = {
        "no", "false", "incorrect", "n", "f", "none", "does not", "doesn't",
        "ទេ", "គ្មាន", "មិនមាន", "អត់", "ខុស", "មិនពិត", "អត់ទេ", "អត់មាន", "មិនមែន"
    }

    if any(s_clean == word or s_clean.startswith(word) for word in affirmative_synonyms) and any(e_clean == word or e_clean.startswith(word) for word in affirmative_synonyms):
        return True

    if any(s_clean == word or s_clean.startswith(word) for word in negative_synonyms) and any(e_clean == word or e_clean.startswith(word) for word in negative_synonyms):
        return True

    # 3. Khmer Multiple Choice Letters (ក -> a, ខ -> b, គ -> c, ឃ -> d)
    khmer_letter_map = {"ក": "a", "ខ": "b", "គ": "c", "ឃ": "d"}
    s_mapped = khmer_letter_map.get(s_clean, s_clean)
    e_mapped = khmer_letter_map.get(e_clean, e_clean)
    if s_mapped == e_mapped:
        return True

    # 4. Bounded full-word keyword match in expected (avoiding sub-word substrings like "is" in "photosynthesis")
    import re
    common_stopwords = {"the", "a", "an", "is", "it", "to", "of", "and", "in", "by", "for", "that", "its", "into", "on", "at", "no", "yes"}
    if len(s_clean) >= 3 and s_clean not in common_stopwords:
        if re.search(rf'\b{re.escape(s_clean)}\b', e_clean):
            return True

    from typing import Optional

    word_to_num = {
        "zero": 0.0, "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0,
        "five": 5.0, "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0,
        "ten": 10.0, "eleven": 11.0, "twelve": 12.0, "half": 0.5,
        "one half": 0.5, "quarter": 0.25, "one quarter": 0.25, "three quarters": 0.75,
        "សូន្យ": 0.0, "មួយ": 1.0, "ពីរ": 2.0, "បី": 3.0, "បួន": 4.0,
        "ប្រាំ": 5.0, "ប្រាំមួយ": 6.0, "ប្រាំពីរ": 7.0, "ប្រាំបី": 8.0, "ប្រាំបួន": 9.0, "ដប់": 10.0
    }

    def parse_val(t: str) -> Optional[float]:
        t = t.strip()
        if t in word_to_num:
            return word_to_num[t]
        t = re.sub(r'^(about|approx|around|=|\s)+', '', t)
        t = re.sub(r'\s*(cookies|apples|candies|cm|m|km|kg|g|dollars|\$|units|hours|mins|seconds).*$', '', t).strip()
        if "/" in t:
            parts = t.split("/")
            if len(parts) == 2:
                try:
                    num = float(parts[0].strip())
                    denom = float(parts[1].strip())
                    if denom != 0:
                        return num / denom
                except Exception:
                    pass
        nums = re.findall(r"[-+]?\d*\.?\d+", t)
        if nums:
            try:
                return float(nums[0])
            except Exception:
                pass
        return None

    s_num = parse_val(s_clean)
    e_num = parse_val(e_clean)
    if s_num is not None and e_num is not None:
        if abs(s_num - e_num) < 0.01:
            return True

    # 5. Science Conceptual Synonyms (Bilingual English & Khmer)
    synonyms = [
        {"evaporation", "evaporate", "evaporates", "vaporization", "liquid to gas", "steam", "liquid turns into gas", "រំហួត", "រំហួតទឹក", "ក្លាយជាចំហាយ"},
        {"condensation", "condense", "condenses", "gas to liquid", "water droplets", "កំណក", "កំណកទឹក"},
        {"photosynthesis", "sunlight and water", "making food", "glucose", "plants make food", "រស្មីសំយោគ", "បង្កើតអាហារ"},
        {"gravity", "gravitational force", "pull of earth", "pulls down", "gravity pulls it down", "ទំនាញផែនដី", "កម្លាំងទំនាញ"},
        {"mitochondria", "powerhouse of the cell", "cellular energy", "atp", "powerhouse"},
        {"backbone", "vertebrate", "vertebrates", "has backbone", "ឆ្អឹងកង", "ឆ្អឹងខ្នង", "សត្វមានឆ្អឹងកង"},
        {"invertebrate", "invertebrates", "no backbone", "without backbone", "ឥតឆ្អឹងកង", "សត្វឥតឆ្អឹងកង", "គ្មានឆ្អឹងខ្នង"},
        {"feathers", "feather", "រោម", "រោមស្លាប"},
        {"wings", "wing", "ស្លាប"},
        {"pincers", "pincer", "claws", "claw", "ដង្កៀប", "ក្រញ៉ាំ"},
        {"hump", "hump on back", "បូក", "បូកនៅលើខ្នង", "បូកខ្នង"},
        {"producer", "producers", "makes own food", "អ្នកផលិត", "រុក្ខជាតិ"},
        {"consumer", "consumers", "eats others", "អ្នកស៊ី", "អ្នកប្រើប្រាស់", "សត្វ"},
        {"herbivore", "plant eater", "eats plants", "អ្នកស៊ីរុក្ខជាតិ", "សត្វស៊ីរុក្ខជាតិ"},
        {"carnivore", "predator", "meat eater", "eats meat", "eats animals", "អ្នកស៊ីសាច់", "សត្វស៊ីសាច់"},
        {"leaves", "leaf", "plant leaves", "ស្លឹក", "ស្លឹកឈើ", "ផ្នែកស្លឹក"},
        {"rabbit", "ទន្សាយ"},
        {"cabbage", "ស្ពៃ", "ស្ពៃក្តោប"},
        {"owl", "owl and eagle", "eagle", "b and d", "b, d", "b and c", "b, c", "សត្វទីទុយ", "ឥន្ទ្រី"}
    ]
    for syn_group in synonyms:
        if any(s in s_clean for s in syn_group) and any(e in e_clean for e in syn_group):
            return True

    return False


# -------------------------------------------------------------------------
# LangGraph Nodes
# -------------------------------------------------------------------------

def process_nlu_node(state: TutorState) -> Dict[str, Any]:
    """
    Resolves student intent if not already provided.
    """
    raw_input = state.get("raw_user_input", state.get("student_attempt", "")).strip()
    intent = state.get("detected_intent")

    if not intent:
        lower = raw_input.lower()
        widget = _get_widget_from_state(state)

        from app.services.nlu.intent import classify_intent_heuristic, IntentType
        heur = classify_intent_heuristic(raw_input)

        if heur.intent == IntentType.CHITCHAT:
            intent = "CHITCHAT"
        elif heur.intent == IntentType.OFF_TOPIC:
            intent = "OFF_TOPIC_DEFLECTED"
        elif any(h in lower for h in ["hint", "clue", "help", "i'm stuck", "stuck", "don't know", "dont know"]):
            intent = StudentIntent.REQUEST_HINT.value
        elif lower.startswith("goto") or lower.startswith("jump") or lower.startswith("step"):
            intent = "NAVIGATION_JUMP"
        elif widget and widget.get_active_step() is not None and (0 < len(raw_input) <= 40):
            intent = StudentIntent.STEP_ANSWER_ATTEMPT.value
        elif not widget or state.get("problem_text") is None or "problem" in lower or len(raw_input) > 40:
            intent = StudentIntent.INITIAL_QUESTION.value
        else:
            intent = StudentIntent.STEP_ANSWER_ATTEMPT.value

    subject = state.get("subject")
    subtopic = state.get("subtopic")
    if not subject:
        from app.services.nlu.router import route_subject_heuristic
        route_res = route_subject_heuristic(raw_input)
        subject = route_res.subject.value
        subtopic = route_res.subtopic

    return {
        "raw_user_input": raw_input,
        "student_attempt": raw_input,
        "detected_intent": intent,
        "subject": subject,
        "subtopic": subtopic
    }


def synthesize_visual_data_for_step(problem_text: str, step_dict: Dict[str, Any], subject: str = "math") -> Optional[Dict[str, Any]]:
    """
    Intelligently determines and constructs structured visual data for a step,
    adhering to the strict rule: NO ANSWER LEAK THROUGH VISUALS.
    Reuses existing frontend VisualWidget types.
    """
    p_lower = (problem_text or "").lower()
    q_lower = (step_dict.get("your_turn") or step_dict.get("mission") or "").lower()
    combined = f"{p_lower} {q_lower}"

    import re
    nums = [int(n) for n in re.findall(r"\b\d+\b", p_lower)]

    # 1. Number Line for Adding/Subtracting or Missing Addends on number line (<= 120)
    if any(k in combined for k in ["+", "plus", "add", "count", "missing", "reach", "jump", "number line", "distance", "___", "["]) and len(nums) >= 2:
        start_val = nums[0]
        jump_val = nums[1]
        if start_val + jump_val <= 120 and (start_val >= 20 or jump_val >= 10 or "reach" in combined or "missing" in combined or "number line" in combined):
            return {
                "type": "number_line",
                "start": start_val,
                "target": start_val + jump_val,
                "frontend_action": "hide_distance",
                "purpose": "help_student_visualize_movement_on_number_line"
            }

    # 2. Object Groups for multi-addition or counting small objects (e.g. 4 + 5 + 6 or 7 + 3 + 2 + 5)
    if any(k in combined for k in ["+", "plus", "add", "combine", "total", "altogether", "apples", "cookies", "stars"]) and len(nums) >= 2:
        if all(1 <= n <= 30 for n in nums[:4]):
            return {
                "type": "objects",
                "groups": nums[:4],
                "purpose": "show_separate_groups_without_revealing_sum"
            }

    # 3. Place Value Blocks (e.g. 146, hundreds, tens, ones)
    if any(k in combined for k in ["place value", "hundreds", "tens", "ones", "digits", "decompose"]) and len(nums) >= 1:
        target_num = nums[0] if nums[0] >= 10 else (nums[1] if len(nums) > 1 else 10)
        return {
            "type": "place_value_blocks",
            "number": target_num,
            "purpose": "scaffold_base_10_decomposition"
        }

    # 4. Animal features & classification
    if any(k in combined for k in ["flamingo", "bird", "feathers", "wings", "beak"]):
        return {
            "type": "animal_feature_card",
            "animal": "ហ្វ្លាមីងហ្គោ (Flamingo)",
            "emoji": "🦩",
            "features": ["ឆ្អឹងកង (Vertebrate)", "រោមស្លាប (Feathers)", "ស្លាបហោះ (Wings)"]
        }
    if any(k in combined for k in ["lobster", "crab", "shell", "claws", "invertebrate"]):
        return {
            "type": "animal_feature_card",
            "animal": "បង្កង (Lobster)",
            "emoji": "🦞",
            "features": ["ឥតឆ្អឹងកង (Invertebrate)", "សំបករឹង (Hard Shell)", "ដង្កៀប (Claws)"]
        }
    if any(k in combined for k in ["camel", "hump", "desert"]):
        return {
            "type": "animal_feature_card",
            "animal": "អូដ្ឋ (Camel)",
            "emoji": "🐪",
            "features": ["ឆ្អឹងកង (Vertebrate)", "ពកខ្នង (Hump)", "រោមក្រាស់ (Fur)"]
        }
    if any(k in combined for k in ["vertebrate", "invertebrate", "backbone", "bones"]):
        return {
            "type": "classification_split",
            "purpose": "visualize_vertebrate_vs_invertebrate"
        }

    # 5. Photosynthesis / Plants
    if any(k in combined for k in ["plant", "leaf", "leaves", "photosynthesis", "roots", "stem", "sunlight"]):
        return {
            "type": "plant_diagram",
            "purpose": "show_plant_anatomy_and_photosynthesis"
        }

    # 6. Ecosystem / Food chain / Producer vs Consumer
    if any(k in combined for k in ["producer", "consumer", "herbivore", "carnivore", "food chain", "eats"]):
        if "chain" in combined or "arrow" in combined:
            return {
                "type": "food_chain",
                "hide_target_word": True,
                "purpose": "trace_energy_flow_in_ecosystem"
            }
        return {
            "type": "producer_consumer_sort",
            "items": ["ស្មៅ (Grass)", "ទន្សាយ (Rabbit)", "ដើមស្រូវ (Rice Plant)", "ឥន្ទ្រី (Eagle)"],
            "purpose": "sort_producers_and_consumers"
        }

    # 7. Electric Circuits
    if any(k in combined for k in ["circuit", "battery", "switch", "bulb", "electricity", "wire"]):
        return {
            "type": "circuit_simulator",
            "switch_closed": False,
            "purpose": "interactive_open_closed_circuit"
        }

    # 8. Balance scale for simple equations
    if ("=" in problem_text or "balance" in combined or "equal" in combined) and len(nums) >= 2:
        return {
            "type": "equation_balance",
            "left": nums[0],
            "right": nums[1] if len(nums) > 1 else nums[0],
            "purpose": "visualize_equality_balance"
        }

    return None


def initial_problem_node(state: TutorState) -> Dict[str, Any]:
    """
    Decomposes the homework problem into 2–4 Socratic step cards using the
    exercise_planning prompt (zero answer leakage, isomorphic parallel examples,
    3-tier progressive hints).  Falls back to the legacy two-step pipeline when
    the LLM is unavailable.
    """
    problem = state.get("problem_text") or state.get("raw_user_input", "Solve the homework problem.")
    grade_level = state.get("grade_level", "grade_1_3")
    session_id = state.get("session_id", "default_session")
    subject = (state.get("subject") or "math").upper()

    # PRIMARY PATH — unified exercise_planning prompt (full card + hints, no answer leakage)
    widget_dict = controller.plan_exercise_socratic_widget(
        problem_text=problem,
        grade_level=grade_level,
        session_id=session_id
    )
    if widget_dict and widget_dict.get("steps") and len(widget_dict["steps"]) >= 2:
        logger.info(f"exercise_planning produced {widget_dict['total_steps']}-step widget via LLM.")
        # Validate / coerce each step through SocraticStep to catch schema mismatches early
        try:
            coerced_steps = []
            for raw in widget_dict["steps"]:
                v_data = raw.get("visual_data") or raw.get("visual") or synthesize_visual_data_for_step(problem, raw, subject)
                coerced_steps.append(SocraticStep(
                    step_number=raw.get("step_number", 1),
                    title=raw.get("title", ""),
                    status=raw.get("status", "locked"),
                    mission=raw.get("mission", ""),
                    clue=raw.get("clue", ""),
                    helpful_example=raw.get("helpful_example", ""),
                    your_turn=raw.get("your_turn", ""),
                    expected_answer=raw.get("expected_answer", ""),
                    concept=raw.get("concept", ""),
                    hints=raw.get("hints", []),
                    current_hint_level=0,
                    visual_data=v_data
                ))
            first_v_data = coerced_steps[0].visual_data if coerced_steps else None
            widget = StepWidgetPayload(
                total_steps=len(coerced_steps),
                current_step_index=0,
                completed_steps=[],
                visual_data=widget_dict.get("visual_data") or first_v_data,
                steps=coerced_steps
            )
            return {
                "problem_text": problem,
                "total_steps_count": len(coerced_steps),
                "step_widget": widget.model_dump(),
                "current_step_index": 0,
                "active_hint": None,
                "current_hint_tier": 0,
                "feedback_message": "🚀 Let's solve this together, step-by-step! Here is Step 1:",
                "is_problem_complete": False,
                "is_problem_solved": False,
                "clarification_needed": False
            }
        except Exception as coerce_err:
            logger.warning(f"SocraticStep coercion failed after exercise_planning: {coerce_err}. Falling back.")

    # 2b. FALLBACK PATH — two-step breakdown → generate_step_card pipeline
    logger.info("exercise_planning unavailable or returned invalid data; using legacy breakdown pipeline.")
    steps_data = controller.breakdown_problem_into_steps(problem, grade_level=grade_level)
    socratic_steps: List[SocraticStep] = []

    def _safe_str(val: Any) -> str:
        if isinstance(val, dict):
            return " ".join(f"{v}" for v in val.values() if v)
        elif isinstance(val, list):
            return " ".join(str(item) for item in val)
        return str(val) if val is not None else ""

    for idx, s in enumerate(steps_data):
        step_num = s.get("step_number", idx + 1)
        card_content = controller.generate_step_card(
            homework_problem=problem,
            step_number=step_num,
            total_steps=len(steps_data),
            step_title=s.get("title", f"Step {step_num}"),
            step_concept=s.get("concept", s.get("mission", "")),
            expected_operation=s.get("clue", ""),
            grade_level=grade_level
        )

        step_hints = card_content.get("hints")
        if not step_hints or len(step_hints) != 3:
            step_title_label = s.get("title", f"Step {step_num}")
            step_hints = [
                f"💡 Focus on the key idea in '{step_title_label}' and identify what the question is asking.",
                f"🍎 Picture the parallel example and apply the same operation step-by-step!",
                f"📐 Break the calculation into two smaller sub-steps without solving either yet."
            ]

        v_data = synthesize_visual_data_for_step(problem, s, subject)
        socratic_steps.append(SocraticStep(
            step_number=step_num,
            title=_safe_str(s.get("title", f"Step {step_num}")),
            status="in_progress" if idx == 0 else ("up_next" if idx == 1 else "locked"),
            mission=_safe_str(card_content.get("mission")),
            clue=_safe_str(card_content.get("clue")),
            helpful_example=_safe_str(card_content.get("helpful_example")),
            your_turn=_safe_str(card_content.get("your_turn")),
            expected_answer=s.get("expected_answer", str(step_num)),
            concept=s.get("concept", ""),
            hints=step_hints,
            current_hint_level=0,
            visual_data=v_data
        ))

    first_v_data = socratic_steps[0].visual_data if socratic_steps else None
    widget = StepWidgetPayload(
        total_steps=len(socratic_steps),
        current_step_index=0,
        completed_steps=[],
        visual_data=first_v_data,
        steps=socratic_steps
    )

    return {
        "problem_text": problem,
        "total_steps_count": len(socratic_steps),
        "step_widget": widget.model_dump(),
        "current_step_index": 0,
        "active_hint": None,
        "current_hint_tier": 0,
        "feedback_message": "🚀 Let's solve this together, step-by-step! Here is Step 1:",
        "is_problem_complete": False,
        "is_problem_solved": False,
        "clarification_needed": False
    }


def validate_attempt_node(state: TutorState) -> Dict[str, Any]:
    """
    Evaluates student answer against active step's expected target.
    Checks in-memory equivalence and queries downstream validator if needed.
    """
    widget = _get_widget_from_state(state)
    if not widget:
        return {"detected_intent": StudentIntent.INITIAL_QUESTION.value}

    active_step = widget.get_active_step()
    if not active_step:
        return {"is_problem_complete": True, "is_problem_solved": True}

    attempt = state.get("student_attempt", "").strip()
    expected = active_step.expected_answer or ""
    grade_level = state.get("grade_level", "grade_1_3")
    history = list(state.get("attempt_history", []))

    # 1. Fast path: in-memory rule-based equivalence
    is_correct = _is_answer_equivalent(attempt, expected)

    # 2. Downstream path: query microservice validator or LLM evaluator if heuristic is not yet matched
    if not is_correct and expected and attempt:
        try:
            from app.services.llm import llm_service, ModelTier
            sys_inst, eval_prompt = controller.get_answer_evaluation_prompt(
                step_question=active_step.question_en or active_step.mission or "",
                expected_answer=expected,
                student_attempt=attempt,
                grade_level=state.get("grade_level", "grade_1_3")
            )
            eval_res = llm_service.generate_text(
                prompt=eval_prompt,
                system_instruction=sys_inst,
                temperature=0.1,
                max_tokens=150,
                model_tier=ModelTier.FAST
            )
            if eval_res and eval_res.text:
                m = re.search(r'\{.*\}', eval_res.text, re.DOTALL)
                if m:
                    parsed_eval = json.loads(m.group(0))
                    if parsed_eval.get("is_correct") is True:
                        is_correct = True
        except Exception as e:
            logger.warning(f"LLM near-correct answer evaluation failed: {e}")

    if is_correct:
        # Praise feedback
        feedback = f"🌟 Spot on! That's correct! ({attempt})"
        active_step.student_answer = attempt
        has_more = widget.advance_step(recorded_answer=attempt)

        history.append({
            "step_number": active_step.step_number,
            "student_attempt": attempt,
            "is_correct": True,
            "feedback": feedback,
            "hints_used": active_step.current_hint_level
        })

        if not has_more:
            return {
                "step_widget": widget.model_dump(),
                "current_step_index": widget.current_step_index,
                "is_problem_complete": True,
                "is_problem_solved": True,
                "feedback_message": "🎉 Amazing work! You have completed all the steps for this problem! ⭐",
                "active_hint": None,
                "current_hint_tier": 0,
                "attempt_history": history
            }

        next_step = widget.get_active_step()
        return {
            "step_widget": widget.model_dump(),
            "current_step_index": widget.current_step_index,
            "is_problem_complete": False,
            "is_problem_solved": False,
            "feedback_message": f"{feedback} Ready for Step {next_step.step_number if next_step else 2}!",
            "active_hint": None,
            "current_hint_tier": 0,
            "attempt_history": history
        }
    else:
        # Incorrect attempt -> escalate hint
        new_tier, hint_text = hint_engine.escalate_hint(
            step=active_step,
            prior_attempts=[attempt],
            grade_level=grade_level
        )
        feedback = f"Gently rethink: '{attempt}' isn't quite what we're looking for. Let's look at this hint! 👇"

        history.append({
            "step_number": active_step.step_number,
            "student_attempt": attempt,
            "is_correct": False,
            "feedback": feedback,
            "hints_used": new_tier
        })

        return {
            "step_widget": widget.model_dump(),
            "current_step_index": widget.current_step_index,
            "is_problem_complete": False,
            "is_problem_solved": False,
            "feedback_message": feedback,
            "active_hint": hint_text,
            "current_hint_tier": new_tier,
            "attempt_history": history
        }


def request_hint_node(state: TutorState) -> Dict[str, Any]:
    """
    Directly escalates and reveals the next progressive hint tier for the active step.
    """
    widget = _get_widget_from_state(state)
    if not widget:
        return {"feedback_message": "Please start a problem first to receive hints!"}

    active_step = widget.get_active_step()
    if not active_step:
        return {"feedback_message": "You've completed all steps!"}

    grade_level = state.get("grade_level", "grade_1_3")
    new_tier, hint_text = hint_engine.escalate_hint(
        step=active_step,
        grade_level=grade_level
    )

    feedback = f"💡 Here is a clue (Tier {new_tier}/3) to guide your thinking:"
    return {
        "step_widget": widget.model_dump(),
        "active_hint": hint_text,
        "current_hint_tier": new_tier,
        "feedback_message": feedback
    }


def navigate_step_node(state: TutorState) -> Dict[str, Any]:
    """
    Jumps to a specific step index requested by the user.
    """
    widget = _get_widget_from_state(state)
    if not widget:
        return {"feedback_message": "No active problem to navigate."}

    target_idx = state.get("target_nav_index", 0)
    success = widget.jump_to_step(target_idx)

    active_step = widget.get_active_step()
    if success and active_step:
        feedback = f"📍 Navigated to Step {active_step.step_number}: {active_step.title}"
    else:
        feedback = "Invalid step requested."

    return {
        "step_widget": widget.model_dump(),
        "current_step_index": widget.current_step_index,
        "feedback_message": feedback,
        "active_hint": None,
        "current_hint_tier": active_step.current_hint_level if active_step else 0
    }


def clarify_node(state: TutorState) -> Dict[str, Any]:
    """
    Emits child-friendly clarification without clearing problem state.
    """
    raw_query = state.get("raw_user_input", "")
    widget = _get_widget_from_state(state)
    grade_level = state.get("grade_level", "grade_1_3")

    clarification_res = clarifier.build_clarification_response(
        raw_query=raw_query,
        widget=widget,
        grade_level=grade_level
    )

    return {
        "clarification_needed": True,
        "clarification_question": clarification_res["clarification_question"],
        "feedback_message": clarification_res["feedback_message"]
    }


def chitchat_node(state: TutorState) -> Dict[str, Any]:
    """
    Handles friendly student greetings and polite chit-chat without launching a stepper card.
    """
    greeting_msg = (
        "👋 Hello there! I'm ReanMore, your AI study buddy! 🦁\n\n"
        "What math or science homework problem would you like to explore together today? "
        "You can type your problem or tap the camera icon 📷 to scan a worksheet!"
    )
    return {
        "feedback_message": greeting_msg,
        "formatted_markdown": greeting_msg,
        "is_deflected": False,
        "detected_intent": "CHITCHAT"
    }


def guardrails_node(state: TutorState) -> Dict[str, Any]:
    """
    Evaluates child safety, redacts PII, and detects off-topic distractions.
    """
    raw_input = state.get("raw_user_input", "").strip()
    widget = _get_widget_from_state(state)
    active_step = widget.get_active_step() if widget else None

    # 1. Safety & PII check
    safety_res = safety_filter.evaluate(raw_input)
    if not safety_res.is_safe:
        return {
            "is_safe": False,
            "safety_violation": safety_res.categories_detected[0].value if safety_res.categories_detected else "UNSAFE",
            "feedback_message": safety_res.safe_response,
            "is_deflected": True,
            "detected_intent": "GUARDRAIL_BLOCKED"
        }

    # 2. Pure PII check (kid typed only personal info without homework question)
    if safety_res.has_pii:
        import re
        stripped = re.sub(
            r'\[(PHONE|EMAIL|ADDRESS|NAME)_REDACTED\]', '', safety_res.redacted_text, flags=re.IGNORECASE
        )
        stripped = re.sub(
            r'\b(my\s+name\s+is|i\s+am|call\s+me|at|to|please|here\s+is|my\s+phone|my\s+number|my\s+address|i\s+live)\b',
            '',
            stripped,
            flags=re.IGNORECASE
        ).strip(' .,!?:;-\t\n')

        # If no actual homework problem/attempt remains
        if len(stripped) < 3:
            notice = safety_res.pii_notice or "🔒 *Privacy Tip: Keep your secret information safe! Never share real phone numbers or addresses online.*"
            if active_step:
                pii_redirect = (
                    f"{notice}\n\n"
                    f"Let's get back to our mission for Step {active_step.step_number}! 🚀\n\n"
                    f"👉 **Your Turn:** {active_step.your_turn}"
                )
            else:
                pii_redirect = (
                    f"{notice}\n\n"
                    f"What science or math homework problem should we work on together? ✏️"
                )
            return {
                "is_safe": True,
                "has_pii": True,
                "redacted_input": safety_res.redacted_text,
                "student_attempt": safety_res.redacted_text,
                "is_deflected": True,
                "deflection_message": pii_redirect,
                "feedback_message": pii_redirect,
                "detected_intent": "OFF_TOPIC_DEFLECTED"
            }

    # 3. Educational Scope Deflection check
    scope_res = scope_deflector.check_scope(safety_res.redacted_text)
    if scope_res.is_off_topic:
        deflection_msg = scope_deflector.build_deflection(
            text=safety_res.redacted_text,
            category=scope_res.category,
            active_step=active_step
        )
        return {
            "is_safe": True,
            "has_pii": safety_res.has_pii,
            "redacted_input": safety_res.redacted_text,
            "student_attempt": safety_res.redacted_text,
            "is_deflected": True,
            "deflection_message": deflection_msg,
            "feedback_message": deflection_msg,
            "detected_intent": "OFF_TOPIC_DEFLECTED"
        }

    # Clean text with PII safely sanitized
    updates: Dict[str, Any] = {
        "is_safe": True,
        "has_pii": safety_res.has_pii,
        "redacted_input": safety_res.redacted_text,
        "student_attempt": safety_res.redacted_text,
        "is_deflected": False
    }
    if safety_res.pii_notice:
        updates["feedback_message"] = safety_res.pii_notice

    return updates


def deflect_node(state: TutorState) -> Dict[str, Any]:
    """
    Emits deflection message preserving existing widget.
    """
    msg = state.get("deflection_message") or state.get("feedback_message", "Let's focus on homework!")
    return {
        "feedback_message": msg
    }


def compile_response_node(state: TutorState) -> Dict[str, Any]:
    """
    Compiles final SocraticResponse with synchronized Markdown and JSON widget.
    """
    widget = _get_widget_from_state(state)
    session_id = state.get("session_id", "default_session")
    feedback = state.get("feedback_message")
    active_hint = state.get("active_hint")
    is_complete = state.get("is_problem_complete", False) or state.get("is_problem_solved", False)

    if state.get("is_safe") is False:
        formatted_md = feedback or "Let's use kind and friendly words here!"
    elif widget:
        socratic_resp = SocraticResponse.from_step_widget(
            session_id=session_id,
            widget=widget,
            feedback_message=feedback,
            active_hint=active_hint,
            is_problem_complete=is_complete
        )
        formatted_md = socratic_resp.formatted_markdown
    else:
        formatted_md = feedback or "Welcome! Please enter a homework question."

    return {
        "formatted_markdown": formatted_md
    }


# -------------------------------------------------------------------------
# Routing Edges
# -------------------------------------------------------------------------

def route_by_intent(state: TutorState) -> str:
    intent = state.get("detected_intent", StudentIntent.INITIAL_QUESTION.value)

    if intent in ("GUARDRAIL_BLOCKED", "OFF_TOPIC_DEFLECTED", "OFF_TOPIC"):
        return "deflect"
    elif intent in ("CHITCHAT", "GREETING"):
        return "chitchat"
    elif intent in (StudentIntent.REQUEST_HINT.value, "HINT", "REQUEST_HINT"):
        return "request_hint"
    elif intent == "NAVIGATION_JUMP":
        return "navigate_step"
    elif intent in (StudentIntent.REQUEST_CLARIFICATION.value, "AMBIGUOUS", "CLARIFY", "REQUEST_CLARIFICATION"):
        return "clarify"
    elif intent in (StudentIntent.STEP_ANSWER_ATTEMPT.value, "STEP_ATTEMPT", "STEP_ANSWER_ATTEMPT"):
        return "validate_attempt"
    elif intent in (StudentIntent.INITIAL_QUESTION.value, "INITIAL_QUESTION", "INITIAL_SOLVE", "REQUEST_PRACTICE"):
        return "initial_problem"
    return "clarify"


# -------------------------------------------------------------------------
# StateGraph Assembly
# -------------------------------------------------------------------------

def build_socratic_graph(checkpointer=None):
    """
    Constructs and compiles the Socratic Tutor StateGraph.
    """
    builder = StateGraph(TutorState)

    # Nodes
    builder.add_node("process_nlu", process_nlu_node)
    builder.add_node("guardrails", guardrails_node)
    builder.add_node("deflect", deflect_node)
    builder.add_node("chitchat", chitchat_node)
    builder.add_node("initial_problem", initial_problem_node)
    builder.add_node("validate_attempt", validate_attempt_node)
    builder.add_node("request_hint", request_hint_node)
    builder.add_node("navigate_step", navigate_step_node)
    builder.add_node("clarify", clarify_node)
    builder.add_node("compile_response", compile_response_node)

    # Edges
    builder.add_edge(START, "process_nlu")
    builder.add_edge("process_nlu", "guardrails")

    builder.add_conditional_edges(
        "guardrails",
        route_by_intent,
        {
            "deflect": "deflect",
            "chitchat": "chitchat",
            "initial_problem": "initial_problem",
            "validate_attempt": "validate_attempt",
            "request_hint": "request_hint",
            "navigate_step": "navigate_step",
            "clarify": "clarify"
        }
    )

    builder.add_edge("deflect", "compile_response")
    builder.add_edge("chitchat", "compile_response")
    builder.add_edge("initial_problem", "compile_response")
    builder.add_edge("validate_attempt", "compile_response")
    builder.add_edge("request_hint", "compile_response")
    builder.add_edge("navigate_step", "compile_response")
    builder.add_edge("clarify", "compile_response")
    builder.add_edge("compile_response", END)

    cp = checkpointer if checkpointer is not None else MemorySaver()
    return builder.compile(checkpointer=cp)


socratic_graph = build_socratic_graph()
