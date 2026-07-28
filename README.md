# Disengagement Showed Up Before the Course Was Over

**PostgreSQL + SQL + Python project using the real Open University Learning
Analytics Dataset (OULAD).**

I used anonymous Open University records to understand when students began to
pull away from an online course and whether the information available at the
time could support earlier help. Nearly one in three course attempts ended in
withdrawal. Typical weekly clicks fell from 70 in week 2 to 18.5 in week 12,
and among students who withdrew they fell from 26 twelve weeks before the
recorded withdrawal to 10 one week before it.

I also tested whether a weekly record could help anticipate a student's next
non-exam assessment being missing by its due date or scoring below 40. The
unit was one student-course attempt at the end of one course week, when a later
non-exam assessment with a known due date was available. In the later 2014J
test, 24,724 of 117,186 weekly snapshots (21.1%) were followed by that result.
Exams were excluded because OULAD often does not provide their due dates. The
calibrated logistic model's alerts were correct 61.6% of the time and found
42.1% of the cases that actually occurred. That result could help an instructor
choose which records to review, but it missed more than half of the actual
cases and should not make an automatic decision about a student.

## Public project journey

- [Project overview](https://website-react-fbd.vercel.app/#/data-science/learning-analytics)
- [Full analysis](https://website-react-fbd.vercel.app/dashboards/learning-analytics/full-analysis)
- [Technical methods](docs/methodology.md)
- [SQL gallery](sql/gallery/queries.sql)
- [Analysis walkthrough](docs/project-walkthrough.md)

`reports/public-summary.json` owns the verified facts shared with the central
portfolio. The portfolio build validates that snapshot against the executed
source audit, model metrics, threshold analysis, and withdrawal-model results.

## Three findings

1. **Disengagement appeared before the course ended.** Withdrawal was recorded
   for 10,156 of 32,593 course attempts (31.2%), and activity declined well
   before the recorded withdrawal week. The data do not explain why a student
   withdrew.
2. **Course context changed the meaning of missing work.** Missing-submission
   rates ranged from 14.7% to 56.5% across course offerings. A single rule for
   every course would have hidden that difference.
3. **The next poor assessment result could be anticipated, with limits.** At a
   50% cutoff, the calibrated logistic model flagged 14.4% of later-test weekly
   snapshots. About 62 of every 100 alerts were correct, but the model found
   only about 42 of every 100 actual cases.

The separate 28-day withdrawal model produced too many false alerts for
individual use. Only 8.0% of its alerts were correct on a 3.9% event rate, so I
report it as an unsuccessful model rather than an individual warning system.

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

## Questions I asked

1. When did declining online activity become visible?
2. Did missing work mean the same thing in every course offering?
3. What changed in the weeks before a recorded withdrawal?
4. Could the information available at the time help anticipate a missing or
   below-40 next assessment?
5. Would the forecast be accurate and early enough to support human review
   without becoming an automated judgment?

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
Reports and focused static full analysis
```

The way I connected and organized the tables is documented in
[docs/sql-design.md](docs/sql-design.md). The Python package is documented in
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
- Programmatic, accessible charts and a generated static full analysis.

## Forecast definition

At the end of one course week, the primary model estimates whether the next
non-exam assessment for that student-course attempt will be absent by its due
date or have a recorded score below 40. One record is one weekly snapshot with
a known upcoming assessment. Exams are excluded because their due dates are
often unavailable. The model uses only activity, submissions, scores, and due
dates that could have been known by the end of that week.

Presentations from 2013 train the models, complete 2014B presentations form the
validation set, and complete 2014J presentations form the later test set. B and
J are the source dataset's labels for earlier- and later-year teaching periods.
No random row split mixes weekly records from the same presentation across the
development and test groups.

## What the analysis found

- All 18 error-level SQL checks passed; six warning or informational checks
  remain visible, including 688,988 pre-course activity rows, 11 assessments
  without due dates, and 1,111 missing deprivation-band values.
- Withdrawn is recorded for 10,156 of 32,593 student-module attempts (31.2%);
  the data do not identify why an attempt ended.
- The largest module-presentation missing-submission rate was 56.5% in CCC
  2014B; course design and unobserved context limit comparison.
- On complete later 2014J presentations, the boosted challenger reached
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
Findings are associative, demographic comparisons require care, and performance
on the later test courses does not establish that the model will transfer elsewhere.
