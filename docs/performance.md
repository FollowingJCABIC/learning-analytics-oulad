# PostgreSQL performance studies

The canonical plans are captured by `sql/09_performance.sql` with `ANALYZE`,
`BUFFERS`, and JSON output. The values below are from the July 23, 2026 local
PostgreSQL 16 run and are machine-specific.

## Weekly engagement aggregation

The original form scanned and grouped the interaction fact at
student-attempt-week grain in **3,563.163 ms**. The reporting form read the
unique, indexed `analytics.weekly_engagement` materialized view in
**197.505 ms**, about 18 times faster for this measured query.
Pre-aggregation trades refresh work and storage for smaller, predictable
repeated queries.

## Model snapshots

For an identical 9,201-row AAA result, generating eligible student-weeks and
range-joining prior activity took **68.965 ms**. Reading cumulative values from
the materialized snapshot table took **10.500 ms**, about 6.6 times faster.
The full build additionally uses ordered window functions instead of repeated
range joins. Materialization trades freshness for reproducibility and keeps
Python from reimplementing temporal joins.

See `reports/tables/performance_summary.csv` for actual execution times and top
plan nodes from the latest run.
