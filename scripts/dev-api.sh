#!/usr/bin/env bash
# Run the API in development mode with auto-reload.
#
# Backing services come from scripts/dev-up.sh; this only runs the app.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root/apps/api"

exec uv run uvicorn ai_workspace_api.api.app:app --reload --host 127.0.0.1 --port "${API_PORT:-8000}"
