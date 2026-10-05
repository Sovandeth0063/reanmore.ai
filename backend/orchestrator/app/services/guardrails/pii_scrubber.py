"""
File: orchestrator/app/services/guardrails/pii_scrubber.py
Description: Targeted PII scrubber and prompt copy sanitizer (Phase 0 / Sprint 1).
             - Scrubs conversational student self-introductions (names, phones, emails, schools).
             - Strictly preserves math answers, calculations, and word-problem characters
               (e.g., 'Sokha has 5 apples' is NOT scrubbed).
             - Provides HTML-entity encoding (&lt;, &gt;) for prompt copies only,
               ensuring math comparison operators (<, >) remain uncorrupted for code grading.
"""

import re
from typing import Tuple

# Max characters allowed for student chat messages
MAX_STUDENT_MESSAGE_CHARS = 300
MAX_WORKSHEET_CHARS = 500

# ─────────────────────────────────────────────────────────────────────────────
# Targeted Conversational Self-Identification Patterns
# ─────────────────────────────────────────────────────────────────────────────

# Self-introduction patterns (English & Khmer)
_NAME_SELF_ID_PATTERNS = [
    # English: "My name is John Smith", "I am Sokha", "Call me Davy"
    r"(?i:\b(?:my\s+name\s+is|call\s+me)\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[a-z]{2,}(?=\s+(?:and|i|im|i'm|pls|please|\.|\,|$)|$))\b",
    r"(?i:\bi(?:'m|\s+am)\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[a-z]{2,}(?=\s+(?:and|i|im|i'm|pls|please|\.|\,|$)|$))\b",
    # Khmer: ខ្ញុំឈ្មោះ (My name is), ខ្ញុំមានឈ្មោះ (I have the name)
    r"(?:ខ្ញុំ\s*ឈ្មោះ|ខ្ញុំ\s*មាន\s*ឈ្មោះ)\s*([\u1780-\u17D2]+(?:\s+[\u1780-\u17D2]+)*)",
]

# Structured telephone patterns (prevent matching isolated numbers, years, or math answers)
_PHONE_PATTERNS = [
    # Cambodia: +855 12 345 678, 012 345 678, 097-123-4567
    r"(?:\+?855[\s.-]?)?0[1-9]\d[\s.-]?\d{3}[\s.-]?\d{3,4}\b",
    # International / US formatted: (123) 456-7890, 123-456-7890
    r"\(\d{3}\)[\s.-]?\d{3}[\s.-]?\d{4}\b",
    r"\b\d{3}[-.]\d{3}[-.]\d{4}\b",
]

# Email addresses
_EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

# School / Personal location self-identification: "I go to XYZ school", "I study at XYZ"
_SCHOOL_SELF_ID = r"\b(?:i\s+go\s+to|i\s+study\s+at)\s+([A-Za-z0-9\s]+?\s+school)\b"


def scrub_student_pii(text: str) -> str:
    """
    Scrubs only personal self-identification disclosures from a student message.
    Preserves math answers, standalone numbers, and word-problem text.
    """
    if not text:
        return ""

    scrubbed = text

    # 1. Email addresses
    scrubbed = re.sub(_EMAIL_PATTERN, "[EMAIL]", scrubbed, flags=re.IGNORECASE)

    # 2. Telephone numbers with strict phone formatting
    for pat in _PHONE_PATTERNS:
        scrubbed = re.sub(pat, "[PHONE]", scrubbed)

    # 3. Conversational self-introductions (English & Khmer)
    for pat in _NAME_SELF_ID_PATTERNS:
        def _replace_name(m):
            prefix = m.group(0)[:m.start(1) - m.start(0)]
            return f"{prefix}[NAME]"
        scrubbed = re.sub(pat, _replace_name, scrubbed)

    # 4. School disclosures
    scrubbed = re.sub(_SCHOOL_SELF_ID, r"i go to [SCHOOL]", scrubbed, flags=re.IGNORECASE)

    return scrubbed


def sanitize_for_prompt(text: str, max_chars: int = MAX_STUDENT_MESSAGE_CHARS) -> str:
    """
    Sanitizes untrusted text specifically for inclusion in an LLM prompt copy:
    1. Enforces character length cap BEFORE entity expansion.
    2. Scrubs student PII self-identifications.
    3. Encodes HTML delimiters (<, >) to &lt; and &gt; to prevent XML prompt breakout.
    
    NOTE: The grading code must continue using the unencoded text so math
    comparison problems (e.g. 5 < 8) evaluate correctly.
    """
    if not text:
        return ""

    # 1. Length cap first (prevents entity expansion from consuming budget)
    capped = text.strip()[:max_chars]

    # 2. Scrub PII
    cleaned = scrub_student_pii(capped)

    # 3. HTML entity encoding for prompt copy only
    encoded = cleaned.replace("<", "&lt;").replace(">", "&gt;")

    return encoded
