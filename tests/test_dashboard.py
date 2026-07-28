from learning_analytics.config import Settings
from learning_analytics.dashboard import FIGURE_FILES, build_dashboard


def test_dashboard_builds_the_plain_language_presentation() -> None:
    settings = Settings()
    build_dashboard(settings)

    page = (settings.project_root / "dashboard" / "index.html").read_text(
        encoding="utf-8"
    )
    text = " ".join(page.split())

    assert "Disengagement showed up before the course was over." in text
    assert "A click can tell me what happened on a platform." in text
    assert "I focused on the decisions behind the numbers" in text
    assert "What this project found" in text
    assert "Three findings in one minute" in text
    assert "10,156 of 32,593 course attempts" in text
    assert "24,724 of 117,186 weekly snapshots (21.1%)" in text
    assert "One weekly snapshot was one student in one course attempt" in text
    assert "Later activity and future results stayed out of the inputs." in text
    assert (
        "I kept complete course offerings together during model evaluation "
        "instead of randomly splitting related weekly records."
    ) in text
    assert "The withdrawal model produced too many false alerts" in text
    assert "within the next 28 days" in text
    assert "only <strong>8.0%</strong> of its alerts were correct" in text
    assert "These records show patterns, not the full lives behind them" in text
    assert "This project made me connect the whole process" in text
    assert "Open my plain-language glossary" in text
    assert "should never make an automatic decision about a student" in text
    assert "How I evaluated the assessment forecast" in text
    assert "How I built the analysis" in text
    assert "$analysis_slides" not in page
    assert "$forecast_slides" not in page

    for filename in FIGURE_FILES:
        assert f'assets/{filename}"' in page
