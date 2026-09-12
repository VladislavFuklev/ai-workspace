#!/usr/bin/env bash
# Every quality check for both workspaces. Read-only: never rewrites a file.
# Use scripts/fix.sh to apply what is applicable automatically.
#
#   scripts/check.sh          run everything, report all failures
#   scripts/check.sh web      web only
#   scripts/check.sh api      API only
#
# Runs every check even after one fails, so a single run surfaces every problem,
# then exits non-zero if any failed.
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

target="${1:-all}"
failed=()

run() {
  local label="$1"; shift
  printf '\n\033[1m==> %s\033[0m\n' "$label"
  if "$@"; then
    printf '    \033[32mok\033[0m\n'
  else
    printf '    \033[31mFAILED\033[0m\n'
    failed+=("$label")
  fi
}

if [ "$target" = "all" ] || [ "$target" = "web" ]; then
  run "web · format"    pnpm --filter @ai-workspace/web format
  run "web · lint"      pnpm --filter @ai-workspace/web lint
  run "web · typecheck" pnpm --filter @ai-workspace/web typecheck
fi

if [ "$target" = "all" ] || [ "$target" = "api" ]; then
  # Run from apps/api: ruff's per-file-ignores and mypy's `files` are resolved
  # relative to the working directory, and mypy misreads the module layout from
  # the repository root.
  api() { (cd apps/api && uv run "$@"); }
  run "api · format"    api ruff format --check .
  run "api · lint"      api ruff check .
  run "api · types"     api mypy
  run "api · tests"     api pytest
fi

echo
if [ ${#failed[@]} -eq 0 ]; then
  printf '\033[32mAll checks passed.\033[0m\n'
  exit 0
fi
printf '\033[31m%d check(s) failed:\033[0m\n' "${#failed[@]}"
printf '  - %s\n' "${failed[@]}"
printf '\nMany of these are auto-fixable: scripts/fix.sh\n'
exit 1
