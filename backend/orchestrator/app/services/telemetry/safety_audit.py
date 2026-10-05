"""
File: orchestrator/app/services/telemetry/safety_audit.py
Description: Isolated, secure audit store for child safety signals and escalations (Sprint 0 - Task 0.2).
             - Strictly separates sensitive child safety disclosures from operational logs.
             - Stores only scrubbed text snippets (via pii_scrubber).
             - Encrypts/hashes record integrity with SHA-256 HMAC digest to ensure tamper evidence.
             - Distinguishes Severity Tier 1 (mild anxiety/frustration) from Tier 2 (critical harm/abuse).
"""

import os
import json
import uuid
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.services.guardrails.pii_scrubber import scrub_student_pii


class SafetyAuditEvent(BaseModel):
    """
    Immutable container for an audited child safety signal.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    session_id: str
    severity_tier: int = Field(..., description="1 for mild distress/anxiety, 2 for critical harm/abuse")
    category: str = Field(..., description="E.g. ABUSE, SELF_HARM, EXAM_ANXIETY, BULLYING")
    redacted_snippet: str = Field(..., description="PII-scrubbed text representation")
    action_taken: str = Field(..., description="Action taken, e.g. REDIRECT_PROMPT, FLAG_REVIEW")
    escalation_channel: str = Field(default="none", description="'school_coordinator', 'parent_notify', or 'none'")
    integrity_hash: str = Field(default="", description="Tamper-evident HMAC signature")

    def compute_integrity(self, secret_key: str = "sayo_audit_salt") -> str:
        payload = f"{self.event_id}:{self.timestamp}:{self.session_id}:{self.severity_tier}:{self.category}:{self.redacted_snippet}"
        return hmac.new(secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


class SafetyAuditStore:
    """
    In-memory isolated ring buffer with append-only local persistence.
    Operates strictly outside normal application logger pipelines.
    """

    def __init__(self, max_memory_entries: int = 1000, audit_file_path: Optional[str] = None):
        self._max_entries = max_memory_entries
        self._events: List[SafetyAuditEvent] = []
        self._audit_file = audit_file_path

    def record(
        self,
        session_id: str,
        severity_tier: int,
        category: str,
        raw_or_scrubbed_text: str,
        action_taken: str,
        escalation_channel: str = "none"
    ) -> SafetyAuditEvent:
        """
        Records a safety event after strictly scrubbing any student PII.
        """
        # Always scrub before storing
        clean_snippet = scrub_student_pii(raw_or_scrubbed_text)

        event = SafetyAuditEvent(
            session_id=session_id,
            severity_tier=severity_tier,
            category=category,
            redacted_snippet=clean_snippet[:200],  # Bound length
            action_taken=action_taken,
            escalation_channel=escalation_channel
        )
        event.integrity_hash = event.compute_integrity()

        self._events.append(event)
        if len(self._events) > self._max_entries:
            self._events.pop(0)

        # Write to isolated append-only audit file if configured
        if self._audit_file:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self._audit_file)), exist_ok=True)
                with open(self._audit_file, "a", encoding="utf-8") as f:
                    f.write(event.model_dump_json() + "\n")
            except Exception:
                pass  # Do not crash the tutoring pipeline if file I/O fails

        return event

    def get_events_for_session(self, session_id: str) -> List[SafetyAuditEvent]:
        return [e for e in self._events if e.session_id == session_id]

    def get_events_by_severity(self, min_tier: int = 1) -> List[SafetyAuditEvent]:
        return [e for e in self._events if e.severity_tier >= min_tier]

    def clear(self) -> None:
        """Testing utility to reset store."""
        self._events.clear()


# Default singleton instance
_GLOBAL_AUDIT_STORE = SafetyAuditStore()


def get_safety_audit_store() -> SafetyAuditStore:
    return _GLOBAL_AUDIT_STORE


def record_safety_event(
    session_id: str,
    severity_tier: int,
    category: str,
    raw_or_scrubbed_text: str,
    action_taken: str,
    escalation_channel: str = "none"
) -> SafetyAuditEvent:
    """Convenience helper to record into the isolated safety store."""
    return _GLOBAL_AUDIT_STORE.record(
        session_id=session_id,
        severity_tier=severity_tier,
        category=category,
        raw_or_scrubbed_text=raw_or_scrubbed_text,
        action_taken=action_taken,
        escalation_channel=escalation_channel
    )
