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
    "model_overview.png",
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
            <summary>How I worked this out</summary>
            <p>{html.escape(technical_note)}</p>
          </details>"""

    return f"""<article class="chart-slide{reverse_class}" id="{html.escape(chart_id)}">
        <div class="chart-copy">
          <p class="eyebrow">{html.escape(eyebrow)}</p>
          <h3>{html.escape(title)}</h3>
          <p class="takeaway">{html.escape(takeaway)}</p>
          <p>{html.escape(explanation)}</p>
          <p class="interpretation-note">
            <strong>What I would not assume:</strong> {html.escape(caution)}
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
    public_summary = json.loads(
        (settings.reports_dir / "public-summary.json").read_text(encoding="utf-8")
    )
    model_explanation = public_summary["modelExplanation"]
    model_families = "\n".join(
        f"""<li>
            <strong>{html.escape(family["name"])}.</strong>
            {html.escape(family["plainLanguage"])}
            <span>{html.escape(family["reason"])}</span>
          </li>"""
        for family in model_explanation["families"]
    )

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
    test_snapshots = int(calibrated["n"])
    test_events = int(round(float(prevalence["prevalence"]) * test_snapshots))
    records_flagged = int(threshold_50["records_flagged"])
    true_alerts = int(threshold_50["true_alerts"])

    withdrawal_metrics = _read_table(settings, "withdrawal_model_metrics.csv")
    withdrawal_test = withdrawal_metrics[
        (withdrawal_metrics["model"] == "withdrawal_logistic_regression")
        & (withdrawal_metrics["split"] == "test")
    ].iloc[0]

    calibration = _read_table(settings, "calibration_bins.csv")
    highest_calibration_bin = calibration.iloc[-1]

    analysis_slides = "\n".join(
        [
            _chart_slide(
                chart_id="course-outcomes",
                filename="outcome_distribution.png",
                eyebrow="Course outcomes",
                title="I began by looking at how each course attempt ended",
                takeaway=(
                    f"The first thing that stood out to me was withdrawal: it "
                    f"accounted for {withdrawal_rate:.1%} of all course attempts."
                ),
                explanation=(
                    f"I counted one outcome for each course attempt: "
                    f"{distinctions:,} distinction, {passes:,} pass, {failures:,} "
                    f"fail, and {withdrawals:,} withdrawal. Here, a course attempt "
                    "means one student taking one course offering. It does not "
                    "necessarily mean one unique person."
                ),
                caution=(
                    "I can see how each attempt ended, but these records do not tell "
                    "me why someone withdrew, failed, passed, or earned a distinction."
                ),
                alt=(
                    f"Bar chart of recorded course outcomes. Pass is highest at "
                    f"{passes:,} attempts, followed by withdrawal at {withdrawals:,}, "
                    f"fail at {failures:,}, and distinction at {distinctions:,}."
                ),
                caption=(
                    "How 32,593 recorded course attempts ended."
                ),
            ),
            _chart_slide(
                chart_id="weekly-activity",
                filename="weekly_engagement.png",
                eyebrow="Weekly online activity",
                title="Next, I followed online activity from week to week",
                takeaway=(
                    f"I found that the typical weekly median rose from "
                    f"{week_0_median:g} clicks "
                    f"in week 0 to {week_2_median:g} in week 2, then fell to "
                    f"{week_12_median:g} by week 12."
                ),
                explanation=(
                    "I used the median to describe a typical active record, then "
                    "compared it with the more active quarter of the records. That "
                    f"group still had {week_12_p75:g} clicks in week 12. The gap "
                    "reminded me that one average could not describe everyone."
                ),
                caution=(
                    "A click only tells me that the platform recorded an action. It "
                    "does not tell me whether someone was attentive, confused, "
                    "motivated, learning offline, or learning at all."
                ),
                alt=(
                    f"Line chart of weekly online-platform clicks. The median peaks "
                    f"at {week_2_median:g} in week 2 and falls to "
                    f"{week_12_median:g} by week 12, while the upper quartile stays "
                    "higher throughout."
                ),
                caption=(
                    "A typical level of recorded activity and a more active comparison."
                ),
                reverse=True,
                technical_note=(
                    "For the chart, I used medians from each course offering. For the "
                    "forecast, I kept one row for every student attempt and course "
                    "week, including weeks with no recorded activity."
                ),
            ),
            _chart_slide(
                chart_id="activity-consistency",
                filename="engagement_consistency.png",
                eyebrow="Activity consistency",
                title="I checked whether regular activity told a different story",
                takeaway=(
                    "Students with similar click totals could have very different "
                    "numbers of active weeks, and the outcome groups still overlapped."
                ),
                explanation=(
                    "That showed me that amount and regularity were not the same "
                    "thing. One student might appear steadily across many weeks while "
                    "another produces similar activity in a much shorter span, so I "
                    "kept both measures."
                ),
                caution=(
                    "Neither measure tells me the quality of someone’s learning, and "
                    "neither one neatly separates the four recorded outcomes."
                ),
                alt=(
                    "Scatter plot comparing mean clicks in active weeks with number "
                    "of active course weeks. Points for distinction, pass, fail, and "
                    "withdrawal overlap across much of the chart."
                ),
                caption=(
                    "Each point is one course attempt. The scale lets low and high "
                    "click totals remain visible together."
                ),
            ),
            _chart_slide(
                chart_id="missing-assessments",
                filename="assessment_missingness.png",
                eyebrow="Missing assessments",
                title="Missing work looked very different from course to course",
                takeaway=(
                    f"I found percentages ranging from "
                    f"{lowest_missing['missing_rate']:.1%} in "
                    f"{lowest_missing['code_module']} "
                    f"{lowest_missing['code_presentation']} to "
                    f"{highest_missing['missing_rate']:.1%} in "
                    f"{highest_missing['code_module']} "
                    f"{highest_missing['code_presentation']}."
                ),
                explanation=(
                    "Each bar shows the share of expected assessments with no "
                    "submission recorded for one course offering. The range was wide "
                    "enough that I did not think one missing-work rule would be fair "
                    "or useful across every course."
                ),
                caution=(
                    "A missing record is not proof of low effort. Course design, "
                    "deadlines, extensions, recording practices, and personal "
                    "circumstances may all be part of the story."
                ),
                alt=(
                    f"Horizontal bar chart of missing assessment percentages by "
                    f"course offering, ranging from "
                    f"{lowest_missing['missing_rate']:.1%} to "
                    f"{highest_missing['missing_rate']:.1%}."
                ),
                caption=(
                    "OULAD uses the word module for a course and presentation for one "
                    "offering of that course."
                ),
                reverse=True,
            ),
            _chart_slide(
                chart_id="submission-timing",
                filename="submission_timing.png",
                eyebrow="Submission timing",
                title="I also looked at when work was submitted",
                takeaway=(
                    f"The typical timing ranged from "
                    f"{abs(earliest_timing['median_submission_delay_days']):g} days "
                    f"early in {earliest_timing['code_module']} "
                    f"{earliest_timing['code_presentation']} to "
                    f"{latest_timing['median_submission_delay_days']:g} days late in "
                    "the latest-recorded offerings."
                ),
                explanation=(
                    "I read a negative number as days before the deadline and a "
                    "positive number as days after it. Zero means the typical "
                    "recorded submission landed on the due date."
                ),
                caution=(
                    "I cannot see every extension, course policy, or personal "
                    "circumstance that may have affected when work was submitted."
                ),
                alt=(
                    f"Horizontal bar chart of median submission timing by course "
                    f"offering, ranging from "
                    f"{abs(earliest_timing['median_submission_delay_days']):g} days "
                    f"before the deadline to "
                    f"{latest_timing['median_submission_delay_days']:g} days after it."
                ),
                caption=(
                    "Typical days before or after the due date. Negative means early."
                ),
            ),
            _chart_slide(
                chart_id="withdrawal-timing",
                filename="withdrawal_alignment.png",
                eyebrow="Withdrawal timing",
                title="Finally, I looked at the weeks leading up to withdrawal",
                takeaway=(
                    f"I saw median weekly clicks move from {withdrawal_week_12:g} twelve "
                    f"weeks before unregistration to {withdrawal_week_1:g} in the "
                    "week immediately before it."
                ),
                explanation=(
                    "I lined up each withdrawing course attempt around its recorded "
                    "unregistration week. That let me compare the lead-up even when "
                    "the actual calendar dates were different."
                ),
                caution=(
                    "This pattern cannot tell me why someone withdrew. Academic, "
                    "financial, employment, family, health, and other circumstances "
                    "may be missing from OULAD."
                ),
                alt=(
                    f"Line chart of activity around withdrawal. Median weekly clicks "
                    f"decline from {withdrawal_week_12:g} twelve weeks before "
                    f"unregistration to {withdrawal_week_1:g} one week before it."
                ),
                caption=(
                    "Typical recorded clicks as the unregistration week approached."
                ),
                reverse=True,
            ),
        ]
    )

    forecast_slides = "\n".join(
        [
            _chart_slide(
                chart_id="model-comparison",
                filename="model_overview.png",
                eyebrow="Model comparison",
                title="The models found a pattern, but not a certain answer",
                takeaway=(
                    "Gradient-boosted decision trees ranked the upcoming assessment "
                    f"cases best at {boosted['pr_auc']:.3f}, compared with a "
                    f"prevalence reference of "
                    f"{prevalence['pr_auc']:.3f}."
                ),
                explanation=(
                    "Calibrated logistic regression scored "
                    f"{calibrated['pr_auc']:.3f}. "
                    "I used it for the alert example because its probabilities, "
                    "contributing factors, and cutoff behavior were easier to explain "
                    "and check. Gradient-boosted decision trees remain the stronger "
                    "ranking comparison."
                ),
                caution=(
                    "Neither predictive method explains why an assessment was missing "
                    "or below 40. "
                    "A forecast should prompt a person to review the recent record, not "
                    "label a student or make an automatic decision."
                ),
                alt=(
                    f"Three-bar comparison of later-test precision-recall AUC, where "
                    f"higher is better. The prevalence reference is "
                    f"{prevalence['pr_auc']:.3f}, calibrated logistic regression is "
                    f"{calibrated['pr_auc']:.3f}, and gradient-boosted decision trees "
                    f"are {boosted['pr_auc']:.3f}."
                ),
                caption=(
                    "Higher is better. The complete model comparison remains available "
                    "with the project files."
                ),
                technical_note=(
                    "I used precision-recall AUC to summarize how well each model ranks "
                    "weekly snapshots followed by a missing or below-40 next assessment "
                    "above the other snapshots. A score of 1.0 would be perfect. The "
                    "event rate is the prevalence reference."
                ),
            ),
            _chart_slide(
                chart_id="calibration",
                filename="calibration.png",
                eyebrow="Probability quality",
                title="Then I checked whether the probabilities were believable",
                takeaway=(
                    "The lower predictions were fairly close to what happened, but "
                    "calibrated logistic regression overstated the rate for the "
                    "highest group."
                ),
                explanation=(
                    f"In that highest group, the average prediction was "
                    f"{highest_calibration_bin['mean_predicted_probability']:.0%} and "
                    f"the actual event rate was "
                    f"{highest_calibration_bin['observed_event_rate']:.0%}. "
                    "The simple question I was asking was: when this method says 30%, "
                    "does something close to 30% actually happen?"
                ),
                caution=(
                    "A predictive method can put records in a useful order while still giving "
                    "imperfect probabilities. I had to check both."
                ),
                alt=(
                    "Calibration plot comparing predicted probability with observed "
                    "event rate. Lower-probability groups stay near the perfect "
                    "calibration line, while the two highest groups fall below it."
                ),
                caption=(
                    "The dashed line shows what perfect agreement would look like."
                ),
                reverse=True,
                technical_note=(
                    f"I also calculated a Brier score of {calibrated['brier']:.3f}. "
                    "It measures the error in the predicted probabilities. Lower is "
                    "better, and 0 would be perfect."
                ),
            ),
            _chart_slide(
                chart_id="thresholds",
                filename="threshold_curve.png",
                eyebrow="Decision thresholds",
                title="I explored what happens when the cutoff changes",
                takeaway=(
                    "When I flagged more records, I found more eventual events, but I "
                    "also created more false alarms."
                ),
                explanation=(
                    f"With a 50% cutoff, {int(threshold_50['records_flagged']):,} of "
                    f"117,186 weekly snapshots were flagged "
                    f"({threshold_50['flag_rate']:.1%}). About 62 of every 100 alerts "
                    "were followed by a missing or below-40 next assessment, and the "
                    "alerts found about 42 of every 100 cases that actually occurred. "
                    f"A correct alert came a median of "
                    f"{threshold_50['median_true_alert_lead_days']:.0f} days before "
                    "the assessment."
                ),
                caution=(
                    "I do not think there is one correct cutoff. It depends on the "
                    "purpose, available help, the cost of mistakes, and whether a flag "
                    "could lead to anything useful."
                ),
                alt=(
                    "Line chart showing precision increasing and recall decreasing "
                    "as the percentage of weekly records flagged becomes smaller."
                ),
                caption=(
                    "The cutoff controls how many records calibrated logistic regression "
                    "would flag."
                ),
                technical_note=(
                    "Precision is the share of my flags that became events. Recall is "
                    "the share of all events I found. A false alarm is a flag without "
                    "the event; a missed case is an event below the cutoff."
                ),
            ),
            _chart_slide(
                chart_id="forecast-timing",
                filename="performance_by_week.png",
                eyebrow="Forecast timing",
                title="I also had to decide how early to make the forecast",
                takeaway=(
                    "Later weeks usually gave the predictive methods more useful information, but "
                    "a later forecast would leave less time to respond."
                ),
                explanation=(
                    "Early in a course, I had very little activity or assessment "
                    "history to work with. Waiting gave the predictive methods a "
                    "fuller record, but "
                    "it also reduced the value of an early warning."
                ),
                caution=(
                    "I only tested this pattern on the later 2014J offerings that were "
                    "not used during model development. It "
                    "could change in another year, institution, or kind of course."
                ),
                alt=(
                    "Line chart showing later-test precision-recall AUC generally "
                    "increasing after course week 2, while Brier score remains lower "
                    "in later weeks."
                ),
                caption=(
                    "An earlier answer uses less information; a later answer may come "
                    "too late to be useful."
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
    content="Full learning analytics evidence and model evaluation for Jose Chavez's OULAD project."
  >
  <meta property="og:title" content="Learning Analytics: Full Analysis | Jose Chavez">
  <meta
    property="og:description"
    content="Complete OULAD evidence, weekly definitions, and temporal model evaluation."
  >
  <meta
    property="og:url"
    content="https://website-react-fbd.vercel.app/dashboards/learning-analytics/full-analysis"
  >
  <link
    rel="canonical"
    href="https://website-react-fbd.vercel.app/dashboards/learning-analytics/full-analysis"
  >
  <title>Learning Analytics: Full Analysis | Jose Chavez</title>
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

    .project-summary {
      background: #edf5f2;
    }

    .project-summary .section-head,
    .summary-copy,
    .summary-conclusion {
      max-width: 920px;
    }

    .project-summary h2 {
      font-family: Georgia, "Times New Roman", serif;
      font-size: 3.2rem;
      font-weight: 600;
    }

    .summary-lead {
      margin: 0;
      color: var(--ink);
      font-size: 1.18rem;
      line-height: 1.65;
    }

    .summary-copy {
      margin-top: 34px;
    }

    .summary-copy p {
      margin: 0;
      color: var(--muted);
      line-height: 1.72;
    }

    .summary-copy p + p {
      margin-top: 20px;
    }

    .summary-copy strong {
      color: var(--ink);
    }

    .summary-findings {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 1px;
      margin-top: 34px;
      border: 1px solid var(--line);
      background: var(--line);
    }

    .summary-finding {
      min-width: 0;
      padding: 24px;
      background: var(--white);
    }

    .summary-finding h3 {
      margin: 0 0 18px;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 1.35rem;
      line-height: 1.25;
    }

    .summary-finding p {
      margin: 0;
      color: var(--muted);
      line-height: 1.62;
    }

    .summary-finding p + p {
      margin-top: 14px;
    }

    .summary-finding strong {
      color: var(--ink);
    }

    .summary-conclusion {
      margin-top: 34px;
      padding: 24px 0 0 24px;
      border-top: 1px solid var(--line);
      border-left: 5px solid var(--coral);
    }

    .summary-conclusion h3 {
      margin: 0 0 10px;
      font-family: inherit;
      font-size: 1.05rem;
    }

    .summary-conclusion p {
      margin: 0;
      color: var(--ink);
      font-size: 1.04rem;
      line-height: 1.7;
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

    .model-definition,
    .model-role-summary {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin: 34px 0 0;
      border-top: 1px solid var(--line);
    }

    .model-definition div,
    .model-role-summary div {
      min-width: 0;
      padding: 18px 22px 18px 0;
      border-bottom: 1px solid var(--line);
    }

    .model-definition div:nth-child(2n),
    .model-role-summary div:nth-child(2n) {
      padding-right: 0;
      padding-left: 22px;
      border-left: 1px solid var(--line);
    }

    .model-definition dt {
      color: var(--blue-dark);
      font-size: 0.74rem;
      font-weight: 850;
      text-transform: uppercase;
    }

    .model-definition dd,
    .model-role-summary p {
      margin: 7px 0 0;
      color: var(--muted);
      font-size: 0.9rem;
      line-height: 1.6;
    }

    .model-family-guide {
      margin-top: 36px;
    }

    .model-family-guide h3 {
      margin: 0;
    }

    .model-family-guide ol {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0 38px;
      margin: 18px 0 0;
      padding: 0;
      border-top: 1px solid var(--line);
      list-style: none;
    }

    .model-family-guide li {
      padding: 15px 0;
      border-bottom: 1px solid var(--line);
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.58;
    }

    .model-family-guide li strong,
    .model-family-guide li span {
      color: var(--ink);
    }

    .model-family-guide li span {
      display: block;
      margin-top: 3px;
    }

    .model-role-summary strong {
      color: var(--blue-dark);
      font-size: 0.86rem;
    }

    .model-guardrails {
      max-width: 900px;
      margin-top: 28px;
      padding-left: 20px;
      border-left: 4px solid var(--coral);
    }

    .model-guardrails p {
      margin: 0;
      color: var(--muted);
      line-height: 1.62;
    }

    .model-guardrails p + p {
      margin-top: 10px;
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

    .forecast-negative {
      max-width: 920px;
      margin-top: 42px;
      padding: 28px;
      border: 1px solid #d9b8b2;
      border-left: 5px solid var(--coral);
      background: var(--white);
    }

    .forecast-negative h3 {
      margin: 0 0 12px;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 1.7rem;
    }

    .forecast-negative p {
      margin: 0;
      color: var(--muted);
      line-height: 1.68;
    }

    .forecast-negative p + p {
      margin-top: 12px;
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

    .footer-links {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      margin-top: 14px;
    }

    .footer-links a {
      color: var(--blue-dark);
      font-weight: 750;
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

      .project-summary h2 {
        font-size: 2.35rem;
      }

      .summary-lead {
        font-size: 1.04rem;
      }

      .summary-conclusion {
        padding-left: 16px;
      }

      .why-section {
        padding-top: 38px;
        padding-bottom: 38px;
      }

      .question-list,
      .metrics,
      .finding-summary,
      .summary-findings,
      .evaluation-flow,
      .model-definition,
      .model-family-guide ol,
      .model-role-summary,
      .model-summary,
      .limits-grid,
      .skills-list,
      .terms {
        grid-template-columns: 1fr;
      }

      .model-definition div:nth-child(2n),
      .model-role-summary div:nth-child(2n) {
        padding-left: 0;
        border-left: 0;
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
  <a class="skip-link" href="#main-content">Skip to the full analysis</a>

  <nav class="project-bar" aria-label="Portfolio and project links">
    <div class="shell">
      <a class="project-name" href="/#/data-science/learning-analytics">
        Jose Chavez · Data Science Portfolio
      </a>
      <div class="project-links">
        <a href="/#/data-science/learning-analytics">Back to project overview</a>
        <a href="$repository">Code and documentation</a>
      </div>
    </div>
  </nav>

  <header class="hero">
    <div class="shell">
      <p class="eyebrow">Learning Analytics · Full analysis</p>
      <h1>Disengagement showed up before the course was over.</h1>
      <p class="hero-intro">
        I worked with real, anonymous Open University records to understand when
        students began to pull away from an online course and whether the information
        available at the time could support earlier help. Nearly one in three course
        attempts ended in withdrawal, and recorded activity had already fallen sharply
        before the course ended. The records showed when concern might be worth a closer
        look, but they could not explain why a student struggled.
      </p>
      <nav class="page-nav" aria-label="Full analysis sections">
        <ul>
          <li><a href="#key-findings">What I found</a></li>
          <li><a href="#questions">What I asked</a></li>
          <li><a href="#data">The records I used</a></li>
          <li><a href="#forecasting">My forecast test</a></li>
          <li><a href="#methods">How I built the analysis</a></li>
          <li><a href="#limits">What I cannot claim</a></li>
        </ul>
      </nav>
    </div>
  </header>

  <main id="main-content">
    <section
      class="section project-summary"
      id="key-findings"
      aria-labelledby="key-findings-title"
    >
      <div class="shell">
        <div class="section-head">
          <p class="eyebrow">What this project found</p>
          <h2 id="key-findings-title">Three findings in one minute</h2>
          <p class="summary-lead">
            OULAD contains course outcomes, assessment records, and online-platform
            activity from selected Open University courses in 2013 and 2014. I used it
            to ask where disengagement became visible, what varied from course to
            course, and whether a weekly record could help someone notice an upcoming
            assessment problem.
          </p>
        </div>

        <div class="summary-findings">
          <article class="summary-finding">
            <p class="eyebrow">Finding 1</p>
            <h3>Disengagement appeared before withdrawal.</h3>
            <p>
              <strong>$withdrawals of $attempts course attempts
              ($withdrawal_rate) ended in withdrawal.</strong> Typical weekly clicks
              fell from $week_2_median in week 2 to $week_12_median in week 12, and
              from $withdrawal_week_12 twelve weeks before withdrawal to
              $withdrawal_week_1 one week before it.
            </p>
            <p>
              <strong>Why it matters:</strong> a support team may have time to review a
              changing pattern before the course ends. Clicks show recorded activity,
              not motivation, learning, or a reason for withdrawal.
            </p>
          </article>
          <article class="summary-finding">
            <p class="eyebrow">Finding 2</p>
            <h3>Course context changed the meaning of missing work.</h3>
            <p>
              Missing submissions ranged from <strong>$missing_low in
              $missing_low_label</strong> to <strong>$missing_high in
              $missing_high_label</strong>. A single rule for every course would have
              hidden a very large difference.
            </p>
            <p>
              <strong>Why it matters:</strong> course design and recording practices
              need to be checked before interpreting a student's missing work.
            </p>
          </article>
          <article class="summary-finding">
            <p class="eyebrow">Finding 3</p>
            <h3>The next assessment could be anticipated, with limits.</h3>
            <p>
              In the later test, <strong>$test_events of $test_snapshots weekly
              snapshots ($test_prevalence)</strong> were followed by a missing or
              below-40 next assessment. At a 50% cutoff, calibrated logistic
              regression alerts were correct <strong>$threshold_precision</strong> of the
              time and found <strong>$threshold_recall</strong> of the actual cases.
            </p>
            <p>
              <strong>Why it matters:</strong> this could help prioritize a record for
              human review. It missed more than half of the cases and should never make
              an automatic decision about a student.
            </p>
          </article>
        </div>

        <div class="summary-conclusion">
          <h3>Overall conclusion</h3>
          <p>
            The records were useful for seeing change over time and deciding where a
            closer human review might be worthwhile. They were not strong enough to
            determine an individual student's outcome, and they do not show that
            clicks, missed work, or any other recorded behavior caused that outcome.
          </p>
        </div>
      </div>
    </section>

    <section class="section why-section shell" aria-labelledby="why-title">
      <div class="section-head">
        <p class="eyebrow">Why I chose this</p>
        <h2 id="why-title">
          A click can tell me what happened on a platform. It cannot tell me why.
        </h2>
        <p>
          That distinction shaped the whole project. I wanted to find useful patterns,
          but I did not want to turn platform activity into a story about motivation,
          intelligence, or effort. So at every step I asked two things: what does this
          record show me, and what would I be guessing?
        </p>
      </div>
    </section>

    <section class="section shell" id="questions" aria-labelledby="questions-title">
      <div class="section-head">
        <p class="eyebrow">Where I began</p>
        <h2 id="questions-title">I focused on the decisions behind the numbers</h2>
        <p>
          I wanted the analysis to answer questions an education team could actually
          face, while keeping a clear line between a useful pattern and an explanation
          of a student's life.
        </p>
      </div>
      <ol class="question-list">
        <li>How did online activity change as a course moved forward?</li>
        <li>Did missing work and submission timing look the same in every course?</li>
        <li>What happened to recorded activity before a withdrawal?</li>
        <li>Could the information available so far help me forecast the next assessment?</li>
        <li>When a forecast gave a probability, how much could I trust it?</li>
      </ol>
    </section>

    <section class="section section-alt shell" id="data" aria-labelledby="data-title">
      <div class="section-head">
        <p class="eyebrow">The records I worked with</p>
        <h2 id="data-title">I used a real, anonymous set of Open University records</h2>
        <p class="dataset-intro">
          It is called the Open University Learning Analytics Dataset, or OULAD. It
          brings together course information, assessment records, final outcomes, and
          activity from an online learning platform. The records cover selected Open
          University course offerings from 2013 and 2014.
        </p>
      </div>
      <dl class="metrics">
        <div>
          <dt><strong>$modules</strong><span>courses</span></dt>
          <dd><small>OULAD calls them modules</small></dd>
        </div>
        <div>
          <dt><strong>$presentations</strong><span>course offerings</span></dt>
          <dd><small>One course taught in one period</small></dd>
        </div>
        <div>
          <dt><strong>$students</strong><span>individual students</span></dt>
          <dd><small>Each person has an anonymous identifier</small></dd>
        </div>
        <div>
          <dt><strong>$attempts</strong><span>course enrollments or attempts</span></dt>
          <dd><small>One student in one course offering</small></dd>
        </div>
        <div>
          <dt><strong>$assessments</strong><span>assessments</span></dt>
          <dd><small>Coursework and exams</small></dd>
        </div>
        <div>
          <dt><strong>$activity_millions</strong><span>recorded online interactions</span></dt>
          <dd><small>$activity_exact separate records</small></dd>
        </div>
      </dl>
      <p class="source-note">
        One detail mattered right away: the same student can appear in more than one
        course attempt. A click only shows recorded platform use. It does not show me
        effort, attention, understanding, motivation, learning, or offline study.
        <a href="$source_url">See the original dataset.</a>
      </p>
    </section>

    <section class="section section-alt shell" aria-labelledby="analysis-title">
      <div class="section-head">
        <p class="eyebrow">How the story unfolded</p>
        <h2 id="analysis-title">I moved from outcomes to activity, timing, and withdrawal</h2>
        <p>
          Let me walk you through the charts in the same order I explored the data.
          For each one, I explain what caught my attention and what I would not read
          into it.
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
        <p class="eyebrow">My forecasting experiment</p>
        <h2 id="forecasting-title">
          Weekly records helped anticipate the next poor assessment result, but not
          an individual withdrawal.
        </h2>
        <p>
          At the end of a course week, I used the information available so far to
          estimate whether one student's next non-exam assessment would be missing by
          its due date or receive a score below 40. The forecast could help an instructor
          decide which recent records to review, but it was not reliable enough to
          label a student or make an automatic decision.
        </p>
      </div>

      <div class="forecast-question">
        <h3>One weekly snapshot was one student in one course attempt</h3>
        <p>
          I included a snapshot only when that student had an upcoming non-exam
          assessment with a known due date. I gave the predictive methods only the activity,
          submissions, and assessment results that could have been known by the end
          of that week. Later activity and future results stayed out of the inputs.
        </p>
      </div>

      <dl class="model-definition">
        <div>
          <dt>Exact outcome</dt>
          <dd>$model_outcome.</dd>
        </div>
        <div>
          <dt>When I made the estimate</dt>
          <dd>$model_time.</dd>
        </div>
        <div>
          <dt>One observation</dt>
          <dd>$model_observation.</dd>
        </div>
        <div>
          <dt>Information available</dt>
          <dd>$model_features.</dd>
        </div>
      </dl>

      <div class="model-family-guide">
        <h3>I compared six approaches for six different reasons</h3>
        <ol>
          $model_families
        </ol>
      </div>

      <div class="evaluation-flow" aria-label="Model evaluation sequence">
        <div>
          <span>01</span>
          <strong>I developed the models with 2013 courses</strong>
          <p>The models learned from course offerings in the earlier year.</p>
        </div>
        <div>
          <span>02</span>
          <strong>I checked my choices with 2014B</strong>
          <p>These first 2014 offerings helped me choose and adjust the models.</p>
        </div>
        <div>
          <span>03</span>
          <strong>I tested once on later 2014J courses</strong>
          <p>These later offerings stayed hidden until the final evaluation.</p>
        </div>
      </div>
      <p class="source-note">
        B and J are the source dataset's labels for earlier- and later-year
        teaching periods.
        I kept complete course offerings together during model evaluation instead
        of randomly splitting related weekly records. Otherwise, records from the
        same offering could appear in both training and testing and make the final
        score look better than it really was.
      </p>

      <div class="model-role-summary" aria-label="Distinct model roles">
        <div>
          <strong>Strongest ranking</strong>
          <p>$strongest_ranking</p>
        </div>
        <div>
          <strong>Most accurate probabilities</strong>
          <p>$best_probabilities</p>
        </div>
        <div>
          <strong>Worked cutoff example</strong>
          <p>$threshold_example</p>
        </div>
        <div>
          <strong>Reference I retained</strong>
          <p>$retained_reference</p>
        </div>
      </div>
      <div class="model-guardrails">
        <p><strong>How I chose:</strong> $selection_criterion</p>
        <p><strong>Demonstrated use:</strong> $practical_use</p>
        <p><strong>Never use it to:</strong> $prohibited_uses</p>
      </div>

      <div class="model-summary" aria-label="Calibrated logistic regression summary">
        <div>
          <strong>$calibrated_pr</strong>
          <span>How well calibrated logistic regression ranked upcoming events</span>
          <p>
            Higher is better and 1.0 would be perfect. My basic comparison score was
            $prevalence_pr. Calibrated logistic regression improved on it, but was far
            from perfect.
          </p>
        </div>
        <div>
          <strong>$calibrated_brier</strong>
          <span>How far the probabilities were from reality</span>
          <p>
            Lower is better and 0 would mean perfect probabilities. I use the
            technical name Brier score in the detailed notes below.
          </p>
        </div>
      </div>

      <div class="chart-sequence">
        $forecast_slides
      </div>

      <article class="forecast-negative" aria-labelledby="withdrawal-model-title">
        <p class="eyebrow">A separate experiment</p>
        <h3 id="withdrawal-model-title">
          The 28-day logistic regression forecast produced too many false alerts for individual use.
        </h3>
        <p>
          I separately tested whether the same kind of weekly snapshot could identify
          a recorded withdrawal within the next 28 days. In the later 2014J test
          records, withdrawal occurred after only <strong>$withdrawal_prevalence</strong>
          of the snapshots. Logistic regression flagged <strong>$withdrawal_flag_rate</strong>
          of all snapshots, but only <strong>$withdrawal_precision</strong> of its
          alerts were correct. It found <strong>$withdrawal_recall</strong> of the
          withdrawals that did occur, but the large number of false alerts made the
          result unsuitable for decisions about individuals.
        </p>
        <p>
          I report this unsuccessful result because it shows where the available
          records did not support the intended use, even though 8.0% precision was
          numerically above the 3.9% event rate.
        </p>
      </article>

      <details class="technical-note">
        <summary>See the complete model comparison</summary>
        <figure>
          <img
            src="assets/model_comparison.png"
            alt="Later-test precision-recall AUC for all assessment models."
            loading="lazy"
            decoding="async"
          >
          <figcaption>
            The overview chart shows the prevalence reference, calibrated logistic
            regression, and gradient-boosted decision trees. This chart preserves
            every comparison.
          </figcaption>
        </figure>
      </details>
    </section>

    <section class="section shell" id="methods" aria-labelledby="methods-title">
      <div class="section-head">
        <p class="eyebrow">How I built the analysis</p>
        <h2 id="methods-title">I kept a clear trail from the original files to every result</h2>
        <p class="method-intro">
          I did not want the charts to be a black box. I checked the original files
          with Python, organized them in PostgreSQL, asked my questions with SQL, and
          returned to Python for the charts and forecasting experiment.
        </p>
      </div>
      <div class="method-flow" aria-label="The path I followed through the data">
        <div>
          <span>01</span>
          <strong>I got the original records</strong>
          <p>I downloaded the historical OULAD files and checked that they arrived unchanged.</p>
        </div>
        <div>
          <span>02</span>
          <strong>I opened and checked them</strong>
          <p>I counted the rows, read the columns, and looked for missing information.</p>
        </div>
        <div>
          <span>03</span>
          <strong>I organized the tables</strong>
          <p>I used PostgreSQL to connect the course, student, activity, and assessment records.</p>
        </div>
        <div>
          <span>04</span>
          <strong>I asked questions with SQL</strong>
          <p>I checked the data and built one consistent set of weekly and course summaries.</p>
        </div>
        <div>
          <span>05</span>
          <strong>I explained the results</strong>
          <p>I used Python for the charts, the forecast, and the final tests.</p>
        </div>
      </div>
      <p class="technology-line">
        <strong>The tools I used:</strong> PostgreSQL 16, SQL, Python, pandas, and
        scikit-learn. I also practiced connecting related tables, building fair
        week-by-week comparisons, checking probability quality, and making the charts
        readable without hiding uncertainty.
      </p>
      <details>
        <summary>See the more technical details</summary>
        <p>
          I defined the important measures once in SQL so I did not quietly calculate
          them a different way for each chart. The project includes six organized
          database areas, saved analysis tables, indexes for faster queries, recorded
          query plans, and twenty-four data checks.
        </p>
      </details>
      <div class="closing-links">
        <a class="button-link" href="$repository/blob/main/docs/sql-design.md">
          See how I designed the SQL
        </a>
        <a class="button-link" href="$repository/blob/main/sql/gallery/queries.sql">
          Read the actual queries
        </a>
        <a class="button-link" href="$repository/blob/main/docs/forecast-evaluation.md">
          How I evaluated the assessment forecast
        </a>
      </div>
    </section>

    <section class="section limits shell" id="limits" aria-labelledby="limits-title">
      <div class="section-head">
        <p class="eyebrow">What I will not claim</p>
        <h2 id="limits-title">These records show patterns, not the full lives behind them</h2>
        <p>
          The biggest lesson for me was that a detailed record can still be incomplete.
          I can describe the patterns I found, but I cannot turn them into an
          explanation of any individual student.
        </p>
      </div>
      <ul class="limits-grid">
        <li>I only studied selected Open University courses from 2013 and 2014.</li>
        <li>
          I cannot see offline study, unrecorded resources, or everything happening
          in a student's life.
        </li>
        <li>
          I do not know every reason for a late assessment, missing submission, or
          withdrawal.
        </li>
        <li>A pattern in the records does not prove that one behavior caused an outcome.</li>
        <li>I would expect the results to change in another year, school, or kind of course.</li>
        <li>
          I would never treat a prediction as a statement about character,
          intelligence, motivation, ability, or potential.
        </li>
      </ul>
    </section>

    <section class="section shell" id="skills" aria-labelledby="skills-title">
      <div class="section-head">
        <p class="eyebrow">What I learned by doing it</p>
        <h2 id="skills-title">This project made me connect the whole process</h2>
        <p>
          Forecasting was only one part of the work. The real challenge was staying with
          the same question from the messy original files through the database,
          analysis, testing, and explanation.
        </p>
      </div>
      <ul class="skills-list">
        <li>I turned seven linked source files into tables I could question and check.</li>
        <li>
          I wrote a repeatable PostgreSQL and SQL workflow instead of relying on
          manual steps.
        </li>
        <li>I built the forecast one week at a time without letting future information slip in.</li>
        <li>I tested the forecast's ranking, probabilities, cutoffs, and timing separately.</li>
        <li>
          I learned to explain a useful result without pretending it was more
          certain than it was.
        </li>
      </ul>
    </section>

    <section class="section section-alt shell" id="glossary" aria-labelledby="glossary-title">
      <div class="section-head">
        <p class="eyebrow">A little help with the terminology</p>
        <h2 id="glossary-title">Here are the few technical terms I still use</h2>
      </div>
      <details class="glossary">
        <summary>Open my plain-language glossary</summary>
        <dl class="terms">
          <dt>OULAD</dt>
          <dd>The anonymous historical Open University records I used for this project.</dd>
          <dt>Course or module</dt>
          <dd>OULAD says module where I would normally say course.</dd>
          <dt>Course offering</dt>
          <dd>One course taught during one period. OULAD calls this a presentation.</dd>
          <dt>Course attempt</dt>
          <dd>One student taking one course offering. A student can have multiple attempts.</dd>
          <dt>Online activity or click</dt>
          <dd>
            An action recorded by the learning platform. I do not treat it as proof of
            attention or learning.
          </dd>
          <dt>Weekly snapshot</dt>
          <dd>The information I could have known at the end of one course week.</dd>
          <dt>Forecast target</dt>
          <dd>
            What I asked the predictive methods to estimate: a missing or below-40
            next assessment.
          </dd>
          <dt>Later test data</dt>
          <dd>Later course offerings I did not use until the final forecast test.</dd>
          <dt>Precision</dt>
          <dd>Of everything I flagged, the share that later became an event.</dd>
          <dt>Recall</dt>
          <dd>Of all the events, the share my chosen cutoff managed to find.</dd>
          <dt>Precision-recall AUC</dt>
          <dd>
            One number summarizing how well a predictive method put upcoming events above
            other records.
          </dd>
          <dt>Brier score</dt>
          <dd>A measure of error in the predicted probabilities. Lower is better.</dd>
          <dt>Calibration</dt>
          <dd>My check of whether predicted probabilities matched what actually happened.</dd>
          <dt>Threshold</dt>
          <dd>The probability cutoff I used to decide which records to flag.</dd>
          <dt>False alarm</dt>
          <dd>A record I flagged even though the event did not happen.</dd>
          <dt>Missed case</dt>
          <dd>An event that happened even though its probability stayed below my cutoff.</dd>
        </dl>
      </details>
    </section>
  </main>

  <footer>
    <div class="shell">
      <p>
        This page uses the same PostgreSQL tables and saved Python results as the
        analysis. You can inspect the SQL, Python, tests, and reproduction instructions
        in the <a href="$repository">code and documentation</a>.
      </p>
      <nav class="footer-links" aria-label="Contact Jose Chavez">
        <a href="https://www.linkedin.com/in/jose-chavez-79841a1b4/">LinkedIn</a>
        <a href="https://github.com/FollowingJCABIC">GitHub</a>
        <a href="mailto:jose.gj.chavez@gmail.com">Email</a>
      </nav>
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
        week_0_median=f"{week_0_median:g}",
        week_2_median=f"{week_2_median:g}",
        week_12_median=f"{week_12_median:g}",
        missing_low=f"{lowest_missing['missing_rate']:.1%}",
        missing_low_n=f"{int(lowest_missing['eligible_student_assessments']):,}",
        missing_low_label=(
            f"{lowest_missing['code_module']} "
            f"{lowest_missing['code_presentation']}"
        ),
        missing_high=f"{highest_missing['missing_rate']:.1%}",
        missing_high_n=f"{int(highest_missing['eligible_student_assessments']):,}",
        missing_high_label=(
            f"{highest_missing['code_module']} "
            f"{highest_missing['code_presentation']}"
        ),
        withdrawal_week_12=f"{withdrawal_week_12:g}",
        withdrawal_week_1=f"{withdrawal_week_1:g}",
        calibrated_pr=f"{calibrated['pr_auc']:.3f}",
        prevalence_pr=f"{prevalence['pr_auc']:.3f}",
        calibrated_brier=f"{calibrated['brier']:.3f}",
        test_snapshots=f"{test_snapshots:,}",
        test_events=f"{test_events:,}",
        test_prevalence=f"{float(prevalence['prevalence']):.1%}",
        records_flagged=f"{records_flagged:,}",
        true_alerts=f"{true_alerts:,}",
        threshold_precision=f"{float(threshold_50['precision']):.1%}",
        threshold_recall=f"{float(threshold_50['recall']):.1%}",
        median_lead_days=f"{int(threshold_50['median_true_alert_lead_days']):,}",
        withdrawal_prevalence=f"{float(withdrawal_test['prevalence']):.1%}",
        withdrawal_flag_rate=f"{float(withdrawal_test['flag_rate']):.1%}",
        withdrawal_precision=f"{float(withdrawal_test['precision']):.1%}",
        withdrawal_recall=f"{float(withdrawal_test['recall']):.1%}",
        model_outcome=html.escape(model_explanation["outcome"]),
        model_time=html.escape(model_explanation["predictionTime"]),
        model_observation=html.escape(model_explanation["observation"]),
        model_features=html.escape(model_explanation["featureTypes"]),
        model_families=model_families,
        strongest_ranking=html.escape(model_explanation["strongestRanking"]),
        best_probabilities=html.escape(model_explanation["bestProbabilities"]),
        threshold_example=html.escape(model_explanation["thresholdExample"]),
        retained_reference=html.escape(model_explanation["retainedReference"]),
        selection_criterion=html.escape(model_explanation["selectionCriterion"]),
        practical_use=html.escape(model_explanation["practicalUse"]),
        prohibited_uses=html.escape(model_explanation["prohibitedUses"]),
        analysis_slides=analysis_slides,
        forecast_slides=forecast_slides,
    )

    (output_dir / "index.html").write_text(page, encoding="utf-8")
