---
name: backend-quality
description: Standards for the FastAPI/Python backend in apps/api — layer boundaries, Pydantic validation at edges, SQLAlchemy and Alembic patterns, transaction and session scope, tenant isolation, authorization, structured logging and error handling. Use before writing or reviewing any code under apps/api.
---

# Backend Quality

Stack as installed: Python 3.13, FastAPI 0.141.x, Pydantic 2.x, uvicorn 0.52.x.
SQLAlchemy, Alembic, psycopg and Redis arrive in phase 2 and later.

## Layers — the boundary is the point

```
api → services → repositories → models
```

`apps/api/src/ai_workspace_api/` has one package per layer, plus `schemas`, `ai`,
`core`, `workers`. Each `__init__.py` states its responsibility. Read them.

| Layer | May import | Must never |
| --- | --- | --- |
| `api` | services, schemas, core | touch the DB session directly, hold business rules |
| `services` | repositories, schemas, ai, core | import `api`, build HTTP responses, know about `Request` |
| `repositories` | models, core | contain business rules or call AI providers |
| `models` | core | import anything above it |
| `ai` | schemas, core | leak vendor types past its own interface |

A router function should read as: validate input (Pydantic), resolve the caller and
tenant (dependency), call one service, map the result to a response schema. If a
router has an `if` on domain state, it is in the wrong layer.

**Why this is enforced hard here:** the product is multi-tenant. Authorization
lives in a place you can audit only if there is a place. Business logic scattered
across routers cannot be audited for tenant isolation, and phase 11 requires
exactly that audit.

## Validation at boundaries

Every value crossing into the system is untrusted: request bodies, query and path
params, headers, uploaded file contents and filenames, environment variables, AI
provider responses, and rows read from another tenant's reach.

- Request and response models are explicit Pydantic models, never `dict`.
- Set an explicit `response_model` so internal fields cannot leak by accident.
- Use `Field` constraints (`max_length`, `ge`, `le`, patterns) rather than
  validating in the handler body.
- Constrain collection sizes — an unbounded list in a request body is a DoS.
- Parse, don't validate: turn input into a typed object once, at the edge, and pass
  the typed object inward.
- Never trust a client-supplied `organization_id`. Derive the tenant from the
  authenticated principal, then check the resource belongs to it.

## Database

**Sessions and transactions.** One unit of work per request. The session is opened
and closed by a dependency; the service defines the transaction boundary; the
repository never commits. Nested commits inside repositories make partial writes
impossible to reason about.

**Queries.** No lazy loading across a response boundary — load what you need
explicitly (`selectinload`/`joinedload`) or you will ship N+1 queries. Every list
endpoint is paginated from the first version; no unbounded `SELECT *`.

**Tenant isolation.** Every tenant-scoped query filters on the organization. Do not
rely on a caller having filtered upstream. Prefer a single enforced path (a scoped
query helper or session-level filter) over remembering a `WHERE` clause in 40
places — a forgotten clause is a cross-tenant data leak, not a bug.

**Migrations.** Schema changes only through Alembic. Review generated migrations —
autogenerate misses renames, server defaults, enum changes and index intent.
Migrations must be reversible or explicitly documented as not. Never edit a
migration that has run anywhere but your machine.

**Indexes.** Add them with the query that needs them, in the same migration.
Foreign keys used in filters, and columns in `ORDER BY` for paginated lists.

## Errors

- A domain failure is a typed exception from the service layer, translated to HTTP
  once by a handler registered on the app — not `HTTPException` raised from deep
  inside business logic.
- Client-facing error bodies carry a stable machine-readable code and a safe
  message. No stack traces, SQL, file paths, or provider payloads.
- Log the detail server-side, return the safe version. These are different strings.
- 404 rather than 403 when revealing existence would itself leak tenant data.

## Logging

Structured, JSON in production. Every log line carries request id, and where
applicable user id and organization id. Never log secrets, tokens, full documents,
or raw prompt/completion bodies — log identifiers, sizes, durations, token counts
and outcomes. Phase 10 needs those numbers; phase 11 audits the absence of the
rest.

## Async

FastAPI is async. A blocking call inside an `async def` stalls the event loop for
every request on that worker. If a library is sync (a driver, an SDK, file or CPU
work), either use its async variant or push it off the loop. Long work does not
belong in a request at all — it belongs in `workers` (phase 5.7).

## Configuration

All configuration through one typed settings object in `core` (pydantic-settings),
validated at startup so a misconfigured deployment fails immediately and loudly.
No `os.environ` reads scattered through the code. No secrets with defaults that
work — a missing secret must fail, not silently run insecurely.

## Testability

Dependencies come in through FastAPI's dependency injection so tests can override
them. Services take their collaborators as arguments rather than importing
singletons. Integration tests run against a real Postgres (phase 12.5); do not
design around an in-memory substitute that behaves differently.

## Review checklist

- [ ] No business logic in a router
- [ ] Explicit request and response models; `response_model` set
- [ ] Tenant derived from the principal, never from the request body
- [ ] Every tenant-scoped query filtered by organization
- [ ] Transaction boundary in the service; no commit in a repository
- [ ] Pagination on every list endpoint
- [ ] Migration reviewed by hand, indexes included
- [ ] No blocking call in an async path
- [ ] Errors: typed inward, safe outward, detailed in logs
- [ ] No secret, token or document body in a log line
- [ ] Tests cover the authorization decision, not only the happy path
