# Project State

## Status
Phase 1 in progress; phase 0 complete. Both workspaces install cleanly, the local backing services
run in Docker, and a quality gate covers both languages. No product features.

## Current phase
Phase 0 — Product and engineering foundation

## Current task
None in progress.

## Last completed task
1.3 — Design tokens (2026-09-12)

## Last session

1.2 and 1.3 in one session, at the user's request. See both task files.

Beyond those: Tailwind 4 has no `z` or `duration` theme namespace, so `@theme`
entries for them generate nothing — declare such utilities with `@utility`. And
1.3 overlapped 0.8; it was reinterpreted as the gaps 1.2 exposed rather than
redone. Later phase-1 tasks may overlap phase 0 the same way — check before
assuming a task is fresh work.

## Next action
Execute task **1.4 — Navigation**; write `docs/tasks/1.4-navigation.md` first.
It fills the `<nav>` region 1.2 left empty and resolves the duplicate "Main"
landmark noted there.

## Known blockers
None.

## Known limitations
- ESLint 9 is on the maintenance channel and marked deprecated by npm; blocked by
  `eslint-config-next`'s plugin set (ADR-010).
- API layering is documented and reviewed but not linter-enforced; revisit in
  phase 2 when those packages contain code.
- Prettier is scoped to `apps/web`; `docs/**` Markdown is deliberately unformatted.
- The API has dependencies, tooling, configuration and a container image but no
  ASGI application (task 2.1).
- `POSTGRES_*` and `DATABASE_URL` in `.env` are separate and must agree (ADR-013).
- Container Python is 3.13.15 vs 3.13.14 on the host; dependencies are locked.
- `infra/postgres/init/` runs only on a fresh volume; task 2.5 must also enable the
  `vector` extension in a migration.
- CI's first real run was red; both causes fixed and `scripts/check-ci.sh` added
  to catch that class before pushing. Needs one green run to confirm.
- No browser automation until 12.8, so UI review is limited to markup and
  generated CSS. `/design` and the error boundary deserve a human look.
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
