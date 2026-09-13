# Project State

## Status
**Phases 0–4 complete.** Both workspaces,
Docker services, quality gate, CI, design system and i18n (en/uk); authentication
end to end; organisations, memberships, roles, permission-guarded endpoints and
organisation switching in the web app.

## Current phase
Phase 5 — Documents and storage

## Current task
None in progress.

## Last completed task
4.7 — Tenant isolation tests (2026-09-13)

## Last session

4.1–4.7 — the whole of phase 4. Organisations, memberships, the role/permission table and the first
tenant-scoped HTTP endpoints. See those task files and ADR-021.

Worth carrying forward: `require_permission(...)` returns the `Depends` itself,
so a guarded route reads `Annotated[TenantScope, require_permission(X)]` and the
check lives in the signature. A non-member and a missing organisation return the
same 404; a member missing a permission gets 403 naming it.

The web app puts the organisation in the URL, which is why slugs matching a
static route are reserved by the API — otherwise such an organisation would be
unreachable. `scripts/check-reserved.mjs` guards the three lists that have to
agree.

The API sends the caller's permissions with each organisation, so the interface
gates on data rather than on a duplicated permission table. Renaming never
changes a slug. Over HTTP the last-owner guard is reachable only by leaving:
nobody may change their own role, and only an owner may act on an owner.

`test_tenant_isolation.py` discovers tenant routes from the route modules — not
from `app.routes`, which FastAPI 0.141 populates lazily and would return empty,
passing every sweep vacuously. Anything added under
`/organizations/{organization_slug}` is swept automatically.

## Next action
Execute task **5.1 — File storage abstraction**; write
`docs/tasks/5.1-file-storage.md` first. MinIO is already running in Compose and
configured; 5.1 is the interface the rest of the product uses, with the tenant
in the object key so isolation survives into storage.

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
- Neither organisation list is paginated.
- No way to add someone to an organisation yet: invitations are phase 10, so a
  second member has to be inserted directly for now.
- No audit trail of role changes, removals or deletions (10.1).
- The organisation switcher's behaviour is verified by reading it, not by a test:
  it is client-side and browser automation is 12.8.
- The remembered organisation is one per browser, not per tab.
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
