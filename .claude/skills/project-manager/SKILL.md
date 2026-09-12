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

Never write "done" on the basis of code that was not run.

```bash
./scripts/check.sh            # format, lint, types — both workspaces, ~2s
git add -A -n                 # nothing generated must be staged
```

**Do not run `check.sh` and then commit.** The pre-commit hook runs it again; that
is a duplicate. Commit and let the hook be the gate. Run it by hand only while
iterating, or when committing with `--no-verify`.

Run `rtk pnpm build` only when the change could affect the build.

Then the acceptance criteria in the task spec, each one actually exercised. A
criterion you did not test is a criterion you did not meet — say so rather than
implying otherwise. That verification is the expensive part of a task and it is
the part worth spending on.

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

### One fact, one place — hard budgets

Measured across 0.1–0.5: ~400 lines of documentation per task, mostly the same
facts restated. Documentation output, not running checks, is what a task costs.

| Where | Budget | Holds |
| --- | --- | --- |
| task outcome | **~20 lines** | check table, deviations, limitations, next task |
| ADR | **~12 lines** | context, decision, rejected, revisit-when, consequence |
| CHANGELOG | **~6 lines** | what changed, one line each |
| PROJECT_STATE | **edit 3 fields** | last completed, next action, limitations delta |
| next task spec | **~20 lines** | objective, steps, acceptance criteria |
| chat handoff | **~8 lines** | only what `ctx.sh` does not already say |

Rules that keep it there:
- Never restate a fact that is already in another file. Point at it.
- Tables, not prose, for versions, checks and criteria.
- No "Files created/modified" list — `git show --stat` has it.
- No preamble, no rationale paragraphs. A rejected alternative is one clause.
- Skip a section entirely when it is empty. "None" is a line worth not writing.

### Process costs worth avoiding

- **Write it right the first time.** Iterating check → fix → check costs a full
  round trip each. Run the gate once, at the end.
- **Do not print a file back after writing it.** The write either succeeded or errored.
- **Do not run `check.sh` before committing.** The pre-commit hook is the gate.
- **Read an installed package's docs before configuring it**, not after it fails.
- **Batch verification** into one command instead of one per criterion.

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
