"""
File: orchestrator/app/services/socratic/skills/fraction_equivalent.py
Description: Skill template for equivalent fractions and visual fraction bar models.
             Target: Grades 4-5 | Visual Model: fraction_bar
"""

import math
from typing import Dict, Any, List
from fractions import Fraction
from app.services.socratic.skills.base import Skill, StepTemplate, skill_registry


class FractionEquivalentSkill:
    skill_id: str = "fraction_equivalent"
    grade_band: str = "grade_4_6"

    def matches(self, problem: Dict[str, Any]) -> bool:
        if problem.get("is_word_problem") or problem.get("type") == "word_problem":
            return False
        op = problem.get("op")
        a = problem.get("a")
        if isinstance(a, Fraction) and a.denominator > 1:
            return True
        if op == "/" and "b" in problem:
            return True
        if problem.get("type") == "fraction_equivalent":
            return True
        return False

    def make_distinct_example(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        if problem.get("op") == "/" and "b" in problem:
            orig_num = int(problem["a"])
            orig_den = int(problem["b"])
        else:
            orig_num = 2
            orig_den = 4

        target_frac = Fraction(orig_num, orig_den)
        forbidden = {orig_num, orig_den}

        candidates = [
            {"orig_num": 2, "orig_den": 8, "scale": 2, "new_num": 1, "new_den": 4},
            {"orig_num": 2, "orig_den": 10, "scale": 2, "new_num": 1, "new_den": 5},
            {"orig_num": 3, "orig_den": 12, "scale": 3, "new_num": 1, "new_den": 4},
            {"orig_num": 3, "orig_den": 15, "scale": 3, "new_num": 1, "new_den": 5},
            {"orig_num": 4, "orig_den": 12, "scale": 4, "new_num": 1, "new_den": 3},
            {"orig_num": 4, "orig_den": 20, "scale": 4, "new_num": 1, "new_den": 5},
            {"orig_num": 5, "orig_den": 20, "scale": 5, "new_num": 1, "new_den": 4},
        ]

        for c in candidates:
            c_val = Fraction(c["orig_num"], c["orig_den"])
            if c_val != target_frac and {c["orig_num"], c["orig_den"], c["new_num"], c["new_den"], c["scale"]}.isdisjoint(forbidden):
                return c
        return candidates[0]

    def build_steps(self, problem: Dict[str, Any]) -> List[StepTemplate]:
        if problem.get("op") == "/" and "b" in problem:
            orig_num = int(problem["a"])
            orig_den = int(problem["b"])
        else:
            a = problem.get("a", Fraction(2, 4))
            if isinstance(a, Fraction):
                orig_num = a.numerator
                orig_den = a.denominator
            else:
                orig_num = 2
                orig_den = 4

        common_gcd = math.gcd(orig_num, orig_den)
        if common_gcd > 1:
            factor = common_gcd
            simp_num = orig_num // factor
            simp_den = orig_den // factor
            action = "divide"
        else:
            factor = 2
            simp_num = orig_num * factor
            simp_den = orig_den * factor
            action = "multiply"

        ex = self.make_distinct_example(problem)

        step1 = StepTemplate(
            step_number=1,
            title="Find the Common Factor",
            mission="To simplify a fraction, find a number that divides both top and bottom!",
            clue=f"What common number greater than 1 can divide both {orig_num} and {orig_den}?",
            helpful_example=(
                f"For {ex['orig_num']}/{ex['orig_den']}: Both numbers can be divided by {ex['scale']}."
            ),
            your_turn=f"What number divides both {orig_num} and {orig_den} evenly?",
            expected_answer=str(factor),
            concept="common_factor",
            visual_spec={
                "type": "fraction_bar",
                "mode": "current",
                "params": {},
                "labels": ["Fraction bar model"],
                "alt_text": "Fraction bar model to simplify."
            },
            hints=[
                f"Think of numbers that divide evenly into both {orig_num} and {orig_den}.",
                f"Check if both numbers are even numbers.",
                f"In our example: common factor is {ex['scale']}. For your problem, think what divides {orig_num} and {orig_den}."
            ]
        )

        step2 = StepTemplate(
            step_number=2,
            title="Simplify to Lowest Terms",
            mission="Divide both the numerator and denominator by your common factor!",
            clue=f"Divide the top number {orig_num} by {factor}, and the bottom number {orig_den} by {factor}.",
            helpful_example=(
                f"For {ex['orig_num']}/{ex['orig_den']}: Top is {ex['orig_num']} ÷ {ex['scale']} = {ex['new_num']}. "
                f"Bottom is {ex['orig_den']} ÷ {ex['scale']} = {ex['new_den']}. We get {ex['new_num']}/{ex['new_den']}!"
            ),
            your_turn=f"What is {orig_num}/{orig_den} in lowest terms?",
            expected_answer=f"{simp_num}/{simp_den}",
            concept="simplify_fraction",
            visual_spec={
                "type": "fraction_bar",
                "mode": "current",
                "params": {"numerator": orig_num, "denominator": orig_den},
                "labels": [f"Original fraction: {orig_num}/{orig_den}"],
                "alt_text": f"Fraction bar showing {orig_num} out of {orig_den} parts shaded."
            },
            hints=[
                f"Divide top by {factor} and bottom by {factor}.",
                f"Calculate {orig_num} ÷ {factor} for the top and {orig_den} ÷ {factor} for the bottom.",
                f"In our example: {ex['orig_num']}/{ex['orig_den']} became {ex['new_num']}/{ex['new_den']}. For your problem: divide top and bottom by {factor}."
            ]
        )

        return [step1, step2]


# Register skill
skill_registry.register(FractionEquivalentSkill())

