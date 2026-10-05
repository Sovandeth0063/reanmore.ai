from contextlib import asynccontextmanager
import asyncio
import time
from fastapi import FastAPI, Request
from app.api.endpoints import router as api_router
from app.api.health_routes import health_router
from app.api.upload import upload_router
from app.api.llm_routes import llm_router
from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.database import init_db
from app.infrastructure.clients import initialize_service_clients, get_service_registry
from app.infrastructure.health_checks import (
    initialize_health_check_service,
    get_health_check_service,
    check_redis_health,
    check_qdrant_health,
    check_postgres_health,
)
from app.services.session import session_manager


# Periodic background health monitoring task
async def periodic_health_check():
    await asyncio.sleep(5.0)  # Initial grace period
    health_service = get_health_check_service()
    registry = get_service_registry()

    while True:
        try:
            clients = registry.get_all_clients()
            if clients:
                system_health = await health_service.check_all_services(clients)
                logger.info(
                    f"[HealthCheck] Overall: {system_health.overall_status.value.upper()} | "
                    f"Readiness: {system_health.readiness.value.upper()} | "
                    + " | ".join([f"{name}: {h.status.value.upper()} ({h.response_time_ms:.1f}ms)" for name, h in system_health.services.items()])
                )

            # Check core storage dependencies
            r_status = check_redis_health(session_manager.redis_client)
            q_status = await check_qdrant_health(settings.QDRANT_HOST, settings.QDRANT_PORT)
            p_status = await check_postgres_health(settings.DATABASE_URL)
            logger.info(f"[Dependencies] Redis: {r_status.upper()} | Qdrant: {q_status.upper()} | Postgres: {p_status.upper()}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"[HealthCheck] Periodic health monitor encountered error: {e}")

        await asyncio.sleep(float(settings.HEALTH_CHECK_INTERVAL_SEC))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Science Chatbot Orchestrator Gateway...")
    await init_db()

    # Initialize microservice clients registry
    logger.info("Initializing Microservice Client Registry...")
    initialize_service_clients(settings)

    # Initialize health check monitoring service
    logger.info("Initializing Health Check Service...")
    initialize_health_check_service(
        check_timeout_sec=settings.HEALTH_CHECK_TIMEOUT_SEC,
        failure_threshold=settings.CIRCUIT_FAILURE_THRESHOLD,
        degraded_response_time_ms=settings.DEGRADED_LATENCY_THRESHOLD_MS,
    )

    # Launch background health check task
    health_task = asyncio.create_task(periodic_health_check())
    logger.info("Orchestrator Gateway initialized successfully.")
    try:
        yield
    finally:
        logger.info("Shutting down Orchestrator Gateway...")
        health_task.cancel()
        try:
            await health_task
        except (asyncio.CancelledError, Exception):
            pass
        registry = get_service_registry()
        await registry.close_all()


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Science Chatbot - Orchestrator Gateway",
    description="Orchestrator Gateway with Socratic Tutoring, Microservice Monitoring, and Resilient Circuit Breaking.",
    version="2.0.0",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) for Frontend SPA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request duration middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(
        f"Incoming Request: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Duration: {process_time:.2f}ms"
    )
    return response

# Register API routers
app.include_router(health_router)
app.include_router(api_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(llm_router, prefix="/api")
