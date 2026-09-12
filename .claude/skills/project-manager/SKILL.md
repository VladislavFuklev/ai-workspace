---
name: project-manager
description: Enforce the task lifecycle in this repository — restore state at session start, select exactly one next task, run the verify gate before claiming completion, update all state documents, and produce the session handoff. Use at the start of every session, before starting any roadmap task, and before every commit.
---

# Project Manager

This project runs ~140 roadmap tasks across many sessions with no shared memory but
the filesystem. This skill is the lifecycle that keeps that working.

## The one rule that matters

**Exactly one roadmap task per session, and it must be the first incomplete one.**

Not "the obvious next thing". Not "0.3 plus a bit of 0.4 since I'm in there". If
work you are doing turns out to belong to a later task, stop and write it into that
task's spec instead of doing it.

## Phase A — Restore (before any edit)

```bash
./scripts/ctx.sh
```

That gives HEAD, tree state, current/last task, blockers, next action, the current
phase's roadmap items and every ADR title. Then read exactly two more things:

1. `docs/tasks/<next-id>-*.md` — the spec for the task you are about to do.
2. `docs/ARCHITECTURE.md` — before creating a file or crossing a layer boundary.

If the digest says the tree is DIRTY, resolve that before starting. A task must
begin from a clean tree so its commit is one logical unit.

If `docs/tasks/<next-id>-*.md` does not exist, write it first (see the template
below) and confirm the scope with the user before implementing.

## Phase B — Plan, and state it before touching files

The user expects a plan before edits. State:

1. Which task, by ID, and why it is the first incomplete one.
2. Scope — and, explicitly, what belongs to later tasks and is therefore excluded.
3. Files you expect to create and modify.
4. Architectural decisions the task forces, with a recommendation for each.
5. What will verify it.

Then wait. Do not begin editing on an unanswered plan.

## Phase C — Verify before claiming anything

Never write "done" on the basis of code that was not run. The gate, as it exists
today (grow it as tooling lands in 0.4 and phase 12):

```bash
rtk pnpm typecheck            # from a clean state — delete .next/ first
rtk pnpm --filter @ai-workspace/web lint
rtk pnpm build
rtk uv run --project apps/api python -c "import ai_workspace_api"
git add -A -n                 # nothing generated must be staged
```

Add for the task at hand: the acceptance criteria in the task spec, each one
actually exercised. A criterion you did not test is a criterion you did not meet —
say so rather than implying otherwise.

## Phase D — Persist state (all of it, every time)

A task is not complete until every one of these is true:

| File | What goes in |
| --- | --- |
| `docs/tasks/<id>-*.md` | An `## Outcome` section: versions chosen, files created/modified, a check→result table, acceptance criteria answered one by one, **deviations from the plan and why**, known limitations, next task |
| `docs/CHANGELOG.md` | A `### <id> — <title> (date)` entry with Added/Changed/Removed/Notes |
| `docs/PROJECT_STATE.md` | Status, last completed task, last session summary, next action, blockers, known limitations |
| `docs/ROADMAP.md` | `- [ ]` → `- [x]` |
| `docs/ARCHITECTURE.md` | Only if structure or toolchain actually changed |
| `docs/DECISIONS.md` | A new ADR for any decision that constrains future work |
| `docs/tasks/<next-id>-*.md` | The next task's spec, so the next session starts with one |

The deviations section is the highest-value thing you write. Any real task departs
from its plan; a future session that cannot see why will undo the reasoning.

## Phase E — Commit

One logical commit. Format `<scope>: <imperative summary>`, scope from
`chore|frontend|backend|ai|infra|docs|test`.

Body: what changed and why, then the checks that were run. Never mix a roadmap task
with unrelated cleanup — commit the cleanup separately, before or after.

Check `git add -A -n` before staging. This repo contains `node_modules/` and
`.venv/`; one careless `git add -A` is a very expensive diff.

## Phase F — Handoff

Output, and mirror into `docs/PROJECT_STATE.md`:

current phase · completed task · files changed · checks run with results ·
commit hash · deviations · remaining issues · exact next task ID · exact next action

Then **stop**. Do not start the next task. `CLAUDE.md` forbids it, and the user
decides sequencing.

## Writing a task spec

Every spec needs: ID, objective, context, prerequisites, implementation steps,
acceptance criteria (each independently checkable), tests, documentation updates,
commit message. Size it at 20–90 minutes of focused work. If it is larger, it is
more than one task — split it and add the split to `docs/ROADMAP.md`.

Model it on `docs/tasks/0.2-monorepo-setup.md`, which has both a spec and a
completed outcome section.

## When something blocks

Stop at the smallest safe boundary. Leave the repository working. Write the blocker
into `docs/PROJECT_STATE.md` under Known blockers with enough detail to resume
cold, and say plainly what is unfinished. Do not scale the task down silently and
report success — narrowing scope is the user's call.
