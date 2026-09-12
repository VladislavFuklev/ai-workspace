#!/usr/bin/env bash
# Every quality check for both workspaces. Read-only: never rewrites a file.
# Use scripts/fix.sh to apply what is applicable automatically.
#
#   scripts/check.sh          run everything, report all failures
#   scripts/check.sh web      web only
#   scripts/check.sh api      API only
#   scripts/check.sh docs     documentation consistency only
#
# Runs every check even after one fails, so a single run surfaces every problem,
# then exits non-zero if any failed.
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

target="${1:-all}"
failed=()
skipped=()

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

if [ "$target" = "all" ] || [ "$target" = "docs" ]; then
  run "docs · consistency" ./scripts/check-docs.sh
fi

if [ "$target" = "all" ] || [ "$target" = "web" ]; then
  run "web · format"    pnpm --filter @ai-workspace/web format
  run "web · lint"      pnpm --filter @ai-workspace/web lint
  run "web · typecheck" pnpm --filter @ai-workspace/web typecheck
  run "web · contrast"  node scripts/check-contrast.mjs
  run "web · messages"  node scripts/check-messages.mjs
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

  # Integration tests need the compose stack. Skipping is reported, not silent:
  # a suite that quietly runs nothing is worse than one that fails.
  if [ -f .env ] && (set -a; . ./.env; set +a; nc -z localhost "${POSTGRES_PORT:-5433}" 2>/dev/null); then
    run "api · integration" bash -c 'set -a; . ./.env; set +a; cd apps/api && uv run pytest -m integration'
  else
    printf '\n\033[1m==> api · integration\033[0m\n'
    printf '    \033[33mskipped\033[0m — database unreachable; run scripts/dev-up.sh\n'
    skipped+=("api · integration")
  fi
fi

echo
if [ ${#skipped[@]} -gt 0 ]; then
  printf '\033[33m%d check(s) skipped:\033[0m %s\n' "${#skipped[@]}" "${skipped[*]}"
fi
if [ ${#failed[@]} -eq 0 ]; then
  printf '\033[32mAll checks passed.\033[0m\n'
  exit 0
fi
printf '\033[31m%d check(s) failed:\033[0m\n' "${#failed[@]}"
printf '  - %s\n' "${failed[@]}"
printf '\nMany of these are auto-fixable: scripts/fix.sh\n'
exit 1
