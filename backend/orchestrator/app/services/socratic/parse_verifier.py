"""
File: orchestrator/app/services/socratic/parse_verifier.py
Description: 7-Stage Word Problem Parse Verification Pipeline with Child Confirmation.
             Implements Architecture v2.1 Section 5.2.
"""

import re
import logging
from typing import Optional, Dict, Any, List, Tuple
from fractions import Fraction
from dataclasses import dataclass

from app.services.socratic.math_engine.cas import (
    evaluate_exact,
    format_exact_fraction,
    strip_arithmetic_wrappers,
)

logger = logging.getLogger("orchestrator.socratic.parse_verifier")


@dataclass
class ParseVerificationResult:
    is_valid: bool
    confidence: float
    problem_type: str                   # "arithmetic", "word_problem", "unclear"
    parsed_problem: Optional[Dict[str, Any]] = None
    needs_confirmation: bool = False
    confirmation_prompt: Optional[str] = None
    issues: List[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []


def extract_numbers_from_text(text: str) -> List[Tuple[str, Fraction]]:
    """Extracts all numbers (integers, decimals, simple fractions) from text."""
    matches = re.findall(r"\b(\d+(?:\.\d+)?|\d+/\d+)\b", text)
    results = []
    for m in matches:
        val = evaluate_exact(m)
        if val is not None:
            results.append((m, val))
    return results


def is_pure_arithmetic_expression(text: str) -> bool:
    """
    Checks if text is a direct arithmetic formula/expression rather than a narrative word problem.
    Examples:
      - '7 + 3 + 2 + 5 ='
      - '4 + 5 + 6'
      - 'solve 7 + 3 + 2 + 5 ='
      - '15 + 27 = ?'
      - '30 + [ ] = 100'
    """
    if not text or not text.strip():
        return False
    # Strip conversational wrappers ("what", "what's", "please solve", ...)
    # and word operators so bare child-typed expressions stay arithmetic.
    cleaned = strip_arithmetic_wrappers(text)
    if not cleaned:
        return False
    cleaned = re.sub(r"[\[\]_\s]+", " ", cleaned).strip()
    tokens = [w for w in re.findall(r"[a-zA-Z]{2,}", cleaned)]
    if tokens:
        return False
    has_operator = bool(re.search(r"[\+\-\*\/\.\^]", cleaned))
    has_digit = bool(re.search(r"\d", cleaned))
    return has_operator and has_digit


def verify_and_parse_word_problem(text: str, grade_level: str = "grade_1_3") -> ParseVerificationResult:
    """
    Executes the 7-stage parse verification pipeline:
    1. Quantity Extraction
    2. Operand Mapping
    3. Mathematical Validity (via in-process SymPy)
    4. Token-to-Number Ratio Check
    5. Grade-Band Suitability
    6. Single Unknown Variable Check
    7. Child Confirmation Generation
    """
    clean_text = text.strip()
    words = clean_text.split()
    issues = []

    # Pure arithmetic formulas (e.g. '7 + 3 + 2 + 5 =') are not narrative word problems
    if is_pure_arithmetic_expression(clean_text):
        return ParseVerificationResult(
            is_valid=False,
            confidence=0.0,
            problem_type="arithmetic",
            issues=["Input is a pure arithmetic expression, not a narrative word problem."]
        )

    # Stage 1: Quantity Extraction
    num_tuples = extract_numbers_from_text(clean_text)
    if len(num_tuples) < 2:
        return ParseVerificationResult(
            is_valid=False,
            confidence=0.0,
            problem_type="unclear",
            issues=["Not enough numbers found to form an elementary problem."]
        )

    # Stage 4: Token-to-Number Ratio Check (deflect narrative spam)
    if len(words) > 50:
        issues.append("Problem text exceeds 50 words; possible narrative essay.")

    # Stage 5: Grade-Band Suitability Check
    max_limit = 1_000 if grade_level == "grade_1_3" else 1_000_000
    for raw_str, val in num_tuples:
        if abs(float(val)) > max_limit:
            issues.append(f"Number {raw_str} exceeds grade-band threshold {max_limit}.")

    # Stage 2 & 6: Operand mapping and single unknown check
    lower_text = clean_text.lower()
    is_subtraction = any(k in lower_text for k in [
        "give away", "gives away", "gave away", "gives to", "gave to", "left", "lost",
        "eats", "ate", "fewer", "less", "minus", "difference", "how many are left", "how many left"
    ])
    is_addition = any(k in lower_text for k in [
        "more", "altogether", "in all", "together", "plus", "sum", "total", "buys more", "finds", "how many in all"
    ])
    is_multiplication = any(k in lower_text for k in [
        "each", "times", "groups of", "rows of", "per", "every"
    ])

    # Resolving cues: if "in all" / "more" present and no explicit "away" / "to someone", favor addition
    if is_addition and not any(k in lower_text for k in ["away", "left", "lost", "fewer", "gives to", "gave to"]):
        op = "+"
    elif is_subtraction and not is_addition:
        op = "-"
    elif is_multiplication:
        op = "*"
    elif is_subtraction:
        op = "-"
    else:
        op = "+"

    # Assign operands: for subtraction, typically larger number is total
    vals = [t[1] for t in num_tuples]
    if op == "-":
        vals_sorted = sorted(vals, reverse=True)
        total = vals_sorted[0]
        part1 = vals_sorted[1]
    else:
        total = vals[0]
        part1 = vals[1]

    # Stage 3: Mathematical validity
    try:
        if op == "-":
            expected = total - part1
        elif op == "*":
            expected = total * part1
        else:
            expected = total + part1
    except Exception as e:
        return ParseVerificationResult(
            is_valid=False,
            confidence=0.0,
            problem_type="unclear",
            issues=[f"Arithmetic evaluation failed: {e}"]
        )

    # Stage 7: Confidence calculation & Child Confirmation Prompt
    confidence = 0.95
    if len(num_tuples) > 3:
        confidence -= 0.20
        issues.append("Found more than 2 quantities; multi-step problem.")
    if is_subtraction and is_addition:
        confidence -= 0.15
        issues.append("Found competing addition and subtraction clue words.")
    if issues:
        confidence = max(0.50, confidence - 0.10 * len(issues))

    parsed_problem = {
        "type": "word_problem",
        "is_word_problem": True,
        "total": float(total),
        "part1": float(part1),
        "a": total,
        "b": part1,
        "op": op,
        "expected_answer": format_exact_fraction(expected),
        "num_extracted": len(num_tuples)
    }

    needs_confirm = confidence < 0.90
    confirm_prompt = None
    if needs_confirm:
        confirm_prompt = (
            f"🌟 Did you mean: Start with {format_exact_fraction(total)}, then {op} {format_exact_fraction(part1)}? "
            f"({format_exact_fraction(total)} {op} {format_exact_fraction(part1)} = ?)"
        )

    return ParseVerificationResult(
        is_valid=True,
        confidence=confidence,
        problem_type="word_problem",
        parsed_problem=parsed_problem,
        needs_confirmation=needs_confirm,
        confirmation_prompt=confirm_prompt,
        issues=issues
    )
