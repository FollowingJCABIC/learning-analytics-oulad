from __future__ import annotations

import json

import pandas as pd

from learning_analytics.config import Settings


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_report(settings: Settings) -> str:
    audit = json.loads((settings.reports_dir / "source-audit.json").read_text(encoding="utf-8"))
    outcomes = pd.read_csv(settings.reports_dir / "tables" / "outcome_distribution.csv")
    assessment = pd.read_csv(settings.reports_dir / "tables" / "assessment_patterns.csv")
    quality = pd.read_csv(settings.reports_dir / "tables" / "sql_quality_results.csv")
    total_attempts = int(outcomes["attempts"].sum())
    withdrawal_attempts = int(
        outcomes.loc[outcomes["final_result"] == "Withdrawn", "attempts"].iloc[0]
    )
    highest_missing = assessment.loc[assessment["missing_rate"].idxmax()]
    errors = quality[(quality["severity"] == "error") & (quality["status"] == "fail")]

    model_section = ""
    model_path = settings.reports_dir / "tables" / "model_metrics.csv"
    if model_path.exists():
        metrics = pd.read_csv(model_path)
        test = metrics[metrics["split"] == "test"]
        best = test.loc[test["pr_auc"].idxmax()]
        calibrated = test[test["model"] == "calibrated_logistic_regression"].iloc[0]
        thresholds = pd.read_csv(
            settings.reports_dir / "tables" / "threshold_analysis.csv"
        )
        threshold = thresholds.iloc[(thresholds["threshold"] - 0.5).abs().argmin()]
        test_snapshots = int(calibrated["n"])
        test_events = int(round(float(calibrated["prevalence"]) * test_snapshots))
        model_section = f"""
## Forecasting the next assessment

At the end of one course week, the forecast estimates whether the next non-exam
assessment for that student-course attempt will be missing by its due date or
have a recorded score below 40. One test record is one weekly snapshot with a
known upcoming assessment. Exams are excluded because their due dates are often
unavailable.

The later 2014J test contains **{test_snapshots:,} weekly snapshots**. The target
occurred after **{test_events:,} snapshots ({_percent(float(calibrated["prevalence"]))})**.
Gradient-boosted decision trees ranked cases best, with precision-recall AUC
**{best["pr_auc"]:.3f}**. Calibrated logistic regression, used for the alert
example, reached PR AUC **{calibrated["pr_auc"]:.3f}** and Brier score
**{calibrated["brier"]:.3f}**. It is the inspectable reference because its
coefficients, probability calibration, and cutoff behavior are easier to check.

At a 0.50 cutoff, calibrated logistic regression flagged
**{int(threshold["records_flagged"]):,} snapshots
({_percent(float(threshold["flag_rate"]))})**. About
**{_percent(float(threshold["precision"]))} of alerts were correct**, and the
alerts found **{_percent(float(threshold["recall"]))} of the actual cases**. A
correct alert came a median of
**{int(threshold["median_true_alert_lead_days"]):,} days** before the assessment.
This result may support human review; it should not label students or make an
automatic decision.
"""
        withdrawal_path = settings.reports_dir / "tables" / "withdrawal_model_metrics.csv"
        if withdrawal_path.exists():
            withdrawal = pd.read_csv(withdrawal_path)
            withdrawal_test = withdrawal[
                (withdrawal["model"] == "withdrawal_logistic_regression")
                & (withdrawal["split"] == "test")
            ].iloc[0]
            model_section += f"""
## A separate logistic regression forecast produced too many false alerts

The separate logistic regression asks whether a recorded unregistration will occur within 28
days after one of the same weekly snapshots. In the later 2014J test records,
that happened after **{_percent(withdrawal_test["prevalence"])}** of snapshots.
At a 0.50 cutoff, logistic regression flagged
**{_percent(withdrawal_test["flag_rate"])}** of snapshots, but only
**{_percent(withdrawal_test["precision"])}** of its alerts were correct. It found
**{_percent(withdrawal_test["recall"])}** of the withdrawals that did occur.
That is far too many false alerts for individual use. I report the unsuccessful
result because it shows where the available records did not support the proposed
use.
"""

    text = f"""# Findings from the saved analysis

These findings come from the PostgreSQL marts and saved model outputs. None is
inferred from the dataset description alone.

## Verified scale

The seven CSV files contain **{audit["calculated_scale"]["csv_rows"]:,}** rows,
including **{audit["calculated_scale"]["activity_records"]:,}** interaction
records, **{audit["calculated_scale"]["student_module_attempts"]:,}**
student-module attempts, and **{audit["calculated_scale"]["unique_students"]:,}**
unique anonymized students across 22 module-presentations.

## Recorded outcomes

Withdrawn is recorded for **{withdrawal_attempts:,} of {total_attempts:,}**
student-module attempts ({_percent(withdrawal_attempts / total_attempts)}).
This is a historical institutional outcome and does not reveal why a student
withdrew.

## Assessment completeness

The highest observed missing-submission rate among module-presentations was
**{_percent(float(highest_missing["missing_rate"]))}** in
**{highest_missing["code_module"]} {highest_missing["code_presentation"]}**.
The comparison is descriptive: assessment design, timing, population, and
recording practices differ by presentation.

## SQL validation

The current quality run contains **{len(errors)} failing error-level checks**.
Warnings and informational profiles remain visible in
`reports/tables/sql_quality_results.csv`; they are not silently converted into
passes.
{model_section}
## Interpretation limits

VLE clicks record platform interactions, not attention, effort, motivation, or
learning. OULAD covers selected anonymized Open University modules from
2013-2014. Associations do not establish causes, and forecast performance on these
presentations does not establish performance in another institution or period.
"""
    output = settings.reports_dir / "findings.md"
    output.write_text(text.strip() + "\n", encoding="utf-8")
    return text
