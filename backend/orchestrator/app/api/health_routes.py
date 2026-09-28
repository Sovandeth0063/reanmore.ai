"""
Health & Microservice Management Endpoints
Dedicated endpoints for liveness, readiness, dependencies, and microservice management.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.config import settings
from app.infrastructure.health_checks import (
    get_health_check_service,
    check_redis_health,
    check_qdrant_health,
    check_postgres_health,
)
from app.infrastructure.clients import get_service_registry
from app.infrastructure import database as database_state
from app.infrastructure.metrics import get_metrics_snapshot
from app.services.session import session_manager

logger = logging.getLogger("orchestrator.health_routes")

health_router = APIRouter(tags=["health & management"])


@health_router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Liveness probe - immediate response with zero downstream I/O."""
    return {
        "status": "healthy",
        "service": "Science Chatbot Orchestrator",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@health_router.get("/ready")
async def readiness_check(request: Request) -> Dict[str, Any]:
    """Readiness probe - verifies core services and dependencies."""
    health_service = get_health_check_service()
    last_health = health_service.get_last_health()
    readiness = last_health.readiness.value if last_health else "ready"

    ready = readiness == "ready" and database_state.database_ready
    return {
        "ready": ready,
        "status": readiness if database_state.database_ready else "database_unavailable",
        "database": "up" if database_state.database_ready else "down",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@health_router.get("/status")
async def dependency_status() -> Dict[str, Any]:
    """Detailed dependency status (Redis, PostgreSQL, Qdrant)."""
    redis_status = check_redis_health(session_manager.redis_client)
    qdrant_status = await check_qdrant_health(settings.QDRANT_HOST, settings.QDRANT_PORT)
    postgres_status = await check_postgres_health(settings.DATABASE_URL)

    return {
        "service": "Science Chatbot Orchestrator",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "dependencies": {
            "redis": redis_status,
            "qdrant": qdrant_status,
            "postgres": postgres_status,
        },
        "metrics": get_metrics_snapshot(),
    }


@health_router.get("/services")
async def get_services_health() -> Dict[str, Any]:
    """Microservice status, latencies, error counters, and circuit breaker states."""
    health_service = get_health_check_service()
    registry = get_service_registry()

    # Trigger live check
    system_health = await health_service.check_all_services(registry.get_all_clients())
    return {
        **system_health.to_dict(),
        "recent_errors": health_service.get_error_history(limit=10),
    }


class CircuitActionRequest(BaseModel):
    action: str = "reset"  # "reset" or "trip"


@health_router.post("/services/{service_name}/circuit")
async def manage_circuit_breaker(service_name: str, payload: CircuitActionRequest) -> Dict[str, Any]:
    """Manual administration endpoint to reset or force-trip a service's circuit breaker."""
    registry = get_service_registry()
    client = registry.get(service_name.upper())

    if not client or not hasattr(client, "circuit_breaker"):
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found in registry.")

    breaker = client.circuit_breaker
    if payload.action.lower() == "reset":
        breaker.manual_reset()
    elif payload.action.lower() == "trip":
        breaker.manual_trip()
    else:
        raise HTTPException(status_code=400, detail="Action must be 'reset' or 'trip'.")

    return {
        "service": service_name.upper(),
        "action": payload.action,
        "status": breaker.get_state_info(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
