# Changelog

## Unreleased

### Tooling — documentation budgets (2026-09-12, not a roadmap task)

**Changed**
- `docs/DECISIONS.md` — compact ADR template (~25 lines). ADR-001..012 keep the
  older longer form; rewriting them would cost more than the inconsistency.
- `project-manager` skill — a per-file documentation budget and a one-fact-one-place
  rule; commit without a manual `check.sh` run, since the pre-commit hook is the gate.
- `token-economy` skill — leads with the measured costs: ~400 lines of docs per
  task, ~470 lines of state documents per session, ~13K of recoverable Bash output.

**Why**
- Measured across 0.1–0.4: documentation output, not running checks, dominates a
  task's cost, and most of it was the same facts restated in four files.

### 0.4 — Code quality tooling (2026-09-12)

**Added**
- `scripts/check.sh` — one read-only command for both workspaces: format, lint and
  types. Runs every check even after one fails, then exits non-zero. ~2.2s.
- `scripts/fix.sh` — applies automatic fixes, then re-runs the check.
- `.githooks/pre-commit` — runs the full suite before each commit; enabled by
  `scripts/bootstrap.sh` via `core.hooksPath`, skippable with `--no-verify`. No
  husky or lint-staged dependency.
- Web: Prettier 3.9.6 with Tailwind class sorting, `eslint-config-prettier`, and
  `eslint-plugin-boundaries` enforcing `app → features → components → lib`
  including the "no sibling feature" rule (ADR-012).
- API: Ruff 0.16.7 (lint + format) and mypy 2.3.1 in `strict` mode, configured in
  `apps/api/pyproject.toml` with rule sets enumerated deliberately (ADR-011).
- `.editorconfig`.
- ADR-010 (TypeScript 5 and ESLint 9 held back), ADR-011 (Ruff + mypy and the rule
  selection), ADR-012 (layering enforced by the linter).
- `docs/tasks/0.5-environment-configuration.md`.

**Changed**
- `apps/web/eslint.config.mjs` — Prettier compatibility plus the layering policy.
- `apps/web/next.config.ts` — reformatted by Prettier.
- `scripts/bootstrap.sh` — enables the git hooks and lists the new commands.
- `docs/ARCHITECTURE.md` — quality-gate section and toolchain rows.

**Notes**
- The TypeScript version question deferred in 0.2 is answered: `typescript-eslint`
  declares `typescript >=4.8.4 <6.1.0`, so TypeScript 7 is not usable while
  `eslint-config-next` depends on it. Separately, ESLint 9 is deprecated on npm but
  four plugins inside `eslint-config-next` cap their peer at `^9`, so ESLint 10 is
  not usable either. Both are registry facts, recorded in ADR-010.
- Every check was verified to fail on a deliberately broken file and then reverted;
  the layering rule was verified against three violation shapes and one legal case.

### 0.3 — Development environment and Docker (2026-09-12)

**Added**
- `infra/docker-compose.yml` — PostgreSQL 18.6 with pgvector 0.8.6, Redis 8 and
  MinIO, each with a healthcheck and a named volume, plus a one-shot container that
  creates the application bucket idempotently.
- `infra/api.Dockerfile` — development API image on `ghcr.io/astral-sh/uv:
  python3.13-trixie-slim`, dependencies in their own layer, running as a non-root
  user. Wired to an optional `api` compose profile, not started by default.
- `infra/postgres/init/01-extensions.sql` — enables the `vector` extension on first
  initialization.
- `scripts/dev-up.sh` / `scripts/dev-down.sh` — start with a health wait and an
  effective-port summary; stop with data preserved, or `--volumes` behind a
  confirmation prompt.
- `.env.example` — development-only defaults, committed; `.env` stays ignored.
- ADR-007 (apps on the host, services in containers), ADR-008 (non-default host
  ports), ADR-009 (MinIO from quay.io).
- `docs/tasks/0.4-code-quality-tooling.md`.

**Changed**
- `README.md` — local development quickstart.
- `docs/ARCHITECTURE.md` — local topology table, `infra/` layout, the PG 18 volume
  path caveat, and the toolchain table extended with the services.

**Notes**
- Host ports are 5433 / 6380 / 9000-9001 because Homebrew `postgresql@16` and
  `redis` already hold 5432 and 6379 on this machine; verified the stack runs
  alongside them.
- `minio/minio` on Docker Hub no longer allows anonymous pulls, so the image comes
  from quay.io.
- PostgreSQL 18 moved its cluster to `/var/lib/postgresql/18/docker`; the volume
  mount accounts for it, and persistence was verified across a full `down`/`up`.

### Tooling — context economy (2026-09-12, not a roadmap task)

**Added**
- `scripts/ctx.sh` — session-start context digest: HEAD commit, tree state, current
  phase and task, blockers, next action, the current phase's roadmap items, ADR
  titles and available task specs. ~35 lines in place of ~470 lines of documents.
- `.claude/skills/token-economy/SKILL.md` — when to read which document, and the
  `rtk` equivalent for each noisy command in this stack.

**Changed**
- `CLAUDE.md` — added a "Context economy" section pointing at both.

**Why**
- `rtk discover` measured 1.8% RTK adoption in a real session here: the global
  rewrite hook does not fire on compound commands, heredocs or pipelines, which is
  most of what this project runs. Calling `rtk` explicitly is the fix.

### 0.2 — Monorepo setup (2026-09-12)

**Added**
- Root pnpm workspace: private `package.json` with `packageManager` and `engines`,
  `pnpm-workspace.yaml` covering `apps/*` and `packages/*`, `.nvmrc` (Node 22),
  committed `pnpm-lock.yaml`.
- `apps/web` — Next.js 16.3.5 (App Router, Turbopack), React 19.2.8, TypeScript 5,
  Tailwind CSS 4, `src/` layout, `@/*` import alias. Scaffolded with `--empty`
  so no starter marketing UI was introduced.
- `apps/api` — uv project pinned to Python 3.13 with FastAPI 0.141.1 and
  uvicorn 0.52.4, `src/ai_workspace_api/` containing the eight layer packages
  (`api`, `services`, `repositories`, `models`, `schemas`, `workers`, `ai`,
  `core`), a `tests/` package, and a committed `uv.lock`.
- `scripts/bootstrap.sh` — verifies node/pnpm/uv are present, installs both
  ecosystems.
- `scripts/dev-api.sh` — runs uvicorn with reload; reports clearly that the ASGI
  app does not exist yet (task 2.1) instead of failing on an import error.
- ADR-006 — keep pnpm's `minimumReleaseAge` dependency-cooldown gate and record
  every bypass in a committed exclusion list.
- `docs/tasks/0.3-development-environment-docker.md`.

**Changed**
- `apps/web/package.json` — renamed to `@ai-workspace/web`, dropped the duplicate
  `packageManager` field, added a `typecheck` script.
- `apps/web/src/app/layout.tsx` — real product metadata instead of the scaffold's
  "Create Next App".
- `.gitignore` — added Next.js and Yarn PnP artifacts (`next-env.d.ts`, `.vercel/`,
  `.pnp*`) so the repository keeps a single ignore file.
- `pnpm-workspace.yaml` — absorbed the `allowBuilds` entries the scaffolder wrote
  to a nested workspace file.
- `docs/ARCHITECTURE.md` — repository and per-app layouts marked as created,
  toolchain table filled in with the versions actually installed.
- `docs/ROADMAP.md`, `docs/PROJECT_STATE.md` — 0.2 recorded as complete.

**Removed**
- `apps/web/pnpm-workspace.yaml`, `apps/web/.gitignore`, `apps/web/README.md` —
  nested files from the scaffolder that would have competed with the root ones.

**Notes**
- `apps/web/AGENTS.md` and `apps/web/CLAUDE.md` are generated and re-created by
  `next dev`; committed deliberately to keep the working tree clean.
- The typecheck script runs `next typegen` first, because Next.js 16 generates the
  global route types that `tsc` needs.
- No database, authentication or AI code was written.

### 0.1 — Repository initialization and architecture decision (2026-09-12)

**Added**
- Root `.gitignore` covering Node, Python, environment files, build output,
  local data and editor/OS artifacts.
- Placeholder `README.md` pointing at the `docs/` source of truth (the real
  README is task 14.6).
- `docs/tasks/0.2-monorepo-setup.md` — specification for the next task.
- ADR-001 … ADR-005 in `docs/DECISIONS.md`: monorepo, workspace boundaries and
  layering, pnpm workspaces with Node 22 LTS, uv with pinned Python 3.13, and
  independent JS/Python dependency graphs joined at the HTTP contract.

**Changed**
- `docs/ARCHITECTURE.md` — added repository topology, per-app internal layouts
  with explicit dependency direction, a toolchain baseline table, and the
  cross-language boundary.
- `docs/ROADMAP.md` — 0.1 marked complete.
- `docs/PROJECT_STATE.md` — records completion of 0.1 and the next action.

**Removed**
- `.claude/.DS_Store` and `docs/.DS_Store` untracked from git (they remain on disk
  and are now ignored).

**Notes**
- No application code, dependencies or infrastructure were created; those begin
  at task 0.2.

---

Project initialized.
