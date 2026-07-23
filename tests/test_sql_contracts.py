from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_snapshot_sql_enforces_point_in_time_activity() -> None:
    sql = (ROOT / "sql" / "06_features.sql").read_text(encoding="utf-8")
    assert "ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW" in sql
    assert "current_week.course_week = weeks.course_week" in sql
    assert "progress.submitted_day <= engagement.snapshot_day" in sql
    assert "latest_feature_day > snapshot_day" in sql


def test_model_target_is_next_later_assessment() -> None:
    sql = (ROOT / "sql" / "06_features.sql").read_text(encoding="utf-8")
    assert "progress.due_day > history.snapshot_day" in sql
    assert "ORDER BY progress.due_day, progress.id_assessment" in sql
    assert "LIMIT 1" in sql


def test_gallery_has_fifteen_numbered_queries() -> None:
    sql = (ROOT / "sql" / "gallery" / "queries.sql").read_text(encoding="utf-8")
    assert sum(f"-- {number:02d}." in sql for number in range(1, 16)) == 15
