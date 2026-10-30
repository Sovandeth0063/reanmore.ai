"""
File: orchestrator/app/services/socratic/skills/sub_within_10.py
Description: Very simple subtraction within 10 for early primary grades.
             Single-step 'take some away, count what is left' strategy with
             concrete object pictures. The starting number is already printed
             and drawn, so it is not re-asked. Deliberately avoids borrowing
             and bar-model language.

             Target: Grades 1-2 | Visual Model: objects
"""

from typing import Dict, Any, List
from fractions import Fraction
from app.services.socratic.skills.base import Skill, StepTemplate, skill_registry

_ITEM = "apple"


def _apples(n: int) -> str:
    return "apple" if n == 1 else "apples"


class SubWithin10Skill:
    skill_id: str = "sub_within_10"
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
        if not (isinstance(a, (int, Fraction)) and isinstance(b, (int, Fraction))):
            return False
        if not (float(a).is_integer() and float(b).is_integer()):
            return False
        a_int = int(a)
        b_int = int(b)
        return 1 <= a_int <= 10 and 0 <= b_int <= a_int

    def make_distinct_example(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """Picks an equally simple subtraction example with different numbers."""
        a = int(problem.get("a", 5))
        b = int(problem.get("b", 2))
        answer = a - b
        forbidden = {a, b, answer}

        best = None
        for x in range(2, 11):
            for y in range(1, x):
                cand_answer = x - y
                if cand_answer < 1:
                    continue
                if not forbidden.isdisjoint({x, y, cand_answer}):
                    continue
                score = (abs(x - a), max(x, y), x)
                if best is None or score < best[0]:
                    best = (score, x, y, cand_answer)

        if best is None:
            return {"a": 4, "b": 1, "answer": 3}
        _, x, y, cand_answer = best
        return {"a": x, "b": y, "answer": cand_answer}

    def build_steps(self, problem: Dict[str, Any]) -> List[StepTemplate]:
        a = int(problem.get("a", 5))
        b = int(problem.get("b", 2))
        answer = a - b
        ex = self.make_distinct_example(problem)

        # Direct facts have exactly one meaningful cognitive act: take away and
        # count what remains. The starting number is already printed and drawn.
        # List the remaining apples for the parallel example only.
        example_left = ", ".join(str(i) for i in range(1, ex["answer"] + 1))
        step1 = StepTemplate(
            step_number=1,
            title="Take Some Away",
            mission=f"Start with {a} {_apples(a)} and take {b} away.",
            clue=f"Take {b} {_apples(b)} away from {a} {_apples(a)}. Count what is left.",
            helpful_example=(
                f"For {ex['a']} - {ex['b']}, take {ex['b']} {_apples(ex['b'])} away. "
                f"Count what is left: {example_left}. "
                f"So {ex['a']} - {ex['b']} = {ex['answer']}."
            ),
            your_turn="How many apples are left?",
            expected_answer=str(answer),
            concept="count_left",
            visual_spec={
                "type": "objects",
                "groups": [a],
                "item_type": _ITEM,
                "title_eng": f"Take {b} away. How many are left?",
                "title_khmer": f"ដក {b} ចេញ។ តើនៅសល់ប៉ុន្មាន?",
            },
            hints=[
                "Count the apples that are left. Do not count the ones we took away.",
                f"Start with {a} {_apples(a)}, then count back {b} numbers.",
                f"In our easy example, {ex['a']} - {ex['b']} leaves {ex['answer']}. "
                "For your problem, count the apples that are left.",
            ],
        )

        return [step1]


# Register skill
skill_registry.register(SubWithin10Skill())
