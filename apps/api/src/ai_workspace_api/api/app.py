"""Application assembly.

`create_app` takes its settings rather than importing them, so a test builds an
app with an environment it controls and never touches the developer's `.env`.
The module-level `app` is what uvicorn imports.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_workspace_api import __version__
from ai_workspace_api.core.database import create_engine, create_session_factory
from ai_workspace_api.core.settings import Settings, get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown.

    Resources that must outlive a request — the database engine, the Redis pool —
    are opened here and stored on `app.state` from task 2.3 onwards. Opening them
    per request is how a service runs out of connections under load.
    """
    settings: Settings = app.state.settings
    logger.info("starting api", extra={"environment": settings.environment.value})

    engine = create_engine(settings)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    try:
        yield
    finally:
        # Dispose even if startup of a later resource failed, or the pool keeps
        # its connections until the process dies.
        await engine.dispose()
        logger.info("stopping api")


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()

    app = FastAPI(
        title="AI Workspace API",
        version=__version__,
        lifespan=lifespan,
        # Interactive docs are for humans in development. Task 2.10 decides what
        # production exposes; until then, closed.
        docs_url="/docs" if resolved.debug else None,
        redoc_url=None,
        openapi_url="/openapi.json" if resolved.debug else None,
    )
    # Read by the lifespan and by the settings dependency, so nothing below has to
    # import the module-level singleton.
    app.state.settings = resolved

    if resolved.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=resolved.cors_origins,
            # The session is a cookie (phase 3), so the browser must be told to
            # send it. This is why a wildcard origin is refused in production.
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
            expose_headers=["X-Request-ID"],
        )

    @app.get("/", tags=["meta"], summary="Service identity")
    async def root() -> dict[str, str]:
        """Confirms which service and which environment answered.

        Not a health check — that is task 2.6, and conflating the two means a load
        balancer keeps sending traffic to a process that cannot reach its database.
        """
        return {
            "service": resolved.service_name,
            "version": __version__,
            "environment": resolved.environment.value,
        }

    return app


app = create_app()
