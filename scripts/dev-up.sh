#!/usr/bin/env bash
# Start the local backing services (PostgreSQL + pgvector, Redis, MinIO).
#
# The web app and the API run on the host (ADR-007); this brings up what they
# talk to. Pass extra arguments straight through to `docker compose up`.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

compose_file="infra/docker-compose.yml"
compose=(docker compose -f "$compose_file")

if [ -f .env ]; then
  compose+=(--env-file .env)
else
  echo "note: no .env found — using the development defaults in $compose_file."
  echo "      cp .env.example .env to override ports or credentials."
fi

if ! docker info >/dev/null 2>&1; then
  echo "error: the Docker daemon is not running. Start Docker Desktop and retry." >&2
  exit 1
fi

# --wait is applied only to the long-running services: it treats the one-shot
# bucket initializer exiting, even successfully, as a failure.
services=(postgres redis minio)
"${compose[@]}" up -d --wait "${services[@]}" "$@"

# Then the initializer, and check it actually succeeded.
"${compose[@]}" up -d --no-deps minio-init >/dev/null
init_status=$("${compose[@]}" ps -a --format '{{.Service}} {{.State}} {{.ExitCode}}' \
  | awk '$1 == "minio-init" { print $3; exit }')
if [ "${init_status:-1}" != "0" ]; then
  echo "error: bucket initialization failed (exit ${init_status:-unknown}). Logs:" >&2
  "${compose[@]}" logs minio-init >&2
  exit 1
fi

echo
"${compose[@]}" ps --format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}'

# Read the effective ports back from compose rather than reprinting the defaults,
# so the summary stays correct when .env overrides them.
port() { "${compose[@]}" port "$1" "$2" 2>/dev/null | sed 's/^0\.0\.0\.0://;s/^\[::\]://' || true; }

echo
echo "postgres  localhost:$(port postgres 5432)  db=${POSTGRES_DB:-ai_workspace} user=${POSTGRES_USER:-ai_workspace}"
echo "redis     localhost:$(port redis 6379)"
echo "minio     localhost:$(port minio 9000)   console http://localhost:$(port minio 9001)"
