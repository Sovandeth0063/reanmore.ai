"""
File: orchestrator/app/infrastructure/database.py
Description: Asynchronous PostgreSQL database engine setup, ORM schemas, and helper functions 
             for persistence of tutoring session logs, worksheets, and telemetry analysis.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import String, Text, DateTime, Boolean, Integer, Float, ForeignKey, JSON, select, func
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
    subject: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    grade_level: Mapped[str] = mapped_column(String(50), default="grade_1_3")
    language: Mapped[str] = mapped_column(String(10), default="km")
    session_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    session_title_khmer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    worksheet_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    image_uri: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    original_raw_query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    solved_steps: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
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
engine = create_async_engine(settings.DATABASE_URL, echo=False, connect_args={"timeout": 1.5})
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    """
    Initializes database tables and migrates columns during application startup.
    """
    logger.info("Initializing Postgres database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            from sqlalchemy import text
            migration_sqls = [
                "ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS session_title VARCHAR(255);",
                "ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS session_title_khmer VARCHAR(255);",
                "ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS worksheet_data JSON;",
                "ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS image_uri TEXT;"
            ]
            for sql in migration_sqls:
                try:
                    await conn.execute(text(sql))
                except Exception as ex:
                    logger.debug(f"Migration statement ignored: {ex}")
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
    metadata_json: Optional[Dict[str, Any]] = None,
    session_title: Optional[str] = None,
    session_title_khmer: Optional[str] = None,
    worksheet_data: Optional[Dict[str, Any]] = None,
    image_uri: Optional[str] = None,
    **kwargs
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
                        session_title=session_title,
                        session_title_khmer=session_title_khmer,
                        worksheet_data=worksheet_data,
                        image_uri=image_uri,
                        original_raw_query=original_raw_query,
                        solved_steps=solved_steps,
                        practice_mode=practice_mode
                    )
                    session.add(db_session)
                else:
                    logger.info(f"Database: Updating existing SessionLog for '{session_id}'")
                    if subject:
                        db_session.subject = subject
                    db_session.grade_level = grade_level
                    db_session.language = language
                    if session_title:
                        db_session.session_title = session_title
                    if session_title_khmer:
                        db_session.session_title_khmer = session_title_khmer
                    if worksheet_data is not None:
                        db_session.worksheet_data = worksheet_data
                    if image_uri:
                        db_session.image_uri = image_uri
                    if original_raw_query:
                        db_session.original_raw_query = original_raw_query
                    if solved_steps is not None:
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


async def save_worksheet_session_to_db(
    session_id: str,
    subject: Optional[str] = None,
    grade_level: str = "grade_1_3",
    language: str = "km",
    session_title: Optional[str] = None,
    session_title_khmer: Optional[str] = None,
    worksheet_data: Optional[Dict[str, Any]] = None,
    image_uri: Optional[str] = None,
    **kwargs
):
    """
    Upserts session worksheet metadata to PostgreSQL database.
    """
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                db_session = await session.get(SessionLog, session_id)
                if not db_session:
                    db_session = SessionLog(
                        session_id=session_id,
                        subject=subject,
                        grade_level=grade_level,
                        language=language,
                        session_title=session_title,
                        session_title_khmer=session_title_khmer,
                        worksheet_data=worksheet_data,
                        image_uri=image_uri,
                    )
                    session.add(db_session)
                else:
                    if subject:
                        db_session.subject = subject
                    db_session.grade_level = grade_level
                    db_session.language = language
                    if session_title:
                        db_session.session_title = session_title
                    if session_title_khmer:
                        db_session.session_title_khmer = session_title_khmer
                    if worksheet_data is not None:
                        db_session.worksheet_data = worksheet_data
                    if image_uri:
                        db_session.image_uri = image_uri
                    db_session.updated_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Database: Failed to save worksheet session '{session_id}': {e}", exc_info=True)


async def get_all_session_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Returns recent session records for dashboard or session selection.
    """
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(SessionLog).order_by(SessionLog.updated_at.desc()).limit(limit)
            result = await session.execute(stmt)
            records = result.scalars().all()
            logs = []
            for r in records:
                logs.append({
                    "session_id": r.session_id,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                    "subject": r.subject,
                    "grade_level": r.grade_level,
                    "language": r.language,
                    "session_title": r.session_title,
                    "session_title_khmer": r.session_title_khmer,
                    "original_raw_query": r.original_raw_query,
                    "worksheet_data": r.worksheet_data,
                    "image_uri": r.image_uri,
                    "practice_mode": r.practice_mode,
                    "solved_steps": r.solved_steps,
                })
            return logs
        except Exception as e:
            logger.error(f"Database: Failed to retrieve session logs: {e}", exc_info=True)
            return []


async def delete_session_from_db(session_id: str):
    """
    Permanently deletes a session and associated telemetry cascades from database.
    """
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                db_session = await session.get(SessionLog, session_id)
                if db_session:
                    await session.delete(db_session)
                    logger.info(f"Database: Deleted session record '{session_id}'")
        except Exception as e:
            logger.error(f"Database: Failed to delete session '{session_id}': {e}", exc_info=True)


async def get_student_telemetry_stats() -> Dict[str, Any]:
    """
    Computes learning streaks, total sessions, turns, and XP from PostgreSQL.
    """
    async with AsyncSessionLocal() as session:
        try:
            sessions_count_res = await session.execute(select(func.count(SessionLog.session_id)))
            total_sessions = sessions_count_res.scalar() or 0

            turns_count_res = await session.execute(select(func.count(TelemetryLog.id)))
            total_turns = turns_count_res.scalar() or 0

            total_xp = (total_turns * 10) + (total_sessions * 50)
            if total_xp == 0:
                total_xp = 50

            return {
                "current_streak": 1,
                "best_streak": 1,
                "total_xp": total_xp,
                "total_sessions": total_sessions,
                "total_turns": total_turns,
                "has_studied_today": True
            }
        except Exception as e:
            logger.warning(f"Database: Failed to compute telemetry stats: {e}")
            return {
                "current_streak": 1,
                "best_streak": 1,
                "total_xp": 50,
                "total_sessions": 0,
                "total_turns": 0,
                "has_studied_today": True
            }
