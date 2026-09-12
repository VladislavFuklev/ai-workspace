# Changelog

## Unreleased

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
