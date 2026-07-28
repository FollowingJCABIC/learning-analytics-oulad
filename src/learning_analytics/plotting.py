from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

COLORS = {
    "blue": "#176B87",
    "coral": "#D95D39",
    "green": "#2A7F62",
    "gold": "#C58A1C",
    "violet": "#665191",
    "gray": "#68717A",
}

MODEL_LABELS = {
    "prevalence_baseline": "Event-rate baseline",
    "sql_rule_baseline": "Simple rules baseline",
    "logistic_regression": "Logistic regression",
    "decision_tree": "Decision tree",
    "gradient_boosted_tree": "Boosted challenger",
    "calibrated_logistic_regression": "Calibrated logistic model",
}


def _finish(figure: plt.Figure, path: Path) -> None:
    figure.tight_layout()
    figure.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def outcome_distribution(frame: pd.DataFrame, path: Path) -> None:
    order = ["Distinction", "Pass", "Fail", "Withdrawn"]
    values = frame.set_index("final_result").reindex(order)["attempts"].fillna(0)
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    axis.bar(
        order,
        values,
        color=[COLORS["green"], COLORS["blue"], COLORS["coral"], COLORS["gold"]],
    )
    axis.set_title("Recorded outcomes across student-module attempts", loc="left")
    axis.set_ylabel("Student-module attempts")
    axis.set_xlabel("Final result recorded in OULAD")
    axis.grid(axis="y", alpha=0.2)
    _finish(figure, path)


def weekly_engagement(frame: pd.DataFrame, path: Path) -> None:
    summary = frame.groupby("course_week", as_index=False).agg(
        median_clicks=("median_clicks", "median"),
        p75_clicks=("p75_clicks", "median"),
    )
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    axis.plot(
        summary["course_week"],
        summary["median_clicks"],
        marker="o",
        color=COLORS["blue"],
        label="Median",
    )
    axis.plot(
        summary["course_week"],
        summary["p75_clicks"],
        marker="s",
        linestyle="--",
        color=COLORS["coral"],
        label="75th percentile",
    )
    axis.set_title("Weekly activity varies substantially within active cohorts", loc="left")
    axis.set_xlabel("Course week")
    axis.set_ylabel("VLE clicks per active student-attempt")
    axis.legend(frameon=False)
    axis.grid(alpha=0.2)
    _finish(figure, path)


def engagement_consistency(frame: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    for outcome, group in frame.groupby("final_result"):
        axis.scatter(
            group["mean_weekly_clicks"],
            group["active_weeks"],
            s=9,
            alpha=0.18,
            label=outcome,
        )
    axis.set_xscale("log")
    axis.set_title("Engagement volume and consistency are related but distinct", loc="left")
    axis.set_xlabel("Mean clicks in active weeks (log scale)")
    axis.set_ylabel("Number of active course weeks")
    axis.legend(frameon=False, markerscale=2)
    axis.grid(alpha=0.2)
    _finish(figure, path)


def withdrawal_alignment(frame: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    axis.plot(
        frame["weeks_from_unregistration"],
        frame["median_clicks"],
        marker="o",
        color=COLORS["violet"],
    )
    axis.axvline(0, color=COLORS["coral"], linestyle="--", label="Recorded unregistration")
    axis.set_title("Activity around recorded withdrawal timing", loc="left")
    axis.set_xlabel("Weeks relative to unregistration")
    axis.set_ylabel("Median weekly clicks among active records")
    axis.legend(frameon=False)
    axis.grid(alpha=0.2)
    _finish(figure, path)


def assessment_missingness(frame: pd.DataFrame, path: Path) -> None:
    plot = frame.sort_values("missing_rate", ascending=True)
    labels = plot["code_module"] + " " + plot["code_presentation"]
    figure, axis = plt.subplots(figsize=(8.4, 6.2))
    axis.barh(labels, plot["missing_rate"] * 100, color=COLORS["gold"])
    axis.set_title("Missing assessment records differ by module-presentation", loc="left")
    axis.set_xlabel("Eligible student-assessments without a submission (%)")
    axis.set_ylabel("Module-presentation")
    axis.grid(axis="x", alpha=0.2)
    _finish(figure, path)


def submission_timing(frame: pd.DataFrame, path: Path) -> None:
    plot = frame.sort_values("median_submission_delay_days")
    labels = plot["code_module"] + " " + plot["code_presentation"]
    figure, axis = plt.subplots(figsize=(8.4, 6.2))
    colors = [
        COLORS["green"] if value <= 0 else COLORS["coral"]
        for value in plot["median_submission_delay_days"]
    ]
    axis.barh(labels, plot["median_submission_delay_days"], color=colors)
    axis.axvline(0, color=COLORS["gray"], linewidth=1)
    axis.set_title("Recorded submission timing relative to assessment due day", loc="left")
    axis.set_xlabel("Median days after due day (negative is early)")
    axis.set_ylabel("Module-presentation")
    axis.grid(axis="x", alpha=0.2)
    _finish(figure, path)


def model_comparison(frame: pd.DataFrame, path: Path) -> None:
    plot = frame[frame["split"] == "test"].sort_values("pr_auc").copy()
    plot["label"] = plot["model"].map(MODEL_LABELS).fillna(
        plot["model"].str.replace("_", " ")
    )
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    bars = axis.barh(plot["label"], plot["pr_auc"], color=COLORS["blue"])
    for bar, model in zip(bars, plot["model"], strict=True):
        if "baseline" in model:
            bar.set_facecolor("white")
            bar.set_edgecolor(COLORS["gray"])
            bar.set_hatch("///")
    axis.bar_label(bars, fmt="%.3f", padding=5, color=COLORS["gray"])
    axis.set_xlim(0, 1)
    axis.set_title("How well each approach ranked the next-assessment cases", loc="left")
    axis.set_xlabel("Precision-recall AUC (higher is better)")
    axis.set_ylabel("")
    axis.grid(axis="x", alpha=0.2)
    _finish(figure, path)


def model_overview(frame: pd.DataFrame, path: Path) -> None:
    selected = {
        "prevalence_baseline",
        "calibrated_logistic_regression",
        "gradient_boosted_tree",
    }
    plot = frame[
        (frame["split"] == "test") & frame["model"].isin(selected)
    ].sort_values("pr_auc").copy()
    plot["label"] = plot["model"].map(MODEL_LABELS)
    colors = [
        COLORS["gray"] if model == "prevalence_baseline"
        else COLORS["green"] if model == "calibrated_logistic_regression"
        else COLORS["blue"]
        for model in plot["model"]
    ]

    figure, axis = plt.subplots(figsize=(8.4, 4.6))
    bars = axis.barh(plot["label"], plot["pr_auc"], color=colors)
    bars[0].set_facecolor("white")
    bars[0].set_edgecolor(COLORS["gray"])
    bars[0].set_hatch("///")
    axis.bar_label(bars, fmt="%.3f", padding=5, color=COLORS["gray"])
    axis.set_xlim(0, 0.75)
    axis.set_title("The boosted model ranked cases best", loc="left")
    axis.set_xlabel("Precision-recall AUC (higher is better)")
    axis.set_ylabel("")
    axis.grid(axis="x", alpha=0.2)
    _finish(figure, path)


def calibration_curve(frame: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(6.2, 5.8))
    axis.plot([0, 1], [0, 1], color=COLORS["gray"], linestyle="--", label="Perfect calibration")
    axis.plot(
        frame["mean_predicted_probability"],
        frame["observed_event_rate"],
        color=COLORS["coral"],
        marker="o",
        label="Calibrated logistic regression",
    )
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.set_title("Predicted probabilities versus observed event rates", loc="left")
    axis.set_xlabel("Mean predicted probability")
    axis.set_ylabel("Observed event rate")
    axis.legend(frameon=False)
    axis.grid(alpha=0.2)
    _finish(figure, path)


def threshold_curve(frame: pd.DataFrame, path: Path) -> None:
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    axis.plot(frame["flag_rate"] * 100, frame["precision"], marker="o", label="Precision")
    axis.plot(frame["flag_rate"] * 100, frame["recall"], marker="s", label="Recall")
    axis.set_title("Threshold choice changes workload and error tradeoffs", loc="left")
    axis.set_xlabel("Records flagged (%)")
    axis.set_ylabel("Metric value")
    axis.set_ylim(0, 1)
    axis.legend(frameon=False)
    axis.grid(alpha=0.2)
    _finish(figure, path)


def performance_by_week(frame: pd.DataFrame, path: Path) -> None:
    plot = frame[frame["dimension"] == "course_week"].copy()
    plot["course_week"] = plot["group"].astype(int)
    plot = plot.sort_values("course_week")
    figure, axis = plt.subplots(figsize=(8.4, 4.8))
    axis.plot(plot["course_week"], plot["pr_auc"], marker="o", label="PR AUC")
    axis.plot(plot["course_week"], plot["brier"], marker="s", label="Brier score")
    axis.set_title("Forecast quality changes as more course history becomes available", loc="left")
    axis.set_xlabel("Course week")
    axis.set_ylabel("Metric value")
    axis.legend(frameon=False)
    axis.grid(alpha=0.2)
    _finish(figure, path)
