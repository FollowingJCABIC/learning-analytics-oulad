# Executed findings

Generated from the PostgreSQL marts and saved model outputs. No finding below
is inferred from the dataset description alone.

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

## Weekly outcome forecasting

The held-out test set contains complete 2014J presentations. The strongest test
precision-recall AUC was **0.642** for
`gradient_boosted_tree`. The calibrated logistic model achieved PR AUC
**0.594**, Brier score **0.130**,
precision **0.616**, and recall
**0.421** at the prespecified 0.50 threshold.

These are forecasts of the next recorded assessment event, not measures of
motivation, aptitude, or instructional need. Threshold analysis is reported
separately because workload and false alerts change with the threshold.

The separate 28-day withdrawal investigation had held-out prevalence
**3.9%**, PR AUC
**0.082**, precision
**0.080**, and recall
**0.617** at threshold 0.50. Its low precision makes
it unsuitable for individual use, and OULAD does not record many reasons for
withdrawal.

## Interpretation limits

VLE clicks record platform interactions, not attention, effort, motivation, or
learning. OULAD covers selected anonymized Open University modules from
2013-2014. Associations do not establish causes, and model performance on these
presentations does not establish performance in another institution or period.
