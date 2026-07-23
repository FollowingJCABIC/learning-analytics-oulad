from __future__ import annotations

import html
import json
import shutil

import pandas as pd

from learning_analytics.config import Settings

FIGURES = [
    (
        "outcome_distribution.png",
        "Recorded outcomes",
        "Counts are student-module attempts, not unique people.",
        "Bar chart of Distinction, Pass, Fail, and Withdrawn attempt counts.",
    ),
    (
        "weekly_engagement.png",
        "Weekly engagement",
        "The median and upper quartile describe active records only; "
        "clicks do not measure motivation.",
        "Line chart of median and 75th percentile weekly VLE clicks.",
    ),
    (
        "engagement_consistency.png",
        "Consistency and volume",
        "Log-scaled volume and active-week count expose different aspects "
        "of recorded platform use.",
        "Scatter plot of mean weekly clicks and number of active weeks by final result.",
    ),
    (
        "assessment_missingness.png",
        "Assessment completeness",
        "Differences may reflect course design and recording practices "
        "as well as student behavior.",
        "Horizontal bars compare missing submission rates across module-presentations.",
    ),
    (
        "submission_timing.png",
        "Submission timing",
        "Negative values indicate that the median recorded submission was before the due day.",
        "Horizontal bars compare median submission timing by module-presentation.",
    ),
    (
        "withdrawal_alignment.png",
        "Withdrawal timing",
        "Alignment is descriptive and cannot identify why an attempt ended.",
        "Line chart of median activity in weeks around recorded unregistration.",
    ),
    (
        "model_comparison.png",
        "Held-out model comparison",
        "Complete 2014J presentations form the test set; correlated weekly "
        "rows are not randomly mixed.",
        "Horizontal bars compare held-out precision-recall AUC by model.",
    ),
    (
        "calibration.png",
        "Probability calibration",
        "Calibration checks whether similar predicted probabilities have "
        "similar observed event rates.",
        "Predicted probability plotted against observed next-assessment event rate.",
    ),
    (
        "threshold_curve.png",
        "Threshold tradeoffs",
        "Changing the threshold changes both the number of records flagged and the error balance.",
        "Precision and recall plotted against percentage of records flagged.",
    ),
    (
        "performance_by_week.png",
        "Forecast timing",
        "Forecast performance changes as a longer course history becomes available.",
        "Line chart of held-out precision-recall AUC and Brier score by course week.",
    ),
]


def build_dashboard(settings: Settings) -> None:
    output_dir = settings.project_root / "dashboard"
    asset_dir = output_dir / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    available = []
    for filename, title, caption, alt in FIGURES:
        source = settings.reports_dir / "figures" / filename
        if source.exists():
            shutil.copy2(source, asset_dir / filename)
            available.append((filename, title, caption, alt))

    audit = json.loads((settings.reports_dir / "source-audit.json").read_text(encoding="utf-8"))
    scale = audit["calculated_scale"]
    metrics_path = settings.reports_dir / "tables" / "model_metrics.csv"
    model_note = "Model outputs are not available in this build."
    if metrics_path.exists():
        metrics = pd.read_csv(metrics_path)
        calibrated = metrics[
            (metrics["model"] == "calibrated_logistic_regression") & (metrics["split"] == "test")
        ].iloc[0]
        model_note = (
            f"Held-out calibrated logistic PR AUC {calibrated['pr_auc']:.3f}; "
            f"Brier score {calibrated['brier']:.3f}."
        )

    figures = "\n".join(
        f"""<figure>
          <img src="assets/{html.escape(filename)}" alt="{html.escape(alt)}">
          <figcaption><strong>{html.escape(title)}</strong>{html.escape(caption)}</figcaption>
        </figure>"""
        for filename, title, caption, alt in available
    )
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OULAD Learning Analytics Dashboard</title>
  <style>
    :root {{ color-scheme: light; --ink:#172126; --muted:#58666d; --line:#ccd5d8;
      --paper:#f7f9f8; --white:#fff; --blue:#176b87; --coral:#d95d39; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Inter, ui-sans-serif, system-ui, sans-serif;
      color:var(--ink); background:var(--paper); line-height:1.55; }}
    header, main, footer {{ width:min(1180px, calc(100% - 40px)); margin:auto; }}
    header {{ padding:64px 0 38px; border-bottom:1px solid var(--line); }}
    h1 {{ max-width:900px; font-size:4rem; line-height:1; margin:8px 0 20px; }}
    h2 {{ font-size:1.6rem; margin:0 0 14px; }}
    p {{ max-width:800px; color:var(--muted); }}
    .eyebrow {{ color:var(--blue); text-transform:uppercase; font-weight:700; font-size:.76rem; }}
    .metrics {{ display:grid; grid-template-columns:repeat(6,1fr); gap:1px;
      margin:32px 0; border:1px solid var(--line); background:var(--line); }}
    .metrics div {{ background:var(--white); padding:18px; }}
    .metrics strong {{ display:block; font-size:1.5rem; }}
    .metrics span {{ color:var(--muted); font-size:.82rem; }}
    section {{ padding:42px 0; border-bottom:1px solid var(--line); }}
    .grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:28px; }}
    figure {{ margin:0; background:var(--white); border:1px solid var(--line); }}
    img {{ display:block; width:100%; height:auto; }}
    figcaption {{ padding:14px 16px 18px; color:var(--muted); font-size:.9rem; }}
    figcaption strong {{ display:block; color:var(--ink); margin-bottom:4px; }}
    code {{ background:#e8edef; padding:2px 5px; }}
    a {{ color:var(--blue); }}
    footer {{ padding:28px 0 60px; color:var(--muted); }}
    @media (max-width:800px) {{
      h1 {{ font-size:2.5rem; }}
      .metrics {{ grid-template-columns:repeat(2,1fr); }}
      .grid {{ grid-template-columns:1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">Learning Analytics / OULAD</div>
    <h1>Engagement, assessment, and outcome forecasting</h1>
    <p>A focused view of anonymized historical patterns and model behavior. This is
    not an operational student-monitoring interface and contains no action list.</p>
    <div class="metrics">
      <div><strong>{scale["modules"]}</strong><span>modules</span></div>
      <div><strong>{scale["module_presentations"]}</strong><span>presentations</span></div>
      <div><strong>{scale["unique_students"]:,}</strong><span>unique students</span></div>
      <div><strong>{scale["student_module_attempts"]:,}</strong><span>student attempts</span></div>
      <div><strong>{scale["assessments"]:,}</strong><span>assessments</span></div>
      <div><strong>{scale["activity_records"]:,}</strong><span>activity records</span></div>
    </div>
  </header>
  <main>
    <section>
      <div class="eyebrow">Architecture</div>
      <h2>SQL defines the analytical contract</h2>
      <p>Official OULAD files -> Python source audit -> PostgreSQL raw, staging, and
      core layers -> SQL marts and weekly snapshots -> Python statistics,
      visualization, and modeling.</p>
    </section>
    <section>
      <div class="eyebrow">Executed analysis</div>
      <h2>Patterns in the downloaded archive</h2>
      <div class="grid">{figures}</div>
    </section>
    <section>
      <div class="eyebrow">Forecast evaluation</div>
      <h2>Next-assessment event, evaluated by presentation</h2>
      <p>{html.escape(model_note)} The target is a missing next assessment by its due
      day or a recorded score below 40. Features use only data available through
      each weekly snapshot.</p>
    </section>
    <section>
      <div class="eyebrow">Limits</div>
      <h2>Clicks are traces, not explanations</h2>
      <p>OULAD describes selected anonymized Open University modules from 2013-2014.
      Clicks do not directly measure effort, motivation, attention, or learning.
      Withdrawal may reflect circumstances absent from the data. Findings are
      associations and may not generalize to another institution or period.</p>
    </section>
  </main>
  <footer>Generated from versioned SQL marts and saved Python outputs.</footer>
</body>
</html>
"""
    (output_dir / "index.html").write_text(page, encoding="utf-8")
