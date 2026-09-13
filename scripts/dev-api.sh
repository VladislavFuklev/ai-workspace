#!/usr/bin/env bash
# Run the API in development mode with auto-reload.
#
# Backing services come from scripts/dev-up.sh; this only runs the app.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root/apps/api"

# --factory: the module exposes create_app rather than a module-level instance,
# so importing it does not require a complete environment.
exec uv run uvicorn --factory ai_workspace_api.api.app:create_app \
  --reload --host 127.0.0.1 --port "${API_PORT:-8000}"
