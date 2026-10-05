"""
File: testing/test_guardrails.py
Description: Exhaustive test suite for Part 4 (Child Safety Guardrails & Educational Scope Deflector).
             Tests PII redaction, inappropriate filtering, gaming/pop-culture deflection,
             context-aware active step bridging, and LangGraph integration.
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
from app.services.guardrails.safety_filter import SafetyFilter, SafetyCategory
# pyrefly: ignore [missing-import]
from app.services.guardrails.educational_scope import EducationalScopeDeflector, OffTopicCategory
# pyrefly: ignore [missing-import]
from app.services.socratic.card_schema import SocraticStep, StepWidgetPayload
# pyrefly: ignore [missing-import]
from app.services.socratic.graph import build_socratic_graph
from langgraph.checkpoint.memory import MemorySaver


@pytest.fixture
def safety_filter():
    return SafetyFilter()


@pytest.fixture
def scope_deflector():
    return EducationalScopeDeflector()


@pytest.fixture
def sample_active_step():
    return SocraticStep(
        step_number=2,
        title="Count Remaining Apples",
        status="in_progress",
        mission="Subtract 3 eaten apples from 10.",
        clue="Subtract: 10 - 3.",
        helpful_example="10 - 2 = 8.",
        your_turn="If you have 10 apples and eat 3, how many apples are left?",
        expected_answer="7",
        concept="subtraction"
    )


# -------------------------------------------------------------------------
# 1. PII Redaction Tests
# -------------------------------------------------------------------------

def test_redact_phone_number(safety_filter):
    text = "Call me at 555-123-4567 to do my math"
    clean, found = safety_filter.redact_pii(text)
    assert found is True
    assert "[PHONE_REDACTED]" in clean
    assert "555-123-4567" not in clean


def test_redact_email_address(safety_filter):
    text = "Send the answer to student@school.org please"
    clean, found = safety_filter.redact_pii(text)
    assert found is True
    assert "[EMAIL_REDACTED]" in clean
    assert "student@school.org" not in clean


def test_redact_physical_address(safety_filter):
    text = "I live at 742 Evergreen Terrace and need help"
    clean, found = safety_filter.redact_pii(text)
    assert found is True
    assert "[ADDRESS_REDACTED]" in clean


def test_pii_preserves_homework_problem(safety_filter):
    text = "My phone is (555) 987-6543 and Leo has 12 apples and eats 4."
    res = safety_filter.evaluate(text)
    assert res.is_safe is True
    assert res.has_pii is True
    assert "[PHONE_REDACTED]" in res.redacted_text
    assert "Leo has 12 apples and eats 4" in res.redacted_text
    assert res.pii_notice is not None


# -------------------------------------------------------------------------
# 2. Inappropriate Content Tests
# -------------------------------------------------------------------------

def test_block_profanity(safety_filter):
    res = safety_filter.evaluate("What the hell is 5 + 5")
    assert res.is_safe is False
    assert SafetyCategory.PROFANITY in res.categories_detected
    assert "nice and kind words" in res.safe_response.lower()


def test_block_bullying(safety_filter):
    res = safety_filter.evaluate("You are stupid and ugly")
    assert res.is_safe is False
    assert SafetyCategory.BULLYING in res.categories_detected
    assert "kind words" in res.safe_response.lower()


def test_crisis_self_harm_guidance(safety_filter):
    res = safety_filter.evaluate("I want to die")
    assert res.is_safe is False
    assert SafetyCategory.SELF_HARM in res.categories_detected
    assert "trusted adult" in res.safe_response.lower()


def test_block_violence(safety_filter):
    res = safety_filter.evaluate("I will shoot you with a gun")
    assert res.is_safe is False
    assert SafetyCategory.VIOLENCE in res.categories_detected
    assert any(term in res.safe_response.lower() for term in ["trusted adult", "police", "safe and friendly", "danger"])


# -------------------------------------------------------------------------
# 3. Educational Scope Deflection Tests
# -------------------------------------------------------------------------

def test_detect_gaming(scope_deflector):
    res = scope_deflector.check_scope("Do you want to play Roblox or Fortnite?")
    assert res.is_off_topic is True
    assert res.category == OffTopicCategory.GAMING


def test_detect_pop_culture(scope_deflector):
    res = scope_deflector.check_scope("Did you watch the new MrBeast YouTube video?")
    assert res.is_off_topic is True
    assert res.category == OffTopicCategory.POP_CULTURE


def test_detect_ai_persona(scope_deflector):
    res = scope_deflector.check_scope("Are you a real human person?")
    assert res.is_off_topic is True
    assert res.category == OffTopicCategory.AI_PERSONA


def test_deflection_without_active_problem(scope_deflector):
    msg = scope_deflector.build_deflection("Can we play Minecraft?", category=OffTopicCategory.GAMING)
    assert "Science and Math homework tutor" in msg
    assert "What homework problem should we work on together" in msg


def test_deflection_bridges_to_active_step(scope_deflector, sample_active_step):
    msg = scope_deflector.build_deflection(
        "Can we play Minecraft?",
        category=OffTopicCategory.GAMING,
        active_step=sample_active_step
    )
    assert "Video games are super exciting!" in msg
    assert "Step 2" in msg
    assert "If you have 10 apples and eat 3" in msg


# -------------------------------------------------------------------------
# 4. False-Positive Safety Checks
# -------------------------------------------------------------------------

def test_legitimate_stem_inputs_not_blocked(safety_filter, scope_deflector):
    valid_queries = [
        "What is 15 minus 7?",
        "Why do plant leaves turn green in the sun?",
        "Leo ate 4 cookies out of 10.",
        "Water turns into ice when it freezes.",
        "Gravity pulls the ball down to the ground."
    ]
    for query in valid_queries:
        safe_res = safety_filter.evaluate(query)
        assert safe_res.is_safe is True, f"Blocked valid query: {query}"
        scope_res = scope_deflector.check_scope(query)
        assert scope_res.is_off_topic is False, f"Deflected valid query: {query}"


# -------------------------------------------------------------------------
# 5. LangGraph End-to-End Integration
# -------------------------------------------------------------------------

def test_graph_deflects_gaming_query():
    graph = build_socratic_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "test_guardrail_deflect"}}

    state = {
        "raw_user_input": "Do you want to play Roblox with me?",
        "session_id": "test_guardrail_deflect"
    }

    result = graph.invoke(state, config=config)
    assert result["is_deflected"] is True
    assert "Roblox" not in result["feedback_message"] or "super exciting" in result["feedback_message"]
    assert "Science and Math" in result["formatted_markdown"] or "homework" in result["formatted_markdown"]


def test_graph_blocks_unsafe_profanity():
    graph = build_socratic_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "test_guardrail_profanity"}}

    state = {
        "raw_user_input": "What the hell is 2 + 2",
        "session_id": "test_guardrail_profanity"
    }

    result = graph.invoke(state, config=config)
    assert result["is_safe"] is False
    assert "nice and kind words" in result["formatted_markdown"].lower()


def test_graph_redirects_pure_pii():
    graph = build_socratic_graph(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "test_guardrail_pure_pii"}}

    state = {
        "raw_user_input": "Call me at 555-123-4567 please",
        "session_id": "test_guardrail_pure_pii"
    }

    result = graph.invoke(state, config=config)
    assert result["is_safe"] is True
    assert result["has_pii"] is True
    assert result["is_deflected"] is True
    assert "Privacy Tip" in result["formatted_markdown"]
