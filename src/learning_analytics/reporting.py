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
        model_section = f"""
## Weekly outcome forecasting

The held-out test set contains complete 2014J presentations. The strongest test
precision-recall AUC was **{best["pr_auc"]:.3f}** for
`{best["model"]}`. The calibrated logistic model achieved PR AUC
**{calibrated["pr_auc"]:.3f}**, Brier score **{calibrated["brier"]:.3f}**,
precision **{calibrated["precision"]:.3f}**, and recall
**{calibrated["recall"]:.3f}** at the prespecified 0.50 threshold.

These are forecasts of the next recorded assessment event, not measures of
motivation, aptitude, or instructional need. Threshold analysis is reported
separately because workload and false alerts change with the threshold.
"""
        withdrawal_path = settings.reports_dir / "tables" / "withdrawal_model_metrics.csv"
        if withdrawal_path.exists():
            withdrawal = pd.read_csv(withdrawal_path)
            withdrawal_test = withdrawal[
                (withdrawal["model"] == "withdrawal_logistic_regression")
                & (withdrawal["split"] == "test")
            ].iloc[0]
            model_section += f"""
The separate 28-day withdrawal investigation had held-out prevalence
**{_percent(withdrawal_test["prevalence"])}**, PR AUC
**{withdrawal_test["pr_auc"]:.3f}**, precision
**{withdrawal_test["precision"]:.3f}**, and recall
**{withdrawal_test["recall"]:.3f}** at threshold 0.50. Its low precision makes
it unsuitable for individual use, and OULAD does not record many reasons for
withdrawal.
"""

    text = f"""# Executed findings

Generated from the PostgreSQL marts and saved model outputs. No finding below
is inferred from the dataset description alone.

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
2013-2014. Associations do not establish causes, and model performance on these
presentations does not establish performance in another institution or period.
"""
    output = settings.reports_dir / "findings.md"
    output.write_text(text.strip() + "\n", encoding="utf-8")
    return text
