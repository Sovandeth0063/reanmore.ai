"""
File: orchestrator/app/services/session.py
Description: Redis-based Session Context persistent storage engine. Manages Socratic tutor 
             conversation turns, StepWidgetPayload persistence, streams telemetry transcripts,
             and handles rolling AI dialogue summaries.
"""

from __future__ import annotations
import os
import json
import logging
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable, Union
import redis
from app.services.socratic.prompts.controller import socratic_prompt_controller as prompt_controller

logger = logging.getLogger(__name__)


@dataclass
class SessionContext:
    session_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active_at: datetime = field(default_factory=datetime.utcnow)
    max_turns: int = 10
    total_turns_count: int = 0
    
    # State Machine Context
    subject: Optional[str] = None
    grade_level: str = "grade_1_3"
    language: str = "en"
    original_raw_query: Optional[str] = None
    
    # Socratic Tutoring Status & Stepper Widget Persistence
    solved_steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step_index: int = 0
    hint_count: int = 0
    practice_mode: bool = False
    original_query: str = ""
    tutor_feedback: str = ""
    step_widget: Optional[Dict[str, Any]] = None       # Serialized StepWidgetPayload dictionary
    formatted_markdown: Optional[str] = None          # Rendered 4-Part card or overview markdown
    is_problem_complete: bool = False
    
    # Conversational Memory & Rolling Summary
    turns: List[Dict[str, Any]] = field(default_factory=list)
    rolling_summary: str = ""  # Evicted turns summarized via Gemini to save context tokens

    # Worksheet, Image & Title Metadata
    worksheet_data: Optional[Dict[str, Any]] = None
    image_uri: Optional[str] = None
    session_title: Optional[str] = None
    session_title_khmer: Optional[str] = None

    # Private callbacks (not serialized)
    _on_change: Optional[Callable[[], None]] = field(default=None, repr=False, compare=False)

    def _trigger_change(self):
        self.last_active_at = datetime.utcnow()
        if self._on_change is not None:
            self._on_change()

    def set_step_widget(self, widget: Union[Dict[str, Any], Any]):
        """
        Stores the StepWidgetPayload, updating current_step_index and solved_steps.
        Supports both StepWidgetPayload instances and raw dictionary representations.
        """
        if hasattr(widget, "model_dump"):
            self.step_widget = widget.model_dump()
            self.current_step_index = getattr(widget, "current_step_index", self.current_step_index)
        elif isinstance(widget, dict):
            self.step_widget = widget
            self.current_step_index = widget.get("current_step_index", self.current_step_index)
        else:
            self.step_widget = None

        if self.step_widget and "steps" in self.step_widget:
            # Sync solved_steps list for telemetry
            self.solved_steps = [
                s for s in self.step_widget["steps"]
                if s.get("status") == "completed"
            ]
            completed_indices = {
                index for index in self.step_widget.get("completed_steps", [])
                if isinstance(index, int) and 0 <= index < len(self.step_widget["steps"])
            }
            total_steps = len(self.step_widget["steps"])
            if len(completed_indices) >= total_steps and total_steps > 0:
                self.is_problem_complete = True

        self._trigger_change()

    def get_step_widget_payload(self) -> Optional[Any]:
        """
        Reconstructs the typed StepWidgetPayload Pydantic model from persistent dictionary.
        """
        if not self.step_widget:
            return None
        try:
            from app.services.socratic.card_schema import StepWidgetPayload
            return StepWidgetPayload.model_validate(self.step_widget)
        except Exception as e:
            logger.warning(f"Failed to deserialize StepWidgetPayload from session {self.session_id}: {e}")
            return None

    def clear_step_widget(self):
        """
        Clears the active problem and resets stepper progress for a new question.
        """
        self.step_widget = None
        self.current_step_index = 0
        self.hint_count = 0
        self.is_problem_complete = False
        self.formatted_markdown = None
        self.solved_steps = []
        self._trigger_change()

    def add_turn(self, user_input: str, bot_response: str):
        """
        Adds a conversation turn (user input + assistant response) to the session context.
        Evicts old turns exceeding max_turns into the rolling summary.
        """
        self.turns.append({
            "user": user_input,
            "bot": bot_response,
            "ts": datetime.utcnow().isoformat()
        })
        self.total_turns_count += 1

        if len(self.turns) > self.max_turns:
            overflow_count = len(self.turns) - self.max_turns
            evicted = self.turns[:overflow_count]
            self.turns = self.turns[overflow_count:]
            
            # Update rolling summary with evicted turns
            self._update_rolling_summary(evicted)

        self._trigger_change()

    def _update_rolling_summary(self, evicted_turns: List[Dict[str, Any]]):
        """
        Summarizes evicted turns using Gemini if available, or falls back to a deterministic string concatenation.
        """
        evicted_lines = []
        for turn in evicted_turns:
            u = turn.get("user", "").strip()
            b = turn.get("bot", "").strip()
            if u:
                evicted_lines.append(f"Student: {u}")
            if b:
                # Capture the first line of tutor response to keep summary concise
                first_b = b.split("\n")[0].strip()
                evicted_lines.append(f"Tutor: {first_b}")
        evicted_text = "\n".join(evicted_lines)

        if not evicted_text:
            return

        try:
            from app.services.llm import llm_service, ModelTier
            prompt = prompt_controller.get_rolling_summary_prompt(self.rolling_summary, evicted_text)
            resp = llm_service.generate_text(prompt, model_tier=ModelTier.FAST)
            summary_text = resp.text.strip()
            if summary_text:
                self.rolling_summary = summary_text
                return
        except Exception as e:
            logger.debug(f"Rolling summary LLM call fallback: {e}")
                
        # Deterministic fallback: preserve previous summary and append latest dialogue turn
        if self.rolling_summary:
            self.rolling_summary = (self.rolling_summary + " | " + evicted_text).strip(" | ")
        else:
            self.rolling_summary = evicted_text.strip()

        if len(self.rolling_summary) > 1000:
            self.rolling_summary = self.rolling_summary[-1000:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat(),
            "max_turns": self.max_turns,
            "total_turns_count": self.total_turns_count,
            "subject": self.subject,
            "grade_level": self.grade_level,
            "language": self.language,
            "original_raw_query": self.original_raw_query,
            "solved_steps": self.solved_steps,
            "current_step_index": self.current_step_index,
            "hint_count": self.hint_count,
            "practice_mode": self.practice_mode,
            "original_query": self.original_query,
            "tutor_feedback": self.tutor_feedback,
            "step_widget": self.step_widget,
            "formatted_markdown": self.formatted_markdown,
            "is_problem_complete": self.is_problem_complete,
            "turns": self.turns,
            "rolling_summary": self.rolling_summary,
            "worksheet_data": self.worksheet_data,
            "image_uri": self.image_uri,
            "session_title": self.session_title,
            "session_title_khmer": self.session_title_khmer
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionContext":
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow()
        last_active_at = datetime.fromisoformat(data["last_active_at"]) if "last_active_at" in data else created_at
        return cls(
            session_id=data["session_id"],
            created_at=created_at,
            last_active_at=last_active_at,
            max_turns=data.get("max_turns", 10),
            total_turns_count=data.get("total_turns_count", 0),
            subject=data.get("subject"),
            grade_level=data.get("grade_level", "grade_1_3"),
            language=data.get("language", "en"),
            original_raw_query=data.get("original_raw_query"),
            solved_steps=data.get("solved_steps", []),
            current_step_index=data.get("current_step_index", 0),
            hint_count=data.get("hint_count", 0),
            practice_mode=data.get("practice_mode", False),
            original_query=data.get("original_query", ""),
            tutor_feedback=data.get("tutor_feedback", ""),
            step_widget=data.get("step_widget"),
            formatted_markdown=data.get("formatted_markdown"),
            is_problem_complete=data.get("is_problem_complete", False),
            turns=data.get("turns", []),
            rolling_summary=data.get("rolling_summary", ""),
            worksheet_data=data.get("worksheet_data"),
            image_uri=data.get("image_uri"),
            session_title=data.get("session_title"),
            session_title_khmer=data.get("session_title_khmer")
        )


class SessionManager:
    """
    Manages session persistence and streaming in Redis with robust in-memory fallback.
    """
    def __init__(self, redis_client: Optional[redis.Redis] = None, connect_redis: bool = True):
        self._local_sessions: Dict[str, SessionContext] = {}
        self.redis_client: Optional[redis.Redis] = redis_client
        
        if self.redis_client is None and connect_redis:
            redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_password = os.getenv("REDIS_PASSWORD") or None
            
            logger.info(f"Connecting to Redis session store at {redis_host}:{redis_port}...")
            try:
                client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    password=redis_password,
                    decode_responses=True,
                    socket_timeout=0.5,
                    socket_connect_timeout=0.5
                )
                client.ping()
                self.redis_client = client
                logger.info("Redis session store connected successfully.")
            except Exception as e:
                logger.warning(f"Redis unavailable ({e}). SessionManager running in local in-memory fallback mode.")

    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """
        Retrieves an existing session without creating a new one if it does not exist.
        Checks Redis first, then in-memory local cache.
        """
        if session_id in self._local_sessions:
            session = self._local_sessions[session_id]
            session._on_change = lambda: self._save_session(session)
            return session

        if self.redis_client:
            try:
                raw_data = self.redis_client.get(f"session:{session_id}:context")
                if raw_data:
                    data = json.loads(raw_data)
                    session = SessionContext.from_dict(data)
                    session._on_change = lambda: self._save_session(session)
                    session._streamed_count = len(session.turns)
                    self._local_sessions[session_id] = session
                    return session
            except Exception as e:
                logger.warning(f"Failed to load session context from Redis ({e}). Checking local cache.")

        return None

    def get_or_create_session(self, session_id: str) -> SessionContext:
        """
        Loads an existing session context from Redis or in-memory fallback, or creates a new one.
        """
        existing = self.get_session(session_id)
        if existing is not None:
            return existing

        # Fallback to new session context creation
        logger.info(f"Creating new session context '{session_id}'.")
        session = SessionContext(session_id=session_id)
        session._on_change = lambda: self._save_session(session)
        session._streamed_count = 0
        self._save_session(session)
        return session

    def delete_session(self, session_id: str) -> bool:
        """
        Removes a session context from local memory and Redis.
        """
        deleted = False
        if session_id in self._local_sessions:
            del self._local_sessions[session_id]
            deleted = True

        if self.redis_client:
            try:
                self.redis_client.delete(f"session:{session_id}:context")
                self.redis_client.delete(f"session:{session_id}:transcript")
                deleted = True
            except Exception as e:
                logger.warning(f"Failed to delete session '{session_id}' from Redis: {e}")

        return deleted

    def _save_session(self, session: SessionContext):
        """
        Saves session context back to Redis (if available) and in-memory cache.
        """
        self._local_sessions[session.session_id] = session

        if not self.redis_client:
            return

        try:
            # 1. Save state context
            self.redis_client.set(
                f"session:{session.session_id}:context",
                json.dumps(session.to_dict()),
                ex=3600  # Expires context after 1 hour of inactivity
            )
            
            # 2. XADD new turns to the transcript stream
            if not hasattr(session, "_streamed_count"):
                session._streamed_count = 0
                
            new_turns = session.turns[session._streamed_count:]
            for turn in new_turns:
                ts_str = turn.get("ts", datetime.utcnow().isoformat())
                
                self.redis_client.xadd(
                    f"session:{session.session_id}:transcript",
                    {
                        "role": "user",
                        "content": turn.get("user", ""),
                        "ts": ts_str
                    }
                )
                self.redis_client.xadd(
                    f"session:{session.session_id}:transcript",
                    {
                        "role": "assistant",
                        "content": turn.get("bot", ""),
                        "ts": ts_str
                    }
                )
            
            session._streamed_count = len(session.turns)
        except Exception as e:
            logger.warning(f"Failed to save session '{session.session_id}' to Redis ({e}). State preserved in memory.")


session_manager = SessionManager()
