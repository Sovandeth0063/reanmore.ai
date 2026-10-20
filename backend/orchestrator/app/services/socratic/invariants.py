"""
File: orchestrator/app/services/socratic/invariants.py
Description: Number Traceability Invariant Verifier & Normalizer (Sprint 4a - Task 4a.3).
             Strictly enforces the 4-stage Grader Order of Operations:
             1. Normalize raw student input (Khmer numerals, number words, locale commas, negatives).
             2. Extract candidate tokens.
             3. Verify traceability of normalized candidate tokens against normalized student input.
             4. Pass verified tokens to AST math grader.
"""

import re
from typing import List, Tuple, Set, Optional, Dict
from fractions import Fraction

from app.services.socratic.safe_math import safe_eval_ast

# Khmer numeral translation mapping
_KHMER_DIGITS_MAP = {ord(k): ord(e) for k, e in zip("០១២៣៤៥៦៧៨៩", "0123456789")}

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

# Comprehensive Khmer number words (single digits, teens, tens, hundreds, thousands, fractions)
_KH_NUMBER_WORDS: Dict[str, str] = {
    # Halves and fractions
    "មួយកន្លះ": "1.5", "ពីរកន្លះ": "2.5", "បីកន្លះ": "3.5", "ដប់កន្លះ": "10.5", "កន្លះ": "1/2",
    # Hundreds & Thousands
    "មួយពាន់": "1000", "ពីរពាន់": "2000", "ប្រាំពាន់": "5000", "ដប់ពាន់": "10000",
    "មួយរយ": "100", "ពីររយ": "200", "បីរយ": "300", "បួនរយ": "400", "ប្រាំរយ": "500",
    "ប្រាំមួយរយ": "600", "ប្រាំពីររយ": "700", "ប្រាំបីរយ": "800", "ប្រាំបួនរយ": "900",
    # Tens with five
    "ម្ភៃប្រាំ": "25", "សាមសិបប្រាំ": "35", "សែសិបប្រាំ": "45", "ហាសិបប្រាំ": "55",
    "ហុកសិបប្រាំ": "65", "ចិតសិបប្រាំ": "75", "ប៉ែតសិបប្រាំ": "85", "កៅសិបប្រាំ": "95",
    # Tens with one, two, etc.
    "ម្ភៃមួយ": "21", "ម្ភៃពីរ": "22", "ម្ភៃបី": "23", "ម្ភៃបួន": "24",
    "សាមសិបមួយ": "31", "សាមសិបពីរ": "32",
    # Tens
    "ម្ភៃ": "20", "សាមសិប": "30", "សែសិប": "40", "ហាសិប": "50",
    "ហុកសិប": "60", "ចិតសិប": "70", "ប៉ែតសិប": "80", "កៅសិប": "90",
    # Teens
    "ដប់ប្រាំបួន": "19", "ដប់ប្រាំបី": "18", "ដប់ប្រាំពីរ": "17", "ដប់ប្រាំមួយ": "16",
    "ដប់ប្រាំ": "15", "ដប់បួន": "14", "ដប់បី": "13", "ដប់ពីរ": "12", "ដប់មួយ": "11",
    "ដប់": "10",
    # Single digits
    "ប្រាំបួន": "9", "ប្រាំបី": "8", "ប្រាំពីរ": "7", "ប្រាំមួយ": "6",
    "ប្រាំ": "5", "បួន": "4", "បី": "3", "ពីរ": "2", "មួយ": "1", "សូន្យ": "0"
}

# Sorted by length descending for longest-match greedy substitution
_ALL_NUMBER_WORDS_SORTED = sorted(
    list(_KH_NUMBER_WORDS.items()) + list(_EN_NUMBER_WORDS.items()),
    key=lambda pair: len(pair[0]),
    reverse=True
)


def normalize_student_input(raw_input: str, context_unit: Optional[str] = None) -> str:
    """
    Normalizes student text into canonical representation:
    1. Translates Khmer numerals (០-៩) to Arabic digits (0-9).
    2. Canonicalizes decomposed Khmer compound vowels (e.g. U+17C1 + U+17B6 -> U+17C4 'ោ').
    3. Maps Khmer and English number words to numeric strings (greedy longest-match).
    4. Disambiguates locale commas based strictly on unit context (currency/discrete counts vs metric),
       NEVER peeking at expected answer target values.
    5. Handles negative prefixes (ដក / negative).
    6. Normalizes whitespace and basic currency/unit symbols.
    """
    if not raw_input:
        return ""

    text = raw_input.strip()

    # 1. Translate Khmer numerals to Arabic digits
    text = text.translate(_KHMER_DIGITS_MAP)

    # 2. Canonicalize Khmer compound vowels (U+17C1 'េ' + U+17B6 'ា' -> U+17C4 'ោ')
    text = text.replace("\u17C1\u17B6", "\u17C4")

    # 3. Handle negative prefixes: e.g. "ដក ៥" -> "-5", "negative 5" -> "-5"
    text = re.sub(r"(?i)\b(?:ដក|negative|minus)\s+(\d+)", r"-\1", text)

    # 4. Replace number words (greedy longest-match)
    for word, digit_str in _ALL_NUMBER_WORDS_SORTED:
        if word in text:
            # Word boundary for english, substring match for Khmer
            if any(ord(c) >= 0x1780 and ord(c) <= 0x17FF for c in word):
                text = text.replace(word, f" {digit_str} ")
            else:
                text = re.sub(rf"\b{re.escape(word)}\b", f" {digit_str} ", text, flags=re.IGNORECASE)

    # 5. Handle locale commas based on unit/problem context (NEVER target value)
    unit_str = (context_unit or "") + " " + text
    is_currency = bool(re.search(r"\b(?:riels?|រៀល|៛|\$|dollars?)\b", unit_str, re.IGNORECASE))
    is_discrete = bool(re.search(r"\b(?:apples?|ផ្លែ|នាក់|គ្រាប់|ដើម|candies?|cookies?|items?)\b", unit_str, re.IGNORECASE))

    if is_currency or is_discrete:
        # Currency and discrete counts in elementary math strictly use thousands separators
        text = re.sub(r"(\d+),(\d{3})(?:\b|\D|$)", r"\1\2", text)
        text = re.sub(r"(\d+),(\d{1,2})(?:\b|\D|$)", r"\1.\2", text)
    else:
        # Standard default: 3 digits = thousands (1,000 -> 1000); 1 or 2 digits = decimal (1,5 -> 1.5)
        text = re.sub(r"(\d+),(\d{3})(?:\b|\D|$)", r"\1\2", text)
        text = re.sub(r"(\d+),(\d{1,2})(?:\b|\D|$)", r"\1.\2", text)

    # 6. Clean extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_ambiguous_locale_number(raw_token: str, context_unit: Optional[str] = None) -> bool:
    """
    Detects if a number formatted with comma is ambiguous without unit context
    (e.g. '1,500' without unit could mean 1500 or 1.500).
    """
    unit_str = context_unit or ""
    is_known_unit = bool(re.search(r"\b(?:riels?|រៀល|៛|\$|dollars?|apples?|ផ្លែ|នាក់|គ្រាប់|ដើម)\b", unit_str, re.IGNORECASE))
    if is_known_unit:
        return False
    cleaned = raw_token.strip().translate(_KHMER_DIGITS_MAP)
    return bool(re.match(r"^\d+,\d{3}$", cleaned))


def extract_raw_input_numeric_tokens(raw_text: str) -> Set[str]:
    """
    Extracts all numeric representations from raw student text after normalization:
    - Digits, fractions, decimals, negatives
    - Also stores integer representations for whole decimals (e.g. 15.0 -> 15)
    """
    if not raw_text:
        return set()

    norm_text = normalize_student_input(raw_text).lower()
    tokens: Set[str] = set()

    # 1. Extract signed numeric tokens (integers, decimals, fractions)
    found_nums = re.findall(r"(?<![\w/])[-+]?\d+(?:\.\d+)?(?:/\d+)?(?![\w/])", norm_text)
    for n in found_nums:
        tokens.add(n)
        if "/" in n:
            for p in n.split("/"):
                tokens.add(p)
        try:
            val = float(n)
            if val.is_integer():
                tokens.add(str(int(val)))
        except ValueError:
            pass

    # 2. Extract words directly
    words = re.findall(r"[\w\u1780-\u17DD]+", norm_text)
    for w in words:
        if w in _EN_NUMBER_WORDS:
            tokens.add(_EN_NUMBER_WORDS[w])
        if w in _KH_NUMBER_WORDS:
            tokens.add(_KH_NUMBER_WORDS[w])

    return tokens


def verify_number_traceability(raw_input: str, candidates: List[str]) -> Tuple[bool, List[str], List[str]]:
    """
    Verifies that all candidates are traceable to the student's normalized message.
    Crucial fix (Item 9): Compares normalized candidates against normalized input,
    ensuring '15' correctly traces to '១៥' or 'ដប់ប្រាំ'.

    Returns:
        (all_traceable: bool, valid_candidates: List[str], hallucinated_candidates: List[str])
    """
    if not candidates:
        return True, [], []

    norm_input = normalize_student_input(raw_input).lower()
    norm_tokens = extract_raw_input_numeric_tokens(raw_input)

    valid: List[str] = []
    hallucinated: List[str] = []

    for cand in candidates:
        cand_clean = cand.strip()
        # Normalize candidate representation
        cand_norm = normalize_student_input(cand_clean).lower()

        # Check numeric candidates
        cand_nums = re.findall(r"(?<![\w/])[-+]?\d+(?:\.\d+)?(?:/\d+)?(?![\w/])", cand_norm)
        if cand_nums:
            is_valid = True
            for num in cand_nums:
                # Check if num exists in norm_tokens or norm_input
                num_int = str(int(float(num))) if ("." in num and safe_eval_ast(num) is not None and float(num).is_integer()) else num
                if num not in norm_tokens and num not in norm_input and num_int not in norm_tokens:
                    is_valid = False
                    break
            if is_valid:
                valid.append(cand_clean)
            else:
                hallucinated.append(cand_clean)
        else:
            # Non-numeric word candidate (e.g. concept name "photosynthesis" / "រុក្ខជាតិ")
            cand_lower = cand_clean.lower()
            if cand_lower in norm_input or any(part in norm_input for part in cand_lower.split()):
                valid.append(cand_clean)
            else:
                hallucinated.append(cand_clean)

    all_traceable = len(hallucinated) == 0
    return all_traceable, valid, hallucinated
