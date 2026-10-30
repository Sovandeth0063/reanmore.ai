"""
File: testing/test_socratic_state.py
Description: Unit and integration tests for Part 2 (LangGraph StateGraph, TutorState,
             and 3-Tier Progressive Hint Engine).
"""

# pyrefly: ignore [missing-import]
import pytest
import os
import sys

# Ensure repo root and orchestrator are on sys.path
def _find_repo_root():
    cur = os.path.abspath(os.path.dirname(__file__))
    while cur and not os.path.exists(os.path.join(cur, "orchestrator")):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return cur

BASE_DIR = _find_repo_root()
ORCHESTRATOR_DIR = os.path.join(BASE_DIR, "orchestrator")
for _p in (BASE_DIR, ORCHESTRATOR_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orchestrator")))

# pyrefly: ignore [missing-import]
from app.services.socratic.card_schema import SocraticStep, StepWidgetPayload
# pyrefly: ignore [missing-import]
from app.services.socratic.state import TutorState
# pyrefly: ignore [missing-import]
from app.services.socratic.hint_engine import HintEngine
# pyrefly: ignore [missing-import]
from app.services.socratic.clarify import SocraticClarifier
# pyrefly: ignore [missing-import]
from app.services.socratic.graph import build_socratic_graph, _is_answer_equivalent
# pyrefly: ignore [missing-import]
from app.services.nlu.schema import StudentIntent
from langgraph.checkpoint.memory import MemorySaver


@pytest.fixture
def hint_engine():
    return HintEngine()


@pytest.fixture
def offline_hint_engine(hint_engine, monkeypatch):
    """Unit tests must not call Gemini.

    Simulating an unavailable model exercises the deterministic, content-derived
    fallback so hint-tier and zero-leakage behaviour stays reproducible.
    """
    monkeypatch.setattr(
        hint_engine.prompt_controller, "_call_gemini_llm", lambda _prompt: ""
    )
    return hint_engine


@pytest.fixture
def sample_step():
    return SocraticStep(
        step_number=1,
        title="Find how many apples were eaten",
        status="in_progress",
        mission="Find how many apples Leo ate.",
        clue="Subtract the eaten apples from the starting total.",
        helpful_example="Maya had 10 cookies and gave 3 to Sam. 10 - 3 = 7 cookies left.",
        your_turn="Leo had 12 apples and ate 4. How many apples are left?",
        expected_answer="8",
        concept="subtraction"
    )


def test_is_answer_equivalent():
    assert _is_answer_equivalent("8", "8") is True
    assert _is_answer_equivalent("8 apples", "8") is True
    assert _is_answer_equivalent("eight", "8") is True
    assert _is_answer_equivalent("9", "8") is False


def test_hint_engine_three_tiers(offline_hint_engine, sample_step):
    # Tier 1: Guiding Nudge
    tier_1, hint_1 = offline_hint_engine.escalate_hint(sample_step, grade_level="grade_1_3")
    assert tier_1 == 1
    assert "👀" in hint_1 or "clue" in hint_1.lower()
    assert "8" not in hint_1  # Zero answer leakage

    # Tier 2: Visual Scaffold
    tier_2, hint_2 = offline_hint_engine.escalate_hint(sample_step, grade_level="grade_1_3")
    assert tier_2 == 2
    assert "🎨" in hint_2 or "🍎" in hint_2
    assert "8" not in hint_2  # Zero answer leakage

    # Tier 3: Worked Parallel Example
    tier_3, hint_3 = offline_hint_engine.escalate_hint(sample_step, grade_level="grade_1_3")
    assert tier_3 == 3
    assert "🧩" in hint_3 or "parallel" in hint_3.lower() or "micro-step" in hint_3.lower()
    assert "8" not in hint_3  # Zero answer leakage in Tier 3

    # Capped at Tier 3
    tier_4, hint_4 = offline_hint_engine.escalate_hint(sample_step, grade_level="grade_1_3")
    assert tier_4 == 3


def test_hint_engine_uses_llm_hint(hint_engine, monkeypatch, sample_step):
    """The LLM prompt is the sole source of hint content in production."""
    monkeypatch.setattr(
        hint_engine.prompt_controller,
        "_call_gemini_llm",
        lambda _prompt: "Look at the clue and decide if the group grows or shrinks.",
    )
    hint = hint_engine.generate_hint(sample_step, tier=1, grade_level="grade_1_3")
    assert hint == "Look at the clue and decide if the group grows or shrinks."


def test_escalate_hint_sanitizes_cached_leak(offline_hint_engine, sample_step):
    """Pre-computed step hints are LLM content too and must pass the leak guard."""
    sample_step.hints = [
        "The answer is 8 apples.",
        "8 is the number you need.",
        "Just write 8.",
    ]
    tier, hint = offline_hint_engine.escalate_hint(sample_step, grade_level="grade_1_3")
    assert tier == 1
    assert "8" not in hint


def test_hint_engine_sanitizes_llm_answer_leak(hint_engine, monkeypatch, sample_step):
    """A leaking LLM hint is quarantined by the zero-leakage guard."""
    monkeypatch.setattr(
        hint_engine.prompt_controller,
        "_call_gemini_llm",
        lambda _prompt: "The answer is 8 apples.",
    )
    hint = hint_engine.generate_hint(sample_step, tier=1, grade_level="grade_1_3")
    assert "8" not in hint


def test_hint_engine_zero_leakage_across_science_topics(offline_hint_engine):
    topics = [
        ("What process happens when water boils into steam?", "Evaporation",
         "Watch what happens to water when it is heated"),
        ("What happens to an ice cube on a hot day?", "Melting",
         "Watch an ice cube on a warm table"),
        ("What force pulls an apple down to Earth?", "Gravity",
         "Watch an apple fall from a tree"),
        ("How do green plants use sunlight to make food?", "Photosynthesis",
         "See how a green plant makes its own food"),
        ("What baby animal hatches from a frog egg?", "Tadpole",
         "Watch a frog egg grow in the pond"),
        ("What action occurs between opposite magnetic poles?", "Attract",
         "Put two opposite magnetic poles near each other"),
    ]

    for question, expected, mission in topics:
        for tier in (1, 2, 3):
            step = SocraticStep(
                step_number=1,
                title=mission,
                status="in_progress",
                mission=mission,
                clue="Think about what you can observe, not the name of the idea.",
                helpful_example="Think of a similar situation in daily life.",
                your_turn=question,
                expected_answer=expected,
                concept="science"
            )
            hint = offline_hint_engine.generate_hint(step, tier=tier, grade_level="grade_1_3")
            assert expected.lower() not in hint.lower(), (
                f"Leak detected in Tier {tier} for expected '{expected}': {hint}"
            )



def test_clarifier_preserves_context(sample_step):
    widget = StepWidgetPayload(
        total_steps=1,
        current_step_index=0,
        completed_steps=[],
        steps=[sample_step]
    )
    res = SocraticClarifier.build_clarification_response("huh?", widget=widget)
    assert res["clarification_needed"] is True
    assert "Step 1" in res["clarification_question"]


async def test_graph_initial_problem():
    graph = build_socratic_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "test_session_1"}}

    state_input: TutorState = {
        "session_id": "test_session_1",
        "raw_user_input": "Leo had 12 apples and ate 4. How many apples are left?",
        "detected_intent": StudentIntent.INITIAL_QUESTION.value,
        "grade_level": "grade_1_3"
    }

    result = await graph.ainvoke(state_input, config=config)
    assert "step_widget" in result
    assert result["current_step_index"] == 0
    assert result["total_steps_count"] >= 2
    assert "🌟 **Our Mission:**" in result["formatted_markdown"]


async def test_graph_step_answer_and_advancement():
    graph = build_socratic_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "test_session_2"}}

    # 1. Start problem
    start_state: TutorState = {
        "session_id": "test_session_2",
        "raw_user_input": "Leo had 12 apples and ate 4. How many apples are left?",
        "detected_intent": StudentIntent.INITIAL_QUESTION.value
    }
    r1 = await graph.ainvoke(start_state, config=config)

    # 2. Submit wrong answer
    wrong_state: TutorState = {
        **r1,
        "raw_user_input": "5",
        "student_attempt": "5",
        "detected_intent": StudentIntent.STEP_ANSWER_ATTEMPT.value
    }
    r2 = await graph.ainvoke(wrong_state, config=config)
    assert r2["current_hint_tier"] == 1
    assert r2["active_hint"] is not None
    assert r2["is_problem_complete"] is False

    # 3. Submit correct answer for step 1
    widget = StepWidgetPayload.model_validate(r2["step_widget"])
    expected_ans = widget.get_active_step().expected_answer or "8"

    correct_state: TutorState = {
        **r2,
        "raw_user_input": expected_ans,
        "student_attempt": expected_ans,
        "detected_intent": StudentIntent.STEP_ANSWER_ATTEMPT.value
    }
    r3 = await graph.ainvoke(correct_state, config=config)
    assert "Spot on!" in r3["feedback_message"]
    assert r3["current_step_index"] == 1


async def test_graph_explicit_hint_request(stub_socratic_llm):
    graph = build_socratic_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "test_session_3"}}

    # Start problem
    r1 = await graph.ainvoke({
        "session_id": "test_session_3",
        "raw_user_input": "How many states of matter are there?",
        "detected_intent": StudentIntent.INITIAL_QUESTION.value
    }, config=config)

    # Ask for hint
    r2 = await graph.ainvoke({
        **r1,
        "raw_user_input": "give me a hint",
        "detected_intent": StudentIntent.REQUEST_HINT.value
    }, config=config)

    assert r2["current_hint_tier"] == 1
    assert r2["active_hint"] is not None


async def test_graph_navigation_jump():
    graph = build_socratic_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "test_session_4"}}

    # Start problem
    r1 = await graph.ainvoke({
        "session_id": "test_session_4",
        "raw_user_input": "Leo had 12 apples and ate 4. How many apples are left?",
        "detected_intent": StudentIntent.INITIAL_QUESTION.value
    }, config=config)

    # Jump to Step index 1
    r2 = await graph.ainvoke({
        **r1,
        "raw_user_input": "goto step 2",
        "detected_intent": "NAVIGATION_JUMP",
        "target_nav_index": 1
    }, config=config)

    assert r2["current_step_index"] == 1
    assert "Navigated to Step 2" in r2["feedback_message"]


async def test_graph_new_problem_during_active_session(stub_socratic_llm):
    """Verify that asking a new problem cleanly switches problems and resets step index."""
    graph = build_socratic_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "test_session_switch"}}

    # 1. Start initial problem (e.g. Leo had 12 apples)
    r1 = await graph.ainvoke({
        "session_id": "test_session_switch",
        "raw_user_input": "Leo had 12 apples and ate 4. How many apples are left?",
        "detected_intent": StudentIntent.INITIAL_QUESTION.value
    }, config=config)
    assert r1["current_step_index"] == 0

    # 2. Advance to step 2
    r2 = await graph.ainvoke({
        **r1,
        "raw_user_input": "goto step 2",
        "detected_intent": "NAVIGATION_JUMP",
        "target_nav_index": 1
    }, config=config)
    assert r2["current_step_index"] == 1

    # 3. User switches to a new problem: "What comes after 19?"
    r3 = await graph.ainvoke({
        **r2,
        "raw_user_input": "What comes after 19?",
        "problem_text": "What comes after 19?",
        "detected_intent": StudentIntent.INITIAL_QUESTION.value,
        "current_step_index": 0,
        "step_widget": None
    }, config=config)

    assert r3["current_step_index"] == 0
    assert r3["is_problem_complete"] is False
    assert "step_widget" in r3
    assert r3["step_widget"] is not None


def test_route_by_intent_aliases():
    """Verify route_by_intent handles both StudentIntent values and IntentType string aliases."""
    # pyrefly: ignore [missing-import]
    from app.services.socratic.graph import route_by_intent

    # Step attempt aliases now route through classify_intent (Sprint 1.4)
    assert route_by_intent({"detected_intent": "STEP_ANSWER_ATTEMPT"}) == "classify_intent"
    assert route_by_intent({"detected_intent": "STEP_ATTEMPT"}) == "classify_intent"

    # Initial problem aliases
    assert route_by_intent({"detected_intent": "INITIAL_QUESTION"}) == "initial_problem"
    assert route_by_intent({"detected_intent": "INITIAL_SOLVE"}) == "initial_problem"
    assert route_by_intent({"detected_intent": "REQUEST_PRACTICE"}) == "initial_problem"

    # Deflect & clarify aliases
    assert route_by_intent({"detected_intent": "OFF_TOPIC"}) == "deflect"
    assert route_by_intent({"detected_intent": "OFF_TOPIC_DEFLECTED"}) == "deflect"
    assert route_by_intent({"detected_intent": "CLARIFY"}) == "clarify"
    assert route_by_intent({"detected_intent": "REQUEST_CLARIFICATION"}) == "clarify"
