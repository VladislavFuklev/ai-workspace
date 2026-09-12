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
for id in $(grep -oE '^- \[x\] [0-9]+\.[0-9]+' docs/ROADMAP.md | awk '{print $3}'); do
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

# --- 4. PROJECT_STATE must name the last ticked roadmap task.
# Compare extracted ids, not a grep: "0.6" as a pattern matches "026" inside a
# date, which made an earlier version of this check silently pass.
last_ticked=$(grep -E '^- \[x\]' docs/ROADMAP.md | tail -1 | awk '{print $3}')
state_task=$(grep -A2 '^## Last completed task' docs/PROJECT_STATE.md |
             grep -oE '^[0-9]+\.[0-9]+' | head -1)
[ "$state_task" = "$last_ticked" ] ||
  fail "state: ROADMAP's last ticked task is $last_ticked, PROJECT_STATE says ${state_task:-nothing}"

if [ "$problems" -eq 0 ]; then
  echo "docs consistent"
  exit 0
fi
printf '\n%d documentation problem(s)\n' "$problems"
exit 1
