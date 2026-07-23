from __future__ import annotations

import json

import pandas as pd

from learning_analytics.config import Settings
from learning_analytics.database import read_query
from learning_analytics.plotting import (
    assessment_missingness,
    calibration_curve,
    engagement_consistency,
    model_comparison,
    outcome_distribution,
    performance_by_week,
    submission_timing,
    threshold_curve,
    weekly_engagement,
    withdrawal_alignment,
)


def build_analysis(settings: Settings) -> None:
    settings.ensure_output_directories()
    figures = settings.reports_dir / "figures"
    tables = settings.reports_dir / "tables"

    outcomes = read_query(
        settings,
        """
        SELECT final_result, count(*) AS attempts
        FROM core.student_attempts GROUP BY 1 ORDER BY 1
        """,
    )
    outcomes.to_csv(tables / "outcome_distribution.csv", index=False)
    outcome_distribution(outcomes, figures / "outcome_distribution.png")

    weekly = read_query(
        settings,
        "SELECT * FROM analytics.weekly_engagement_summary ORDER BY 1, 2, 3",
    )
    weekly.to_csv(tables / "weekly_engagement_summary.csv", index=False)
    weekly_engagement(weekly, figures / "weekly_engagement.png")

    consistency = read_query(
        settings,
        """
        SELECT
            attempt.final_result,
            attempt.code_module,
            attempt.code_presentation,
            attempt.id_student,
            avg(engagement.click_count)::numeric AS mean_weekly_clicks,
            count(*)::integer AS active_weeks
        FROM core.student_attempts AS attempt
        JOIN analytics.weekly_engagement AS engagement
            USING (code_module, code_presentation, id_student)
        WHERE engagement.course_week BETWEEN 0 AND 12
        GROUP BY 1, 2, 3, 4
        """,
    )
    engagement_consistency(consistency, figures / "engagement_consistency.png")

    withdrawal = read_query(
        settings,
        """
        SELECT
            floor(days_relative_to_unregistration / 7.0)::integer AS weeks_from_unregistration,
            percentile_cont(0.5) WITHIN GROUP (ORDER BY click_count) AS median_clicks,
            count(DISTINCT (code_module, code_presentation, id_student)) AS attempts
        FROM analytics.withdrawal_aligned_engagement
        WHERE days_relative_to_unregistration BETWEEN -84 AND 28
        GROUP BY 1 ORDER BY 1
        """,
    )
    withdrawal.to_csv(tables / "withdrawal_alignment.csv", index=False)
    withdrawal_alignment(withdrawal, figures / "withdrawal_alignment.png")

    assessment = read_query(
        settings,
        """
        SELECT
            code_module,
            code_presentation,
            avg(missing_submission)::float AS missing_rate,
            percentile_cont(0.5) WITHIN GROUP (ORDER BY submission_delay_days)
                AS median_submission_delay_days,
            count(*) AS eligible_student_assessments
        FROM analytics.assessment_progress
        GROUP BY 1, 2 ORDER BY 1, 2
        """,
    )
    assessment.to_csv(tables / "assessment_patterns.csv", index=False)
    assessment_missingness(assessment, figures / "assessment_missingness.png")
    submission_timing(
        assessment.dropna(subset=["median_submission_delay_days"]),
        figures / "submission_timing.png",
    )

    plans = read_query(
        settings,
        """
        SELECT captured_at, case_name, variant, plan
        FROM analytics.performance_runs
        ORDER BY case_name, variant
        """,
    )
    performance_dir = settings.reports_dir / "performance"
    performance_dir.mkdir(parents=True, exist_ok=True)
    records = plans.to_dict(orient="records")
    for record in records:
        record["captured_at"] = record["captured_at"].isoformat()
    (performance_dir / "postgresql_plans.json").write_text(
        json.dumps(records, indent=2) + "\n",
        encoding="utf-8",
    )


def build_model_plots(settings: Settings) -> None:
    tables = settings.reports_dir / "tables"
    figures = settings.reports_dir / "figures"
    model_comparison(pd.read_csv(tables / "model_metrics.csv"), figures / "model_comparison.png")
    calibration_curve(pd.read_csv(tables / "calibration_bins.csv"), figures / "calibration.png")
    threshold_curve(pd.read_csv(tables / "threshold_analysis.csv"), figures / "threshold_curve.png")
    performance_by_week(
        pd.read_csv(tables / "grouped_model_metrics.csv"),
        figures / "performance_by_week.png",
    )
