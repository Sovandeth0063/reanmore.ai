"""
File: orchestrator/app/services/nlu/interpretation_schema.py
Description: Structured Pydantic Interpretation Schema, Correction Marker Parser,
             and Disjunctive Inquiry Resolver (Sprint 2 - Task 2.1).
             Adheres to the core principle: "LLM interprets, code judges."
"""

import re
from typing import Optional, List, Literal, Tuple
from pydantic import BaseModel, Field

from app.services.guardrails.pii_scrubber import scrub_student_pii


# ─────────────────────────────────────────────────────────────────────────────
# Structured Pydantic Interpretation Schema
# ─────────────────────────────────────────────────────────────────────────────

class StudentInterpretation(BaseModel):
    """
    Standardized semantic interpretation output from LLM tier.
    Code alone uses this to route and evaluate; the LLM never determines correctness.
    """
    primary_intent: Literal[
        "answer_attempt",
        "clarify",
        "hint_request",
        "answer_demand",
        "off_topic",
        "safety_concern",
        "unclear"
    ]
    safety_severity: Optional[Literal["low_frustration", "moderate_distress", "critical_harm"]] = None
    safety_rationale: Optional[str] = None
    secondary_intent: Optional[Literal["clarify", "hint_request"]] = None
    answer_candidates: List[str] = Field(
        default_factory=list,
        description="Chronological raw answer candidate tokens mentioned in student input."
    )
    detected_language: Literal["km", "en", "mixed"] = "en"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    resolved_candidate: Optional[str] = Field(
        default=None,
        description="Final selected candidate after applying correction markers or disambiguation."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Correction Markers & Disjunctive Inquiry Parser
# ─────────────────────────────────────────────────────────────────────────────

# Explicit correction markers indicating student changed their mind
_EN_CORRECTION_MARKERS = [
    r"\bno\s+wait\b",
    r"\bi\s+mean\b",
    r"\bsorry\b",
    r"\bactually\b",
    r"\bwait\s+no\b",
    r"\bnot\s+\d+\b",
]

_KH_CORRECTION_MARKERS = [
    r"អត់ទេ",
    r"ខុសហើយ",
    r"គឺ",
    r"វិញ",
    r"សុំទោស",
]

# Disjunctive inquiry pattern: "is it X or Y?", "តើ X ឬ Y?"
_DISJUNCTIVE_INQUIRY_RE = re.compile(
    r"(?:\b(?:is\s+it|could\s+it\s+be|what\s+about)\s+([^?]+?)\s+or\s+([^?]+?)\??$|"
    r"តើ\s*([^?]+?)\s*(?:ឬ|ឬក៏)\s*([^?]+?)(?:\?|$))",
    re.IGNORECASE
)


def has_correction_marker(text: str) -> bool:
    """Checks whether text contains an explicit student correction marker."""
    lower = text.lower()
    for pat in _EN_CORRECTION_MARKERS:
        if re.search(pat, lower):
            return True
    for pat in _KH_CORRECTION_MARKERS:
        if re.search(pat, text):
            return True
    return False


def is_disjunctive_inquiry(text: str) -> bool:
    """
    Detects whether the input is a questioning inquiry between two possibilities
    (e.g., 'Is it 14 or 15?' or 'តើ ១៤ ឬ ១៥?').
    Such queries must route to clarify / unclear, never adopting the second number!
    """
    if has_correction_marker(text):
        return False
    return bool(_DISJUNCTIVE_INQUIRY_RE.search(text.strip()))


def resolve_answer_candidates(raw_text: str, candidates: List[str]) -> Tuple[Optional[str], str]:
    """
    Resolves the final candidate answer token from candidates list based on correction markers:
    1. If a disjunctive inquiry (e.g. 'Is it 14 or 15?'), returns (None, 'disjunctive_inquiry').
    2. If multiple candidates and correction marker present ('I think 10, no wait 15'), returns last candidate.
    3. If multiple candidates without correction marker, returns first candidate or flags ambiguous.
    4. If single candidate, returns candidate.
    """
    if not candidates:
        return None, "no_candidates"

    if is_disjunctive_inquiry(raw_text):
        return None, "disjunctive_inquiry"

    if len(candidates) == 1:
        return candidates[0], "single_candidate"

    if has_correction_marker(raw_text):
        # Adopt the last candidate following the explicit correction
        return candidates[-1], "correction_marker_applied"

    # Multiple candidates without correction: adopt primary candidate
    return candidates[0], "first_candidate_selected"
