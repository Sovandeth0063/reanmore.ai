"""
File: orchestrator/app/services/guardrails/safety_filter.py
Description: Child safety pre-filter for Elementary STEM tutoring (Sprint 4a - Task 4a.6).
             - Categorical Tier 2 Split:
               * TIER2_CHILD_ABUSE: Child abuse / domestic violence -> Safeguarding Lead
               * TIER2_SELF_HARM: Self-harm / suicidal ideation -> School Counselor + Child Helpline 1280
               * TIER2_IMMEDIATE_DANGER: Physical threats / kidnapping / fire -> Immediate trusted adult / 119
             - Trauma-informed safe responses in English & Khmer.
             - Never presumes secrecy or directs abused children to abusive parents.
             - Targeted PII scrubber.
"""

import re
from enum import Enum
from typing import List, Tuple, Optional
from pydantic import BaseModel, Field

from app.core.tutoring_config import (
    CHILD_HELPLINE_CAMBODIA,
    EMERGENCY_POLICE_CAMBODIA,
    EMERGENCY_AMBULANCE_CAMBODIA,
    EMERGENCY_SERVICES_FALLBACK,
)


class SafetyCategory(str, Enum):
    SAFE = "SAFE"
    PII = "PII"
    PROFANITY = "PROFANITY"
    BULLYING = "BULLYING"
    SELF_HARM = "SELF_HARM"
    TIER2_SELF_HARM = "TIER2_SELF_HARM"
    VIOLENCE = "VIOLENCE"
    INAPPROPRIATE = "INAPPROPRIATE"
    EXAM_ANXIETY = "EXAM_ANXIETY"
    ACADEMIC_FRUSTRATION = "ACADEMIC_FRUSTRATION"
    CHILD_ABUSE = "CHILD_ABUSE"
    TIER2_CHILD_ABUSE = "TIER2_CHILD_ABUSE"
    IMMEDIATE_DANGER = "IMMEDIATE_DANGER"
    TIER2_IMMEDIATE_DANGER = "TIER2_IMMEDIATE_DANGER"


class SafetyResult(BaseModel):
    is_safe: bool = Field(..., description="True if content is safe to proceed")
    severity_tier: int = Field(default=0, description="0=safe, 1=mild anxiety/frustration, 2=critical harm/abuse")
    categories_detected: List[SafetyCategory] = Field(default_factory=list)
    has_pii: bool = Field(default=False, description="True if personal identifiable information was found")
    redacted_text: str = Field(..., description="Sanitized text with PII replaced by protective tokens")
    safe_response: Optional[str] = Field(default=None, description="Child-friendly redirection response if unsafe")
    pii_notice: Optional[str] = Field(default=None, description="Privacy reminder if PII was detected")
    escalate: bool = Field(default=False, description="True only for Tier 2 critical safety signals")
    tier: Optional[str] = Field(default=None, description="Explicit tier string e.g. TIER2_CHILD_ABUSE")
    primary_category: Optional[str] = Field(default=None, description="Primary detected category")


class SafetyFilter:
    """
    Elementary safety filter (Sprint 4a):
    - Categorical Tier 2 split (Abuse, Harm, Danger).
    - Localized Cambodia crisis helplines (Child Helpline 1280).
    - School counselor & safeguarding lead first routing.
    """

    # --- PII Regex Patterns ---
    _PHONE_RE = re.compile(
        r'(?:\+?1[-.\s]?)?\(?\b[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    )
    _EMAIL_RE = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    )
    _ADDRESS_RE = re.compile(
        r'\b\d{1,5}\s+[A-Za-z0-9\s.,]+?\b(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Court|Ct|Terrace|Ter|Place|Pl|Circle|Cir)\b',
        re.IGNORECASE
    )
    _NAME_INTRO_RE = re.compile(
        r'\b(?:my\s+name\s+is|i\s+am|call\s+me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        re.IGNORECASE
    )

    # --- Inappropriate Patterns (Elementary Kid-Filtered) ---
    _PROFANITY_RE = re.compile(
        r'\b(?:damn|hell|crap|shit|fuck|bitch|ass|asshole|bastard|dick|piss)\b',
        re.IGNORECASE
    )
    _BULLYING_RE = re.compile(
        r'\b(?:you(?:\'?re|\s+are)\s+(?:stupid|dumb|ugly|an\s+idiot|trash|worthless)|'
        r'shut\s+up|i\s+hate\s+you|loser|get\s+lost)\b',
        re.IGNORECASE
    )

    # --- Tier 2B: Self-Harm Patterns ---
    _SELF_HARM_RE = re.compile(
        r'\b(?:kill(?:ing)?\s+myself|want\s+to\s+die|hurt\s+myself|suicide|cutting?\s+(?:my(?:self)?|wrists?|skin|arm|hand)|'
        r'cut\s+(?:my\s+)?(?:wrists?|arm|skin|hand)|commit\s+suicide|drink\s+poison|sleep\s+forever|'
        r'hang\s+myself|bleed|stab(?:bing)?\s+(?:my(?:self)?|arm)|end\s+(?:my\s+life|it)|'
        r'better\s+without\s+me|no\s+one\s+will\s+miss\s+me|goodbye\s+forever|wish\s+a\s+truck\s+would\s+hit\s+me|'
        r'pills?\s+so\s+i\s+can\s+sleep|bottle\s+of\s+pills|take\s+all\s+medicine|'
        r'(?:don\'?t|do\s+not|not?)\s+want\s+to\s+live|hate\s+my\s+life|jump\s+(?:from|off|in|into)\s+.*(?:roof|building|river|bridge)|'
        r'drown|painlessly|stop\s+the\s+pain|dying\s+is\s+better|'
        r'jong\s+commit\s+suicide|jong\s+slap|jong\s+somlab\s+khluon|somlab\s+khluon|jong\s+die|'
        r'knhom\s+cut\s+wrist|jong\s+jump|jong\s+cut\s+(?:my\s+)?(?:hand|wrist))\b|'
        r'(?:ចង់\s*ស្លាប់|សម្លាប់\s*ខ្លួន|មិន\s*ចង់\s*រស់|កាត់\s*ដៃ|ផឹកថ្នាំ|ចងក|បញ្ចប់ជីវិត|'
        r'បើខ្ញុំស្លាប់|លាហើយ|ចាក់ដៃ|លេបថ្នាំ|លោត|គ្មានអ្នកណានឹក|កាំបិតចាក់ដៃ)',
        re.IGNORECASE
    )

    # --- Tier 2A: Child Abuse Patterns ---
    _ABUSE_RE = re.compile(
        r'\b(?:(?:my\s+)?(?:dad|mom|uncle|stepdad|stepmom|parents?|cousin|neighbor|ke|pa|mak|mak\s+chong|poo)\s+.*'
        r'(?:hits?|beats?|hurts?|slaps?|slapped|burns?|burned|kicks?|threw|whipped|punish|locks?|forces?|pulls?|violent|drunk|does\s+bad\s+things)|'
        r'someone\s+(?:is\s+)?(?:touching|hurting|beating|hitting|forces?)\s+me|someone\s+hurts?\s+me|'
        r'someone\s+touching\s+me|someone\s+force\s+me|touch\s+him|touches\s+me|'
        r'i\s+am\s+being\s+(?:hurt|abused|beaten|hit)|'
        r'abuse|abused|(?:don\'?t\s+feel|not|feel\s+not)\s+safe\s+at\s+home|poo\s+.*beats?\s+me|'
        r'hit\s+me\s+with|whipped\s+with|private\s+parts|closet\s+for\s+hours|'
        r'comes\s+to\s+my\s+room|comes\s+into\s+my\s+room|'
        r'bruises?\s+on\s+my|(?:scared|afraid|fear|klach)\s+(?:of\s+)?(?:going\s+home|my\s+uncle|my\s+dad|him|her|them|someone|a\s+person|strangers?)|'
        r'burned?\s+my\s+hand|slapped?\s+me|pulls?\s+(?:my\s+)?clothes|nobody\s+feeds\s+me|'
        r'threw\s+a\s+.*bottle|told\s+me\s+not\s+to\s+tell|don\'?t\s+talk|'
        r'beat\s+me\s+with\s+(?:wire|stick)|ke\s+beat\s+me|pa\s+hit\s+me|pa\s+slap|'
        r'knhom\s+klach\s+going\s+home|poo\s+knhom\s+beat\s+me|ke\s+thveu\s+bab\s+knhom)\b|'
        r'(?:គេ\s*វាយ\s*ខ្ញុំ|គេ\s*ធ្វើ\s*បាប\s*ខ្ញុំ|មាន\s*គេ\s*ធ្វើ\s*បាប\s*ខ្ញុំ|'
        r'(?:ឪពុក|ពូ|ម្តាយ|ម៉ែ|ប៉ា|ម៉ាក់|ម៉ែចុង)(?:\s*ខ្ញុំ)?\s*(?:វាយ|ធ្វើបាប|ទះ|ទាត់|ដេញ|ស្រវឹង|ចាប់|បង្ខំ|ដុត)|'
        r'បៀតបៀន(?:រាងកាយ)?|មិន\s*(?:មាន\s*)?សុវត្ថិភាព|ខ្សែក្រវ៉ាត់|ចូលបន្ទប់ខ្ញុំ|កន្លែងកំបាំង|'
        r'ខ្លាច\s*មិន\s*ហ៊ាន\s*ទៅផ្ទះ|បង្ខំ\s*ខ្ញុំ|គំរាម|បិទទ្វារបន្ទប់|ដេញ\s*ខ្ញុំ\s*ចេញ|'
        r'ទាត់\s*ខ្ញុំ|ដំបង)',
        re.IGNORECASE
    )

    # --- Tier 2C: Immediate Danger & Violence Patterns ---
    _DANGER_RE = re.compile(
        r'\b(?:stranger.*(?:follow(?:ed|s|ing)?|offer(?:ed|s|ing)?|candy|pull(?:ed|s|ing)?|grab(?:bed|s|bing)?)|someone\s+(?:is\s+)?(?:follow(?:ed|s|ing)?)\s+me|'
        r'someone\s+follow\s+me|ke\s+follow\s+me|dor\s+tam\s+knhom|'
        r'two\s+(?:big\s+)?men\s+are\s+following|following\s+me\s+in\s+the\s+alley|'
        r'man\s+with\s+(?:a\s+)?(?:knife|gun|machete)|standing\s+outside\s+my\s+window|'
        r'house\s+is\s+on\s+fire|gas\s+leak|filling\s+with\s+smoke|smoke\s+everywhere|'
        r'fire\s+in\s+(?:my\s+house|kitchen)|cannot\s+breathe|'
        r'water\s+flooding|flooding\s+our\s+house|house\s+is\s+flooding|flood|'
        r'breaking\s+into|break\s+(?:my\s+)?window|force\s+open.*(?:door|window)|front\s+door|'
        r'kidnap|kidnapper|black\s+van|chasing\s+me|car\s+stop.*come\s+inside|'
        r'shoot\s+(?:us|you|everyone|people|kids|school)|threatening\s+to\s+shoot|'
        r'locked\s+outside\s+in\s+the\s+dark|grabbed?\s+my\s+(?:backpack|arm|hand)|'
        r'strange\s+person|thief.*(?:house|knife)|gun|bomb|murder|machete)\b|'
        r'(?:មនុស្សចម្លែក|ដើរតាម|គាស់ផ្ទះ|ផ្ទះ.*កំពុងឆេះ|ភ្លើងឆេះ|ដេញកាប់|តាមចាប់|កាន់កាំភ្លើង|ចាប់កាតាប|'
        r'ឡាន.*ឡើងជិះ|ទឹកជន់លិច|លួចមើល.*បង្អួច|តាមលួចមើល|ផ្សែង|ទាញដៃ|ចោរ|កាំបិត|ជាប់នៅក្នុងបន្ទប់)',
        re.IGNORECASE
    )

    # --- Tier 1: Mild Distress & Exam Anxiety ---
    _TIER1_ANXIETY_RE = re.compile(
        r'\b(?:(?:so\s+)?stressed\s+about\s+(?:the\s+)?(?:test|exam|math)|feel\s+(?:so\s+)?stupid|'
        r'math\s+(?:is\s+making|makes)\s+me\s+cry|hate\s+exams?|afraid\s+to\s+fail|failing\s+my\s+class|'
        r'too\s+tired\s+of\s+homework|(?:teacher|parents?|mom|dad)\s+will\s+be\s+mad|'
        r'headache\s+from\s+studying|quit\s+school|everyone\s+is\s+smarter)\b|'
        r'(?:klach\s+prolorng|math\s+makes\s+me\s+cry|tired\s+of\s+homework|mak\s+nung\s+khung|feel\s+so\s+stupid)',
        re.IGNORECASE
    )
    _KHMER_TIER1_RE = re.compile(
        r'(?:ខ្ញុំ\s*ខ្លាច\s*(?:ការ\s*)?ប្រឡង|ខ្ញុំ\s*ខ្លាច\s*ប្រឡង\s*ធ្លាក់|ខ្លួនឯង\s*ល្ងង់|'
        r'គណិតវិទ្យា\s*ធ្វើ\s*ឲ្យ\s*ខ្ញុំ\s*យំ|ស្អប់\s*ការ\s*ប្រឡង|ម៉ែ\s*(?:នឹង\s*)?ខឹង|'
        r'ឈឺក្បាល\s*(?:ណាស់\s*)?ពេល\s*រៀន|ចង់\s*ឈប់\s*រៀន|មិត្តភក្តិ\s*គេ\s*ចេះ\s*ទាំងអស់|'
        r'ខ្ញុំ\s*ពិបាកចិត្ត|រៀន\s*មិន\s*ចេះ|ហត់\s*ណាស់)',
        re.IGNORECASE
    )

    def redact_pii(self, text: str) -> Tuple[str, bool]:
        """Redacts personal identifying data."""
        redacted = text
        pii_found = False

        if self._PHONE_RE.search(redacted):
            redacted = self._PHONE_RE.sub("[PHONE_REDACTED]", redacted)
            pii_found = True

        if self._EMAIL_RE.search(redacted):
            redacted = self._EMAIL_RE.sub("[EMAIL_REDACTED]", redacted)
            pii_found = True

        if self._ADDRESS_RE.search(redacted):
            redacted = self._ADDRESS_RE.sub("[ADDRESS_REDACTED]", redacted)
            pii_found = True

        match_name = self._NAME_INTRO_RE.search(redacted)
        if match_name:
            full_name = match_name.group(1)
            redacted = redacted.replace(full_name, "[NAME_REDACTED]")
            pii_found = True

        return redacted, pii_found

    def evaluate(self, text: str) -> SafetyResult:
        """Full evaluation of child safety and PII with categorical Tier 2 split."""
        if not text or not text.strip():
            return SafetyResult(is_safe=True, redacted_text="", tier="TIER0_SAFE")

        categories: List[SafetyCategory] = []
        clean_text, has_pii = self.redact_pii(text)
        if has_pii:
            categories.append(SafetyCategory.PII)

        # 1. Tier 2B: Self-Harm Crisis
        if self._SELF_HARM_RE.search(text):
            categories.extend([SafetyCategory.SELF_HARM, SafetyCategory.TIER2_SELF_HARM])
            is_km = any(0x1780 <= ord(c) <= 0x17FF for c in text)
            safe_resp = (
                f"🛡️ ខ្ញុំពិតជារីករាយដែលប្អូនបានប្រាប់ខ្ញុំ។ ប្អូនមានតម្លៃណាស់ ហើយប្អូនមិននៅម្នាក់ឯងទេ។ "
                f"សូមនិយាយជាមួយអ្នកប្រឹក្សាយោបល់សាលា គ្រូបង្រៀន ឬមនុស្សធំដែលទុកចិត្តនៅក្បែរប្អូនឥឡូវនេះ។ "
                f"ប្រសិនបើមានគ្រោះថ្នាក់បន្ទាន់ សូមទូរស័ព្ទទៅ {EMERGENCY_AMBULANCE_CAMBODIA} (សង្គ្រោះបន្ទាន់)។ "
                f"ប្អូនក៏អាចទូរស័ព្ទ ឬផ្ញើសារទៅកាន់ខ្សែទូរស័ព្ទទាន់ហេតុការណ៍កុមារ {CHILD_HELPLINE_CAMBODIA} (ឥតគិតថ្លៃ និងសម្ងាត់ ២៤ម៉ោង/២៤ម៉ោង)។ 💛"
                if is_km else
                f"🛡️ I'm really glad you told me. You matter very much, and you don't have to carry this alone. "
                f"Please talk to your school counselor, teacher, or a trusted adult right now. "
                f"If you are in immediate danger, call {EMERGENCY_AMBULANCE_CAMBODIA} (Ambulance). "
                f"You can also call or text Child Helpline {CHILD_HELPLINE_CAMBODIA} (free, confidential, 24/7). 💛"
            )
            return SafetyResult(
                is_safe=False,
                severity_tier=2,
                tier="TIER2_SELF_HARM",
                primary_category="SELF_HARM",
                escalate=True,
                categories_detected=categories,
                has_pii=has_pii,
                redacted_text=clean_text,
                safe_response=safe_resp
            )

        # 2. Tier 2A: Child Abuse / Domestic Violence
        if self._ABUSE_RE.search(text):
            categories.extend([SafetyCategory.CHILD_ABUSE, SafetyCategory.TIER2_CHILD_ABUSE])
            is_km = any(0x1780 <= ord(c) <= 0x17FF for c in text)
            safe_resp = (
                f"🛡️ ខ្ញុំពិតជារីករាយដែលប្អូនបានប្រាប់ខ្ញុំ។ ប្អូនមានសុវត្ថិភាពនៅទីនេះ។ ខ្ញុំកំពុងចែករំលែកដំណឹងនេះទៅកាន់អ្នកទទួលបន្ទុកសុវត្ថិភាពសាលា ដើម្បីជួយគាំទ្រប្អូន។ "
                f"សូមនិយាយជាមួយគ្រូបង្រៀន ឬមនុស្សធំដែលទុកចិត្តនៅក្បែរប្អូនឥឡូវនេះ ឬទាក់ទងខ្សែទូរស័ព្ទកុមារ {CHILD_HELPLINE_CAMBODIA} (ឥតគិតថ្លៃ ២៤/២៤ម៉ោង)។ 💛"
                if is_km else
                f"🛡️ I'm really glad you told me. You are safe here. I am sharing this with your school safeguarding lead so they can support you. "
                f"Please talk to a teacher or trusted adult near you right now, or reach Child Helpline {CHILD_HELPLINE_CAMBODIA} (free 24/7). 💛"
            )
            return SafetyResult(
                is_safe=False,
                severity_tier=2,
                tier="TIER2_CHILD_ABUSE",
                primary_category="CHILD_ABUSE",
                escalate=True,
                categories_detected=categories,
                has_pii=has_pii,
                redacted_text=clean_text,
                safe_response=safe_resp
            )

        # 3. Tier 2C: Immediate Danger & Violence
        if self._DANGER_RE.search(text):
            categories.extend([SafetyCategory.VIOLENCE, SafetyCategory.TIER2_IMMEDIATE_DANGER])
            is_km = any(0x1780 <= ord(c) <= 0x17FF for c in text)
            safe_resp = (
                f"🛡️ សូមរត់ទៅរកគ្រូបង្រៀន បុគ្គលិកសាលា ឬមនុស្សធំដែលនៅក្បែរប្អូនឥឡូវនេះ។ "
                f"ប្រសិនបើមានគ្រោះថ្នាក់បន្ទាន់ សូមទូរស័ព្ទទៅ {EMERGENCY_POLICE_CAMBODIA} (នគរបាល) {EMERGENCY_AMBULANCE_CAMBODIA} (សង្គ្រោះបន្ទាន់) ឬខ្សែទូរស័ព្ទកុមារ {CHILD_HELPLINE_CAMBODIA} (២៤/២៤ម៉ោង)។ 💛"
                if is_km else
                f"🛡️ Please go to a teacher, school staff, or a trusted adult near you right now. "
                f"If there is immediate danger, call {EMERGENCY_POLICE_CAMBODIA} (Police), {EMERGENCY_AMBULANCE_CAMBODIA} (Ambulance), or Child Helpline {CHILD_HELPLINE_CAMBODIA} (24/7). 💛"
            )
            return SafetyResult(
                is_safe=False,
                severity_tier=2,
                tier="TIER2_IMMEDIATE_DANGER",
                primary_category="IMMEDIATE_DANGER",
                escalate=True,
                categories_detected=categories,
                has_pii=has_pii,
                redacted_text=clean_text,
                safe_response=safe_resp
            )

        # 4. Adult Content Check
        if re.search(r'\b(?:sex|sexy|porn|nude|naked|penis|vagina|boobs)\b', text, re.IGNORECASE):
            categories.append(SafetyCategory.INAPPROPRIATE)
            return SafetyResult(
                is_safe=False,
                severity_tier=2,
                tier="TIER2_INAPPROPRIATE",
                primary_category="INAPPROPRIATE",
                escalate=False,
                categories_detected=categories,
                has_pii=has_pii,
                redacted_text=clean_text,
                safe_response=(
                    "🌟 Let's focus on our school homework! What math or science question "
                    "would you like help with today?"
                )
            )

        # 5. Profanity Check (Tier 1)
        if self._PROFANITY_RE.search(text):
            categories.append(SafetyCategory.PROFANITY)
            return SafetyResult(
                is_safe=False,
                severity_tier=1,
                tier="TIER1_PROFANITY",
                primary_category="PROFANITY",
                escalate=False,
                categories_detected=categories,
                has_pii=has_pii,
                redacted_text=clean_text,
                safe_response=(
                    "✨ Oops! Let's use nice and kind words here. "
                    "Ready to solve your homework problem together?"
                )
            )

        # 6. Bullying Check (Tier 1)
        if self._BULLYING_RE.search(text):
            categories.append(SafetyCategory.BULLYING)
            return SafetyResult(
                is_safe=False,
                severity_tier=1,
                tier="TIER1_BULLYING",
                primary_category="BULLYING",
                escalate=False,
                categories_detected=categories,
                has_pii=has_pii,
                redacted_text=clean_text,
                safe_response=(
                    "💛 Kind words make learning fun! I'm here to help you do your best. "
                    "Let's work on our homework problem together!"
                )
            )

        # 7. Exam Anxiety & Academic Frustration (Tier 1 - Supportive, Non-blocking)
        if self._TIER1_ANXIETY_RE.search(text) or self._KHMER_TIER1_RE.search(text):
            categories.append(SafetyCategory.EXAM_ANXIETY)
            return SafetyResult(
                is_safe=True,
                severity_tier=1,
                tier="TIER1_EXAM_ANXIETY",
                primary_category="EXAM_ANXIETY",
                escalate=False,
                categories_detected=categories,
                has_pii=has_pii,
                redacted_text=clean_text,
                safe_response=(
                    "🌟 It's completely okay to feel nervous! Take a deep breath. "
                    "Mistakes help us learn and grow. You are doing great! 💪"
                )
            )

        pii_notice = None
        if has_pii:
            pii_notice = "🔒 *Privacy Tip: Keep your secret information safe! Never share real phone numbers or addresses online.*"

        return SafetyResult(
            is_safe=True,
            severity_tier=0,
            tier="TIER0_SAFE",
            primary_category="SAFE",
            escalate=False,
            categories_detected=categories,
            has_pii=has_pii,
            redacted_text=clean_text,
            pii_notice=pii_notice
        )


_DEFAULT_FILTER = SafetyFilter()

def evaluate_safety_tier(text: str) -> SafetyResult:
    """Convenience functional interface for safety evaluation."""
    return _DEFAULT_FILTER.evaluate(text)
