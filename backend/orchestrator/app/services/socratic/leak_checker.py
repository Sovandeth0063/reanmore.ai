"""
File: orchestrator/app/services/socratic/leak_checker.py
Description: State-Aware Numeric-Token Leak Checker & Multi-Step Praise Shield (Sprint 4a - Task 4a.5).
             - Tokenizes numeric values and evaluates arithmetic expressions (e.g. '30/2')
               to prevent subtle answer leakage.
             - State-aware Praise Shield: When a step is solved, bypass is strictly scoped to that step's target.
               All future unsolved steps (S_{k+1..N}) and the final answer remain under zero-tolerance leak defense.
             - Word/digit boundary checks: Ensures '15' does not false-positive on '150' or '1.5'.
             - Problem text exemption: Numbers explicitly given in the problem statement are exempted.
             - Replaces leaked replies with deterministic pedagogical fallback clues or safe praise templates.
"""

import re
from typing import Tuple, Optional, List, Set
from fractions import Fraction

from app.core.tutoring_config import (
    SAFE_PRAISE_FALLBACK_ENG,
    SAFE_PRAISE_FALLBACK_KHMER,
    SAFE_CLUE_FALLBACK_ENG,
    SAFE_CLUE_FALLBACK_KHMER
)
from app.services.socratic.invariants import (
    normalize_student_input,
    extract_raw_input_numeric_tokens,
    _ALL_NUMBER_WORDS_SORTED
)
from app.services.socratic.safe_math import safe_eval_ast, safe_eval_float

_KHMER_DIGITS_MAP = {ord(k): ord(e) for k, e in zip("០១២៣៤៥៦៧៨៩", "0123456789")}

# Proximity encouragement patterns that could invite brute-force guessing
_PROXIMITY_FEEDBACK_RE = re.compile(
    r"\b(?:just\s+(?:1|one|2|two)\s+away|off\s+by\s+(?:1|one|2|two)|almost\s+there,\s+so\s+close)\b",
    re.IGNORECASE
)

# Backward compatibility alias
SAFE_CLUE_FALLBACK = SAFE_CLUE_FALLBACK_ENG
SAFE_CONCEPTUAL_GUIDANCE = SAFE_CLUE_FALLBACK_ENG


def _extract_target_value(target_answer: str) -> Optional[Fraction]:
    """Extracts target answer as a Fraction value."""
    if not target_answer:
        return None
    cleaned = target_answer.strip().translate(_KHMER_DIGITS_MAP)
    return safe_eval_ast(cleaned)


def _contains_khmer(text: str) -> bool:
    """Checks if text contains Khmer Unicode characters."""
    return any(0x1780 <= ord(c) <= 0x17FF for c in text)


# Pattern capturing sequences of digits and separators (dots, commas, slashes)
# Permits adjacent letters on either side (e.g. "គឺ15", "15cm", "5,10,15", "1,500")
_DIGIT_RUN_RE = re.compile(
    r"[-+−]?[0-9\u17E0-\u17E9]+(?:[.,/][0-9\u17E0-\u17E9]+)*"
)

# Multi-term arithmetic expression pattern (e.g. "10 + 5", "3 * 5", "30 / 2", "0.5 * 30")
_ARITHMETIC_EXPR_RE = re.compile(
    r"(?<![0-9\u17E0-\u17E9.,/])[-+−]?[0-9\u17E0-\u17E9]+(?:\.[0-9\u17E0-\u17E9]+)?(?:\s*[-+*/]\s*[-+−]?[0-9\u17E0-\u17E9]+(?:\.[0-9\u17E0-\u17E9]+)?)+(?![0-9\u17E0-\u17E9])"
)


def _normalize_arithmetic_and_word_expressions(text: str) -> str:
    """
    Expands word arithmetic, symbols, English/Khmer number words, and operators into AST-evaluable strings.
    Crucially preserves commas so that digit runs like '1,500' and lists like '5,10,15' can be evaluated
    under all plausible interpretations (decimals, thousands, and list items) by _generate_plausible_readings.
    """
    t = text.strip()

    # 1. Translate Khmer numerals to Arabic digits
    t = t.translate(_KHMER_DIGITS_MAP)

    # 2. Canonicalize Khmer compound vowels (U+17C1 'េ' + U+17B6 'ា' -> U+17C4 'ោ')
    t = t.replace("\u17C1\u17B6", "\u17C4")

    # 3. Handle word arithmetic BEFORE single number word substitution
    # English word arithmetic
    t = re.sub(r"(?i)\bhalf\s+of\s+", "0.5 * ", t)
    t = re.sub(r"(?i)\b1/2\s+of\s+", "0.5 * ", t)
    t = re.sub(r"(?i)\bquarter\s+of\s+", "0.25 * ", t)
    t = re.sub(r"(?i)\b1/4\s+of\s+", "0.25 * ", t)
    t = re.sub(r"(?i)\bdivided\s+by\b", " / ", t)
    t = re.sub(r"(?i)\btimes\b", " * ", t)
    t = re.sub(r"(?i)\bplus\b", " + ", t)
    t = re.sub(r"(?i)\bminus\b", " - ", t)

    # Khmer word arithmetic
    t = re.sub(r"កន្លះនៃ\s*", "0.5 * ", t)
    t = re.sub(r"ចែកនឹង\s*", " / ", t)
    t = re.sub(r"គុណនឹង\s*", " * ", t)
    t = re.sub(r"បូកនឹង\s*|បូក\s*", " + ", t)
    t = re.sub(r"ដកនឹង\s*|ដក\s*", " - ", t)

    # 4. Operator symbols
    t = t.replace("×", " * ").replace("÷", " / ")

    # 5. 'x' multiplication between digits (e.g. "3x5" or "3 x 5")
    t = re.sub(r"(\d+)\s*[xX]\s*(\d+)", r"\1 * \2", t)

    # 6. Replace number words (greedy longest-match)
    # Using \b for English words to protect words like "them", "making", etc.
    for word, digit_str in _ALL_NUMBER_WORDS_SORTED:
        if word in t:
            if any(0x1780 <= ord(c) <= 0x17FF for c in word):
                t = t.replace(word, f" {digit_str} ")
            else:
                t = re.sub(rf"\b{re.escape(word)}\b", f" {digit_str} ", t, flags=re.IGNORECASE)

    # 7. Clean extra whitespace
    t = re.sub(r"[ \t]+", " ", t).strip()
    return t


def _generate_plausible_readings(token: str) -> List[Tuple[Fraction, str]]:
    """
    Evaluates every plausible numerical interpretation of a token:
    - Pure value: '15' -> 15, '30/2' -> 15
    - Comma as thousands: '1,500' -> 1500
    - Comma as decimal dot: '1,500' -> 1.5, '1,5' -> 1.5
    - Comma as list separator: '5,10,15' -> [5, 10, 15], '1,500' -> [1, 500]
    """
    results: List[Tuple[Fraction, str]] = []
    t_clean = token.strip().translate(_KHMER_DIGITS_MAP).replace("−", "-")

    # 1. Direct AST evaluation
    val = safe_eval_ast(t_clean)
    if val is not None:
        results.append((val, t_clean))

    # 2. Comma interpretations
    if "," in t_clean:
        # A. Comma as thousands separator (e.g. 1,500 -> 1500)
        t_no_comma = t_clean.replace(",", "")
        val_no_comma = safe_eval_ast(t_no_comma)
        if val_no_comma is not None:
            results.append((val_no_comma, t_no_comma))

        # B. Comma as decimal dot (e.g. 1,5 -> 1.5, 1,500 -> 1.5)
        t_dot = t_clean.replace(",", ".")
        val_dot = safe_eval_ast(t_dot)
        if val_dot is not None:
            results.append((val_dot, t_dot))

        # C. Comma as list separator (e.g. '5,10,15' -> 5, 10, 15)
        subparts = [p.strip() for p in t_clean.split(",") if p.strip()]
        if len(subparts) > 1:
            for p in subparts:
                p_val = safe_eval_ast(p)
                if p_val is not None:
                    results.append((p_val, p))

    return results


def _token_matches_value(text: str, target_val: Fraction, exempted_tokens: Set[str]) -> Tuple[bool, Optional[str]]:
    """
    Checks if text contains any numeric token, list item, or arithmetic expression equaling target_val.
    Evaluates all plausible readings (decimals, thousands, lists, arithmetic expressions).
    """
    norm_text = _normalize_arithmetic_and_word_expressions(text)

    # 1. Extract digit-run tokens and test all plausible interpretations
    candidate_tokens = _DIGIT_RUN_RE.findall(norm_text)
    for tok in candidate_tokens:
        tok_clean = tok.strip().translate(_KHMER_DIGITS_MAP).replace("−", "-")
        if tok_clean in exempted_tokens:
            continue
        readings = _generate_plausible_readings(tok_clean)
        for cand_val, cand_repr in readings:
            if cand_repr in exempted_tokens:
                continue
            if cand_val == target_val:
                return True, tok_clean

    # 2. Check multi-term arithmetic expressions (e.g. "10 + 5", "3 * 5", "0.5 * 30")
    expr_candidates = _ARITHMETIC_EXPR_RE.findall(norm_text)
    for expr in expr_candidates:
        expr_clean = expr.strip().translate(_KHMER_DIGITS_MAP).replace("−", "-")
        if expr_clean in exempted_tokens:
            continue
        expr_val = safe_eval_ast(expr_clean)
        if expr_val is not None and expr_val == target_val:
            return True, expr_clean

    return False, None


def check_tutor_response_leak(
    tutor_reply: str,
    target_answer: str,
    is_step_solved: bool = False,
    is_reveal_state: Optional[bool] = None,
    current_hint_tier: int = 0,
    step_number: Optional[int] = None,
    attempts_count: int = 1,
    unsolved_step_values: Optional[List[str]] = None,
    final_answer: Optional[str] = None,
    problem_text: Optional[str] = None
) -> Tuple[bool, str, str]:
    """
    Evaluates tutor reply for answer leakage and guessing game proximity signals.

    Args:
        tutor_reply:          Proposed tutor response text
        target_answer:        Expected answer string for current step (e.g. '15')
        is_step_solved:       True if the student has already correctly solved this step
        is_reveal_state:      Explicit boolean: True ONLY after student completed 3 failed attempts and requested reveal.
                              When False, strictly forbids reveal even if current_hint_tier >= 3.
                              When None, falls back to legacy current_hint_tier >= 3 check.
        current_hint_tier:    Hint tier 0, 1, 2, or 3 (3 = analogous worked example)
        step_number:          Active step number (to allow e.g. 'Step 2')
        attempts_count:       Number of student attempts on the current step
        unsolved_step_values: List of answer values for future unsolved steps (Task 4a.5)
        final_answer:         Problem final answer (Task 4a.5)
        problem_text:         Original problem text to exempt stated numbers (Task 4a.5)

    Returns:
        (is_leak_detected: bool, final_reply: str, reason: str)
    """
    if not tutor_reply or not target_answer:
        return False, tutor_reply, "empty_input"

    # Extract numbers in the problem statement that are safe to mention,
    # BUT EXCLUDE any problem numbers that collide with the active target or any unsolved target!
    exempted_tokens: Set[str] = set()
    if problem_text:
        raw_exempted = extract_raw_input_numeric_tokens(problem_text)
        active_and_unsolved: Set[Fraction] = set()
        t_val = _extract_target_value(target_answer)
        if t_val is not None:
            active_and_unsolved.add(t_val)
        for u in (unsolved_step_values or []):
            u_v = _extract_target_value(u)
            if u_v is not None:
                active_and_unsolved.add(u_v)
        if final_answer:
            f_v = _extract_target_value(final_answer)
            if f_v is not None:
                active_and_unsolved.add(f_v)

        for tok in raw_exempted:
            tok_v = safe_eval_ast(tok)
            # Only exempt if it does not collide with active/unsolved targets
            if tok_v is not None and tok_v not in active_and_unsolved:
                exempted_tokens.add(tok)
            elif tok_v is None and tok.lower() not in {target_answer.lower()} | {u.lower() for u in (unsolved_step_values or [])}:
                exempted_tokens.add(tok)

    # Normalize reply (translate Khmer digits)
    norm_reply = tutor_reply.translate(_KHMER_DIGITS_MAP)

    # Exclude active step label indicator (e.g. "Step 2" or "ជំហានទី ២")
    cleaned_reply = re.sub(r"(?i)\bstep\s+\d+\b", " ", norm_reply)
    cleaned_reply = re.sub(r"ជំហានទី\s*\d+", " ", cleaned_reply)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Multi-Step Praise Shield (Item 2 / Task 4a.5):
    # Even if current step is solved, check future unsolved steps & final answer!
    # ─────────────────────────────────────────────────────────────────────────
    future_targets = list(unsolved_step_values or [])
    if final_answer and final_answer not in future_targets:
        future_targets.append(final_answer)

    for future_t in future_targets:
        if not future_t:
            continue
        fut_val = _extract_target_value(future_t)
        if fut_val is not None:
            leaked, leaked_tok = _token_matches_value(cleaned_reply, fut_val, exempted_tokens)
            if leaked:
                fallback = SAFE_PRAISE_FALLBACK_KHMER if _contains_khmer(tutor_reply) else SAFE_PRAISE_FALLBACK_ENG
                return True, fallback, f"unsolved_future_step_leak_detected ({leaked_tok})"
        else:
            # Word target
            w_target = future_t.strip().lower()
            if len(w_target) >= 4 and w_target in cleaned_reply.lower() and w_target not in exempted_tokens:
                fallback = SAFE_PRAISE_FALLBACK_KHMER if _contains_khmer(tutor_reply) else SAFE_PRAISE_FALLBACK_ENG
                return True, fallback, f"unsolved_future_concept_leak_detected ({w_target})"

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Current Step State Awareness:
    # Disclosure of CURRENT step is allowed ONLY if the step is solved or in explicit RevealState.
    # When is_reveal_state=False, disclosure is strictly forbidden even at Hint Tier 3.
    # ─────────────────────────────────────────────────────────────────────────
    reveal_allowed = is_step_solved or (
        is_reveal_state if is_reveal_state is not None else (current_hint_tier >= 3)
    )
    if reveal_allowed:
        return False, tutor_reply, "state_allows_answer"



    # ─────────────────────────────────────────────────────────────────────────
    # 3. Check current step leakage:
    # ─────────────────────────────────────────────────────────────────────────
    target_val = _extract_target_value(target_answer)
    clue_fallback = SAFE_CLUE_FALLBACK_KHMER if _contains_khmer(tutor_reply) else SAFE_CLUE_FALLBACK_ENG

    if target_val is None:
        # Non-numeric target (e.g. word concept 'chloroplast')
        target_word = target_answer.strip().lower()
        if len(target_word) >= 4 and target_word in cleaned_reply.lower() and target_word not in exempted_tokens:
            return True, clue_fallback, "concept_word_leak_detected"
        return False, tutor_reply, "non_numeric_clean"

    leaked, leaked_tok = _token_matches_value(cleaned_reply, target_val, exempted_tokens)
    if leaked:
        return True, clue_fallback, f"numeric_answer_leak_detected ({leaked_tok})"

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Proximity Feedback Constraint:
    # Near-miss proximity feedback ("You're just 1 away!") is restricted to at most once per step.
    # ─────────────────────────────────────────────────────────────────────────
    if _PROXIMITY_FEEDBACK_RE.search(tutor_reply):
        if attempts_count > 1:
            sanitized = _PROXIMITY_FEEDBACK_RE.sub("Let's review the step carefully", tutor_reply)
            return False, sanitized, "proximity_feedback_constrained"

    return False, tutor_reply, "clean_no_leak"


def check_response_for_leaks(
    tutor_response: str,
    solved_step_value: Optional[str] = None,
    unsolved_step_values: Optional[List[str]] = None,
    final_answer: Optional[str] = None,
    problem_text: Optional[str] = None,
    is_step_solved: bool = True
) -> Tuple[str, bool]:
    """
    Convenience wrapper for multi-step praise checking.
    Returns:
        (sanitized_response: str, was_quarantined: bool)
    """
    target = solved_step_value or ""
    is_leak, final_reply, _ = check_tutor_response_leak(
        tutor_reply=tutor_response,
        target_answer=target,
        is_step_solved=is_step_solved,
        unsolved_step_values=unsolved_step_values,
        final_answer=final_answer,
        problem_text=problem_text
    )
    return final_reply, is_leak
