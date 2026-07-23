from learning_analytics.config import PROJECT_ROOT, get_settings


def test_project_root_is_repository_root() -> None:
    settings = get_settings()
    assert settings.project_root == PROJECT_ROOT
    assert (settings.project_root / "pyproject.toml").exists()
