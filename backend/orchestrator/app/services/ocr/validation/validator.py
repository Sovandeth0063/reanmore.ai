"""
Validation layer: runs structural, confidence, and math checks
on the pipeline output before the final API response is assembled.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from app.services.ocr.schemas.homework import (
    HomeworkResponse, Page, Question, QuestionType,
    ValidationResult, ReviewFlag, ReviewReason,
    ElementType, QUESTION_KINDS,
)
from app.services.ocr.utils.bbox_utils import validate_answer_area_bbox
from app.services.ocr.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Math validation helpers
# ---------------------------------------------------------------------------

# Simple arithmetic pattern: "2 + 3 = __" or "10 - 4 = ___"
_MATH_SIMPLE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*([\+\-\×\*\/÷])\s*(\d+(?:\.\d+)?)\s*=\s*[_\[\]\s]*(\d+(?:\.\d+)?)?",
    re.UNICODE,
)
_OP_MAP = {"+": "+", "-": "-", "×": "*", "*": "*", "/": "/", "÷": "/"}


def _evaluate_simple_math(expr: str) -> Optional[float]:
    """
    Evaluate a simple two-operand arithmetic expression string.
    Returns the numeric result, or None if parsing fails.
    """
    m = _MATH_SIMPLE_RE.search(expr)
    if not m:
        return None
    a, op_raw, b = m.group(1), m.group(2), m.group(3)
    op = _OP_MAP.get(op_raw)
    if not op:
        return None
    try:
        from sympy import sympify, Rational
        result = sympify(f"{a}{op}{b}")
        return float(result)
    except Exception:
        return None


def _check_math_question(question: Question) -> list[str]:
    """
    For math equation questions with a student answer, verify the arithmetic.
    Returns a list of warning strings (empty = no issues).
    """
    warnings = []
    if question.type != QuestionType.MATH_EQUATION:
        return warnings
    if not question.prompt:
        return warnings

    expected = _evaluate_simple_math(question.prompt)
    if expected is None:
        return warnings  # Complex expression — skip

    student_ans = question.student_answer
    if student_ans is None:
        return warnings  # No answer to check

    try:
        student_val = float(str(student_ans).strip())
        if abs(student_val - expected) > 1e-6:
            warnings.append(
                f"Q{question.question_no}: math mismatch — expected {expected}, "
                f"student answered {student_val}"
            )
    except (ValueError, TypeError):
        pass  # Non-numeric answer — skip

    return warnings


# ---------------------------------------------------------------------------
# Public validation entry point
# ---------------------------------------------------------------------------

class Validator:
    """
    Runs a suite of validation checks on the assembled HomeworkResponse.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.60,
    ):
        self._threshold = confidence_threshold

    def validate(self, response: HomeworkResponse) -> ValidationResult:
        """
        Run all checks. Returns ValidationResult.
        Model warnings from each page are merged into validation.warnings.
        response.warnings is NOT used — everything lives in validation.
        """
        issues: list[str] = []
        warnings: list[str] = []

        for page in response.pages:
            # Collect model-emitted warnings (Item 4)
            for w in page.warnings:
                mw = f"Page {page.page_number} [model]: {w}"
                if mw not in warnings:
                    warnings.append(mw)

            page_warnings, page_issues = self._validate_page(page)
            warnings.extend(page_warnings)
            issues.extend(page_issues)

        # Global confidence check (null-safe)
        if response.confidence is not None and response.confidence < self._threshold:
            warnings.append(
                f"Overall confidence {response.confidence:.2f} is below threshold {self._threshold}"
            )

        # Item 4: single source of truth — do NOT duplicate into response.warnings
        response.warnings.clear()

        passed = len(issues) == 0
        result = ValidationResult(passed=passed, issues=issues, warnings=warnings)
        logger.info(
            "Validation: passed=%s  issues=%d  warnings=%d",
            passed, len(issues), len(warnings),
        )
        return result

    def _validate_page(self, page: Page) -> tuple[list[str], list[str]]:
        warnings: list[str] = []
        issues: list[str] = []
        p = page.page_number

        # --- Check: regions present (only meaningful when layout pipeline is on) ---
        if settings.use_layout_regions and not page.regions:
            warnings.append(f"Page {p}: no layout regions detected")

        # --- Check: sections / questions present ---
        if not page.sections:
            issues.append(f"Page {p}: no sections extracted by VLM")

        all_questions: list[Question] = []
        for sec in page.sections:
            all_questions.extend(sec.questions)

        # --- Check: low-confidence questions (null-safe) ---
        low_conf = [
            q for q in all_questions
            if q.confidence is not None and q.confidence < self._threshold
        ]
        if low_conf:
            qnos = [q.question_no or "?" for q in low_conf]
            warnings.append(
                f"Page {p}: {len(low_conf)} question(s) with low confidence: {qnos}"
            )

        # --- Check: question numbers not empty ---
        no_number = [q for q in all_questions if not q.question_no]
        if no_number:
            warnings.append(
                f"Page {p}: {len(no_number)} question(s) have no question number"
            )

        # --- Check: duplicate question_id ---
        qids = [q.question_id for q in all_questions if q.question_id]
        seen_ids: set[str] = set()
        dup_ids: list[str] = []
        for qid in qids:
            if qid in seen_ids:
                dup_ids.append(qid)
            seen_ids.add(qid)
        if dup_ids:
            issues.append(f"Page {p}: duplicate question_id(s) detected: {dup_ids}")

        # --- Check: answer_area bboxes ---
        for q in all_questions:
            for area in q.answer_areas:
                probs = validate_answer_area_bbox(
                    area.bbox, label=q.question_id or q.question_no or "?"
                )
                for prob in probs:
                    warnings.append(f"Page {p}: invalid answer_area bbox — {prob}")

        # --- Check: math answers ---
        for q in all_questions:
            math_warns = _check_math_question(q)
            warnings.extend(math_warns)

        # --- Check: bbox bounds ---
        if page.width and page.height:
            for region in page.regions:
                x1, y1, x2, y2 = region.bbox
                if x1 < 0 or y1 < 0 or x2 > page.width or y2 > page.height:
                    warnings.append(
                        f"Page {p}: region {region.region_id} bbox {region.bbox} exceeds page bounds"
                    )

        # --- Check: unknown question types → ISSUE (fail validation) ---
        unknowns = [q for q in all_questions if q.type == QuestionType.UNKNOWN]
        if unknowns:
            for q in unknowns:
                raw = ""
                if q.review and q.review.detail and q.review.detail.startswith("unrecognised_type:"):
                    raw = f" (raw={q.review.detail.split(':', 1)[1]!r})"
                issues.append(
                    f"Page {p}: question {q.question_id or q.question_no or '?'} "
                    f"has unrecognised type{raw}"
                )

        # --- Check: invalid answer_area kind values → warning ---
        for q in all_questions:
            for area in q.answer_areas:
                if area.kind not in QUESTION_KINDS:
                    warnings.append(
                        f"Page {p}: [{q.question_id or q.question_no}] answer_area has "
                        f"unrecognised kind={area.kind!r} (allowed: {sorted(QUESTION_KINDS)})"
                    )

        return warnings, issues
