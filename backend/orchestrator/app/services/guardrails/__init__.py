"""
File: orchestrator/app/services/guardrails/__init__.py
Description: Public exports for the Child Safety Guardrails & Educational Scope Deflector.
"""

from app.services.guardrails.safety_filter import (
    SafetyFilter,
    SafetyResult,
    SafetyCategory
)
from app.services.guardrails.educational_scope import (
    EducationalScopeDeflector,
    ScopeCheckResult,
    OffTopicCategory
)
def __getattr__(name: str):
    if name in ("LeakGuard", "check_tutor_response_leak", "check_response_for_leaks"):
        from app.services.guardrails import leak_guard
        return getattr(leak_guard, name)
    if name in (
        "dispatch_safety_alert",
        "dispatch_escalation_alert",
        "dispatch_external_safeguarding_ping",
        "get_safeguarding_review_queue",
        "clear_safeguarding_review_queue",
        "format_content_free_notification_ping",
        "SafeguardingAlertRecord",
    ):
        from app.services.guardrails import escalation
        return getattr(escalation, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "SafetyFilter",
    "SafetyResult",
    "SafetyCategory",
    "EducationalScopeDeflector",
    "ScopeCheckResult",
    "OffTopicCategory",
    "LeakGuard",
    "check_tutor_response_leak",
    "check_response_for_leaks",
    "dispatch_safety_alert",
    "dispatch_escalation_alert",
    "dispatch_external_safeguarding_ping",
    "get_safeguarding_review_queue",
    "clear_safeguarding_review_queue",
    "format_content_free_notification_ping",
    "SafeguardingAlertRecord",
]
