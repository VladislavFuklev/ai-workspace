# Project State

## Status
Phase 0 in progress. Both workspaces install cleanly, the local backing services
run in Docker, and a quality gate covers both languages. No product features.

## Current phase
Phase 0 — Product and engineering foundation

## Current task
None in progress.

## Last completed task
0.4 — Code quality tooling (2026-09-12)

## Last session

Executed task 0.4 only.

Added Prettier (with Tailwind class sorting) and `eslint-plugin-boundaries` to the
web app, Ruff and strict mypy to the API, `.editorconfig`, `scripts/check.sh` and
`scripts/fix.sh`, and a `.githooks/pre-commit` hook enabled by `bootstrap.sh`.

The version question deferred in 0.2 is answered from the registry rather than
assumed: `typescript-eslint` declares `typescript >=4.8.4 <6.1.0`, so TypeScript 7
is unusable while `eslint-config-next` depends on it; and four plugins inside
`eslint-config-next` cap their `eslint` peer at `^9`, so ESLint 10 is unusable even
though npm marks 9.x deprecated. Both recorded in ADR-010 with the condition that
lifts them.

Verified: the full suite passes in 2.2s; every check was made to fail on a
deliberately broken file and then reverted; Prettier is deterministic across two
runs; the layering rule rejects feature→sibling-feature, component→feature and
lib→component while allowing a feature to import its own internals; `fix.sh`
repairs both languages and reports what remains; the pre-commit hook aborted a bad
commit with HEAD unchanged; the API image rebuilds and runs the tools.

Two bugs found by running rather than reading: the first boundaries config used
deprecated v5 syntax, and mypy misreads the module layout when invoked from the
repository root — the Python checks now run with `apps/api` as the working
directory.

## Next action
Execute task **0.5 — Environment configuration** per
`docs/tasks/0.5-environment-configuration.md`. Add a typed `pydantic-settings`
object in `ai_workspace_api/core`, validate the web app's public environment, and
resolve the host-vs-container connection split flagged in ADR-007.

## Known blockers
None.

## Known limitations
- ESLint 9 is on the maintenance channel and marked deprecated by npm; blocked by
  `eslint-config-next`'s plugin set (ADR-010).
- API layering is documented and reviewed but not linter-enforced; revisit in
  phase 2 when those packages contain code.
- Prettier is scoped to `apps/web`; `docs/**` Markdown is deliberately unformatted.
- The API has dependencies, tooling and a container image but no ASGI application
  (task 2.1) and no configuration (task 0.5).
- Container Python is 3.13.15 vs 3.13.14 on the host; dependencies are locked.
- `infra/postgres/init/` runs only on a fresh volume; task 2.5 must also enable the
  `vector` extension in a migration.
- No tests anywhere yet — the first arrive with 0.5's settings object; the wider
  tooling is phase 12. No CI (0.6).

## Important notes
- Do not skip ahead.
- The roadmap and task files are the source of truth.
- Update this file after every completed task.
- Start a session with `./scripts/ctx.sh`, not by reading every document.
- Run `./scripts/check.sh` before committing; the pre-commit hook does it too.
