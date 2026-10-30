"""
File: orchestrator/app/infrastructure/database.py
Description: Asynchronous PostgreSQL database engine setup, ORM schemas, and helper functions 
             for persistence of tutoring session logs and telemetry analysis.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import String, Text, DateTime, Boolean, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.core.logging import logger

# Declare declarative base
class Base(DeclarativeBase):
    pass

class SessionLog(Base):
    """
    ORM Model capturing metadata and status of active tutoring sessions.
    """
    __tablename__ = "session_logs"

    session_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    subject: Mapped[Optional[str]] = mapped_column(String(50))
    grade_level: Mapped[str] = mapped_column(String(50))
    language: Mapped[str] = mapped_column(String(10))
    original_raw_query: Mapped[Optional[str]] = mapped_column(Text)
    solved_steps: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)
    practice_mode: Mapped[bool] = mapped_column(Boolean, default=False)

    turns: Mapped[List["TelemetryLog"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="selectin"
    )


class TelemetryLog(Base):
    """
    ORM Model capturing granular telemetry for each interactive query (student attempt).
    """
    __tablename__ = "telemetry_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("session_logs.session_id", ondelete="CASCADE"), index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_query: Mapped[str] = mapped_column(Text)
    tutor_response: Mapped[str] = mapped_column(Text)
    step_index: Mapped[int] = mapped_column(Integer)
    hint_count: Mapped[int] = mapped_column(Integer)
    is_mistake: Mapped[bool] = mapped_column(Boolean)
    processing_time_ms: Mapped[float] = mapped_column(Float)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    session: Mapped["SessionLog"] = relationship(back_populates="turns")


# Setup Engine and async session factory
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    """
    Initializes database tables during application startup.
    """
    logger.info("Initializing Postgres database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Postgres database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing Postgres database: {e}", exc_info=True)


async def save_session_and_telemetry(
    session_id: str,
    subject: Optional[str],
    grade_level: str,
    language: str,
    original_raw_query: Optional[str],
    solved_steps: Optional[List[Dict[str, Any]]],
    practice_mode: bool,
    user_query: str,
    tutor_response: str,
    step_index: int,
    hint_count: int,
    is_mistake: bool,
    processing_time_ms: float,
    metadata_json: Optional[Dict[str, Any]] = None
):
    """
    Saves session metadata (upserts) and inserts a telemetry record inside a transaction.
    """
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                # 1. Upsert SessionLog
                db_session = await session.get(SessionLog, session_id)
                if not db_session:
                    logger.info(f"Database: Creating new SessionLog for '{session_id}'")
                    db_session = SessionLog(
                        session_id=session_id,
                        subject=subject,
                        grade_level=grade_level,
                        language=language,
                        original_raw_query=original_raw_query,
                        solved_steps=solved_steps,
                        practice_mode=practice_mode
                    )
                    session.add(db_session)
                else:
                    logger.info(f"Database: Updating existing SessionLog for '{session_id}'")
                    db_session.subject = subject
                    db_session.grade_level = grade_level
                    db_session.language = language
                    db_session.original_raw_query = original_raw_query
                    db_session.solved_steps = solved_steps
                    db_session.practice_mode = practice_mode
                    db_session.updated_at = datetime.utcnow()

                # 2. Insert TelemetryLog turn
                telemetry = TelemetryLog(
                    session_id=session_id,
                    user_query=user_query,
                    tutor_response=tutor_response,
                    step_index=step_index,
                    hint_count=hint_count,
                    is_mistake=is_mistake,
                    processing_time_ms=processing_time_ms,
                    metadata_json=metadata_json
                )
                session.add(telemetry)
            
            logger.info(f"Database: Saved session & telemetry turn for '{session_id}' successfully.")
        except Exception as e:
            logger.error(f"Database: Failed to save session/telemetry for session '{session_id}': {e}", exc_info=True)
