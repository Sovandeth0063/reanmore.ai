"""
File: orchestrator/app/api/endpoints.py
Description: FastAPI endpoint router exposing the /query route which executes 
             prompts through the Socratic tutoring LangGraph workflow.
             Incorporates grade-level categorization, Khmer-English pivot translation, 
             and strict Redis-based Session Context persistence.
"""

import time
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from app.infrastructure.database import save_session_and_telemetry
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from app.core.logging import logger
from app.services.graph import socratic_graph
from app.services.prompts import prompt_controller
from app.services.session import session_manager
import uuid

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    grade_level: str = Field(default="grade_10_12", description="Target grade: grade_1_3, grade_4_6, grade_7_9, grade_10_12")
    language: str = Field(default="en", description="Preferred tutor language: en or khmer")

class QueryResponse(BaseModel):
    category: str
    solution: str                      # Socratic feedback/hint
    steps: List[Dict[str, Any]]
    source: str
    current_step_index: int
    hint_count: int
    practice_mode: bool
    grade_level: str
    session_id: str
    language: str

async def translate_to_khmer(text: str) -> str:
    """
    Translates English tutor response to Khmer using Gemini, preserving LaTeX math.
    """
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = prompt_controller.get_translation_to_khmer_prompt(text)
        response = model.generate_content(prompt)
        translated = response.text.strip()
        return translated if translated else text
    except Exception as e:
        logger.error(f"Failed to translate response to Khmer: {e}")
        return text

@router.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest, background_tasks: BackgroundTasks):
    query = request.query.strip()
    session_id = request.session_id or str(uuid.uuid4())
    language = request.language.lower().strip()
    if language not in ["en", "khmer"]:
        language = "en"
        
    config = {"configurable": {"thread_id": session_id}}

    start_time = time.time()

    # 1. Load context state from Redis
    session = session_manager.get_or_create_session(session_id)
    prev_hint_count = session.hint_count
    prev_step_index = session.current_step_index

    try:
        # Check if LangGraph checkpointer has active checkpoint
        state_snapshot = socratic_graph.get_state(config)
        has_checkpoint = True if (state_snapshot and state_snapshot.values) else False
        
        if has_checkpoint:
            # Resuming session (student submitted a step attempt)
            logger.info(f"Endpoints: Resuming session {session_id} in {language} with attempt: '{query}'")
            
            history = state_snapshot.values.get("history", []) or []
            history.append({"role": "user", "content": query})
            socratic_graph.update_state(config, {
                "student_attempt": query,
                "history": history,
                "language": language
            })
            
            # Resume graph execution
            await socratic_graph.ainvoke(None, config=config)
        else:
            # Starting new session (student submitted a new query)
            logger.info(f"Endpoints: Starting new session {session_id} in {language} with query: '{query}'")
            
            initial_history = [{"role": "user", "content": query}]
            inputs = {
                "query": query,
                "session_id": session_id,
                "subject": None,
                "grade_level": request.grade_level,
                "language": language,
                "original_raw_query": query,
                "solved_steps": [],
                "current_step_index": 0,
                "student_attempt": "",
                "hint_count": 0,
                "history": initial_history,
                "practice_mode": False,
                "original_query": "",
                "tutor_feedback": ""
            }
            # Start graph execution from START node
            await socratic_graph.ainvoke(inputs, config=config)

        # 2. Retrieve the updated values after LangGraph completes execution
        final_snapshot = socratic_graph.get_state(config)
        state_values = final_snapshot.values
        
        tutor_feedback = state_values.get("tutor_feedback", "")
        
        # Translate final output back to Khmer if preferred by user
        if language == "khmer" and tutor_feedback:
            logger.info("Endpoints: Translating final Socratic response back to Khmer...")
            tutor_feedback = await translate_to_khmer(tutor_feedback)
            
        history = state_values.get("history", []) or []
        history.append({"role": "assistant", "content": tutor_feedback})
        
        # Save assistant message back to checkpoint history
        socratic_graph.update_state(config, {"history": history})

        # 3. Persist latest values back to Redis session context
        session.subject = state_values.get("subject")
        session.grade_level = state_values.get("grade_level", "grade_10_12")
        session.language = language
        session.original_raw_query = state_values.get("original_raw_query") or query
        session.solved_steps = state_values.get("solved_steps", [])
        session.current_step_index = state_values.get("current_step_index", 0)
        session.hint_count = state_values.get("hint_count", 0)
        session.practice_mode = state_values.get("practice_mode", False)
        session.original_query = state_values.get("original_query", "")
        session.tutor_feedback = tutor_feedback
        
        # Log this turn into conversation turns list (triggers Redis persistent save)
        session.add_turn(user_input=query, bot_response=tutor_feedback)

        # 4. Save session metadata and granular telemetry to PostgreSQL asynchronously
        processing_time_ms = (time.time() - start_time) * 1000
        is_mistake = session.hint_count > prev_hint_count

        background_tasks.add_task(
            save_session_and_telemetry,
            session_id=session_id,
            subject=session.subject,
            grade_level=session.grade_level,
            language=session.language,
            original_raw_query=session.original_raw_query,
            solved_steps=session.solved_steps,
            practice_mode=session.practice_mode,
            user_query=query,
            tutor_response=tutor_feedback,
            step_index=session.current_step_index,
            hint_count=session.hint_count,
            is_mistake=is_mistake,
            processing_time_ms=processing_time_ms,
            metadata_json={
                "prev_step_index": prev_step_index,
                "prev_hint_count": prev_hint_count,
                "user_intent": state_values.get("user_intent"),
                "resolved_query": state_values.get("resolved_query")
            }
        )

        return QueryResponse(
            category=session.subject or "GENERAL",
            solution=tutor_feedback,
            steps=session.solved_steps,
            source="Orchestrator Socratic Tutor",
            current_step_index=session.current_step_index,
            hint_count=session.hint_count,
            practice_mode=session.practice_mode,
            grade_level=session.grade_level,
            session_id=session_id,
            language=session.language
        )

    except Exception as e:
        logger.error(f"Error executing Socratic Graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Socratic loop execution error: {str(e)}")
