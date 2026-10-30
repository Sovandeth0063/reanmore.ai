"""
File: orchestrator/app/services/socratic/skills/add_within_20.py
Description: Skill template for addition within 20 using the 'Make a Ten' strategy.
             Target: Grades 1-2 | Visual Model: ten_frame
"""

from typing import Dict, Any, List
from fractions import Fraction
from app.services.socratic.skills.base import Skill, StepTemplate, skill_registry


class AddWithin20Skill:
    skill_id: str = "add_within_20"
    grade_band: str = "grade_1_3"

    def matches(self, problem: Dict[str, Any]) -> bool:
        if problem.get("is_word_problem") or problem.get("type") == "word_problem":
            return False
        if problem.get("op") != "+":
            return False
        a = problem.get("a")
        b = problem.get("b")
        if a is None or b is None:
            return False
        if not (isinstance(a, (int, Fraction)) and isinstance(b, (int, Fraction))):
            return False
        if float(a).is_integer() and float(b).is_integer():
            a_int = int(a)
            b_int = int(b)
            # Only use 'make a ten' when the sum really crosses ten.
            # Simpler sums (e.g. 2 + 2) are handled by add_within_10.
            return (a_int > 0 and b_int > 0 and 10 < (a_int + b_int) <= 20)
        return False

    def make_distinct_example(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        a = int(problem.get("a", 8))
        b = int(problem.get("b", 6))
        if a < b:
            a, b = b, a
        total = a + b
        need = 10 - a
        prob_nums = {a, b, total}
        targets = {need, total}

        # Search candidates in descending order of a
        for cand_a in [9, 8, 7, 6]:
            cand_need = 10 - cand_a
            for cand_b in range(cand_need + 1, 10):
                cand_rem = cand_b - cand_need
                cand_sum = cand_a + cand_b
                cand_prob_nums = {cand_a, cand_b, cand_sum}
                cand_all = {cand_a, cand_b, cand_sum, cand_need, cand_rem}

                if not prob_nums.isdisjoint(cand_prob_nums):
                    continue
                if not targets.isdisjoint(cand_all):
                    continue
                return {
                    "a": cand_a,
                    "b": cand_b,
                    "need": cand_need,
                    "rem": cand_rem,
                    "sum": cand_sum
                }

        # Dynamic fallback if needed
        offset_a = a + 10
        offset_b = b + 1
        return {
            "a": offset_a,
            "b": offset_b,
            "need": 10 - (offset_a % 10 or 1),
            "rem": offset_b - (10 - (offset_a % 10 or 1)),
            "sum": offset_a + offset_b
        }

    def build_steps(self, problem: Dict[str, Any]) -> List[StepTemplate]:
        a = int(problem.get("a", 8))
        b = int(problem.get("b", 6))

        # Order so larger number is first
        if a < b:
            a, b = b, a

        need_for_ten = 10 - a
        remainder = b - need_for_ten
        final_sum = a + b
        ex = self.make_distinct_example(problem)

        step1 = StepTemplate(
            step_number=1,
            title="Make a Full Ten",
            mission=f"Let's make a full ten using our first group of {a}!",
            clue=f"When adding numbers near 10, fill up a ten-frame first. How many more does {a} need to reach 10?",
            helpful_example=(
                f"For {ex['a']} + {ex['b']}: {ex['a']} needs {ex['need']} more to make 10. "
                f"So we take {ex['need']} from {ex['b']}, leaving {ex['rem']}."
            ),
            your_turn=f"How many more does {a} need to make 10?",
            expected_answer=str(need_for_ten),
            concept="make_a_ten",
            visual_spec={
                "type": "ten_frame",
                "mode": "current",
                "params": {"frames": [{"filled": a}, {"filled": b}], "color": "apple"},
                "highlights": [{"from_frame": 1, "move": need_for_ten, "to_frame": 0}],
                "labels": [f"{a} apples", f"{b} more apples"],
                "alt_text": f"Two ten-frames showing {a} counters and {b} counters."
            },
            hints=[
                f"Count up from {a} to 10: {a}... how many more fingers?",
                f"Look at the first ten-frame with {a} dots. How many empty boxes are left to fill 10?",
                f"In our example: {ex['a']} needs {ex['need']}. For your problem: count how many more {a} needs to make 10."
            ]
        )

        step2 = StepTemplate(
            step_number=2,
            title="Add the Remaining Ones",
            mission="Now add the leftover ones to 10 to find our total!",
            clue=f"We took {need_for_ten} from {b}, leaving {remainder}. Adding leftover ones to 10 gives a teen number!",
            helpful_example=(
                f"For {ex['a']} + {ex['b']}: We made 10, and had {ex['rem']} left over. "
                f"10 + {ex['rem']} = {ex['sum']}!"
            ),
            your_turn=f"Add your {remainder} leftover ones to 10. What is the total sum?",
            expected_answer=str(final_sum),
            concept="add_to_ten",
            visual_spec={
                "type": "ten_frame",
                "mode": "current",
                "params": {"frames": [{"filled": 10}, {"filled": remainder}], "color": "apple"},
                "labels": ["1 full ten (10)", f"{remainder} ones left"],
                "alt_text": f"Ten-frame full with 10 dots, and second frame with {remainder} dots."
            },
            hints=[
                f"Combine 10 with your {remainder} ones.",
                f"Picture 1 full box of 10 and {remainder} extra dots beside it.",
                f"In our example: 10 + {ex['rem']} = {ex['sum']}. For your problem: combine 10 and {remainder}."
            ]
        )

        return [step1, step2]


# Register skill
skill_registry.register(AddWithin20Skill())
