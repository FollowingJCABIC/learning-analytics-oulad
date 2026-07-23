from __future__ import annotations

import html
import json
import shutil
from string import Template

import pandas as pd

from learning_analytics.config import Settings

REPOSITORY = "https://github.com/FollowingJCABIC/learning-analytics-oulad"
SOURCE_URL = (
    "https://archive.ics.uci.edu/dataset/349/"
    "open+university+learning+analytics+dataset"
)

FIGURE_FILES = (
    "outcome_distribution.png",
    "weekly_engagement.png",
    "engagement_consistency.png",
    "assessment_missingness.png",
    "submission_timing.png",
    "withdrawal_alignment.png",
    "model_comparison.png",
    "calibration.png",
    "threshold_curve.png",
    "performance_by_week.png",
)


def _read_table(settings: Settings, filename: str) -> pd.DataFrame:
    return pd.read_csv(settings.reports_dir / "tables" / filename)


def _chart_slide(
    *,
    chart_id: str,
    filename: str,
    eyebrow: str,
    title: str,
    takeaway: str,
    explanation: str,
    caution: str,
    alt: str,
    caption: str,
    reverse: bool = False,
    technical_note: str | None = None,
) -> str:
    reverse_class = " chart-slide-reverse" if reverse else ""
    note = ""
    if technical_note:
        note = f"""
          <details class="technical-note">
            <summary>Technical note</summary>
            <p>{html.escape(technical_note)}</p>
          </details>"""

    return f"""<article class="chart-slide{reverse_class}" id="{html.escape(chart_id)}">
        <div class="chart-copy">
          <p class="eyebrow">{html.escape(eyebrow)}</p>
          <h3>{html.escape(title)}</h3>
          <p class="takeaway">{html.escape(takeaway)}</p>
          <p>{html.escape(explanation)}</p>
          <p class="interpretation-note">
            <strong>Keep in mind:</strong> {html.escape(caution)}
          </p>{note}
        </div>
        <figure>
          <img
            src="assets/{html.escape(filename)}"
            alt="{html.escape(alt)}"
            loading="lazy"
            decoding="async"
          >
          <figcaption>{html.escape(caption)}</figcaption>
        </figure>
      </article>"""


def build_dashboard(settings: Settings) -> None:
    output_dir = settings.project_root / "dashboard"
    asset_dir = output_dir / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)

    for filename in FIGURE_FILES:
        source = settings.reports_dir / "figures" / filename
        if source.exists():
            shutil.copy2(source, asset_dir / filename)

    audit = json.loads(
        (settings.reports_dir / "source-audit.json").read_text(encoding="utf-8")
    )
    scale = audit["calculated_scale"]

    outcomes = _read_table(settings, "outcome_distribution.csv")
    attempts = int(outcomes["attempts"].sum())
    withdrawals = int(
        outcomes.loc[outcomes["final_result"] == "Withdrawn", "attempts"].iloc[0]
    )
    passes = int(outcomes.loc[outcomes["final_result"] == "Pass", "attempts"].iloc[0])
    failures = int(outcomes.loc[outcomes["final_result"] == "Fail", "attempts"].iloc[0])
    distinctions = int(
        outcomes.loc[outcomes["final_result"] == "Distinction", "attempts"].iloc[0]
    )
    withdrawal_rate = withdrawals / attempts

    weekly = _read_table(settings, "weekly_engagement_summary.csv")
    weekly_plot = weekly.groupby("course_week", as_index=True).agg(
        median_clicks=("median_clicks", "median"),
        p75_clicks=("p75_clicks", "median"),
    )
    week_0_median = float(weekly_plot.loc[0, "median_clicks"])
    week_2_median = float(weekly_plot.loc[2, "median_clicks"])
    week_12_median = float(weekly_plot.loc[12, "median_clicks"])
    week_12_p75 = float(weekly_plot.loc[12, "p75_clicks"])

    assessments = _read_table(settings, "assessment_patterns.csv")
    lowest_missing = assessments.loc[assessments["missing_rate"].idxmin()]
    highest_missing = assessments.loc[assessments["missing_rate"].idxmax()]
    timing = assessments.dropna(subset=["median_submission_delay_days"])
    earliest_timing = timing.loc[timing["median_submission_delay_days"].idxmin()]
    latest_timing = timing.loc[timing["median_submission_delay_days"].idxmax()]

    withdrawal = _read_table(settings, "withdrawal_alignment.csv").set_index(
        "weeks_from_unregistration"
    )
    withdrawal_week_12 = float(withdrawal.loc[-12, "median_clicks"])
    withdrawal_week_1 = float(withdrawal.loc[-1, "median_clicks"])

    metrics = _read_table(settings, "model_metrics.csv")

    def model_row(model: str) -> pd.Series:
        return metrics[(metrics["model"] == model) & (metrics["split"] == "test")].iloc[
            0
        ]

    prevalence = model_row("prevalence_baseline")
    calibrated = model_row("calibrated_logistic_regression")
    boosted = model_row("gradient_boosted_tree")

    thresholds = _read_table(settings, "threshold_analysis.csv")
    threshold_50 = thresholds.iloc[(thresholds["threshold"] - 0.5).abs().argmin()]

    calibration = _read_table(settings, "calibration_bins.csv")
    highest_calibration_bin = calibration.iloc[-1]

    analysis_slides = "\n".join(
        [
            _chart_slide(
                chart_id="course-outcomes",
                filename="outcome_distribution.png",
                eyebrow="Course outcomes",
                title="How often did each recorded course outcome occur?",
                takeaway=(
                    f"Withdrawal accounted for {withdrawal_rate:.1%} of course "
                    "attempts, so it was not a rare edge case in these records."
                ),
                explanation=(
                    f"The bars count one outcome for each course attempt: "
                    f"{distinctions:,} distinction, {passes:,} pass, {failures:,} "
                    f"fail, and {withdrawals:,} withdrawal. A course attempt is one "
                    "student taking one course offering, not necessarily one unique "
                    "person."
                ),
                caution=(
                    "The chart reports historical outcomes. It does not explain why "
                    "a course attempt ended in withdrawal, failure, or success."
                ),
                alt=(
                    f"Bar chart of recorded course outcomes. Pass is highest at "
                    f"{passes:,} attempts, followed by withdrawal at {withdrawals:,}, "
                    f"fail at {failures:,}, and distinction at {distinctions:,}."
                ),
                caption=(
                    "Recorded outcomes across 32,593 course enrollments or attempts."
                ),
            ),
            _chart_slide(
                chart_id="weekly-activity",
                filename="weekly_engagement.png",
                eyebrow="Weekly online activity",
                title="How did recorded platform activity change across the term?",
                takeaway=(
                    f"The typical weekly median rose from {week_0_median:g} clicks "
                    f"in week 0 to {week_2_median:g} in week 2, then fell to "
                    f"{week_12_median:g} by week 12."
                ),
                explanation=(
                    "The median represents a typical active record. The upper "
                    "quartile represents a comparatively active portion of the "
                    f"records and remained at {week_12_p75:g} clicks in week 12. "
                    "The gap shows why one average cannot describe everyone."
                ),
                caution=(
                    "This chart summarizes active records. The forecasting data also "
                    "retains weeks with zero recorded activity so those weeks are not "
                    "silently dropped. Clicks indicate platform use, not attention, "
                    "understanding, motivation, or learning."
                ),
                alt=(
                    f"Line chart of weekly online-platform clicks. The median peaks "
                    f"at {week_2_median:g} in week 2 and falls to "
                    f"{week_12_median:g} by week 12, while the upper quartile stays "
                    "higher throughout."
                ),
                caption=(
                    "Median and upper-quartile clicks per active course-attempt record."
                ),
                reverse=True,
                technical_note=(
                    "The plotted lines are medians of module-presentation summaries. "
                    "The forecasting table uses one row per student attempt and course "
                    "week, including explicit zero-activity weeks."
                ),
            ),
            _chart_slide(
                chart_id="activity-consistency",
                filename="engagement_consistency.png",
                eyebrow="Activity consistency",
                title="Why separate activity volume from consistency?",
                takeaway=(
                    "Similar activity volumes appear across very different numbers "
                    "of active weeks, and the recorded outcome groups overlap heavily."
                ),
                explanation=(
                    "Two students can produce a similar number of clicks per active "
                    "week while one appears in many more course weeks. Volume and "
                    "consistency describe different aspects of the historical record, "
                    "so the analysis retains both."
                ),
                caution=(
                    "Neither axis measures learning quality, and neither measure alone "
                    "cleanly separates the four recorded course outcomes."
                ),
                alt=(
                    "Scatter plot comparing mean clicks in active weeks with number "
                    "of active course weeks. Points for distinction, pass, fail, and "
                    "withdrawal overlap across much of the chart."
                ),
                caption=(
                    "Each point is a course attempt; the horizontal axis uses a log "
                    "scale so low and high click volumes remain visible."
                ),
            ),
            _chart_slide(
                chart_id="missing-assessments",
                filename="assessment_missingness.png",
                eyebrow="Missing assessments",
                title="How much did missing assessment records differ by course?",
                takeaway=(
                    f"The percentage ranged from "
                    f"{lowest_missing['missing_rate']:.1%} in "
                    f"{lowest_missing['code_module']} "
                    f"{lowest_missing['code_presentation']} to "
                    f"{highest_missing['missing_rate']:.1%} in "
                    f"{highest_missing['code_module']} "
                    f"{highest_missing['code_presentation']}."
                ),
                explanation=(
                    "Each bar is the percentage of eligible student-assessment pairs "
                    "without a recorded submission in one course offering. The wide "
                    "range is why the analysis keeps course context rather than using "
                    "one universal missing-work rule."
                ),
                caution=(
                    "Differences may reflect course structure, assessment design, "
                    "deadlines, extensions, recording practices, and circumstances "
                    "not represented in the data. Missing work is not proof of low "
                    "effort."
                ),
                alt=(
                    f"Horizontal bar chart of missing assessment percentages by "
                    f"course offering, ranging from "
                    f"{lowest_missing['missing_rate']:.1%} to "
                    f"{highest_missing['missing_rate']:.1%}."
                ),
                caption=(
                    "OULAD calls courses modules and course offerings module "
                    "presentations."
                ),
                reverse=True,
            ),
            _chart_slide(
                chart_id="submission-timing",
                filename="submission_timing.png",
                eyebrow="Submission timing",
                title="Were assessments usually recorded before or after the deadline?",
                takeaway=(
                    f"Typical timing ranged from "
                    f"{abs(earliest_timing['median_submission_delay_days']):g} days "
                    f"early in {earliest_timing['code_module']} "
                    f"{earliest_timing['code_presentation']} to "
                    f"{latest_timing['median_submission_delay_days']:g} days late in "
                    "the latest-recorded offerings."
                ),
                explanation=(
                    "A negative value means the median submission was recorded before "
                    "the due date. A positive value means it was recorded after the "
                    "due date. Zero means the typical recorded submission occurred on "
                    "the deadline."
                ),
                caution=(
                    "The chart does not capture every extension, local policy, or "
                    "personal circumstance that may have affected timing."
                ),
                alt=(
                    f"Horizontal bar chart of median submission timing by course "
                    f"offering, ranging from "
                    f"{abs(earliest_timing['median_submission_delay_days']):g} days "
                    f"before the deadline to "
                    f"{latest_timing['median_submission_delay_days']:g} days after it."
                ),
                caption=(
                    "Median days relative to the assessment due date; negative values "
                    "mean early."
                ),
            ),
            _chart_slide(
                chart_id="withdrawal-timing",
                filename="withdrawal_alignment.png",
                eyebrow="Withdrawal timing",
                title="What did recorded activity look like near withdrawal?",
                takeaway=(
                    f"Median weekly clicks moved from {withdrawal_week_12:g} twelve "
                    f"weeks before unregistration to {withdrawal_week_1:g} in the "
                    "week immediately before it."
                ),
                explanation=(
                    "The chart aligns each withdrawing course attempt around the week "
                    "in which unregistration was recorded. This makes relative timing "
                    "comparable even when calendar dates differ."
                ),
                caution=(
                    "The pattern cannot explain why someone withdrew. Academic, "
                    "financial, employment, family, health, and other circumstances "
                    "may be absent from OULAD, and the number of observable attempts "
                    "changes across relative weeks."
                ),
                alt=(
                    f"Line chart of activity around withdrawal. Median weekly clicks "
                    f"decline from {withdrawal_week_12:g} twelve weeks before "
                    f"unregistration to {withdrawal_week_1:g} one week before it."
                ),
                caption=(
                    "Median recorded clicks in weeks aligned to the unregistration date."
                ),
                reverse=True,
            ),
        ]
    )

    forecast_slides = "\n".join(
        [
            _chart_slide(
                chart_id="model-comparison",
                filename="model_comparison.png",
                eyebrow="Model comparison",
                title="Did the historical records contain predictive information?",
                takeaway=(
                    f"The calibrated logistic model reached "
                    f"{calibrated['pr_auc']:.3f} precision-recall AUC, compared with "
                    f"an event prevalence baseline of {prevalence['pr_auc']:.3f}."
                ),
                explanation=(
                    f"The gradient-boosted challenger ranked highest at "
                    f"{boosted['pr_auc']:.3f}, while the calibrated logistic model "
                    "remains the interpretable probability reference. The later 2014J "
                    "course offerings were unseen during model training."
                ),
                caution=(
                    "The result shows some predictive information, not certainty, "
                    "causation, or deployment readiness. It is not a diagnosis of a "
                    "student."
                ),
                alt=(
                    f"Horizontal bar chart comparing held-out precision-recall AUC. "
                    f"The prevalence baseline is {prevalence['pr_auc']:.3f}, the "
                    f"calibrated logistic model is {calibrated['pr_auc']:.3f}, and "
                    f"the gradient-boosted model is highest at "
                    f"{boosted['pr_auc']:.3f}."
                ),
                caption=(
                    "Higher precision-recall AUC means better ranking of upcoming "
                    "negative assessment events."
                ),
                technical_note=(
                    "Precision-recall AUC summarizes how effectively a model ranks "
                    "records with an upcoming event above records without one. A score "
                    "of 1.0 is perfect; event prevalence supplies a useful baseline."
                ),
            ),
            _chart_slide(
                chart_id="calibration",
                filename="calibration.png",
                eyebrow="Probability quality",
                title="Did predicted probabilities resemble what happened?",
                takeaway=(
                    "Predicted and observed rates were close in lower-risk groups, "
                    "while the highest-risk group was overestimated."
                ),
                explanation=(
                    f"In the highest probability group, the mean prediction was "
                    f"{highest_calibration_bin['mean_predicted_probability']:.0%} and "
                    f"the observed event rate was "
                    f"{highest_calibration_bin['observed_event_rate']:.0%}. "
                    "Calibration asks whether a predicted 30% risk corresponds to an "
                    "event rate near 30% among similar records."
                ),
                caution=(
                    "A model can rank records reasonably well while still producing "
                    "imperfect probabilities. Ranking and probability accuracy are "
                    "different evaluation questions."
                ),
                alt=(
                    "Calibration plot comparing predicted probability with observed "
                    "event rate. Lower-probability groups stay near the perfect "
                    "calibration line, while the two highest groups fall below it."
                ),
                caption=(
                    "The dashed diagonal represents perfect agreement between "
                    "predicted and observed rates."
                ),
                reverse=True,
                technical_note=(
                    f"The calibrated logistic model's Brier score is "
                    f"{calibrated['brier']:.3f}. Brier score measures squared error "
                    "between predicted probabilities and outcomes; lower is better "
                    "and 0 is perfect."
                ),
            ),
            _chart_slide(
                chart_id="thresholds",
                filename="threshold_curve.png",
                eyebrow="Decision thresholds",
                title="What changes when the probability cutoff moves?",
                takeaway=(
                    "Flagging more records finds more eventual events, but it also "
                    "creates more false alarms."
                ),
                explanation=(
                    f"At a 50% cutoff, {int(threshold_50['records_flagged']):,} of "
                    f"117,186 weekly records were flagged "
                    f"({threshold_50['flag_rate']:.1%}). Precision was "
                    f"{threshold_50['precision']:.1%}, recall was "
                    f"{threshold_50['recall']:.1%}, and true alerts had a median "
                    f"{threshold_50['median_true_alert_lead_days']:.0f} days of lead "
                    "time."
                ),
                caution=(
                    "There is no universally correct threshold. The appropriate "
                    "cutoff depends on purpose, resources, consequences of errors, "
                    "and whether flagging would actually help."
                ),
                alt=(
                    "Line chart showing precision increasing and recall decreasing "
                    "as the percentage of weekly records flagged becomes smaller."
                ),
                caption=(
                    "A threshold is the predicted-probability cutoff used to decide "
                    "which records would be flagged."
                ),
                technical_note=(
                    "Precision is the share of flags that became events. Recall is "
                    "the share of all events that were flagged. A false alarm is a "
                    "flag without the event; a missed case is an event below the cutoff."
                ),
            ),
            _chart_slide(
                chart_id="forecast-timing",
                filename="performance_by_week.png",
                eyebrow="Forecast timing",
                title="How did forecast quality change as more history became available?",
                takeaway=(
                    "Later weeks generally provided better ranking, but a later "
                    "forecast also leaves less time for any useful response."
                ),
                explanation=(
                    "Early in a course, the model has relatively little activity and "
                    "assessment history. Later weekly records contain a longer "
                    "history, which can improve the forecast while reducing lead time."
                ),
                caution=(
                    "The chart describes held-out 2014J offerings only. Week-specific "
                    "performance may change in another institution, period, or course "
                    "design."
                ),
                alt=(
                    "Line chart showing held-out precision-recall AUC generally "
                    "increasing after course week 2, while Brier score remains lower "
                    "in later weeks."
                ),
                caption=(
                    "The practical tradeoff is earlier warning versus more complete "
                    "information."
                ),
                reverse=True,
            ),
        ]
    )

    page = Template(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta
    name="description"
    content="A plain-language presentation of an OULAD learning analytics project."
  >
  <title>Understanding Student Engagement and Course Outcomes | Jose Chavez</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #172126;
      --muted: #526168;
      --line: #c9d3d6;
      --paper: #f6f8f7;
      --white: #ffffff;
      --blue: #176b87;
      --blue-dark: #0d536c;
      --coral: #c94f32;
      --green: #2a7f62;
      --gold: #a86f0c;
      --forecast: #f4f7f9;
      --limits: #fff4ef;
    }

    * {
      box-sizing: border-box;
    }

    html {
      scroll-behavior: smooth;
    }

    body {
      margin: 0;
      color: var(--ink);
      background: var(--white);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
      line-height: 1.6;
    }

    img {
      max-width: 100%;
    }

    a {
      color: var(--blue-dark);
      text-underline-offset: 3px;
    }

    a:hover {
      color: var(--coral);
    }

    a:focus-visible,
    summary:focus-visible {
      outline: 3px solid var(--gold);
      outline-offset: 4px;
    }

    .skip-link {
      position: fixed;
      top: 10px;
      left: 10px;
      z-index: 20;
      padding: 10px 14px;
      color: var(--white);
      background: var(--ink);
      transform: translateY(-150%);
    }

    .skip-link:focus {
      transform: translateY(0);
    }

    .shell {
      width: min(1180px, calc(100% - 40px));
      margin: 0 auto;
    }

    .project-bar {
      border-bottom: 1px solid var(--line);
      background: var(--white);
    }

    .project-bar .shell {
      display: flex;
      min-height: 58px;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
    }

    .project-name {
      color: var(--ink);
      font-size: 0.88rem;
      font-weight: 800;
      text-decoration: none;
    }

    .project-links {
      display: flex;
      flex-wrap: wrap;
      gap: 18px;
      font-size: 0.84rem;
      font-weight: 700;
    }

    .hero {
      padding: 52px 0 44px;
      background: var(--paper);
    }

    .eyebrow {
      margin: 0 0 10px;
      color: var(--blue-dark);
      font-size: 0.74rem;
      font-weight: 800;
      text-transform: uppercase;
    }

    h1,
    h2,
    h3 {
      letter-spacing: 0;
    }

    h1 {
      max-width: 990px;
      margin: 0 0 20px;
      font-size: 3.7rem;
      line-height: 1.02;
    }

    h2 {
      max-width: 820px;
      margin: 0 0 16px;
      font-size: 2.55rem;
      line-height: 1.08;
    }

    h3 {
      margin: 8px 0 18px;
      font-size: 1.8rem;
      line-height: 1.18;
    }

    .hero-intro {
      max-width: 820px;
      margin: 0;
      color: var(--muted);
      font-size: 1.2rem;
    }

    .responsible-use {
      max-width: 850px;
      margin: 22px 0 0;
      padding: 14px 0 14px 20px;
      border-left: 4px solid var(--coral);
      color: var(--ink);
      font-weight: 650;
    }

    .page-nav {
      margin-top: 28px;
    }

    .page-nav ul {
      display: flex;
      flex-wrap: wrap;
      gap: 9px;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .page-nav a {
      display: inline-flex;
      min-height: 42px;
      align-items: center;
      padding: 8px 13px;
      border: 1px solid var(--line);
      border-radius: 4px;
      color: var(--ink);
      background: var(--white);
      font-size: 0.84rem;
      font-weight: 750;
      text-decoration: none;
    }

    .page-nav a:hover {
      border-color: var(--blue);
      color: var(--blue-dark);
    }

    .section {
      padding: 72px 0;
      border-bottom: 1px solid var(--line);
    }

    .section-alt {
      background: var(--paper);
      box-shadow: 0 0 0 100vmax var(--paper);
      clip-path: inset(0 -100vmax);
    }

    .why-section {
      padding-top: 48px;
      padding-bottom: 48px;
    }

    .why-section .section-head {
      margin-bottom: 0;
    }

    .section-forecast {
      background: var(--forecast);
      box-shadow: 0 0 0 100vmax var(--forecast);
      clip-path: inset(0 -100vmax);
    }

    .section-head {
      max-width: 820px;
      margin-bottom: 38px;
    }

    .section-head > p:last-child,
    .chart-copy > p:not(.eyebrow, .takeaway, .interpretation-note) {
      color: var(--muted);
    }

    .question-list {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin: 0;
      padding: 0;
      border-top: 1px solid var(--line);
      list-style: none;
      counter-reset: question;
    }

    .question-list li {
      position: relative;
      min-width: 0;
      padding: 21px 22px 21px 52px;
      border-right: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      counter-increment: question;
    }

    .question-list li:nth-child(2n) {
      border-right: 0;
    }

    .question-list li::before {
      position: absolute;
      top: 21px;
      left: 8px;
      color: var(--coral);
      font-size: 0.74rem;
      font-weight: 800;
      content: "0" counter(question);
    }

    .dataset-intro {
      max-width: 880px;
      color: var(--muted);
      font-size: 1.05rem;
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin: 36px 0 22px;
      border-top: 1px solid var(--line);
      border-left: 1px solid var(--line);
    }

    .metrics div {
      min-width: 0;
      padding: 21px;
      border-right: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      background: var(--white);
    }

    .metrics strong {
      display: block;
      font-size: 1.7rem;
      line-height: 1.1;
    }

    .metrics span,
    .metrics small {
      display: block;
    }

    .metrics span {
      margin-top: 5px;
      font-weight: 750;
    }

    .metrics small {
      margin-top: 4px;
      color: var(--muted);
      font-size: 0.78rem;
    }

    .source-note {
      max-width: 880px;
      margin: 0;
      color: var(--muted);
      font-size: 0.9rem;
    }

    .finding-summary {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0 36px;
      margin: 0;
      padding: 0;
      border-top: 1px solid var(--line);
      list-style: none;
    }

    .finding-summary li {
      min-width: 0;
      padding: 22px 0;
      border-bottom: 1px solid var(--line);
    }

    .finding-summary strong {
      display: block;
      margin-bottom: 6px;
      font-size: 1.05rem;
    }

    .finding-summary span {
      color: var(--muted);
    }

    .chart-sequence {
      border-top: 1px solid var(--line);
    }

    .chart-slide {
      display: grid;
      grid-template-columns: minmax(0, 0.78fr) minmax(0, 1.22fr);
      gap: 52px;
      align-items: center;
      padding: 58px 0;
      border-bottom: 1px solid var(--line);
    }

    .chart-slide-reverse .chart-copy {
      order: 2;
    }

    .chart-slide-reverse figure {
      order: 1;
    }

    .chart-copy {
      min-width: 0;
    }

    .takeaway {
      margin: 0 0 18px;
      padding-left: 16px;
      border-left: 3px solid var(--gold);
      color: var(--ink);
      font-size: 1.08rem;
      font-weight: 750;
      line-height: 1.5;
    }

    .interpretation-note {
      margin: 22px 0 0;
      padding-top: 16px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 0.88rem;
    }

    .interpretation-note strong {
      color: var(--ink);
    }

    figure {
      min-width: 0;
      margin: 0;
      border: 1px solid var(--line);
      border-radius: 4px;
      background: var(--white);
      overflow: hidden;
    }

    figure img {
      display: block;
      width: 100%;
      height: auto;
    }

    figcaption {
      padding: 14px 16px 17px;
      color: var(--muted);
      font-size: 0.84rem;
    }

    details {
      margin-top: 20px;
      border-top: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
    }

    summary {
      padding: 12px 0;
      color: var(--blue-dark);
      font-weight: 800;
      cursor: pointer;
    }

    details p {
      margin: 0;
      padding: 0 0 16px;
      color: var(--muted);
      font-size: 0.9rem;
    }

    .forecast-question {
      max-width: 940px;
      padding: 26px 0 26px 24px;
      border-left: 5px solid var(--blue);
    }

    .forecast-question h3 {
      margin-top: 0;
    }

    .forecast-question p {
      max-width: 820px;
      color: var(--muted);
    }

    .evaluation-flow,
    .method-flow {
      display: grid;
      margin: 38px 0;
      border-top: 1px solid var(--line);
      border-left: 1px solid var(--line);
    }

    .evaluation-flow {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .method-flow {
      grid-template-columns: repeat(5, minmax(0, 1fr));
    }

    .evaluation-flow div,
    .method-flow div {
      min-width: 0;
      padding: 20px;
      border-right: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      background: var(--white);
    }

    .evaluation-flow span,
    .method-flow span {
      display: block;
      margin-bottom: 14px;
      color: var(--coral);
      font-size: 0.73rem;
      font-weight: 850;
    }

    .evaluation-flow strong,
    .method-flow strong {
      display: block;
      margin-bottom: 6px;
    }

    .evaluation-flow p,
    .method-flow p {
      margin: 0;
      color: var(--muted);
      font-size: 0.84rem;
    }

    .model-summary {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 28px;
      margin-top: 34px;
    }

    .model-summary div {
      padding: 22px 0;
      border-top: 4px solid var(--green);
      border-bottom: 1px solid var(--line);
    }

    .model-summary strong {
      display: block;
      font-size: 2rem;
    }

    .model-summary span {
      display: block;
      margin: 5px 0 10px;
      font-weight: 800;
    }

    .model-summary p {
      margin: 0;
      color: var(--muted);
      font-size: 0.88rem;
    }

    .method-intro {
      max-width: 850px;
      color: var(--muted);
      font-size: 1.04rem;
    }

    .technology-line {
      margin: 26px 0 0;
      color: var(--muted);
    }

    .technology-line strong {
      color: var(--ink);
    }

    .limits {
      background: var(--limits);
      box-shadow: 0 0 0 100vmax var(--limits);
      clip-path: inset(0 -100vmax);
      border-top: 5px solid var(--coral);
    }

    .limits-grid,
    .skills-list {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0 36px;
      margin: 30px 0 0;
      padding: 0;
      border-top: 1px solid var(--line);
      list-style: none;
    }

    .limits-grid li,
    .skills-list li {
      position: relative;
      padding: 16px 0 16px 24px;
      border-bottom: 1px solid var(--line);
    }

    .limits-grid li::before,
    .skills-list li::before {
      position: absolute;
      left: 0;
      color: var(--coral);
      font-weight: 900;
      content: "/";
    }

    .skills-list li::before {
      color: var(--green);
      content: "+";
    }

    .glossary {
      margin-top: 0;
      border: 0;
    }

    .glossary summary {
      display: inline-flex;
      min-height: 44px;
      align-items: center;
      padding: 10px 0;
      font-size: 1rem;
    }

    .terms {
      display: grid;
      grid-template-columns: minmax(180px, 0.32fr) minmax(0, 1fr);
      margin: 24px 0 0;
      border-top: 1px solid var(--line);
    }

    .terms dt,
    .terms dd {
      margin: 0;
      padding: 13px 0;
      border-bottom: 1px solid var(--line);
    }

    .terms dt {
      padding-right: 20px;
      font-weight: 850;
    }

    .terms dd {
      color: var(--muted);
    }

    .closing-links {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 30px;
    }

    .button-link {
      display: inline-flex;
      min-height: 44px;
      align-items: center;
      padding: 10px 15px;
      border: 1px solid var(--blue);
      border-radius: 4px;
      color: var(--blue-dark);
      background: var(--white);
      font-weight: 800;
      text-decoration: none;
    }

    footer {
      padding: 34px 0 56px;
      color: var(--muted);
      background: var(--paper);
      font-size: 0.86rem;
    }

    footer p {
      margin: 0;
    }

    @media (max-width: 900px) {
      h1 {
        font-size: 3.15rem;
      }

      .chart-slide,
      .method-flow {
        grid-template-columns: 1fr;
      }

      .chart-slide-reverse .chart-copy,
      .chart-slide-reverse figure {
        order: initial;
      }

      .method-flow div {
        display: grid;
        grid-template-columns: 36px minmax(0, 1fr);
        gap: 0 8px;
      }

      .method-flow span {
        grid-row: span 2;
      }
    }

    @media (max-width: 680px) {
      .shell {
        width: min(100% - 24px, 1180px);
      }

      .project-bar .shell {
        align-items: flex-start;
        flex-direction: column;
        gap: 5px;
        padding: 12px 0;
      }

      .project-links {
        gap: 12px;
      }

      .hero,
      .section {
        padding: 48px 0;
      }

      .hero {
        padding: 34px 0;
      }

      h1 {
        font-size: 2.2rem;
      }

      h2 {
        font-size: 2rem;
      }

      h3 {
        font-size: 1.45rem;
      }

      .hero-intro {
        font-size: 1.04rem;
        line-height: 1.5;
      }

      .responsible-use {
        margin-top: 20px;
        padding: 12px 0 12px 18px;
        line-height: 1.5;
      }

      .page-nav {
        display: none;
      }

      .why-section {
        padding-top: 38px;
        padding-bottom: 38px;
      }

      .question-list,
      .metrics,
      .finding-summary,
      .evaluation-flow,
      .model-summary,
      .limits-grid,
      .skills-list,
      .terms {
        grid-template-columns: 1fr;
      }

      .question-list li {
        border-right: 0;
      }

      .metrics {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .chart-slide {
        gap: 28px;
        padding: 44px 0;
      }

      .terms dt {
        padding-bottom: 3px;
        border-bottom: 0;
      }

      .terms dd {
        padding-top: 0;
      }
    }

    @media (prefers-reduced-motion: reduce) {
      html {
        scroll-behavior: auto;
      }
    }
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to project content</a>

  <nav class="project-bar" aria-label="Project resources">
    <div class="shell">
      <a class="project-name" href="/#/data-science/learning-analytics">
        Jose Chavez / Learning Analytics
      </a>
      <div class="project-links">
        <a href="/#/data-science/learning-analytics">Project case study</a>
        <a href="$repository">GitHub repository</a>
        <a href="$repository/blob/main/docs/methodology.md">Methodology</a>
      </div>
    </div>
  </nav>

  <header class="hero">
    <div class="shell">
      <p class="eyebrow">Learning Analytics Project</p>
      <h1>Understanding Student Engagement, Assessments, and Course Outcomes</h1>
      <p class="hero-intro">
        This project uses anonymized historical online-course data to study how
        recorded platform activity and assessment behavior relate to course
        outcomes. It also tests whether information available during a course can
        help estimate the risk of a poor result on the next assessment.
      </p>
      <p class="responsible-use">
        This is a historical research and portfolio project. It does not monitor
        current students, recommend interventions, or make decisions about individuals.
      </p>
      <nav class="page-nav" aria-label="Presentation sections">
        <ul>
          <li><a href="#questions">Questions</a></li>
          <li><a href="#data">Data</a></li>
          <li><a href="#key-findings">Key findings</a></li>
          <li><a href="#forecasting">Forecasting</a></li>
          <li><a href="#methods">How it was built</a></li>
          <li><a href="#limits">Limitations</a></li>
        </ul>
      </nav>
    </div>
  </header>

  <main id="main-content">
    <section class="section why-section shell" aria-labelledby="why-title">
      <div class="section-head">
        <p class="eyebrow">Why this matters</p>
        <h2 id="why-title">Online-course data is easy to count and easy to misread</h2>
        <p>
          Learning platforms create detailed records, but a click is not the same as
          learning and a forecast is not the same as an explanation. This project
          shows how those records can be organized into useful historical evidence
          while keeping context, uncertainty, and responsible limits visible.
        </p>
      </div>
    </section>

    <section class="section shell" id="questions" aria-labelledby="questions-title">
      <div class="section-head">
        <p class="eyebrow">What this project asks</p>
        <h2 id="questions-title">Five questions guide the analysis</h2>
        <p>
          These questions organize the charts that follow, moving from description
          to forecasting without treating a statistical association as a cause.
        </p>
      </div>
      <ol class="question-list">
        <li>How did recorded online activity change across the course?</li>
        <li>How did missing assessments and submission timing differ across courses?</li>
        <li>What did recorded activity look like near withdrawal?</li>
        <li>Could information available so far help forecast the next assessment?</li>
        <li>How reliable were the model's rankings and predicted probabilities?</li>
      </ol>
    </section>

    <section class="section section-alt shell" id="data" aria-labelledby="data-title">
      <div class="section-head">
        <p class="eyebrow">The historical data</p>
        <h2 id="data-title">What is OULAD?</h2>
        <p class="dataset-intro">
          The Open University Learning Analytics Dataset (OULAD) is an anonymized
          historical dataset containing course information, assessment records,
          recorded student outcomes, and activity on an online learning platform.
          It covers selected Open University course offerings from 2013 and 2014.
        </p>
      </div>
      <dl class="metrics">
        <div>
          <dt><strong>$modules</strong><span>courses</span></dt>
          <dd><small>Called modules in OULAD</small></dd>
        </div>
        <div>
          <dt><strong>$presentations</strong><span>course offerings</span></dt>
          <dd><small>Called module presentations</small></dd>
        </div>
        <div>
          <dt><strong>$students</strong><span>individual students</span></dt>
          <dd><small>Unique anonymized identifiers</small></dd>
        </div>
        <div>
          <dt><strong>$attempts</strong><span>course enrollments or attempts</span></dt>
          <dd><small>One student taking one offering</small></dd>
        </div>
        <div>
          <dt><strong>$assessments</strong><span>assessments</span></dt>
          <dd><small>Coursework and exam definitions</small></dd>
        </div>
        <div>
          <dt><strong>$activity_millions</strong><span>recorded online interactions</span></dt>
          <dd><small>$activity_exact exact activity records</small></dd>
        </div>
      </dl>
      <p class="source-note">
        The same student can appear in more than one course attempt. A recorded click
        indicates platform use, but it does not directly measure effort, motivation,
        attention, understanding, learning, or offline study.
        <a href="$source_url">View the official UCI source.</a>
      </p>
    </section>

    <section
      class="section shell"
      id="key-findings"
      aria-labelledby="key-findings-title"
    >
      <div class="section-head">
        <p class="eyebrow">What I found</p>
        <h2 id="key-findings-title">The main findings in one minute</h2>
        <p>
          Each statement below comes from the downloaded archive, PostgreSQL analysis
          tables, or saved held-out model results.
        </p>
      </div>
      <ul class="finding-summary">
        <li>
          <strong>Withdrawal was a substantial recorded outcome.</strong>
          <span>$withdrawals of $attempts attempts, or $withdrawal_rate, ended in
          withdrawal. The data does not record every reason why.</span>
        </li>
        <li>
          <strong>Recorded activity changed over the course.</strong>
          <span>The typical active-record median peaked at $week_2_median clicks in
          week 2 and was $week_12_median by week 12.</span>
        </li>
        <li>
          <strong>Missing assessments varied greatly by course offering.</strong>
          <span>Observed rates ranged from $missing_low to $missing_high, so one
          universal missing-work rule would ignore course context.</span>
        </li>
        <li>
          <strong>Recorded activity became quieter near withdrawal.</strong>
          <span>Median clicks moved from $withdrawal_week_12 twelve weeks before
          unregistration to $withdrawal_week_1 one week before it.</span>
        </li>
        <li>
          <strong>The assessment forecast found some useful signal.</strong>
          <span>The interpretable calibrated model reached $calibrated_pr precision-recall
          AUC against a $prevalence_pr prevalence baseline.</span>
        </li>
        <li>
          <strong>The forecast remained uncertain and context-specific.</strong>
          <span>Probability errors remained, performance changed by week, and results
          may not transfer to another institution or period.</span>
        </li>
      </ul>
    </section>

    <section class="section section-alt shell" aria-labelledby="analysis-title">
      <div class="section-head">
        <p class="eyebrow">The descriptive story</p>
        <h2 id="analysis-title">What the historical records show</h2>
        <p>
          Each chart answers one project question. The takeaway appears first, followed
          by what was measured and the most important interpretation limit.
        </p>
      </div>
      <div class="chart-sequence">
        $analysis_slides
      </div>
    </section>

    <section
      class="section section-forecast shell"
      id="forecasting"
      aria-labelledby="forecasting-title"
    >
      <div class="section-head">
        <p class="eyebrow">Forecasting</p>
        <h2 id="forecasting-title">
          Can course information available so far help forecast the next assessment?
        </h2>
        <p>
          The historical records contained some useful predictive information, but
          the forecast remained uncertain. It should be treated as an analytical
          demonstration, not a diagnosis or an automated decision about an individual.
        </p>
      </div>

      <div class="forecast-question">
        <h3>What exactly is being forecast?</h3>
        <p>
          At the end of each course week, the model estimates whether the next non-exam
          assessment will be missing by its due date or will receive a recorded score
          below 40. Each weekly snapshot represents what would have been known by the
          end of that week. Later activity and future assessment results are excluded.
        </p>
      </div>

      <div class="evaluation-flow" aria-label="Model evaluation sequence">
        <div>
          <span>01</span>
          <strong>Learn from 2013</strong>
          <p>The models were trained using earlier course offerings.</p>
        </div>
        <div>
          <span>02</span>
          <strong>Choose with 2014B</strong>
          <p>A separate group supported model selection and probability calibration.</p>
        </div>
        <div>
          <span>03</span>
          <strong>Test on unseen 2014J</strong>
          <p>Complete later offerings were held back for the final evaluation.</p>
        </div>
      </div>
      <p class="source-note">
        Weekly records from the same course offering were kept together instead of
        being randomly scattered across training and testing. This temporal held-out
        design reduces the chance that closely related records appear on both sides of
        the evaluation.
      </p>

      <div class="model-summary" aria-label="Interpretable model summary">
        <div>
          <strong>$calibrated_pr</strong>
          <span>Precision-recall AUC</span>
          <p>
            Summarizes how well the model ranks upcoming negative assessment events
            above other records. Higher is better; 1.0 is perfect. The held-out event
            prevalence baseline was $prevalence_pr.
          </p>
        </div>
        <div>
          <strong>$calibrated_brier</strong>
          <span>Brier score</span>
          <p>
            Measures how close predicted probabilities were to what happened. Lower
            is better; 0 represents perfect probability predictions.
          </p>
        </div>
      </div>

      <div class="chart-sequence">
        $forecast_slides
      </div>
    </section>

    <section class="section shell" id="methods" aria-labelledby="methods-title">
      <div class="section-head">
        <p class="eyebrow">How I built the analysis</p>
        <h2 id="methods-title">A reproducible path from source files to findings</h2>
        <p class="method-intro">
          I used Python to inspect and validate the original files, PostgreSQL and SQL
          to organize the data into consistent analysis tables, and Python again for
          statistics, visualization, forecasting, and model evaluation.
        </p>
      </div>
      <div class="method-flow" aria-label="Analysis workflow">
        <div>
          <span>01</span>
          <strong>OULAD source</strong>
          <p>Checksum-verified historical CSV files</p>
        </div>
        <div>
          <span>02</span>
          <strong>Python audit</strong>
          <p>Rows, fields, missing values, and source scale</p>
        </div>
        <div>
          <span>03</span>
          <strong>PostgreSQL</strong>
          <p>Raw, staging, and relational core tables</p>
        </div>
        <div>
          <span>04</span>
          <strong>SQL analysis</strong>
          <p>Quality tests, analytical tables, and weekly snapshots</p>
        </div>
        <div>
          <span>05</span>
          <strong>Python outputs</strong>
          <p>Statistics, charts, forecasts, and evaluation</p>
        </div>
      </div>
      <p class="technology-line">
        <strong>Technologies and methods:</strong> PostgreSQL 16, SQL, Python, pandas,
        scikit-learn, relational modeling, window functions, time-aware feature
        engineering, probability calibration, threshold analysis, and accessible
        data visualization.
      </p>
      <details>
        <summary>Technical note: consistent analytical definitions</summary>
        <p>
          SQL defines the analytical contract, meaning that key metrics, table grains,
          and weekly records are created through consistent, reviewable definitions
          rather than being recalculated differently for each chart. The project
          includes six database schemas, materialized analysis tables, indexes,
          captured query plans, and twenty-four quality profiles and tests.
        </p>
      </details>
      <div class="closing-links">
        <a class="button-link" href="$repository/blob/main/docs/sql-mastery.md">
          Read the SQL design
        </a>
        <a class="button-link" href="$repository/blob/main/sql/gallery/queries.sql">
          Open the SQL query gallery
        </a>
        <a class="button-link" href="$repository/blob/main/docs/model-card.md">
          Read the model card
        </a>
      </div>
    </section>

    <section class="section limits shell" id="limits" aria-labelledby="limits-title">
      <div class="section-head">
        <p class="eyebrow">Responsible interpretation</p>
        <h2 id="limits-title">What this analysis cannot tell us</h2>
        <p>
          <strong>Clicks are traces, not explanations.</strong> The project preserves
          uncertainty because the records omit much of the context needed to understand
          any individual experience.
        </p>
      </div>
      <ul class="limits-grid">
        <li>The anonymized data covers selected Open University courses from 2013-2014.</li>
        <li>Platform clicks do not directly measure learning, attention, or motivation.</li>
        <li>Students may study offline or use resources not represented in the records.</li>
        <li>Reasons for withdrawal are not fully represented in the dataset.</li>
        <li>Course differences may reflect design, deadlines, policy, or recording practice.</li>
        <li>Historical associations do not establish that one behavior caused an outcome.</li>
        <li>Results may not generalize to other years, institutions, or course structures.</li>
        <li>The forecasts should not be used as an automated decision system.</li>
        <li>
          Predictions are not statements about character, intelligence, motivation,
          ability, or potential.
        </li>
        <li>
          Fairness in another setting would require local validation, governance, and
          meaningful participation from affected people.
        </li>
      </ul>
    </section>

    <section class="section shell" id="skills" aria-labelledby="skills-title">
      <div class="section-head">
        <p class="eyebrow">Professional relevance</p>
        <h2 id="skills-title">What this project demonstrates</h2>
        <p>
          The value of the project is not only the final model. It is the complete,
          reviewable process from a large relational source to a careful public
          explanation.
        </p>
      </div>
      <ul class="skills-list">
        <li>Translating a complex relational dataset into usable analytical tables</li>
        <li>Designing reproducible PostgreSQL and SQL data pipelines</li>
        <li>Conducting exploratory and statistical analysis</li>
        <li>Creating weekly, time-aware forecasting features</li>
        <li>Preventing future information from leaking into model training</li>
        <li>Evaluating ranking, probability quality, thresholds, and timing</li>
        <li>Communicating uncertainty, responsible-use limits, and negative results</li>
        <li>Presenting one analysis to both technical and nontechnical audiences</li>
      </ul>
    </section>

    <section class="section section-alt shell" id="glossary" aria-labelledby="glossary-title">
      <div class="section-head">
        <p class="eyebrow">Plain-language reference</p>
        <h2 id="glossary-title">Terms used on this page</h2>
      </div>
      <details class="glossary">
        <summary>Open the compact glossary</summary>
        <dl class="terms">
          <dt>OULAD</dt>
          <dd>The Open University Learning Analytics Dataset, an anonymized historical dataset.</dd>
          <dt>Course or module</dt>
          <dd>A course. OULAD uses the term module.</dd>
          <dt>Course offering</dt>
          <dd>One course delivered in one period. OULAD calls this a presentation.</dd>
          <dt>Course attempt</dt>
          <dd>One student taking one course offering. A student can have multiple attempts.</dd>
          <dt>Online activity or click</dt>
          <dd>
            A recorded interaction with the online learning platform, not a measure
            of attention.
          </dd>
          <dt>Weekly snapshot</dt>
          <dd>A record of information available at the end of a particular course week.</dd>
          <dt>Forecast target</dt>
          <dd>The event being estimated: a missing or below-40 next non-exam assessment.</dd>
          <dt>Held-out test data</dt>
          <dd>Later course offerings kept unseen until the final model evaluation.</dd>
          <dt>Precision</dt>
          <dd>The share of flagged weekly records that later became target events.</dd>
          <dt>Recall</dt>
          <dd>The share of all target events that the chosen cutoff flagged.</dd>
          <dt>Precision-recall AUC</dt>
          <dd>A summary of how well the model ranks target events above other records.</dd>
          <dt>Brier score</dt>
          <dd>A measure of predicted-probability error. Lower values are better.</dd>
          <dt>Calibration</dt>
          <dd>Agreement between predicted probabilities and observed event rates.</dd>
          <dt>Threshold</dt>
          <dd>The probability cutoff above which a weekly record would be flagged.</dd>
          <dt>False alarm</dt>
          <dd>A flagged record for which the target event did not occur.</dd>
          <dt>Missed case</dt>
          <dd>A target event that fell below the chosen probability cutoff.</dd>
        </dl>
      </details>
    </section>
  </main>

  <footer>
    <div class="shell">
      <p>
        Generated from versioned PostgreSQL analysis tables and saved Python outputs.
        Source, tests, and complete methodology are available in the
        <a href="$repository">public project repository</a>.
      </p>
    </div>
  </footer>
</body>
</html>
"""
    ).substitute(
        repository=REPOSITORY,
        source_url=SOURCE_URL,
        modules=f"{scale['modules']:,}",
        presentations=f"{scale['module_presentations']:,}",
        students=f"{scale['unique_students']:,}",
        attempts=f"{scale['student_module_attempts']:,}",
        assessments=f"{scale['assessments']:,}",
        activity_millions=f"{scale['activity_records'] / 1_000_000:.1f} million",
        activity_exact=f"{scale['activity_records']:,}",
        withdrawals=f"{withdrawals:,}",
        withdrawal_rate=f"{withdrawal_rate:.1%}",
        week_2_median=f"{week_2_median:g}",
        week_12_median=f"{week_12_median:g}",
        missing_low=f"{lowest_missing['missing_rate']:.1%}",
        missing_high=f"{highest_missing['missing_rate']:.1%}",
        withdrawal_week_12=f"{withdrawal_week_12:g}",
        withdrawal_week_1=f"{withdrawal_week_1:g}",
        calibrated_pr=f"{calibrated['pr_auc']:.3f}",
        prevalence_pr=f"{prevalence['pr_auc']:.3f}",
        calibrated_brier=f"{calibrated['brier']:.3f}",
        analysis_slides=analysis_slides,
        forecast_slides=forecast_slides,
    )

    (output_dir / "index.html").write_text(page, encoding="utf-8")
