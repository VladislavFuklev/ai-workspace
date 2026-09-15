#!/usr/bin/env bash
# Nothing under source is invisible to git.
#
# `storage/` in .gitignore is unanchored, so it matched a source package and
# kept it out of a commit. Everything passed locally, because the files were on
# disk; CI checked out a tree without them. `git status` never mentioned it —
# ignored files are not listed.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# .DS_Store is Finder's, not ours, and is ignored on purpose.
roots=(apps/api/src apps/api/tests apps/web/src apps/web/messages packages scripts infra docs)
existing=()
for root in "${roots[@]}"; do [ -e "$root" ] && existing+=("$root"); done

ignored="$(git status --ignored --short "${existing[@]}" 2>/dev/null \
  | sed -n 's/^!! //p' | grep -Ev '__pycache__|\.next/|node_modules/|\.DS_Store' || true)"

if [ -n "$ignored" ]; then
  echo "Source that git would not ship:" >&2
  echo "$ignored" | sed 's/^/  - /' >&2
  echo "A .gitignore pattern is matching it. Anchor the pattern, or add the path." >&2
  exit 1
fi

echo "${#existing[@]} source roots, nothing ignored"
