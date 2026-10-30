"""
File: orchestrator/app/services/session.py
Description: Redis-based Session Context persistent storage engine. Manages Socratic tutor 
             conversation turns, streams telemetry transcripts, and handles rolling summaries.
"""

from __future__ import annotations
import os
import json
import logging
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
import google.generativeai as genai
import redis
from app.services.prompts import prompt_controller

logger = logging.getLogger(__name__)

# Initialize Gemini safely
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@dataclass
class SessionContext:
    session_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    max_turns: int = 10
    total_turns_count: int = 0
    
    # State Machine Context
    subject: Optional[str] = None
    grade_level: str = "grade_10_12"
    language: str = "en"
    original_raw_query: Optional[str] = None
    
    # Socratic Tutoring Status
    solved_steps: List[Dict[str, Any]] = field(default_factory=list)
    current_step_index: int = 0
    hint_count: int = 0
    practice_mode: bool = False
    original_query: str = ""
    tutor_feedback: str = ""
    
    # Conversational Memory & Rolling Summary
    turns: List[Dict[str, Any]] = field(default_factory=list)
    rolling_summary: str = ""  # Evicted turns summarized via Gemini to save context tokens

    # Private callbacks (not serialized)
    _on_change: Optional[Callable[[], None]] = field(default=None, repr=False, compare=False)

    def _trigger_change(self):
        if self._on_change is not None:
            self._on_change()

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
        evicted_text = " | ".join(f"User: {t['user']} Tutor: {t['bot']}" for t in evicted_turns)
        
        if GEMINI_API_KEY:
            try:
                model = genai.GenerativeModel("gemini-2.5-flash")
                prompt = prompt_controller.get_rolling_summary_prompt(self.rolling_summary, evicted_text)
                response = model.generate_content(prompt)
                summary_text = response.text.strip()
                if summary_text:
                    self.rolling_summary = summary_text
                    return
            except Exception as e:
                logger.error(f"Failed to generate AI rolling summary: {e}. Falling back to deterministic append.")
                
        # Deterministic fallback
        self.rolling_summary = (self.rolling_summary + " | " + evicted_text).strip(" | ")
        if len(self.rolling_summary) > 1000:
            self.rolling_summary = self.rolling_summary[-1000:]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
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
            "turns": self.turns,
            "rolling_summary": self.rolling_summary
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionContext":
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow()
        return cls(
            session_id=data["session_id"],
            created_at=created_at,
            max_turns=data.get("max_turns", 10),
            total_turns_count=data.get("total_turns_count", 0),
            subject=data.get("subject"),
            grade_level=data.get("grade_level", "grade_10_12"),
            language=data.get("language", "en"),
            original_raw_query=data.get("original_raw_query"),
            solved_steps=data.get("solved_steps", []),
            current_step_index=data.get("current_step_index", 0),
            hint_count=data.get("hint_count", 0),
            practice_mode=data.get("practice_mode", False),
            original_query=data.get("original_query", ""),
            tutor_feedback=data.get("tutor_feedback", ""),
            turns=data.get("turns", []),
            rolling_summary=data.get("rolling_summary", "")
        )

class SessionManager:
    """
    Manages session persistence and streaming in Redis.
    """
    def __init__(self):
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD") or None
        
        logger.info(f"Connecting to Redis session store at {redis_host}:{redis_port}...")
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=2.0
        )
        # Verify connection on startup
        try:
            self.redis_client.ping()
            logger.info("Redis session store connected successfully.")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}. SessionManager will fail if Redis is unavailable.")

    def get_or_create_session(self, session_id: str) -> SessionContext:
        """
        Loads an existing session context from Redis, or creates a new one.
        """
        try:
            raw_data = self.redis_client.get(f"session:{session_id}:context")
            if raw_data:
                data = json.loads(raw_data)
                session = SessionContext.from_dict(data)
                session._on_change = lambda: self._save_session(session)
                session._streamed_count = len(session.turns)
                logger.info(f"Loaded existing session context '{session_id}' from Redis.")
                return session
        except Exception as e:
            logger.error(f"Failed to load session context from Redis: {e}")

        # Fallback to new session context creation
        logger.info(f"Creating new session context '{session_id}' in Redis.")
        session = SessionContext(session_id=session_id)
        session._on_change = lambda: self._save_session(session)
        session._streamed_count = 0
        self._save_session(session)
        return session

    def _save_session(self, session: SessionContext):
        """
        Saves session context back to Redis and streams new turns to Redis stream logs.
        """
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
            logger.error(f"Failed to save session '{session.session_id}' to Redis: {e}")

session_manager = SessionManager()
