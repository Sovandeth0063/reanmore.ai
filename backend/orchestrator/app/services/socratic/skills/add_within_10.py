"""
File: orchestrator/app/services/socratic/skills/add_within_10.py
Description: Very simple addition within 10 for early primary grades.
             Single-step 'count them all' strategy with concrete object
             pictures. The operands are already printed and drawn, so the
             only question asked is the total. Deliberately avoids make-a-ten,
             bar models, and word-problem stories so that a question like
             2 + 2 is explained as simply as it was asked.

             Target: Grades 1-2 | Visual Model: objects
"""

from typing import Dict, Any, List
from fractions import Fraction
from app.services.socratic.skills.base import Skill, StepTemplate, skill_registry

_ITEM = "apple"


def _apples(n: int) -> str:
    return "apple" if n == 1 else "apples"


class AddWithin10Skill:
    skill_id: str = "add_within_10"
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
        if not (float(a).is_integer() and float(b).is_integer()):
            return False
        a_int = int(a)
        b_int = int(b)
        return (
            a_int >= 0
            and b_int >= 0
            and 1 <= (a_int + b_int) <= 10
        )

    def make_distinct_example(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        Picks a parallel example that is just as easy as the child's problem.
        Examples are ordered by how close their total is, so a small problem
        never gets a bigger, more confusing example.
        """
        a = int(problem.get("a", 2))
        b = int(problem.get("b", 2))
        total = a + b
        forbidden = {a, b, total}

        best = None
        for x in range(1, 10):
            for y in range(1, 10):
                cand_sum = x + y
                if cand_sum > 10 or cand_sum < 3:
                    continue
                if not forbidden.isdisjoint({x, y, cand_sum}):
                    continue
                # Prefer the closest total, then the smallest operands.
                score = (abs(cand_sum - total), max(x, y), cand_sum, x)
                if best is None or score < best[0]:
                    best = (score, x, y, cand_sum)

        if best is None:
            return {"a": 3, "b": 3, "sum": 6}
        _, x, y, cand_sum = best
        return {"a": x, "b": y, "sum": cand_sum}

    def build_steps(self, problem: Dict[str, Any]) -> List[StepTemplate]:
        a = int(problem.get("a", 2))
        b = int(problem.get("b", 2))
        total = a + b
        ex = self.make_distinct_example(problem)
        example_count_on = ", ".join(
            str(ex["a"] + step) for step in range(1, ex["b"] + 1)
        )

        # Direct facts have exactly one meaningful cognitive act: find the total.
        # The operands are already printed and drawn, so do not ask the child to
        # transcribe the first/second group back to us.
        step1 = StepTemplate(
            step_number=1,
            title="Count Them All",
            mission=f"Let's put {a} {_apples(a)} and {b} {_apples(b)} together.",
            clue="Count every apple in both groups to find how many there are in all.",
            helpful_example=(
                f"For {ex['a']} + {ex['b']}, start at {ex['a']} and count on: "
                f"{example_count_on}. So {ex['a']} + {ex['b']} = {ex['sum']}."
            ),
            your_turn="How many apples are there in all?",
            expected_answer=str(total),
            concept="count_all",
            visual_spec={
                "type": "objects",
                "groups": [a, b],
                "item_type": _ITEM,
                "title_eng": "Count every apple.",
                "title_khmer": "រាប់ផ្លែប៉ោមទាំងអស់",
            },
            hints=[
                "Count every apple in both groups. Touch each apple as you count.",
                f"Start at {a}. Then count {b} more numbers.",
                f"In our easy example, {ex['a']} + {ex['b']} makes {ex['sum']}. "
                "For your problem, count all the apples together.",
            ],
        )

        return [step1]


# Register skill
skill_registry.register(AddWithin10Skill())
