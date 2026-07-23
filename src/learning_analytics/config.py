from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    raw_dir: Path = PROJECT_ROOT / "data" / "raw"
    source_dir: Path = PROJECT_ROOT / "data" / "raw" / "source"
    processed_dir: Path = PROJECT_ROOT / "data" / "processed"
    reports_dir: Path = PROJECT_ROOT / "reports"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://learning_analytics:learning_analytics@localhost:5432/learning_analytics",
    )
    random_seed: int = 20260723

    def ensure_output_directories(self) -> None:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        (self.reports_dir / "figures").mkdir(parents=True, exist_ok=True)
        (self.reports_dir / "tables").mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    return Settings()
