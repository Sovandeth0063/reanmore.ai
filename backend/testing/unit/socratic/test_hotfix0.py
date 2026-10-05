"""
Unit tests for Hotfix 0:
  - pii_scrubber.py (Targeted PII scrubbing, math protection, prompt entity encoding)
  - safe_math.py (Sandboxed AST Fraction arithmetic, DoS bounds)
"""

# pyrefly: ignore [missing-import]
import pytest
import os
import sys

# Ensure repo root and orchestrator are on sys.path
def _find_repo_root():
    cur = os.path.abspath(os.path.dirname(__file__))
    while cur and not os.path.exists(os.path.join(cur, "orchestrator")):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return cur

BASE_DIR = _find_repo_root()
ORCHESTRATOR_DIR = os.path.join(BASE_DIR, "orchestrator")
for _p in (BASE_DIR, ORCHESTRATOR_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orchestrator")))

# pyrefly: ignore [missing-import]
from app.services.guardrails.pii_scrubber import scrub_student_pii, sanitize_for_prompt
# pyrefly: ignore [missing-import]
from app.services.socratic.safe_math import safe_eval_ast, safe_eval_float


# ─────────────────────────────────────────────────────────────────────────────
# 1. PII Scrubber & Prompt Sanitization Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPiiScrubber:

    def test_scrubs_english_self_intro(self):
        text = "Hello! My name is John Smith and I need help with math."
        scrubbed = scrub_student_pii(text)
        assert "[NAME]" in scrubbed
        assert "John Smith" not in scrubbed
        assert "Hello!" in scrubbed

    def test_scrubs_khmer_self_intro(self):
        text = "សួស្តី ខ្ញុំឈ្មោះ សុខា ខ្ញុំចង់ដឹងពីមេរៀននេះ"
        scrubbed = scrub_student_pii(text)
        assert "[NAME]" in scrubbed
        assert "សុខា" not in scrubbed

    def test_scrubs_phone_numbers(self):
        text = "Call my mom at 012 345 678 please."
        scrubbed = scrub_student_pii(text)
        assert "[PHONE]" in scrubbed
        assert "012 345 678" not in scrubbed

    def test_scrubs_email(self):
        text = "My email is student123@school.edu."
        scrubbed = scrub_student_pii(text)
        assert "[EMAIL]" in scrubbed
        assert "student123@school.edu" not in scrubbed

    def test_preserves_standalone_numbers_and_years(self):
        text = "The answer is 15 and the year was 2024."
        scrubbed = scrub_student_pii(text)
        assert "15" in scrubbed
        assert "2024" in scrubbed
        assert "[PHONE]" not in scrubbed

    def test_preserves_word_problem_characters(self):
        # Word problem characters must NOT be scrubbed
        text = "Sokha has 5 apples and Bopha has 3 apples. How many total?"
        scrubbed = scrub_student_pii(text)
        assert "Sokha" in scrubbed
        assert "Bopha" in scrubbed
        assert "[NAME]" not in scrubbed

    def test_sanitize_for_prompt_encodes_tags_and_caps(self):
        malicious = "<script>alert('hack')</script> " + "A" * 400
        safe = sanitize_for_prompt(malicious, max_chars=300)
        assert "<" not in safe
        assert ">" not in safe
        assert "&lt;script&gt;" in safe
        assert len(safe) <= 350  # 300 chars capped before entity expansion


# ─────────────────────────────────────────────────────────────────────────────
# 2. Safe AST Math Sandbox Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSafeMath:

    def test_basic_arithmetic(self):
        assert safe_eval_float("12 + 15") == 27.0
        assert safe_eval_float("8 * 7") == 56.0
        assert safe_eval_float("24 / 4") == 6.0
        assert safe_eval_float("15 - 9") == 6.0

    def test_fractions(self):
        assert safe_eval_float("1/2 + 1/4") == 0.75
        assert safe_eval_float("3 / 6") == 0.5

    def test_division_by_zero_returns_none(self):
        assert safe_eval_float("10 / 0") is None

    def test_exponent_within_bounds(self):
        assert safe_eval_float("2 ** 3") == 8.0
        assert safe_eval_float("3 ^ 2") == 9.0

    def test_exponent_dos_rejected(self):
        # Giant exponents that would cause DoS are blocked
        assert safe_eval_float("9 ** 99") is None
        assert safe_eval_float("2 ** 50") is None

    def test_number_size_limit(self):
        # Constants exceeding MAX_VALUE (1,000,000) are blocked
        assert safe_eval_float("1000000000 + 1") is None

    def test_rejects_code_execution_injections(self):
        assert safe_eval_float("__import__('os').system('dir')") is None
        assert safe_eval_float("open('/etc/passwd')") is None
        assert safe_eval_float("exec('x = 1')") is None
        assert safe_eval_float("[x for x in (1, 2)]") is None
