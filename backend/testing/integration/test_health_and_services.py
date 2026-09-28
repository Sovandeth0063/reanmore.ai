"""
Unit and Integration Tests for Microservice Monitoring, Resilient Clients,
Circuit Breakers, and Health Routes.
"""

import os
import sys
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
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

# pyrefly: ignore [missing-import]
from app.core.config import settings
# pyrefly: ignore [missing-import]
from app.infrastructure.clients import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitOpenException,
    RetryConfig,
    MathServiceClient,
    ScienceServiceClient,
    ServiceRegistry,
    ServiceClientFactory,
    get_service_registry,
    initialize_service_clients,
    solver_client,
)
# pyrefly: ignore [missing-import]
from app.infrastructure.health_checks import (
    HealthCheckService,
    ServiceHealthStatus,
    SystemReadiness,
    get_health_check_service,
    initialize_health_check_service,
    check_redis_health,
)
# pyrefly: ignore [missing-import]
from app.infrastructure.metrics import (
    record_query,
    record_service_error,
    record_circuit_trip,
    get_metrics_snapshot,
)
# pyrefly: ignore [missing-import]
from app.main import app


# ==========================================
# 1. Circuit Breaker & Retry Tests
# ==========================================

def test_circuit_breaker_state_transitions():
    cb = CircuitBreaker("TEST_SERVICE", failure_threshold=2, recovery_timeout=0.2, half_open_max_calls=2)
    assert cb.state == CircuitBreakerState.CLOSED

    # 1 failure - still closed
    cb.record_failure()
    assert cb.state == CircuitBreakerState.CLOSED
    cb.check_state()  # should not raise

    # 2nd failure - threshold reached -> OPEN
    cb.record_failure()
    assert cb.state == CircuitBreakerState.OPEN

    # Check state while OPEN -> raises CircuitOpenException
    with pytest.raises(CircuitOpenException):
        cb.check_state()

    # Wait for recovery timeout
    time.sleep(0.25)

    # Calling check_state after timeout transitions to HALF_OPEN
    cb.check_state()
    assert cb.state == CircuitBreakerState.HALF_OPEN

    # First successful trial in HALF_OPEN
    cb.record_success()
    assert cb.state == CircuitBreakerState.HALF_OPEN

    # Second successful trial in HALF_OPEN -> transitions back to CLOSED
    cb.record_success()
    assert cb.state == CircuitBreakerState.CLOSED


def test_circuit_breaker_manual_controls():
    cb = CircuitBreaker("TEST_SERVICE")
    assert cb.state == CircuitBreakerState.CLOSED

    cb.manual_trip()
    assert cb.state == CircuitBreakerState.OPEN

    cb.manual_reset()
    assert cb.state == CircuitBreakerState.CLOSED


def test_retry_config_backoff():
    cfg = RetryConfig(max_retries=3, initial_backoff_ms=100, max_backoff_ms=1000, exponential_base=2.0, jitter=False)
    assert cfg.get_backoff_sec(0) == 0.1
    assert cfg.get_backoff_sec(1) == 0.2
    assert cfg.get_backoff_sec(2) == 0.4


# ==========================================
# 2. Service Registry & Factory Tests
# ==========================================

def test_service_registry():
    registry = ServiceRegistry()
    math_client = ServiceClientFactory.create_math_client("http://math-service:9001")
    science_client = ServiceClientFactory.create_science_client("http://science-service:9002")

    registry.register("MATH", math_client)
    registry.register("SCIENCE", science_client)

    assert registry.get("MATH") == math_client
    assert registry.get("SCIENCE") == science_client
    assert len(registry.get_all_clients()) == 2


@pytest.mark.asyncio
async def test_service_client_keeps_configured_url_after_connection_failure():
    client = ServiceClientFactory.create_math_client("http://math-service:9001")
    client.retry_config = RetryConfig(max_retries=0)
    client.client.get = AsyncMock(side_effect=ConnectionError("service unavailable"))

    with pytest.raises(ConnectionError):
        await client.health()

    assert client.base_url == "http://math-service:9001"
    await client.close()


# ==========================================
# 3. Health Check Service Tests
# ==========================================

@pytest.mark.asyncio
async def test_health_check_service_computation():
    hcs = HealthCheckService(check_timeout_sec=1, failure_threshold=2)

    mock_math = AsyncMock()
    mock_math.health = AsyncMock(return_value={"status": "ok"})
    mock_math.get_circuit_breaker_status = MagicMock(return_value={"state": "CLOSED"})

    mock_science = AsyncMock()
    mock_science.health = AsyncMock(side_effect=Exception("Connection refused"))
    mock_science.get_circuit_breaker_status = MagicMock(return_value={"state": "OPEN"})

    clients = {"MATH": mock_math, "SCIENCE": mock_science}
    system_health = await hcs.check_all_services(clients)

    assert system_health.services["MATH"].status == ServiceHealthStatus.UP
    assert system_health.services["SCIENCE"].status == ServiceHealthStatus.DOWN
    assert system_health.overall_status == ServiceHealthStatus.DOWN
    assert system_health.readiness == SystemReadiness.NOT_READY
    assert len(hcs.get_error_history()) > 0


def test_redis_health_helper():
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    assert check_redis_health(mock_redis) == "up"

    mock_failing_redis = MagicMock()
    mock_failing_redis.ping.side_effect = Exception("Redis connection lost")
    assert check_redis_health(mock_failing_redis) == "down"

    assert check_redis_health(None) == "down"


# ==========================================
# 4. Metrics Recording Tests
# ==========================================

def test_metrics_collection():
    record_query("MATH", "SUCCESS", 0.05)
    record_service_error("MATH", "TIMEOUT")
    record_circuit_trip("SCIENCE")

    snapshot = get_metrics_snapshot()
    assert snapshot["total_queries"] >= 1
    assert "MATH:TIMEOUT" in snapshot["service_errors"]
    assert "SCIENCE" in snapshot["circuit_trips"]


# ==========================================
# 5. FastAPI Health Routes Integration Tests
# ==========================================

@pytest.mark.asyncio
async def test_api_health_endpoints():
    initialize_service_clients(settings)
    initialize_health_check_service()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. /health liveness probe
        res = await ac.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        # 2. /ready readiness probe
        res = await ac.get("/ready")
        assert res.status_code == 200
        assert "ready" in res.json()

        # 3. /status dependency probe
        res = await ac.get("/status")
        assert res.status_code == 200
        data = res.json()
        assert "dependencies" in data
        assert "redis" in data["dependencies"]

        # 4. /services monitoring probe
        res = await ac.get("/services")
        assert res.status_code == 200
        data = res.json()
        assert "services" in data
        assert "status" in data

        # 5. /services/{name}/circuit management action
        res = await ac.post("/services/MATH/circuit", json={"action": "trip"})
        assert res.status_code == 200
        assert res.json()["status"]["state"] == "OPEN"

        res = await ac.post("/services/MATH/circuit", json={"action": "reset"})
        assert res.status_code == 200
        assert res.json()["status"]["state"] == "CLOSED"
