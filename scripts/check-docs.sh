#!/usr/bin/env bash
# Catch documentation that has drifted out of step with the repository.
#
# Cheap, offline, no dependencies. Reports every problem, then exits non-zero.
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

problems=0
fail() { printf '  %s\n' "$1"; problems=$((problems + 1)); }

# --- 1. A ticked roadmap entry needs a task file with an outcome, and vice versa.
for id in $(grep -oE '^- \[x\] [0-9]+\.[0-9]+' docs/ROADMAP.md | grep -oE '[0-9]+\.[0-9]+$'); do
  file=$(ls docs/tasks/"$id"-*.md 2>/dev/null | head -1)
  if [ -z "$file" ]; then
    fail "roadmap: $id is ticked but docs/tasks/$id-*.md does not exist"
  elif ! grep -q '^## Outcome' "$file"; then
    fail "roadmap: $id is ticked but $file has no '## Outcome' section"
  fi
done

for file in docs/tasks/*.md; do
  case "$(basename "$file")" in _*) continue ;; esac  # _TEMPLATE.md and friends
  grep -q '^## Outcome' "$file" || continue
  id=$(basename "$file" | grep -oE '^[0-9]+\.[0-9]+')
  grep -qE "^- \[x\] $id " docs/ROADMAP.md ||
    fail "roadmap: $file records an outcome but $id is not ticked"
done

# --- 2. Relative links must resolve. Anchors and absolute URLs are skipped.
while IFS= read -r source; do
  while IFS= read -r target; do
    [ -n "$target" ] || continue
    case "$target" in http*|\#*|mailto:*) continue ;; esac
    resolved="$(dirname "$source")/${target%%#*}"
    [ -e "$resolved" ] || fail "link: $source -> $target does not exist"
  done < <(grep -oE '\]\([^)]+\)' "$source" | sed -E 's/^\]\(//; s/\)$//')
done < <(find docs README.md -name '*.md' | sort -u)

# --- 3. Every ADR-NNN mentioned anywhere must exist in DECISIONS.md.
declared=$(grep -oE '^## ADR-[0-9]+' docs/DECISIONS.md | grep -oE '[0-9]+$' | sort -u)
for ref in $(grep -rhoE 'ADR-[0-9]{3}' docs .claude/skills README.md 2>/dev/null |
             grep -oE '[0-9]{3}$' | sort -u); do
  grep -qx "$ref" <<<"$declared" || fail "reference: ADR-$ref is cited but not defined in docs/DECISIONS.md"
done

# --- 4. PROJECT_STATE's last completed task must be a ticked roadmap task.
# Not "the last ticked one": completion order and roadmap order legitimately
# diverge — 1.11 was added and completed after 2.10.
state_task=$(grep -A2 '^## Last completed task' docs/PROJECT_STATE.md |
             grep -oE '^[0-9]+\.[0-9]+' | head -1)
if [ -z "$state_task" ]; then
  fail "state: PROJECT_STATE names no completed task"
elif ! grep -qE "^- \[x\] $state_task " docs/ROADMAP.md; then
  fail "state: PROJECT_STATE claims $state_task is complete, but ROADMAP does not tick it"
fi

# --- 5. PROJECT_STATE's phase must match the phase of the next unticked task.
# Not awk field numbers: "- [ ] 1.5" has four fields and "- [x] 1.1" has three.
next_id=$(grep -m1 -oE '^- \[ \] [0-9]+\.[0-9]+' docs/ROADMAP.md | grep -oE '[0-9]+\.[0-9]+$')
if [ -n "$next_id" ]; then
  next_phase=${next_id%%.*}
  state_phase=$(grep -A2 '^## Current phase' docs/PROJECT_STATE.md |
                grep -oE 'Phase [0-9]+' | head -1 | awk '{print $2}')
  [ "$state_phase" = "$next_phase" ] ||
    fail "state: next task is $next_id (phase $next_phase) but PROJECT_STATE says phase ${state_phase:-nothing}"
fi

if [ "$problems" -eq 0 ]; then
  echo "docs consistent"
  exit 0
fi
printf '\n%d documentation problem(s)\n' "$problems"
exit 1
