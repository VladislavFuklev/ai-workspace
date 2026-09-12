#!/usr/bin/env bash
# Run the API in development mode with auto-reload.
#
# The ASGI application does not exist yet; it is created in task 2.1. Until then
# this script only reports that, rather than failing with an import error.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root/apps/api"

app_module="ai_workspace_api.api.app:app"

if ! uv run python -c "import ai_workspace_api.api.app" >/dev/null 2>&1; then
  echo "The API application module does not exist yet (roadmap task 2.1)." >&2
  echo "Expected: apps/api/src/ai_workspace_api/api/app.py exposing 'app'." >&2
  exit 1
fi

exec uv run uvicorn "$app_module" --reload --host 127.0.0.1 --port 8000
