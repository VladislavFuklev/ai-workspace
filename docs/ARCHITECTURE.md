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
│   ├── web/           [reserved: 0.2] Next.js App Router frontend
│   └── api/           [reserved: 0.2] FastAPI backend + workers
├── packages/          [reserved: on demand] shared TypeScript packages
├── infra/             [reserved: 0.3] Docker Compose, container and deploy config
├── scripts/           [reserved: 0.2] repo-level developer and CI helper scripts
├── docs/              [exists] persistent project memory
│   └── tasks/         [exists] per-task specifications
├── .claude/           [exists] Claude Code skills and commands
├── .gitignore         [exists]
├── CLAUDE.md          [exists] agent operating rules
├── MASTER_PROMPT.md   [exists] full product specification
└── README.md          [exists] placeholder until task 14.6
```

`packages/` stays empty until a second consumer genuinely exists. Shared code is
extracted when duplication appears, not in anticipation of it.

### Web internals — `apps/web` (layout fixed here, created in 0.2 / 1.1)

```
apps/web/
├── src/app/           App Router routes, layouts, route handlers
├── src/features/      feature modules (auth, organizations, documents, chat, usage)
├── src/components/    shared presentational components and primitives
├── src/lib/           API client, query client, validation, utilities
├── src/styles/        global styles and design tokens
├── tests/             unit and component tests
└── e2e/               Playwright specs
```

Dependency direction: `app → features → components → lib`.
A feature may not import another feature's internals; shared code moves down a layer.

### API internals — `apps/api` (layout fixed here, created in 0.2 / 2.1)

```
apps/api/
├── src/ai_workspace_api/
│   ├── api/           HTTP routers, versioned (v1), request/response wiring only
│   ├── services/      business logic and orchestration
│   ├── repositories/  data access
│   ├── models/        SQLAlchemy ORM models
│   ├── schemas/       Pydantic schemas for boundaries and domain payloads
│   ├── workers/       background jobs
│   ├── ai/            provider abstraction: embeddings, chat, structured output, tools
│   └── core/          configuration, logging, error handling, security primitives
├── migrations/        Alembic revisions
└── tests/             unit and integration tests
```

Dependency direction: `api → services → repositories → models`.
Routers contain no business logic. Services never import routers. All
provider-specific AI code lives under `ai/` and is reached through an interface.

## Toolchain baseline

| Concern | Choice | Pinned | ADR |
| --- | --- | --- | --- |
| Repository topology | monorepo | — | ADR-001 |
| JS runtime | Node.js 22 LTS | `.nvmrc`, `engines` (0.2) | ADR-003 |
| JS packages | pnpm workspaces | `packageManager` field (0.2) | ADR-003 |
| JS task runner | none yet | — | ADR-003 |
| Python runtime | Python 3.13 | `.python-version` (0.2) | ADR-004 |
| Python packages | uv + `pyproject.toml` | `uv.lock` (0.2) | ADR-004 |
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
