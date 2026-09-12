# Project State

## Status
Phase 0 in progress. Both workspaces install cleanly and the local backing
services run in Docker. No product features, no schema, no AI code.

## Current phase
Phase 0 — Product and engineering foundation

## Current task
None in progress.

## Last completed task
0.3 — Development environment and Docker (2026-09-12)

## Last session

Executed task 0.3 only.

Created `infra/docker-compose.yml` (PostgreSQL 18.6 + pgvector 0.8.6, Redis 8,
MinIO, plus a one-shot bucket initializer), `infra/api.Dockerfile` behind an
optional `api` profile, `infra/postgres/init/01-extensions.sql`,
`scripts/dev-up.sh`, `scripts/dev-down.sh` and `.env.example`.

Three environment findings shaped the design and are recorded as ADRs:
- Homebrew `postgresql@16` and `redis` already hold 5432/6379, so host ports are
  5433/6380/9000-9001 and configurable (ADR-008).
- `minio/minio` on Docker Hub no longer permits anonymous pulls; the image comes
  from quay.io (ADR-009).
- Apps run on the host, containers hold backing services (ADR-007).

Verified: all services healthy; `vector` extension present at 0.8.6 and vector
arithmetic works; Redis PING and SET/GET; bucket created; MinIO API and console
both HTTP 200; **data in all three services survived a full `down`/`up`**; all four
host ports reachable with Homebrew's services still running; API image builds,
imports every layer package, and runs as a non-root user; `down` left 0 containers
and 0 networks while keeping the 3 volumes; `.env` ignored and `.env.example`
tracked.

One bug found by running rather than reading: `docker compose up --wait` treats the
one-shot initializer's clean exit as a failure, which killed `dev-up.sh` under
`set -e`. The script now waits on the long-running services and checks the
initializer's exit code separately.

## Next action
Execute task **0.4 — Code quality tooling** per
`docs/tasks/0.4-code-quality-tooling.md`. Add Prettier and layering rules to the
web app, Ruff and a type checker to the API, resolve the deferred TypeScript
version question, and expose one check command per workspace.

## Known blockers
None.

## Known limitations
- The API has dependencies and a container image but no ASGI application; the
  `api` compose profile and `scripts/dev-api.sh` both report this. Task 2.1.
- Container Python is 3.13.15 vs 3.13.14 on the host — the base image ships a newer
  patch. Dependencies are locked; pin the base image by digest if it ever matters.
- `infra/postgres/init/` runs only on a fresh volume. Task 2.5 must also enable the
  `vector` extension in a migration for environments not built from this compose
  file.
- `.env` is read only by compose; typed application configuration is task 0.5.
- No formatter, Python linter or type checker yet (0.4); no tests (phase 12); no CI
  (0.6).
- The MinIO image is pinned to a September 2025 release; see ADR-009.

## Important notes
- Do not skip ahead.
- The roadmap and task files are the source of truth.
- Update this file after every completed task.
- Start a session with `./scripts/ctx.sh`, not by reading every document.
