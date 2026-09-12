# Project State

## Status
**Phase 0 complete.** Both workspaces install cleanly, the local backing services
run in Docker, and a quality gate covers both languages. No product features.

## Current phase
Phase 0 — Product and engineering foundation

## Current task
None in progress.

## Last completed task
0.8 — Design system foundation (2026-09-12)

## Last session

0.8 only, completing phase 0. See `docs/tasks/0.8-design-system-foundation.md`.

Beyond that file: a Tailwind class composed at runtime (`bg-${token}`) generates
no CSS, and both the build and the typechecker are happy about it. Grep the built
stylesheet for the utilities a page claims to use.

## Next action
Phase 1. Execute task **1.1 — Next.js application shell**; write
`docs/tasks/1.1-nextjs-application-shell.md` first.

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
- CI is written and verified locally but has never run on GitHub: the branch is
  ahead of `origin/main` and unpushed.
- No browser automation until 12.8, so UI review is limited to markup and
  generated CSS. `/design` deserves a human look.
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
