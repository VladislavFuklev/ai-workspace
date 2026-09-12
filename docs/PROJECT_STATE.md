# Project State

## Status
Phase 0 in progress. Both workspaces exist and install cleanly. No product
features, no database, no AI code.

## Current phase
Phase 0 — Product and engineering foundation

## Current task
None in progress.

## Last completed task
0.2 — Monorepo setup (2026-09-12)

## Last session

Executed task 0.2 only, materializing the structure decided in 0.1.

Created:
- Root pnpm workspace: `package.json` (private, `packageManager`, `engines`),
  `pnpm-workspace.yaml`, `.nvmrc` (Node 22), `pnpm-lock.yaml`.
- `apps/web` — Next.js 16.3.5 App Router, React 19.2.8, TypeScript 5, Tailwind 4,
  `src/` layout, `@/*` alias. Scaffolded with `--empty`, so no starter marketing UI.
- `apps/api` — uv project on Python 3.13.14, FastAPI 0.141.1 + uvicorn 0.52.4,
  `src/ai_workspace_api/` with all eight layer packages, `tests/`, `uv.lock`.
- `scripts/bootstrap.sh`, `scripts/dev-api.sh`.
- ADR-006 — keep pnpm's dependency-cooldown supply-chain gate.

Checks run (all passing):
- `pnpm install` from a clean root
- `pnpm --filter @ai-workspace/web typecheck` from a clean state (no `.next/`)
- `pnpm --filter @ai-workspace/web lint`
- `pnpm --filter @ai-workspace/web build` — 3 static routes generated
- web dev server booted and served HTTP 200 with the correct `<title>`
- `uv sync` in `apps/api`
- `uv run python -c "import ai_workspace_api"` plus every layer package

## Next action
Execute task **0.3 — Development environment and Docker** per
`docs/tasks/0.3-development-environment-docker.md`. Add `infra/docker-compose.yml`
with PostgreSQL + pgvector, Redis and an S3-compatible object store, plus
development Dockerfiles and contributor setup documentation.

## Known blockers
None.

## Known limitations
- The API has dependencies but no application: no ASGI app, no routes, no config.
  `scripts/dev-api.sh` detects this and exits with a clear message. Task 2.1.
- ESLint arrived with the Next.js scaffold and is unconfigured beyond the default.
  Formatting, Python linting and type checking across both apps are task 0.4.
- No tests exist in either app. Test tooling is task 0.4 / phase 12.
- `apps/web/AGENTS.md` and `apps/web/CLAUDE.md` are generated and rewritten by
  `next dev`; they are committed deliberately so the tree stays clean.
- No environment configuration or `.env.example` yet — task 0.5.
- `packages/` and `infra/` do not exist yet; they are created when they have real
  content.

## Important notes
- Do not skip ahead.
- The roadmap and task files are the source of truth.
- Update this file after every completed task.
