# Architecture Decision Records

Format:

## ADR-XXX — Title

### Context
What problem exists?

### Decision
What was chosen?

### Alternatives
What alternatives were considered?

### Consequences
What becomes easier/harder?

### Status
Accepted / Superseded / Rejected

---

## ADR-001 — Single monorepo for web, API and infrastructure

### Context
AI Workspace has a TypeScript frontend, a Python backend, shared infrastructure
definitions and a documentation system that acts as persistent project memory.
The repository must be decided before any scaffolding (task 0.2) happens.

### Decision
Use one git repository containing all deliverables: `apps/web`, `apps/api`,
`infra/`, `scripts/`, `docs/`.

### Alternatives
- **Separate repositories per app.** Rejected: cross-stack changes (an API contract
  change plus its frontend consumer) would need coordinated PRs across repos, and
  the documentation-as-memory system would have no single home.
- **Monorepo with a heavyweight tool (Nx, Bazel) from day one.** Rejected as
  premature; see ADR-003.

### Consequences
- Easier: atomic cross-stack commits, one CI pipeline, one place for docs and ADRs,
  one Docker Compose describing the whole system, one task = one commit.
- Harder: CI must scope jobs per app to stay fast; the repository has two unrelated
  dependency ecosystems (addressed by ADR-005).
- Independent release cadences per app are not available. Acceptable — both are
  deployed together.

### Status
Accepted — 2026-09-12

---

## ADR-002 — Workspace boundaries and layered internals

### Context
The master prompt specifies `app → features → components → lib` for the frontend
and `api → services → repositories → models` for the backend. These boundaries must
be fixed before code exists, otherwise the layering is decided accidentally by the
first file written.

### Decision
Top level: `apps/` (deployable units), `packages/` (shared TypeScript, empty for
now), `infra/` (compose and deployment), `scripts/`, `docs/`, `.claude/`.

Enforce a one-directional dependency flow inside each app:
- web: `app → features → components → lib`; features never import each other's
  internals.
- api: `api → services → repositories → models`; routers hold no business logic;
  all provider-specific AI code lives under `ai/` behind an interface.

`packages/` is created only when a second real consumer exists.

### Alternatives
- **Flat `web/` and `api/` at the repository root.** Rejected: no room for shared
  packages or infrastructure without later restructuring.
- **Create shared packages up front** (`packages/types`, `packages/config`).
  Rejected under rule 4 — speculative abstraction with a single consumer.

### Consequences
- Easier: predictable file placement, reviewable boundaries, layering violations are
  visible in imports and can later be lint-enforced (task 0.4).
- Harder: sharing types between web and API requires a deliberate step (generating
  a client from OpenAPI, or extracting a package) rather than a casual import.

### Status
Accepted — 2026-09-12

---

## ADR-003 — pnpm workspaces, no JS task runner yet

### Context
The JavaScript side needs a package manager and, eventually, a way to run tasks
across packages. Choosing a task runner before there is more than one package would
add configuration with nothing to orchestrate.

### Decision
Use **pnpm workspaces** (pnpm 11.x, available locally) with **Node.js 22 LTS**,
pinned via `.nvmrc` and `packageManager`/`engines` in task 0.2.

Do **not** adopt Turborepo/Nx now. Revisit when either condition holds:
1. `packages/` contains at least one shared package with more than one consumer, or
2. CI wall-clock time for the JS jobs becomes a practical problem.

Until then, root `package.json` scripts delegate to the workspace.

### Alternatives
- **npm workspaces.** Workable, but slower installs and weaker default protection
  against phantom dependencies.
- **Turborepo now.** Rejected: caching and pipeline orchestration solve a problem
  that does not exist with one JS app.
- **Yarn Berry.** Rejected: PnP adds tooling friction for no benefit here.

### Consequences
- Easier: fast, disk-efficient installs; strict node_modules layout catches
  undeclared dependencies early; trivially adding Turborepo later (it layers on top
  of pnpm workspaces without restructuring).
- Harder: cross-package task orchestration is manual until a runner is adopted.

### Status
Accepted — 2026-09-12

---

## ADR-004 — uv with a pinned Python 3.13 interpreter

### Context
The local system interpreter is Python 3.9, too old for the target backend stack.
Backend dependency management, virtual environments and interpreter version must be
reproducible across the developer machine, Docker and CI.

### Decision
Use **uv** for interpreter provisioning, dependency resolution and locking, with a
`pyproject.toml` per Python app and a committed `uv.lock`. Pin **Python 3.13** via
`.python-version` (task 0.2).

### Alternatives
- **Poetry.** Not installed locally, slower resolution, and does not manage the
  interpreter itself.
- **pip + requirements.txt + venv.** Rejected: weak transitive-dependency locking.
- **Python 3.12.** The conservative choice. Rejected because the entire target stack
  (FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, pgvector, psycopg) supports 3.13,
  and starting on the current stable release avoids a migration mid-project. If a
  required dependency turns out to lack 3.13 support, downgrading is a one-line
  change to `.python-version` plus a re-lock — this ADR is then superseded.

### Consequences
- Easier: identical, locked environments locally, in Docker and in CI; the stale
  system Python is irrelevant; installs are fast.
- Harder: contributors need uv installed (documented in 0.3); a dependency without
  3.13 wheels would need a source build or the fallback above.

### Status
Accepted — 2026-09-12

---

## ADR-005 — Two independent dependency graphs joined at the HTTP contract

### Context
A monorepo containing both TypeScript and Python invites a unified build tool that
drives both ecosystems. Such setups are fragile and hard to reproduce in CI.

### Decision
Keep the JS and Python dependency graphs fully independent. They meet at exactly
two seams:
1. **The HTTP contract** — the API's OpenAPI schema; the web app consumes the API
   over HTTP and never imports Python code.
2. **Docker Compose** — the local topology that runs both together.

CI runs web and API as separate jobs.

### Alternatives
- **A polyglot build tool (Bazel, Pants, Nx with Python plugins).** Rejected:
  operational cost far exceeds the benefit at this size.
- **Root-level scripts shelling into both ecosystems as the primary interface.**
  Partially adopted — convenience scripts are fine, but they are not a build graph
  and must not become a required layer.

### Consequences
- Easier: each ecosystem uses its native, well-documented tooling; CI jobs are
  independently cacheable and can fail independently; onboarding matches what any
  Next.js or FastAPI developer already expects.
- Harder: no compile-time type sharing across the boundary. Type safety at the seam
  must come from generating a typed client from OpenAPI (planned for task 1.7).

### Status
Accepted — 2026-09-12

---

## ADR-006 — Keep pnpm's dependency-cooldown gate

### Context
pnpm 11 applies a `minimumReleaseAge` cooldown by default: a package version
published very recently is not installed silently. This is a supply-chain control —
most malicious package releases are caught and yanked within hours or days of
publication, so a short waiting period removes a large share of the risk.

Installing Next.js 16.3.5 hit this gate, and pnpm recorded the affected versions
under `minimumReleaseAgeExclude` in `pnpm-workspace.yaml`.

### Decision
Keep the cooldown enabled at pnpm's default. Record deliberate exceptions in
`minimumReleaseAgeExclude` in `pnpm-workspace.yaml`, committed to git, so every
bypass is visible in review and in history.

Do not set `minimumReleaseAgeStrict`; the current behaviour (record the exclusion,
report it) is enough friction to notice without blocking work.

### Alternatives
- **Disable the cooldown** (`minimumReleaseAge: 0`). Rejected: removes a cheap,
  real supply-chain control for no gain other than installing brand-new releases a
  few days sooner.
- **A long custom cooldown.** Rejected: would routinely block legitimate framework
  upgrades and push contributors toward disabling it entirely.

### Consequences
- Easier: brand-new (and therefore least-vetted) package versions cannot enter the
  lockfile unnoticed; every exception is an auditable line in a committed file.
- Harder: adopting a just-published release requires an explicit exclusion entry.
  Contributors will encounter this and should be pointed at this ADR rather than
  reaching for a global override.
- The exclusion list grows over time and should be pruned when the listed versions
  are no longer recent.

### Status
Accepted — 2026-09-12
