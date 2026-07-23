#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATABASE_URL="${DATABASE_URL:-postgresql://learning_analytics:learning_analytics@localhost:5432/learning_analytics}"

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT/sql/00_database.sql"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$ROOT/sql/01_raw_tables.sql"

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<SQL
\copy raw.courses FROM '$ROOT/data/raw/source/courses.csv' WITH (FORMAT csv, HEADER true)
\copy raw.assessments FROM '$ROOT/data/raw/source/assessments.csv' WITH (FORMAT csv, HEADER true)
\copy raw.vle FROM '$ROOT/data/raw/source/vle.csv' WITH (FORMAT csv, HEADER true)
\copy raw.student_info FROM '$ROOT/data/raw/source/studentInfo.csv' WITH (FORMAT csv, HEADER true)
\copy raw.student_registration FROM '$ROOT/data/raw/source/studentRegistration.csv' WITH (FORMAT csv, HEADER true)
\copy raw.student_assessment FROM '$ROOT/data/raw/source/studentAssessment.csv' WITH (FORMAT csv, HEADER true)
\copy raw.student_vle FROM '$ROOT/data/raw/source/studentVle.csv' WITH (FORMAT csv, HEADER true)
SQL

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<SQL
CREATE INDEX raw_vle_resource_key_idx
    ON raw.vle (code_module, code_presentation, id_site);
CREATE INDEX raw_student_info_attempt_key_idx
    ON raw.student_info (code_module, code_presentation, id_student);
ANALYZE raw.student_vle;
ANALYZE raw.vle;
ANALYZE raw.student_info;
SQL
