"""
File: orchestrator/app/services/pipeline_tracer.py
Description: End-to-end Question Projection Tracer for the Socratic Orchestrator.
             Tracks and visualizes the lifecycle:
             Raw Query -> Normalize -> Rewrite if needed -> Route to Microservice -> Results
             Formats a clean, tidy, structured console/log projection box.
"""

import re
from typing import Optional, Dict, Any, Tuple, List
from pydantic import BaseModel, Field

from app.services.nlu.normalizer import normalize_text_sync
from app.services.nlu.router import route_subject_heuristic, SubjectArea
from app.core.config import settings


class PipelineTrace(BaseModel):
    """
    Structured container for the full question projection pipeline.
    """
    session_id: str = Field(default="")
    grade_level: str = Field(default="grade_1_3")
    raw_query: str = Field(description="Original student query input")
    normalized_query: str = Field(description="Cleaned, standardized text (math, typos, units)")
    rewrite_needed: bool = Field(default=False, description="True if coreference/contextual rewriting was applied")
    rewritten_query: str = Field(description="Query after contextual rewrite (or normalized if not rewritten)")
    rewrite_note: str = Field(default="Self-contained query", description="Reasoning or notes on rewrite decision")
    subject: str = Field(default="GENERAL", description="Subject area: MATH, SCIENCE, or GENERAL")
    subtopic: str = Field(default="general", description="Granular detected subtopic")
    intent: str = Field(default="INITIAL_QUESTION", description="Detected student intent")
    target_service: str = Field(description="Target microservice name or orchestrator subsystem")
    service_endpoint: str = Field(description="Target microservice URL or internal handler")
    routing_reason: str = Field(default="", description="Why this route was selected")
    result_summary: str = Field(description="Concise summary of tutor action and step progression")
    is_deflected: bool = Field(default=False)
    is_problem_complete: bool = False
    latency_ms: float = Field(default=0.0, description="Execution time in milliseconds")
    status: str = Field(default="SUCCESS", description="SUCCESS | DEFLECTED | BLOCKED | ERROR")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


def normalize_query(raw_query: str) -> str:
    """
    Runs deterministic normalization on student query.
    Standardizes math symbols, fixes common kid typos, contractions, and unit spacing.
    """
    if not raw_query:
        return ""
    return normalize_text_sync(raw_query.strip())


from app.services.llm import llm_service, ModelTier

# Regex patterns for coreference pronouns and elliptical queries
_PRONOUN_RE = re.compile(r'\b(it|this|that|these|those|its|them|they)\b', re.IGNORECASE)
_ELLIPTICAL_RE = re.compile(
    r'^(how\??|why\??|what\??|what now\??|what next\??|what about (?:it|this|that)\??|how to do (?:it|this)\??|how do i (?:do it|solve it)\??|is that right\??|is it right\??|am i right\??|hint|help|help me|idk|i am stuck|stuck)$',
    re.IGNORECASE
)


def resolve_query_rewrite(
    query: str,
    normalized_query: str,
    active_step: Optional[Dict[str, Any]] = None,
    previous_query: Optional[str] = None,
    history: Optional[List[Dict[str, Any]]] = None,
    has_active_problem: bool = False
) -> Tuple[str, bool, str]:
    """
    Evaluates whether the question requires coreference or contextual rewriting.
    Uses LLM Management Service (ModelTier.FAST) with deterministic fallback.
    
    Returns:
        (rewritten_query, rewrite_needed, rewrite_note)
    """
    norm = normalized_query or query
    has_pronoun = bool(_PRONOUN_RE.search(norm))
    is_elliptical = bool(_ELLIPTICAL_RE.search(norm))
    is_short_attempt = bool(
        has_active_problem and active_step and len(norm.split()) <= 4 and 
        not norm.lower().startswith(("what", "why", "how", "solve", "can"))
    )

    # Fast-path: if query has no pronouns, is not elliptical, and has no active context -> self-contained
    if not has_pronoun and not is_elliptical and not is_short_attempt and not previous_query:
        return (norm, False, "Self-contained query (no rewrite needed)")

    # Direct contextualization for short answer attempts (e.g. "7", "6 cookies", "photosynthesis")
    # Preserves student's actual step answer attempt without prompting an LLM to hallucinate a new question
    if is_short_attempt and active_step:
        step_num = active_step.get("step_number", 1)
        step_title = active_step.get("title", f"Step {step_num}")
        mission = active_step.get("mission", "")
        rewritten = f"Step {step_num} Attempt: '{norm}' for mission '{mission or step_title}'"
        return (rewritten, True, f"Contextualized answer attempt for active Step {step_num}")

    # 1. Primary: LLM Gateway Coreference Resolution (for pronouns and elliptical queries)
    try:

        context_parts = []
        if active_step:
            context_parts.append(
                f"Active Step {active_step.get('step_number')}: {active_step.get('title')} "
                f"(Mission: {active_step.get('mission', '')})"
            )
        if history:
            for h in history[-3:]:
                role = "Student" if h.get("role") in ["user", "student"] else "Tutor"
                text = h.get("content") or h.get("user_input") or h.get("bot_response") or ""
                if text:
                    context_parts.append(f"{role}: {text}")
        elif previous_query:
            context_parts.append(f"Previous student query: {previous_query}")

        context_str = "\n".join(context_parts) if context_parts else "No previous history."
        prompt = (
            "You are an elementary STEM question coreference rewriter.\n"
            "Examine the conversation history and active step context. Rewrite the student's latest query "
            "to resolve all pronouns ('it', 'this', 'that', 'they') and elliptical references into a clear, standalone question.\n"
            "- If the query is already self-contained or does not need rewriting, return it exactly as-is.\n"
            "Return ONLY the rewritten query text without quotes, formatting, or preamble.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Latest Query: '{norm}'"
        )
        resp = llm_service.generate_text(prompt=prompt, model_tier=ModelTier.FAST)
        if resp.provider != "mock" or resp.text != "Mock LLM generated response.":
            candidate = resp.text.strip().strip('"\'')
            if candidate and candidate.lower() != norm.lower():
                return (candidate, True, f"LLM Coreference Rewrite ({resp.provider}/{resp.model_name})")
            elif candidate:
                return (candidate, False, "Self-contained query (LLM verified)")
    except Exception:
        pass  # Fallback to deterministic resolution

    # 2. Deterministic Fallback (if LLM is unavailable or offline)
    if has_active_problem and active_step:
        step_num = active_step.get("step_number", 1)
        step_title = active_step.get("title", f"Step {step_num}")
        mission = active_step.get("mission", "")

        if has_pronoun or is_elliptical:
            clean_q = _PRONOUN_RE.sub(f"Step {step_num} ({step_title})", norm)
            rewritten = f"{clean_q} [Context: {mission}]" if mission else clean_q
            return (rewritten, True, f"Resolved pronoun/elliptical reference to active Step {step_num}")

        if is_short_attempt:
            rewritten = f"Step {step_num} Attempt: '{norm}' for mission '{mission or step_title}'"
            return (rewritten, True, f"Contextualized answer attempt for active Step {step_num}")

    if previous_query and has_pronoun and not has_active_problem:
        rewritten = _PRONOUN_RE.sub(f"'{previous_query}'", norm)
        return (rewritten, True, "Resolved pronoun using previous conversation context")

    return (norm, False, "Self-contained query (no rewrite needed)")


def determine_routing(
    subject: str,
    subtopic: str,
    intent: str,
    is_deflected: bool = False,
    is_safe: bool = True
) -> Tuple[str, str, str]:
    """
    Determines the target microservice / subsystem, endpoint URL, and routing reason.
    """
    if not is_safe:
        return (
            "ORCHESTRATOR_GUARDRAILS",
            "app.services.guardrails.safety_filter",
            "Child safety guardrail triggered - blocked unsafe content"
        )

    if is_deflected:
        return (
            "ORCHESTRATOR_GUARDRAILS",
            "app.services.guardrails.educational_scope",
            "Off-topic distraction detected - deflected back to STEM homework"
        )

    if intent == "NAVIGATION_JUMP":
        return (
            "ORCHESTRATOR_STEPPER_NAVIGATOR",
            "/api/step/navigate",
            "Direct stepper jump to specific step card"
        )

    if intent == "REQUEST_HINT":
        return (
            "ORCHESTRATOR_HINT_ENGINE",
            "app.services.socratic.hint_engine.HintEngine",
            "Pedagogical 3-tier progressive hint request"
        )

    subj_upper = subject.upper()
    math_url = getattr(settings, "MATH_SERVICE_URL", "http://localhost:9001")
    science_url = getattr(settings, "SCIENCE_SERVICE_URL", "http://localhost:9002")

    if subj_upper == "MATH":
        if intent == "STEP_ANSWER_ATTEMPT":
            endpoint = f"{math_url}/validate"
            reason = f"Math domain validation ({subtopic}) via Math Microservice"
        else:
            endpoint = f"{math_url}/solve"
            reason = f"Math problem decomposition & solving ({subtopic}) via Math Microservice"
        return ("MATH_SERVICE", endpoint, reason)

    if subj_upper == "SCIENCE":
        if intent == "STEP_ANSWER_ATTEMPT":
            endpoint = f"{science_url}/validate"
            reason = f"Science domain concept validation ({subtopic}) via Science Microservice"
        else:
            endpoint = f"{science_url}/solve"
            reason = f"Science question decomposition & reasoning ({subtopic}) via Science Microservice"
        return ("SCIENCE_SERVICE", endpoint, reason)

    # General Socratic decomposition
    return (
        "ORCHESTRATOR_SOCRATIC_STEPPER",
        "app.services.socratic.graph.socratic_graph",
        f"Elementary Socratic tutor loop ({subtopic}) via Central Orchestrator"
    )


def summarize_results(
    widget_dict: Optional[Dict[str, Any]],
    current_step_idx: int,
    current_hint_tier: int,
    is_complete: bool,
    is_deflected: bool,
    feedback_message: str = ""
) -> str:
    """
    Generates a concise, single-line summary of the pipeline execution results.
    """
    if is_deflected:
        short_fb = (feedback_message[:60] + "...") if len(feedback_message) > 60 else feedback_message
        return f"Deflected to homework: {short_fb}"

    if is_complete:
        return "🎉 Problem Complete! All steps solved successfully."

    if widget_dict and "steps" in widget_dict:
        steps = widget_dict.get("steps", [])
        total = len(steps)
        curr = current_step_idx + 1
        active_title = ""
        active_ans = ""
        if 0 <= current_step_idx < total:
            active_title = steps[current_step_idx].get("title", f"Step {curr}")
            active_ans = steps[current_step_idx].get("expected_answer", "")

        hints_str = f" | Hints: Tier {current_hint_tier}" if current_hint_tier > 0 else ""
        expected_str = f" | Target: '{active_ans}'" if active_ans else ""
        return f"Step {curr}/{total} Active: '{active_title}'{expected_str}{hints_str}"

    if feedback_message:
        clean_fb = feedback_message.replace("\n", " ").strip()
        return (clean_fb[:70] + "...") if len(clean_fb) > 70 else clean_fb

    return "Socratic response generated."


def format_tidy_pipeline_log(trace: PipelineTrace, box_width: int = 88) -> str:
    """
    Renders an elegant, tidy ASCII/Unicode projection box for orchestrator logs.
    Guarantees consistent line lengths and beautiful visual hierarchy across all terminals.
    """
    def pad_line(label: str, text: str) -> str:
        prefix = f"│ {label:<14}: "
        # Calculate available space for text
        available = box_width - len(prefix) - 2
        if available < 10:
            available = 10
        if len(text) > available:
            trimmed = text[:available - 3] + "..."
        else:
            trimmed = text
        padding = " " * (box_width - len(prefix) - len(trimmed) - 2)
        return f"{prefix}{trimmed}{padding}│"

    # Rewrite display text
    if trace.rewrite_needed:
        rewrite_display = f"[Rewritten] {trace.rewritten_query}"
    else:
        rewrite_display = "[No rewrite needed] (self-contained)"

    # Shorten service endpoint if URL
    endpoint_display = trace.service_endpoint
    if "/solve" in endpoint_display:
        endpoint_display = "/solve"
    elif "/validate" in endpoint_display:
        endpoint_display = "/validate"
    elif len(endpoint_display) > 30:
        endpoint_display = endpoint_display.split(".")[-1]

    # Routing display text
    routing_display = f"{trace.subject} ({trace.subtopic}) ──▶ {trace.target_service} ({endpoint_display})"

    # Timing / status display
    status_display = (
        f"{trace.latency_ms:.2f} ms | Grade: {trace.grade_level} | "
        f"Intent: {trace.intent} | Status: {trace.status}"
    )

    header_title  = " [QUESTION PIPELINE PROJECTION TRACE] "
    header_dashes = (box_width - 2 - len(header_title)) // 2
    header_line   = "┌" + "─" * header_dashes + header_title + "─" * (box_width - 2 - header_dashes - len(header_title)) + "┐"
    divider_line  = "├" + "─" * (box_width - 2) + "┤"
    bottom_border = "└" + "─" * (box_width - 2) + "┘"

    lines = [
        header_line,
        pad_line("Session ID", trace.session_id or "N/A"),
        pad_line("1. Raw Query", trace.raw_query),
        pad_line("2. Normalize", trace.normalized_query),
        pad_line("3. Rewrite", rewrite_display),
        pad_line("4. Routing", routing_display),
        pad_line("5. Results", trace.result_summary),
        divider_line,
        pad_line("⏱  Execution", status_display),
        bottom_border,
    ]

    return "\n".join(lines)
