"""
Bilingual Normalization & OCR Text Cleaning Engine for Elementary STEM Chatbot.
Handles kid typos, mobile slang, OCR worksheet artifacts, Khmenglish transliterations,
and provides a safe, invariant-preserving Tier-2 LLM fallback.
"""

import os
import re
import json
import asyncio
from functools import lru_cache
from typing import Dict, List, Set, Optional, Tuple

from app.services.prompts import prompt_controller

# Default dictionary path relative to this file
_DEFAULT_DICT_PATH = os.path.join(os.path.dirname(__file__), "typo_dictionary.json")

# Precompiled Unicode and Unit Constants for Sub-millisecond Execution
_UNICODE_EXPONENTS = {
    "⁰": "^0", "¹": "^1", "²": "^2", "³": "^3", "⁴": "^4",
    "⁵": "^5", "⁶": "^6", "⁷": "^7", "⁸": "^8", "⁹": "^9"
}

_UNICODE_FRACTIONS = {
    "½": "1/2", "⅓": "1/3", "⅔": "2/3", "¼": "1/4", "¾": "3/4",
    "⅕": "1/5", "⅖": "2/5", "⅗": "3/5", "⅘": "4/5",
    "⅙": "1/6", "⅚": "5/6", "⅛": "1/8", "⅜": "3/8", "⅝": "5/8", "⅞": "7/8"
}

_UNICODE_MATH_OPS = {
    "×": " * ", "·": " * ", "⋅": " * ", "÷": " / ",
    "≠": " != ", "≤": " <= ", "≥": " >= ", "±": " +/- "
}

_UNITS_SPACING_REGEX = re.compile(
    r'(\d+(?:\.\d+)?)\s*('
    r'cm\^[23]|m\^[23]|km\^[23]|mm\^[23]|ft\^[23]|in\^[23]|'
    r'km/h|kph|mph|m/s|'
    r'mm|cm|km|mg|kg|ml|gal|lbs?|oz|ft|in|yd|mi|'
    r'sec|secs|min|mins|hrs?|'
    r'°C|°F|'
    r'[glLms]'
    r')\b',
    flags=re.IGNORECASE
)


class NormalizerEngine:
    def __init__(self, dict_path: Optional[str] = None):
        self.dict_path = dict_path or _DEFAULT_DICT_PATH
        self.ocr_map: Dict[str, str] = {}
        self.math_map: Dict[str, str] = {}
        self.science_map: Dict[str, str] = {}
        self.slang_map: Dict[str, str] = {}
        self.khmenglish_map: Dict[str, str] = {}
        self.voice_map: Dict[str, str] = {}
        self.known_vocab: Set[str] = set()
        
        # Compiled master regex patterns
        self._compiled_regex: Optional[re.Pattern] = None
        self._replacement_map: Dict[str, str] = {}
        
        self.load_dictionary()

    def load_dictionary(self):
        """Loads typo dictionary and compiles longest-match-first regex."""
        if os.path.exists(self.dict_path):
            with open(self.dict_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        self.ocr_map = data.get("ocr_artifacts", {})
        self.math_map = data.get("english_math", {})
        self.science_map = data.get("english_science", {})
        self.slang_map = data.get("kid_slang_contractions", {})
        self.khmenglish_map = data.get("khmenglish_transliterations", {})
        self.voice_map = data.get("voice_speech_artifacts", {})
        self.known_vocab = set(data.get("known_stem_vocab", []))

        # Build master replacement map
        combined: Dict[str, str] = {}
        # Priority order: Voice phrases -> Slang -> Math/Science -> Khmenglish -> OCR
        for d in [self.voice_map, self.slang_map, self.math_map, self.science_map, self.khmenglish_map]:
            for k, v in d.items():
                combined[k.lower()] = v

        self._replacement_map = combined
        
        # Sort keys by length descending to prevent sub-word collisions
        sorted_keys = sorted(combined.keys(), key=lambda x: len(x), reverse=True)
        if sorted_keys:
            # Escape regex chars in keys
            pattern_parts = [r'\b' + re.escape(k) + r'\b' for k in sorted_keys]
            self._compiled_regex = re.compile("|".join(pattern_parts), flags=re.IGNORECASE)
        else:
            self._compiled_regex = None

    def detect_language(self, text: str) -> str:
        """
        Detects primary language/script.
        Returns: 'khmer', 'khmenglish', or 'english'.
        """
        if not text:
            return "english"
            
        # 1. Check for Khmer Unicode script (\u1780 to \u17FF)
        if re.search(r'[\u1780-\u17FF]', text):
            return "khmer"
            
        # 2. Check for Khmenglish terms
        lower = text.lower()
        khm_hits = sum(1 for k in self.khmenglish_map if re.search(r'\b' + re.escape(k) + r'\b', lower))
        if khm_hits > 0:
            return "khmenglish"
            
        return "english"

    def standardize_units_and_exponents(self, text: str) -> str:
        """
        Standardizes scientific units, exponents, and Unicode superscripts:
        - Unicode superscripts: cm² -> cm^2, m³ -> m^3, x² -> x^2
        - Shorthand exponents: cm2 -> cm^2, m3 -> m^3, 25cm2 -> 25 cm^2
        - Unit spacing: 5cm -> 5 cm, 10kg -> 10 kg, 250ml -> 250 ml, 15km/h -> 15 km/h
        """
        cleaned = text

        # 1. Convert Unicode superscripts
        for sup, ascii_exp in _UNICODE_EXPONENTS.items():
            cleaned = cleaned.replace(sup, ascii_exp)
        # Clean double caret if input had e.g. cm^²
        cleaned = re.sub(r'\^{2,}', '^', cleaned)

        # 2. Fix OCR / shorthand unit exponents without caret (e.g. 25cm2 -> 25 cm^2, 50m3 -> 50 m^3)
        cleaned = re.sub(r'(\d+)\s*(cm|m|km|mm|ft|in)2\b', r'\1 \2^2', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'(\d+)\s*(cm|m|km|mm|ft|in)3\b', r'\1 \2^3', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\b(cm|m|km|mm|ft|in)2\b', r'\1^2', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\b(cm|m|km|mm|ft|in)3\b', r'\1^3', cleaned, flags=re.IGNORECASE)

        # 3. Standardize spacing between digits and scientific units
        cleaned = _UNITS_SPACING_REGEX.sub(r'\1 \2', cleaned)

        return cleaned

    def standardize_fractions(self, text: str) -> str:
        """
        Standardizes fraction expressions:
        - Unicode fraction characters (½ -> 1/2, 2½ -> 2 1/2)
        - Ordinal fraction suffixes (3/4th, 3/4ths, 1/2nd, 2/3rds -> 3/4, 1/2, 2/3)
        - Spaced fractions (3 / 4 -> 3/4)
        - Mixed numbers (1 and 1/2 -> 1 1/2)
        """
        cleaned = text

        # 1. Separate digits adjacent to unicode fractions (e.g. 2½ -> 2 ½)
        cleaned = re.sub(r'(\d+)([½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])', r'\1 \2', cleaned)

        # 2. Convert Unicode fractions to ASCII
        for u_frac, a_frac in _UNICODE_FRACTIONS.items():
            cleaned = cleaned.replace(u_frac, a_frac)

        # 3. Strip ordinal suffixes from fractions (e.g. 3/4th, 3/4ths, 1/2nd, 2/3rds, 5/8ths)
        cleaned = re.sub(r'(\b\d+/\d+)(?:st|nd|rd|ths?|rds?)\b', r'\1', cleaned, flags=re.IGNORECASE)

        # 4. Spaced fractions vs division between digits (e.g. 3 / 4 -> 3/4, 10 / 2 -> 10 / 2)
        def _format_fraction_or_div(match):
            num, den = int(match.group(1)), int(match.group(2))
            if num < den:
                return f"{match.group(1)}/{match.group(2)}"
            return f"{match.group(1)} / {match.group(2)}"

        cleaned = re.sub(r'(\d+)\s*/\s*(\d+)', _format_fraction_or_div, cleaned)

        # 5. Mixed numbers (e.g. "1 and 1/2" -> "1 1/2")
        cleaned = re.sub(r'\b(\d+)\s+and\s+(\d+/\d+)\b', r'\1 \2', cleaned, flags=re.IGNORECASE)

        return cleaned

    def standardize_math_operators(self, text: str) -> str:
        """
        Converts word operators, Unicode operators, and OCR confusions to canonical ASCII (+, -, *, /, =, ^, <=, >=, !=).
        - Multiplication: 3 x 4, 3 X 4, 3 times 4, 3 multiplied by 4, 3 · 4, 3 × 4 -> 3 * 4
        - Division: 10 / 2, 10 divided by 2, 10 : 2, 10 ÷ 2, 10 over 2 -> 10 / 2
        - Addition & Subtraction: 5 plus 3 -> 5 + 3, 8 minus 2 -> 8 - 2, 5t3 -> 5 + 3
        - Equivalence & Relations: equals, is equal to, equal to -> =, >=, <=, !=
        """
        cleaned = text

        # 1. Convert Unicode math operators
        for u_op, a_op in _UNICODE_MATH_OPS.items():
            cleaned = cleaned.replace(u_op, a_op)

        # 2. Multiplication operators:
        # - 'x' / 'X' between digits or after unit: 4 x 5 -> 4 * 5, 5cm x 4 -> 5cm * 4
        cleaned = re.sub(r'(\d)\s*[xX]\s*(\d)', r'\1 * \2', cleaned)
        cleaned = re.sub(r'(\b[a-zA-Z]+(?:\^[23])?|\))\s*[xX]\s*(\d|\()', r'\1 * \2', cleaned)
        # - Word operators: "times", "multiplied by"
        cleaned = re.sub(r'(\d+(?:/\d+)?|\b[a-zA-Z]+(?:\^[23])?|\))\s+(?:times|multiplied\s+by)\s+(\d+(?:/\d+)?|\()', r'\1 * \2', cleaned, flags=re.IGNORECASE)

        # 3. Division operators:
        # - Word operators: "divided by", "over"
        cleaned = re.sub(r'(\d+(?:/\d+)?|\b[a-zA-Z]+(?:\^[23])?|\))\s+(?:divided\s+by|over)\s+(\d+(?:/\d+)?|\()', r'\1 / \2', cleaned, flags=re.IGNORECASE)
        # - Spaced colon between numbers (10 : 2 -> 10 / 2) avoiding unspaced timestamps (10:30)
        cleaned = re.sub(r'(\d+)\s+:\s+(\d+)', r'\1 / \2', cleaned)
        cleaned = re.sub(r'(\d+):(\d\b(?!\d))', r'\1 / \2', cleaned)

        # 4. Addition & Subtraction operators:
        # - "plus" and "minus" between operands (handles numbers, fractions, and units: 4 * 5 cm plus 1/2)
        cleaned = re.sub(r'(\d+(?:/\d+)?|\b[a-zA-Z]+(?:\^[23])?|\))\s+plus\s+(\d+(?:/\d+)?|\()', r'\1 + \2', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'(\d+(?:/\d+)?|\b[a-zA-Z]+(?:\^[23])?|\))\s+minus\s+(\d+(?:/\d+)?|\()', r'\1 - \2', cleaned, flags=re.IGNORECASE)
        # - OCR 't' between digits as '+'
        cleaned = re.sub(r'(\d)t(\d)', r'\1 + \2', cleaned)

        # 5. Equivalence and Relational comparisons:
        cleaned = re.sub(r'(\d+(?:/\d+)?|\b[a-zA-Z]+(?:\^[23])?|\))\s+(?:is\s+greater\s+than\s+or\s+equal\s+to|greater\s+than\s+or\s+equal\s+to)\s+(\d+(?:/\d+)?|\()', r'\1 >= \2', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'(\d+(?:/\d+)?|\b[a-zA-Z]+(?:\^[23])?|\))\s+(?:is\s+less\s+than\s+or\s+equal\s+to|less\s+than\s+or\s+equal\s+to)\s+(\d+(?:/\d+)?|\()', r'\1 <= \2', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'(\d+(?:/\d+)?|\b[a-zA-Z]+(?:\^[23])?|\))\s+(?:is\s+not\s+equal\s+to|not\s+equal\s+to)\s+(\d+(?:/\d+)?|\()', r'\1 != \2', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'(\d+(?:/\d+)?|\b[a-zA-Z]+(?:\^[23])?|\))\s+(?:is\s+equal\s+to|equals?\s+to|equals)\s+(\d+(?:/\d+)?|\()', r'\1 = \2', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'(\d+(?:/\d+)?|\b[a-zA-Z]+(?:\^[23])?|\))\s+(?:is\s+equal\s+to|equals?\s+to|equals)\s*(\?|$|\.)', r'\1 = \2', cleaned, flags=re.IGNORECASE)

        return cleaned

    def clean_equation_formatting(self, text: str) -> str:
        """
        Cleans spacing around parentheses and canonicalizes binary operator padding:
        - ( 3 + 4 ) -> (3 + 4)
        - 3+4 -> 3 + 4
        """
        cleaned = text

        # Clean parentheses spacing: ( 3 + 4 ) -> (3 + 4)
        cleaned = re.sub(r'\(\s+', '(', cleaned)
        cleaned = re.sub(r'\s+\)', ')', cleaned)

        # Standardize spacing around binary operators between numbers
        cleaned = re.sub(r'(\d)\s*([+*=])\s*(\d)', r'\1 \2 \3', cleaned)
        cleaned = re.sub(r'(\d)\s*-\s*(\d)', r'\1 - \2', cleaned)
        cleaned = re.sub(r'(\d)\s*(<=|>=|!=|<|>)\s*(\d)', r'\1 \2 \3', cleaned)

        return cleaned

    def clean_ocr_artifacts(self, text: str) -> str:
        """
        Fixes OCR digit/letter character confusions from worksheet scans:
        - 'l' or 'I' as '1' when adjacent to numbers (l2 -> 12, I0 -> 10)
        - 'O' as '0' in number sequences (2O -> 20, 1O0 -> 100)
        """
        cleaned = text

        # 1. Specific OCR single/double character replacements
        for k, v in self.ocr_map.items():
            pattern = r'\b' + re.escape(k) + r'\b'
            cleaned = re.sub(pattern, v, cleaned)

        # 2. Fix 'l' or 'I' leading a number: e.g. "l2", "I5", "l00"
        cleaned = re.sub(r'\b[lI](\d+)\b', r'1\1', cleaned)
        # Fix 'l' or 'I' trailing a number: e.g. "2l" -> "21"
        cleaned = re.sub(r'\b(\d+)[lI]\b', r'\g<1>1', cleaned)

        # 3. Fix 'O' inside digits: e.g. "2O" -> "20", "1O0" -> "100"
        cleaned = re.sub(r'(?<=\d)[oO](?=\d)', '0', cleaned)
        cleaned = re.sub(r'(?<=\d)[oO]\b', '0', cleaned)
        cleaned = re.sub(r'\b[oO](?=\d)', '0', cleaned)

        return cleaned

    def clean_voice_artifacts(self, text: str) -> str:
        """Fixes spoken math transcriptions into standard symbolic notation."""
        cleaned = text
        for phrase, replacement in self.voice_map.items():
            pattern = r'\b' + re.escape(phrase) + r'\b'
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        return cleaned

    def compress_repeated_characters(self, text: str) -> str:
        """Compresses 3 or more repeated characters: e.g. 'meee' -> 'me', 'sooo' -> 'so'."""
        return re.sub(r'([a-zA-Z])\1{2,}', r'\1', text)

    def normalize_tier1_regex(self, text: str) -> str:
        """
        Executes fast deterministic regex normalization (<1ms).
        Pipeline order:
        1. Longest-match-first dictionary replacement (slang, typos, math words)
        2. Unicode superscripts & exponents standardization
        3. Fractions standardization
        4. Scientific unit spacing
        5. OCR artifact cleaning (l2 -> 12, 2O -> 20)
        6. Math operators standardization (x, times, :, divided by, plus, minus)
        7. Spoken / voice artifact cleaning
        8. Excess repeated letters compression (meee -> me)
        9. Equation formatting & parentheses cleanup
        10. Whitespace collapsing
        """
        if not text or not text.strip():
            return ""

        cleaned = text.strip()

        # Step 1: Longest-match-first dictionary replacement (slang, typos, math words)
        if self._compiled_regex:
            def _replace_match(match):
                word = match.group(0).lower()
                return self._replacement_map.get(word, match.group(0))

            cleaned = self._compiled_regex.sub(_replace_match, cleaned)

        # Step 2: Unicode superscripts & shorthand exponents
        cleaned = self.standardize_units_and_exponents(cleaned)

        # Step 3: Fractions standardization (Unicode, ordinals, spaced, mixed)
        cleaned = self.standardize_fractions(cleaned)

        # Step 4: Unit spacing
        cleaned = self.standardize_units_and_exponents(cleaned)

        # Step 5: OCR artifact cleaning (digit/letter confusions)
        cleaned = self.clean_ocr_artifacts(cleaned)

        # Step 6: Math operators standardization
        cleaned = self.standardize_math_operators(cleaned)

        # Step 7: Spoken / voice artifact cleaning
        cleaned = self.clean_voice_artifacts(cleaned)

        # Step 8: Compress leftover excess repeated letters (e.g. 'meee' -> 'me')
        cleaned = self.compress_repeated_characters(cleaned)

        # Step 9: Clean equation formatting and parentheses
        cleaned = self.clean_equation_formatting(cleaned)

        # Step 10: Normalize multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned

    def should_trigger_llm(self, raw_text: str, tier1_text: str) -> bool:
        """
        Heuristic check to determine if Tier-2 Gemini LLM fallback is needed:
        - Only triggered on multi-word sentences (>= 3 words)
        - Triggers if Out-Of-Vocabulary (OOV) ratio > 30%
        """
        words = re.findall(r'[a-zA-Z]+', tier1_text)
        if len(words) < 3:
            return False  # Short answers stay fast-path

        if not self.known_vocab:
            return False

        oov_count = sum(1 for w in words if w.lower() not in self.known_vocab and w.lower() not in self._replacement_map.values())
        oov_ratio = oov_count / len(words)
        
        return oov_ratio > 0.30

    def verify_invariants(self, raw_text: str, cleaned_text: str) -> bool:
        """
        Post-LLM Safety Verification:
        Ensures that cleaning never alters numerical values or arithmetic operators.
        Normalizes raw_text deterministically first to recognize semantic math equivalents.
        """
        canonical_raw = self.normalize_tier1_regex(raw_text)
        raw_digits = re.findall(r'\d+', canonical_raw)
        cleaned_digits = re.findall(r'\d+', cleaned_text)
        
        # Operators check (+, -, *, /, =, ^)
        raw_ops = re.findall(r'[+\-*/=^]', canonical_raw)
        cleaned_ops = re.findall(r'[+\-*/=^]', cleaned_text)
        
        return (raw_digits == cleaned_digits) and (raw_ops == cleaned_ops)

    async def _llm_normalize_fallback(self, text: str, lang: str) -> Optional[str]:
        """
        Tier 2: Async Gemini Flash fallback with 1.5s timeout.
        Returns None if offline, unconfigured, or timed out.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None

        # Hotfix 0.1: Sanitize untrusted input for prompt copy (PII scrub + tag encode + length cap)
        from app.services.guardrails.pii_scrubber import sanitize_for_prompt
        safe_prompt_text = sanitize_for_prompt(text)

        prompt = prompt_controller.get_normalizer_prompt(text=safe_prompt_text, lang=lang)

        try:
            # We attempt to import and call google.genai or return None if not installed
            from google import genai
            client = genai.Client(api_key=api_key)
            
            async def _call_gemini():
                # Run synchronous call in thread pool for async compatibility
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt
                    )
                )
                return response.text.strip().strip('"')

            result = await asyncio.wait_for(_call_gemini(), timeout=1.5)
            return result
        except Exception:
            return None

    async def normalize_text(self, raw_text: str) -> str:
        """
        Master Async Normalizer:
        1. Fast Tier-1 Regex & OCR Normalization (<1ms)
        2. Heuristic check: triggers Tier-2 Gemini Fallback if needed
        3. Post-LLM Invariant Safety Verification
        """
        if not raw_text or not raw_text.strip():
            return ""

        tier1_result = self.normalize_tier1_regex(raw_text)
        
        if self.should_trigger_llm(raw_text, tier1_result):
            lang = self.detect_language(raw_text)
            llm_result = await self._llm_normalize_fallback(raw_text, lang)
            if llm_result and self.verify_invariants(raw_text, llm_result):
                return llm_result

        return tier1_result

    def normalize_text_sync(self, raw_text: str) -> str:
        """Synchronous deterministic normalization path (<1ms)."""
        return self.normalize_tier1_regex(raw_text)


# Global Singleton Instance for fast re-use and caching
_ENGINE = NormalizerEngine()

@lru_cache(maxsize=1024)
def normalize_text_sync(raw_text: str) -> str:
    """Cached synchronous normalizer entrypoint."""
    return _ENGINE.normalize_text_sync(raw_text)

async def normalize_text(raw_text: str) -> str:
    """Async hybrid normalizer entrypoint."""
    return await _ENGINE.normalize_text(raw_text)

def detect_language(text: str) -> str:
    """Detects language (khmer, khmenglish, english)."""
    return _ENGINE.detect_language(text)

def verify_invariants(raw_text: str, cleaned_text: str) -> bool:
    """Checks that numbers and math operators are preserved."""
    return _ENGINE.verify_invariants(raw_text, cleaned_text)
