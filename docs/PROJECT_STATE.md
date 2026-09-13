# Project State

## Status
**Phases 0–3 complete; phase 4 in progress (4.1–4.4 done).** Both workspaces,
Docker services, quality gate, CI, design system and i18n (en/uk); authentication
end to end; organisations, memberships, roles and permission-guarded endpoints.

## Current phase
Phase 4 — Organizations and RBAC

## Current task
None in progress.

## Last completed task
4.4 — Permissions (2026-09-13)

## Last session

4.1–4.4. Organisations, memberships, the role/permission table and the first
tenant-scoped HTTP endpoints. See those task files and ADR-021.

Worth carrying forward: `require_permission(...)` returns the `Depends` itself,
so a guarded route reads `Annotated[TenantScope, require_permission(X)]` and the
check lives in the signature. A non-member and a missing organisation return the
same 404; a member missing a permission gets 403 naming it.

## Next action
Execute task **4.5 — Organization switching**; write
`docs/tasks/4.5-organization-switching.md` first. The API identifies the tenant
by a path slug, so switching is a frontend concern: which organisation the app
shell is currently showing, and how that survives a reload.

## Known blockers
None.

## Known limitations
- ESLint 9 is on the maintenance channel and marked deprecated by npm; blocked by
  `eslint-config-next`'s plugin set (ADR-010).
- Prettier is scoped to `apps/web`; `docs/**` Markdown is deliberately unformatted.
- No generated TypeScript client; `apps/web/src/lib/api` still hand-writes the
  response schemas the OpenAPI document could produce.
- The API's error codes have no catalogue entries, so a domain error shows the
  server's English fallback (ADR-015).
- Ukrainian copy has not been reviewed by a native speaker.
- `POSTGRES_*` and `DATABASE_URL` in `.env` are separate and must agree (ADR-013).
- Container Python is 3.13.15 vs 3.13.14 on the host; dependencies are locked.
- `infra/postgres/init/` runs only on a fresh volume; task 2.5 must also enable the
  `vector` extension in a migration.
- No browser automation until 12.8, so UI review is limited to markup and
  generated CSS. The `(dev)` pages deserve a human look.
- No web test runner (12.1): the API client, retry policy and form wiring were
  each verified once, not continuously.
- `(dev)` is reachable in production builds; gating belongs with deployment.
- No theme switcher yet (1.5); `data-theme` must be set by hand.
- API layering is documented and reviewed but not linter-enforced.
- Neither organisation list is paginated, and no endpoint yet changes a role or
  removes a member over HTTP — that is 4.6.
- `ci.yml` duplicates the commands in `scripts/check.sh`; both must be updated
  together.

## Important notes
- Do not skip ahead.
- The roadmap and task files are the source of truth.
- Update this file after every completed task.
- Start a session with `./scripts/ctx.sh`, not by reading every document.
- Commit and let the pre-commit hook run `check.sh`; do not run it manually first.
- Documentation budgets per task are in the `project-manager` skill. Verification
  is worth spending on; restating the same facts in four files is not.
