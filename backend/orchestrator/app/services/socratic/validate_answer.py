"""
File: orchestrator/app/services/socratic/validate_answer.py
Description: Rich Answer Validation Node for the Socratic tutoring pipeline (Sprint 4a - Task 4a.3 & 4a.4).
             Evaluates student attempts with three-tier granularity:
             - "correct": Full credit, advances to next step or completes problem.
             - "partial": Near-miss (strictly non-directional identical feedback within +/- 1),
                          unit mismatch, or partial science concept.
             - "incorrect": Off-target answer, increments hint tier / escalates.
             Adheres to Grader Order of Operations: Normalize -> Extract -> Trace -> Evaluate.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from fractions import Fraction

from app.core.tutoring_config import (
    PROXIMITY_FEEDBACK_TOLERANCE,
    MAX_ATTEMPTS_BEFORE_REVEAL,
    NEAR_MISS_FEEDBACK_ENG,
    NEAR_MISS_FEEDBACK_KHMER,
    PROPERTY_QUERY_DEFLECTION_ENG,
    PROPERTY_QUERY_DEFLECTION_KHMER
)
from app.services.socratic.invariants import (
    normalize_student_input,
    extract_raw_input_numeric_tokens
)
from app.services.socratic.safe_math import safe_eval_ast

logger = logging.getLogger("orchestrator.socratic.validate_answer")

VALIDATION_CORRECT = "correct"
VALIDATION_PARTIAL = "partial"
VALIDATION_INCORRECT = "incorrect"


@dataclass
class RevealState:
    """
    Explicit tracking of reveal state, decoupled from HintLevel 3.
    Hint Level 3 = analogous worked example with active problem numbers withheld.
    RevealState = activated only after 3 failed attempts, offering the worked solution.
    """
    is_reveal_active: bool = False
    attempts_count: int = 0
    max_attempts: int = MAX_ATTEMPTS_BEFORE_REVEAL
    worked_example_shown: bool = False
    solution_revealed: bool = False

    @property
    def allows_answer_disclosure(self) -> bool:
        """Only allowed if solution has been explicitly revealed after reaching max attempts."""
        return self.is_reveal_active and self.attempts_count >= self.max_attempts and self.solution_revealed


@dataclass
class ValidationOutcome:
    outcome: str               # "correct" | "partial" | "incorrect"
    is_correct: bool           # True only for VALIDATION_CORRECT
    is_partial: bool           # True for VALIDATION_PARTIAL
    feedback_eng: str
    feedback_khmer: str
    numeric_diff: Optional[float] = None
    unit_mismatch: bool = False
    is_near_miss: bool = False       # Flag for proximity feedback
    is_property_probe: bool = False  # Flag for binary search / property query deflection


_PROPERTY_CONFIRMATION_RE = re.compile(
    r"(?:\b(?:is\s+it\s+(?:even|odd|greater|more|less|bigger|smaller|above|below)|"
    r"is\s+the\s+answer\s+(?:even|odd)|"
    r"does\s+it\s+(?:start|end)\s+with|"
    r"can\s+you\s+tell\s+me\s+if\s+it'?s)\b|"
    r"\bis\s+it\s*[><=]|"
    r"(?:តើ(?:ជា)?លេខ(?:គូ|សេស)|តើ(?:ធំ|តូច)ជាង|តើ(?:ចាប់ផ្តើម|បញ្ចប់)ដោយ|តើចម្លើយគឺ))",
    re.IGNORECASE
)


def check_property_confirmation_query(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Detects if student is attempting a binary search / 20-questions attack
    probing properties of the target answer ('Is it even?', 'Is it > 10?').
    Returns (is_property_query, deflection_eng, deflection_khmer).
    """
    if not text:
        return False, None, None
    if _PROPERTY_CONFIRMATION_RE.search(text):
        return True, PROPERTY_QUERY_DEFLECTION_ENG, PROPERTY_QUERY_DEFLECTION_KHMER
    return False, None, None


_UNIT_PATTERNS = [
    r"\b(?:cm|centimeters?|សង់ទីម៉ែត្រ|ស\.ម)\b",
    r"\b(?:m|meters?|ម៉ែត្រ|ម)\b",
    r"\b(?:km|kilometers?|គីឡូម៉ែត្រ|គ\.ម)\b",
    r"\b(?:kg|kilograms?|គីឡូក្រាម|គីឡូ|គ\.ក្រ)\b",
    r"\b(?:g|grams?|ក្រាម)\b",
    r"\b(?:apples?|ផ្លែប៉ោម)\b",
    r"\b(?:cookies?|នំ)\b",
    r"\b(?:candies?|ស្ករគ្រាប់)\b",
    r"\b(?:dollars?|\$|ដុល្លារ)\b",
    r"\b(?:riels?|រៀល|៛)\b",
    r"\b(?:hours?|ម៉ោង)\b",
    r"\b(?:mins?|minutes?|នាទី)\b",
    r"\b(?:seconds?|secs?|វិនាទី)\b",
    r"\b(?:នាក់|គ្រាប់|ដើម)\b"
]


def _extract_number_and_unit(text: str) -> tuple[Optional[float], Optional[str]]:
    """Extracts numeric value (including fractions and percentages) and trailing unit after normalization."""
    t_norm = normalize_student_input(text).lower()

    # Detect unit if present
    found_unit = None
    for pat in _UNIT_PATTERNS:
        m = re.search(pat, t_norm)
        if m:
            found_unit = m.group(0)
            t_norm = t_norm[:m.start()] + t_norm[m.end():]
            break

    t_norm = t_norm.strip()

    # Percentage: e.g. 50%
    if t_norm.endswith("%"):
        try:
            val = float(t_norm[:-1].strip()) / 100.0
            return val, "percent"
        except ValueError:
            pass

    # Fraction: e.g. 1/2 or 3/4
    if "/" in t_norm:
        parts = t_norm.split("/")
        if len(parts) == 2:
            try:
                num = float(parts[0].strip())
                denom = float(parts[1].strip())
                if denom != 0:
                    return num / denom, found_unit
            except ValueError:
                pass

    # Signed Decimal or integer
    nums = re.findall(r"[-+]?\d*\.?\d+", t_norm)
    if nums:
        try:
            return float(nums[0]), found_unit
        except ValueError:
            pass

    return None, found_unit


# ─────────────────────────────────────────────────────────────────────────────
# Science Conceptual Groups for Partial Matching
# ─────────────────────────────────────────────────────────────────────────────

_SCIENCE_CONCEPTS: List[Dict[str, Any]] = [
    {
        "name": "evaporation",
        "primary": [
            "evaporation", "evaporates", "evaporate", "vaporization",
            "liquid to gas", "liquid turns into gas", "water turns into gas",
            "water to gas", "រំហួត", "រំហួតទឹក", "ក្លាយជាចំហាយ"
        ],
        "partials": ["steam", "gas", "vapor", "heat", "ចំហាយ", "ក្តៅ"],
        "feedback_eng": "You noticed the steam/gas forming! That process where liquid turns to gas is called **evaporation**.",
        "feedback_khmer": "អ្នកបានសម្គាល់ឃើញចំហាយទឹក! ដំណើរការដែលទឹកក្លាយជាចំហាយហៅថា **រំហួត**។",
    },
    {
        "name": "condensation",
        "primary": ["condensation", "condense", "condenses", "កំណក", "កំណកទឹក"],
        "partials": ["droplets", "drops", "cools", "gas to liquid", "ដំណក់ទឹក", "ត្រជាក់"],
        "feedback_eng": "Good observation about the water droplets! When steam cools down into liquid, that is **condensation**.",
        "feedback_khmer": "ការសង្កេតល្អណាស់ចំពោះដំណក់ទឹក! នៅពេលចំហាយចុះត្រជាក់ក្លាយជាទឹក ហៅថា **កំណក**។",
    },
    {
        "name": "photosynthesis",
        "primary": ["photosynthesis", "រស្មីសំយោគ"],
        "partials": ["sunlight", "sun", "water", "food", "leaves", "ពន្លឺព្រះអាទិត្យ", "ទឹក", "អាហារ"],
        "feedback_eng": "Great clue! Plants use sunlight and water to make food — that amazing process is called **photosynthesis**.",
        "feedback_khmer": "តម្រុយល្អណាស់! រុក្ខជាតិប្រើពន្លឺព្រះអាទិត្យ និងទឹកដើម្បីបង្កើតអាហារ ដែលហៅថា **រស្មីសំយោគ**។",
    },
    {
        "name": "vertebrates",
        "primary": ["vertebrate", "vertebrates", "has backbone", "ឆ្អឹងកង", "ឆ្អឹងខ្នង", "សត្វមានឆ្អឹងកង"],
        "partials": ["backbone", "spine", "bones", "ឆ្អឹង"],
        "feedback_eng": "You're right about having a backbone! Animals with a backbone are called **vertebrates**.",
        "feedback_khmer": "អ្នកនិយាយត្រូវអំពីឆ្អឹងខ្នង! សត្វដែលមានឆ្អឹងកងហៅថា **សត្វមានឆ្អឹងកង**។",
    },
    {
        "name": "producers",
        "primary": ["producer", "producers", "makes own food", "អ្នកផលិត"],
        "partials": ["plant", "plants", "grass", "tree", "រុក្ខជាតិ", "ស្មៅ", "ដើមឈើ"],
        "feedback_eng": "Plants make their own food! In the food chain, organisms that make their own food are **producers**.",
        "feedback_khmer": "រុក្ខជាតិបង្កើតអាហារដោយខ្លួនឯង! ក្នុងខ្សែច្រវាក់អាហារ ពួកវាជា **អ្នកផលិត**។",
    },
    {
        "name": "consumers",
        "primary": ["consumer", "consumers", "eats others", "អ្នកស៊ី", "អ្នកប្រើប្រាស់"],
        "partials": ["animal", "animals", "eats", "hunter", "សត្វ", "ស៊ី"],
        "feedback_eng": "Animals must eat other living things! That makes them **consumers** in the food chain.",
        "feedback_khmer": "សត្វត្រូវតែស៊ីភាវរស់ដទៃ! ដូច្នេះពួកវាជា **អ្នកស៊ី** ក្នុងខ្សែច្រវាក់អាហារ។",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Master Validation Function
# ─────────────────────────────────────────────────────────────────────────────

def validate_student_answer(
    student_attempt: str,
    expected_answer: str,
    acceptable_answers: Optional[List[str]] = None,
    subject: str = "math",
    step_id: Optional[str] = None,
    reveal_state: Optional[RevealState] = None
) -> ValidationOutcome:
    """
    Evaluates student answer following the 4-stage Grader Order of Operations:
    0. Multi-Turn Zero Property Confirmation: Deflects 20-questions guessing attacks without LLM.
    1. Normalize student attempt and expected answer (with locale comma context awareness).
    2. Candidate token extraction.
    3. Check exact match, cross-language booleans, numeric equivalence.
    4. Near-miss non-directional invariant: Identical clue for all wrong guesses in T +/- 1.
    """
    s_raw = (student_attempt or "").strip()
    e_raw = (expected_answer or "").strip()

    if not s_raw or not e_raw:
        return ValidationOutcome(
            outcome=VALIDATION_INCORRECT,
            is_correct=False,
            is_partial=False,
            feedback_eng="Please type or choose an answer to continue.",
            feedback_khmer="សូមវាយបញ្ចូល ឬជ្រើសរើសចម្លើយដើម្បីបន្ត។",
        )

    # 0. Check Multi-Turn Zero-Property Confirmation Query
    is_prop, def_eng, def_kh = check_property_confirmation_query(s_raw)
    if is_prop and def_eng and def_kh:
        return ValidationOutcome(
            outcome=VALIDATION_PARTIAL,
            is_correct=False,
            is_partial=True,
            feedback_eng=def_eng,
            feedback_khmer=def_kh,
            is_property_probe=True
        )

    # 1. Normalize both inputs using unit context if present (never target value)
    _, s_unit_pre = _extract_number_and_unit(s_raw)
    _, e_unit_pre = _extract_number_and_unit(e_raw)
    active_unit = s_unit_pre or e_unit_pre

    s_clean = normalize_student_input(s_raw, context_unit=active_unit).lower()
    e_clean = normalize_student_input(e_raw, context_unit=active_unit).lower()

    # 1. Exact match check
    if s_clean == e_clean:
        return ValidationOutcome(
            outcome=VALIDATION_CORRECT,
            is_correct=True,
            is_partial=False,
            feedback_eng="Spot on! Your answer is correct!",
            feedback_khmer="ត្រឹមត្រូវហើយ! ចម្លើយរបស់អ្នកពិតជាត្រឹមត្រូវល្អណាស់!",
        )

    # Check acceptable_answers list if provided
    if acceptable_answers:
        for acc in acceptable_answers:
            acc_clean = normalize_student_input(acc).lower()
            if s_clean == acc_clean:
                return ValidationOutcome(
                    outcome=VALIDATION_CORRECT,
                    is_correct=True,
                    is_partial=False,
                    feedback_eng="Spot on! That's an accepted answer!",
                    feedback_khmer="ត្រឹមត្រូវហើយ! ចម្លើយនេះត្រូវបានទទួលស្គាល់!",
                )

    # 2. Affirmative / Negative Cross-Language Check
    affirmative = {"yes", "true", "correct", "y", "t", "has", "បាទ", "ចាស", "មាន", "ពិតជាមាន", "ត្រូវ", "ពិត"}
    negative = {"no", "false", "incorrect", "n", "f", "none", "ទេ", "គ្មាន", "មិនមាន", "អត់", "ខុស"}

    s_is_aff = any(s_clean == w or s_clean.startswith(w) for w in affirmative)
    e_is_aff = any(e_clean == w or e_clean.startswith(w) for w in affirmative)
    s_is_neg = any(s_clean == w or s_clean.startswith(w) for w in negative)
    e_is_neg = any(e_clean == w or e_clean.startswith(w) for w in negative)

    if (s_is_aff and e_is_aff) or (s_is_neg and e_is_neg):
        return ValidationOutcome(
            outcome=VALIDATION_CORRECT,
            is_correct=True,
            is_partial=False,
            feedback_eng="Spot on! That's correct!",
            feedback_khmer="ត្រឹមត្រូវហើយ!",
        )

    # 3. Numeric & Arithmetic Equivalence + Non-Directional Near-Miss Check
    s_val, s_unit = _extract_number_and_unit(s_clean)
    e_val, e_unit = _extract_number_and_unit(e_clean)

    if s_val is not None and e_val is not None:
        diff = abs(s_val - e_val)

        # Exact numeric match
        if diff < 0.001:
            # Check unit mismatch
            if s_unit and e_unit and s_unit != e_unit:
                return ValidationOutcome(
                    outcome=VALIDATION_PARTIAL,
                    is_correct=False,
                    is_partial=True,
                    feedback_eng=f"The number **{s_val}** is right, but check your units ({s_unit} vs {e_unit})!",
                    feedback_khmer=f"លេខ **{s_val}** ត្រឹមត្រូវហើយ ប៉ុន្តែសូមពិនិត្យមើលខ្នាតឡើងវិញ ({s_unit} និង {e_unit})!",
                    numeric_diff=0.0,
                    unit_mismatch=True,
                )
            return ValidationOutcome(
                outcome=VALIDATION_CORRECT,
                is_correct=True,
                is_partial=False,
                feedback_eng=f"Excellent! **{s_raw}** is the exact correct value!",
                feedback_khmer=f"ពូកែណាស់! **{s_raw}** គឺពិតជាតម្លៃត្រឹមត្រូវ!",
                numeric_diff=0.0,
            )

        # Invariant-Gated Near-Miss: Off by within PROXIMITY_FEEDBACK_TOLERANCE (Item 1)
        # Feedback is STRICTLY IDENTICAL for all wrong guesses in T +/- 1.
        # Zero directional cues ('try adding', 'count on') to prevent answer deduction.
        if diff <= (PROXIMITY_FEEDBACK_TOLERANCE + 0.001) and diff > 0.001:
            return ValidationOutcome(
                outcome=VALIDATION_PARTIAL,
                is_correct=False,
                is_partial=True,
                feedback_eng=NEAR_MISS_FEEDBACK_ENG,
                feedback_khmer=NEAR_MISS_FEEDBACK_KHMER,
                numeric_diff=diff,
                is_near_miss=True,
            )

    # 4. Science Partial Concept Matching
    for concept in _SCIENCE_CONCEPTS:
        if any(w in e_clean for w in concept["primary"]):
            if any(w in s_clean for w in concept["primary"]):
                return ValidationOutcome(
                    outcome=VALIDATION_CORRECT,
                    is_correct=True,
                    is_partial=False,
                    feedback_eng=f"Excellent! **{s_raw}** correctly identifies the concept of {concept['name']}!",
                    feedback_khmer="ពូកែណាស់! អ្នកបានឆ្លើយត្រូវចំគោលដៅវិទ្យាសាស្ត្រ!",
                )
            if any(w in s_clean for w in concept["partials"]):
                return ValidationOutcome(
                    outcome=VALIDATION_PARTIAL,
                    is_correct=False,
                    is_partial=True,
                    feedback_eng=concept["feedback_eng"],
                    feedback_khmer=concept["feedback_khmer"],
                )

    # 5. Fallback: Incorrect
    return ValidationOutcome(
        outcome=VALIDATION_INCORRECT,
        is_correct=False,
        is_partial=False,
        feedback_eng=f"**Let's rethink this together!** **{s_raw}** isn't quite right. Tap a hint if you need a clue!",
        feedback_khmer=f"**សាកល្បងគិតម្តងទៀតណា៎!** ចម្លើយ **{s_raw}** មិនទាន់ត្រឹមត្រូវឡើយ។ ចុចមើលតម្រុយដើម្បីជួយអ្នក!",
    )


def validate_socratic_answer(
    student_attempt: Optional[str] = None,
    expected_answer: Optional[str] = None,
    user_input: Optional[str] = None,
    target_value: Optional[str] = None,
    acceptable_answers: Optional[List[str]] = None,
    subject: str = "math",
    step_id: Optional[str] = None,
    reveal_state: Optional[RevealState] = None
) -> ValidationOutcome:
    """Flexible wrapper accepting both (student_attempt, expected_answer) and (user_input, target_value)."""
    attempt = student_attempt if student_attempt is not None else (user_input or "")
    target = expected_answer if expected_answer is not None else (target_value or "")
    return validate_student_answer(
        student_attempt=attempt,
        expected_answer=target,
        acceptable_answers=acceptable_answers,
        subject=subject,
        step_id=step_id,
        reveal_state=reveal_state
    )
