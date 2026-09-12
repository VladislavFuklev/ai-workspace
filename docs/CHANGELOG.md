# Changelog

## Unreleased

### 2.7 — Structured logging (2026-09-13)

- structlog: JSON outside local, console locally, with the standard library and
  uvicorn routed through the same processors.
- A request-id context variable so a line written deep in a repository carries it
  without a parameter; middleware assigns it, logs each request's outcome and
  duration, and returns it as `X-Request-ID`.
- A valid inbound id is honoured so a trace spans services; anything else is
  replaced, since the value is echoed in a header and written to logs.
- Credential-shaped keys are redacted.

### 2.6 — Health endpoints (2026-09-13)

- `/health/live` checks nothing external: a failure there means restart, and a
  liveness probe that touched the database would restart every replica in a loop
  during an outage.
- `/health/ready` checks Postgres and Redis concurrently with a timeout and
  returns 503 when either is down, naming which. The body carries a failure class,
  not a driver message — the endpoint is often unauthenticated.
- Both mounted off the versioned prefix: a probe URL should not change with the
  API version.

### 2.5 — Alembic migrations (2026-09-13)

- Alembic on the async template, reading the URL from the application's settings
  rather than `alembic.ini`, with `compare_type` and `compare_server_default` on.
- First revision creates the `vector` extension; its downgrade is a documented
  no-op because dropping it would take every vector column with it.
- CI runs `alembic upgrade head`, which also tests the migrations; the helper
  script from 2.3 is deleted.
- Tests: single head, every revision has a downgrade, and models do not drift from
  the schema — with a second test proving the drift check can fail.

### 2.4 — SQLAlchemy models (2026-09-13)

- `Base` with a constraint naming convention, plus `UUIDPrimaryKey` and
  `Timestamps` mixins. No domain tables — those belong to the phases that need them.
- The convention is the point: Postgres names unnamed constraints itself, in a
  form the metadata cannot predict, so a later migration has nothing to drop.

### 2.3 — Database connection (2026-09-13)

- `core/database.py`: one async engine per process opened in the lifespan and
  disposed on shutdown, one session per request from `SessionDep`.
- `session_scope` guarantees rollback and close; committing stays with the caller,
  which is the only place that knows where a unit of work ends.
- Integration tests against the real Postgres, marked and excluded from the
  default run, executed by `scripts/check.sh` with an explicit skip when the stack
  is down. CI gains a Postgres 18 + pgvector service.

### 2.2 — Configuration (2026-09-13)

- `service_name`, `api_prefix`, `cors_origins`, `max_request_body_bytes`; CORS
  wired from settings, with the middleware omitted entirely when no origin is set.
- A wildcard origin in production fails startup: browsers reject it alongside
  credentials, so the misconfiguration would otherwise surface as a browser error.
- Overlapped 0.5; scoped to the gap rather than redone.

### 2.1 — FastAPI application structure (2026-09-13)

- `create_app(settings)` factory plus the module-level `app` uvicorn imports; a
  lifespan for resources that outlive a request; a settings dependency so handlers
  receive configuration instead of importing a singleton.
- `/` identifies the service — deliberately not a health check (2.6).
- Interactive docs only outside production.
- `scripts/dev-api.sh` runs the server instead of reporting there is none.

### 1.10 — Reusable UI surface (2026-09-13)

- `(dev)` becomes a navigable reference: Tokens, Components, Forms, with an
  "internal" marker and the same active-state mechanism as the product nav.
- `(dev)/components` shows every shared component in the states it ships in,
  leading with empty, error and long content rather than the happy path.
- A page rather than Storybook: the app's own build, tokens and theme, with no
  second dependency tree to keep in step.

### 1.9 — Forms and validation (2026-09-13)

- `Field` (render prop, full ARIA wiring), `Input`, `Textarea`, `SubmitButton`,
  `FormError`, and `applyServerErrors` mapping a 422 back onto its fields.
- React Hook Form with a Zod resolver; one schema for client validation and the
  API payload.
- Working demo at `(dev)/forms` covering client validation, a server field error
  and a form-level failure.
- Fixes 1.7: `errorFromResponse` parsed the server's `detail` and discarded it.

### 1.8 — Query and cache architecture (2026-09-12)

- TanStack Query 5.102.8: `queryKeys` built centrally so an invalidation cannot
  miss its own query, and a hierarchy where a parent key covers its children.
- Retry follows `ApiError.isRetryable` — a 403 is not worth four attempts — with a
  ceiling of two and exponential backoff. Mutations never retry.
- `QueryProvider` creates the client in state, not at module scope, so server
  requests cannot share a cache.

### 1.7 — API client (2026-09-12)

- `createApiClient({ baseUrl })` with a bounded timeout, `credentials: "include"`,
  and Zod validation of every response body at the boundary.
- `ApiError` with a `kind` discriminator (network / timeout / http / parse), the
  server's code and request id, and a retryability rule.
- Configured instance in `lib/api/index.ts`; the transport itself imports no
  configuration, which is what makes it exercisable.

### 1.6 — Error, loading and empty states (2026-09-12)

- `Skeleton`, `SkeletonText`, `EmptyState`, `ErrorState`, `Spinner` in
  `components/ui/`; `error.tsx` and `(app)/loading.tsx` recomposed on them.
- Every destination has an empty state naming the action that fills it, with the
  action rendered disabled and labelled with the phase that enables it.

### 1.5 — Theme system (2026-09-12)

- Three-way `ThemeToggle` (light / dark / system) as a radiogroup, persisted in
  `localStorage` with every access guarded.
- Inline `<head>` script applies a stored choice before first paint.
- **Fixes a 0.8 bug:** the `prefers-color-scheme` path set `color-scheme` but not
  the dark tokens, so system dark rendered the light palette. Dark now works with
  no JavaScript, and `check-contrast.mjs` asserts the two dark blocks are identical.

### Fix — documentation drift check missed a stale phase (2026-09-12)

- `PROJECT_STATE.md` still said "Phase 0" four tasks into phase 1.
- `check-docs.sh` now asserts the recorded phase matches the phase of the next
  unticked roadmap task, and extracts task ids by pattern rather than awk field
  number — `- [ ] 1.5` has four fields where `- [x] 1.1` has three, which had the
  new check reporting `]` as the task id.

### 1.4 — Navigation (2026-09-12)

- `NAVIGATION_ITEMS` as the single source of destinations; `Navigation` renders
  them in both the sidebar and the drawer, closing the drawer on navigation.
- Active state from `useSelectedLayoutSegment`, marked with `aria-current="page"`.
- Route skeletons for `/documents`, `/assistant`, `/usage`, `/settings`.
- Duplicate "Main" landmark resolved: the drawer's `<nav>` is unnamed because the
  dialog already names the region.

### 1.3 — Design tokens (2026-09-12)

- Layering (`z-sticky` … `z-skip-link`), motion (two durations, two easings) and
  frame metrics (`h-header`, `w-sidebar`, `w-drawer`, `max-w-content`).
- Tailwind 4 has no `z` or `duration` namespace, so those are declared with
  `@utility`; the rest come from `@theme`.
- `prefers-reduced-motion` zeroes the duration tokens themselves.
- `check-contrast.mjs` now fails on a raw hex outside `globals.css`, with two
  documented exemptions.
- Overlapped 0.8; scoped to the gaps 1.2 exposed rather than redone.

### 1.2 — Responsive application layout (2026-09-12)

- `AppShell` client component: sidebar inline at `lg`+, native `<dialog>` drawer
  below, so focus trapping, `Escape` and an inert background come from the browser.
- `(app)/layout.tsx` stays a Server Component and composes it.
- `Sidebar` takes an `id`: it renders twice, and only the drawer instance may
  carry the one `aria-controls` points at.

### 1.1 — Next.js application shell (2026-09-12)

- Route groups: `(marketing)` owns `/`, `(app)` wraps the authenticated product at
  concrete routes such as `/workspace`, `(dev)` holds the token page.
- Root layout: title template, `themeColor` for both schemes, font variables.
- `(app)/layout.tsx`: header region, `<main>` landmark, skip link.
- Boundaries: `error.tsx` (Next 16 passes `retry`, not `reset`),
  `global-error.tsx` with inline styles, `not-found.tsx`, skeleton `loading.tsx`.
- `check-contrast.mjs` also asserts `viewport.themeColor` matches `--color-bg`.

### Fix — CI red on its first real run (2026-09-12)

- `ci.yml`: `NEXT_PUBLIC_API_URL` moved to job level — `next typegen` validates the
  environment, so typecheck needs it as much as build.
- `ci.yml`: `astral-sh/setup-uv@v10` does not exist; that action publishes major
  aliases only up to v7. Pinned `@v10.1.0`.
- `scripts/check-ci.sh` — runs the workflow locally: verifies every action ref
  resolves, then executes each step with its declared cwd and env and the root
  `.env` moved aside. Both failures were reintroduced and confirmed caught.

### 0.8 — Design system foundation (2026-09-12)

- Semantic design tokens in `globals.css` under Tailwind 4 `@theme`: neutral ramp,
  surfaces, text, one accent, three status colours, type scale, spacing, radii,
  two elevations. Complete dark set under `[data-theme="dark"]`.
- Inter and JetBrains Mono self-hosted through `next/font`; base layer sets a
  visible `:focus-visible` ring and honours `prefers-reduced-motion`.
- `/design` renders every token for review.
- `scripts/check-contrast.mjs` measures 20 pairings in both themes against WCAG
  AA and rejects malformed colour values. Part of `check.sh` and CI.

### 0.7 — Documentation system (2026-09-12)

- `docs/README.md` — index of which document answers which question.
- `docs/tasks/_TEMPLATE.md` — task spec and outcome template.
- `scripts/check-docs.sh` — fails on a roadmap entry contradicting its task file,
  a dead relative link, an ADR cited but never defined, or a project state that
  disagrees with the roadmap. Runs in 0.2s as part of `scripts/check.sh`.
- ADR-014 — the decision log stays in one file.

### 0.6 — CI baseline (2026-09-12)

- `.github/workflows/ci.yml` — parallel web and api jobs on push to `main` and
  every PR; concurrency cancellation; read-only token.
- Versions come from `.nvmrc`, `packageManager` and `.python-version`; installs
  use `--frozen-lockfile` / `--locked` so a stale lockfile fails.
- pnpm store and uv cache keyed on the lockfiles.
- Verified locally without a `.env`: both jobs pass, a lint error and a stale
  lockfile each fail. Not yet observed green on GitHub.

### 0.5 — Environment configuration (2026-09-12)

**Added**
- `ai_workspace_api/core/settings.py` — typed `pydantic-settings` object, the only
  module that reads the environment. Validated on construction; secrets are
  `SecretStr`; no secret has a working default.
- `apps/api/tests/` — the repository's first tests (18), covering a valid
  environment, six missing-variable cases and seven malformed-value cases.
- `apps/web/src/lib/env.ts` — Zod-validated public environment, checked at build
  time via `next.config.ts`; `load-root-env.ts` loads the monorepo-root `.env`.
- ADR-013 — one host-facing `.env`, overridden per container.

**Changed**
- `.env.example` — application configuration section, host-facing by design.
- `infra/docker-compose.yml` — the `api` service loads the root `.env` and
  overrides the three addresses that differ inside the cluster.
- `scripts/check.sh` — runs `pytest`.

**Notes**
- Verified from the same `.env`: on the host the API resolves `localhost:5433`, in
  the container `postgres:5432`. No secret appears in `.next/static`.

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
