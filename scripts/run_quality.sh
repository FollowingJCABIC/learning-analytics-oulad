#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATABASE_URL="${DATABASE_URL:-postgresql://learning_analytics:learning_analytics@localhost:5432/learning_analytics}"

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT/sql/04_quality.sql"
if psql "$DATABASE_URL" -Atc "select to_regclass('features.model_snapshots') is not null" | grep -qx t
then
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT/sql/quality/snapshot_tests.sql"
fi
psql "$DATABASE_URL" -P pager=off -c \
  "select severity, check_name, failing_rows, status, detail from quality.latest_results order by severity, check_name"

ERRORS="$(psql "$DATABASE_URL" -Atc "select count(*) from quality.latest_results where severity = 'error' and status = 'fail'")"
if [[ "$ERRORS" != "0" ]]; then
  echo "$ERRORS error-level SQL quality checks failed" >&2
  exit 1
fi
