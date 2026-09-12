#!/usr/bin/env bash
# Compact project-context digest for session start.
#
# Replaces reading docs/PROJECT_STATE.md, docs/ROADMAP.md, docs/DECISIONS.md and
# git history in full (~600 lines) with ~35 lines carrying the same decisions.
# Read the full documents only when the digest says you need them.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

state="docs/PROJECT_STATE.md"
roadmap="docs/ROADMAP.md"
decisions="docs/DECISIONS.md"

# Body of a "## Heading" section, blank lines squeezed, trailing blanks dropped.
section() {
  awk -v want="## $1" '
    $0 == want { grab = 1; next }
    /^## / && grab { exit }
    grab { print }
  ' "$state" | awk 'NF { blank = 0; print; next } { blank = 1 } END {}' | sed '/^$/d'
}

field() { printf '  %-11s %s\n' "$1" "$(section "$2" | head -n "${3:-1}" | tr '\n' ' ')"; }

echo "AI Workspace — context digest ($(date +%Y-%m-%d))"
echo
printf '  %-11s %s\n' "commit" "$(git log --oneline -1)"
if [ -n "$(git status --porcelain)" ]; then
  printf '  %-11s %s\n' "tree" "DIRTY — $(git status --porcelain | wc -l | tr -d ' ') file(s)"
  git status --short | sed 's/^/              /'
else
  printf '  %-11s %s\n' "tree" "clean"
fi

echo
echo "STATE"
field "phase"     "Current phase"
field "current"   "Current task"
field "completed" "Last completed task"
field "blockers"  "Known blockers"
echo "  next        $(section 'Next action' | tr '\n' ' ' | cut -c1-160)"

echo
done_n=$(grep -c '^- \[x\]' "$roadmap" || true)
todo_n=$(grep -c '^- \[ \]' "$roadmap" || true)
next_id=$(grep -m1 '^- \[ \]' "$roadmap" | sed 's/^- \[ \] //' || true)
next_phase=${next_id%%.*}
echo "ROADMAP  ${done_n} done / $((done_n + todo_n)) total  |  next: ${next_id}"
awk -v p="$next_phase" '
  /^## Phase / { inphase = ($3 == p) }
  inphase && /^- \[/ { print "  " $0 }
' "$roadmap"

echo
echo "DECISIONS"
grep '^## ADR-' "$decisions" | grep -v 'ADR-XXX' | sed 's/^## /  /'

echo
printf 'TASK SPECS  '
ls docs/tasks/ 2>/dev/null | sed 's/-.*//' | tr '\n' ' '
echo
echo
echo "Full docs when needed: $state, $roadmap, docs/ARCHITECTURE.md, $decisions"
