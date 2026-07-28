# Forecast Evaluation

## Purpose

Estimate, at the end of a course week, the probability that the next eligible
recorded assessment will be absent by its due day or receive a score below 40.
One record is one student-course attempt at the end of one week, when a
non-exam assessment with a known due date is still ahead. Exams are excluded
because their due dates are often unavailable.

## Non-purpose

The forecast is not a measure of intelligence, motivation, effort, readiness,
or need. It is not an automatic grading, admission, discipline, surveillance,
or intervention system. No action should be taken from the score alone.

## Data and split

Training uses 2013 OULAD presentations, validation uses complete 2014B
presentations, and testing uses complete 2014J presentations. The dataset is
historical and covers selected anonymized Open University modules.

B and J are OULAD labels for earlier- and later-year teaching periods. The
models learn from 2013 offerings, model choices and probability adjustments use
2014B, and the final evaluation uses later 2014J offerings that were not used
for fitting.

I kept complete course offerings together during model evaluation instead of
randomly splitting related weekly records. This prevents records from the same
offering from appearing on both sides of the final test.

## Features

Recent and cumulative click counts, active days, distinct sites, days since
activity, engagement change, prior submissions, scores available by the
snapshot, missing assessments already due, and cumulative weighted progress.
Module and presentation term are categorical context. Demographic fields are
not model features; selected fields are retained only for evaluation.

## Evaluation

On the complete later 2014J set of 117,186 weekly snapshots, 24,724 snapshots
(21.1%) were followed by a missing or below-40 next assessment. The boosted
challenger had the strongest precision-recall AUC at 0.642 and a Brier score of
0.123. The calibrated logistic model produced PR AUC 0.594, ROC AUC 0.800,
Brier score 0.130, precision 0.616, and recall 0.421 at threshold 0.50.

The calibrated logistic model is the recommended inspectable reference. It
gives up 0.048 PR AUC relative to the challenger, but keeps coefficients,
preprocessing, calibration, and threshold behavior easier to inspect. The
boosted model remains a documented performance challenger rather than being
declared the default from one aggregate metric.

Saved metrics are in `reports/tables/model_metrics.csv`; calibration,
threshold, weekly, presentation, and subgroup diagnostics are saved beside it.
The 0.50 threshold is descriptive, not an operational recommendation.

## Secondary withdrawal investigation

A separate logistic model forecasts recorded unregistration within the next 28
days. On later 2014J snapshots, prevalence was 3.9%, PR AUC was 0.082,
precision was 0.080, and recall was 0.617 at threshold 0.50. The low precision
means this model would produce many false alerts and is not recommended for
individual use. Withdrawal can occur for reasons absent from OULAD.

## Failure modes

- no or sparse online activity despite substantial offline study;
- module-specific assessment structures;
- missing submission or withdrawal causes absent from OULAD;
- changes in platform instrumentation or course design;
- prevalence and calibration shifts across presentations;
- confidence on patterns outside the training distribution.

## Fairness

Demographic attributes are excluded from model inputs. Evaluation tables report
sample size and errors where sufficient data exist. Differences must be
interpreted in institutional and measurement context, never as innate traits.

## Appropriate use

Historical research, method comparison, feature-timing audits, model
calibration study, and aggregate planning analysis with qualified domain
interpretation.

## Inappropriate use

Automated decisions about individuals, ranking students or educators,
diagnosing motivation or aptitude, withholding opportunities, or applying the
model to another setting without new validation and governance.
