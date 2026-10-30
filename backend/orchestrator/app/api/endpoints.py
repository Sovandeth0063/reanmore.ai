"""
File: orchestrator/app/api/endpoints.py
Description: FastAPI endpoint router exposing /api/query, /api/step/navigate, and /api/session routes.
             Executes student prompts through the 4-Part Socratic card LangGraph workflow
             with Grade 1-3 pedagogy, child safety guardrails, Stepper Widget payloads,
             Khmer-English pivot translation, and Redis session persistence with re-hydration.
"""

import re
import time
import uuid
import asyncio
from collections import OrderedDict
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends, status
from pydantic import BaseModel, Field
from app.core.config import settings
from app.services.llm import llm_service, ModelTier
from app.core.logging import logger
from app.api.auth import get_optional_user, get_current_user
from app.services.quota.quota_guard import quota_guard, QuotaExhaustedException
from app.infrastructure.database import (
    save_session_and_telemetry,
    get_all_session_logs,
    save_worksheet_session_to_db,
    delete_session_from_db,
    get_student_telemetry_stats,
)
from app.services.socratic.graph import socratic_graph, _is_answer_equivalent
from app.services.socratic.math_engine.cas import strip_arithmetic_wrappers
from app.services.socratic.validate_answer import validate_student_answer
from app.services.socratic.card_schema import StepWidgetPayload
from app.services.socratic.prompts.controller import socratic_prompt_controller as prompt_controller
from app.services.session import session_manager
from app.services.pipeline_tracer import (
    PipelineTrace,
    normalize_query,
    resolve_query_rewrite,
    determine_routing,
    summarize_results,
    format_tidy_pipeline_log,
)
from app.services.nlu.router import route_subject_heuristic
from app.services.nlu.intent import classify_intent_heuristic, IntentType
from app.services.nlu.pipeline import _map_intent
from app.services.nlu.schema import StudentIntent

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    grade_level: str = Field(default="grade_1_3", description="Target grade: grade_1_3, grade_4_6 (Grades 1-6)")
    language: str = Field(default="en", description="Preferred tutor language: en or khmer")
    problem_context: Optional[Dict[str, Any]] = Field(default=None, description="Active problem/worksheet context metadata")
    active_step: Optional[Dict[str, Any]] = Field(default=None, description="Active step metadata if within a worksheet exercise")
    worksheet_page: Optional[int] = Field(default=None, description="Worksheet page number")
    exercise_id: Optional[str] = Field(default=None, description="ID of the current exercise")


class QueryResponse(BaseModel):
    category: str
    solution: str                          # Formatted Markdown or Socratic card response
    steps: List[Dict[str, Any]]
    source: str
    current_step_index: int
    hint_count: int
    practice_mode: bool
    grade_level: str
    session_id: str
    language: str
    # Part 1 Stepper Widget payload & dual-mode response fields
    step_widget: Optional[Dict[str, Any]] = None
    formatted_markdown: Optional[str] = None
    is_problem_complete: bool = False
    is_deflected: bool = False
    # Pipeline trace for question projection observability
    pipeline_trace: Optional[Dict[str, Any]] = None
    suggested_chips: Optional[List[str]] = None
    degrade_to_tap_first: Optional[bool] = None


class NavigateRequest(BaseModel):
    session_id: str
    target_step_index: Optional[int] = Field(default=None, description="0-indexed target step number (0, 1, 2...)")
    step_number: Optional[int] = Field(default=None, description="1-indexed target step number for clicking dots (1, 2, 3...)")
    direction: Optional[str] = Field(default=None, description="Relative step movement: 'next', 'back', or 'prev'")


class StepAnswerRequest(BaseModel):
    session_id: str
    step_number: int = Field(..., description="1-indexed step number")
    student_answer: str = Field(..., description="Student input text or numeral")
    is_correct: Optional[bool] = Field(default=None, description="Optional pre-evaluated correctness flag")


class TranslateRequest(BaseModel):
    text: Optional[str] = None
    texts: Optional[List[str]] = None
    target_language: Optional[str] = None
    target_lang: Optional[str] = None

    def get_target_lang(self) -> str:
        lang = self.target_lang or self.target_language or "km"
        return "km" if lang.lower().strip() in ("km", "khmer") else "en"


class TranslateResponse(BaseModel):
    translated_text: Optional[str] = None
    translated_texts: Optional[List[str]] = None
    target_language: str = "km"
    target_lang: str = "km"


_TRANSLATION_CACHE_LIMIT = 512
_translation_cache: "OrderedDict[str, str]" = OrderedDict()


async def translate_to_khmer(text: str) -> str:
    """
    Translates English tutor response to Khmer using LLM Service, preserving LaTeX math.
    Uses in-memory caching to avoid redundant API calls.
    """
    if not getattr(settings, "ENABLE_KHMER_LANGUAGE", False):
        return text

    if not text or not text.strip():
        return text
    
    cached = _translation_cache.get(text.strip())
    if cached:
        _translation_cache.move_to_end(text.strip())
        return cached

    try:
        prompt = prompt_controller.get_translation_to_khmer_prompt(text)
        resp = await llm_service.generate_text_async(prompt, model_tier=ModelTier.TRANSLATION)
        translated = resp.text.strip()
        # Reject mock LLM test artifacts and return the original text
        if (
            getattr(resp, "provider", "") == "mock"
            or not translated
            or "mock llm" in translated.lower()
            or translated == "Mock LLM generated response."
        ):
            logger.info("translate_to_khmer: received mock LLM response, keeping original text.")
            return text

        if translated:
            cache_key = text.strip()
            _translation_cache[cache_key] = translated
            _translation_cache.move_to_end(cache_key)
            while len(_translation_cache) > _TRANSLATION_CACHE_LIMIT:
                _translation_cache.popitem(last=False)
            return translated
        return text
    except Exception as e:
        logger.warning(f"Failed to translate response to Khmer: {e}")
        return text


_TRANSLATE_CACHE: Dict[str, str] = {}


@router.post("/translate", response_model=TranslateResponse)
async def handle_translate(request: TranslateRequest):
    """
    Direct endpoint for translating arbitrary UI, problem, or step strings to Khmer or English.
    Supports single text or batch texts with caching and prompt-controller LLM integration.
    """
    if not getattr(settings, "ENABLE_KHMER_LANGUAGE", False):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Khmer translation is deferred to ReanMore v2.2. English-first mode is active."
        )

    target = request.get_target_lang()
    source = request.source_lang or ("km" if target == "en" else "en")

    async def _do_translate(text: str) -> str:
        if not text or not text.strip():
            return ""
        cache_key = f"{target}:{text.strip()}"
        if cache_key in _TRANSLATE_CACHE:
            return _TRANSLATE_CACHE[cache_key]

        sys_inst, prompt = prompt_controller.get_translation_prompt(
            text=text.strip(),
            target_lang=target,
            source_lang=source
        )
        try:
            response = await llm_service.generate_text_async(
                prompt=prompt,
                system_instruction=sys_inst,
                temperature=0.1,
                max_tokens=500,
                model_tier=ModelTier.FAST
            )
            translated = response.text.strip()
            if (
                translated
                and getattr(response, "provider", "") != "mock"
                and "mock llm" not in translated.lower()
                and translated != "Mock LLM generated response."
            ):
                _TRANSLATE_CACHE[cache_key] = translated
                return translated
        except Exception as e:
            logger.warning(f"Translation LLM call failed: {e}")

        # Fallback to translate_to_khmer if target is km, else return original text
        if target == "km":
            return await translate_to_khmer(text)
        return text

    if request.text:
        translated = await _do_translate(request.text)
        return TranslateResponse(translated_text=translated, target_language=target, target_lang=target, source_lang=source)
    elif request.texts:
        results = [await _do_translate(t) for t in request.texts]
        return TranslateResponse(translated_texts=results, target_language=target, target_lang=target, source_lang=source)

    return TranslateResponse(
        translated_text=request.text,
        translated_texts=request.texts,
        target_language=target,
        target_lang=target,
        source_lang=source
    )



@router.post("/query", response_model=QueryResponse)
async def handle_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
):
    raw_query = request.query.strip()
    session_id = request.session_id or str(uuid.uuid4())
    req_lang = request.language.lower().strip()
    language = "khmer" if req_lang in ["km", "khmer"] else "en"
        
    config = {"configurable": {"thread_id": session_id}}
    start_time = time.time()

    # 1. Load context state from SessionManager (Redis / Local fallback)
    session = session_manager.get_or_create_session(session_id)
    if current_user:
        session.user_id = current_user.get("user_id")
        session.student_name = current_user.get("student_name")
        session.role = current_user.get("role", "student")
        session.class_code = current_user.get("class_code")

    prev_hint_count = session.hint_count
    prev_step_index = session.current_step_index

    try:
        # Check active checkpoint in Socratic StateGraph
        state_snapshot = socratic_graph.get_state(config)
        has_active_state = bool(state_snapshot and state_snapshot.values and state_snapshot.values.get("step_widget"))
        
        # Re-hydrate LangGraph checkpointer if empty but session has saved step_widget
        if not has_active_state and session.step_widget:
            socratic_graph.update_state(config, {
                "session_id": session_id,
                "step_widget": session.step_widget,
                "current_step_index": session.current_step_index,
                "problem_text": session.original_query,
                "grade_level": session.grade_level,
                "subject": session.subject or "math",
                "is_problem_complete": session.is_problem_complete,
            })
            state_snapshot = socratic_graph.get_state(config)
            has_active_state = bool(state_snapshot and state_snapshot.values and state_snapshot.values.get("step_widget"))

        active_step_dict: Optional[Dict[str, Any]] = None
        if has_active_state and state_snapshot and state_snapshot.values:
            sw = state_snapshot.values.get("step_widget", {})
            steps = sw.get("steps", [])
            curr_idx = state_snapshot.values.get("current_step_index", 0)
            if 0 <= curr_idx < len(steps):
                active_step_dict = steps[curr_idx]

        # Integrate request problem_context / active_step if provided from frontend
        p_ctx = request.problem_context or {}
        if not active_step_dict and request.active_step:
            active_step_dict = request.active_step

        ctx_statement = p_ctx.get("statementEng") or p_ctx.get("statementKhmer") or p_ctx.get("titleEng") or ""
        ctx_step_q = (active_step_dict or {}).get("questionEng") or (active_step_dict or {}).get("questionKhmer") or p_ctx.get("currentStepQuestion") or ""

        # Detect if this is an English language / literacy exercise:
        p_subj = str(p_ctx.get("subject", "")).lower()
        p_title = str(p_ctx.get("titleEng", "")).lower()
        is_english_exercise = (
            p_subj == "english"
            or (active_step_dict and str(active_step_dict.get("subject", "")).lower() == "english")
            or bool(re.search(r'\b(?:english|vocabulary|spelling|grammar|phonics|reading)\b', f"{ctx_statement} {p_title}", re.I))
        )
        if is_english_exercise:
            language = "en"

        # 2. Pipeline Stage 1 & 2: Normalize
        normalized_query = normalize_query(raw_query)

        # Check if incoming query is a standalone arithmetic calculation (e.g. '4 + 5 =', 'what 2+2') or explicit solve request
        is_fraction_literal = bool(re.match(r'^\s*-?\d+/\d+\s*$', normalized_query))
        math_candidate = strip_arithmetic_wrappers(normalized_query)
        has_binary_math = not is_fraction_literal and bool(re.search(r'^\s*\d+(?:\.\d+)?(?:\s*[\+\-\*\/xX×÷]\s*\d+(?:\.\d+)?)+(?:\s*=\s*\??)?\s*$', math_candidate))
        expected_ans_str = str(active_step_dict.get("expected_answer") or "").strip() if active_step_dict else ""
        is_step_ans_match = bool(expected_ans_str and normalized_query.strip() == expected_ans_str)
        is_explicit_solve = bool(re.match(
            r"^(?:solve|calculate|compute|"
            r"what(?:['’]?s|\s+is|\s+are)?(?=\s*\d)|whats(?=\s*\d)|"
            r"how\s+much\s+is\s+\d+|how\s+many\s+is\s+\d+|"
            r"find\s+the\s+(?:sum|difference)|new\s+problem|another\s+problem)",
            normalized_query, re.I
        ))
        is_standalone_new_math = has_binary_math and not is_step_ans_match

        # If query is an unambiguous new problem, override and reset active state
        if is_standalone_new_math or is_explicit_solve:
            has_active_state = False
            active_step_dict = None
            ctx_statement = None
        elif not has_active_state and (active_step_dict or (ctx_statement and p_ctx.get("activeStepIndex", 0) > 0)):
            has_active_state = True

        # Phase 1: Quota Check (Only for fresh problem plans; free for active problem steps/hints)
        user_id = session.user_id or (current_user.get("user_id") if current_user else None) or "anonymous_student"
        user_role = session.role or (current_user.get("role") if current_user else None) or "student"
        
        # 1 Page = 1 Quota deduction on worksheet scan confirmation (or exercise_id or session_id)
        if request.worksheet_page:
            quota_problem_id = f"{session_id}_page_{request.worksheet_page}"
        elif request.exercise_id:
            quota_problem_id = request.exercise_id
        else:
            quota_problem_id = session_id

        is_new_problem_plan = not has_active_state

        if is_new_problem_plan:
            quota_check = await quota_guard.check_quota(
                user_id=user_id,
                role=user_role,
                problem_id=quota_problem_id,
            )
            if not quota_check.allowed:
                raise QuotaExhaustedException(quota_check)

        # 3. Pipeline Stage 3: Rewrite if needed (resolve pronouns/elliptical references)
        prev_q = session.turns[-1].get("user") if session.turns else None
        rewritten_query, rewrite_needed, rewrite_note = resolve_query_rewrite(
            query=raw_query,
            normalized_query=normalized_query,
            active_step=active_step_dict,
            previous_query=prev_q,
            history=session.turns,
            has_active_problem=has_active_state or bool(ctx_statement)
        )

        # Detect domain subject and granular subtopic
        effective_query_for_subject = f"{ctx_statement} {normalized_query}".strip() if ctx_statement else normalized_query
        route_res = route_subject_heuristic(effective_query_for_subject)
        detected_subject = route_res.subject.value
        detected_subtopic = route_res.subtopic

        # 4. Classify intent via heuristic NLU engine
        intent_res = classify_intent_heuristic(
            query=normalized_query,
            history=session.turns,
            current_step=active_step_dict
        )

        # Auto-detect grade level from problem context or query text
        detected_grade_str = request.grade_level
        combined_text = f"{raw_query} {ctx_statement} {p_ctx.get('titleKhmer', '')} {p_ctx.get('titleEng', '')}"
        km_g_match = re.search(r'ថ្នាក់ទី\s*([១-៦1-6])', combined_text)
        en_g_match = re.search(r'grade\s*([1-6])', combined_text, re.I)

        detected_num = None
        if p_ctx.get("grade"):
            try:
                detected_num = int(p_ctx["grade"])
            except Exception:
                pass
        elif km_g_match:
            km_map = {'១': 1, '២': 2, '៣': 3, '៤': 4, '៥': 5, '៦': 6}
            val = km_g_match.group(1)
            detected_num = km_map.get(val, int(val) if val.isdigit() else 4)
        elif en_g_match:
            detected_num = int(en_g_match.group(1))

        if detected_num:
            if detected_num <= 2:
                detected_grade_str = "grade_1_2"
            elif detected_num <= 4:
                detected_grade_str = "grade_3_4"
            else:
                detected_grade_str = "grade_5_6"

        group_name, grade_guide = prompt_controller._get_grade_info(detected_grade_str)

        state_input: Dict[str, Any] = {
            "session_id": session_id,
            "raw_user_input": raw_query,
            "student_attempt": raw_query,
            "grade_level": detected_grade_str,
            "subject": detected_subject,
            "subtopic": detected_subtopic,
        }

        # Context-aware explanation handling for active exercise page
        is_explain_query = bool(re.search(r'\b(?:explain|help|tell\s+me|how\s+to|what\s+is\s+this|confused|dont\s+understand|don\'t\s+understand)\b', raw_query, re.I))
        if is_explain_query and (ctx_statement or ctx_step_q):
            try:
                sys_inst, explain_prompt = prompt_controller.get_contextual_explanation_prompt(
                    query=raw_query,
                    exercise_context=ctx_statement or p_ctx.get("titleEng", "Science & Math"),
                    current_step_question=ctx_step_q,
                    grade_level=detected_grade_str
                )
                explain_resp = await llm_service.generate_text_async(
                    prompt=explain_prompt,
                    system_instruction=sys_inst,
                    temperature=0.3,
                    max_tokens=300,
                    model_tier=ModelTier.FAST
                )
                if explain_resp and explain_resp.text:
                    solution_text = explain_resp.text.strip()
                    if language == "khmer" and getattr(settings, "ENABLE_KHMER_LANGUAGE", False):
                        solution_text = await translate_to_khmer(solution_text)
                    return QueryResponse(
                        category=detected_subject,
                        solution=solution_text,
                        steps=[],
                        source="ReanMore Contextual Tutor",
                        current_step_index=p_ctx.get("activeStepIndex", 0),
                        hint_count=0,
                        practice_mode=False,
                        grade_level=request.grade_level,
                        session_id=session_id,
                        language=language,
                        step_widget=None,
                        formatted_markdown=solution_text,
                        is_problem_complete=False,
                        is_deflected=False
                    )
            except Exception as e:
                logger.warning(f"Contextual explanation generation failed: {e}")

        # Route according to classified intent
        is_new_problem_intent = (
            intent_res.intent in (IntentType.INITIAL_SOLVE, IntentType.REQUEST_PRACTICE)
            or is_standalone_new_math
            or is_explicit_solve
        ) and (intent_res.intent not in (IntentType.CHITCHAT, IntentType.OFF_TOPIC, IntentType.CLARIFY))

        if not has_active_state or is_new_problem_intent:
            if intent_res.intent == IntentType.CHITCHAT:
                state_input["detected_intent"] = "CHITCHAT"
            elif intent_res.intent == IntentType.OFF_TOPIC:
                state_input["detected_intent"] = "OFF_TOPIC_DEFLECTED"
            elif intent_res.intent == IntentType.CLARIFY:
                state_input["detected_intent"] = "CLARIFY"
            else:
                effective_problem_text = normalized_query if is_new_problem_intent else (ctx_statement or (rewritten_query if rewrite_needed else normalized_query))
                state_input["problem_text"] = effective_problem_text
                state_input["detected_intent"] = StudentIntent.INITIAL_QUESTION.value
                state_input["current_step_index"] = 0
                state_input["step_widget"] = None
        else:
            if intent_res.intent == IntentType.CHITCHAT:
                state_input["detected_intent"] = "CHITCHAT"
            elif intent_res.intent == IntentType.OFF_TOPIC:
                state_input["detected_intent"] = "OFF_TOPIC_DEFLECTED"
            elif intent_res.intent == IntentType.CLARIFY:
                state_input["detected_intent"] = "CLARIFY"
            elif intent_res.intent == IntentType.STEP_ATTEMPT:
                state_input["detected_intent"] = StudentIntent.STEP_ANSWER_ATTEMPT.value
                state_input["student_attempt"] = intent_res.extracted_answer or raw_query
            else:
                state_input["detected_intent"] = StudentIntent.STEP_ANSWER_ATTEMPT.value
                state_input["student_attempt"] = intent_res.extracted_answer or raw_query

        # 5. Invoke Socratic Graph asynchronously
        res = await socratic_graph.ainvoke(state_input, config=config)

        # 5. Extract results
        widget_dict = res.get("step_widget")
        formatted_md = res.get("formatted_markdown", "")
        feedback_msg = res.get("feedback_message", "")
        solution_text = formatted_md or feedback_msg
        current_step_idx = res.get("current_step_index", 0)
        current_hint_tier = res.get("current_hint_tier", 0)
        is_complete = bool(res.get("is_problem_complete") or res.get("is_problem_solved"))
        is_deflected = bool(res.get("is_deflected", False))
        subject = res.get("subject", detected_subject)
        subtopic = res.get("subtopic", detected_subtopic)
        intent = res.get("detected_intent", "INITIAL_QUESTION" if (not has_active_state or is_new_problem_intent) else "STEP_ANSWER_ATTEMPT")

        # Translate to Khmer if requested
        if language == "khmer" and getattr(settings, "ENABLE_KHMER_LANGUAGE", False):
            if solution_text:
                logger.info("Endpoints: Translating final Socratic response back to Khmer...")
                solution_text = await translate_to_khmer(solution_text)
            if widget_dict and "steps" in widget_dict:
                logger.info("Endpoints: Translating step widget cards to Khmer in parallel...")
                tasks = []
                targets = []
                for s in widget_dict["steps"]:
                    for field in ["title", "mission", "clue", "helpful_example", "your_turn"]:
                        val = s.get(field)
                        if val:
                            tasks.append(translate_to_khmer(val))
                            targets.append((s, field, None))
                    if s.get("hints") and isinstance(s["hints"], list):
                        for h_idx, h in enumerate(s["hints"]):
                            if h:
                                tasks.append(translate_to_khmer(h))
                                targets.append((s, "hints", h_idx))
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for (step_obj, field, h_idx), res_text in zip(targets, results):
                        if (
                            isinstance(res_text, str)
                            and res_text
                            and "mock llm" not in res_text.lower()
                            and res_text != "Mock LLM generated response."
                        ):
                            if field == "hints" and h_idx is not None:
                                step_obj["hints"][h_idx] = res_text
                            else:
                                step_obj[field] = res_text

        # Build legacy step representations for backwards compatibility
        steps_list: List[Dict[str, Any]] = []
        if widget_dict and "steps" in widget_dict:
            for s in widget_dict["steps"]:
                steps_list.append({
                    "step_number": s.get("step_number"),
                    "title": s.get("title"),
                    "mission": s.get("mission"),
                    "clue": s.get("clue"),
                    "status": s.get("status")
                })

        # 6. Pipeline Stage 4: Route to Microservice / Subsystem
        target_service, service_endpoint, routing_reason = determine_routing(
            subject=subject,
            subtopic=subtopic,
            intent=intent,
            is_deflected=is_deflected,
            is_safe=res.get("is_safe", True)
        )

        # 7. Pipeline Stage 5: Summarize Results & Build Tidy Log Projection
        result_summary = summarize_results(
            widget_dict=widget_dict,
            current_step_idx=current_step_idx,
            current_hint_tier=current_hint_tier,
            is_complete=is_complete,
            is_deflected=is_deflected,
            feedback_message=feedback_msg or solution_text
        )

        processing_time_ms = (time.time() - start_time) * 1000

        pipeline_trace = PipelineTrace(
            session_id=session_id,
            grade_level=request.grade_level,
            raw_query=raw_query,
            normalized_query=normalized_query,
            rewrite_needed=rewrite_needed,
            rewritten_query=rewritten_query,
            rewrite_note=rewrite_note,
            subject=subject,
            subtopic=subtopic,
            intent=intent,
            target_service=target_service,
            service_endpoint=service_endpoint,
            routing_reason=routing_reason,
            result_summary=result_summary,
            is_deflected=is_deflected,
            is_problem_complete=is_complete,
            latency_ms=round(processing_time_ms, 2),
            status="DEFLECTED" if is_deflected else ("BLOCKED" if res.get("is_safe") is False else "SUCCESS")
        )

        # Print tidy structured projection box to logs
        try:
            logger.info("\n" + format_tidy_pipeline_log(pipeline_trace))
        except Exception:
            pass

        # 8. Update session context
        session.subject = subject
        session.grade_level = request.grade_level
        session.language = language
        session.current_step_index = current_step_idx
        session.hint_count = current_hint_tier
        session.tutor_feedback = solution_text
        session.formatted_markdown = solution_text
        session.is_problem_complete = is_complete

        # Phase 2: Quota Commit (Deducts 1 quota point only upon successful problem plan creation)
        if is_new_problem_plan and widget_dict and widget_dict.get("steps") and not is_deflected and res.get("is_safe") is not False:
            commit_res = await quota_guard.commit_quota(
                user_id=user_id,
                problem_id=quota_problem_id,
                problem_hash=None,
                subject=subject or "math",
                tokens_consumed=0,
                role=user_role,
            )
            widget_dict["quota_remaining"] = {
                "daily": commit_res.daily_remaining,
                "monthly": commit_res.monthly_remaining,
            }
        elif widget_dict:
            # For free interactions (hints, answer validations, steps), populate current quota remaining
            now_phnom = quota_guard.get_phnom_penh_now()
            d_str, m_str = quota_guard.get_date_keys(now_phnom)
            d_used, m_used = quota_guard._get_current_usage(user_id, d_str, m_str)
            widget_dict["quota_remaining"] = {
                "daily": max(0, settings.QUOTA_DAILY - d_used),
                "monthly": max(0, settings.QUOTA_MONTHLY - m_used),
            }

        if widget_dict:
            session.set_step_widget(widget_dict)
        session.add_turn(user_input=raw_query, bot_response=solution_text)

        # 9. Background PostgreSQL telemetry saving
        background_tasks.add_task(
            save_session_and_telemetry,
            session_id=session_id,
            subject=subject,
            grade_level=request.grade_level,
            language=language,
            original_raw_query=raw_query,
            solved_steps=steps_list,
            practice_mode=False,
            user_query=raw_query,
            tutor_response=solution_text,
            step_index=current_step_idx,
            hint_count=current_hint_tier,
            is_mistake=(current_hint_tier > prev_hint_count),
            processing_time_ms=processing_time_ms,
            metadata_json={
                "prev_step_index": prev_step_index,
                "prev_hint_count": prev_hint_count,
                "is_complete": is_complete,
                "is_deflected": is_deflected,
                "pipeline_trace": pipeline_trace.to_dict()
            },
            worksheet_data=getattr(session, "worksheet_data", None),
            image_uri=getattr(session, "image_uri", None),
            session_title=getattr(session, "session_title", None),
            session_title_khmer=getattr(session, "session_title_khmer", None),
            user_id=session.user_id,
        )

        return QueryResponse(
            category=subject,
            solution=solution_text,
            steps=steps_list,
            source="Orchestrator Socratic Tutor",
            current_step_index=current_step_idx,
            hint_count=current_hint_tier,
            practice_mode=False,
            grade_level=request.grade_level,
            session_id=session_id,
            language=language,
            step_widget=widget_dict,
            formatted_markdown=solution_text,
            is_problem_complete=is_complete,
            is_deflected=is_deflected,
            pipeline_trace=pipeline_trace.to_dict(),
            suggested_chips=res.get("suggested_chips"),
            degrade_to_tap_first=res.get("degrade_to_tap_first", False)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing Socratic Graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Socratic loop execution error: {str(e)}")


@router.post("/step/navigate")
async def navigate_step(request: NavigateRequest):
    """
    Jumps directly to a target step index in the active Stepper Widget.
    Supports:
    - 0-indexed: target_step_index (0, 1, 2)
    - 1-indexed dot clicks: step_number (1, 2, 3)
    - Directional navigation: direction ('next', 'back', 'prev')
    """
    config = {"configurable": {"thread_id": request.session_id}}
    session = session_manager.get_or_create_session(request.session_id)

    # 1. Retrieve or re-hydrate widget state
    state_snapshot = socratic_graph.get_state(config)
    has_active_state = bool(state_snapshot and state_snapshot.values and state_snapshot.values.get("step_widget"))

    if not has_active_state and session.step_widget:
        socratic_graph.update_state(config, {
            "session_id": request.session_id,
            "step_widget": session.step_widget,
            "current_step_index": session.current_step_index,
            "grade_level": session.grade_level,
            "subject": session.subject or "math",
            "is_problem_complete": session.is_problem_complete,
        })
        state_snapshot = socratic_graph.get_state(config)
        has_active_state = True

    widget_dict = None
    if has_active_state and state_snapshot and state_snapshot.values:
        widget_dict = state_snapshot.values.get("step_widget")
    elif session.step_widget:
        widget_dict = session.step_widget

    if not widget_dict or "steps" not in widget_dict or not widget_dict["steps"]:
        raise HTTPException(status_code=400, detail="No active problem session found to navigate.")

    total_steps = widget_dict.get("total_steps", len(widget_dict["steps"]))
    current_idx = widget_dict.get("current_step_index", session.current_step_index)

    # 2. Determine target 0-indexed step from request
    target_idx: Optional[int] = None
    if request.target_step_index is not None:
        target_idx = request.target_step_index
    elif request.step_number is not None:
        target_idx = request.step_number - 1  # Convert 1-indexed dot click to 0-indexed
    elif request.direction is not None:
        dir_clean = request.direction.lower().strip()
        if dir_clean == "next":
            target_idx = current_idx + 1
        elif dir_clean in ("back", "prev", "previous"):
            target_idx = current_idx - 1
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid direction '{request.direction}'. Use 'next' or 'back'."
            )
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide target_step_index (0-indexed), step_number (1-indexed), or direction ('next'/'back')."
        )

    # 3. Boundary validation
    if target_idx < 0 or target_idx >= total_steps:
        raise HTTPException(
            status_code=400,
            detail=f"Target step {target_idx} is out of bounds (Problem has {total_steps} steps, valid indices 0 to {total_steps - 1})."
        )

    # 4. Invoke graph navigation
    state_input = {
        "session_id": request.session_id,
        "raw_user_input": f"jump {target_idx + 1}",
        "target_nav_index": target_idx,
        "detected_intent": "NAVIGATION_JUMP"
    }

    try:
        res = await socratic_graph.ainvoke(state_input, config=config)
        updated_widget = res.get("step_widget")
        res_idx = res.get("current_step_index", target_idx)
        formatted_md = res.get("formatted_markdown")
        feedback = res.get("feedback_message")

        # 5. Persist updated step in SessionManager
        session.current_step_index = res_idx
        if formatted_md:
            session.formatted_markdown = formatted_md
        if updated_widget:
            session.set_step_widget(updated_widget)
        else:
            session._trigger_change()

        active_step_obj = None
        if updated_widget and "steps" in updated_widget and 0 <= res_idx < len(updated_widget["steps"]):
            active_step_obj = updated_widget["steps"][res_idx]

        return {
            "session_id": request.session_id,
            "current_step_index": res_idx,
            "step_widget": updated_widget,
            "active_step": active_step_obj,
            "formatted_markdown": formatted_md,
            "feedback_message": feedback
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error navigating step: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Navigation error: {str(e)}")


@router.post("/step/answer")
async def submit_step_answer(request: StepAnswerRequest):
    """
    Records and deterministically validates an inline student answer for a specific step.
    Updates session stepper widget state without incurring an expensive LLM round-trip.
    """
    config = {"configurable": {"thread_id": request.session_id}}
    session = session_manager.get_or_create_session(request.session_id)

    # Re-hydrate state if needed
    state_snapshot = socratic_graph.get_state(config)
    has_active_state = bool(state_snapshot and state_snapshot.values and state_snapshot.values.get("step_widget"))

    widget_dict = None
    if has_active_state and state_snapshot and state_snapshot.values:
        widget_dict = state_snapshot.values.get("step_widget")
    elif session.step_widget:
        widget_dict = session.step_widget

    if not widget_dict or "steps" not in widget_dict or not widget_dict["steps"]:
        logger.info(f"submit_step_answer: session {request.session_id} has no widget steps; returning answer ack.")
        return {
            "session_id": request.session_id,
            "step_number": request.step_number,
            "student_answer": request.student_answer,
            "is_correct": request.is_correct if request.is_correct is not None else False,
            "is_problem_complete": False,
            "step_widget": None
        }

    step_idx = request.step_number - 1
    total_steps = len(widget_dict["steps"])

    if 0 <= step_idx < len(widget_dict["steps"]):
        target_step = widget_dict["steps"][step_idx]
        expected_ans = target_step.get("expected_answer")
        if request.is_correct is not None:
            is_correct = request.is_correct
        else:
            is_correct = bool(
                expected_ans is not None
                and str(expected_ans).strip()
                and _is_answer_equivalent(
                    request.student_answer,
                    str(expected_ans),
                    target_step.get("acceptable_answers"),
                )
            )

        target_step["student_answer"] = request.student_answer
        target_step["status"] = "completed" if is_correct else "in_progress"

        completed_steps = [
            index for index in widget_dict.get("completed_steps", [])
            if isinstance(index, int) and 0 <= index < total_steps
        ]
        if is_correct and step_idx not in completed_steps:
            completed_steps.append(step_idx)
            widget_dict["completed_steps"] = completed_steps

        is_all_complete = len(completed_steps) >= total_steps
        widget_dict["is_problem_complete"] = is_all_complete
        session.is_problem_complete = is_all_complete
        session.set_step_widget(widget_dict)

        try:
            socratic_graph.update_state(config, {
                "step_widget": widget_dict,
                "is_problem_complete": is_all_complete,
            })
        except Exception as e:
            logger.warning(f"Could not update graph state for answer: {e}")

        logger.info(f"Recorded step {request.step_number} answer for session {request.session_id}: correct={is_correct}")

        return {
            "session_id": request.session_id,
            "step_number": request.step_number,
            "student_answer": request.student_answer,
            "is_correct": is_correct,
            "is_problem_complete": is_all_complete,
            "step_widget": widget_dict
        }

    raise HTTPException(
        status_code=400,
        detail=f"Step {request.step_number} is out of bounds (valid steps: 1-{total_steps}).",
    )


class StepValidateRequest(BaseModel):
    student_answer: str
    expected_answer: str
    step_number: Optional[int] = 1
    language: Optional[str] = "km"
    hints: Optional[List[str]] = None


@router.post("/step/validate")
async def fast_validate_answer_endpoint(request: StepValidateRequest):
    """
    Ultra-fast (< 5ms) deterministic answer evaluation for inline math and science steps.
    Routes through validate_student_answer as the single validation path, guaranteeing
    non-directional near-miss feedback and invariant-backed evaluation.
    """
    outcome = validate_student_answer(
        student_attempt=request.student_answer,
        expected_answer=request.expected_answer,
        step_id=str(request.step_number) if request.step_number else None,
    )

    is_km = request.language == "km"
    is_correct = outcome.is_correct
    near_miss = outcome.is_near_miss
    diff = outcome.numeric_diff

    # Non-directional standardized feedback
    msg_km = outcome.feedback_khmer
    msg_en = outcome.feedback_eng

    return {
        "is_correct": is_correct,
        "near_miss": near_miss,
        "difference": diff,
        "feedback_khmer": msg_km,
        "feedback_eng": msg_en,
        "feedback": msg_km if is_km else msg_en,
    }


class SessionSyncRequest(BaseModel):
    session_id: str
    subject: Optional[str] = None
    grade_level: str = "grade_1_3"
    language: str = "km"
    title: Optional[str] = None
    title_khmer: Optional[str] = None
    image_uri: Optional[str] = None
    worksheet_queue: Optional[Dict[str, Any]] = None
    problem_step_progress: Optional[Dict[str, Any]] = None
    step_widget: Optional[Dict[str, Any]] = None
    current_step_index: Optional[int] = 0
    messages: Optional[List[Dict[str, Any]]] = None
    is_problem_complete: Optional[bool] = False


@router.get("/sessions")
async def get_all_sessions(limit: int = 50):
    """
    Retrieves a list of recent Socratic and multi-exercise worksheet sessions from PostgreSQL DB.
    """
    try:
        db_logs = await get_all_session_logs(limit=limit)
        return {"sessions": db_logs, "total": len(db_logs)}
    except Exception as e:
        logger.error(f"Error fetching session logs from DB: {e}", exc_info=True)
        return {"sessions": [], "total": 0, "error": str(e)}


@router.get("/stats")
@router.get("/streak")
async def get_student_stats(current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)):
    """
    Retrieves dynamic student learning streak, total XP, and activity metrics computed from PostgreSQL database.
    """
    try:
        stats = await get_student_telemetry_stats()
        return stats
    except Exception as e:
        logger.error(f"Error computing student stats: {e}", exc_info=True)
        return {
            "available": False,
            "current_streak": 0,
            "best_streak": 0,
            "total_xp": 0,
            "total_sessions": 0,
            "total_turns": 0,
            "has_studied_today": False,
            "error": str(e)
        }


@router.post("/session/sync")
async def sync_session(
    request: SessionSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict[str, Any]] = Depends(get_optional_user),
):
    """
    Synchronizes full session state (including multi-exercise worksheet queues, titles, problem step progress, and step widgets)
    to both Redis / local memory and PostgreSQL database.
    Does not persist empty/blank chats that have no user text, no worksheet, and no image.
    """
    try:
        # Check if this session has any meaningful user activity (user message, worksheet problems, image)
        has_user_msgs = any(m.get("sender") == "user" for m in (request.messages or []))
        has_ws = bool(request.worksheet_queue and request.worksheet_queue.get("problems"))
        has_img = bool(request.image_uri)

        session = session_manager.get_or_create_session(request.session_id)
        if current_user:
            session.user_id = current_user.get("user_id")
            session.student_name = current_user.get("student_name")
            session.role = current_user.get("role", "student")
            session.class_code = current_user.get("class_code")

        if request.subject:
            session.subject = request.subject
        session.grade_level = request.grade_level
        session.language = "khmer" if request.language in ("km", "khmer") else "en"
        if request.title:
            session.session_title = request.title
        if request.title_khmer:
            session.session_title_khmer = request.title_khmer
        if request.image_uri:
            session.image_uri = request.image_uri
        if request.worksheet_queue is not None:
            session.worksheet_data = request.worksheet_queue
            if request.problem_step_progress is not None:
                session.worksheet_data["problem_step_progress"] = request.problem_step_progress
        elif request.problem_step_progress is not None:
            if session.worksheet_data is None:
                session.worksheet_data = {}
            session.worksheet_data["problem_step_progress"] = request.problem_step_progress
        if request.step_widget is not None:
            session.set_step_widget(request.step_widget)
        if request.current_step_index is not None:
            session.current_step_index = request.current_step_index
        if request.is_problem_complete is not None:
            session.is_problem_complete = request.is_problem_complete

        # Trigger Redis / memory save
        session._trigger_change()

        # Only persist to Postgres if there is actual content/interaction
        if has_user_msgs or has_ws or has_img:
            background_tasks.add_task(
                save_worksheet_session_to_db,
                session_id=request.session_id,
                subject=session.subject,
                grade_level=request.grade_level,
                language=session.language,
                session_title=request.title or session.session_title,
                session_title_khmer=request.title_khmer or session.session_title_khmer,
                worksheet_data=session.worksheet_data,
                image_uri=request.image_uri or session.image_uri,
                user_id=session.user_id,
            )

        return {
            "session_id": request.session_id,
            "status": "synced" if (has_user_msgs or has_ws or has_img) else "in_memory_only",
            "is_worksheet": bool(session.worksheet_data and session.worksheet_data.get("problems")),
            "exercise_count": len(session.worksheet_data.get("problems", [])) if (session.worksheet_data and "problems" in session.worksheet_data) else 1
        }
    except Exception as e:
        logger.error(f"Error syncing session {request.session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Session sync error: {str(e)}")


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """
    Retrieves the active Stepper Widget, active step card, worksheet queue, and conversation state for a given session.
    Checks SessionManager (Redis / in-memory cache) and re-hydrates LangGraph checkpoint.
    """
    config = {"configurable": {"thread_id": session_id}}
    try:
        session = session_manager.get_session(session_id)
        state_snapshot = socratic_graph.get_state(config)
        graph_widget = state_snapshot.values.get("step_widget") if (state_snapshot and state_snapshot.values) else None

        effective_widget = None
        current_step_idx = 0
        formatted_md = None
        is_complete = False
        grade_level = "grade_1_3"
        subject = "general"
        turns = []
        rolling_summary = ""
        total_turns = 0
        worksheet_data = None
        image_uri = None
        session_title = None
        session_title_khmer = None

        if session:
            effective_widget = session.step_widget
            current_step_idx = session.current_step_index
            formatted_md = session.formatted_markdown
            is_complete = session.is_problem_complete
            grade_level = session.grade_level
            subject = session.subject or "general"
            turns = session.turns
            rolling_summary = session.rolling_summary
            total_turns = session.total_turns_count
            worksheet_data = session.worksheet_data
            image_uri = session.image_uri
            session_title = session.session_title
            session_title_khmer = session.session_title_khmer

        if not effective_widget and graph_widget:
            effective_widget = graph_widget
            vals = state_snapshot.values
            current_step_idx = vals.get("current_step_index", 0)
            formatted_md = vals.get("formatted_markdown")
            is_complete = bool(vals.get("is_problem_complete") or vals.get("is_problem_solved"))
            grade_level = vals.get("grade_level", "grade_1_3")
            subject = vals.get("subject", "general")

        # Re-hydrate graph checkpoint if session had it but graph was empty
        if effective_widget and not graph_widget:
            socratic_graph.update_state(config, {
                "session_id": session_id,
                "step_widget": effective_widget,
                "current_step_index": current_step_idx,
                "grade_level": grade_level,
                "subject": subject,
                "is_problem_complete": is_complete,
                "formatted_markdown": formatted_md
            })

        active_step = None
        if effective_widget and "steps" in effective_widget and 0 <= current_step_idx < len(effective_widget["steps"]):
            active_step = effective_widget["steps"][current_step_idx]

        return {
            "session_id": session_id,
            "subject": subject,
            "grade_level": grade_level,
            "current_step_index": current_step_idx,
            "step_widget": effective_widget,
            "active_step": active_step,
            "formatted_markdown": formatted_md,
            "is_problem_complete": is_complete,
            "worksheet_data": worksheet_data,
            "image_uri": image_uri,
            "session_title": session_title,
            "session_title_khmer": session_title_khmer,
            "turns": turns,
            "rolling_summary": rolling_summary,
            "total_turns_count": total_turns,
            "message": "No active Socratic problem in this session." if not effective_widget else None
        }
    except Exception as e:
        logger.error(f"Error fetching session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Session retrieval error: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_session_endpoint(session_id: str, background_tasks: BackgroundTasks):
    """
    Deletes a session from local memory, Redis, and persistent PostgreSQL database.
    """
    deleted = session_manager.delete_session(session_id)
    background_tasks.add_task(delete_session_from_db, session_id=session_id)
    return {"session_id": session_id, "deleted": deleted}


class TranslateRequest(BaseModel):
    text: str
    target_lang: str = Field(default="km", description="Target language: 'km' (Khmer) or 'en' (English)")
    source_lang: Optional[str] = Field(default=None, description="Source language if known")


class TranslateResponse(BaseModel):
    translated_text: str
    target_lang: str
    source_lang: Optional[str] = None
    cached: bool = False


@router.get("/system-prompt")
def get_system_prompt_endpoint(request: Request, grade: int = 4, language: str = "km"):
    """
    Returns dynamic, age-adapted Socratic system prompt compiled from central prompt controller.
    Restricted in non-debug mode to protect tutor instructions from prompt injection and answer leakage.
    """
    admin_key = request.headers.get("X-Admin-Key")
    configured_key = getattr(settings, "ADMIN_SECRET_KEY", "dev_secret")
    if not getattr(settings, "DEBUG", True) and admin_key != configured_key:
        raise HTTPException(status_code=403, detail="Forbidden: System prompt inspection is restricted")

    prompt = prompt_controller.get_grade_adapted_system_prompt(grade=grade, language=language)
    return {"grade": grade, "language": language, "system_prompt": prompt}


