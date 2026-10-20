"""
File: orchestrator/app/services/socratic/skills/mult_tables.py
Description: Skill template for elementary multiplication tables and array models.
             Target: Grades 3-4 | Visual Model: array_grid
"""

from typing import Dict, Any, List
from app.services.socratic.skills.base import Skill, StepTemplate, skill_registry


class MultTablesSkill:
    skill_id: str = "mult_tables"
    grade_band: str = "grade_1_3"

    def matches(self, problem: Dict[str, Any]) -> bool:
        if problem.get("is_word_problem") or problem.get("type") == "word_problem":
            return False
        if problem.get("op") != "*":
            return False
        a = problem.get("a")
        b = problem.get("b")
        if a is None or b is None:
            return False
        if float(a).is_integer() and float(b).is_integer():
            a_int = int(a)
            b_int = int(b)
            # Elementary tables: 1 to 12
            return 1 <= a_int <= 12 and 1 <= b_int <= 12
        return False

    def make_distinct_example(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        a = int(problem.get("a", 4))
        b = int(problem.get("b", 3))
        prod = a * b
        forbidden = {a, b, prod}

        for ex_a in range(2, 10):
            for ex_b in range(2, 10):
                cand_prod = ex_a * ex_b
                if {ex_a, ex_b, cand_prod}.isdisjoint(forbidden):
                    return {"a": ex_a, "b": ex_b, "prod": cand_prod}
        return {"a": 7, "b": 9, "prod": 63}

    def build_steps(self, problem: Dict[str, Any]) -> List[StepTemplate]:
        a = int(problem.get("a", 4))
        b = int(problem.get("b", 3))
        prod = a * b
        ex = self.make_distinct_example(problem)

        step1 = StepTemplate(
            step_number=1,
            title="Read as Equal Groups",
            mission=f"Let's visualize {a} × {b}. Think of it as {a} equal groups of {b}!",
            clue="Multiplication is a fast way of counting equal groups.",
            helpful_example=(
                f"For {ex['a']} × {ex['b']}: That means {ex['a']} rows of {ex['b']} dots. "
                f"Each row has exactly {ex['b']} dots."
            ),
            your_turn=f"In {a} × {b}, how many dots are in EACH group?",
            expected_answer=str(b),
            concept="equal_groups",
            visual_spec={
                "type": "array_grid",
                "mode": "current",
                "params": {"rows": a, "cols": None},
                "labels": [f"{a} equal rows"],
                "alt_text": f"Array grid showing {a} rows to fill."
            },
            hints=[
                f"Look at the second number in {a} × {b}.",
                f"The expression means {a} equal groups.",
                f"In our example: each row has {ex['b']} dots. For your problem: look at the second number."
            ]
        )

        step2 = StepTemplate(
            step_number=2,
            title="Count by Groups to Find Total",
            mission=f"Now skip count or add {a} groups of {b} to find the total product!",
            clue=f"You can skip count by {b}s, or add {b} repeatedly {a} times.",
            helpful_example=(
                f"For {ex['a']} × {ex['b']}: Skip counting by {ex['b']}s {ex['a']} times gives {ex['prod']}!"
            ),
            your_turn=f"What is {a} × {b}?",
            expected_answer=str(prod),
            concept="repeated_addition",
            visual_spec={
                "type": "array_grid",
                "mode": "current",
                "params": {"rows": a, "cols": b},
                "labels": [f"Total: {a} rows of {b}"],
                "alt_text": f"Complete array grid of {a} by {b} dots."
            },
            hints=[
                f"Add {b} repeatedly {a} times.",
                f"Count the total number of dots in the {a} by {b} grid.",
                f"In our example: {ex['a']} × {ex['b']} = {ex['prod']}. For your problem: add {b} repeatedly {a} times."
            ]
        )

        return [step1, step2]


# Register skill
skill_registry.register(MultTablesSkill())
