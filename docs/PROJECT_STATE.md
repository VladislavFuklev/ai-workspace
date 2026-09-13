# Project State

## Status
**Phases 0, 1 and 2 complete.** Phase 0 complete: both workspaces, Docker services, quality gate, CI, docs system, design tokens. Both workspaces install cleanly, the local backing services
run in Docker, and a quality gate covers both languages. No product features.

## Current phase
Phase 3 — Authentication and identity

## Current task
None in progress.

## Last completed task
3.3 — Login (2026-09-13)

## Last session

3.3 only. See `docs/tasks/3.3-login.md`.

Beyond that file: `is_active` is verified after the password on purpose — checking
it first makes a disabled account answer faster and leaks that the address exists.
Any future check on the user must go after the password comparison for the same
reason.

## Next action
Execute task **3.5 — Access and refresh token strategy**; write
`docs/tasks/3.5-tokens.md` first. Login currently returns a profile and nothing
is actually signed in. The web client sends `credentials: "include"` (task 1.7),
so a cookie session is the shape it already expects.

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
- The API's error codes have no catalogue entries, so a domain error shows the
  server's English fallback (ADR-015).
- Ukrainian copy has not been reviewed by a native speaker.
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
