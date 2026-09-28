"""
File: orchestrator/app/services/socratic/graph.py
Description: LangGraph StateGraph orchestration pipeline for the Socratic elementary tutoring workflow.
             Handles intent routing, problem decomposition, step validation, 3-tier progressive hints,
             and dual-payload (JSON widget + Markdown) response compilation.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

import re
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
    unit stripping, and science conceptual synonyms.
    """
    if not student_attempt or not expected_answer:
        return False

    s_clean = student_attempt.strip().lower()
    e_clean = expected_answer.strip().lower()

    # Fast-path checks:
    # 1. Exact match: s_clean == e_clean (e.g. "evaporation" == "evaporation")
    # 2. Sentence containment: e_clean in s_clean (e.g. "the answer is evaporation" contains "evaporation")
    if s_clean == e_clean or e_clean in s_clean:
        return True

    # 3. Bounded full-word keyword match in expected (avoiding sub-word substrings like "is" in "photosynthesis")
    import re
    common_stopwords = {"the", "a", "an", "is", "it", "to", "of", "and", "in", "by", "for", "that", "its", "into", "on", "at", "no", "yes"}
    if len(s_clean) >= 3 and s_clean not in common_stopwords:
        if re.search(rf'\b{re.escape(s_clean)}\b', e_clean):
            return True

    import re
    from typing import Optional

    word_to_num = {
        "zero": 0.0, "one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0,
        "five": 5.0, "six": 6.0, "seven": 7.0, "eight": 8.0, "nine": 9.0,
        "ten": 10.0, "eleven": 11.0, "twelve": 12.0, "half": 0.5,
        "one half": 0.5, "quarter": 0.25, "one quarter": 0.25, "three quarters": 0.75
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

    # Science Conceptual Synonyms
    synonyms = [
        {"evaporation", "evaporate", "evaporates", "vaporization", "liquid to gas", "steam", "liquid turns into gas"},
        {"condensation", "condense", "condenses", "gas to liquid", "water droplets"},
        {"photosynthesis", "sunlight and water", "making food", "glucose", "plants make food"},
        {"gravity", "gravitational force", "pull of earth", "pulls down", "gravity pulls it down"},
        {"mitochondria", "powerhouse of the cell", "cellular energy", "atp", "powerhouse"}
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

        if any(h in lower for h in ["hint", "clue", "help", "i'm stuck", "stuck", "don't know", "dont know"]):
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


def initial_problem_node(state: TutorState) -> Dict[str, Any]:
    """
    Decomposes the homework problem into 2–4 Socratic steps and generates Step 1 card.
    """
    problem = state.get("problem_text") or state.get("raw_user_input", "Solve the homework problem.")
    grade_level = state.get("grade_level", "grade_1_3")

    # Decompose into steps using prompt controller
    steps_data = controller.breakdown_problem_into_steps(problem, grade_level=grade_level)
    socratic_steps: List[SocraticStep] = []

    for idx, s in enumerate(steps_data):
        step_num = s.get("step_number", idx + 1)
        # Generate 4-part card content for each step
        card_content = controller.generate_step_card(
            homework_problem=problem,
            step_number=step_num,
            total_steps=len(steps_data),
            step_title=s.get("title", f"Step {step_num}"),
            step_concept=s.get("concept", s.get("mission", "")),
            expected_operation=s.get("clue", ""),
            grade_level=grade_level
        )
        def _safe_str(val: Any) -> str:
            if isinstance(val, dict):
                return " ".join(f"{v}" for v in val.values() if v)
            elif isinstance(val, list):
                return " ".join(str(item) for item in val)
            return str(val) if val is not None else ""

        step_obj = SocraticStep(
            step_number=step_num,
            title=s.get("title", f"Step {step_num}"),
            status="in_progress" if idx == 0 else "pending",
            mission=_safe_str(card_content.get("mission")),
            clue=_safe_str(card_content.get("clue")),
            helpful_example=_safe_str(card_content.get("helpful_example")),
            your_turn=_safe_str(card_content.get("your_turn")),
            expected_answer=s.get("expected_answer", str(step_num)),
            concept=s.get("concept", "")
        )

        socratic_steps.append(step_obj)

    widget = StepWidgetPayload(
        total_steps=len(socratic_steps),
        current_step_index=0,
        completed_steps=[],
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
    If correct -> advances step and emits praise.
    If incorrect -> triggers progressive hint and gentle encouragement.
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

    is_correct = _is_answer_equivalent(attempt, expected)

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
    elif intent in (StudentIntent.REQUEST_HINT.value, "HINT", "REQUEST_HINT"):
        return "request_hint"
    elif intent in ("NAVIGATION_JUMP", "NAVIGATE_STEP"):
        return "navigate_step"
    elif intent in (StudentIntent.REQUEST_CLARIFICATION.value, "CLARIFY", "AMBIGUOUS", "REQUEST_CLARIFICATION"):
        return "clarify"
    elif intent in (StudentIntent.STEP_ANSWER_ATTEMPT.value, "STEP_ATTEMPT", "STEP_ANSWER_ATTEMPT"):
        return "validate_attempt"
    elif intent in (StudentIntent.INITIAL_QUESTION.value, "INITIAL_SOLVE", "INITIAL_QUESTION", "REQUEST_PRACTICE"):
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
            "initial_problem": "initial_problem",
            "validate_attempt": "validate_attempt",
            "request_hint": "request_hint",
            "navigate_step": "navigate_step",
            "clarify": "clarify"
        }
    )

    builder.add_edge("deflect", "compile_response")
    builder.add_edge("initial_problem", "compile_response")
    builder.add_edge("validate_attempt", "compile_response")
    builder.add_edge("request_hint", "compile_response")
    builder.add_edge("navigate_step", "compile_response")
    builder.add_edge("clarify", "compile_response")
    builder.add_edge("compile_response", END)

    cp = checkpointer if checkpointer is not None else MemorySaver()
    return builder.compile(checkpointer=cp)


socratic_graph = build_socratic_graph()
