"""
File: orchestrator/app/services/socratic/state.py
Description: Defines the TutorState TypedDict schema representing the persistent
             state machine context for the Socratic elementary tutoring workflow.
"""

from typing import TypedDict, Optional, List, Dict, Any
from app.services.socratic.card_schema import StepWidgetPayload, SocraticStep
from app.services.nlu.schema import NLUResult, StudentIntent


# Step attempt recorder class
class StepAttempt(TypedDict, total=False):
    step_number: int
    student_attempt: str
    is_correct: bool
    feedback: str
    hints_used: int


# Skill mastery record (Sprint 1 — persisted per concept)
class SkillRecord(TypedDict, total=False):
    correct_first_try: int
    needed_hints: int
    needed_reveal: int


# Tutor state - Persistent state of the Socratic session
class TutorState(TypedDict, total=False):
    # --- Session and Identity Context ---
    session_id: str
    raw_user_input: str
    grade_level: str               # "grade_1_3" | "grade_4_6"
    subject: str                   # "math" | "science" | "general" (from NLU)
    subtopic: Optional[str]        # "arithmetic", "photosynthesis", etc.

    # --- Safety & Guardrails (Part 4) ---
    is_safe: bool
    safety_violation: Optional[str]
    has_pii: bool
    redacted_input: Optional[str]
    is_deflected: bool
    deflection_message: Optional[str]
    flag_for_review: bool          # Sprint 1.4: flagged for teacher/parent review

    # --- OCR Quality Gate (Sprint 1.1) ---
    ocr_confidence: Optional[float]  # 0.0-1.0 confidence from OCR service
    ocr_confirmed: bool              # True after student confirms OCR text

    # --- Problem Context ---
    problem_text: str              # Problem statement as student sees it
    total_steps_count: int         # 2 to 4 decomposition steps
    steps_verified: bool           # Sprint 2.1: True when steps pass schema & math verification
    verification_issues: List[str] # List of verification warnings/errors
    decompose_retry_count: int     # Retries on decomposition failure
    validation_outcome: Optional[str] # Sprint 2.1: "correct" | "partial" | "incorrect"

    # --- Stepper Widget & Step Cards ---
    step_widget: Optional[Dict[str, Any]]  # Serialized StepWidgetPayload dictionary
    current_step_index: int                # Active 0-indexed step pointer

    # --- NLU Understanding ---
    nlu_result: Optional[Dict[str, Any]]   # Serialized NLUResult
    detected_intent: Optional[str]

    # --- Active Interaction and Hinting ---
    student_attempt: Optional[str]         # Current message / answer attempt
    target_nav_index: Optional[int]        # Step index for manual navigation
    active_hint: Optional[str]             # Current hint text being displayed
    current_hint_tier: int                 # 0=none, 1=nudge, 2=visual, 3=micro-breakdown
    attempt_history: List[Dict[str, Any]]

    # --- Frustration & Pacing (Sprint 1.3) ---
    frustration_score: float               # 0.0-1.0 cumulative frustration signal
    take_a_break: bool                     # True when break is recommended
    response_time_ms: Optional[float]      # Time taken for last answer (ms)
    idle_seconds: Optional[float]          # Idle time before last answer (s)

    # --- Mastery Tracking (Sprint 2.4 prep) ---
    mastery: Dict[str, Any]                # per-concept SkillRecord dicts

    # --- Output Payloads ---
    feedback_message: Optional[str]        # Feedback on current attempt
    formatted_markdown: Optional[str]
    is_problem_complete: bool              # True when all steps are finished
    is_problem_solved: bool                # Alias for backwards compatibility
    clarification_needed: bool             # True if query was ambiguous
    clarification_question: Optional[str]

    # --- Chat History ---
    messages: List[Dict[str, str]]

    # --- Ingress & Degradation (Sprint 0.3) ---
    unclear_streak: int                    # Consecutive UNCLEAR turns count
    degrade_to_tap_first: bool             # True when >= 3 consecutive UNCLEAR turns
    suggested_chips: Optional[List[str]]   # Tap-first choice chips (hints, pad, reread)