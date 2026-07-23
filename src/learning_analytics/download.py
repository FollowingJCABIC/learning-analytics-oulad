from __future__ import annotations

import hashlib
import logging
import shutil
import urllib.request
import zipfile
from pathlib import Path

from learning_analytics.config import Settings

LOGGER = logging.getLogger(__name__)
SOURCE_URL = (
    "https://archive.ics.uci.edu/static/public/349/"
    "open%2Buniversity%2Blearning%2Banalytics%2Bdataset.zip"
)
EXPECTED_SHA256 = "f2ed1902616c1fe8d2824d872c0b7d2d72be435bf0124d077044fe4be2c6d3e4"
EXPECTED_FILES = {
    "assessments.csv",
    "courses.csv",
    "studentAssessment.csv",
    "studentInfo.csv",
    "studentRegistration.csv",
    "studentVle.csv",
    "vle.csv",
    "OULAD.names",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_dataset(settings: Settings, force: bool = False) -> Path:
    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    archive_path = settings.raw_dir / "oulad.zip"
    if force or not archive_path.exists():
        LOGGER.info("Downloading OULAD from UCI")
        with urllib.request.urlopen(SOURCE_URL, timeout=120) as response:
            with archive_path.open("wb") as target:
                shutil.copyfileobj(response, target)

    actual_checksum = sha256(archive_path)
    if actual_checksum != EXPECTED_SHA256:
        raise ValueError(
            f"Checksum mismatch for {archive_path}: {actual_checksum} != {EXPECTED_SHA256}"
        )

    settings.source_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        missing = EXPECTED_FILES - names
        if missing:
            raise ValueError(f"Official archive is missing expected files: {sorted(missing)}")
        archive.extractall(settings.source_dir)
    return settings.source_dir
