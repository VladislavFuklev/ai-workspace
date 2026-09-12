# Changelog

## Unreleased

### 0.1 — Repository initialization and architecture decision (2026-09-12)

**Added**
- Root `.gitignore` covering Node, Python, environment files, build output,
  local data and editor/OS artifacts.
- Placeholder `README.md` pointing at the `docs/` source of truth (the real
  README is task 14.6).
- `docs/tasks/0.2-monorepo-setup.md` — specification for the next task.
- ADR-001 … ADR-005 in `docs/DECISIONS.md`: monorepo, workspace boundaries and
  layering, pnpm workspaces with Node 22 LTS, uv with pinned Python 3.13, and
  independent JS/Python dependency graphs joined at the HTTP contract.

**Changed**
- `docs/ARCHITECTURE.md` — added repository topology, per-app internal layouts
  with explicit dependency direction, a toolchain baseline table, and the
  cross-language boundary.
- `docs/ROADMAP.md` — 0.1 marked complete.
- `docs/PROJECT_STATE.md` — records completion of 0.1 and the next action.

**Removed**
- `.claude/.DS_Store` and `docs/.DS_Store` untracked from git (they remain on disk
  and are now ignored).

**Notes**
- No application code, dependencies or infrastructure were created; those begin
  at task 0.2.

---

Project initialized.
