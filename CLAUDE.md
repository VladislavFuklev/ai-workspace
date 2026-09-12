# AI Workspace — Claude Code Rules

This repository is a production-style portfolio project.

Read `docs/PROJECT_STATE.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, and relevant `docs/tasks/*` before meaningful work.

## Source of truth

- Roadmap: `docs/ROADMAP.md`
- Current state: `docs/PROJECT_STATE.md`
- Architecture: `docs/ARCHITECTURE.md`
- Decisions: `docs/DECISIONS.md`
- Changelog: `docs/CHANGELOG.md`
- Task specs: `docs/tasks/`

## Context economy

Start a session with `./scripts/ctx.sh` — a ~35 line digest of state, roadmap
position, blockers and ADR titles. Open the full documents only when the work
needs them.

Prefer `rtk <command>` over the raw command in Bash (`rtk pnpm`, `rtk next`,
`rtk tsc`, `rtk uv`, `rtk git`, `rtk grep`, `rtk read`, `rtk docker`, `rtk psql`,
`rtk err`). The global rewrite hook does not fire on compound commands, heredocs
or pipelines, which is most of what this project runs.

See the `token-economy` skill for the full list and rationale.

## Operating mode

Work on one task at a time.

Do not silently skip tasks.

Do not start the next task automatically after completing the current task.

Before changing code, investigate the existing repository.

After changing code:
- test it
- update documentation
- update project state
- update changelog
- commit one logical unit

If a decision affects architecture, record it in `docs/DECISIONS.md`.

Never use chat history as the only memory.
