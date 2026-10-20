"""
File: orchestrator/app/services/socratic/skills/add_2digit_regroup.py
Description: Skill template for 2-digit addition with regrouping (carrying).
             Target: Grades 2-3 | Visual Model: base_ten_blocks
"""

from typing import Dict, Any, List
from app.services.socratic.skills.base import Skill, StepTemplate, skill_registry


class Add2DigitRegroupSkill:
    skill_id: str = "add_2digit_regroup"
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
        if float(a).is_integer() and float(b).is_integer():
            a_int = int(a)
            b_int = int(b)
            if 10 <= a_int < 100 and 10 <= b_int < 100:
                # Regrouping happens if sum of ones digits >= 10
                return ((a_int % 10) + (b_int % 10)) >= 10
        return False

    def make_distinct_example(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        a = int(problem.get("a", 15))
        b = int(problem.get("b", 27))
        ones_a = a % 10
        ones_b = b % 10
        ones_sum = ones_a + ones_b
        ones_rem = ones_sum % 10
        tens_sum = (a // 10) + (b // 10) + 1
        total = a + b
        forbidden = {a, b, total, ones_a, ones_b, ones_sum, ones_rem, tens_sum}

        # Search candidates with ones regrouping
        for ex_a in range(15, 60, 3):
            for ex_b in range(15, 40, 2):
                cand_ones_sum = (ex_a % 10) + (ex_b % 10)
                if cand_ones_sum < 10:
                    continue
                cand_ones_rem = cand_ones_sum % 10
                cand_tens_total = (ex_a // 10) + (ex_b // 10) + 1
                cand_total = ex_a + ex_b
                cand_vals = {ex_a, ex_b, ex_a % 10, ex_b % 10, cand_ones_sum, cand_ones_rem, cand_tens_total, cand_total}
                if cand_vals.isdisjoint(forbidden):
                    return {
                        "a": ex_a, "b": ex_b,
                        "ones_a": ex_a % 10, "ones_b": ex_b % 10,
                        "ones_sum": cand_ones_sum,
                        "ones_rem": cand_ones_rem,
                        "tens_a": ex_a // 10, "tens_b": ex_b // 10,
                        "tens_total": cand_tens_total,
                        "total": cand_total
                    }
        return {
            "a": 18, "b": 24, "ones_a": 8, "ones_b": 4, "ones_sum": 12, "ones_rem": 2,
            "tens_a": 1, "tens_b": 2, "tens_total": 4, "total": 42
        }

    def build_steps(self, problem: Dict[str, Any]) -> List[StepTemplate]:
        a = int(problem.get("a", 15))
        b = int(problem.get("b", 27))

        ones_a = a % 10
        ones_b = b % 10
        tens_a = a // 10
        tens_b = b // 10

        ones_sum = ones_a + ones_b
        ones_remainder = ones_sum % 10
        tens_sum = tens_a + tens_b + 1
        final_total = a + b
        ex = self.make_distinct_example(problem)

        step1 = StepTemplate(
            step_number=1,
            title="Count Single Blocks (Ones) 🧱",
            mission="Let's count our single blocks 🧱 on the right side!",
            clue=f"Put the bigger number {max(ones_a, ones_b)} in your head, then count on {min(ones_a, ones_b)} more fingers! 🖐️",
            helpful_example=(
                f"Like {ex['a']} + {ex['b']}: {ex['ones_a']} blocks + {ex['ones_b']} blocks = {ex['ones_sum']} blocks in all! 🧱"
            ),
            your_turn=f"Add the single blocks: What is {ones_a} + {ones_b}? 🧱",
            expected_answer=str(ones_sum),
            concept="add_ones_column",
            visual_spec={
                "type": "base_ten_blocks",
                "mode": "current",
                "params": {"tens": tens_a + tens_b, "ones": ones_a, "regroup": False},
                "labels": [f"{tens_a + tens_b} ten-towers 🗼", f"Single blocks: {ones_a} and {ones_b} 🧱"],
                "alt_text": f"Blocks showing {ones_a} singles and {ones_b} singles."
            },
            hints=[
                f"Put {max(ones_a, ones_b)} in your mind, then tap your fingers to count up {min(ones_a, ones_b)} more! 🖐️",
                f"Imagine {ones_a} red apples 🍎 and {ones_b} green apples 🍏 in one bowl. Count them together!",
                f"In our example: {ex['ones_a']} + {ex['ones_b']} = {ex['ones_sum']}. For your problem: add {ones_a} and {ones_b}."
            ]
        )

        step2 = StepTemplate(
            step_number=2,
            title="Pack a Ten-Box! 📦",
            mission=f"We have {ones_sum} loose blocks! Let's pack 10 blocks into 1 ten-tower 🗼!",
            clue=f"Every time we have 10 or more, 10 blocks snap into a ten-tower! 🗼 How many loose blocks are left outside?",
            helpful_example=(
                f"For {ex['ones_sum']} cookies 🍪: Pack 10 in a box 📦, and {ex['ones_rem']} loose cookies stay on the plate!"
            ),
            your_turn=f"You pack 10 out of your {ones_sum} blocks into a ten-tower. How many loose blocks are left? 🧱",
            expected_answer=str(ones_remainder),
            concept="trade_ones_for_ten",
            visual_spec={
                "type": "base_ten_blocks",
                "mode": "current",
                "params": {"ones": ones_sum, "regroup": False},
                "highlights": [{"type": "carry_ten", "amount": 1}],
                "labels": [f"We have {ones_sum} loose blocks 🧱", "Pack 10 blocks into 1 ten-tower 🗼"],
                "alt_text": f"Packing 10 single blocks into 1 ten-tower, leaving loose single blocks."
            },
            hints=[
                f"Take 10 away from {ones_sum}: what is left over? 🍪",
                f"Think: 10 + what number makes {ones_sum}? Look at the last digit of {ones_sum}!",
                f"In our cookie box example: {ex['ones_sum']} cookies left {ex['ones_rem']} loose ones. For {ones_sum}, how many stay outside?"
            ]
        )

        step3 = StepTemplate(
            step_number=3,
            title="Count All Ten-Towers! 🗼",
            mission=f"Now count all the 10-towers together, including our 1 new packed tower! ✨",
            clue=f"Count the towers: {tens_a} from the first number, {tens_b} from the second, plus 1 new tower ({tens_a} + {tens_b} + 1 = {tens_sum} towers = {tens_sum * 10}). Plus your {ones_remainder} loose blocks!",
            helpful_example=(
                f"For {ex['a']} + {ex['b']}: {ex['tens_total']} ten-towers ({ex['tens_total'] * 10}) plus {ex['ones_rem']} singles gives {ex['total']}! 🌟"
            ),
            your_turn=f"What is the final answer for {a} + {b}? 🚀",
            expected_answer=str(final_total),
            concept="add_tens_with_carry",
            visual_spec={
                "type": "base_ten_blocks",
                "mode": "current",
                "params": {"tens": tens_sum, "ones": ones_remainder, "regroup": True},
                "labels": [f"{tens_sum} ten-towers ({tens_sum * 10})", f"{ones_remainder} single blocks"],
                "alt_text": f"Complete blocks showing {tens_sum} ten-towers and {ones_remainder} singles."
            },
            hints=[
                f"You have {tens_sum} ten-towers ({tens_sum * 10}) and {ones_remainder} loose blocks. Put them together! 🧱",
                f"What is {tens_sum * 10} plus {ones_remainder}? 🚀",
                f"In our example: {ex['tens_total']} tens and {ex['ones_rem']} ones = {ex['total']}. What is {tens_sum} tens and {ones_remainder} ones?"
            ]
        )

        return [step1, step2, step3]


# Register skill
skill_registry.register(Add2DigitRegroupSkill())

