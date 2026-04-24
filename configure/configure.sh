#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DUMP="$PROJECT_DIR/dump/dump.sql"
if [[ ! -f "$DUMP" ]]; then
    echo "Error: dump not found at dump/dump.sql" >&2; exit 1
fi

echo "==> Importing DB dump..."
docker compose -f "$PROJECT_DIR/docker-compose.prod.yml" exec -T db \
    bash -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < "$DUMP"

echo "==> Done."
