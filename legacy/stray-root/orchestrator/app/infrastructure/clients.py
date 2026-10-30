"""
File: orchestrator/app/infrastructure/clients.py
Description: Centralized, resilient HTTP client layer for downstream solver microservices.
             Integrates connection pooling, exponential backoff retries, and custom circuit breakers.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger("orchestrator.clients")


class CircuitOpenException(Exception):
    """
    Exception raised when a request is made while the circuit breaker is in the OPEN state.
    """
    pass


class CircuitBreaker:
    """
    Custom Circuit Breaker to monitor the health of a downstream service.
    Transitions through CLOSED, OPEN, and HALF_OPEN states.
    """
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count = 0
        self.last_state_change = 0.0

    def record_success(self):
        """
        Record a successful service call.
        Resets failure count and closes the circuit if it was HALF_OPEN.
        """
        if self.state == "HALF_OPEN":
            logger.info(f"Circuit Breaker [{self.name}]: Service recovered. State transitioned from HALF_OPEN to CLOSED.")
            self.state = "CLOSED"
        self.failure_count = 0

    def record_failure(self):
        """
        Record a failed service call.
        Trips the circuit to OPEN if failure threshold is met in CLOSED/HALF_OPEN.
        """
        self.failure_count += 1
        logger.warning(f"Circuit Breaker [{self.name}]: Recorded failure. Consecutive failure count: {self.failure_count}/{self.failure_threshold}")
        
        if self.state in ("CLOSED", "HALF_OPEN") and self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_state_change = time.time()
            logger.error(
                f"Circuit Breaker [{self.name}]: Failure threshold reached. State transitioned to OPEN. "
                f"Fast-failing requests for the next {self.recovery_timeout} seconds."
            )

    def check_state(self):
        """
        Check the current state of the circuit breaker.
        Transitions OPEN to HALF_OPEN if the recovery timeout has elapsed.
        Raises CircuitOpenException if the circuit is OPEN.
        """
        if self.state == "OPEN":
            if time.time() - self.last_state_change > self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.last_state_change = time.time()
                logger.info(f"Circuit Breaker [{self.name}]: Recovery timeout elapsed. Transitioned to HALF_OPEN to test service health.")
            else:
                raise CircuitOpenException(f"Circuit for service '{self.name}' is currently OPEN (fast-failing).")


class ResilientSolverClient:
    """
    Resilient client wrapper managing a shared connection pool and separate circuit breakers
    for the MATH, PHYSICS, CHEMISTRY, and BIOLOGY microservices.
    """
    def __init__(self):
        # Configure the shared connection pool
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
        self.client = httpx.AsyncClient(limits=limits, timeout=httpx.Timeout(10.0, connect=3.0))

        # Separate circuit breakers for each solver service
        self.breakers = {
            "MATH": CircuitBreaker("MATH", failure_threshold=3, recovery_timeout=30.0),
            "PHYSICS": CircuitBreaker("PHYSICS", failure_threshold=3, recovery_timeout=30.0),
            "CHEMISTRY": CircuitBreaker("CHEMISTRY", failure_threshold=3, recovery_timeout=30.0),
            "BIOLOGY": CircuitBreaker("BIOLOGY", failure_threshold=3, recovery_timeout=30.0),
        }

    async def close(self):
        """
        Gracefully close the underlying HTTP connection pool.
        """
        logger.info("Closing ResilientSolverClient connection pool...")
        await self.client.aclose()

    async def request_with_retry(
        self,
        service_name: str,
        method: str,
        url: str,
        retries: int = 2,
        backoff_factor: float = 0.5,
        **kwargs
    ) -> httpx.Response:
        """
        Execute an HTTP request with exponential backoff retries and circuit breaker monitoring.
        """
        breaker = self.breakers.get(service_name)
        if not breaker:
            # Fallback for services without a configured circuit breaker
            return await self.client.request(method, url, **kwargs)

        # 1. Enforce Circuit Breaker state rules (raises exception if OPEN)
        breaker.check_state()

        last_exception = None
        for attempt in range(retries + 1):
            try:
                response = await self.client.request(method, url, **kwargs)
                
                # Check for HTTP status errors (5xx server errors represent service failures)
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"Server error returned: {response.status_code}",
                        request=response.request,
                        response=response
                    )
                
                # Success: record success to reset breaker state and return
                breaker.record_success()
                return response

            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_exception = e
                logger.warning(
                    f"Request to [{service_name}] failed on attempt {attempt + 1}/{retries + 1}: {e}"
                )
                
                # Apply exponential backoff before retrying
                if attempt < retries:
                    sleep_time = backoff_factor * (2 ** attempt)
                    await asyncio.sleep(sleep_time)

        # 2. If all retries are exhausted, record a failure in the breaker and propagate the exception
        breaker.record_failure()
        if last_exception:
            raise last_exception
        raise httpx.RequestError("Request failed after retries.")

    async def solve(self, subject: str, service_url: str, query: str, grade_level: str) -> Dict[str, Any]:
        """
        Query a solver microservice's /solve endpoint to get the hidden step-by-step solution path.
        """
        try:
            response = await self.request_with_retry(
                service_name=subject,
                method="POST",
                url=f"{service_url}/solve",
                json={"query": query, "context": {"grade_level": grade_level}}
            )
            if response.status_code == 200:
                return response.json()
        except CircuitOpenException as e:
            logger.error(f"Solver solve call skipped for {subject} (Circuit is OPEN): {e}")
        except Exception as e:
            logger.error(f"Solver solve call failed for {subject}: {e}")
        
        return {"success": False}

    async def validate(self, subject: str, service_url: str, student_attempt: str, expected_step: str) -> bool:
        """
        Query a solver microservice's /validate endpoint to verify correctness of a student step attempt.
        """
        try:
            response = await self.request_with_retry(
                service_name=subject,
                method="POST",
                url=f"{service_url}/validate",
                json={"student_attempt": student_attempt, "expected_step": expected_step}
            )
            if response.status_code == 200:
                return response.json().get("equivalent", False)
        except CircuitOpenException as e:
            logger.error(f"Solver validate call skipped for {subject} (Circuit is OPEN): {e}")
        except Exception as e:
            logger.error(f"Solver validate call failed for {subject}: {e}")
        
        return False


# Global singleton instance
solver_client = ResilientSolverClient()
