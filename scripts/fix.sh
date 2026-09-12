#!/usr/bin/env bash
# Apply every automatic fix, then report what still needs a human.
#
#   scripts/fix.sh          both workspaces
#   scripts/fix.sh web|api  one of them
#
# This rewrites files. scripts/check.sh never does.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

target="${1:-all}"

if [ "$target" = "all" ] || [ "$target" = "web" ]; then
  echo "==> web · eslint --fix"
  pnpm --filter @ai-workspace/web lint:fix || true
  echo "==> web · prettier --write"
  pnpm --filter @ai-workspace/web format:write
fi

if [ "$target" = "all" ] || [ "$target" = "api" ]; then
  echo "==> api · ruff check --fix"
  (cd apps/api && uv run ruff check --fix .) || true
  echo "==> api · ruff format"
  (cd apps/api && uv run ruff format .)
fi

echo
echo "Fixes applied. Remaining problems (type errors and non-auto-fixable rules):"
exec "$repo_root/scripts/check.sh" "$target"
