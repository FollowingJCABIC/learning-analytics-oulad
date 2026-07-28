# Project walkthrough

## Two minutes

1. Read the first screen of [README.md](../README.md) for the SQL/Python
   architecture and verified scale.
2. Open [dashboard/index.html](../dashboard/index.html) for the main
   visualizations.
3. Scan [sql/gallery/queries.sql](../sql/gallery/queries.sql) to see the
   progression from row grains to snapshots and execution plans.

## Five minutes

1. Inspect the ERD and table grains in [sql-design.md](sql-design.md).
2. Read `sql/06_features.sql`, especially the point-in-time predicates and
   lateral next-assessment join.
3. Scan `src/learning_analytics/modeling.py` for pipelines, complete-
   presentation splits, calibration, and threshold evaluation.
4. Read [reports/findings.md](../reports/findings.md) for claims tied to the
   saved analysis outputs.

## Fifteen minutes

1. Verify the source checksum and calculated counts in
   `reports/source-audit.json`.
2. Run or inspect `reports/tables/sql_quality_results.csv`.
3. Follow the availability registry and leakage test in `sql/06_features.sql`
   and `sql/quality/snapshot_tests.sql`.
4. Compare captured plans in `analytics.performance_runs` with
   [performance.md](performance.md).
5. Review [methodology.md](methodology.md),
   [forecast-evaluation.md](forecast-evaluation.md), and
   the test suite.
