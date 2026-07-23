# Learning Analytics: Engagement, Assessment, and Outcome Forecasting

**PostgreSQL + SQL + Python project using the real Open University Learning
Analytics Dataset (OULAD).**

This project builds a relational analytics system for studying engagement,
assessment progress, withdrawal timing, and weekly outcome forecasts. SQL owns
the data model, stable metric definitions, quality checks, analytical marts,
window functions, and point-in-time feature snapshots. Python owns source
verification, statistical analysis, visualization, model pipelines,
calibration, threshold analysis, and report generation.

[SQL gallery](sql/gallery/queries.sql) | [Methodology](docs/methodology.md) |
[Model card](docs/model-card.md) | [Dashboard](dashboard/index.html) |
[Two-minute walkthrough](docs/reviewer-guide.md)

## Verified dataset

The reproducible source audit calculates these values from the official UCI
archive rather than copying them from a summary:

| Measure | Calculated value |
| --- | ---: |
| Modules | 7 |
| Module-presentations | 22 |
| Unique anonymized students | 28,785 |
| Student-module attempts | 32,593 |
| Assessments | 206 |
| VLE resources | 6,364 |
| Student-assessment records | 173,912 |
| VLE activity records | 10,655,280 |
| Rows across all seven CSV files | 10,900,970 |

OULAD covers selected anonymized Open University modules from 2013 and 2014.
The source is licensed under CC BY 4.0; see [DATA_LICENSE.md](DATA_LICENSE.md).
Source files are downloaded on demand and are not committed.

## Analytical questions

1. How do engagement volume, consistency, and inactivity differ across weeks
   and module-presentations?
2. How do assessment availability, submission timing, missing submissions, and
   weighted progress vary?
3. What recorded activity patterns appear before withdrawal, without treating
   association as explanation?
4. At the end of a course week, how well can available information forecast a
   missing or below-pass next assessment?
5. How do calibration, threshold workload, course week, and held-out
   presentation affect the interpretation of model performance?

## Architecture

```text
Official OULAD CSV files
    |
    v
Python checksum verification and source audit
    |
    v
PostgreSQL raw -> staging -> core
    |
    v
SQL quality checks, analytical marts, weekly snapshots
    |
    v
Python analysis, visualizations, modeling, calibration
    |
    v
Reports and focused static dashboard
```

The relational design and table grains are documented in
[docs/sql-mastery.md](docs/sql-mastery.md). The Python package is documented in
[docs/python-engineering.md](docs/python-engineering.md).

## SQL highlights

- Six named schemas: `raw`, `staging`, `core`, `quality`, `analytics`, and
  `features`.
- Constrained module-presentation, attempt, assessment, submission, resource,
  and interaction tables.
- Weekly engagement, assessment progress, withdrawal-aligned activity, and
  weekly model snapshots.
- `LAG`, cumulative and rolling windows, conditional aggregation,
  `percent_rank`, lateral joins, materialized views, and composite indexes.
- Executable source, key, relationship, range, category, date, and leakage
  tests with error, warning, and informational severity.
- Fifteen executable portfolio queries and two measured performance studies.

## Python highlights

- Typed settings and environment-based database configuration.
- Checksum-verified download and streaming source profiler.
- Parameterized database utilities and importable analysis modules.
- Reproducible scikit-learn pipelines with prevalence and SQL-rule baselines,
  logistic regression, a constrained decision tree, and a boosted challenger.
- Complete-presentation temporal splits, probability calibration, threshold
  analysis, subgroup diagnostics, and saved model artifacts.
- Programmatic, accessible charts and a generated static dashboard.

## Forecast definition

At the end of a weekly snapshot, the primary target records whether the next
non-exam assessment is absent by its expected due day or has a recorded score
below the documented pass threshold of 40. Features use only activity,
submissions, and due dates available at or before that snapshot. The label is
used only after its future outcome becomes known.

Presentations from 2013 train the models, complete 2014B presentations form the
validation set, and complete 2014J presentations form the held-out test set.
No random row split mixes weekly records from the same presentation across
partitions.

## Executed results

- All 18 error-level SQL checks passed; six warning or informational checks
  remain visible, including 688,988 pre-course activity rows, 11 assessments
  without due dates, and 1,111 missing deprivation-band values.
- Withdrawn is recorded for 10,156 of 32,593 student-module attempts (31.2%);
  the data do not identify why an attempt ended.
- The largest module-presentation missing-submission rate was 56.5% in CCC
  2014B; course design and unobserved context limit comparison.
- On complete held-out 2014J presentations, the boosted challenger reached
  0.642 precision-recall AUC. The calibrated logistic reference reached 0.594
  PR AUC and a 0.130 Brier score.
- The weekly materialized mart ran about 18 times faster than the measured raw
  aggregation; the materialized AAA snapshot scan ran about 6.6 times faster
  than regenerating its range join on this machine.

Full claims and limitations are generated in
[`reports/findings.md`](reports/findings.md).

## Reproduce

Requirements: Python 3.11+, PostgreSQL 16, and either local PostgreSQL commands
or Docker.

```bash
cp .env.example .env
make setup
make data
make db-up
make ingest
make sql
make validate
make analyze
make model
make report
make dashboard
make test
make lint
```

For a local trusted PostgreSQL installation, set:

```bash
export DATABASE_URL=postgresql:///learning_analytics
```

Rebuild from scratch with `make clean-db`, `make db-init`, `make ingest`, and
`make sql`.

## Repository map

| Path | Purpose |
| --- | --- |
| `sql/00_database.sql` to `sql/09_performance.sql` | Ordered PostgreSQL workflow |
| `sql/gallery/queries.sql` | Fifteen foundational-to-advanced queries |
| `sql/quality/` | Point-in-time and leakage checks |
| `src/learning_analytics/` | Importable Python package |
| `tests/` | Cutoff, leakage, configuration, and source tests |
| `reports/tables/` | Executed audit, quality, analysis, and model outputs |
| `reports/figures/` | Programmatically generated charts |
| `dashboard/` | Static analytical dashboard |
| `docs/` | Methodology, engineering, model, and data documentation |

## Interpretation limits

VLE clicks are platform traces, not direct measures of effort, attention,
motivation, understanding, or intelligence. Withdrawal may occur for reasons
not represented in the data. OULAD is historical and institution-specific.
Findings are associative, demographic comparisons require care, and held-out
performance here does not establish performance elsewhere.
