# Documentation

The filesystem is this project's memory between sessions. Each file answers one
question; read the one you need rather than all of them.

Start here: **`./scripts/ctx.sh`** prints a ~35-line digest of state, roadmap
position, blockers and every decision title. Open a full document only when the
digest says you need it.

| File | Answers | Read it when |
| --- | --- | --- |
| [PROJECT_STATE.md](PROJECT_STATE.md) | Where are we, what is next, what is broken | Starting a session |
| [ROADMAP.md](ROADMAP.md) | What is built, what is left, in what order | Choosing the next task |
| [tasks/](tasks/) | One spec + outcome per task: steps, acceptance criteria, checks run, deviations | Before starting a task; when asking why something was done that way |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Structure, layering, toolchain, local topology, quality gate | Before creating a file or crossing a layer |
| [DECISIONS.md](DECISIONS.md) | Why a choice was made, what was rejected, when to revisit | Before contradicting an existing decision |
| [CHANGELOG.md](CHANGELOG.md) | What changed, per task, newest first | Reviewing history |
| [../MASTER_PROMPT.md](../MASTER_PROMPT.md) | The full product specification | Settling a question of scope |

## Conventions

- **One task per commit.** A task is complete only when its outcome section, the
  changelog, the project state and the roadmap tick all exist.
- **Decisions live in `DECISIONS.md`**, numbered and never renumbered. Superseding
  an ADR means adding a new one and marking the old one superseded.
- **Task specs use [_TEMPLATE.md](tasks/_TEMPLATE.md).**
- **Documentation is checked, not trusted.** `scripts/check-docs.sh` runs as part
  of `scripts/check.sh` and fails on a roadmap entry that contradicts its task
  file, a dead relative link, an ADR cited but never defined, or a project state
  that disagrees with the roadmap.
- **Budgets** for how much to write per task are in the `project-manager` skill.
  Restating the same fact in four files is the main way this documentation set
  gets expensive.
