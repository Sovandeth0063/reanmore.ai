"""
Unit tests for Component 1: 4-Part Socratic Card & Stepper Serializer.
Validates Pydantic models, JSON serialization, Markdown generation, and Prompt Controllers.
"""

import os
import sys
import json
# pyrefly: ignore [missing-import]
import pytest

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

# pyrefly: ignore [missing-import]
from app.services.socratic.card_schema import (
    SocraticStep,
    StepWidgetPayload,
    SocraticResponse,
)
# pyrefly: ignore [missing-import]
from app.services.socratic.prompts.controller import (
    socratic_prompt_controller,
)


class TestSocraticCardSchema:
    """Test SocraticStep Pydantic model and markdown rendering."""

    def test_socratic_step_creation_and_markdown(self):
        step = SocraticStep(
            step_number=1,
            title="Identify starting items",
            status="in_progress",
            mission="Let's find how many apples Leo started with!",
            clue="Check the opening sentence of the story.",
            helpful_example="🍪🍪🍪🍪🍪🍪🍪🍪🍪🍪 (Maya started with 10 cookies)",
            your_turn="What is the starting number of apples Leo has in his basket?",
            expected_answer="12",
            hints=[
                "Look at the first number in the story.",
                "Count: Leo has a dozen apples.",
                "The number is 12."
            ]
        )

        assert step.step_number == 1
        assert step.status == "in_progress"
        assert step.student_answer is None

        # Render basic Markdown
        md = step.to_markdown()
        assert "🌟 **Our Mission:** Let's find how many apples Leo started with!" in md
        assert "💡 **Clue:** Check the opening sentence of the story." in md
        assert "🍎 **Helpful Picture / Example:**" in md
        assert "> 🍪🍪🍪🍪🍪🍪🍪🍪🍪🍪 (Maya started with 10 cookies)" in md
        assert "👉 **Your Turn:**" in md
        assert "What is the starting number of apples Leo has in his basket?" in md
        assert "💡 **Hint" not in md

        # Render with progressive hint level 2
        step.current_hint_level = 2
        md_with_hint = step.to_markdown()
        assert "💡 **Hint (2/3):** Count: Leo has a dozen apples." in md_with_hint


class TestStepWidgetPayload:
    """Test multi-step state management, step advance, jump, and overview mode."""

    @pytest.fixture
    def sample_payload(self):
        steps = [
            SocraticStep(
                step_number=1,
                title="Find total apples",
                status="in_progress",
                mission="Find starting total",
                clue="Look at sentence 1",
                helpful_example="Maya has 10 cookies",
                your_turn="How many apples does Leo have?",
                expected_answer="12"
            ),
            SocraticStep(
                step_number=2,
                title="Subtract eaten apples",
                status="pending",
                mission="Take away 4 apples",
                clue="Subtraction means taking away",
                helpful_example="10 - 2 = 8 cookies",
                your_turn="12 minus 4 is how many?",
                expected_answer="8"
            ),
            SocraticStep(
                step_number=3,
                title="Divide into boxes",
                status="pending",
                mission="Split into 2 boxes",
                clue="Divide by 2",
                helpful_example="8 / 2 = 4 in each jar",
                your_turn="What is 8 divided by 2?",
                expected_answer="4"
            )
        ]
        return StepWidgetPayload(
            total_steps=3,
            current_step_index=0,
            completed_steps=[],
            steps=steps
        )

    def test_get_active_step(self, sample_payload):
        active = sample_payload.get_active_step()
        assert active is not None
        assert active.step_number == 1

    def test_step_progression(self, sample_payload):
        # Advance from step 1 to step 2
        advanced = sample_payload.advance_step(recorded_answer="12")
        assert advanced is True
        assert sample_payload.current_step_index == 1
        assert 0 in sample_payload.completed_steps
        assert sample_payload.steps[0].status == "completed"
        assert sample_payload.steps[0].student_answer == "12"
        assert sample_payload.steps[1].status == "in_progress"

        # Advance from step 2 to step 3
        advanced2 = sample_payload.advance_step(recorded_answer="8")
        assert advanced2 is True
        assert sample_payload.current_step_index == 2
        assert sample_payload.steps[1].status == "completed"

        # Advance from step 3 (final)
        advanced3 = sample_payload.advance_step(recorded_answer="4")
        assert advanced3 is False
        assert sample_payload.steps[2].status == "completed"

    def test_jump_to_step(self, sample_payload):
        jumped = sample_payload.jump_to_step(1)
        assert jumped is True
        assert sample_payload.current_step_index == 1
        assert sample_payload.steps[1].status == "in_progress"

        invalid_jump = sample_payload.jump_to_step(10)
        assert invalid_jump is False

    def test_to_overview_markdown(self, sample_payload):
        sample_payload.steps[0].status = "completed"
        sample_payload.steps[0].student_answer = "12"
        sample_payload.current_step_index = 1
        sample_payload.steps[1].status = "in_progress"

        overview = sample_payload.to_overview_markdown()
        assert "📋 **Full Solution Journey (Overview Mode)**" in overview
        assert "✅ **Step 1: Find total apples**" in overview
        assert "🔄 **Step 2: Subtract eaten apples**" in overview
        assert "⏳ **Step 3: Divide into boxes**" in overview
        # Ensure 'Your Turn' is NOT present in overview mode
        assert "👉 **Your Turn:**" not in overview


class TestSocraticResponse:
    """Test SocraticResponse factory, frontend schema spec conformance, and dual payload."""

    def test_from_step_widget_factory(self):
        step = SocraticStep(
            step_number=1,
            title="Step 1",
            status="in_progress",
            mission="Mission 1",
            clue="Clue 1",
            helpful_example="Example 1",
            your_turn="Question 1"
        )
        widget = StepWidgetPayload(
            total_steps=1,
            current_step_index=0,
            completed_steps=[],
            steps=[step]
        )

        response = SocraticResponse.from_step_widget(
            session_id="sess_test_123",
            widget=widget,
            feedback_message="Awesome start! 🌟"
        )

        assert response.session_id == "sess_test_123"
        assert response.step_widget.total_steps == 1
        assert "Awesome start! 🌟" in response.formatted_markdown
        assert "🌟 **Our Mission:** Mission 1" in response.formatted_markdown
        assert "👉 **Your Turn:**" in response.formatted_markdown

    def test_stepper_widget_specification_conformance(self):
        """
        Validates 100% field-by-field compatibility with stepper_widget_specification.md (Section 7).
        Ensures the Frontend Stepper component can render directly from this payload without adaptation.
        """
        step1 = SocraticStep(
            step_number=1,
            title="Starting Apples",
            status="completed",
            mission="Find how many apples Leo started with!",
            clue="Look at the very first sentence of the story.",
            helpful_example="🍪🍪🍪🍪🍪🍪🍪🍪🍪🍪 (Maya starts with 10 cookies)",
            your_turn="What is the total number of apples Leo has at the beginning?",
            student_answer="12",
            hints=[
                "Look at the first number in the story problem.",
                "Count: Leo has one dozen (12) apples in his basket."
            ],
            current_hint_level=0
        )
        step2 = SocraticStep(
            step_number=2,
            title="Subtract Given Away",
            status="in_progress",
            mission="Let's take away the apples Leo gives to his sister!",
            clue="'Gives away' means subtraction (-).",
            helpful_example="🍪🍪🍪🍪🍪🍪🍪🍪🍪🍪 (10) take away 🍪🍪 (2) = 🍪🍪🍪🍪🍪🍪🍪🍪 (8)",
            your_turn="Leo started with 12 apples and gives away 4. How many are left?",
            student_answer=None,
            hints=[
                "Try counting backwards 4 steps starting from 12: 11, 10, 9, ...?",
                "🍏🍏🍏🍏🍏🍏🍏🍏 ❌❌❌❌ (We crossed out 4 apples. Count the green 🍏 left!)",
                "Let's do two smaller steps: 12 - 2 = 10, then what is 10 - 2?"
            ],
            current_hint_level=2
        )

        widget = StepWidgetPayload(
            total_steps=4,
            current_step_index=1,
            completed_steps=[0],
            steps=[step1, step2]
        )

        response = SocraticResponse.from_step_widget(
            session_id="sess_12345",
            widget=widget
        )

        dumped = response.model_dump()

        # Top-level checks
        assert dumped["session_id"] == "sess_12345"
        assert "step_widget" in dumped
        assert "formatted_markdown" in dumped

        # step_widget checks
        sw = dumped["step_widget"]
        assert sw["total_steps"] == 4
        assert sw["current_step_index"] == 1
        assert sw["completed_steps"] == [0]
        assert len(sw["steps"]) == 2

        # Step 1 field checks
        s1 = sw["steps"][0]
        assert s1["step_number"] == 1
        assert s1["title"] == "Starting Apples"
        assert s1["status"] == "completed"
        assert s1["mission"] == "Find how many apples Leo started with!"
        assert s1["clue"] == "Look at the very first sentence of the story."
        assert s1["helpful_example"] == "🍪🍪🍪🍪🍪🍪🍪🍪🍪🍪 (Maya starts with 10 cookies)"
        assert s1["your_turn"] == "What is the total number of apples Leo has at the beginning?"
        assert s1["student_answer"] == "12"
        assert len(s1["hints"]) == 2
        assert s1["current_hint_level"] == 0

        # Step 2 field checks
        s2 = sw["steps"][1]
        assert s2["step_number"] == 2
        assert s2["title"] == "Subtract Given Away"
        assert s2["status"] == "in_progress"
        assert s2["mission"] == "Let's take away the apples Leo gives to his sister!"
        assert s2["clue"] == "'Gives away' means subtraction (-)."
        assert s2["your_turn"] == "Leo started with 12 apples and gives away 4. How many are left?"
        assert s2["student_answer"] is None
        assert len(s2["hints"]) == 3
        assert s2["current_hint_level"] == 2

        # Verify JSON serializability
        json_str = response.model_dump_json()
        assert json_str is not None
        parsed_json = json.loads(json_str)
        assert parsed_json["session_id"] == "sess_12345"


class TestSocraticPromptController:
    """Test prompt builder methods and JSON extraction parsing."""

    def test_prompt_builders(self):
        controller = socratic_prompt_controller
        card_prompt = controller.get_step_card_prompt(
            homework_problem="Leo has 8 apples",
            step_number=1,
            total_steps=2,
            step_title="Identify starting amount"
        )
        assert "Grade 1-3" in card_prompt
        assert "Leo has 8 apples" in card_prompt
        assert "🌟 Mission" in card_prompt

        parallel_prompt = controller.get_parallel_example_prompt("Leo has 8 apples")
        assert "PARALLEL ISOMORPHIC EXAMPLE" in parallel_prompt
        assert "Leo has 8 apples" in parallel_prompt

        hint_prompt = controller.get_progressive_hint_prompt(
            step_mission="Subtract 3 apples",
            your_turn_question="What is 8 - 3?",
            hint_tier=2
        )
        assert "Tier 2 of 3" in hint_prompt

        feedback_prompt = controller.get_socratic_feedback_prompt(
            step_number=1,
            student_attempt="5",
            is_correct=True
        )
        assert "Is Correct: True" in feedback_prompt

    def test_parse_socratic_card_json_resilience(self):
        controller = socratic_prompt_controller
        raw_llm_json = """
        Here is the 4-part card:
        ```json
        {
          "mission": "Let's subtract the given cookies!",
          "clue": "Taking away means minus.",
          "helpful_example": "🍪🍪🍪 (3) - 🍪 (1) = 🍪🍪 (2)",
          "your_turn": "If you have 5 cookies and give 2, how many are left?"
        }
        ```
        """
        step = controller.parse_socratic_card(
            llm_output=raw_llm_json,
            step_number=2,
            title="Subtract Cookies"
        )
        assert step.step_number == 2
        assert step.title == "Subtract Cookies"
        assert step.mission == "Let's subtract the given cookies!"
        assert step.clue == "Taking away means minus."
        assert "🍪" in step.helpful_example
        assert "5 cookies" in step.your_turn

    def test_dynamic_translation_prompts(self):
        controller = socratic_prompt_controller
        to_km = controller.get_translation_to_khmer_prompt("What is 5 + 3?")
        assert "Cambodian primary school educational translator" in to_km
        assert "What is 5 + 3?" in to_km

        sys_p, usr_p = controller.get_translation_prompt("Photosynthesis is green", target_lang="km")
        assert "Cambodian primary school educational translator" in sys_p
        assert "Photosynthesis is green" in usr_p

    def test_dynamic_contextual_explanation_prompt(self):
        controller = socratic_prompt_controller
        sys_p, usr_p = controller.get_contextual_explanation_prompt(
            query="why is the sun hot?",
            exercise_context="Solar system unit",
            current_step_question="What is the center of the solar system?",
            grade_level="grade_1_3"
        )
        assert "ReanMore" in sys_p
        assert "Solar system unit" in usr_p
        assert "why is the sun hot?" in usr_p

    def test_dynamic_answer_evaluation_prompt(self):
        controller = socratic_prompt_controller
        sys_p, usr_p = controller.get_answer_evaluation_prompt(
            step_question="What is 4 + 4?",
            expected_answer="8",
            student_attempt="eight",
            grade_level="grade_1_3"
        )
        assert "ReanMore" in sys_p
        assert "What is 4 + 4?" in usr_p
        assert "eight" in usr_p

    def test_dynamic_rolling_summary_prompt(self):
        controller = socratic_prompt_controller
        res = controller.get_rolling_summary_prompt("Previous summary", "Student: Hi | Tutor: Hello")
        assert "summarization assistant" in res
        assert "Previous summary" in res

    def test_dynamic_grade_adapted_system_prompt(self):
        controller = socratic_prompt_controller
        prompt_km = controller.get_grade_adapted_system_prompt(grade=2, language="km")
        assert "ReanMore" in prompt_km
        assert "កុមារថ្នាក់ទី ១–២" in prompt_km

        prompt_en = controller.get_grade_adapted_system_prompt(grade=4, language="en")
        assert "ReanMore" in prompt_en
        assert "Grade 3-4" in prompt_en

    def test_dynamic_coreference_rewrite_prompt(self):
        controller = socratic_prompt_controller
        res = controller.get_coreference_rewrite_prompt(
            context_str="Step 1: 5 + 3 = 8",
            norm="what is it?"
        )
        assert "coreference rewriter" in res
        assert "what is it?" in res


if __name__ == "__main__":
    pytest.main(["-v", __file__])
