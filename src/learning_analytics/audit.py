from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from learning_analytics.config import Settings
from learning_analytics.download import EXPECTED_FILES, sha256

CSV_FILES = sorted(EXPECTED_FILES - {"OULAD.names"})


def _csv_profile(path: Path) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = 0
        missing = Counter()
        for row in reader:
            rows += 1
            missing.update({column: 1 for column, value in row.items() if value in {"", "?"}})
    return {
        "file": path.name,
        "rows": rows,
        "columns": len(reader.fieldnames or []),
        "column_names": reader.fieldnames or [],
        "missing_cells": dict(missing),
        "sha256": sha256(path),
    }


def build_source_audit(settings: Settings) -> dict[str, Any]:
    missing_files = [name for name in CSV_FILES if not (settings.source_dir / name).exists()]
    if missing_files:
        raise FileNotFoundError(f"Run `make data`; missing {missing_files}")

    profiles = [_csv_profile(settings.source_dir / name) for name in CSV_FILES]
    student_info = pd.read_csv(settings.source_dir / "studentInfo.csv", na_values="?")
    courses = pd.read_csv(settings.source_dir / "courses.csv", na_values="?")
    assessments = pd.read_csv(settings.source_dir / "assessments.csv", na_values="?")
    registrations = pd.read_csv(settings.source_dir / "studentRegistration.csv", na_values="?")

    attempt_key = ["code_module", "code_presentation", "id_student"]
    audit = {
        "source": "UCI Machine Learning Repository, dataset 349",
        "download_url": (
            "https://archive.ics.uci.edu/dataset/349/open+university+learning+analytics+dataset"
        ),
        "files": profiles,
        "calculated_scale": {
            "csv_rows": int(sum(profile["rows"] for profile in profiles)),
            "unique_students": int(student_info["id_student"].nunique()),
            "student_module_attempts": int(student_info[attempt_key].drop_duplicates().shape[0]),
            "modules": int(courses["code_module"].nunique()),
            "module_presentations": int(
                courses[["code_module", "code_presentation"]].drop_duplicates().shape[0]
            ),
            "assessments": int(assessments["id_assessment"].nunique()),
            "activity_records": next(
                profile["rows"] for profile in profiles if profile["file"] == "studentVle.csv"
            ),
        },
        "observed_anomalies": {
            "student_attempt_duplicates": int(student_info.duplicated(attempt_key).sum()),
            "registration_attempt_duplicates": int(registrations.duplicated(attempt_key).sum()),
            "missing_imd_band": int(student_info["imd_band"].isna().sum()),
            "missing_assessment_due_dates": int(assessments["date"].isna().sum()),
            "missing_unregistration_dates": int(registrations["date_unregistration"].isna().sum()),
        },
    }
    settings.ensure_output_directories()
    output = settings.reports_dir / "source-audit.json"
    output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(profiles).drop(columns=["column_names", "missing_cells"]).to_csv(
        settings.reports_dir / "tables" / "source_file_profile.csv", index=False
    )
    return audit
