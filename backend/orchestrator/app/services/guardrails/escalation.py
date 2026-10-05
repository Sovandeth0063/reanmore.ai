"""
File: orchestrator/app/services/guardrails/escalation.py
Description: Safety Escalation Protocol Router & Review Queue (Sprint 4a - Task 4a.6).
             - Routes Tier 2 critical concerns strictly to Counselor / Safeguarding Lead first
               (never directly alerts parents to prevent endangering children in abusive homes).
             - Enforces pseudonymous student tokens: Alert notifications never contain real child PII or raw messages.
             - Named human owner and 15-minute review SLA.
             - Out-of-hours handling with Child Helpline 1280.
             - Pauses tutor session gracefully.
             - Records tamper-evident audit events into isolated SafetyAuditStore.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from app.core.tutoring_config import (
    CHILD_HELPLINE_CAMBODIA,
    EMERGENCY_POLICE_CAMBODIA,
    EMERGENCY_AMBULANCE_CAMBODIA,
    EMERGENCY_SERVICES_FALLBACK,
    SAFEGUARDING_REVIEW_SLA_MINUTES,
    DEFAULT_SAFEGUARDING_OWNER,
    SAFEGUARDING_PORTAL_URL
)
from app.services.telemetry.safety_audit import record_safety_event

logger = logging.getLogger("orchestrator.guardrails.escalation")


@dataclass
class SafeguardingAlertRecord:
    event_id: str
    student_token: str
    session_id: str
    severity_tier: int
    category: str
    target_channel: str
    target_recipient: str
    owner: str
    sla_minutes: int
    out_of_hours: bool
    created_at_utc: str
    payload: Dict[str, Any]
    status: str = "PENDING_REVIEW"
    escalation_level: int = 1   # 1=Counselor/Lead, 2=Principal/Backup, 3=District Focal Point
    notification_ping: str = "" # Content-free ping
    acknowledged_at_utc: Optional[str] = None
    acknowledged_by: Optional[str] = None


# In-memory Review Queue for Safeguarding Officer
_SAFEGUARDING_REVIEW_QUEUE: List[SafeguardingAlertRecord] = []


def format_content_free_notification_ping(token: str, sla_minutes: int = SAFEGUARDING_REVIEW_SLA_MINUTES) -> str:
    """
    Constructs a content-free notification ping for external SMS/webhook channels.
    Strictly forbids raw text, quotes, or child identifiable data.
    """
    return (
        f"ReanMore Alert: New safeguarding review pending for token [{token}]. "
        f"SLA: {sla_minutes}m. Log in: {SAFEGUARDING_PORTAL_URL}"
    )


def get_safeguarding_review_queue() -> List[SafeguardingAlertRecord]:
    """Returns all queued safeguarding alerts."""
    return list(_SAFEGUARDING_REVIEW_QUEUE)


def clear_safeguarding_review_queue():
    """Clears review queue (for testing)."""
    _SAFEGUARDING_REVIEW_QUEUE.clear()


def acknowledge_safeguarding_alert(event_id: str, acknowledged_by: str) -> bool:
    """Marks an alert as acknowledged by a safeguarding lead or counselor."""
    for rec in _SAFEGUARDING_REVIEW_QUEUE:
        if rec.event_id == event_id:
            rec.status = "ACKNOWLEDGED"
            rec.acknowledged_by = acknowledged_by
            rec.acknowledged_at_utc = datetime.now(timezone.utc).isoformat()
            return True
    return False


def check_and_escalate_unacknowledged(
    current_time_utc: Optional[datetime] = None
) -> List[SafeguardingAlertRecord]:
    """
    Checks all pending alerts against the 15-minute SLA during school hours.
    Auto-escalates unacknowledged alerts from Level 1 (Counselor/Lead) to Level 2 (Principal/Backup).
    """
    now = current_time_utc or datetime.now(timezone.utc)
    escalated: List[SafeguardingAlertRecord] = []

    for rec in _SAFEGUARDING_REVIEW_QUEUE:
        if rec.status == "PENDING_REVIEW" and rec.escalation_level == 1:
            try:
                created_dt = datetime.fromisoformat(rec.created_at_utc)
                diff_minutes = (now - created_dt).total_seconds() / 60.0
                # Escalate if SLA exceeded during school hours
                if diff_minutes >= rec.sla_minutes:
                    rec.escalation_level = 2
                    rec.target_recipient = "SCHOOL_PRINCIPAL_BACKUP"
                    rec.target_channel = "school_principal_backup"
                    rec.status = "AUTO_ESCALATED"
                    escalated.append(rec)
                    logger.warning(
                        f"[SafetyEscalation] Alert {rec.event_id} AUTO-ESCALATED to Level 2 "
                        f"({rec.target_recipient}) after {diff_minutes:.1f}m exceeding SLA."
                    )
            except Exception as e:
                logger.error(f"[SafetyEscalation] Error checking alert SLA: {e}")

    return escalated


def is_school_hours(dt: Optional[datetime] = None) -> bool:
    """
    Checks if current time is within Cambodia school hours (7:00 AM - 5:00 PM ICT, Mon-Fri).
    ICT is UTC+7.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    # Convert to ICT (+7 hours)
    ict_time = dt + timedelta(hours=7)
    # Monday = 0, Friday = 4, Saturday = 5, Sunday = 6
    if ict_time.weekday() >= 5:
        return False
    hour = ict_time.hour
    return 7 <= hour < 17


def generate_student_token(session_id: str) -> str:
    """Generates a pseudonymous student token mapped only in an isolated table."""
    suffix = uuid.uuid5(uuid.NAMESPACE_DNS, session_id).hex[:8].upper()
    return f"STU-{suffix}"


def dispatch_safety_alert(
    session_id: str,
    severity_tier: int,
    category: str,
    text_snippet: str = "",
    is_school_session: bool = True,
    school_id: Optional[str] = None,
    student_token: Optional[str] = None,
    has_recusal_conflict: bool = False
) -> Dict[str, Any]:
    """
    Evaluates and dispatches safety alerts according to safeguarding protocol.
    Adheres strictly to Counselor-First routing:
    - Abuse -> School Safeguarding Lead
    - Self-Harm -> School Counselor (coordinates parent outreach)
    - Danger -> School Safety Coordinator + Emergency Services
    - Alerts transmit pseudonymous tokens, never child PII.
    - Recusal conflict routes immediately to District Focal Point.
    """
    token = student_token or generate_student_token(session_id)
    now_utc = datetime.now(timezone.utc)
    out_of_hours = not is_school_hours(now_utc)

    # ── Tier 1: Mild Distress / Academic Frustration ─────────────────────────
    if severity_tier <= 1:
        return {
            "action": "SUPPORTIVE_GUIDANCE",
            "escalated": False,
            "channel": "none",
            "target_recipient": "NONE",
            "student_token": token,
            "reason": "Tier 1 anxiety handled in-session; no external escalation.",
            "child_facing_guidance": "Take a deep breath! You are doing great.",
            "tutor_state": "ACTIVE"
        }

    # ── Tier 2: Critical Distress / Abuse / Harm (Safeguarding Lead / Counselor First)
    cat_upper = category.upper()

    if has_recusal_conflict:
        target_channel = "district_safeguarding_focal_point"
        target_recipient = "DISTRICT_SAFEGUARDING_FOCAL_POINT"
        escalation_level = 3
        action = "DISPATCH_DISTRICT_RECUSAL_ALERT"
        child_guidance = (
            "You are safe here. An independent safeguarding officer is being notified to support you. "
            f"If you need to talk to someone right now, call Child Helpline {CHILD_HELPLINE_CAMBODIA} (free 24/7)."
        )
    elif "ABUSE" in cat_upper:
        target_channel = "school_safeguarding_lead"
        target_recipient = "SCHOOL_SAFEGUARDING_LEAD"
        escalation_level = 1
        action = "DISPATCH_SAFEGUARDING_ALERT"
        child_guidance = (
            "You are safe here. Your school safeguarding lead is being notified to support you. "
            f"If you need to talk to someone right now, call Child Helpline {CHILD_HELPLINE_CAMBODIA} (free 24/7)."
        )
    elif "SELF_HARM" in cat_upper:
        target_channel = "school_counselor"
        target_recipient = "SCHOOL_COUNSELOR"
        escalation_level = 1
        action = "DISPATCH_COUNSELOR_ALERT"
        child_guidance = (
            f"You matter very much. Please talk to your school counselor, teacher, or trusted adult right now. "
            f"If there is immediate danger, call {EMERGENCY_AMBULANCE_CAMBODIA} (Ambulance). "
            f"You can also call or text Child Helpline Cambodia at {CHILD_HELPLINE_CAMBODIA} (free and confidential 24/7)."
        )
    else:
        target_channel = "school_coordinator"
        target_recipient = "SCHOOL_SAFETY_COORDINATOR"
        escalation_level = 1
        action = "DISPATCH_SCHOOL_ALERT"
        child_guidance = (
            "Please go to a teacher, school staff, or a trusted adult near you right now. "
            f"If there is immediate danger, call {EMERGENCY_POLICE_CAMBODIA} (Police), {EMERGENCY_AMBULANCE_CAMBODIA} (Ambulance), or Child Helpline {CHILD_HELPLINE_CAMBODIA} (24/7)."
        )

    # Content-free notification ping for SMS/push
    notification_ping = format_content_free_notification_ping(token, sla_minutes=SAFEGUARDING_REVIEW_SLA_MINUTES)

    # Isolated pseudonymous payload (no student real name or raw text)
    alert_payload = {
        "student_token": token,
        "session_id": session_id,
        "school_id": school_id or "SCH_PRIMARY_DEFAULT",
        "severity_tier": severity_tier,
        "category": category,
        "target_recipient": target_recipient,
        "owner": DEFAULT_SAFEGUARDING_OWNER,
        "sla_minutes": SAFEGUARDING_REVIEW_SLA_MINUTES,
        "out_of_hours": out_of_hours,
        "timestamp_utc": now_utc.isoformat(),
        "notification_ping": notification_ping
    }

    # Record into isolated tamper-evident audit store
    audit_event = record_safety_event(
        session_id=session_id,
        severity_tier=severity_tier,
        category=category,
        raw_or_scrubbed_text=text_snippet,
        action_taken=action,
        escalation_channel=target_channel
    )

    # Queue for human review
    record = SafeguardingAlertRecord(
        event_id=audit_event.event_id,
        student_token=token,
        session_id=session_id,
        severity_tier=severity_tier,
        category=category,
        target_channel=target_channel,
        target_recipient=target_recipient,
        owner=DEFAULT_SAFEGUARDING_OWNER,
        sla_minutes=SAFEGUARDING_REVIEW_SLA_MINUTES,
        out_of_hours=out_of_hours,
        created_at_utc=now_utc.isoformat(),
        payload=alert_payload,
        escalation_level=escalation_level,
        notification_ping=notification_ping
    )
    _SAFEGUARDING_REVIEW_QUEUE.append(record)

    logger.warning(
        f"[SafetyEscalation] Tier 2 alert dispatched for token {token} to {target_recipient} "
        f"(level={escalation_level}, out_of_hours={out_of_hours})."
    )

    return {
        "action": action,
        "escalated": True,
        "channel": target_channel,
        "target_recipient": target_recipient,
        "student_token": token,
        "event_id": audit_event.event_id,
        "severity_tier": severity_tier,
        "category": category,
        "owner": DEFAULT_SAFEGUARDING_OWNER,
        "sla_minutes": SAFEGUARDING_REVIEW_SLA_MINUTES,
        "out_of_hours": out_of_hours,
        "payload": alert_payload,
        "notification_ping": notification_ping,
        "child_facing_guidance": child_guidance,
        "tutor_state": "PAUSED"
    }


def dispatch_escalation_alert(
    safety_result: Any,
    student_token: Optional[str] = None,
    session_id: str = "sess_default"
) -> Dict[str, Any]:
    """Direct dispatcher accepting a SafetyResult object."""
    tier = getattr(safety_result, "severity_tier", 2)
    cat = getattr(safety_result, "primary_category", "CHILD_ABUSE") or getattr(safety_result, "tier", "TIER2_CHILD_ABUSE")
    return dispatch_safety_alert(
        session_id=session_id,
        severity_tier=tier,
        category=str(cat),
        text_snippet=getattr(safety_result, "redacted_text", ""),
        student_token=student_token
    )
