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
