"""
File: orchestrator/app/services/socratic/skills/sub_within_20.py
Description: Skill template for subtraction within 20 using 'Count back to 10'.
             Target: Grades 1-2 | Visual Model: number_line
"""

from typing import Dict, Any, List
from fractions import Fraction
from app.services.socratic.skills.base import Skill, StepTemplate, skill_registry


class SubWithin20Skill:
    skill_id: str = "sub_within_20"
    grade_band: str = "grade_1_3"

    def matches(self, problem: Dict[str, Any]) -> bool:
        if problem.get("is_word_problem") or problem.get("type") == "word_problem":
            return False
        if problem.get("op") != "-":
            return False
        a = problem.get("a")
        b = problem.get("b")
        if a is None or b is None:
            return False
        if float(a).is_integer() and float(b).is_integer():
            a_int = int(a)
            b_int = int(b)
            return (10 < a_int <= 20 and 0 < b_int < 10 and a_int > b_int)
        return False

    def make_distinct_example(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        a = int(problem.get("a", 14))
        b = int(problem.get("b", 6))
        to_ten = a - 10
        rem = b - to_ten
        ans = a - b
        forbidden = {a, b, ans, to_ten, rem, 10}

        # Search candidates in [11..19] x [2..9] requiring regrouping across 10
        for ex_a in range(11, 20):
            ex_to_ten = ex_a - 10
            for ex_b in range(ex_to_ten + 1, 10):
                ex_rem = ex_b - ex_to_ten
                ex_ans = ex_a - ex_b
                candidate_vals = {ex_a, ex_b, ex_ans, ex_to_ten, ex_rem, 10 - ex_rem}
                if candidate_vals.isdisjoint(forbidden):
                    return {
                        "a": ex_a,
                        "b": ex_b,
                        "to_ten": ex_to_ten,
                        "rem": ex_rem,
                        "ans": ex_ans
                    }

        # Dynamic fallback outside 20 if all 1-20 pairs collide
        offset_a = a + 11
        offset_b = b + 1
        return {
            "a": offset_a,
            "b": offset_b,
            "to_ten": offset_a % 10 or 1,
            "rem": offset_b - (offset_a % 10 or 1),
            "ans": offset_a - offset_b
        }

    def build_steps(self, problem: Dict[str, Any]) -> List[StepTemplate]:
        a = int(problem.get("a", 14))
        b = int(problem.get("b", 6))

        to_ten = a - 10
        rem = b - to_ten
        final_ans = a - b
        ex = self.make_distinct_example(problem)

        step1 = StepTemplate(
            step_number=1,
            title="Hop Back to 10",
            mission=f"Let's hop back on our number line from {a} to land on 10!",
            clue=f"Landing on friendly numbers like 10 makes subtracting easy. How many do you take away from {a} to get to 10?",
            helpful_example=(
                f"For {ex['a']} - {ex['b']}: Starting at {ex['a']}, we hop back {ex['to_ten']} to land on 10. "
                f"({ex['a']} - {ex['to_ten']} = 10)."
            ),
            your_turn=f"How many hops back from {a} to reach 10?",
            expected_answer=str(to_ten),
            concept="hop_back_to_ten",
            visual_spec={
                "type": "number_line",
                "mode": "current",
                "params": {"start": a, "step": -1, "hops": []},
                "labels": [f"Start at {a}", "Hop back to land on 10"],
                "alt_text": f"Number line starting at {a} to hop back to 10."
            },
            hints=[
                f"Look at the ones digit of {a}. Taking away just that ones digit leaves 10!",
                f"Count down from {a} until you hit 10.",
                f"In our example: {ex['a']} hops back {ex['to_ten']}. For your problem: how many do you subtract from {a} to reach 10?"
            ]
        )

        if rem == final_ans:
            s2_your_turn = "Subtract the rest of the hops from 10. Where do you land?"
            s2_labels = ["Start at 10", "Hop back remaining steps"]
            s2_hints = [
                "Think of 10 fingers. Put down the remaining fingers. How many are up?",
                "Count backwards from 10 by the remaining steps.",
                f"In our example: taking away {ex['rem']} leaves {ex['ans']}. For your problem: take your remaining hops from 10."
            ]
        else:
            s2_your_turn = f"Subtract the remaining {rem} hops from 10. Where do you land?"
            s2_labels = ["Start at 10", f"Hop back {rem} more"]
            s2_hints = [
                f"Think of your 10 fingers. Put down {rem} fingers. How many are still up?",
                f"Count backwards {rem} steps from 10.",
                f"In our example: taking away {ex['rem']} leaves {ex['ans']}. For your problem: take {rem} away from 10."
            ]

        step2 = StepTemplate(
            step_number=2,
            title="Subtract the Remaining Hops",
            mission="Now subtract the rest of our hops from 10!",
            clue=f"We needed to subtract {b} in all. We already subtracted {to_ten}. Now subtract the remaining hops.",
            helpful_example=(
                f"For {ex['a']} - {ex['b']}: We needed {ex['b']} hops. We already did {ex['to_ten']}, "
                f"so {ex['rem']} hops are left, giving {ex['ans']}!"
            ),
            your_turn=s2_your_turn,
            expected_answer=str(final_ans),
            concept="subtract_from_ten",
            visual_spec={
                "type": "number_line",
                "mode": "current",
                "params": {"start": 10, "step": -1, "hops": []},
                "labels": s2_labels,
                "alt_text": "Number line from 10 hopping back remaining steps."
            },
            hints=s2_hints
        )

        return [step1, step2]


# Register skill
skill_registry.register(SubWithin20Skill())
