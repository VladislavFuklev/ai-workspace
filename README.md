# AI Workspace

Multi-tenant AI document intelligence platform: upload documents, process them
asynchronously, search semantically, and ask questions with cited answers.

> **Status:** Phase 0 — engineering foundation. No application code yet.
> This README is a placeholder; the full project README is roadmap task 14.6.

## Stack (target)

- **Web:** Next.js (App Router), React, TypeScript, Tailwind CSS, TanStack Query
- **API:** FastAPI, Pydantic, SQLAlchemy, Alembic
- **Data:** PostgreSQL + pgvector, Redis
- **Storage:** S3-compatible object storage
- **AI:** provider-abstracted embeddings, RAG, structured outputs, tool calling

## Local development

Requires Node 22, pnpm 11, uv and Docker.

```bash
cp .env.example .env      # development defaults; override ports if they clash
./scripts/bootstrap.sh    # install both workspaces
./scripts/dev-up.sh       # start PostgreSQL + pgvector, Redis, MinIO
pnpm dev                  # web app on http://localhost:3000
```

`./scripts/dev-down.sh` stops the services and keeps the data; add `--volumes` to
delete it. The API (`./scripts/dev-api.sh`) has no application yet — roadmap 2.1.

Host ports are non-standard on purpose so the stack coexists with a locally
installed Postgres or Redis: **5433** (PostgreSQL), **6380** (Redis), **9000/9001**
(MinIO and its console).

## Documentation

The `docs/` directory is the project's persistent source of truth.

| File | Purpose |
| --- | --- |
| [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) | Where the project currently stands |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Task sequencing |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Repository structure and system design |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Architecture decision records |
| [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | What changed, per task |
| [`docs/tasks/`](docs/tasks/) | Per-task specifications |
