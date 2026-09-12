# Architecture

## Product
AI Workspace — multi-tenant AI document intelligence SaaS.

## Target topology

Web:
- Next.js App Router
- React
- TypeScript
- Tailwind
- accessible component system
- TanStack Query

API:
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

Data:
- PostgreSQL
- pgvector
- Redis

Storage:
- S3-compatible object storage

AI:
- provider abstraction
- embeddings
- RAG
- structured outputs
- tool calling
- agent orchestration

Workers:
- Python background jobs
- Redis-backed queue appropriate for the chosen architecture

## Repository topology

Single git repository, organized as a monorepo (see ADR-001, ADR-002).

Legend: **[exists]** created; **[reserved]** planned, created by the task noted.

```
ai-workspace/
├── apps/
│   ├── web/           [exists] Next.js App Router frontend
│   └── api/           [exists] FastAPI backend + workers
├── packages/          [reserved: on demand] shared TypeScript packages
├── infra/             [exists] Docker Compose, container and deploy config
├── scripts/           [exists] repo-level developer and CI helper scripts
├── docs/              [exists] persistent project memory
│   └── tasks/         [exists] per-task specifications
├── .claude/           [exists] Claude Code skills and commands
├── .gitignore         [exists] single ignore file for the whole repository
├── .nvmrc             [exists] Node 22
├── package.json       [exists] private workspace root
├── pnpm-workspace.yaml[exists]
├── pnpm-lock.yaml     [exists]
├── CLAUDE.md          [exists] agent operating rules
├── MASTER_PROMPT.md   [exists] full product specification
└── README.md          [exists] placeholder until task 14.6
```

`packages/` stays empty until a second genuine consumer exists. Shared code is extracted when duplication appears,
not in anticipation of it.

The repository has a single `.gitignore` at the root rather than one per app, so
there is one place to look when something is unexpectedly ignored.

### Web internals — `apps/web`

```
apps/web/
├── src/app/           [exists] App Router routes, layouts, route handlers
├── src/features/      feature modules (auth, organizations, documents, chat, usage)
├── src/components/    shared presentational components and primitives
├── src/lib/           API client, query client, validation, utilities
├── src/styles/        global styles and design tokens
├── tests/             unit and component tests
└── e2e/               Playwright specs
```

Only `src/app/` exists today. The remaining directories are created when the first
file that belongs in them is written (phase 1 onwards) rather than as empty
placeholders — the layering below is the contract, not the directory listing.

Route groups (no URL segment of their own):

| Group | Owns | Holds |
| --- | --- | --- |
| `(marketing)` | `/` | the public surface; landing page is task 14.1 |
| `(app)` | `/workspace`, `/documents`, `/assistant`, `/usage`, `/settings` | header, sidebar/drawer, `<main>`, skip link |
| `(dev)` | `/design`, `/components`, `/forms` | internal reference surfaces, not product |

Top-level `error.tsx`, `global-error.tsx` and `not-found.tsx` cover every route.
Next 16 passes `retry` to an error boundary, not `reset`, and generates
`LayoutRoutes = "/"` only — group layouts all type as `LayoutProps<"/">`.

Dependency direction: `app → features → components → lib`.
A feature may not import another feature's internals; shared code moves down a layer.

As of phase 1, `lib/` holds the environment (`env.ts`), the API client (`api/`) and
the query layer (`query/`); `components/` holds the shell (`layout/`), shared state
components (`ui/`) and form primitives (`form/`). `features/` is still empty — the
first feature arrives with documents in phase 5.

### API internals — `apps/api`

```
apps/api/
├── pyproject.toml     [exists] project metadata and dependencies
├── uv.lock            [exists] fully resolved dependency lock
├── .python-version    [exists] 3.13
├── src/ai_workspace_api/
│   ├── api/           HTTP routers, versioned (v1), request/response wiring only
│   ├── services/      business logic and orchestration
│   ├── repositories/  data access
│   ├── models/        SQLAlchemy ORM models
│   ├── schemas/       Pydantic schemas for boundaries and domain payloads
│   ├── workers/       background jobs
│   ├── ai/            provider abstraction: embeddings, chat, structured output, tools
│   └── core/          configuration, logging, error handling, security primitives
├── migrations/        [exists] Alembic revisions; URL comes from settings
└── tests/             [exists] unit and integration tests
```

Every layer package exists and is importable; all are empty apart from a docstring
stating the layer's responsibility. The FastAPI application itself is task 2.1.

Dependency direction: `api → services → repositories → models`.
Routers contain no business logic. Services never import routers. All
provider-specific AI code lives under `ai/` and is reached through an interface.

## Local development topology

`infra/docker-compose.yml` runs the backing services. The web app and the API run
on the host (ADR-007); host ports avoid the defaults so the stack coexists with
locally installed Postgres and Redis (ADR-008).

| Service | Image | Host port | In-cluster |
| --- | --- | --- | --- |
| PostgreSQL + pgvector | `pgvector/pgvector:pg18` (PG 18.6, vector 0.8.6) | 5433 | `postgres:5432` |
| Redis | `redis:8-alpine` | 6380 | `redis:6379` |
| MinIO (S3-compatible) | `quay.io/minio/minio` (ADR-009) | 9000, console 9001 | `minio:9000` |
| API (optional `api` profile) | built from `infra/api.Dockerfile` | 8000 | `api:8000` |

```
infra/
├── docker-compose.yml         backing services + optional api profile
├── api.Dockerfile             development API image (production image: task 13.1)
└── postgres/init/
    └── 01-extensions.sql      enables the vector extension on first init
```

Named volumes `postgres-data`, `redis-data` and `minio-data` persist across
`down`/`up`; `scripts/dev-down.sh --volumes` destroys them behind a confirmation.

Two connection contexts exist and must not be conflated: host processes use
`localhost` with the mapped port, containers use the service name with the internal
port. Task 0.5 makes this explicit in configuration.

Note on the Postgres image: PG 18 keeps its cluster in
`/var/lib/postgresql/18/docker`, so the volume mounts `/var/lib/postgresql`. This
differs from PG 17 and earlier, where it was `/var/lib/postgresql/data`.

## Toolchain baseline

| Concern | Choice | Pinned | ADR |
| --- | --- | --- | --- |
| Repository topology | monorepo | — | ADR-001 |
| JS runtime | Node.js 22 LTS | `.nvmrc`, root `engines` | ADR-003 |
| JS packages | pnpm 11 workspaces | root `packageManager`, `pnpm-lock.yaml` | ADR-003 |
| JS task runner | none yet | — | ADR-003 |
| Web framework | Next.js 16 (App Router), React 19, Tailwind 4 | `apps/web/package.json` | — |
| Python runtime | Python 3.13 | `apps/api/.python-version` | ADR-004 |
| Python packages | uv + `pyproject.toml` | `apps/api/uv.lock` | ADR-004 |
| API framework | FastAPI + uvicorn | `apps/api/pyproject.toml` | — |
| Dependency cooldown | pnpm `minimumReleaseAge` default | `pnpm-workspace.yaml` | ADR-006 |
| Local services | Docker Compose v5 | `infra/docker-compose.yml` | ADR-007 |
| Database | PostgreSQL 18.6 + pgvector 0.8.6 | compose | ADR-008 |
| Cache / queue | Redis 8 | compose | — |
| Object storage | MinIO, S3-compatible | compose | ADR-009 |
| Web format | Prettier 3.9 + Tailwind class sorting | `apps/web/.prettierrc.json` | — |
| Web lint | ESLint 9 + `eslint-config-next` | `apps/web/eslint.config.mjs` | ADR-010 |
| Layering enforcement | `eslint-plugin-boundaries` | `apps/web/eslint.config.mjs` | ADR-012 |
| Python lint + format | Ruff 0.16.7 | `apps/api/pyproject.toml` | ADR-011 |
| Python types | mypy 2.3.1, `strict` | `apps/api/pyproject.toml` | ADR-011 |
| Check entry point | `scripts/check.sh` / `scripts/fix.sh` | — | — |
| CI | GitHub Actions, two parallel jobs | `.github/workflows/ci.yml` | — |
| Local orchestration | Docker Compose | `infra/` (0.3) | — |

The local system Python (3.9) is not used; uv provisions and pins the interpreter.

## Quality gate

`scripts/check.sh` is the single command for both workspaces; it never rewrites a
file, runs every check even after one fails, and exits non-zero if any did.
`scripts/fix.sh` applies the automatic fixes and then re-runs the check.

| | web | api |
| --- | --- | --- |
| format | `prettier --check` | `ruff format --check` |
| lint | `eslint` | `ruff check` |
| types | `next typegen && tsc --noEmit` | `mypy --strict` |
| tests | phase 12 | `pytest` (units) + `pytest -m integration` (real Postgres) |

Plus `scripts/check.sh docs`: documentation consistency (`scripts/check-docs.sh`),
and `scripts/check-contrast.mjs`: WCAG AA for every token pairing in both themes.

## Design tokens

`apps/web/src/app/globals.css` is the whole design system: Tailwind 4 `@theme`
declares the light values and generates the utilities, `[data-theme="dark"]`
redefines every semantic token, and no token is defined only inside a media query.

Components reference semantic names (`surface`, `text-muted`, `border-strong`),
never the neutral ramp or a raw colour. Contrast is measured, not estimated.
`/design` renders the full set.

Tailwind scans source as text: a class composed at runtime (`` `bg-${token}` ``)
generates no CSS while building and typechecking cleanly. Write class names out
in full.

Tailwind 4 recognises a fixed set of `@theme` namespaces (colour, spacing, text,
radius, shadow, ease, …). There is **no `z` or `duration` namespace**: those
tokens are declared as variables and exposed with `@utility`. A `@theme` entry in
an unknown namespace silently generates nothing.

`check-contrast.mjs` enforces the system: WCAG AA for every pairing in both
themes, `viewport.themeColor` matching `--color-bg`, and no raw hex anywhere in
`apps/web/src` outside `globals.css`.

Python checks run with `apps/api` as the working directory: Ruff's per-file-ignores
and mypy's `files` resolve relative to the working directory, and mypy misreads the
module layout from the repository root.

`.githooks/pre-commit` runs the whole suite (~2s) before each commit; it is enabled
by `scripts/bootstrap.sh` via `core.hooksPath` and skippable with `--no-verify`.

The layering stated below is enforced by the linter for the web app (ADR-012), not
only by review. The API's layering is documented and reviewed; enforcing it in
Python is deferred until there is code in those packages to enforce it against.

## Configuration

One `.env` at the repository root serves both apps and Docker Compose. It is
**host-facing** (ADR-013): its addresses are `localhost` plus the published ports.
Compose overrides the three that differ for the `api` service, so the same file
works in both contexts.

| | reads it | how |
| --- | --- | --- |
| API | `ai_workspace_api/core/settings.py` | `pydantic-settings`, validated on construction; the only module that reads the environment |
| Web (public) | `src/lib/env.ts` | Zod; `NEXT_PUBLIC_*` only, validated at build time via `next.config.ts` |
| Web (root `.env`) | `src/lib/load-root-env.ts` | `@next/env` with `forceReload`; Next only looks in the app directory |
| Compose | `infra/docker-compose.yml` | `${VAR:-default}`, plus `env_file` for the `api` service |

Rules: no secret has a working default; secrets are `SecretStr` so they do not
appear in logs or tracebacks; nothing outside those modules reads the environment;
`NEXT_PUBLIC_*` is world-readable, so server-only values will go in a future
`src/lib/env.server.ts` guarded by `import "server-only"`.

Both settings modules locate the root `.env` by walking up to the `.git` directory,
because the apps are run from more than one working directory.

## Domain boundaries

Frontend:
- app
- features
- components
- lib

Backend:
- api
- services
- repositories
- models
- schemas
- workers

## Cross-language boundary

The JavaScript and Python dependency graphs are independent (ADR-005). They meet
at exactly two places:

1. **The HTTP contract** — the API's OpenAPI schema is the interface; the web app
   consumes it and does not import Python code.
2. **Docker Compose** — the local development topology that runs both.

Because nothing is shared at compile time, the web app validates every response
body with Zod inside `lib/api` before it reaches a component. A cast would only
move the failure somewhere harder to diagnose.

No shared build tool spans the two languages. CI runs them as separate jobs.

## Architectural principles

- explicit domain boundaries
- tenant isolation
- validate at boundaries
- database migrations
- provider abstraction for AI
- observable asynchronous processing
- tests around business-critical behavior
- avoid premature abstractions

This file must be updated when architecture materially changes.
