# Project State

## Status
**Phases 0, 1 and 2 complete.** Phase 0 complete: both workspaces, Docker services, quality gate, CI, docs system, design tokens. Both workspaces install cleanly, the local backing services
run in Docker, and a quality gate covers both languages. No product features.

## Current phase
Phase 3 — Authentication and identity

## Current task
None in progress.

## Last completed task
2.10 — OpenAPI documentation (2026-09-13)

## Last session

2.1 through 2.10 in one session, at the user's request — phase 2 complete. See the
individual task files.

Carried forward: the two discoveries that changed how tests are written here.
`httpx.ASGITransport` does not run the lifespan (use `running_app`), and FastAPI
0.141 does not flatten included routers into `app.routes` (assert routing by
request). Both cost a debugging cycle each.

## Next action
Phase 3. Execute task **3.1 — User model**; write `docs/tasks/3.1-user-model.md`
first. It is the first domain table, so it is also the first real exercise of the
2.4 base and the 2.5 autogenerate path.

## Known blockers
None.

## Known limitations
- ESLint 9 is on the maintenance channel and marked deprecated by npm; blocked by
  `eslint-config-next`'s plugin set (ADR-010).
- API layering is documented and reviewed but not linter-enforced; revisit in
  phase 2 when those packages contain code.
- Prettier is scoped to `apps/web`; `docs/**` Markdown is deliberately unformatted.
- The API has no domain endpoints yet: the v1 router is mounted and empty.
- No authentication, so OpenAPI declares no security schemes.
- No generated TypeScript client; `apps/web/src/lib/api` still hand-writes the
  response schemas the OpenAPI document could produce.
- `POSTGRES_*` and `DATABASE_URL` in `.env` are separate and must agree (ADR-013).
- Container Python is 3.13.15 vs 3.13.14 on the host; dependencies are locked.
- `infra/postgres/init/` runs only on a fresh volume; task 2.5 must also enable the
  `vector` extension in a migration.
- CI's first real run was red; both causes fixed and `scripts/check-ci.sh` added
  to catch that class before pushing. Needs one green run to confirm.
- No browser automation until 12.8, so UI review is limited to markup and
  generated CSS. The `(dev)` pages deserve a human look.
- No web test runner (12.1): the API client, retry policy and form wiring were
  each verified once, not continuously.
- `(dev)` is reachable in production builds; gating belongs with deployment.
- No theme switcher yet (1.5); `data-theme` must be set by hand.
- `ci.yml` duplicates the commands in `scripts/check.sh`; both must be updated
  together.
- Tests exist only for settings (18, via pytest, wired into `check.sh`). The wider
  test tooling is phase 12. No CI yet (0.6).

## Important notes
- Do not skip ahead.
- The roadmap and task files are the source of truth.
- Update this file after every completed task.
- Start a session with `./scripts/ctx.sh`, not by reading every document.
- Commit and let the pre-commit hook run `check.sh`; do not run it manually first.
- Documentation budgets per task are in the `project-manager` skill. Verification
  is worth spending on; restating the same facts in four files is not.
