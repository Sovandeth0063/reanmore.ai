"""
File: backend/testing/integration/test_compose_health.py
Description: Configuration and topology qualification test for ReanMore deployment (Phase 6).
             - Verifies docker-compose.yml structure, 4-container topology, and network.
             - Verifies PostgreSQL 16 upgrade, Ollama continuous fallback (11434),
               and frontend (3000:80).
             - Verifies absence of obsolete standalone OCR container.
             - Verifies Pydantic settings schema alignment.
"""

import os
import sys
from pathlib import Path
import pytest
import yaml

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
from app.core.config import Settings


COMPOSE_FILE = Path(__file__).resolve().parent.parent.parent / "docker-compose.yml"


@pytest.fixture(scope="module")
def compose_config():
    assert COMPOSE_FILE.exists(), f"Missing docker-compose.yml at {COMPOSE_FILE}"
    with open(COMPOSE_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), "docker-compose.yml did not parse as a dictionary"
    return data


def test_compose_contains_4_reanmore_services(compose_config):
    """Architecture v2.1 Section 12.1: Exactly 4 services in the streamlined MVP."""
    services = compose_config.get("services", {})
    assert len(services) == 4, f"Expected 4 services, got {len(services)}: {list(services.keys())}"

    expected_containers = {
        "reanmore-postgres",
        "reanmore-ollama",
        "reanmore-orchestrator",
        "reanmore-frontend",
    }
    actual_containers = {s.get("container_name") for s in services.values() if isinstance(s, dict)}
    assert expected_containers.issubset(actual_containers), (
        f"Missing container names: {expected_containers - actual_containers}"
    )


def test_postgres_16_alpine_upgrade(compose_config):
    """Spec Section 11: Postgres must be upgraded to postgres:16-alpine."""
    services = compose_config.get("services", {})
    db = services.get("db", {})
    assert "postgres:16-alpine" in db.get("image", "")
    assert db.get("container_name") == "reanmore-postgres"


def test_pruned_distributed_services_absent(compose_config):
    """Architecture v2.1: Redis, Qdrant, MinIO are pruned from the Phase 1 MVP stack."""
    services = compose_config.get("services", {})
    for pruned in ("redis", "qdrant", "minio", "math-service", "science-service"):
        assert pruned not in services, f"Pruned service '{pruned}' must not be in docker-compose.yml"


def test_ollama_local_fallback_service(compose_config):
    """Spec Section 11: Ollama must be present on port 11434 for continuous local fallback."""
    services = compose_config.get("services", {})
    ollama = services.get("ollama", {})
    assert ollama.get("container_name") == "reanmore-ollama"
    ports = ollama.get("ports", [])
    assert any("11434:" in p for p in ports)


def test_frontend_container_configuration(compose_config):
    """Spec Section 11: Frontend web application mapped to port 3000:80."""
    services = compose_config.get("services", {})
    frontend = services.get("frontend", {})
    assert frontend.get("container_name") == "reanmore-frontend"
    ports = frontend.get("ports", [])
    assert any("3000:80" in p for p in ports)


def test_obsolete_ocr_service_removed(compose_config):
    """Spec Section 11 & Section 13: Standalone port 8000 OCR container removed."""
    services = compose_config.get("services", {})
    assert "ocr-service" not in services, "Obsolete standalone ocr-service must not be in docker-compose.yml"
    for s_name, s_cfg in services.items():
        if isinstance(s_cfg, dict):
            assert s_cfg.get("container_name") != "ocr-service"
            ports = s_cfg.get("ports", [])
            assert not any("8000:8000" in p for p in ports), f"Port 8000 still present on {s_name}"


def test_reanmore_network_driver(compose_config):
    """Verify unified bridge network is named reanmore-network."""
    networks = compose_config.get("networks", {})
    assert "reanmore-network" in networks
    assert networks["reanmore-network"].get("driver") == "bridge"


def test_pydantic_settings_alignment():
    """Verify Settings class loads MinIO and Gemini model tier settings correctly."""
    s = Settings(
        GEMINI_FAST_MODEL="gemini-2.0-flash",
        GEMINI_REASONING_MODEL="gemini-2.0-flash-thinking",
        GEMINI_VISION_MODEL="gemini-2.0-flash",
        MINIO_ENDPOINT="minio:9000",
        MINIO_ACCESS_KEY="minioadmin",
        MINIO_SECRET_KEY="minioadmin",
    )
    assert s.GEMINI_FAST_MODEL == "gemini-2.0-flash"
    assert s.GEMINI_REASONING_MODEL == "gemini-2.0-flash-thinking"
    assert s.MINIO_ENDPOINT == "minio:9000"
    assert s.QUOTA_DAILY == 10
    assert s.QUOTA_MONTHLY == 300
    assert s.AUTH_SECRET_KEY is not None
