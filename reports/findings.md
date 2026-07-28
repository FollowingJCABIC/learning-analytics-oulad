# Findings from the saved analysis

These findings come from the PostgreSQL marts and saved model outputs. None is
inferred from the dataset description alone.

## Verified scale

The seven CSV files contain **10,900,970** rows,
including **10,655,280** interaction
records, **32,593**
student-module attempts, and **28,785**
unique anonymized students across 22 module-presentations.

## Recorded outcomes

Withdrawn is recorded for **10,156 of 32,593**
student-module attempts (31.2%).
This is a historical institutional outcome and does not reveal why a student
withdrew.

## Assessment completeness

The highest observed missing-submission rate among module-presentations was
**56.5%** in
**CCC 2014B**.
The comparison is descriptive: assessment design, timing, population, and
recording practices differ by presentation.

## SQL validation

The current quality run contains **0 failing error-level checks**.
Warnings and informational profiles remain visible in
`reports/tables/sql_quality_results.csv`; they are not silently converted into
passes.

## Forecasting the next assessment

At the end of one course week, the forecast estimates whether the next non-exam
assessment for that student-course attempt will be missing by its due date or
have a recorded score below 40. One test record is one weekly snapshot with a
known upcoming assessment. Exams are excluded because their due dates are often
unavailable.

The later 2014J test contains **117,186 weekly snapshots**. The target
occurred after **24,724 snapshots (21.1%)**.
Gradient-boosted decision trees ranked cases best, with precision-recall AUC
**0.642**. Calibrated logistic regression, used for the alert
example, reached PR AUC **0.594** and Brier score
**0.130**. It is the inspectable reference because its
coefficients, probability calibration, and cutoff behavior are easier to check.

At a 0.50 cutoff, calibrated logistic regression flagged
**16,901 snapshots
(14.4%)**. About
**61.6% of alerts were correct**, and the
alerts found **42.1% of the actual cases**. A
correct alert came a median of
**26 days** before the assessment.
This result may support human review; it should not label students or make an
automatic decision.

## A separate logistic regression forecast produced too many false alerts

The separate logistic regression asks whether a recorded unregistration will occur within 28
days after one of the same weekly snapshots. In the later 2014J test records,
that happened after **3.9%** of snapshots.
At a 0.50 cutoff, logistic regression flagged
**30.3%** of snapshots, but only
**8.0%** of its alerts were correct. It found
**61.7%** of the withdrawals that did occur.
That is far too many false alerts for individual use. I report the unsuccessful
result because it shows where the available records did not support the proposed
use.

## Interpretation limits

VLE clicks record platform interactions, not attention, effort, motivation, or
learning. OULAD covers selected anonymized Open University modules from
2013-2014. Associations do not establish causes, and forecast performance on these
presentations does not establish performance in another institution or period.
