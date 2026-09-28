"""
Resilient Client Layer & Service Registry
Includes exponential backoff retries with jitter, 3-state circuit breakers,
dedicated service client classes, and centralized service registry lifecycle.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional

import httpx
from app.core.config import settings

logger = logging.getLogger("orchestrator.clients")


class CircuitOpenException(Exception):
    """Raised when an operation is attempted while circuit is OPEN."""
    pass


class CircuitBreakerState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class RetryConfig:
    """Exponential backoff retry configuration."""
    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff_ms: int = 200,
        max_backoff_ms: int = 2400,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.initial_backoff_ms = initial_backoff_ms
        self.max_backoff_ms = max_backoff_ms
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_backoff_sec(self, attempt: int) -> float:
        backoff = self.initial_backoff_ms * (self.exponential_base ** attempt)
        backoff = min(backoff, self.max_backoff_ms)
        if self.jitter:
            backoff += random.uniform(0, backoff * 0.1)
        return backoff / 1000.0


class CircuitBreaker:
    """
    3-State Circuit Breaker (CLOSED -> OPEN -> HALF_OPEN).
    """
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 2,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()
        self.last_failure_time: Optional[float] = None

    def get_state_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "uptime_seconds": round(time.time() - self.last_state_change, 2),
        }

    def check_state(self):
        """Enforce circuit breaker rules before making an outbound request."""
        if self.state == CircuitBreakerState.OPEN:
            time_since_failure = time.time() - self.last_state_change
            if time_since_failure >= self.recovery_timeout:
                logger.info(f"[{self.name}] Recovery timeout reached ({time_since_failure:.1f}s). Transitioning OPEN -> HALF_OPEN")
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                self.last_state_change = time.time()
            else:
                raise CircuitOpenException(
                    f"Circuit breaker is OPEN for {self.name}. Fast-failing. Recovery in {self.recovery_timeout - time_since_failure:.1f}s"
                )

        if self.state == CircuitBreakerState.HALF_OPEN and self.success_count >= self.half_open_max_calls:
            raise CircuitOpenException(f"Circuit breaker {self.name} is testing recovery (HALF_OPEN trial limit reached).")

    def record_success(self):
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            logger.info(f"[{self.name}] HALF_OPEN trial success ({self.success_count}/{self.half_open_max_calls})")
            if self.success_count >= self.half_open_max_calls:
                logger.info(f"[{self.name}] Service recovered! Transitioning HALF_OPEN -> CLOSED")
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.last_state_change = time.time()
        elif self.state == CircuitBreakerState.CLOSED:
            if self.failure_count > 0:
                self.failure_count = 0

    def record_failure(self, error: Optional[Exception] = None):
        self.failure_count += 1
        self.last_failure_time = time.time()
        logger.warning(f"[{self.name}] Service error recorded ({self.failure_count}/{self.failure_threshold}): {error}")

        if self.state in (CircuitBreakerState.CLOSED, CircuitBreakerState.HALF_OPEN) and self.failure_count >= self.failure_threshold:
            logger.error(f"[{self.name}] Failure threshold reached. Transitioning to OPEN.")
            self.state = CircuitBreakerState.OPEN
            self.last_state_change = time.time()

    def manual_reset(self):
        """Force reset circuit to CLOSED."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()
        logger.info(f"[{self.name}] Circuit manually reset to CLOSED.")

    def manual_trip(self):
        """Force trip circuit to OPEN."""
        self.state = CircuitBreakerState.OPEN
        self.last_state_change = time.time()
        logger.warning(f"[{self.name}] Circuit manually tripped to OPEN.")


class BaseServiceClient:
    """Base client with interface for microservice communication."""
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def health(self) -> Dict[str, Any]:
        raise NotImplementedError

    async def close(self):
        pass


class HttpxServiceClient(BaseServiceClient):
    """Resilient HTTP client with retry logic, circuit breaker, and health check support."""
    def __init__(
        self,
        base_url: str,
        name: str,
        timeout: float = 10.0,
        retry_config: Optional[RetryConfig] = None,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
    ):
        super().__init__(base_url, timeout)
        self.name = name
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
        self.client = httpx.AsyncClient(limits=limits, timeout=httpx.Timeout(timeout, connect=3.0))
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        return self.circuit_breaker.get_state_info()

    async def close(self):
        await self.client.aclose()

    async def _execute_with_retry(self, operation_name: str, operation_func: Callable[[], Any]) -> Any:
        self.circuit_breaker.check_state()
        last_exception = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                result = await operation_func()
                self.circuit_breaker.record_success()
                return result
            except (httpx.ConnectError, httpx.TimeoutException, asyncio.TimeoutError) as e:
                last_exception = e
                if attempt >= self.retry_config.max_retries:
                    break
                await asyncio.sleep(self.retry_config.get_backoff_sec(attempt))
            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code >= 500 or e.response.status_code == 429:
                    if attempt >= self.retry_config.max_retries:
                        break
                    await asyncio.sleep(self.retry_config.get_backoff_sec(attempt))
                else:
                    break
            except Exception as e:
                last_exception = e
                break

        self.circuit_breaker.record_failure(last_exception)
        if last_exception:
            raise last_exception
        raise httpx.RequestError(f"Operation {operation_name} failed.")

    async def health(self) -> Dict[str, Any]:
        async def _probe():
            url = f"{self.base_url}/health"
            resp = await self.client.get(url, timeout=3.0)
            resp.raise_for_status()
            return resp.json()
        return await self._execute_with_retry("HEALTH_CHECK", _probe)


class MathServiceClient(HttpxServiceClient):
    """Client for Math Microservice."""
    def __init__(self, base_url: str):
        super().__init__(base_url=base_url, name="MATH", timeout=10.0)

    async def solve(self, query: str, grade_level: str) -> Dict[str, Any]:
        payload = {"query": query, "subject": "MATH", "context": {"grade_level": grade_level}}
        async def _call():
            url = f"{self.base_url}/solve"
            resp = await self.client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
        return await self._execute_with_retry("MATH_SOLVE", _call)

    async def validate(self, student_attempt: str, expected_step: str) -> bool:
        payload = {"student_attempt": student_attempt, "expected_step": expected_step, "subject": "MATH"}
        async def _call():
            url = f"{self.base_url}/validate"
            resp = await self.client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json().get("equivalent", False)
        return await self._execute_with_retry("MATH_VALIDATE", _call)


class ScienceServiceClient(HttpxServiceClient):
    """Client for Science Microservice (Physics, Chemistry, Biology)."""
    def __init__(self, base_url: str):
        super().__init__(base_url=base_url, name="SCIENCE", timeout=15.0)

    async def solve(self, query: str, grade_level: str, subject: str = "SCIENCE") -> Dict[str, Any]:
        payload = {"query": query, "subject": subject, "context": {"grade_level": grade_level}}
        async def _call():
            url = f"{self.base_url}/solve"
            resp = await self.client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
        return await self._execute_with_retry("SCIENCE_SOLVE", _call)

    async def validate(self, student_attempt: str, expected_step: str, subject: str = "SCIENCE") -> bool:
        payload = {"student_attempt": student_attempt, "expected_step": expected_step, "subject": subject}
        async def _call():
            url = f"{self.base_url}/validate"
            resp = await self.client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json().get("equivalent", False)
        return await self._execute_with_retry("SCIENCE_VALIDATE", _call)


class HomeworkScannerClient(HttpxServiceClient):
    """Client for Homework OCR/VLM Microservice."""
    def __init__(self, base_url: str, timeout: float = 60.0):
        super().__init__(base_url=base_url, name="HOMEWORK_SCANNER", timeout=timeout)

    async def process_homework(
        self,
        file_bytes: bytes,
        filename: str,
        debug_crops: bool = False,
    ) -> Dict[str, Any]:
        files = {"file": (filename, file_bytes)}
        params = {"debug_crops": debug_crops}

        async def _call():
            url = f"{self.base_url}/process-homework"
            resp = await self.client.post(url, files=files, params=params)
            resp.raise_for_status()
            return resp.json()

        return await self._execute_with_retry("HOMEWORK_PROCESS", _call)


class ServiceRegistry:
    """Central registry of active microservice clients."""
    def __init__(self):
        self.clients: Dict[str, BaseServiceClient] = {}

    def register(self, name: str, client: BaseServiceClient):
        self.clients[name] = client
        logger.info(f"Registered microservice client: [{name}] ({client.base_url})")

    def get(self, name: str) -> Optional[BaseServiceClient]:
        return self.clients.get(name)

    def get_all_clients(self) -> Dict[str, BaseServiceClient]:
        return self.clients.copy()

    async def close_all(self):
        for name, client in self.clients.items():
            try:
                await client.close()
                logger.info(f"Closed client connection pool: [{name}]")
            except Exception as e:
                logger.warning(f"Error closing client [{name}]: {e}")


class ServiceClientFactory:
    """Factory for standard service client instantiation."""
    @staticmethod
    def create_math_client(base_url: str) -> MathServiceClient:
        return MathServiceClient(base_url=base_url)

    @staticmethod
    def create_science_client(base_url: str) -> ScienceServiceClient:
        return ScienceServiceClient(base_url=base_url)

    @staticmethod
    def create_homework_scanner_client(base_url: str) -> HomeworkScannerClient:
        return HomeworkScannerClient(base_url=base_url)


# Global Service Registry singleton
_service_registry: Optional[ServiceRegistry] = None

def get_service_registry() -> ServiceRegistry:
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry


def initialize_service_clients(cfg: Any = settings) -> ServiceRegistry:
    registry = get_service_registry()
    if getattr(cfg, "MATH_SERVICE_URL", None):
        registry.register("MATH", ServiceClientFactory.create_math_client(cfg.MATH_SERVICE_URL))
    if getattr(cfg, "SCIENCE_SERVICE_URL", None):
        registry.register("SCIENCE", ServiceClientFactory.create_science_client(cfg.SCIENCE_SERVICE_URL))
    if getattr(cfg, "HOMEWORK_SCANNER_URL", None):
        registry.register("HOMEWORK_SCANNER", ServiceClientFactory.create_homework_scanner_client(cfg.HOMEWORK_SCANNER_URL))
    return registry


# Backward-compatible adapter so existing LangGraph nodes keep working seamlessly
class ResilientSolverAdapter:
    async def solve(self, subject: str, service_url: str, query: str, grade_level: str) -> Dict[str, Any]:
        registry = get_service_registry()
        key = "MATH" if subject.upper() == "MATH" else "SCIENCE"
        client = registry.get(key)
        if client:
            try:
                if key == "MATH":
                    return await client.solve(query=query, grade_level=grade_level)
                else:
                    return await client.solve(query=query, grade_level=grade_level, subject=subject)
            except Exception as e:
                logger.error(f"Solver call failed via {key} client: {e}")
                return {"success": False}
        return {"success": False}

    async def validate(self, subject: str, service_url: str, student_attempt: str, expected_step: str) -> bool:
        registry = get_service_registry()
        key = "MATH" if subject.upper() == "MATH" else "SCIENCE"
        client = registry.get(key)
        if client:
            try:
                if key == "MATH":
                    return await client.validate(student_attempt=student_attempt, expected_step=expected_step)
                else:
                    return await client.validate(student_attempt=student_attempt, expected_step=expected_step, subject=subject)
            except Exception as e:
                logger.error(f"Validator call failed via {key} client: {e}")
                return False
        return False

    async def close(self):
        await get_service_registry().close_all()


solver_client = ResilientSolverAdapter()
