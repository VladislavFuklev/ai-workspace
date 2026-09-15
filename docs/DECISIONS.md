# Architecture Decision Records

Format (keep an ADR to ~25 lines — every fact, no padding):

## ADR-XXX — Title

**Context.** The problem, in two or three sentences.

**Decision.** What was chosen, with the evidence it rests on.

**Rejected.** Each alternative and the one reason it lost.

**Revisit when** the condition that would change this.

**Consequence.** What becomes harder. What becomes easier is usually obvious.

Accepted / Superseded / Rejected — date

ADR-001 through ADR-012 use an earlier, longer template. They are not rewritten:
the churn would cost more than the inconsistency does.

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

---

## ADR-007 — Apps run on the host in development; containers hold backing services

### Context
Task 0.3 needed a local environment. The obvious options are to containerize
everything, or to containerize only what the apps depend on.

Both apps are developed on macOS, where bind-mounted source in a Linux VM has slow
filesystem events. Next.js Fast Refresh and uvicorn `--reload` both depend on those
events, so containerizing the apps directly degrades the inner loop that gets used
hundreds of times a day.

### Decision
`infra/docker-compose.yml` runs PostgreSQL + pgvector, Redis and MinIO. The web app
runs on the host via `pnpm dev`; the API runs on the host via `scripts/dev-api.sh`.

`infra/api.Dockerfile` exists and is wired to an **optional `api` compose profile**,
not started by default. It provides a container-parity check now and the basis for
the production image in task 13.1.

### Alternatives
- **Everything in compose.** Rejected: slow reload on macOS, plus an extra rebuild
  step between editing a file and seeing the result.
- **No API container at all until 13.1.** Rejected: the Dockerfile is cheap now,
  catches "works on my machine" dependency problems early, and CI will want it.

### Consequences
- Easier: fast native reload for both apps; contributors debug and profile with
  host tooling; backing services are still identical to everyone else's.
- Harder: the host must have Node, pnpm, uv and Docker rather than only Docker.
  `scripts/bootstrap.sh` checks for them and says what is missing.
- Two connection contexts exist: host processes reach services on `localhost` and
  the mapped ports, containers reach them by service name on the internal port.
  Task 0.5 must make this explicit in configuration rather than implicit.

### Status
Accepted — 2026-09-12

---

## ADR-008 — Non-default host ports for the development stack

### Context
The development machine already runs Homebrew `postgresql@16` on 5432 and `redis`
on 6379 as launch agents. Binding the compose services to those ports would either
fail to start or, worse, appear to work while the application talked to the wrong
database.

### Decision
Publish on non-default host ports by default: PostgreSQL **5433**, Redis **6380**,
MinIO **9000/9001**. Every port is overridable from the root `.env`
(`POSTGRES_PORT`, `REDIS_PORT`, `MINIO_PORT`, `MINIO_CONSOLE_PORT`), and compose
carries the defaults inline so the stack starts with no `.env` at all.

Container-to-container traffic keeps standard ports; only the host mapping shifts.

### Alternatives
- **Standard ports, ask contributors to stop conflicting services.** Rejected: it
  breaks other work on the machine, and the failure mode when someone forgets is
  connecting to the wrong database.
- **No published ports, exec into containers.** Rejected: apps run on the host
  (ADR-007) and need to reach the services.

### Consequences
- Easier: the stack coexists with anything already installed; verified with
  Homebrew's postgres and redis running throughout.
- Harder: every connection string and document must use the project's ports, and
  `psql`'s defaults are wrong here — pass `-p 5433`. `scripts/dev-up.sh` prints the
  effective ports after start, read from compose rather than reprinted from the
  defaults.

### Status
Accepted — 2026-09-12

---

## ADR-009 — Pull MinIO from quay.io, not Docker Hub

### Context
`minio/minio` on Docker Hub now returns `401 UNAUTHORIZED` for anonymous pulls,
verified against the registry API while writing task 0.3. An image that cannot be
pulled without credentials is unusable in a fresh clone and in CI.

### Decision
Pull MinIO and its client from **quay.io**, pinned by release tag:
`quay.io/minio/minio:RELEASE.2025-09-07T16-13-09Z` and
`quay.io/minio/mc:RELEASE.2025-08-13T08-35-41Z`. Both were confirmed to be
anonymously pullable and were pulled and run.

MinIO stays behind the storage abstraction (task 5.1), so nothing outside `infra/`
and configuration depends on it.

### Alternatives
- **Authenticate to Docker Hub.** Rejected: a credential requirement in the
  onboarding path and in CI, for a development dependency.
- **LocalStack, SeaweedFS, Garage.** Viable, and worth revisiting if MinIO's open
  releases stop. Not chosen now: MinIO is the closest behavioral match to S3 and
  the one contributors are most likely to recognize.

### Consequences
- Easier: a fresh clone can start the stack with no registry login.
- Harder: the pinned release is from September 2025 — MinIO's open-source release
  cadence has slowed, so this will age. The storage abstraction is what keeps
  replacing it a contained change; revisit at task 5.1 or if the image stops being
  maintained.

### Status
Accepted — 2026-09-12

---

## ADR-010 — Stay on TypeScript 5 and ESLint 9

### Context
Task 0.2 deferred a version question: the Next.js scaffold pins `typescript@^5`
while TypeScript **7.0.2** is published. Separately, installing dependencies in 0.4
surfaced that `eslint@9.39.5` is deprecated — npm's `latest` is **10.10.0**, and 9.x
is now the `maintenance` channel.

Both are tempting upgrades on a project meant to demonstrate current practice.
Neither is currently possible.

### Decision
Stay on **TypeScript 5** and **ESLint 9**, both pinned by what
`eslint-config-next@16.3.5` supports.

Evidence, read from the registry rather than assumed:

- `typescript-eslint@8.70.0` declares `peerDependencies.typescript: ">=4.8.4
  <6.1.0"`. It is a direct dependency of `eslint-config-next`, so TypeScript 7
  would break linting, not just type checking.
- `eslint-plugin-import`, `eslint-plugin-react`, `eslint-plugin-jsx-a11y` and
  `eslint-plugin-react-hooks` — all pulled in by `eslint-config-next` — cap their
  `eslint` peer range at `^9`. ESLint 10 would produce four peer conflicts inside
  Next.js's own config.

Revisit when `eslint-config-next` ships a plugin set declaring ESLint 10, and when
`typescript-eslint` widens its TypeScript range. Both are single-line changes plus
a re-lock; the check suite will show immediately whether they hold.

### Alternatives
- **Force the upgrades with overrides.** Rejected: overriding a peer range does not
  make the code compatible, it only silences the warning. A linter that
  intermittently misparses is worse than an older linter that works.
- **Drop `eslint-config-next`** and assemble the config by hand. Rejected: it
  supplies the Next.js and React Hooks rules that catch real App Router mistakes.

### Consequences
- Easier: the toolchain is internally consistent and the checks are trustworthy.
- Harder: the project runs an ESLint release that no longer receives support. This
  is a documented, dated limitation rather than an oversight, and the constraint
  belongs to Next.js's dependency set rather than to a choice made here.

### Status
Accepted — 2026-09-12

---

## ADR-011 — Ruff plus mypy for Python, with rule sets chosen explicitly

### Context
The API needed a linter, a formatter and a type checker that run identically
locally and in CI (task 0.6), with no network access and no interactive prompts.

### Decision
**Ruff 0.16.7** for both linting and formatting, and **mypy 2.3.1** in `strict`
mode for type checking. Both are dev dependencies of `apps/api`, locked in
`uv.lock`, configured in `apps/api/pyproject.toml`.

Rule sets are enumerated rather than enabled with `ALL`:
`E`/`W`, `F`, `I`, `UP`, `B`, `S`, `ASYNC`, `A`, `C4`, `DTZ`, `T20`, `SIM`, `PTH`,
`RUF`. Three of these were chosen for what this product specifically gets wrong:

- **`S`** (bandit) — the app handles uploaded files, tokens and credentials.
- **`ASYNC`** — a blocking call inside `async def` stalls the event loop for every
  concurrent request; this is the FastAPI failure mode that is hardest to spot in
  review.
- **`DTZ`** — naive datetimes in a multi-tenant, multi-region product produce
  corruption that surfaces months later. Every timestamp must be timezone-aware.

`E501` is disabled: line length belongs to the formatter.

### Alternatives
- **`select = ["ALL"]`** with a long ignore list. Rejected: every Ruff release then
  adds rules nobody chose, and the ignore list becomes the real configuration —
  read in reverse, which is harder.
- **`ty`** (Astral's type checker) instead of mypy. Rejected for now: at 0.0.80 it
  is pre-release, and a type checker that gates CI needs a stable contract. Worth
  revisiting once it reaches 1.0 — it would remove the one slow check.
- **pyright.** Viable and fast, but it needs Node in the Python toolchain, which
  cuts across ADR-005's separation of the two dependency graphs.
- **Black + isort + flake8.** Rejected: three tools and three configs for what Ruff
  does in one, considerably faster.

### Consequences
- Easier: the full check suite for both workspaces runs in about two seconds, which
  is what makes the pre-commit hook viable. `strict` mypy from the first file means
  types are never retrofitted onto an untyped codebase.
- Harder: `strict` mode requires annotating everything, including test helpers, and
  third-party packages without stubs must be declared rather than ignored silently
  (`disallow_any_unimported`). This is the intended cost.
- Ruff's `S` rules will flag legitimate patterns in tests; `tests/**` already
  ignores the assert and hardcoded-credential rules.

### Status
Accepted — 2026-09-12

---

## ADR-012 — Architectural layering enforced by the linter

### Context
`docs/ARCHITECTURE.md` states the frontend layering as `app → features →
components → lib`, with the additional rule that a feature may not import another
feature's internals. Documented conventions decay: the violation that matters is
the one added at 6pm by someone who has not read the document.

### Decision
Enforce the layering with `eslint-plugin-boundaries` in
`apps/web/eslint.config.mjs`, using `boundaries/dependencies` with
`default: "disallow"` and explicit allow policies per layer. The capture on the
feature element (`captured: { feature: "{{from.feature}}" }`) is what distinguishes
"a feature importing itself" from "a feature importing a sibling".

Violations are errors, not warnings, and the message points at
`docs/ARCHITECTURE.md`.

### Alternatives
- **Code review alone.** Rejected: it is the mechanism that already fails in every
  project that has this problem.
- **`no-restricted-imports` patterns.** Rejected: it cannot express "this feature
  but not that feature" relative to the importing file, which is the rule that
  matters most.
- **`eslint-plugin-import`'s `no-restricted-paths`.** Closer, but the same-type
  distinction is awkward, and `eslint-config-next` already pins that plugin's
  version.

### Consequences
- Easier: a layering violation fails locally, in the pre-commit hook and in CI,
  with a message naming the layers involved. New contributors learn the
  architecture from the error rather than from a document.
- Harder: genuinely shared code must be moved down a layer rather than imported
  sideways — which is the intended pressure, but it will occasionally require a
  refactor that a quick import would have avoided.
- The rule is configuration, not proof: it was verified against four deliberate
  violations and one legal case, not assumed to work.

### Status
Accepted — 2026-09-12

---

## ADR-013 — One host-facing `.env`, overridden per container

**Context.** ADR-007 left a trap: host processes reach services at `localhost` and
the published ports (5433/6380/9000), containers reach them by service name on the
internal port. The same setting has two correct values, and Compose, the API and
the web app all need configuration.

**Decision.** A single `.env` at the repository root, written for the **host**.
`infra/docker-compose.yml` gives the `api` service `env_file: ../.env` and then
overrides only `DATABASE_URL`, `REDIS_URL` and `S3_ENDPOINT_URL` with in-cluster
addresses. Verified both ways: on the host the API resolves `localhost:5433`, in
the container `postgres:5432`, from the same file.

Both apps locate the file by walking up to `.git` — `scripts/dev-api.sh` runs from
`apps/api`, and Next.js only looks in the app directory, so a plain relative path
would resolve against whichever directory happened to be current.

**Rejected.** *Container-facing `.env` with host overrides* — the host is the
common case and would carry the overrides. *One `.env` per app* — three files to
keep in step, and Compose needs the same values. *Only environment variables, no
file* — no working `git clone && start`.

**Revisit when** a second deployable needs different values, or secrets move to a
secret manager (phase 13).

**Consequence.** `POSTGRES_*` and `DATABASE_URL` both exist and must agree; a
password changed in one and not the other fails at connection time. Accepted over
the alternative of assembling the DSN from parts, which would diverge from managed
Postgres, where a URL is what you are given.

Accepted — 2026-09-12

---

## ADR-014 — Keep the decision log in one file

**Context.** `DECISIONS.md` is 515 lines across 13 ADRs and will roughly triple
over the remaining roadmap. Task 0.7 asked whether to split it into
`docs/decisions/NNN-*.md` with an index.

**Decision.** One file. `scripts/ctx.sh` indexes the titles, and reading a single
ADR is `sed -n '/## ADR-010/,/^## ADR-/p'` — as cheap as opening a small file.

**Rejected.** *One file per ADR* — its main benefit is avoiding merge conflicts in
a team, which does not apply here, and it would cost a migration plus a more
complex `ctx.sh` today.

**Revisit when** the file passes ~1500 lines, or more than one person edits it.

**Consequence.** Appends always touch the same file. Numbers are never reused, so
a superseded ADR stays in place and is marked, not deleted.

Accepted — 2026-09-12

---

## ADR-015 — Translation lives in the client; the API returns codes

**Context.** The product ships in English and Ukrainian (task 1.11). Failures
reach the user as text, and that text has to be in their language.

**Decision.** The API returns a stable machine-readable `code` with every failure
and never a translated message; the web app owns all wording. This is what task
2.8 already built — the envelope's `message` is a fallback for a code the client
does not recognise, not the string a user is meant to read.

**Rejected.** *Message catalogues in the API* — it would need the same
translations, kept in step with the frontend's, and would still get the tone
wrong because it cannot see the surrounding interface. *`Accept-Language` on API
requests* — moves the same problem to a header and makes responses uncacheable
per language for no gain.

**Revisit when** a non-browser client needs human-readable errors — a webhook
payload, or an email the API sends itself.

**Consequence.** Every new domain error needs a matching catalogue entry, or the
user sees the English fallback. Worth a check once the catalogue covers codes.

Accepted — 2026-09-13

---

## ADR-016 — The locale is in the URL

**Context.** next-intl can keep the locale in a cookie alone or in the path.

**Decision.** Always in the path: `/en/workspace`, `/uk/workspace`. The cookie
only remembers a choice for the next visit and for negotiating `/`.

**Rejected.** *Cookie only* — one URL would then serve two languages, which
breaks sharing a link, makes a CDN cache key wrong unless it varies on the
cookie, and makes "this page is broken" in a bug report ambiguous.

**Revisit when** the marketing site and the app diverge enough that the app could
drop prefixes while the public pages keep them for SEO.

**Consequence.** Every internal link must go through `@/i18n/navigation`, not
`next/link`, or it loses the prefix. An unknown prefix redirects into the
negotiated locale and 404s there rather than 404ing directly.

Accepted — 2026-09-13

---

## ADR-017 — Argon2id for password hashing

**Context.** Passwords need a slow, salted, memory-hard hash. The realistic
choices are Argon2id, scrypt and bcrypt.

**Decision.** Argon2id via `argon2-cffi`, at OWASP's baseline — 19 MiB memory,
two iterations, one lane. Memory cost is what makes GPU cracking expensive, so it
is the parameter to raise first. The hash is self-describing, so parameters can
change without a migration, and `check_needs_rehash` upgrades a stored hash
during a successful sign-in — the only moment the plaintext is available.

**Rejected.** *bcrypt* — a 72-byte input limit that silently truncates, and no
memory hardness. *scrypt* — sound, but Argon2 is the current recommendation and
the tuning guidance is better documented.

**Revisit when** OWASP's baseline moves, or sign-in latency becomes a complaint.
Raising `memory_cost` is a one-line change; existing hashes upgrade themselves.

**Consequence.** Each verification costs ~19 MiB and ~50 ms. That is deliberate,
and it means a sign-in endpoint must be rate-limited (10.5) or the hashing itself
becomes the denial of service.

Accepted — 2026-09-13

---

## ADR-018 — Registration does not reveal whether an address is taken

**Context.** A registration endpoint that answers "that address is already
registered" turns any list of addresses into a membership test — for a document
platform, that is "does this company use this product", answerable at scale by
anyone.

**Decision.** The same status and body whether or not the address exists. A
duplicate creates nothing and changes nothing; the caller cannot tell.

**Rejected.** *409 on a duplicate* — the common choice, and the leak itself.
*A CAPTCHA instead* — raises the cost of enumeration without removing it, and
the oracle is still there for a determined attacker.

**Revisit when** email delivery exists. The design is only half-built without it:
a new address should receive a welcome, an existing one a "someone tried to
register with your address" — which is what tells a legitimate person what
happened. Until then a duplicate registration is silently inert, and someone who
forgot they had an account gets no feedback. That is a real usability cost,
accepted deliberately rather than by omission.

**Consequence.** Registration is now cheap to call repeatedly and does hashing
work each time, so it needs rate limiting (10.5) more than most endpoints. Sign-in
(3.3) has to keep the same property, or the pair leaks what neither does alone.

Accepted — 2026-09-13

---

## ADR-019 — Short JWT access token, opaque rotating refresh token, both in cookies

**Context.** A session has to satisfy two things that pull apart: most requests
should not need a database read, and a session must be revocable.

**Decision.** Two tokens. A 15-minute JWT access token, verified with a signature
and nothing else. A 30-day opaque refresh token, stored **hashed**, checked
against a row. Both in `HttpOnly` cookies, `SameSite=Lax`; the refresh cookie's
`Path` is the refresh endpoint so it is not attached to every request.

Refresh **rotates**: each use issues a new token and retires the old one, within
a `family_id`. Presenting a retired token revokes the entire family — that is a
stolen token being replayed, and signing both parties out is the point.

The refresh token is hashed with SHA-256, not Argon2: it is 256 bits of
randomness, so there is no dictionary to slow down, and a slow hash would add
50 ms to every refresh for nothing.

**Rejected.** *Stateless JWT only* — cannot be revoked, so a compromised session
lives until it expires. *Server-side sessions only* — a database read on every
request, and no way to keep the hot path cheap later. *Tokens in
`localStorage`* — readable by script, so any XSS is a stolen session; `HttpOnly`
is the whole reason cookies win here.

**Revisit when** an access token needs to carry authorisation (phase 4). Roles in
a JWT go stale, so a revoked role would keep working until the token expires —
15 minutes is the ceiling on how wrong it can be, and that is a decision to make
consciously then.

**Consequence.** An access token cannot be revoked before it expires; ending a
session takes effect within 15 minutes for reads and immediately for refresh.
`SameSite=Lax` covers CSRF for the state-changing endpoints, so no separate CSRF
token — but any future `GET` that changes state would break that assumption.

Accepted — 2026-09-13

---

## ADR-020 — A provider email matching an existing account does not link automatically

**Context.** Someone signs in with Google using an address that already has a
password account here. Linking them is convenient and is what many products do.

**Decision.** Refuse, and tell them to sign in with their password and connect
the provider from settings. Linking on a matching address means anyone who can
get a provider to assert that address takes over the account behind it —
through a provider that does not verify emails, a corporate domain where an
address is reassigned after someone leaves, or a provider account compromise
that should only have cost the provider account.

`email_verified` from the provider is recorded but is not enough on its own: it
proves the provider believes the address, not that the person controls *this*
account.

**Rejected.** *Link when `email_verified` is true* — narrower, but still lets a
compromised or reassigned provider account inherit an account here. *Link
silently always* — the same, with no floor at all.

**Revisit when** there is a verified-domain concept (an organisation proving it
owns `@company.com`), which is a stronger claim than a provider's word.

**Consequence.** A user with both a password and a provider must sign in once
with the password to connect them. That is a real friction, and the alternative
is an account-takeover path.

Accepted — 2026-09-13

---

## ADR-021 — Tenant scope as a type, not a parameter

**Context.** Multi-tenant leaks do not come from someone deciding to skip a
check. They come from one query out of forty where the
`WHERE organization_id = ...` was forgotten, in a file nobody reviewed closely,
months later. Phase 11 has to audit this; the audit is only feasible if there is
one path to audit.

**Decision.** `TenantScope` is a frozen value produced *only* by
`MembershipService.resolve_scope`, which verifies a membership row. Tenant-scoped
repositories take one in their constructor. Forgetting to filter becomes
impossible rather than unlikely: a repository cannot be built without a scope, so
the mistake is a type error at the call site instead of a leak in production.

It is deliberately not a bare `uuid`. An id can be passed from anywhere including
a request body, which is the same leak with extra steps; a `TenantScope` can only
come from a check.

**Rejected.** *A `WHERE` clause per query, enforced by review* — the status quo
this exists to avoid. *PostgreSQL row-level security* — genuinely stronger, and
worth revisiting, but it moves the rule into the database where the application's
tests cannot see it, and it interacts badly with a connection pool that reuses
sessions across users. *A session-level filter* — invisible at the call site, so
the one query that needs to cross tenants (an admin report) becomes a silent
special case.

**Revisit when** something legitimately needs to read across tenants, or at 11.4
when the isolation audit runs — that is the point at which "is this actually
enforced everywhere" gets tested rather than asserted.

**Consequence.** Every tenant-scoped repository gains a constructor argument, and
a service that forgets it will not compile. A non-member resolving a scope gets
the same `NotFoundError` as a missing organisation, so a URL cannot be used to
discover which tenants exist.

Accepted — 2026-09-13

## ADR-022 — The tenant is in the object key, and the caller never writes one

**Context.** Storage sits outside the database, so `TenantScope` (ADR-021) stops
protecting it the moment a key is a string someone can influence. Two things go
wrong in practice: a key derived from an uploaded filename lets a name like
`../../other-org/x.pdf` escape a prefix, and a key stored in a row that points
somewhere else turns a wrong join into a download.

**Decision.** Keys are `org/{organization_id}/{kind}/{uuid}{extension}`, built
inside the storage layer from a `TenantScope`. The uploaded filename never
reaches the key — only an extension that matches `^\.[a-z0-9]{1,8}$` survives,
and the name itself lives in a database column, where it is text rather than a
path. Every read, delete and signature re-checks that the key starts with the
caller's own prefix and answers `NotFoundError` when it does not.

The interface is an abstract base class whose public methods hold the rules and
whose subclasses implement only transport. A `Protocol` would let a second
implementation satisfy the type while forgetting a rule.

**Rejected.** *A bucket per organisation* — stronger isolation, but bucket limits
and per-bucket policy make thousands of tenants an operational problem, and
creating one is a slow, failure-prone step in the signup path. *The filename in
the key* — readable in a listing, and the source of every traversal bug in this
class. *Trusting the row* — the row is the thing most likely to be wrong.

**Revisit when** a tenant needs their own bucket or KMS key for compliance
reasons, or when object counts make a flat per-organisation prefix slow to list.

**Consequence.** An object is attributable to one organisation from its key
alone, so a mistake is visible in a bucket listing rather than only in a join.
The original filename must be stored in the document row (task 5.4) or it is
lost. Changing the layout later means moving objects, so it is settled now.

Accepted — 2026-09-15
