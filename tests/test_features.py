import pandas as pd
import pytest

from learning_analytics.features import (
    assert_no_future_features,
    days_since_last_activity,
    snapshot_day,
    temporal_split,
)


def test_snapshot_day_rejects_negative_weeks() -> None:
    with pytest.raises(ValueError):
        snapshot_day(pd.Series([0, -1]))


def test_snapshot_day_is_end_of_week() -> None:
    assert snapshot_day(pd.Series([0, 1, 4])).tolist() == [6, 13, 34]


def test_days_since_activity_respects_cutoff() -> None:
    assert days_since_last_activity(28, [-3, 4, 18, 35]) == 10


def test_leakage_check_rejects_future_information() -> None:
    frame = pd.DataFrame({"snapshot_day": [14], "latest_feature_day": [15]})
    with pytest.raises(ValueError, match="future information"):
        assert_no_future_features(frame)


def test_temporal_split_uses_complete_presentations() -> None:
    frame = pd.DataFrame({"code_presentation": ["2013B", "2013J", "2014B", "2014J"]})
    assert temporal_split(frame).tolist() == ["train", "train", "validation", "test"]
