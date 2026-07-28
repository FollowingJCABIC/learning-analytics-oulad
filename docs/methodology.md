# Methodology

## Scope

The study analyzes anonymized historical records from seven selected Open
University modules and 22 module-presentations in 2013-2014. The unit of most
analysis is a student-module-presentation attempt, not a unique person.

## Cohorts and questions

All recorded attempts are retained for descriptive outcome summaries.
Engagement charts distinguish observed active weeks from generated weekly
snapshots containing zero activity. Assessment analysis excludes exams from
the next-assessment target because exam due dates are often unavailable.

The analysis asks how engagement, assessment, and withdrawal-aligned patterns
vary, then tests a weekly next-assessment forecast. It does not infer
motivation, aptitude, or causes.

## Weekly snapshots

Snapshots cover course weeks 0 through 12 and include attempts registered and
not yet unregistered at the snapshot day. The feature availability registry in
`features.availability_registry` states when each value becomes observable.

Activity features use relative days no later than `course_week * 7 + 6`, the
end of the numbered course week.
Assessment features use submissions no later than the snapshot and missingness
only for assessments already due. A SQL exception and independent Python test
reject future-dated feature inputs.

## Primary target

For each snapshot, a lateral join selects the next non-exam assessment with a
known due day after the snapshot. The event is one when that assessment has no
submission by its due day or its recorded score is below 40. Banked
assessments remain visible in the source mart and can be analyzed separately.

The target is evaluated because it is temporally definable and grounded in the
documented pass threshold. It is not chosen to maximize predictive performance.

## Secondary target

A separate logistic regression estimates whether recorded unregistration occurs
within the next 28 days. The eventual unregistration date is used only to
construct this future label and is never included as a feature. Withdrawal can
reflect work, health, finances, access, course fit, or other circumstances not
measured in OULAD, so this forecast must not be interpreted as motivation,
aptitude, or a prescribed response.

## Approaches compared

1. training-presentation prevalence;
2. transparent inactivity, prior-missingness, or declining-engagement rule;
3. regularized logistic regression;
4. depth-constrained decision tree;
5. histogram gradient-boosted decision trees;
6. logistic probability calibration on the validation presentations.

## Split strategy

Presentations from 2013 train the models. Complete 2014B presentations form the
validation set. Complete 2014J presentations form the later test set and are not
used during predictive development. This
prevents weekly rows from the same module-presentation from crossing
partitions and tests movement to later presentations. The split is stricter
and more operationally meaningful than a random 80/20 row split.

## Evaluation

Saved metrics include precision, recall, F1, ROC AUC, precision-recall AUC,
Brier score, accuracy, and flag rate. Calibration bins compare predicted and
observed rates. Threshold tables report records flagged, precision, recall,
true alerts, and false alerts. Grouped tables show course-week,
module-presentation, module, gender, and age-band behavior when at least 100
records and both classes are present.

Subgroup differences are descriptive and potentially influenced by access,
course design, prior preparation, measurement, sample selection, and
unobserved circumstances. They must not be interpreted as innate differences.

## Statistical interpretation

Charts report sample sizes or link to underlying tables. Comparisons are
descriptive unless a statistical procedure is explicitly named. Feature
coefficients and importances describe learned associations, not causal effects.

## Limitations

OULAD is historical, selected, anonymized, and institution-specific. VLE
interaction counts omit offline activity and do not measure attention or
learning. Assessment absence and withdrawal have unmeasured causes. Weekly
bucket boundaries simplify continuous activity. Performance can shift across
presentations and does not establish deployment validity.
