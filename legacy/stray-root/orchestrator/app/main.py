import asyncio
import time
import httpx
from fastapi import FastAPI, Request
from app.api.endpoints import router as api_router
from app.services.session import session_manager
from app.core.config import settings
from app.core.logging import logger
from app.infrastructure.database import init_db


app = FastAPI(title="Science Chatbot - Orchestrator Gateway")

# Register HTTP Middleware to track incoming request response times
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

app.include_router(api_router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "healthy"}

# Downstream health checking background task functions
async def check_service_health(name: str, url: str) -> bool:
    async with httpx.AsyncClient() as client:
        try:
            start_time = time.time()
            response = await client.get(url, timeout=3.0)
            duration = (time.time() - start_time) * 1000
            if response.status_code == 200:
                logger.info(f"Health Check: {name} is HEALTHY - Duration: {duration:.2f}ms")
                return True
            else:
                logger.warning(f"Health Check: {name} is UNHEALTHY - Status: {response.status_code} - Duration: {duration:.2f}ms")
                return False
        except Exception as e:
            logger.error(f"Health Check: {name} is UNREACHABLE - Error: {e}")
            return False

async def check_redis_health() -> bool:
    if not session_manager.redis_client:
        logger.error("Health Check: Redis is UNHEALTHY (client not initialized)")
        return False
    try:
        start_time = time.time()
        session_manager.redis_client.ping()
        duration = (time.time() - start_time) * 1000
        logger.info(f"Health Check: Redis is HEALTHY - Duration: {duration:.2f}ms")
        return True
    except Exception as e:
        logger.error(f"Health Check: Redis is UNHEALTHY - Error: {e}")
        return False

async def check_qdrant_health() -> bool:
    url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/readyz"
    async with httpx.AsyncClient() as client:
        try:
            start_time = time.time()
            response = await client.get(url, timeout=3.0)
            duration = (time.time() - start_time) * 1000
            if response.status_code == 200:
                logger.info(f"Health Check: Qdrant is HEALTHY - Duration: {duration:.2f}ms")
                return True
            else:
                logger.warning(f"Health Check: Qdrant is UNHEALTHY - Status: {response.status_code} - Duration: {duration:.2f}ms")
                return False
        except Exception as e:
            logger.error(f"Health Check: Qdrant is UNREACHABLE - Error: {e}")
            return False

async def periodic_health_check():
    # Wait initially for service startup
    await asyncio.sleep(5.0)
    while True:
        logger.info("-------------------- Downstream Dependencies Health Report --------------------")
        await check_redis_health()
        await check_qdrant_health()
        await check_service_health("Math Service", f"{settings.MATH_SERVICE_URL}/health")
        await check_service_health("Physics Service", f"{settings.PHYSICS_SERVICE_URL}/health")
        await check_service_health("Chemistry Service", f"{settings.CHEMISTRY_SERVICE_URL}/health")
        await check_service_health("Biology Service", f"{settings.BIOLOGY_SERVICE_URL}/health")
        logger.info("--------------------------------------------------------------------------------")
        await asyncio.sleep(30.0)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Orchestrator Gateway...")
    await init_db()
    # Spawn background task
    asyncio.create_task(periodic_health_check())

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Orchestrator Gateway...")
    from app.infrastructure.clients import solver_client
    await solver_client.close()


