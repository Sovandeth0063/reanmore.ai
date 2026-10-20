"""
File: backend/testing/unit/auth/test_auth.py
Description: Unit tests for Class Code + 4-digit PIN authentication,
             JWT tokens, role enforcement, and FastAPI dependency checks.
"""

# pyrefly: ignore [missing-import]
import os
import sys
import pytest
from httpx import AsyncClient, ASGITransport

# Ensure repo root and orchestrator are on sys.path
def _find_repo_root():
    cur = os.path.abspath(os.path.dirname(__file__))
    while cur and not os.path.exists(os.path.join(cur, "orchestrator")):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return cur

BASE_DIR = _find_repo_root()
ORCHESTRATOR_DIR = os.path.join(BASE_DIR, "orchestrator")
for _p in (BASE_DIR, ORCHESTRATOR_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "orchestrator")))

# pyrefly: ignore [missing-import]
from app.main import app
# pyrefly: ignore [missing-import]
from app.services.auth.security import (
    hash_pin,
    verify_pin,
    create_access_token,
    decode_access_token,
)
# pyrefly: ignore [missing-import]
from app.core.config import settings
# pyrefly: ignore [missing-import]
from app.services.session import session_manager


# ── Unit Tests for Security Utilities ──

def test_pin_hashing_and_verification():
    pin = "1234"
    hashed = hash_pin(pin)
    
    assert "$" in hashed
    assert verify_pin("1234", hashed) is True
    assert verify_pin("0000", hashed) is False
    assert verify_pin("12345", hashed) is False
    assert verify_pin("", hashed) is False
    assert verify_pin("1234", "invalid_format") is False


def test_jwt_creation_and_decoding():
    payload = {"sub": "student_123", "role": "student", "grade_level": 4}
    token = create_access_token(payload, settings.AUTH_SECRET_KEY, expires_in_seconds=3600)

    assert isinstance(token, str)
    assert len(token.split(".")) == 3

    decoded = decode_access_token(token, settings.AUTH_SECRET_KEY)
    assert decoded["sub"] == "student_123"
    assert decoded["role"] == "student"
    assert decoded["grade_level"] == 4
    assert "exp" in decoded


def test_jwt_tampered_signature_rejected():
    payload = {"sub": "student_123", "role": "student"}
    token = create_access_token(payload, settings.AUTH_SECRET_KEY, expires_in_seconds=3600)
    
    parts = token.split(".")
    # Tamper payload
    tampered = f"{parts[0]}.eyJyZXBsYWNlZCI6InRydWUifQ.{parts[2]}"
    with pytest.raises(ValueError, match="Invalid token signature"):
        decode_access_token(tampered, settings.AUTH_SECRET_KEY)


def test_jwt_expired_token_rejected():
    payload = {"sub": "student_123"}
    # Token expired 10 seconds ago
    expired_token = create_access_token(payload, settings.AUTH_SECRET_KEY, expires_in_seconds=-10)

    with pytest.raises(ValueError, match="Token has expired"):
        decode_access_token(expired_token, settings.AUTH_SECRET_KEY)


# ── Integration Tests for Auth Endpoints via Test Client ──

@pytest.mark.asyncio
async def test_auth_login_successful_demo_student():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/auth/login",
            json={
                "class_code": "GRADE4A",
                "student_name": "sochea",
                "pin": "1234",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user_id"] == "account_student_sochea"
        assert data["student_name"] == "sochea"
        assert data["role"] == "student"
        assert data["grade_level"] == 4
        assert data["class_code"] == "GRADE4A"


@pytest.mark.asyncio
async def test_auth_login_successful_teacher():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/auth/login",
            json={
                "class_code": "GRADE4A",
                "student_name": "teacher",
                "pin": "9999",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "teacher"
        assert data["user_id"] == "account_teacher_lokkru"


@pytest.mark.asyncio
async def test_auth_login_invalid_pin_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/auth/login",
            json={
                "class_code": "GRADE4A",
                "student_name": "sochea",
                "pin": "9999",  # Wrong PIN for sochea
            },
        )
        assert resp.status_code == 401
        assert "PIN មិនត្រឹមត្រូវ" in resp.json()["detail"] or "Incorrect PIN" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_auth_login_unknown_student_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/auth/login",
            json={
                "class_code": "GRADE99X",
                "student_name": "unknown_student",
                "pin": "1234",
            },
        )
        assert resp.status_code == 401
        assert "រកមិនឃើញ" in resp.json()["detail"] or "not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_auth_me_with_valid_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First login to get a token
        login_res = await client.post(
            "/api/auth/login",
            json={
                "class_code": "GRADE4A",
                "student_name": "sochea",
                "pin": "1234",
            },
        )
        token = login_res.json()["token"]

        # Call /me with Bearer token
        me_res = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["user_id"] == "account_student_sochea"
        assert me_data["student_name"] == "sochea"
        assert me_data["role"] == "student"


@pytest.mark.asyncio
async def test_auth_me_without_token_returns_401():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        me_res = await client.get("/api/auth/me")
        assert me_res.status_code == 401


@pytest.mark.asyncio
async def test_register_student_role_protection():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Student login token
        student_login = await client.post(
            "/api/auth/login",
            json={"class_code": "GRADE4A", "student_name": "sochea", "pin": "1234"},
        )
        student_token = student_login.json()["token"]

        # Attempt to register another student as a student -> 403 Forbidden
        reg_res = await client.post(
            "/api/auth/register-student",
            json={
                "class_code": "GRADE4A",
                "student_name": "new_kid",
                "pin": "5555",
                "grade_level": 4,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert reg_res.status_code == 403


@pytest.mark.asyncio
async def test_session_sync_attaches_authenticated_student_identity():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login to obtain student token
        login_res = await client.post(
            "/api/auth/login",
            json={"class_code": "GRADE4A", "student_name": "sochea", "pin": "1234"},
        )
        token = login_res.json()["token"]

        test_session_id = "test_auth_sync_session_001"
        sync_res = await client.post(
            "/api/session/sync",
            json={
                "session_id": test_session_id,
                "title": "Math Homework Page 1",
                "grade_level": "grade_4",
                "language": "en",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert sync_res.status_code == 200

        # Verify session context now holds authenticated student identity
        session = session_manager.get_session(test_session_id)
        assert session is not None
        assert session.user_id == "account_student_sochea"
        assert session.student_name == "sochea"
        assert session.role == "student"
        assert session.class_code == "GRADE4A"


@pytest.mark.asyncio
async def test_stats_endpoint_with_and_without_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Anonymous call
        anon_res = await client.get("/api/stats")
        assert anon_res.status_code == 200

        # Authenticated call
        login_res = await client.post(
            "/api/auth/login",
            json={"class_code": "GRADE4A", "student_name": "sochea", "pin": "1234"},
        )
        token = login_res.json()["token"]
        auth_res = await client.get("/api/stats", headers={"Authorization": f"Bearer {token}"})
        assert auth_res.status_code == 200

