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
├── infra/             [reserved: 0.3] Docker Compose, container and deploy config
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

`packages/` and `infra/` stay empty until they have real content; `packages/` waits
for a second genuine consumer. Shared code is extracted when duplication appears,
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

Dependency direction: `app → features → components → lib`.
A feature may not import another feature's internals; shared code moves down a layer.

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
├── migrations/        [reserved: 2.5] Alembic revisions
└── tests/             [exists] unit and integration tests
```

Every layer package exists and is importable; all are empty apart from a docstring
stating the layer's responsibility. The FastAPI application itself is task 2.1.

Dependency direction: `api → services → repositories → models`.
Routers contain no business logic. Services never import routers. All
provider-specific AI code lives under `ai/` and is reached through an interface.

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
| Local orchestration | Docker Compose | `infra/` (0.3) | — |

The local system Python (3.9) is not used; uv provisions and pins the interpreter.

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
