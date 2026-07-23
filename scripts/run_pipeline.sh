#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATABASE_URL="${DATABASE_URL:-postgresql://learning_analytics:learning_analytics@localhost:5432/learning_analytics}"

for script in \
  02_staging.sql \
  03_core.sql \
  04_quality.sql \
  05_analytics.sql \
  06_features.sql \
  07_indexes.sql \
  08_exports.sql \
  quality/snapshot_tests.sql \
  09_performance.sql
do
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT/sql/$script"
done

mkdir -p "$ROOT/data/processed" "$ROOT/reports/tables"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c \
  "\copy (select * from features.model_snapshots order by code_module, code_presentation, id_student, course_week) to '$ROOT/data/processed/model_snapshots.csv' csv header"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c \
  "\copy (select * from quality.latest_results order by severity, check_name) to '$ROOT/reports/tables/sql_quality_results.csv' csv header"
