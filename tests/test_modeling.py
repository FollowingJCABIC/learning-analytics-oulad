from pathlib import Path

import pandas as pd
import pytest

from learning_analytics.config import get_settings
from learning_analytics.modeling import _evaluate, load_model_frame


def test_model_contract_requires_snapshot_features(tmp_path: Path) -> None:
    source = tmp_path / "snapshots.csv"
    pd.DataFrame(
        {
            "code_module": ["AAA"],
            "code_presentation": ["2013J"],
            "target_next_assessment_event": [0],
        }
    ).to_csv(source, index=False)
    with pytest.raises(ValueError, match="missing"):
        load_model_frame(source)


def test_evaluation_reports_probability_and_threshold_metrics() -> None:
    actual = pd.Series([0, 0, 1, 1])
    evaluation = _evaluate(
        "test_model",
        "test",
        actual,
        pd.Series([0.1, 0.4, 0.6, 0.9]).to_numpy(),
    )
    assert evaluation.precision == 1.0
    assert evaluation.recall == 1.0
    assert evaluation.brier < 0.1


def test_random_seed_is_fixed() -> None:
    assert get_settings().random_seed == 20260723
