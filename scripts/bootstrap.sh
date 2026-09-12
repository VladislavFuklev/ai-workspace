#!/usr/bin/env bash
# Install dependencies for both workspaces from a clean checkout.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

require() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "error: '$1' is required but not installed. $2" >&2
    exit 1
  }
}

require node "Install Node.js 22 LTS (see .nvmrc)."
require pnpm "Install pnpm 11: corepack enable pnpm"
require uv   "Install uv: https://docs.astral.sh/uv/getting-started/installation/"

echo "==> Installing JavaScript workspace dependencies"
pnpm install

echo "==> Installing Python API dependencies"
uv sync --project apps/api

echo
echo "Done. Next:"
echo "  pnpm dev              # web dev server on http://localhost:3000"
echo "  scripts/dev-api.sh    # API dev server on http://localhost:8000"
