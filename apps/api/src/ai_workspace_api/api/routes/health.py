"""Liveness and readiness.

Two endpoints, because they answer different questions and an orchestrator acts
on them differently:

- **Liveness** — is this process wedged? A failure here restarts the container.
  It must therefore depend on *nothing external*: if liveness checked the
  database, an outage would restart every replica in a loop while the database
  was the thing that was down.
- **Readiness** — can this process serve traffic right now? A failure here takes
  it out of the load balancer and leaves it running, which is what you want while
  a dependency recovers.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Literal

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text

from ai_workspace_api import __version__
from ai_workspace_api.api.dependencies import SessionDep, SettingsDep

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

# A readiness probe that hangs is worse than one that fails: the orchestrator
# waits for its own timeout instead of acting.
CHECK_TIMEOUT_SECONDS = 2.0


class LivenessResponse(BaseModel):
    status: Literal["alive"]
    version: str


class DependencyStatus(BaseModel):
    ok: bool
    error: str | None = None


class ReadinessResponse(BaseModel):
    status: Literal["ready", "degraded"]
    checks: dict[str, DependencyStatus]


@router.get("/health/live", response_model=LivenessResponse, summary="Liveness probe")
async def live() -> LivenessResponse:
    """Answers if the event loop is running. Deliberately checks nothing else."""
    return LivenessResponse(status="alive", version=__version__)


async def _check_database(session: SessionDep) -> DependencyStatus:
    try:
        async with asyncio.timeout(CHECK_TIMEOUT_SECONDS):
            await session.execute(text("SELECT 1"))
    except Exception as error:
        # The reason is logged in full; the response carries only a short form,
        # since a readiness endpoint is often reachable without authentication.
        logger.warning("database readiness check failed", exc_info=error)
        return DependencyStatus(ok=False, error=type(error).__name__)
    return DependencyStatus(ok=True)


async def _check_redis(url: str) -> DependencyStatus:
    client: Redis = Redis.from_url(url)
    try:
        async with asyncio.timeout(CHECK_TIMEOUT_SECONDS):
            await client.ping()
    except Exception as error:
        logger.warning("redis readiness check failed", exc_info=error)
        return DependencyStatus(ok=False, error=type(error).__name__)
    finally:
        await client.aclose()
    return DependencyStatus(ok=True)


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    responses={503: {"model": ReadinessResponse, "description": "A dependency is unavailable"}},
)
async def ready(
    session: SessionDep, settings: SettingsDep, response: Response
) -> ReadinessResponse:
    """Checks every dependency a request would need, concurrently.

    Returns 503 when any of them is down — the status code is what the load
    balancer reads; the body is for a human looking at why.
    """
    database, redis = await asyncio.gather(
        _check_database(session), _check_redis(str(settings.redis_url))
    )
    checks = {"database": database, "redis": redis}
    healthy = all(check.ok for check in checks.values())

    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="ready" if healthy else "degraded", checks=checks)
