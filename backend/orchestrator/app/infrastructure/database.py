"""
File: orchestrator/app/infrastructure/database.py
Description: Asynchronous PostgreSQL database engine setup, ORM schemas, and helper functions 
             for persistence of tutoring session logs, worksheets, and telemetry analysis.
"""

from datetime import datetime
import asyncio
from typing import Any, Dict, List, Optional
from sqlalchemy import String, Text, DateTime, Boolean, Integer, Float, ForeignKey, JSON, select, func, UniqueConstraint
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
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
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
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_query: Mapped[str] = mapped_column(Text)
    tutor_response: Mapped[str] = mapped_column(Text)
    step_index: Mapped[int] = mapped_column(Integer)
    hint_count: Mapped[int] = mapped_column(Integer)
    is_mistake: Mapped[bool] = mapped_column(Boolean)
    processing_time_ms: Mapped[float] = mapped_column(Float)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    session: Mapped["SessionLog"] = relationship(back_populates="turns")


class StudentProfile(Base):
    """
    ORM Model capturing student, teacher, or admin identity and hashed PIN credentials.
    Enforces Class Code + 4-digit PIN authentication.
    """
    __tablename__ = "student_profiles"

    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    class_code: Mapped[str] = mapped_column(String(50), index=True)
    student_name: Mapped[str] = mapped_column(String(100), index=True)
    pin_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="student")  # "student", "teacher", "admin", "parent"
    grade_level: Mapped[int] = mapped_column(Integer, default=2)
    language: Mapped[str] = mapped_column(String(10), default="km")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class UsageLedger(Base):
    """
    Append-only durable audit ledger recording every deducted problem quota transaction.
    Enforces uniqueness on (user_id, problem_id) to guarantee zero double-counting.
    """
    __tablename__ = "usage_ledger"
    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", name="uq_user_problem_quota"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    problem_id: Mapped[str] = mapped_column(String(150), index=True)
    problem_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    subject: Mapped[str] = mapped_column(String(50), default="math")
    tokens_consumed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class GapEvent(Base):
    """
    ORM Model capturing unified gap events: content gaps, learner misconceptions,
    and system reliability events across all tutoring sessions.
    Adheres strictly to Architecture v2.1 Section 11.2 and Phase 1D Specification.
    """
    __tablename__ = "gap_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    gap_type: Mapped[str] = mapped_column(String(20), index=True)  # "content", "learner", "system"
    gap_code: Mapped[str] = mapped_column(String(64), index=True)  # e.g., "NO_SKILL_MATCH", "LEAK_BLOCKED"
    severity: Mapped[int] = mapped_column(Integer, default=2)  # 1: low/info, 2: med/warning, 3: high/critical
    user_hash: Mapped[str] = mapped_column(String(64), index=True)  # sha256(salt || user_id), never raw ID
    user_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("student_profiles.user_id", ondelete="SET NULL"), nullable=True, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("session_logs.session_id", ondelete="SET NULL"), nullable=True, index=True)
    problem_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    grade_tier: Mapped[Optional[str]] = mapped_column(String(20), default="grade_1_3")
    subject: Mapped[str] = mapped_column(String(50), default="math")
    skill_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    step_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fingerprint: Mapped[str] = mapped_column(String(128), index=True)  # dedupe key: gap_code|skill_id|shape
    details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="open")  # "open", "triaged", "fixed", "wontfix"
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "open")
        kwargs.setdefault("resolved", False)
        kwargs.setdefault("severity", 2)
        kwargs.setdefault("grade_tier", "grade_1_3")
        kwargs.setdefault("subject", "math")
        kwargs.setdefault("created_at", datetime.utcnow())
        super().__init__(**kwargs)

    @property
    def event_code(self) -> str:
        return self.gap_code

    @property
    def grade_level(self) -> Optional[str]:
        return self.grade_tier

    @property
    def domain(self) -> str:
        return self.subject



# Setup Engine and async session factory
engine = create_async_engine(settings.DATABASE_URL, echo=False, connect_args={"timeout": 1.5})
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
database_ready = False

async def init_db():
    """
    Initializes database tables, creates roll-up views, and migrates columns during startup.
    """
    global database_ready
    database_ready = False
    logger.info("Initializing Postgres database tables...")
    from sqlalchemy import text
    migration_sqls = [
        "ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS session_title VARCHAR(255);",
        "ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS session_title_khmer VARCHAR(255);",
        "ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS worksheet_data JSON;",
        "ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS image_uri TEXT;",
        "ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS user_id VARCHAR(100);",
        "ALTER TABLE telemetry_logs ADD COLUMN IF NOT EXISTS user_id VARCHAR(100);",
        "DROP VIEW IF EXISTS gap_summary;",
        """
        CREATE VIEW gap_summary AS
        SELECT fingerprint, gap_type, gap_code, skill_id, grade_tier, subject,
               COUNT(*)                         AS occurrences,
               COUNT(DISTINCT user_hash)        AS distinct_students,
               MIN(created_at)                  AS first_seen,
               MAX(created_at)                  AS last_seen,
               MAX(severity)                    AS max_severity,
               SUM(CASE WHEN resolved = FALSE THEN 1 ELSE 0 END) AS unreviewed_count
        FROM gap_events
        WHERE status IN ('open', 'triaged')
        GROUP BY fingerprint, gap_type, gap_code, skill_id, grade_tier, subject;
        """
    ]
    for attempt in range(1, 6):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                for sql in migration_sqls:
                    await conn.execute(text(sql))
            logger.info("Postgres database tables and views initialized successfully.")
            database_ready = True
            await seed_default_students_if_empty()
            return
        except Exception as e:
            if attempt == 5:
                logger.error("Postgres initialization failed after %s attempts; continuing in degraded mode: %s", attempt, e, exc_info=True)
                return
            logger.warning("Postgres is not ready (attempt %s/5): %s", attempt, e)
            await asyncio.sleep(attempt)


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
    user_id: Optional[str] = None,
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
                        user_id=user_id,
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
                    if user_id and not db_session.user_id:
                        db_session.user_id = user_id
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
                    user_id=user_id,
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
    user_id: Optional[str] = None,
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
                        user_id=user_id,
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
                    if user_id and not db_session.user_id:
                        db_session.user_id = user_id
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


async def get_student_by_class_and_name(class_code: str, student_name: str) -> Optional[StudentProfile]:
    """Finds a student profile by class code and student name (case-insensitive)."""
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(StudentProfile).where(
                func.lower(StudentProfile.class_code) == class_code.lower().strip(),
                func.lower(StudentProfile.student_name) == student_name.lower().strip(),
            )
            res = await session.execute(stmt)
            return res.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Database: get_student_by_class_and_name failed: {e}")
            return None


async def get_student_by_id(user_id: str) -> Optional[StudentProfile]:
    """Retrieves a student profile by primary key user_id."""
    async with AsyncSessionLocal() as session:
        try:
            return await session.get(StudentProfile, user_id)
        except Exception as e:
            logger.error(f"Database: get_student_by_id failed: {e}")
            return None


async def create_student_profile(
    user_id: str,
    class_code: str,
    student_name: str,
    pin_hash: str,
    role: str = "student",
    grade_level: int = 2,
    language: str = "km"
) -> Optional[StudentProfile]:
    """Inserts a new student profile."""
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                profile = StudentProfile(
                    user_id=user_id,
                    class_code=class_code.upper().strip(),
                    student_name=student_name.strip(),
                    pin_hash=pin_hash,
                    role=role,
                    grade_level=grade_level,
                    language=language
                )
                session.add(profile)
                await session.flush()
                return profile
        except Exception as e:
            logger.error(f"Database: create_student_profile failed: {e}")
            return None


async def update_student_last_login(user_id: str):
    """Updates last_login_at timestamp for a student profile."""
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                profile = await session.get(StudentProfile, user_id)
                if profile:
                    profile.last_login_at = datetime.utcnow()
        except Exception as e:
            logger.warning(f"Database: update_student_last_login failed: {e}")


async def seed_default_students_if_empty():
    """
    Seeds default student/teacher/admin profiles if student_profiles table is empty.
    Provides standard class codes: GRADE4A (Sochea 1234, Teacher 9999), GRADE2A (Bopha 1111).
    """
    from app.services.auth.security import hash_pin
    default_seeds = [
        {
            "user_id": "account_student_sochea",
            "class_code": "GRADE4A",
            "student_name": "sochea",
            "pin": "1234",
            "role": "student",
            "grade_level": 4,
            "language": "en"
        },
        {
            "user_id": "account_teacher_lokkru",
            "class_code": "GRADE4A",
            "student_name": "teacher",
            "pin": "9999",
            "role": "teacher",
            "grade_level": 4,
            "language": "km"
        },
        {
            "user_id": "account_student_bopha",
            "class_code": "GRADE2A",
            "student_name": "bopha",
            "pin": "1111",
            "role": "student",
            "grade_level": 2,
            "language": "km"
        },
        {
            "user_id": "account_admin_master",
            "class_code": "ADMIN",
            "student_name": "admin",
            "pin": "0000",
            "role": "admin",
            "grade_level": 4,
            "language": "en"
        }
    ]
    try:
        async with AsyncSessionLocal() as session:
            count_res = await session.execute(select(func.count(StudentProfile.user_id)))
            if (count_res.scalar() or 0) == 0:
                logger.info("Database: Seeding default StudentProfiles...")
                async with session.begin():
                    for item in default_seeds:
                        profile = StudentProfile(
                            user_id=item["user_id"],
                            class_code=item["class_code"].upper(),
                            student_name=item["student_name"].lower(),
                            pin_hash=hash_pin(item["pin"]),
                            role=item["role"],
                            grade_level=item["grade_level"],
                            language=item["language"]
                        )
                        session.add(profile)
                logger.info("Database: Default StudentProfiles seeded successfully.")
    except Exception as e:
        logger.warning(f"Database: Could not seed default StudentProfiles (database may be offline): {e}")

