"""
File: orchestrator/app/services/socratic/graph.py
Description: LangGraph StateGraph orchestration pipeline for the Socratic elementary tutoring workflow.
             Handles intent routing, problem decomposition, step validation, 3-tier progressive hints,
             dual-payload (JSON widget + Markdown) response compilation, intent classification,
             and hint-level-3 exit via the reveal_and_continue node.
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
from app.services.socratic.intent_classifier import classify_intent_node
from app.services.socratic.reveal_and_continue import (
    reveal_and_continue_node,
    compute_frustration_score,
)
from app.services.socratic.verify_steps import verify_steps_node
from app.services.socratic.validate_answer import (
    validate_student_answer,
    VALIDATION_CORRECT,
    VALIDATION_PARTIAL,
    VALIDATION_INCORRECT,
)
from app.services.telemetry.gap_recorder import log_gap_event

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
    unit stripping, and Khmer-English cross-language equivalence.
    Equivalence strictly delegates to SymPy CAS / safe_math for math and
    validate_student_answer rubric for science.
    """
    if not student_attempt or not expected_answer:
        return False

    # Khmer digit conversion map (KEEP)
    khmer_digits = str.maketrans("០១២៣៤៥៦៧៨៩", "0123456789")

    s_clean = student_attempt.strip().lower().translate(khmer_digits)
    e_clean = expected_answer.strip().lower().translate(khmer_digits)

    # 1. Exact match (KEEP)
    if s_clean == e_clean:
        return True

    # 2. Khmer & English Affirmative / Negative Cross-Language Matching (KEEP)
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

    # 3. Khmer Multiple Choice Letters (ក -> a, ខ -> b, គ -> c, ឃ -> d) (KEEP)
    khmer_letter_map = {"ក": "a", "ខ": "b", "គ": "c", "ឃ": "d"}
    s_mapped = khmer_letter_map.get(s_clean, s_clean)
    e_mapped = khmer_letter_map.get(e_clean, e_clean)
    if s_mapped == e_mapped:
        return True

    # 4. Input normalization: word_to_num mapping (KEEP)
    from typing import Optional
    import re
    from app.services.socratic.safe_math import safe_eval_ast

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
        t = re.sub(r'\s*(cookies|apples|candies|cm|m|km|kg|g|dollars|\$|units|hours|mins|seconds|នាក់|គ្រាប់|ដើម).*$', '', t).strip()
        if t in word_to_num:
            return word_to_num[t]
        try:
            val_frac = safe_eval_ast(t)
            if val_frac is not None:
                return float(val_frac)
        except Exception:
            pass
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

    # Math equivalence via safe_math AST / CAS
    s_num = parse_val(s_clean)
    e_num = parse_val(e_clean)
    if s_num is not None and e_num is not None:
        if abs(s_num - e_num) < 0.001:
            return True

    # SymPy CAS symbolic algebraic equivalence check (e.g. algebraic expressions)
    try:
        from sympy import sympify
        s_sym = sympify(s_clean)
        e_sym = sympify(e_clean)
        if s_sym == e_sym or (s_sym - e_sym) == 0:
            return True
    except Exception:
        pass

    # Science equivalence delegates strictly to validate_student_answer rubric (NO canned synonym dictionaries)
    try:
        val_outcome = validate_student_answer(
            student_attempt=s_clean,
            expected_answer=e_clean,
            subject="science"
        )
        if val_outcome and val_outcome.is_correct:
            return True
    except Exception as e:
        logger.warning(f"Science rubric validation failed: {e}")

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
    Decomposes the homework problem into 2–4 Socratic step cards.
    Phase 1A: Checks the deterministic Skill Template Library first (100% mathematical
    accuracy, answer-safe visual specs, distinct parallel examples, zero marginal cost).
    Falls back to LLM exercise_planning and legacy prompts when unhandled by skill templates.
    """
    problem = state.get("problem_text") or state.get("raw_user_input", "Solve the homework problem.")
    grade_level = state.get("grade_level", "grade_1_3")
    session_id = state.get("session_id", "default_session")
    subject = (state.get("subject") or "math").upper()

    # 0. DETERMINISTIC SKILL TEMPLATE LIBRARY (Phase 1A - Spec Section 7)
    if subject == "MATH":
        from app.services.socratic.math_engine.cas import parse_binary_arithmetic
        from app.services.socratic.parse_verifier import verify_and_parse_word_problem
        from app.services.socratic.skills import skill_registry

        parsed_prob = parse_binary_arithmetic(problem)
        if not parsed_prob:
            parse_res = verify_and_parse_word_problem(problem, grade_level=grade_level)
            if parse_res.is_valid and parse_res.needs_confirmation and parse_res.confirmation_prompt:
                return {
                    "problem_text": problem,
                    "clarification_needed": True,
                    "clarification_question": parse_res.confirmation_prompt,
                    "feedback_message": parse_res.confirmation_prompt,
                    "is_problem_complete": False,
                    "is_problem_solved": False,
                }
            elif parse_res.is_valid and parse_res.parsed_problem:
                parsed_prob = parse_res.parsed_problem
            else:
                log_gap_event(
                    gap_type="content",
                    gap_code="UNPARSED_WORD_PROBLEM",
                    severity=2,
                    user_id=state.get("user_id"),
                    session_id=session_id,
                    problem_id=state.get("problem_id"),
                    grade_tier=grade_level,
                    subject="math",
                    details={"raw_problem": problem, "issues": getattr(parse_res, "issues", [])}
                )

        if parsed_prob:
            matched_skill = skill_registry.match(parsed_prob)
            if matched_skill:
                logger.info(f"[SkillTemplate] Matched deterministic skill: {matched_skill.skill_id}")
                templates = matched_skill.build_steps(parsed_prob)
                if templates and len(templates) >= 2:
                    coerced_steps = []
                    for t in templates:
                        coerced_steps.append(SocraticStep(
                            step_number=t.step_number,
                            title=t.title,
                            status="in_progress" if t.step_number == 1 else "pending",
                            mission=t.mission,
                            clue=t.clue,
                            helpful_example=t.helpful_example,
                            your_turn=t.your_turn,
                            expected_answer=t.expected_answer,
                            concept=t.concept,
                            hints=t.hints,
                            current_hint_level=0,
                            visual_data=t.visual_spec
                        ))
                    widget = StepWidgetPayload(
                        total_steps=len(coerced_steps),
                        current_step_index=0,
                        completed_steps=[],
                        visual_data=coerced_steps[0].visual_data if coerced_steps else None,
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
            else:
                log_gap_event(
                    gap_type="content",
                    gap_code="NO_SKILL_MATCH",
                    severity=2,
                    user_id=state.get("user_id"),
                    session_id=session_id,
                    problem_id=state.get("problem_id"),
                    grade_tier=grade_level,
                    subject="math",
                    details={"parsed_problem": parsed_prob, "raw_problem": problem}
                )

    # 0B. CURRICULUM SCIENCE RAG (Phase 3)
    retrieved_science_context = ""
    curriculum_citations = []
    if subject == "SCIENCE":
        try:
            from app.services.rag.retriever import get_science_retriever
            retriever = get_science_retriever()
            hits, retrieved_science_context, is_grounded = retriever.retrieve_grounded_context(
                query=problem,
                grade_band=grade_level,
                session_id=session_id
            )
            if hits and is_grounded:
                curriculum_citations = [h.get("source") for h in hits if h.get("source")]
                logger.info(f"[ScienceRAG] Grounded in {len(hits)} textbook passages (top: {hits[0].get('title')})")
        except Exception as rag_err:
            logger.warning(f"[ScienceRAG] Retrieval failed: {rag_err}")

    # PRIMARY PATH — unified exercise_planning prompt (full card + hints, no answer leakage)
    widget_dict = controller.plan_exercise_socratic_widget(
        problem_text=problem,
        grade_level=grade_level,
        session_id=session_id,
        exercise_context=retrieved_science_context or None
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
                "clarification_needed": False,
                "retrieved_context": retrieved_science_context,
                "curriculum_citations": curriculum_citations
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
            clue_text = card_content.get("clue") or s.get("clue") or "Look closely at the question!"
            ex_text = card_content.get("helpful_example") or "Picture real objects in front of you!"
            if subject == "science":
                step_hints = [
                    f"💡 Helpful Clue: {clue_text}",
                    f"🍎 Real-World Example: {ex_text}",
                    "✨ Give it your best try! What word or idea fits our clue best?"
                ]
            else:
                step_hints = [
                    f"💡 Helpful Clue: {clue_text}",
                    f"🍎 Parallel Example: {ex_text}",
                    "🔢 Count step-by-step or draw it on scratch paper to see the answer!"
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
        "clarification_needed": False,
        "retrieved_context": retrieved_science_context,
        "curriculum_citations": curriculum_citations
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

    # 1. Fast path: rich answer validation (equivalence, near-miss, unit check, science concepts)
    val_res = validate_student_answer(
        student_attempt=attempt,
        expected_answer=expected,
        subject=state.get("subject", "math"),
    )
    is_correct = val_res.is_correct
    is_partial = val_res.is_partial

    # 2. Downstream path: query microservice validator or LLM evaluator if not matched
    if not is_correct and not is_partial and expected and attempt:
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
        feedback = val_res.feedback_eng if val_res.feedback_eng else f"🌟 Spot on! That's correct! ({attempt})"
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
                "validation_outcome": VALIDATION_CORRECT,
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
            "validation_outcome": VALIDATION_CORRECT,
            "active_hint": None,
            "current_hint_tier": 0,
            "attempt_history": history
        }
    elif is_partial:
        # Near-miss or unit mismatch: give targeted feedback WITHOUT escalating hint tier
        feedback = val_res.feedback_eng
        history.append({
            "step_number": active_step.step_number,
            "student_attempt": attempt,
            "is_correct": False,
            "is_partial": True,
            "feedback": feedback,
            "hints_used": active_step.current_hint_level
        })
        return {
            "step_widget": widget.model_dump(),
            "current_step_index": widget.current_step_index,
            "is_problem_complete": False,
            "is_problem_solved": False,
            "feedback_message": feedback,
            "validation_outcome": VALIDATION_PARTIAL,
            "active_hint": state.get("active_hint"),
            "current_hint_tier": active_step.current_hint_level,
            "attempt_history": history,
            "frustration_score": state.get("frustration_score", 0.0),
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

        # Check for error streaks (>= 3 consecutive wrong attempts on this step)
        step_mistakes = [h for h in history if h.get("step_number") == active_step.step_number and not h.get("is_correct")]
        if len(step_mistakes) >= 3:
            log_gap_event(
                gap_type="learner",
                gap_code="STEP_ERROR_STREAK",
                severity=2,
                user_id=state.get("user_id"),
                session_id=state.get("session_id"),
                problem_id=state.get("problem_id"),
                grade_tier=grade_level,
                subject=state.get("subject", "math"),
                step_index=active_step.step_number,
                details={
                    "step_title": active_step.title,
                    "concept": active_step.concept,
                    "attempts": [h.get("student_attempt") for h in step_mistakes[-3:]],
                }
            )
            concept_str = (active_step.concept or "").lower()
            if "regroup" in concept_str or "borrow" in concept_str:
                log_gap_event(
                    gap_type="learner",
                    gap_code="MISCONCEPTION_REGROUP",
                    severity=2,
                    user_id=state.get("user_id"),
                    session_id=state.get("session_id"),
                    problem_id=state.get("problem_id"),
                    grade_tier=grade_level,
                    subject=state.get("subject", "math"),
                    step_index=active_step.step_number,
                    details={"concept": active_step.concept, "attempt": attempt}
                )

        # Compute frustration score after recording attempt
        frustration = compute_frustration_score(
            attempt_history=history,
            response_time_ms=state.get("response_time_ms"),
            idle_seconds=state.get("idle_seconds"),
        )

        return {
            "step_widget": widget.model_dump(),
            "current_step_index": widget.current_step_index,
            "is_problem_complete": False,
            "is_problem_solved": False,
            "feedback_message": feedback,
            "validation_outcome": VALIDATION_INCORRECT,
            "active_hint": hint_text,
            "current_hint_tier": new_tier,
            "attempt_history": history,
            "frustration_score": frustration,
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

    log_gap_event(
        gap_type="content",
        gap_code="PARSE_UNCONFIRMED",
        severity=1,
        user_id=state.get("user_id"),
        session_id=state.get("session_id"),
        problem_id=state.get("problem_id"),
        grade_tier=grade_level,
        subject=state.get("subject", "math"),
        details={"raw_query": raw_query}
    )

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
        # If Tier 2 crisis detected (Child abuse, Self-harm, Immediate danger), dispatch escalation alert
        if getattr(safety_res, "escalate", False) or safety_res.severity_tier >= 2:
            try:
                from app.services.guardrails.escalation import dispatch_escalation_alert
                dispatch_escalation_alert(
                    safety_result=safety_res,
                    session_id=state.get("session_id", "sess_default"),
                )
            except Exception as esc_err:
                logger.error(f"[Guardrails] Failed to dispatch crisis escalation: {esc_err}")

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
    Enforces Output Leak Guard (Spec Section 1, 2.3, 9, 10):
    - Deterministically scans every outgoing student message (feedback_message,
      active_hint, formatted_markdown) for expected answer leaks.
    - Zero leaks allowed across Hint Tiers 1-3.
    - Disclosure allowed ONLY if is_step_solved is True OR is_reveal_state is explicitly True.
    - Multi-Step Praise Shield: Prevents revealing future unsolved steps or final answers in praise.
    - Quarantines any detected leak with safe pedagogical guidance.
    """
    widget = _get_widget_from_state(state)
    session_id = state.get("session_id", "default_session")
    feedback = state.get("feedback_message")
    active_hint = state.get("active_hint")
    is_complete = state.get("is_problem_complete", False) or state.get("is_problem_solved", False)

    from app.services.guardrails.leak_guard import check_tutor_response_leak

    # 1. Output Leak Guard scan on outgoing feedback and hints
    leak_detected = False
    is_step_solved = False
    is_reveal_state = bool(state.get("is_reveal_state", False))
    current_hint_tier = state.get("current_hint_tier", 0)
    attempts_count = len(state.get("attempt_history", []))
    unsolved_targets: List[str] = []
    final_answer: Optional[str] = None
    target_answer = ""
    active_step = None
    problem_text = state.get("problem_text")

    if widget and state.get("is_safe") is not False:
        active_step = widget.get_active_step()
        target_answer = active_step.expected_answer if active_step else ""
        is_step_solved = bool(
            state.get("validation_outcome") == VALIDATION_CORRECT
            or (active_step and (active_step.status == "completed" or (active_step.step_number - 1) in widget.completed_steps))
        )

        # Build list of unsolved future steps & final answer
        final_answer = widget.steps[-1].expected_answer if widget.steps else None
        for s in widget.steps:
            is_s_completed = (s.status == "completed" or (s.step_number - 1) in widget.completed_steps)
            if not is_s_completed and s.expected_answer and s != active_step:
                unsolved_targets.append(s.expected_answer)

        # Scan feedback_message
        if feedback and target_answer:
            is_leak, sanitized_fb, reason = check_tutor_response_leak(
                tutor_reply=feedback,
                target_answer=target_answer,
                is_step_solved=is_step_solved,
                is_reveal_state=is_reveal_state,
                current_hint_tier=current_hint_tier,
                step_number=active_step.step_number if active_step else None,
                attempts_count=attempts_count,
                unsolved_step_values=unsolved_targets,
                final_answer=final_answer,
                problem_text=problem_text
            )
            if is_leak:
                logger.warning(f"[OutputLeakGuard] Intercepted feedback leak: {reason}. Quarantining.")
                leak_detected = True
                feedback = sanitized_fb

        # Scan active_hint
        if active_hint and target_answer:
            is_leak_hint, sanitized_hint, reason_hint = check_tutor_response_leak(
                tutor_reply=active_hint,
                target_answer=target_answer,
                is_step_solved=is_step_solved,
                is_reveal_state=is_reveal_state,
                current_hint_tier=current_hint_tier,
                step_number=active_step.step_number if active_step else None,
                attempts_count=attempts_count,
                unsolved_step_values=unsolved_targets,
                final_answer=final_answer,
                problem_text=problem_text
            )
            if is_leak_hint:
                logger.warning(f"[OutputLeakGuard] Intercepted hint leak: {reason_hint}. Quarantining.")
                leak_detected = True
                active_hint = sanitized_hint

        # Scan visual_data for active step
        if active_step and active_step.visual_data:
            try:
                from app.services.visuals import VisualSpec, check_visual_spec_leak
                v_spec = VisualSpec.model_validate(active_step.visual_data)
                v_leak, sanitized_v_spec, v_reason = check_visual_spec_leak(
                    spec=v_spec,
                    target_answer=target_answer,
                    unsolved_targets=unsolved_targets
                )
                if v_leak:
                    logger.warning(f"[VisualLeakGuard] Intercepted visual leak: {v_reason}. Sanitizing.")
                    leak_detected = True
                    active_step.visual_data = sanitized_v_spec.model_dump()
                    widget.visual_data = sanitized_v_spec.model_dump()
                else:
                    widget.visual_data = active_step.visual_data
            except Exception as e:
                logger.debug(f"Visual spec leak check skipped: {e}")

    # 2. Compile synchronized Markdown presentation
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

    # 3. Final fail-safe barrier on compiled Markdown output
    if widget and formatted_md and state.get("is_safe") is not False:
        if target_answer and not is_step_solved and not is_reveal_state:
            is_md_leak, sanitized_md, md_reason = check_tutor_response_leak(
                tutor_reply=formatted_md,
                target_answer=target_answer,
                is_step_solved=False,
                is_reveal_state=False,
                current_hint_tier=current_hint_tier,
                step_number=active_step.step_number if active_step else None,
                attempts_count=attempts_count,
                unsolved_step_values=unsolved_targets,
                final_answer=final_answer,
                problem_text=problem_text
            )
            if is_md_leak:
                logger.warning(f"[OutputLeakGuard] Intercepted markdown leak: {md_reason}. Sanitizing.")
                leak_detected = True
                formatted_md = sanitized_md

    updates: Dict[str, Any] = {
        "formatted_markdown": formatted_md,
        "feedback_message": feedback,
        "active_hint": active_hint,
    }
    if leak_detected:
        updates["leak_quarantined"] = True

    return updates


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
        return "classify_intent"
    elif intent in (StudentIntent.INITIAL_QUESTION.value, "INITIAL_QUESTION", "INITIAL_SOLVE", "REQUEST_PRACTICE"):
        return "initial_problem"
    return "clarify"


def route_after_classify_intent(state: TutorState) -> str:
    """
    After intent classification, route to the appropriate handler.
    Deflected intents (safety, answer demand, off-topic, unclear) go straight to deflect.
    Clarification goes to request_hint.
    Answer attempts go to validate_attempt.
    """
    intent = state.get("detected_intent", StudentIntent.STEP_ANSWER_ATTEMPT.value)
    if intent in ("GUARDRAIL_BLOCKED", "OFF_TOPIC_DEFLECTED", "UNCLEAR"):
        return "deflect"
    elif intent in ("REQUEST_HINT", StudentIntent.REQUEST_HINT.value):
        return "request_hint"
    return "validate_attempt"


def route_after_validate(state: TutorState) -> str:
    """
    After validation, check if hint level 3 was reached on an incorrect answer.
    If so, route to reveal_and_continue instead of compile_response.
    Also route to reveal if frustration score >= 0.8 (take_a_break path).
    """
    hint_tier = state.get("current_hint_tier", 0)
    is_complete = state.get("is_problem_complete", False) or state.get("is_problem_solved", False)
    frustration = state.get("frustration_score", 0.0)

    if is_complete:
        return "compile_response"
    if hint_tier >= 3 or frustration >= 0.8:
        return "reveal_and_continue"
    return "compile_response"


# -------------------------------------------------------------------------
# StateGraph Assembly
# -------------------------------------------------------------------------

def build_socratic_graph(checkpointer=None):
    """
    Constructs and compiles the Socratic Tutor StateGraph.

    Node execution order for answer attempts:
        process_nlu → guardrails → classify_intent → validate_attempt
            → (hint tier < 3) → compile_response
            → (hint tier >= 3 or frustration >= 0.8) → reveal_and_continue → compile_response
    """
    builder = StateGraph(TutorState)

    # Nodes
    builder.add_node("process_nlu", process_nlu_node)
    builder.add_node("guardrails", guardrails_node)
    builder.add_node("deflect", deflect_node)
    builder.add_node("chitchat", chitchat_node)
    builder.add_node("initial_problem", initial_problem_node)
    builder.add_node("verify_steps", verify_steps_node)                # NEW: Sprint 2.1
    builder.add_node("classify_intent", classify_intent_node)          # NEW: Sprint 1.4
    builder.add_node("validate_attempt", validate_attempt_node)
    builder.add_node("reveal_and_continue", reveal_and_continue_node)   # NEW: Sprint 1.3
    builder.add_node("request_hint", request_hint_node)
    builder.add_node("navigate_step", navigate_step_node)
    builder.add_node("clarify", clarify_node)
    builder.add_node("compile_response", compile_response_node)

    # Edges
    builder.add_edge(START, "process_nlu")
    builder.add_edge("process_nlu", "guardrails")

    # Main intent routing (from guardrails)
    builder.add_conditional_edges(
        "guardrails",
        route_by_intent,
        {
            "deflect": "deflect",
            "chitchat": "chitchat",
            "initial_problem": "initial_problem",
            "classify_intent": "classify_intent",   # answer attempts go here first
            "request_hint": "request_hint",
            "navigate_step": "navigate_step",
            "clarify": "clarify"
        }
    )

    # Intent classifier → deflect / request_hint / validate_attempt
    builder.add_conditional_edges(
        "classify_intent",
        route_after_classify_intent,
        {
            "deflect": "deflect",
            "request_hint": "request_hint",
            "validate_attempt": "validate_attempt",
        }
    )

    # validate_attempt → reveal_and_continue (tier 3 exit) OR compile_response
    builder.add_conditional_edges(
        "validate_attempt",
        route_after_validate,
        {
            "compile_response": "compile_response",
            "reveal_and_continue": "reveal_and_continue",
        }
    )

    builder.add_edge("deflect", "compile_response")
    builder.add_edge("chitchat", "compile_response")
    builder.add_edge("initial_problem", "verify_steps")                 # NEW: Sprint 2.1 verify
    builder.add_edge("verify_steps", "compile_response")                # NEW: Sprint 2.1 verify
    builder.add_edge("reveal_and_continue", "compile_response")         # NEW
    builder.add_edge("request_hint", "compile_response")
    builder.add_edge("navigate_step", "compile_response")
    builder.add_edge("clarify", "compile_response")
    builder.add_edge("compile_response", END)

    cp = checkpointer if checkpointer is not None else MemorySaver()
    return builder.compile(checkpointer=cp)


socratic_graph = build_socratic_graph()
