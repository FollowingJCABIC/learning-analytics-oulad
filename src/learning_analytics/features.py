from __future__ import annotations

import numpy as np
import pandas as pd


def snapshot_day(course_week: pd.Series) -> pd.Series:
    if (course_week < 0).any():
        raise ValueError("Model snapshots cannot use negative course weeks")
    return course_week.astype(int) * 7 + 6


def days_since_last_activity(snapshot: int, activity_days: list[int]) -> float:
    eligible = [day for day in activity_days if day <= snapshot]
    return float(snapshot - max(eligible)) if eligible else np.nan


def assert_no_future_features(frame: pd.DataFrame) -> None:
    required = {"snapshot_day", "latest_feature_day"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Leakage audit requires columns: {sorted(missing)}")
    leaking = frame["latest_feature_day"].notna() & (
        frame["latest_feature_day"] > frame["snapshot_day"]
    )
    if leaking.any():
        raise ValueError(f"Found {int(leaking.sum())} snapshots containing future information")


def temporal_split(frame: pd.DataFrame) -> pd.Series:
    presentation_year = frame["code_presentation"].str[:4].astype(int)
    presentation_term = frame["code_presentation"].str[-1]
    return pd.Series(
        np.select(
            [
                presentation_year <= 2013,
                (presentation_year == 2014) & (presentation_term == "B"),
            ],
            ["train", "validation"],
            default="test",
        ),
        index=frame.index,
        name="split",
    )
