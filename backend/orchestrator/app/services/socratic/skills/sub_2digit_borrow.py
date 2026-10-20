"""
File: orchestrator/app/services/socratic/skills/sub_2digit_borrow.py
Description: Skill template for 2-digit subtraction with regrouping (borrowing).
             Target: Grades 2-3 | Visual Model: base_ten_blocks
"""

from typing import Dict, Any, List
from app.services.socratic.skills.base import Skill, StepTemplate, skill_registry


class Sub2DigitBorrowSkill:
    skill_id: str = "sub_2digit_borrow"
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
            if 10 <= a_int < 100 and 10 <= b_int < 100 and a_int > b_int:
                # Borrowing happens if ones digit of a < ones digit of b
                return (a_int % 10) < (b_int % 10)
        return False

    def make_distinct_example(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        a = int(problem.get("a", 42))
        b = int(problem.get("b", 17))
        ones_a = a % 10
        ones_b = b % 10
        regroup_ones = ones_a + 10
        sub_ones = regroup_ones - ones_b
        sub_tens = (a // 10 - 1) - (b // 10)
        diff = a - b
        forbidden = {a, b, diff, ones_a, ones_b, regroup_ones, sub_ones, sub_tens, 10}

        for ex_a in range(32, 95):
            for ex_b in range(14, ex_a - 10):
                if (ex_a % 10) >= (ex_b % 10):
                    continue
                cand_regroup_ones = (ex_a % 10) + 10
                cand_sub_ones = cand_regroup_ones - (ex_b % 10)
                cand_sub_tens = (ex_a // 10 - 1) - (ex_b // 10)
                cand_diff = ex_a - ex_b
                cand_vals = {ex_a, ex_b, ex_a % 10, ex_b % 10, ex_a // 10, ex_b // 10, cand_regroup_ones, cand_sub_ones, cand_sub_tens, cand_diff}
                if cand_vals.isdisjoint(forbidden):
                    return {
                        "a": ex_a, "b": ex_b,
                        "ones_a": ex_a % 10, "ones_b": ex_b % 10,
                        "tens_a": ex_a // 10, "tens_b": ex_b // 10,
                        "regroup_ones": cand_regroup_ones,
                        "sub_ones": cand_sub_ones,
                        "sub_tens": cand_sub_tens,
                        "diff": cand_diff
                    }

        return {
            "a": 52, "b": 24, "ones_a": 2, "ones_b": 4, "tens_a": 5, "tens_b": 2,
            "regroup_ones": 12, "sub_ones": 8, "sub_tens": 2, "diff": 28
        }

    def build_steps(self, problem: Dict[str, Any]) -> List[StepTemplate]:
        a = int(problem.get("a", 42))
        b = int(problem.get("b", 17))

        ones_a = a % 10
        ones_b = b % 10
        tens_a = a // 10
        tens_b = b // 10

        regrouped_ones = ones_a + 10
        rem_tens = tens_a - 1
        sub_ones = regrouped_ones - ones_b
        sub_tens = rem_tens - tens_b
        final_diff = a - b
        ex = self.make_distinct_example(problem)

        if ones_a == 0:
            s1_title = "Check the Single Blocks 🧱"
            s1_mission = "Look at our single blocks: we have 0 blocks!"
            s1_clue = "We have 0 loose blocks to give away. We need to open 1 ten-box 📦 to get more blocks!"
            s1_your_turn = "Do we need to open a ten-box to get loose blocks? (yes or no)"
            s1_expected = "yes"
            s1_hints = [
                "We have 0 loose blocks right now.",
                "Since we need to give some away, we must open a ten-box to get blocks!",
                "In our example: we cannot give away blocks from an empty box, so we answer yes!"
            ]
            s1_visual_spec = {
                "type": "base_ten_blocks",
                "mode": "current",
                "params": {"tens": tens_a, "ones": 0, "regroup": False},
                "labels": [f"{tens_a} ten-boxes in {a} 📦", "0 single blocks"],
                "alt_text": f"Blocks showing {tens_a} ten-boxes and 0 single blocks."
            }
        else:
            s1_title = "Unpack a Ten-Box! 📦"
            s1_mission = f"We need to give away {ones_b} blocks, but we only have {ones_a}! Let's open 1 ten-box!"
            s1_clue = f"Opening 1 ten-box gives 10 loose blocks! Add those 10 new blocks to your {ones_a} blocks."
            s1_your_turn = f"10 new blocks plus your {ones_a} blocks. How many loose blocks do you have now? 🧱"
            s1_expected = str(regrouped_ones)
            s1_hints = [
                f"Start at 10 and count up {ones_a} more fingers! 🖐️",
                f"What is 10 + {ones_a}? 🧱",
                f"In our example: {ex['ones_a']} became {ex['regroup_ones']}. What is 10 + {ones_a}?"
            ]
            s1_visual_spec = {
                "type": "base_ten_blocks",
                "mode": "current",
                "params": {"tens": tens_a, "ones": ones_a, "regroup": False},
                "labels": [f"{tens_a} ten-boxes 📦", f"{ones_a} single blocks (need to open a box!)"],
                "alt_text": f"Blocks showing {tens_a} ten-boxes and {ones_a} single blocks."
            }

        step1 = StepTemplate(
            step_number=1,
            title=s1_title,
            mission=s1_mission,
            clue=s1_clue,
            helpful_example=(
                f"For {ex['a']} - {ex['b']}: {ex['ones_a']} is smaller than {ex['ones_b']}. "
                f"We open 1 ten-box to get 10 more blocks, giving {ex['regroup_ones']} loose blocks! 🎁"
            ),
            your_turn=s1_your_turn,
            expected_answer=s1_expected,
            concept="regroup_ten_to_ones",
            visual_spec=s1_visual_spec,
            hints=s1_hints
        )

        step2 = StepTemplate(
            step_number=2,
            title="Take Away Single Blocks 🧱",
            mission=f"Now take away {ones_b} blocks from your {regrouped_ones} blocks!",
            clue=f"Count backwards from {regrouped_ones}, or think: {ones_b} plus what number makes {regrouped_ones}?",
            helpful_example=(
                f"For {ex['a']} - {ex['b']}: {ex['regroup_ones']} blocks minus {ex['ones_b']} blocks = {ex['sub_ones']} blocks left! 🧱"
            ),
            your_turn=f"Take away {ones_b} from {regrouped_ones}. How many single blocks are left? 🧱",
            expected_answer=str(sub_ones),
            concept="subtract_regrouped_ones",
            visual_spec={
                "type": "base_ten_blocks",
                "mode": "current",
                "params": {"ones": regrouped_ones, "regroup": True},
                "labels": [f"{regrouped_ones} loose blocks", f"Take away {ones_b} blocks ❌"],
                "alt_text": f"Blocks showing {regrouped_ones} singles to subtract from."
            },
            hints=[
                f"Count backwards {ones_b} steps starting from {regrouped_ones}.",
                f"What number plus {ones_b} equals {regrouped_ones}?",
                f"In our example: {ex['regroup_ones']} minus {ex['ones_b']} is {ex['sub_ones']}. What is {regrouped_ones} minus {ones_b}?"
            ]
        )

        step3 = StepTemplate(
            step_number=3,
            title="Count Remaining Ten-Boxes! 📦",
            mission=f"Now subtract the remaining ten-boxes: {rem_tens} boxes minus {tens_b} boxes!",
            clue=f"We started with {tens_a} boxes, opened 1, leaving {rem_tens} boxes. Take away {tens_b} boxes, then combine with your {sub_ones} single blocks!",
            helpful_example=(
                f"For {ex['a']} - {ex['b']}: {ex['tens_a'] - 1} boxes - {ex['tens_b']} boxes = {ex['sub_tens']} boxes ({ex['sub_tens'] * 10}). "
                f"With {ex['sub_ones']} singles, the final answer is {ex['diff']}! 🌟"
            ),
            your_turn=f"What is the final answer for {a} - {b}? 🚀",
            expected_answer=str(final_diff),
            concept="subtract_tens_column",
            visual_spec={
                "type": "base_ten_blocks",
                "mode": "current",
                "params": {"tens": rem_tens, "ones": sub_ones, "regroup": True},
                "labels": [f"{rem_tens} boxes minus {tens_b} boxes", f"{sub_ones} single blocks remaining"],
                "alt_text": f"Blocks with {rem_tens} ten-boxes and {sub_ones} single blocks."
            },
            hints=[
                f"{sub_tens} ten-boxes makes {sub_tens * 10}. Combine that with your {sub_ones} single blocks.",
                f"What is {sub_tens * 10} plus {sub_ones}? 🚀",
                f"In our example: {ex['sub_tens']} tens and {ex['sub_ones']} ones = {ex['diff']}. Combine your {sub_tens} tens and {sub_ones} ones!"
            ]
        )

        return [step1, step2, step3]


# Register skill
skill_registry.register(Sub2DigitBorrowSkill())
