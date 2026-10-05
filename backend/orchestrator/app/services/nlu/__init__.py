"""
Package: orchestrator/app/services/nlu
Description: Natural Language Understanding (NLU) Pipeline for elementary student queries.
"""

from app.services.nlu.schema import (
    StudentIntent,
    SubjectArea,
    GradeTier,
    NLUResult,
)
from app.services.nlu.normalizer import (
    normalize_text,
    normalize_text_sync,
    detect_language,
    verify_invariants,
)
from app.services.nlu.clarify import (
    AmbiguityType,
    AmbiguityResult,
    detect_ambiguity,
    is_gibberish_sync,
    get_kid_friendly_reprompt,
)
from app.services.nlu.intent import (
    IntentType,
    IntentResult,
    classify_intent,
    classify_intent_sync,
    classify_intent_heuristic,
    format_chat_history,
    extract_core_answer,
    disambiguate_step_input,
    is_step_active,
    get_off_topic_redirection_prompt,
    generate_off_topic_redirection_llm,
)
from app.services.nlu.router import (
    RoutingResult,
    route_subject,
    route_subject_sync,
    route_subject_heuristic,
    route_subject_and_grade,
    route_subject_and_grade_sync,
    route_subject_and_grade_heuristic,
)
from app.services.nlu.pipeline import (
    process_nlu,
    process_nlu_sync,
)
from app.services.nlu.context_cache import (
    ContextCache,
    generate_context_cache_key,
    is_cacheable_intent,
)
from app.services.nlu.interpretation_schema import (
    StudentInterpretation,
    resolve_answer_candidates,
    is_disjunctive_inquiry,
    has_correction_marker,
)
from app.services.nlu.node import (
    nlu_node,
    nlu_node_sync,
)

__all__ = [
    "StudentIntent",
    "SubjectArea",
    "GradeTier",
    "NLUResult",
    "normalize_text",
    "normalize_text_sync",
    "detect_language",
    "verify_invariants",
    "AmbiguityType",
    "AmbiguityResult",
    "detect_ambiguity",
    "is_gibberish_sync",
    "get_kid_friendly_reprompt",
    "IntentType",
    "IntentResult",
    "classify_intent",
    "classify_intent_sync",
    "classify_intent_heuristic",
    "format_chat_history",
    "extract_core_answer",
    "disambiguate_step_input",
    "is_step_active",
    "get_off_topic_redirection_prompt",
    "generate_off_topic_redirection_llm",
    "RoutingResult",
    "route_subject",
    "route_subject_sync",
    "route_subject_heuristic",
    "route_subject_and_grade",
    "route_subject_and_grade_sync",
    "route_subject_and_grade_heuristic",
    "process_nlu",
    "process_nlu_sync",
    "nlu_node",
    "nlu_node_sync",
    "ContextCache",
    "generate_context_cache_key",
    "is_cacheable_intent",
    "StudentInterpretation",
    "resolve_answer_candidates",
    "is_disjunctive_inquiry",
    "has_correction_marker",
]
