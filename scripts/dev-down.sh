#!/usr/bin/env bash
# Stop the local backing services.
#
#   scripts/dev-down.sh              stop containers, keep data
#   scripts/dev-down.sh --volumes    also delete the volumes (destroys local data)
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

compose=(docker compose -f infra/docker-compose.yml)
[ -f .env ] && compose+=(--env-file .env)

wipe=0
for arg in "$@"; do
  case "$arg" in
    --volumes|-v) wipe=1 ;;
  esac
done

if [ "$wipe" -eq 1 ]; then
  echo "This deletes the local database, Redis data and object storage. Ctrl-C to abort."
  read -r -p "Type 'yes' to continue: " reply
  [ "$reply" = "yes" ] || { echo "aborted"; exit 1; }
  "${compose[@]}" down --volumes --remove-orphans
  echo "services stopped, volumes removed"
else
  "${compose[@]}" down --remove-orphans
  echo "services stopped, data preserved"
fi
