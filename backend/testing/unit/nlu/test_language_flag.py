"""
Unit tests for ReanMore v2.1 Feature Flags & Language Deferral (Phase 7).
Verifies that:
1. When ENABLE_KHMER_LANGUAGE is False (default):
   - detect_language returns "english" unconditionally
   - translate_to_khmer returns the original text untouched
   - /api/translate returns HTTP 501 Not Implemented
2. When ENABLE_KHMER_LANGUAGE is True:
   - detect_language recognizes Khmer Unicode and Khmenglish
3. Voice STT is disabled by default in v2.1.
"""

import os
import sys
# pyrefly: ignore [missing-import]
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

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

# pyrefly: ignore [missing-import]
from app.core.config import settings
# pyrefly: ignore [missing-import]
from app.services.nlu import detect_language
# pyrefly: ignore [missing-import]
from app.api.endpoints import translate_to_khmer
# pyrefly: ignore [missing-import]
from app.main import app

client = TestClient(app)


def test_default_feature_flags():
    """Verify v2.1 default feature flag states."""
    assert getattr(settings, "ENABLE_KHMER_LANGUAGE", False) is False
    assert getattr(settings, "ENABLE_VOICE_STT", False) is False


def test_detect_language_when_disabled():
    """When ENABLE_KHMER_LANGUAGE is False, all input returns 'english'."""
    with patch.object(settings, "ENABLE_KHMER_LANGUAGE", False):
        # Khmer script
        assert detect_language("តើ 5 + 3 ស្មើនឹងប៉ុន្មាន?") == "english"
        # Khmenglish slang
        assert detect_language("bong help me solve this") == "english"
        # English
        assert detect_language("What is 5 + 3?") == "english"


def test_detect_language_when_enabled():
    """When ENABLE_KHMER_LANGUAGE is True, scripts and Khmenglish are detected."""
    with patch.object(settings, "ENABLE_KHMER_LANGUAGE", True):
        # Khmer script
        assert detect_language("តើ 5 + 3 ស្មើនឹងប៉ុន្មាន?") == "khmer"
        # English
        assert detect_language("What is 5 + 3?") == "english"


@pytest.mark.asyncio
async def test_translate_to_khmer_deferred():
    """When ENABLE_KHMER_LANGUAGE is False, translate_to_khmer returns original text."""
    with patch.object(settings, "ENABLE_KHMER_LANGUAGE", False):
        orig = "First, let's identify the given numbers."
        result = await translate_to_khmer(orig)
        assert result == orig


def test_translate_endpoint_returns_501_when_disabled():
    """Calling /api/translate returns HTTP 501 with clean explanation when disabled."""
    with patch.object(settings, "ENABLE_KHMER_LANGUAGE", False):
        response = client.post(
            "/api/translate",
            json={"text": "Hello world", "target_lang": "km"}
        )
        assert response.status_code == 501
        data = response.json()
        assert "ReanMore v2.2" in data["detail"]
