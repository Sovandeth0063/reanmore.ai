"""
File: orchestrator/app/services/state.py
Description: Defines the SocraticTutorState TypedDict schema representing state variables 
             persisted in LangGraph across tutor session turns.
"""

from typing import TypedDict, Optional, List, Dict, Any

class SocraticTutorState(TypedDict):
    # Core User Context
    query: str                         # Current question text (in English)
    session_id: str                    
    subject: Optional[str]             # 'MATH' | 'PHYSICS' | 'CHEMISTRY' | 'BIOLOGY' | 'GENERAL'
    grade_level: str                   # 'grade_1_3' | 'grade_4_6' | 'grade_7_9' | 'grade_10_12'
    language: str                      # 'en' | 'khmer'
    original_raw_query: Optional[str]  # User's raw input query in their native language
    
    # NLU / Query Understanding metadata
    user_intent: Optional[str]         # 'INITIAL_SOLVE' | 'STEP_ATTEMPT' | 'CLARIFY' | 'REQUEST_PRACTICE' | 'CHITCHAT'
    resolved_query: Optional[str]      # Query text resolved of pronouns and context
    search_keywords: Optional[str]     # Optimized keywords for Qdrant RAG searches
    
    # Hidden Ground Truth (computed by specialized service once on startup)
    solved_steps: List[Dict[str, Any]] # Solved steps: [{"step_num": 1, "expression": "3x = 9", "hint": "..."}]
    current_step_index: int            # Index of expected step student is on
    
    # Active Student Conversation
    student_attempt: str               # Student's latest message / step attempt
    hint_count: int                    # Consecutively failed attempts on current step
    history: List[Dict[str, str]]      # Message list: [{"role": "user"/"assistant", "content": "..."}]
    
    # Practice Mode Info
    practice_mode: bool                # Is this a similar practice problem?
    original_query: str                # The original exercise query
    
    # Output to Student
    tutor_feedback: str                # Hint or Socratic response to show the student
