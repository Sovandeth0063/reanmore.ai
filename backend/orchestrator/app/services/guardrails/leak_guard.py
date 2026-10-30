"""
File: orchestrator/app/services/guardrails/leak_guard.py
Description: Output Leak Barrier & Socratic Invariant Enforcer (Spec Section 1, 2.3, 9, 10).
             - Deterministic scanner that checks every outgoing tutor message for:
               1. Expected step answer (numbers, fractions, decimals, units).
               2. Arithmetic expressions evaluating to the answer (e.g. '10 + 5', '30 / 2', '3x5').
               3. Word-to-number expansions (English & Khmer number words, composite words, fractions).
               4. Known answer phrasing ('the answer is X', 'equals X', 'ចម្លើយគឺ X').
               5. Non-numeric concept keywords (e.g. 'photosynthesis', 'gas', 'chloroplast').
             - Strict Tier 3 Socratic Prohibition:
               Tier 1, Tier 2, and Tier 3 hints NEVER disclose the step's target answer.
               Answer disclosure is permitted ONLY if is_step_solved=True OR is_reveal_state=True
               (explicit exit after 3 failed attempts in reveal_and_continue.py).
             - Multi-Step Praise Shield: When a step is solved, praise may reference the solved
               step's value, but all future unsolved steps (S_{k+1..N}) and the final answer
               remain under zero-tolerance leak defense.
             - Problem text exemption: Numbers explicitly given in the problem statement are exempted,
               provided they do not collide with active or unsolved targets.
             - Quarantines leaks by replacing them with deterministic pedagogical fallbacks.
"""

import re
import logging
from typing import Tuple, Optional, List, Set, Dict, Any
from fractions import Fraction

from app.core.tutoring_config import (
    SAFE_PRAISE_FALLBACK_ENG,
    SAFE_PRAISE_FALLBACK_KHMER,
    SAFE_CLUE_FALLBACK_ENG,
    SAFE_CLUE_FALLBACK_KHMER,
    SAFE_CLUE_FALLBACK_SCIENCE_ENG,
    SAFE_CLUE_FALLBACK_SCIENCE_KHMER,
)
from app.services.socratic.safe_math import safe_eval_ast, safe_eval_float

logger = logging.getLogger("orchestrator.guardrails.leak_guard")

# Basic elementary number words in English
_EN_NUMBER_WORDS: Dict[str, str] = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20",
    "thirty": "30", "forty": "40", "fifty": "50", "sixty": "60",
    "seventy": "70", "eighty": "80", "ninety": "90",
    "one hundred": "100", "hundred": "100", "one thousand": "1000", "thousand": "1000",
    "half": "1/2", "third": "1/3", "quarter": "1/4", "three quarters": "3/4"
}

# Comprehensive Khmer number words
_KH_NUMBER_WORDS: Dict[str, str] = {
    "មួយកន្លះ": "1.5", "ពីរកន្លះ": "2.5", "បីកន្លះ": "3.5", "ដប់កន្លះ": "10.5", "កន្លះ": "1/2",
    "មួយពាន់": "1000", "ពីរពាន់": "2000", "ប្រាំពាន់": "5000", "ដប់ពាន់": "10000",
    "មួយរយ": "100", "ពីររយ": "200", "បីរយ": "300", "បួនរយ": "400", "ប្រាំរយ": "500",
    "ប្រាំមួយរយ": "600", "ប្រាំពីររយ": "700", "ប្រាំបីរយ": "800", "ប្រាំបួនរយ": "900",
    "ម្ភៃប្រាំ": "25", "សាមសិបប្រាំ": "35", "សែសិបប្រាំ": "45", "ហាសិបប្រាំ": "55",
    "ហុកសិបប្រាំ": "65", "ចិតសិបប្រាំ": "75", "ប៉ែតសិបប្រាំ": "85", "កៅសិបប្រាំ": "95",
    "ម្ភៃមួយ": "21", "ម្ភៃពីរ": "22", "ម្ភៃបី": "23", "ម្ភៃបួន": "24",
    "សាមសិបមួយ": "31", "សាមសិបពីរ": "32",
    "ម្ភៃ": "20", "សាមសិប": "30", "សែសិប": "40", "ហាសិប": "50",
    "ហុកសិប": "60", "ចិតសិប": "70", "ប៉ែតសិប": "80", "កៅសិប": "90",
    "ដប់ប្រាំបួន": "19", "ដប់ប្រាំបី": "18", "ដប់ប្រាំពីរ": "17", "ដប់ប្រាំមួយ": "16",
    "ដប់ប្រាំ": "15", "ដប់បួន": "14", "ដប់បី": "13", "ដប់ពីរ": "12", "ដប់មួយ": "11",
    "ដប់": "10",
    "ប្រាំបួន": "9", "ប្រាំបី": "8", "ប្រាំពីរ": "7", "ប្រាំមួយ": "6",
    "ប្រាំ": "5", "បួន": "4", "បី": "3", "ពីរ": "2", "មួយ": "1", "សូន្យ": "0"
}

_KHMER_DIGITS_MAP = {ord(k): ord(e) for k, e in zip("០១២៣៤៥៦៧៨៩", "0123456789")}

# Proximity encouragement patterns that could invite brute-force guessing
_PROXIMITY_FEEDBACK_RE = re.compile(
    r"\b(?:just\s+(?:1|one|2|two)\s+away|off\s+by\s+(?:1|one|2|two)|almost\s+there,\s+so\s+close)\b",
    re.IGNORECASE
)

# Known answer disclosure phrasing patterns
_ANSWER_DISCLOSURE_PHRASES_RE = re.compile(
    r"(?i)\b(?:the\s+answer\s+is|correct\s+answer\s+is|answer\s*:\s*|result\s+is|equals\s+|is\s+equal\s+to|gives\s+you\s+|so\s+we\s+get\s+|it\s+is\s+|which\s+is\s+|therefore\s+it\s+is)\b|"
    r"(?:ចម្លើយគឺ|គឺ|ស្មើនឹង|ទទួលបាន)\s*",
    re.IGNORECASE
)


def _is_in_disclosure_window(text: str, target_val: Fraction) -> bool:
    """
    Checks if a target numeric value appears within 6 words following an explicit
    answer disclosure phrase (e.g. 'the answer is 12', 'equals 12').
    """
    for match in _ANSWER_DISCLOSURE_PHRASES_RE.finditer(text):
        end_idx = match.end()
        after_text = text[end_idx : end_idx + 80]
        tokens = after_text.split()[:6]
        for tok in tokens:
            cleaned_tok = tok.strip().strip(".,;:!?()[]\"'").translate(_KHMER_DIGITS_MAP).replace("−", "-")
            val = safe_eval_ast(cleaned_tok)
            if val is not None and val == target_val:
                return True
    return False


def _mask_verified_parallel_examples(text: str, forbidden_targets: Set[Fraction]) -> str:
    """
    If the response contains a Socratic helpful_example block, inspects all numbers
    within it. If NONE of the numbers inside the example match forbidden_targets,
    masks the example lines with placeholder tokens so that parallel expressions
    (e.g. '10 - 2 = 8' when the student's target is 5) do not trigger false alarms.
    """
    example_match = re.search(r"(?s)(🍎\s*\*\*Helpful\s+(?:Picture\s*/\s*)?Example:\*\*.*?>[^\n]+(?:\n>[^\n]+)*)", text)
    if not example_match:
        return text

    example_block = example_match.group(1)
    norm_block = _normalize_arithmetic_and_word_expressions(example_block)
    candidate_tokens = _DIGIT_RUN_RE.findall(norm_block)
    for tok in candidate_tokens:
        tok_clean = tok.strip().translate(_KHMER_DIGITS_MAP).replace("−", "-")
        readings = _generate_plausible_readings(tok_clean)
        for cand_val, _ in readings:
            if cand_val in forbidden_targets:
                # Collides with student's target, do not mask!
                return text

    # All numbers are disjoint from student targets; mask example body
    masked_block = re.sub(r">.*", "> [Verified Parallel Example]", example_block)
    return text[:example_match.start(1)] + masked_block + text[example_match.end(1):]


# Common grammatical stop words to exclude from short concept word checks
_COMMON_STOP_WORDS = {
    "a", "an", "the", "in", "on", "at", "to", "of", "and", "or", "is", "it",
    "be", "do", "we", "he", "she", "by", "for", "as", "if", "my", "so", "up",
    "no", "yes", "not"
}

# Backward compatibility aliases
SAFE_CLUE_FALLBACK = SAFE_CLUE_FALLBACK_ENG
SAFE_CONCEPTUAL_GUIDANCE = SAFE_CLUE_FALLBACK_ENG

# Composite English number words generator (e.g. "twenty five", "twenty-five" -> 25)
_TENS_WORDS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90
}
_ONES_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9
}

_COMPOSITE_EN_NUMBER_WORDS: Dict[str, str] = {}
for _t_name, _t_val in _TENS_WORDS.items():
    for _o_name, _o_val in _ONES_WORDS.items():
        _c_val = str(_t_val + _o_val)
        _COMPOSITE_EN_NUMBER_WORDS[f"{_t_name} {_o_name}"] = _c_val
        _COMPOSITE_EN_NUMBER_WORDS[f"{_t_name}-{_o_name}"] = _c_val

# Extended sorted number words (longest match first)
_EXTENDED_NUMBER_WORDS_SORTED: List[Tuple[str, str]] = sorted(
    list(_KH_NUMBER_WORDS.items())
    + list(_COMPOSITE_EN_NUMBER_WORDS.items())
    + list(_EN_NUMBER_WORDS.items()),
    key=lambda pair: len(pair[0]),
    reverse=True
)

# Pattern capturing sequences of digits and separators (dots, commas, slashes)
_DIGIT_RUN_RE = re.compile(
    r"[-+−]?[0-9\u17E0-\u17E9]+(?:[.,/][0-9\u17E0-\u17E9]+)*"
)

# Multi-term arithmetic expression pattern (e.g. "10 + 5", "3 * 5", "30 / 2", "0.5 * 30")
_ARITHMETIC_EXPR_RE = re.compile(
    r"(?<![0-9\u17E0-\u17E9.,/])[-+−]?[0-9\u17E0-\u17E9]+(?:\.[0-9\u17E0-\u17E9]+)?(?:\s*[-+*/]\s*[-+−]?[0-9\u17E0-\u17E9]+(?:\.[0-9\u17E0-\u17E9]+)?)+(?![0-9\u17E0-\u17E9])"
)


def _extract_target_value(target_answer: str) -> Optional[Fraction]:
    """Extracts target answer as a Fraction value."""
    if not target_answer:
        return None
    cleaned = target_answer.strip().translate(_KHMER_DIGITS_MAP)
    return safe_eval_ast(cleaned)


def _contains_khmer(text: str) -> bool:
    """Checks if text contains Khmer Unicode characters."""
    return any(0x1780 <= ord(c) <= 0x17FF for c in text)


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

    # 6. Replace number words (greedy longest-match with extended composite numbers)
    for word, digit_str in _EXTENDED_NUMBER_WORDS_SORTED:
        if word in t or word in t.lower():
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


def _token_matches_value(
    text: str,
    target_val: Fraction,
    exempted_tokens: Set[str],
    problem_operands: Optional[Set[Fraction]] = None
) -> Tuple[bool, Optional[str]]:
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
            # If all operands in expr_clean are given numbers from the problem statement,
            # and it is NOT an explicit answer disclosure (e.g. "What is 12 - 4?"), permit it.
            if problem_operands:
                raw_nums = _DIGIT_RUN_RE.findall(expr_clean)
                expr_nums = [safe_eval_ast(t) for t in raw_nums]
                if expr_nums and all(n is not None and n in problem_operands for n in expr_nums):
                    if not _is_in_disclosure_window(norm_text, expr_val) and not re.search(rf"{re.escape(expr_clean)}\s*=\s*", norm_text):
                        continue
            return True, expr_clean

    return False, None


_MATH_SUBJECT_ALIASES = frozenset({"", "math", "mathematics", "arithmetic"})


def _clue_fallback(tutor_reply: str, subject: Optional[str]) -> str:
    """Picks an answer-safe nudge that fits the subject of the exercise."""
    is_khmer = _contains_khmer(tutor_reply)
    subject_l = (subject or "").strip().lower()
    if subject_l in _MATH_SUBJECT_ALIASES:
        return SAFE_CLUE_FALLBACK_KHMER if is_khmer else SAFE_CLUE_FALLBACK_ENG
    return SAFE_CLUE_FALLBACK_SCIENCE_KHMER if is_khmer else SAFE_CLUE_FALLBACK_SCIENCE_ENG


def _future_leak_fallback(
    tutor_reply: str, subject: Optional[str], is_step_solved: bool
) -> str:
    """A solved step may be praised; an unsolved one must be nudged instead.

    The old fallback always praised the student, so an intercepted first-step
    reply could tell a student who had answered nothing "That is correct!".
    """
    if is_step_solved:
        return (
            SAFE_PRAISE_FALLBACK_KHMER
            if _contains_khmer(tutor_reply)
            else SAFE_PRAISE_FALLBACK_ENG
        )
    return _clue_fallback(tutor_reply, subject)


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
    problem_text: Optional[str] = None,
    subject: Optional[str] = None,
) -> Tuple[bool, str, str]:
    """
    Evaluates tutor reply for answer leakage and guessing game proximity signals.
    Enforces the Socratic Invariant (Spec Section 1, 2.3, 9).

    Args:
        tutor_reply:          Proposed tutor response text
        target_answer:        Expected answer string for current step (e.g. '15')
        is_step_solved:       True if the student has already correctly solved this step
        is_reveal_state:      Explicit boolean: True ONLY when in explicit RevealState
                              (after 3 failed attempts in reveal_and_continue.py).
                              When False or None, disclosure is strictly forbidden even at Tier 3.
        current_hint_tier:    Hint tier 0, 1, 2, or 3 (3 = worked parallel example; never reveals answer)
        step_number:          Active step number (to allow e.g. 'Step 2')
        attempts_count:       Number of student attempts on the current step
        unsolved_step_values: List of answer values for future unsolved steps
        final_answer:         Problem final answer
        problem_text:         Original problem text to exempt stated numbers
        subject:              Active subject (math/science/...) so a quarantined
                              reply gets subject-appropriate fallback wording

    Returns:
        (is_leak_detected: bool, final_reply: str, reason: str)
    """
    if not tutor_reply or not target_answer:
        return False, tutor_reply, "empty_input"

    # Normalize reply (translate Khmer digits)
    norm_reply = tutor_reply.translate(_KHMER_DIGITS_MAP)

    # Exclude active step label indicator (e.g. "Step 2" or "ជំហានទី ២")
    cleaned_reply = re.sub(r"(?i)\bstep\s+\d+\b", " ", norm_reply)
    cleaned_reply = re.sub(r"ជំហានទី\s*\d+", " ", cleaned_reply)

    # Collect all active and future unsolved target values
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

    # Mask verified parallel examples that do not collide with forbidden targets
    cleaned_reply = _mask_verified_parallel_examples(cleaned_reply, active_and_unsolved)

    # ─────────────────────────────────────────────────────────────────────────
    # Given Operands Allowlist (Spec Section 10.1):
    # Numbers explicitly stated in the student's problem text are safe to restate,
    # UNLESS they appear within a direct 6-token disclosure window ("The answer is X").
    # ─────────────────────────────────────────────────────────────────────────
    exempted_tokens: Set[str] = set()
    given_operands: Set[Fraction] = set()
    if problem_text:
        from app.services.socratic.invariants import extract_raw_input_numeric_tokens
        raw_exempted = extract_raw_input_numeric_tokens(problem_text)
        for tok in raw_exempted:
            tok_v = safe_eval_ast(tok)
            if tok_v is not None:
                given_operands.add(tok_v)
                # If tok_v collides with an active/future target, only exempt if NOT in disclosure window
                if tok_v in active_and_unsolved:
                    if not _is_in_disclosure_window(norm_reply, tok_v):
                        exempted_tokens.add(tok)
                else:
                    exempted_tokens.add(tok)
            elif tok_v is None and tok.lower() not in {target_answer.lower()} | {u.lower() for u in (unsolved_step_values or [])}:
                exempted_tokens.add(tok)

        # Words already named in the problem statement are given information,
        # exactly like its numbers. Without this, a step target such as
        # "sunlight" in "why do plants need sunlight?" made the active step's
        # own mission text look like an answer leak.
        problem_l = problem_text.lower()
        for word in re.findall(r"[a-z][a-z'\-]+", problem_l):
            exempted_tokens.add(word)
        for target in [target_answer, *(unsolved_step_values or []), final_answer or ""]:
            target_l = str(target or "").strip().lower()
            # Numeric targets already go through the disclosure-window-aware
            # operand allowlist above; this exemption is for word concepts only.
            if (
                target_l
                and not re.search(r"\d", target_l)
                and re.search(rf"\b{re.escape(target_l)}\b", problem_l)
            ):
                exempted_tokens.add(target_l)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Multi-Step Praise Shield:
    # Even if current step is solved, check future unsolved steps & final answer!
    # ─────────────────────────────────────────────────────────────────────────
    t_val_check = _extract_target_value(target_answer)
    future_targets: List[str] = []
    for u in (unsolved_step_values or []):
        if not u:
            continue
        u_val = _extract_target_value(u)
        if u_val is not None and t_val_check is not None and u_val == t_val_check:
            continue
        if u.strip().lower() == target_answer.strip().lower():
            continue
        future_targets.append(u)

    if final_answer and final_answer not in future_targets:
        f_val = _extract_target_value(final_answer)
        if not (f_val is not None and t_val_check is not None and f_val == t_val_check) and final_answer.strip().lower() != target_answer.strip().lower():
            future_targets.append(final_answer)

    for future_t in future_targets:
        if not future_t:
            continue
        fut_val = _extract_target_value(future_t)
        if fut_val is not None:
            leaked, leaked_tok = _token_matches_value(cleaned_reply, fut_val, exempted_tokens, problem_operands=given_operands)
            if leaked:
                fallback = _future_leak_fallback(tutor_reply, subject, is_step_solved)
                return True, fallback, f"unsolved_future_step_leak_detected ({leaked_tok})"
        else:
            # Word concept target
            w_target = future_t.strip().lower()
            if (
                len(w_target) >= 2
                and w_target not in _COMMON_STOP_WORDS
                and w_target not in exempted_tokens
                and re.search(rf"\b{re.escape(w_target)}\b", cleaned_reply, re.IGNORECASE)
            ):
                fallback = _future_leak_fallback(tutor_reply, subject, is_step_solved)
                return True, fallback, f"unsolved_future_concept_leak_detected ({w_target})"

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Current Step State Awareness:
    # Tier 3 Socratic Invariant: Answer disclosure is permitted ONLY if
    # is_step_solved is True OR is_reveal_state is explicitly True.
    # At Tier 1, Tier 2, AND Tier 3 hints, answer disclosure is STRICTLY FORBIDDEN.
    # ─────────────────────────────────────────────────────────────────────────
    reveal_allowed = is_step_solved or (is_reveal_state is True)
    if reveal_allowed:
        return False, tutor_reply, "state_allows_answer"

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Check current step leakage:
    # ─────────────────────────────────────────────────────────────────────────
    target_val = _extract_target_value(target_answer)
    clue_fallback = _clue_fallback(tutor_reply, subject)

    if target_val is None:
        # Non-numeric target (e.g. word concept 'chloroplast', 'gas', 'liquid', 'vertebrate')
        target_word = target_answer.strip().lower()
        if (
            len(target_word) >= 2
            and target_word not in _COMMON_STOP_WORDS
            and target_word not in exempted_tokens
            and re.search(rf"\b{re.escape(target_word)}\b", cleaned_reply, re.IGNORECASE)
        ):
            return True, clue_fallback, f"concept_word_leak_detected ({target_word})"
        return False, tutor_reply, "non_numeric_clean"

    leaked, leaked_tok = _token_matches_value(cleaned_reply, target_val, exempted_tokens, problem_operands=given_operands)
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


class LeakGuard:
    """
    Production Output Leak Guard (Spec Section 9).
    Wraps deterministic scanning, regeneration triggering, and fail-safe sanitization.
    """

    def __init__(self):
        self.max_regeneration_attempts: int = 2

    def inspect_and_sanitize(
        self,
        text: str,
        target_answer: str,
        is_step_solved: bool = False,
        is_reveal_state: bool = False,
        current_hint_tier: int = 0,
        unsolved_step_values: Optional[List[str]] = None,
        final_answer: Optional[str] = None,
        problem_text: Optional[str] = None,
        attempts_count: int = 1
    ) -> Tuple[bool, str, str]:
        """
        Scans a candidate text for leaks and returns (is_leak, sanitized_text, reason).
        """
        is_leak, sanitized, reason = check_tutor_response_leak(
            tutor_reply=text,
            target_answer=target_answer,
            is_step_solved=is_step_solved,
            is_reveal_state=is_reveal_state,
            current_hint_tier=current_hint_tier,
            attempts_count=attempts_count,
            unsolved_step_values=unsolved_step_values,
            final_answer=final_answer,
            problem_text=problem_text
        )
        if is_leak:
            try:
                from app.services.telemetry.gap_recorder import log_gap_event
                log_gap_event(
                    gap_type="system",
                    gap_code="LEAK_BLOCKED",
                    severity=3,
                    details={
                        "reason": reason,
                        "target_answer": target_answer,
                        "current_hint_tier": current_hint_tier,
                        "problem_text": problem_text,
                    }
                )
            except Exception as e:
                logger.debug(f"[LeakGuard] Gap log failed: {e}")
        return is_leak, sanitized, reason


def scan_visual_spec(
    spec: Any,
    target_answer: Optional[str] = None,
    unsolved_targets: Optional[List[str]] = None,
    problem_numbers: Optional[Set[Any]] = None
) -> Tuple[bool, Any, Optional[str]]:
    """
    Leak Guard v2 VisualSpec security scanner (Architecture v2.1 Section 8.3 & 10.1).
    Scans visual model parameters, labels, and alt_text for answers or collisions.
    """
    from app.services.visuals.schema import VisualSpec
    from app.services.visuals.leak_checker import check_visual_spec_leak

    if isinstance(spec, dict):
        v_spec = VisualSpec.model_validate(spec)
        is_leak, sanitized, reason = check_visual_spec_leak(
            spec=v_spec,
            target_answer=target_answer,
            unsolved_targets=unsolved_targets,
            problem_numbers=problem_numbers
        )
        return is_leak, sanitized.model_dump(), reason
    elif isinstance(spec, VisualSpec):
        return check_visual_spec_leak(
            spec=spec,
            target_answer=target_answer,
            unsolved_targets=unsolved_targets,
            problem_numbers=problem_numbers
        )
    return False, spec, None

