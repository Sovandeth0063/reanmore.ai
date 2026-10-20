"""
File: orchestrator/app/api/auth.py
Description: Student & Teacher Authentication Router (Class Code + 4-digit PIN)
             with JWT issuance, role enforcement, and current_user dependency.
"""

from typing import Optional, Dict, Any, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.database import (
    get_student_by_name,
    get_student_by_class_and_name,
    get_student_by_id,
    create_student_profile,
    update_student_last_login,
)
from app.services.auth.security import (
    hash_pin,
    verify_pin,
    create_access_token,
    decode_access_token,
)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Pydantic Request & Response Schemas ──

class LoginRequest(BaseModel):
    student_name: str = Field(..., description="Student username or name (e.g. 'dara')")
    pin: str = Field(..., min_length=4, max_length=6, description="4-digit PIN (e.g. '1234')")
    class_code: Optional[str] = Field(default="MAIN", description="Optional class code (defaults to 'MAIN')")


class RegisterRequest(BaseModel):
    student_name: str = Field(..., min_length=2, max_length=50, description="Student name / username")
    pin: str = Field(..., min_length=4, max_length=6, description="4-digit PIN")
    grade_level: int = Field(default=4, ge=1, le=6, description="Elementary Grade Level (1-6)")
    role: str = Field(default="student", description="Role ('student', 'parent')")
    language: str = Field(default="en", description="Language preference ('en' or 'km')")
    class_code: Optional[str] = Field(default="MAIN", description="Class code (defaults to 'MAIN')")


class RegisterStudentRequest(BaseModel):
    student_name: str = Field(..., description="Student name / username")
    pin: str = Field(..., min_length=4, max_length=6, description="4-digit PIN")
    class_code: Optional[str] = Field(default="MAIN", description="Class code to enroll student into")
    role: str = Field(default="student", description="Role ('student', 'parent')")
    grade_level: int = Field(default=4, ge=1, le=6, description="Elementary Grade Level (1-6)")
    language: str = Field(default="en", description="Language preference ('km' or 'en')")


class LoginResponse(BaseModel):
    token: str
    user_id: str
    student_name: str
    role: str
    grade_level: int
    class_code: str
    language: str


class UserMeResponse(BaseModel):
    user_id: str
    student_name: str
    role: str
    grade_level: int
    class_code: str
    language: str


# ── Dependency: get_current_user ──

async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    FastAPI dependency extracting Bearer JWT from Authorization header.
    Validates token signature and expiration.
    Returns decoded user payload dict containing user_id, role, grade_level, class_code.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Please log in with your Class Code & PIN.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    try:
        payload = decode_access_token(token, settings.AUTH_SECRET_KEY)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Session authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_optional_user(
    authorization: Optional[str] = Header(None)
) -> Optional[Dict[str, Any]]:
    """
    Optional user dependency. Returns user payload if valid token is supplied; otherwise None.
    Used for graceful migration during transition.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split("Bearer ", 1)[1].strip()
    try:
        return decode_access_token(token, settings.AUTH_SECRET_KEY)
    except Exception:
        return None


def require_role(allowed_roles: List[str]):
    """Role-guard dependency requiring the authenticated user to hold one of the allowed roles."""
    async def role_checker(user: Dict[str, Any] = Depends(get_current_user)):
        user_role = user.get("role", "student")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {allowed_roles}",
            )
        return user
    return role_checker


# ── Endpoints ──

@auth_router.post("/register", response_model=LoginResponse)
async def register(req: RegisterRequest):
    """
    Public self-registration endpoint for students and parents.
    Enrolls student directly into the PostgreSQL database, hashes 4-digit PIN,
    and issues a signed 30-day JWT.
    """
    clean_name = req.student_name.strip()
    clean_username = clean_name.lower().replace(" ", "_")
    clean_pin = req.pin.strip()
    clean_class = (req.class_code or "MAIN").strip().upper()

    # Check if student name already exists in database
    existing = await get_student_by_name(clean_username)
    if existing:
        # If the PIN matches the existing user's PIN, log them in seamlessly
        if verify_pin(clean_pin, existing.pin_hash):
            user_id = existing.user_id
            await update_student_last_login(user_id)
            token = create_access_token(
                {
                    "sub": user_id,
                    "user_id": user_id,
                    "student_name": existing.student_name,
                    "class_code": existing.class_code,
                    "role": existing.role,
                    "grade_level": existing.grade_level,
                    "language": existing.language,
                },
                settings.AUTH_SECRET_KEY,
                expires_in_seconds=86400 * settings.AUTH_TOKEN_EXPIRE_DAYS,
            )
            return LoginResponse(
                token=token,
                user_id=user_id,
                student_name=existing.student_name,
                role=existing.role,
                grade_level=existing.grade_level,
                class_code=existing.class_code,
                language=existing.language,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ឈ្មោះនេះមានរួចហើយ សូមជ្រើសរើសឈ្មោះផ្សេង (This username is already taken. Please choose another name).",
            )

    user_id = f"student_{uuid.uuid4().hex[:10]}"
    pin_hashed = hash_pin(clean_pin)

    created = await create_student_profile(
        user_id=user_id,
        class_code=clean_class,
        student_name=clean_username,
        pin_hash=pin_hashed,
        role=req.role,
        grade_level=req.grade_level,
        language=req.language,
    )

    if not created:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed in database. Please try again.",
        )

    token = create_access_token(
        {
            "sub": user_id,
            "user_id": user_id,
            "student_name": clean_username,
            "class_code": clean_class,
            "role": req.role,
            "grade_level": req.grade_level,
            "language": req.language,
        },
        settings.AUTH_SECRET_KEY,
        expires_in_seconds=86400 * settings.AUTH_TOKEN_EXPIRE_DAYS,
    )

    logger.info(f"Auth: Successfully registered new user {user_id} ({clean_username}) grade={req.grade_level}")

    return LoginResponse(
        token=token,
        user_id=user_id,
        student_name=clean_username,
        role=req.role,
        grade_level=req.grade_level,
        class_code=clean_class,
        language=req.language,
    )


@auth_router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """
    Authenticates a student or parent via Username/Name + 4-digit PIN.
    No class code or staff code required.
    Issues signed JWT access token valid for 30 days.
    """
    clean_name = req.student_name.strip().lower().replace(" ", "_")
    clean_pin = req.pin.strip()
    clean_class = (req.class_code or "MAIN").strip().upper()

    # 1. Lookup in Postgres database by student username
    student = await get_student_by_name(clean_name)
    if not student and clean_class:
        student = await get_student_by_class_and_name(clean_class, clean_name)

    if not student:
        logger.warning(f"Auth: User not found for '{clean_name}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="រកមិនឃើញគណនីនេះឡើយ សូមចុះឈ្មោះជាមុនសិន (Account not found. Please register first).",
        )

    if not verify_pin(clean_pin, student.pin_hash):
        logger.warning(f"Auth: Invalid PIN attempt for '{clean_name}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN មិនត្រឹមត្រូវឡើយ (Incorrect PIN. Please try again).",
        )

    user_id = student.user_id
    role = student.role
    grade_level = student.grade_level
    language = student.language
    await update_student_last_login(user_id)

    # 2. Create signed JWT access token
    payload = {
        "sub": user_id,
        "user_id": user_id,
        "student_name": student.student_name,
        "class_code": student.class_code,
        "role": role,
        "grade_level": grade_level,
        "language": language,
    }
    token = create_access_token(
        payload,
        settings.AUTH_SECRET_KEY,
        expires_in_seconds=86400 * settings.AUTH_TOKEN_EXPIRE_DAYS,
    )

    logger.info(f"Auth: Successful login for {user_id} ({student.student_name}) role={role}")

    return LoginResponse(
        token=token,
        user_id=user_id,
        student_name=student.student_name,
        role=role,
        grade_level=grade_level,
        class_code=student.class_code,
        language=language,
    )


@auth_router.get("/me", response_model=UserMeResponse)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile from the token.
    """
    return UserMeResponse(
        user_id=current_user.get("user_id", current_user.get("sub", "")),
        student_name=current_user.get("student_name", ""),
        role=current_user.get("role", "student"),
        grade_level=current_user.get("grade_level", 2),
        class_code=current_user.get("class_code", ""),
        language=current_user.get("language", "km"),
    )


@auth_router.post("/register-student", response_model=LoginResponse)
async def register_student(
    req: RegisterStudentRequest,
    current_user: Dict[str, Any] = Depends(require_role(["teacher", "admin"]))
):
    """
    Registers a new student profile under a class code.
    Restricted to authenticated Teachers and Admins.
    """
    clean_class = (req.class_code or "MAIN").strip().upper()
    clean_name = req.student_name.strip().lower()
    clean_pin = req.pin.strip()

    # Check if student already exists in this class
    existing = await get_student_by_class_and_name(clean_class, clean_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student '{clean_name}' is already registered in class '{clean_class}'.",
        )

    user_id = f"student_{clean_class.lower()}_{uuid.uuid4().hex[:8]}"
    pin_hashed = hash_pin(clean_pin)

    created = await create_student_profile(
        user_id=user_id,
        class_code=clean_class,
        student_name=clean_name,
        pin_hash=pin_hashed,
        role=req.role,
        grade_level=req.grade_level,
        language=req.language,
    )

    token = create_access_token(
        {
            "sub": user_id,
            "user_id": user_id,
            "student_name": clean_name,
            "class_code": clean_class,
            "role": req.role,
            "grade_level": req.grade_level,
            "language": req.language,
        },
        settings.AUTH_SECRET_KEY,
        expires_in_seconds=86400 * settings.AUTH_TOKEN_EXPIRE_DAYS,
    )

    logger.info(f"Auth: Teacher {current_user.get('user_id')} registered new student {user_id} in {clean_class}")

    return LoginResponse(
        token=token,
        user_id=user_id,
        student_name=clean_name,
        role=req.role,
        grade_level=req.grade_level,
        class_code=clean_class,
        language=req.language,
    )
