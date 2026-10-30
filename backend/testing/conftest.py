"""
Pytest configuration and root path resolution for all test suites.
Ensures `orchestrator` and repository root are on `sys.path` regardless of invocation directory.
"""
import json
import os
import sys
from pathlib import Path

import pytest

# Unit/integration tests must be deterministic and offline. Pin the LLM gateway to
# the in-process mock provider before any `app.*` module reads Settings (which would
# otherwise load a developer .env pointing at a cloud or local Ollama instance).
os.environ["LLM_PRIMARY_PROVIDER"] = "mock"
os.environ["LLM_FALLBACK_PROVIDER"] = "mock"
# Phase 1 MVP defers worksheet OCR; tests opt in per-test via monkeypatch.
os.environ["ENABLE_API_OCR"] = "false"
# Khmer UI toggle + /api/translate ship in v2.1 (full NLP is deferred).
os.environ["ENABLE_KHMER_LANGUAGE"] = "true"

# Find repository root by searching upward for orchestrator directory
_current = Path(__file__).resolve().parent
while _current != _current.parent:
    if (_current / "orchestrator").is_dir():
        break
    _current = _current.parent

REPO_ROOT = _current
ORCHESTRATOR_DIR = REPO_ROOT / "orchestrator"
PROJECT_ROOT = REPO_ROOT.parent

for _p in (str(REPO_ROOT), str(ORCHESTRATOR_DIR), str(PROJECT_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Embedded Qdrant takes an exclusive lock on its storage folder. Copy the
# curriculum store into a per-session temp dir so the test suite can run while a
# developer backend (or a parallel evaluator) is using the real one.
if "QDRANT_PATH" not in os.environ:
    import shutil
    import tempfile

    _qdrant_tmp = tempfile.mkdtemp(prefix="reanmore_qdrant_")
    _qdrant_src = Path(REPO_ROOT) / "orchestrator" / "data" / "qdrant"
    if _qdrant_src.is_dir():
        for _entry in _qdrant_src.iterdir():
            if _entry.name == ".lock":
                continue
            _dest = Path(_qdrant_tmp) / _entry.name
            try:
                if _entry.is_dir():
                    shutil.copytree(_entry, _dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(_entry, _dest)
            except OSError:
                pass
    os.environ["QDRANT_PATH"] = _qdrant_tmp


_STUB_WIDGET = {
    "total_steps": 2,
    "current_step_index": 0,
    "completed_steps": [],
    "steps": [
        {
            "step_number": 1,
            "title": "Find the key idea",
            "status": "in_progress",
            "mission": "Read the question and spot the main idea.",
            "clue": "Look for the process or relationship being described.",
            "helpful_example": "Think of a similar situation you have seen.",
            "your_turn": "What is the main idea in the question?",
            "expected_answer": "idea",
            "concept": "science",
            "hints": ["Read the clue once more.", "Picture the situation.", "Say the idea in your own words."],
            "visual_data": None,
        },
        {
            "step_number": 2,
            "title": "Explain it simply",
            "status": "up_next",
            "mission": "Use the idea to answer the question.",
            "clue": "Connect the clue to the question.",
            "helpful_example": "Explain it to a friend in one sentence.",
            "your_turn": "How would you explain this?",
            "expected_answer": "explanation",
            "concept": "science",
            "hints": ["Start with the clue.", "Use simple words.", "Check that it answers the question."],
            "visual_data": None,
        },
    ],
}


@pytest.fixture
def stub_socratic_llm(monkeypatch):
    """Return a deterministic exercise-planning payload from the LLM gateway.

    Graph tests that use topics without a deterministic skill template need step
    cards. Stub the controller call so the test exercises graph wiring instead of
    whatever LLM happens to be reachable from the developer machine.
    """
    from app.services.socratic.prompts.controller import SocraticPromptController

    payload = json.dumps(_STUB_WIDGET)
    monkeypatch.setattr(
        SocraticPromptController, "_call_gemini_llm", lambda _self, _prompt: payload
    )
    return _STUB_WIDGET
