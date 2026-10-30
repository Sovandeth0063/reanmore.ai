import re
from typing import Dict, Any, List
from fractions import Fraction
from app.services.socratic.skills.base import Skill, StepTemplate, skill_registry


class OneStepWordProblemSkill:
    skill_id: str = "one_step_word_problem"
    grade_band: str = "grade_1_3"

    def matches(self, problem: Dict[str, Any]) -> bool:
        return problem.get("type") == "word_problem" or problem.get("is_word_problem") is True

    def make_distinct_example(self, problem: Dict[str, Any], forbidden: set) -> Dict[str, Any]:
        candidates = [
            {"total": 3, "part1": 1, "part2": 2, "char": "Dara", "item": "balls"},
            {"total": 4, "part1": 1, "part2": 3, "char": "Maya", "item": "ducks"},
            {"total": 5, "part1": 2, "part2": 3, "char": "Sokha", "item": "books"},
            {"total": 6, "part1": 3, "part2": 3, "char": "Vannak", "item": "stickers"},
            {"total": 7, "part1": 3, "part2": 4, "char": "Chann", "item": "crayons"},
            {"total": 8, "part1": 3, "part2": 5, "char": "Kolab", "item": "oranges"},
            {"total": 9, "part1": 4, "part2": 5, "char": "Rithy", "item": "pencils"},
            {"total": 10, "part1": 4, "part2": 6, "char": "Bopha", "item": "mangoes"},
            {"total": 14, "part1": 6, "part2": 8, "char": "Bopha", "item": "mangoes"},
            {"total": 15, "part1": 6, "part2": 9, "char": "Chann", "item": "crayons"},
            {"total": 16, "part1": 7, "part2": 9, "char": "Vannak", "item": "stickers"},
            {"total": 18, "part1": 5, "part2": 13, "char": "Sokha", "item": "pencils"},
            {"total": 20, "part1": 7, "part2": 13, "char": "Kolab", "item": "oranges"},
            {"total": 22, "part1": 8, "part2": 14, "char": "Rithy", "item": "erasers"},
        ]
        # Keep the worked example at a similar difficulty to the child's problem.
        if "a" in problem and "b" in problem:
            target = int(problem["a"]) + int(problem["b"])
        else:
            target = int(problem.get("total", 0)) or (
                int(problem.get("part1", 0)) + int(problem.get("part2", 0))
            )
        ordered = sorted(candidates, key=lambda c: abs(c["total"] - target))
        for c in ordered:
            if {c["total"], c["part1"], c["part2"]}.isdisjoint(forbidden):
                return c
        return {
            "total": 30, "part1": 11, "part2": 19, "char": "Bopha", "item": "stars"
        }

    def build_steps(self, problem: Dict[str, Any]) -> List[StepTemplate]:
        item = problem.get("item") or "items"
        op = problem.get("op", "-")

        if "a" in problem and "b" in problem:
            val_a = int(problem["a"])
            val_b = int(problem["b"])
            if op == "+":
                part1 = val_a
                part2 = val_b
                total = val_a + val_b
                missing_part = total
            else:
                total = max(val_a, val_b)
                part1 = min(val_a, val_b)
                part2 = total - part1
                missing_part = part2
        else:
            total = int(problem.get("total", 15))
            part1 = int(problem.get("part1", 7))
            part2 = total - part1 if op == "-" else total + part1
            missing_part = part2

        forbidden = {total, part1, part2, missing_part}
        ex = self.make_distinct_example(problem, forbidden)

        if op == "*":
            # One-step multiplication word problem: equal groups -> one total.
            # Asking "how many groups?" would just re-read a number already in
            # the story, so there is a single meaningful question.
            group_count = int(problem["a"])
            per_group = int(problem["b"])
            product = group_count * per_group
            ex_pairs = [(4, 3), (3, 5), (2, 6), (4, 5), (3, 7), (6, 4), (2, 9)]
            ex_a, ex_b = next(
                ((x, y) for x, y in ex_pairs
                 if {x, y, x * y}.isdisjoint({group_count, per_group, product})),
                (4, 3),
            )
            skip_partial = ", ".join(
                str(per_group * i) for i in range(1, group_count)
            ) or str(per_group)

            step1 = StepTemplate(
                step_number=1,
                title="Find the Total",
                mission=f"Each group has {per_group} {item}. There are {group_count} equal groups.",
                clue="Multiply the number of groups by the number in each group.",
                helpful_example=(
                    f"For {ex_a} groups of {ex_b}: {ex_a} × {ex_b} = "
                    f"{ex_a * ex_b} {item} in all."
                ),
                your_turn=f"How many {item} are there in all?",
                expected_answer=str(product),
                concept="repeated_addition",
                visual_spec={
                    "type": "array_grid",
                    "mode": "current",
                    "params": {"rows": group_count, "cols": per_group},
                    "labels": [f"{group_count} groups of {per_group}"],
                    "alt_text": f"Array grid of {group_count} rows by {per_group} columns.",
                },
                hints=[
                    f"Add {per_group} repeatedly {group_count} times.",
                    f"Skip count by {per_group}s: {skip_partial}...",
                    f"In our example: {ex_a} × {ex_b} = {ex_a * ex_b}. "
                    f"For your problem, multiply {group_count} by {per_group}.",
                ],
            )
            return [step1]

        if op == "+":
            # Addition word problem: Part + Part = Total
            step1 = StepTemplate(
                step_number=1,
                title="Identify the Starting Part",
                mission="Let's find the first group from our story!",
                clue="In a bar model, we put the smaller parts together to make the whole.",
                helpful_example=(
                    f"For {ex['char']}'s problem: The first part is {ex['part1']} {ex['item']}. "
                    f"The second part is {ex['part2']} {ex['item']}."
                ),
                your_turn=f"What is the first starting amount of {item}?",
                expected_answer=str(part1),
                concept="identify_part",
                visual_spec={
                    "type": "bar_model",
                    "mode": "current",
                    "params": {"whole": None, "parts": [None, part2], "unknown_index": 0},
                    "labels": ["Total: ?", f"Second part: {part2}"],
                    "alt_text": f"Part-whole bar model with second part {part2}."
                },
                hints=[
                    f"Look at how many {item} we started with in the story.",
                    f"Find the first number of {item} mentioned.",
                    f"In our example: first part was {ex['part1']}. For your problem: check the first sentence."
                ]
            )

            step2 = StepTemplate(
                step_number=2,
                title="Find the Total Amount",
                mission="Add the two parts together to find the total!",
                clue=f"Combine {part1} {item} and {part2} {item}.",
                helpful_example=(
                    f"For {ex['char']}: {ex['part1']} + {ex['part2']} = {ex['total']} {ex['item']} in all."
                ),
                your_turn=f"How many {item} in all?",
                expected_answer=str(total),
                concept="solve_total",
                visual_spec={
                    "type": "bar_model",
                    "mode": "current",
                    "params": {"whole": None, "parts": [part1, part2], "unknown_index": 0},
                    "labels": [f"Part 1: {part1}", f"Part 2: {part2}", "Total: ?"],
                    "alt_text": f"Bar model showing parts {part1} and {part2} to find the total."
                },
                hints=[
                    f"Add the two numbers together: {part1} + {part2}.",
                    f"Start at {part1} and count up {part2} more.",
                    f"In our example: {ex['part1']} + {ex['part2']} = {ex['total']}. For your problem: add {part1} and {part2}."
                ]
            )
        else:
            # Subtraction word problem: Whole - Part = Missing Part
            step1 = StepTemplate(
                step_number=1,
                title="Identify the Starting Total",
                mission="Let's find the total amount we started with!",
                clue="In a bar model, the long bar is the starting TOTAL. Smaller boxes are PARTS.",
                helpful_example=(
                    f"For {ex['char']}'s problem: The whole is {ex['total']} {ex['item']}. "
                    f"One part is {ex['part1']}. The missing part is {ex['part2']}."
                ),
                your_turn=f"What is the starting total amount of {item}?",
                expected_answer=str(total),
                concept="identify_whole",
                visual_spec={
                    "type": "bar_model",
                    "mode": "current",
                    "params": {"whole": None, "parts": [part1, None], "unknown_index": 0},
                    "labels": ["Total: ?", f"Given part: {part1}"],
                    "alt_text": f"Part-whole bar model with unknown starting total and known part {part1}."
                },
                hints=[
                    f"Look at how many {item} there were at the very beginning.",
                    f"Find the starting number of {item} before any went away.",
                    f"In our example: starting whole was {ex['total']}. For your problem: check the first sentence."
                ]
            )

            step2 = StepTemplate(
                step_number=2,
                title="Calculate the Missing Amount",
                mission="Now find how many are left!",
                clue=f"Subtract the known part ({part1}) from the whole ({total}).",
                helpful_example=(
                    f"For {ex['char']}: {ex['total']} - {ex['part1']} = {ex['part2']} {ex['item']} left."
                ),
                your_turn=f"How many {item} are left?",
                expected_answer=str(missing_part),
                concept="solve_missing_part",
                visual_spec={
                    "type": "bar_model",
                    "mode": "current",
                    "params": {"whole": total, "parts": [part1, None], "unknown_index": 1},
                    "labels": [f"Total: {total}", f"Given part: {part1}", "Left: ?"],
                    "alt_text": f"Bar model showing total {total}, known part {part1}, and unknown part."
                },
                hints=[
                    f"Take away {part1} from {total}.",
                    f"Count back {part1} steps from {total}.",
                    f"In our example: {ex['total']} minus {ex['part1']} gave {ex['part2']}. For your problem: take {part1} from {total}."
                ]
            )

        return [step1, step2]


# Register skill
skill_registry.register(OneStepWordProblemSkill())

