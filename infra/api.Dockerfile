# Development image for the API. Production images are roadmap task 13.1.
#
# Build context is the repository root, so the lockfile and source both resolve:
#   docker compose -f infra/docker-compose.yml --profile api build api
#
# The interpreter is pinned to the same 3.13 the host uses (ADR-004), and uv comes
# from the base image so the container and the host resolve identically.
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim

# Faster and more predictable in a container: no bytecode surprises across layers,
# copy packages instead of hardlinking across the layer boundary, no version probe.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependencies first, in their own layer, so source edits do not re-resolve them.
COPY apps/api/pyproject.toml apps/api/uv.lock apps/api/.python-version ./
RUN uv sync --locked --no-install-project

COPY apps/api/src ./src
RUN uv sync --locked

ENV PATH="/app/.venv/bin:$PATH"

# Run as a non-root user. Uploaded files and AI output are untrusted input; the
# process handling them should not be root.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# The ASGI application is created in task 2.1. Until then this image is built and
# imported as a parity check rather than served.
CMD ["uvicorn", "--factory", "ai_workspace_api.api.app:create_app", "--host", "0.0.0.0", "--port", "8000"]
