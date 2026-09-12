---
name: token-economy
description: Keep context spend low in this repository. Use at session start to restore project state, and before running any noisy command (installs, builds, typechecks, test runs, git inspection, file reads, searches). Explains why the global RTK hook misses most commands here and what to call instead.
---

# Token Economy

Context is the scarce resource in a long multi-session project. This repository is
built over ~140 roadmap tasks, so the same costs recur every session. Two of them
dominate, and neither is covered by the global RTK hook.

## 1. Session start — use the digest, not the documents

`CLAUDE.md` requires reading `docs/PROJECT_STATE.md`, `docs/ROADMAP.md`,
`docs/ARCHITECTURE.md`, `docs/DECISIONS.md` and `docs/CHANGELOG.md` before
meaningful work. Read in full that is ~470 lines and grows every task.

Run this instead:

```bash
./scripts/ctx.sh
```

It prints ~35 lines: HEAD commit, whether the tree is dirty, current phase, current
and last-completed task, blockers, next action, the current phase's roadmap items,
every ADR title, and which task specs exist. That is enough to know what to do next
and which document actually needs opening.

Then read only what the work requires:

- the task spec for the task you are about to do — `docs/tasks/<id>-*.md`
- `docs/ARCHITECTURE.md` — before creating files or crossing a layer boundary
- a specific ADR body — only when revisiting or contradicting that decision
- `docs/CHANGELOG.md` — rarely; the digest and task specs cover it

Do not re-read a document you already read this session.

## 2. Commands — call `rtk` explicitly

A global `PreToolUse` hook rewrites simple Bash commands to their `rtk` equivalent.
It cannot rewrite the shapes used most in this repo: `cd x && ...`, heredocs,
subshells, pipelines, `for` loops. Measured adoption in a real session here was
**1.8%** — the hook is effectively not helping.

So write `rtk` yourself. It covers nearly this whole stack:

| Instead of | Use | Why |
| --- | --- | --- |
| `pnpm install` / `pnpm <script>` | `rtk pnpm ...` | drops progress spam |
| `pnpm build` / `next build` | `rtk next build` | build summary only |
| `tsc --noEmit` | `rtk tsc ...` | errors grouped by file |
| `eslint` | `rtk lint ...` | violations grouped by rule |
| `uv run ...` | `rtk uv run ...` | keeps uv env semantics |
| `pytest` / `vitest` / `playwright` | `rtk test ...` / `rtk vitest ...` / `rtk playwright ...` | failures only |
| `ruff` / formatters | `rtk ruff ...` / `rtk format ...` | compact |
| `git status` / `diff` / `log` | `rtk git ...` | compact |
| `docker ...`, `psql ...` | `rtk docker ...`, `rtk psql ...` | needed from task 0.3 |
| `cat file` | `rtk read file` | intelligent filtering |
| `grep -rn` / `rg` | `rtk grep` / `rtk rg` | grouped by file, truncated |
| `ls -la` / `find` / `tree` | `rtk ls` / `rtk find` / `rtk tree` | compact |
| any noisy command | `rtk err <cmd>` | errors and warnings only |

`rtk proxy <cmd>` runs unfiltered when you genuinely need raw output (debugging a
filter, or output you must quote exactly).

Do not wrap the dedicated Read/Edit/Write tools in rtk — this applies to Bash.

## 3. Habits that cost the most here

- **Verifying an edit by re-reading the file.** Edit and Write fail loudly; a
  successful call means the change landed.
- **`cat`-ing a whole doc for one section.** Use `sed -n '/^## Heading/,/^## /p'`
  or `rtk read`.
- **Full installs to check one version.** `rtk deps`, or read the manifest.
- **Re-running a passing check.** Run the suite once, at the end of the task.
- **Dumping a build log to confirm success.** `| tail -12`, or `rtk err`.
- **Committing without `--dry-run` first** and then reading a huge accidental
  diff. `git add -A -n` is cheap insurance in a repo with `node_modules/`.

## 4. Check the return

```bash
rtk gain          # savings so far
rtk discover      # commands in recent history that RTK could have handled
```

Run `rtk discover` occasionally. If adoption is low again, the fix is this file:
add the missed command to the table above.
