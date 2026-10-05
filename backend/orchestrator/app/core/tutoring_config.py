"""
File: orchestrator/app/core/tutoring_config.py
Description: Centralized Socratic Tutoring Configuration & Single Source of Truth (Sprint 4a - Task 4a.2).
             Resolves all historic discrepancies across thresholds, reveal policies,
             multimodal confidence gates, and safeguarding escalation targets.
"""

from typing import Final

# ─────────────────────────────────────────────────────────────────────────────
# 1. Socratic Grader & Tutoring Policies
# ─────────────────────────────────────────────────────────────────────────────

# Invariant: Near-miss feedback allowed strictly within +/- 1
PROXIMITY_FEEDBACK_TOLERANCE: Final[int] = 1

# Limit near-miss encouragement to at most once per step to prevent hot/cold guessing
MAX_PROXIMITY_FEEDBACK_PER_STEP: Final[int] = 1

# Explicit decision: Student must complete exactly 3 failed attempts before reveal/continuation option
MAX_ATTEMPTS_BEFORE_REVEAL: Final[int] = 3

# Frustration score threshold (0.0 to 1.0) above which a supportive break is offered
FRUSTRATION_BREAK_THRESHOLD: Final[float] = 0.8

# Consecutive unclear turns before degrading to tap-first UI (choice chips / keypad)
MAX_UNCLEAR_STREAK: Final[int] = 3

# Flag answers submitted in under 1.5 seconds ONLY if incorrect (anti-rapid guessing)
RAPID_WRONG_GUESS_TIME_S: Final[float] = 1.5

# ─────────────────────────────────────────────────────────────────────────────
# 2. Multimodal Quality Gates
# ─────────────────────────────────────────────────────────────────────────────

# Consolidated OCR confidence threshold: Tokens below 0.80 flagged for user verification
OCR_CONFIDENCE_THRESHOLD: Final[float] = 0.80

# STT transcription confidence threshold: Prompts audio confirmation below 0.85
STT_CONFIDENCE_THRESHOLD: Final[float] = 0.85

# Maximum decomposition retries before offering explicit similar-problem fallback
MAX_DECOMPOSITION_RETRIES: Final[int] = 2

# Maximum syllables per sentence for Khmer Grade 1–3 readability gate
MAX_KHMER_SYLLABLES_PER_SENTENCE: Final[int] = 25

# ─────────────────────────────────────────────────────────────────────────────
# 3. Safeguarding & Escalation Constants (Cambodia Context)
# ─────────────────────────────────────────────────────────────────────────────

# Emergency Services in Cambodia (Verified official dispatch numbers)
EMERGENCY_POLICE_CAMBODIA: Final[str] = "117"
EMERGENCY_FIRE_CAMBODIA: Final[str] = "118"
EMERGENCY_AMBULANCE_CAMBODIA: Final[str] = "119"

# Child Helpline Cambodia (Free, 24/7 child counseling and crisis reporting via phone & SMS)
CHILD_HELPLINE_CAMBODIA: Final[str] = "1280"
HELPLINE_SOURCE_CHECKED_DATE: Final[str] = "2026-10-04"
HELPLINE_WRITTEN_CONFIRMATION_PENDING: Final[bool] = True
CHILD_HELPLINE_VERIFIED_DATE: Final[str] = HELPLINE_SOURCE_CHECKED_DATE  # Alias for backward-compatibility

# Emergency Services Fallback string (accurately identifying police vs ambulance vs helpline)
EMERGENCY_SERVICES_FALLBACK: Final[str] = (
    f"{EMERGENCY_POLICE_CAMBODIA} (Police) / {EMERGENCY_AMBULANCE_CAMBODIA} (Ambulance) / {CHILD_HELPLINE_CAMBODIA} (Child Helpline 24/7)"
)

# Standard in-school escalation review SLA
SAFEGUARDING_REVIEW_SLA_MINUTES: Final[int] = 15

# Default designated human owner for escalation reviews
DEFAULT_SAFEGUARDING_OWNER: Final[str] = "DesignatedSchoolSafeguardingLead"

# Escalation portal URL for content-free notification pings
SAFEGUARDING_PORTAL_URL: Final[str] = "https://portal.reanmore.edu.kh/safeguarding"

# ─────────────────────────────────────────────────────────────────────────────
# 4. Standard Safe Fallback Clues & Praise Templates
# ─────────────────────────────────────────────────────────────────────────────

SAFE_PRAISE_FALLBACK_ENG: Final[str] = (
    "🎉 Awesome job! That is correct. Let's move to the next step!"
)

SAFE_PRAISE_FALLBACK_KHMER: Final[str] = (
    "🎉 អស្ចារ្យណាស់! អ្នកធ្វើបានត្រឹមត្រូវហើយ។ តោះទៅជំហានបន្ទាប់!"
)

SAFE_CLUE_FALLBACK_ENG: Final[str] = (
    "💡 You're on the right track! Think about the relationship between the numbers in this step. "
    "What operation can you apply next?"
)

SAFE_CLUE_FALLBACK_KHMER: Final[str] = (
    "💡 អ្នកដើរត្រូវផ្លូវហើយ! សូមគិតអំពីទំនាក់ទំនងរវាងលេខនៅក្នុងជំហាននេះ។ "
    "តើអ្នកអាចប្រើប្រមាណវិធីអ្វីបន្តទៀត?"
)

NEAR_MISS_FEEDBACK_ENG: Final[str] = (
    "💡 You are very close! Take another look at your calculation."
)

NEAR_MISS_FEEDBACK_KHMER: Final[str] = (
    "💡 ជិតត្រូវហើយ! សាកល្បងពិនិត្យការគិតលេខឡើងវិញណា៎!"
)

PROPERTY_QUERY_DEFLECTION_ENG: Final[str] = (
    "💡 I cannot confirm properties or clues directly! Let's look at the problem details together to figure it out step by step."
)

PROPERTY_QUERY_DEFLECTION_KHMER: Final[str] = (
    "💡 ខ្ញុំមិនអាចបញ្ជាក់លក្ខណៈ ឬតម្រុយដោយផ្ទាល់បានទេ! តោះពិនិត្យមើលព័ត៌មានលម្អិតក្នុងលំហាត់ទាំងអស់គ្នា ដើម្បីដោះស្រាយមួយជំហានម្តងៗ។"
)
