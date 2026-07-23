from learning_analytics.config import Settings
from learning_analytics.dashboard import FIGURE_FILES, build_dashboard


def test_dashboard_builds_the_plain_language_presentation() -> None:
    settings = Settings()
    build_dashboard(settings)

    page = (settings.project_root / "dashboard" / "index.html").read_text(
        encoding="utf-8"
    )
    text = " ".join(page.split())

    assert "Understanding Student Engagement, Assessments, and Course Outcomes" in text
    assert "Online-course data is easy to count and easy to misread" in text
    assert "What this project asks" in text
    assert "The main findings in one minute" in text
    assert "What exactly is being forecast?" in text
    assert "Later activity and future assessment results are excluded." in text
    assert "What this analysis cannot tell us" in text
    assert "What this project demonstrates" in text
    assert "Open the compact glossary" in text
    assert "does not monitor current students" in text
    assert "$analysis_slides" not in page
    assert "$forecast_slides" not in page

    for filename in FIGURE_FILES:
        assert f'assets/{filename}"' in page
