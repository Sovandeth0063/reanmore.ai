"""
File: orchestrator/app/services/socratic/leak_checker.py
Description: Backward-compatibility shim for Output Leak Barrier.
             All leak guard logic has been relocated and strengthened in:
             `app.services.guardrails.leak_guard` (Spec Section 9).
             This module re-exports all symbols to preserve existing imports.
"""

from app.services.guardrails.leak_guard import (
    _KHMER_DIGITS_MAP,
    _PROXIMITY_FEEDBACK_RE,
    _DIGIT_RUN_RE,
    _ARITHMETIC_EXPR_RE,
    SAFE_PRAISE_FALLBACK_ENG,
    SAFE_PRAISE_FALLBACK_KHMER,
    SAFE_CLUE_FALLBACK_ENG,
    SAFE_CLUE_FALLBACK_KHMER,
    SAFE_CLUE_FALLBACK,
    SAFE_CONCEPTUAL_GUIDANCE,
    _extract_target_value,
    _contains_khmer,
    _normalize_arithmetic_and_word_expressions,
    _generate_plausible_readings,
    _token_matches_value,
    check_tutor_response_leak,
    check_response_for_leaks,
    LeakGuard,
)

__all__ = [
    "_KHMER_DIGITS_MAP",
    "_PROXIMITY_FEEDBACK_RE",
    "_DIGIT_RUN_RE",
    "_ARITHMETIC_EXPR_RE",
    "SAFE_PRAISE_FALLBACK_ENG",
    "SAFE_PRAISE_FALLBACK_KHMER",
    "SAFE_CLUE_FALLBACK_ENG",
    "SAFE_CLUE_FALLBACK_KHMER",
    "SAFE_CLUE_FALLBACK",
    "SAFE_CONCEPTUAL_GUIDANCE",
    "_extract_target_value",
    "_contains_khmer",
    "_normalize_arithmetic_and_word_expressions",
    "_generate_plausible_readings",
    "_token_matches_value",
    "check_tutor_response_leak",
    "check_response_for_leaks",
    "LeakGuard",
]
