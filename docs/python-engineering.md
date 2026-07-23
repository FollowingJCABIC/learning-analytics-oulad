# Python engineering

## Package structure

| Module | Responsibility |
| --- | --- |
| `config.py` | immutable paths, database URL, and deterministic seed |
| `download.py` | UCI download, archive validation, and SHA-256 verification |
| `audit.py` | streaming source profile and calculated dataset scale |
| `database.py` | scoped PostgreSQL connections and parameterized reads |
| `features.py` | cutoff, inactivity, temporal split, and leakage assertions |
| `analysis.py` | SQL-backed analytical tables and charts |
| `plotting.py` | reusable accessible chart functions |
| `modeling.py` | pipelines, baselines, calibration, slices, and thresholds |
| `reporting.py` | findings assembled from executed outputs |
| `dashboard.py` | static dashboard generation |
| `cli.py` | reproducible command entry points |

Core logic is importable and tested. Notebooks are optional exploration
surfaces and do not contain the canonical transformations.

## Division of work

SQL performs relational joins, metric definition, weekly aggregation,
assessment histories, cumulative features, next-assessment eligibility,
point-in-time snapshots, and quality tests. These operations benefit from
database constraints, query plans, and a single shared definition.

Python handles network acquisition, source profiling, statistical graphics,
model preprocessing, grouped temporal evaluation, probability calibration,
threshold analysis, artifact serialization, and report generation. These tasks
benefit from scientific Python libraries and reusable pipelines.

Transformations are not duplicated between languages: Python consumes the SQL
snapshot export as its model contract.

## Reproducibility and safety

- no local absolute paths in project code;
- credentials come from `DATABASE_URL`;
- source archive checksum is fixed and verified;
- seed `20260723` controls model randomness;
- complete presentations define the split;
- model pipelines persist preprocessing with the estimator;
- failures raise exceptions rather than returning partial silent outputs;
- generated tables record the model run and thresholds.
