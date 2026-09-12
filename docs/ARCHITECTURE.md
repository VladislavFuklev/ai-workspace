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
