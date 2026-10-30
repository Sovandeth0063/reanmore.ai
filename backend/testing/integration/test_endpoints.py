"""
File: testing/test_endpoints.py
Description: Tests for /api/query, /api/step/navigate, and /api/session/{session_id} endpoints
             verifying Socratic Stepper Widget payloads and dual-mode markdown output.
"""

import os
import sys

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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orchestrator")))

from fastapi.testclient import TestClient
# pyrefly: ignore [missing-import]
from app.main import app

client = TestClient(app)


def test_api_query_initial_problem():
    payload = {
        "query": "Leo had 10 cookies and gave 4 to Sam. How many are left?",
        "session_id": "test_endpoint_session_1",
        "grade_level": "grade_1_3",
        "language": "en"
    }
    response = client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_endpoint_session_1"
    assert "solution" in data
    assert data["step_widget"] is not None
    assert len(data["step_widget"]["steps"]) >= 2
    assert data["current_step_index"] == 0
    assert data["is_problem_complete"] is False


def test_api_step_navigation():
    # First initialize a problem
    session_id = "test_endpoint_nav_session"
    init_res = client.post("/api/query", json={
        "query": "What is 15 - 5?",
        "session_id": session_id,
        "grade_level": "grade_1_3"
    })
    assert init_res.status_code == 200

    # Jump to Step 2 (index 1)
    nav_res = client.post("/api/step/navigate", json={
        "session_id": session_id,
        "target_step_index": 1
    })
    assert nav_res.status_code == 200
    nav_data = nav_res.json()
    assert nav_data["current_step_index"] == 1
    assert "Step 2" in nav_data["feedback_message"]


def test_api_get_session(stub_socratic_llm):
    session_id = "test_endpoint_get_session"
    # Query first
    client.post("/api/query", json={
        "query": "Why do plants need sunlight?",
        "session_id": session_id,
        "grade_level": "grade_1_3"
    })

    # Retrieve session
    res = client.get(f"/api/session/{session_id}")
    assert res.status_code == 200
    session_data = res.json()
    assert session_data["session_id"] == session_id
    assert session_data["step_widget"] is not None
