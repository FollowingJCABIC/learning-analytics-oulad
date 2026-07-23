from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from learning_analytics.config import Settings
from learning_analytics.features import temporal_split

IDENTIFIERS = [
    "code_module",
    "code_presentation",
    "id_student",
    "course_week",
    "snapshot_day",
    "next_assessment_id",
    "next_assessment_due_day",
]
CATEGORICAL_FEATURES = ["code_module", "presentation_term"]
NUMERIC_FEATURES = [
    "clicks_7d",
    "clicks_prior_7d",
    "clicks_14d",
    "clicks_to_date",
    "active_days_14d",
    "distinct_sites_14d",
    "days_since_activity",
    "engagement_change",
    "submissions_to_date",
    "mean_score_to_date",
    "missing_due_to_date",
    "weighted_score_to_date",
]


@dataclass(frozen=True)
class Evaluation:
    model: str
    split: str
    n: int
    prevalence: float
    precision: float
    recall: float
    f1: float
    accuracy: float
    roc_auc: float
    pr_auc: float
    brier: float
    flag_rate: float


def _preprocessor() -> ColumnTransformer:
    numeric = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        [
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ]
    )


def _evaluate(name: str, split: str, y: pd.Series, probability: np.ndarray) -> Evaluation:
    prediction = (probability >= 0.5).astype(int)
    return Evaluation(
        model=name,
        split=split,
        n=len(y),
        prevalence=float(y.mean()),
        precision=float(precision_score(y, prediction, zero_division=0)),
        recall=float(recall_score(y, prediction, zero_division=0)),
        f1=float(f1_score(y, prediction, zero_division=0)),
        accuracy=float(accuracy_score(y, prediction)),
        roc_auc=float(roc_auc_score(y, probability)),
        pr_auc=float(average_precision_score(y, probability)),
        brier=float(brier_score_loss(y, probability)),
        flag_rate=float(prediction.mean()),
    )


def load_model_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["presentation_term"] = frame["code_presentation"].str[-1]
    frame["split"] = temporal_split(frame)
    required = set(
        NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
        + ["target_next_assessment_event", "target_withdrawal_28d"]
    )
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Model snapshot export is missing: {sorted(missing)}")
    return frame


def train_models(settings: Settings) -> pd.DataFrame:
    source_path = settings.processed_dir / "model_snapshots.csv"
    frame = load_model_frame(source_path)
    train = frame[frame["split"] == "train"].copy()
    validation = frame[frame["split"] == "validation"].copy()
    test = frame[frame["split"] == "test"].copy()
    if min(len(train), len(validation), len(test)) == 0:
        raise ValueError("Temporal split produced an empty partition")

    x_train = train[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_train = train["target_next_assessment_event"].astype(int)
    x_validation = validation[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_validation = validation["target_next_assessment_event"].astype(int)
    x_test = test[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_test = test["target_next_assessment_event"].astype(int)

    models: dict[str, Any] = {
        "logistic_regression": LogisticRegression(
            C=0.5, max_iter=1000, class_weight="balanced", random_state=settings.random_seed
        ),
        "decision_tree": DecisionTreeClassifier(
            max_depth=5,
            min_samples_leaf=100,
            class_weight="balanced",
            random_state=settings.random_seed,
        ),
        "gradient_boosted_tree": HistGradientBoostingClassifier(
            max_depth=6,
            learning_rate=0.08,
            max_iter=150,
            l2_regularization=1.0,
            random_state=settings.random_seed,
        ),
    }

    results: list[Evaluation] = []
    fitted: dict[str, Pipeline] = {}
    test_probabilities: dict[str, np.ndarray] = {}
    prevalence = float(y_train.mean())
    for split_name, y in [("validation", y_validation), ("test", y_test)]:
        baseline_probability = np.full(len(y), prevalence, dtype=float)
        results.append(
            _evaluate(
                "prevalence_baseline",
                split_name,
                y,
                baseline_probability,
            )
        )
        if split_name == "test":
            test_probabilities["prevalence_baseline"] = baseline_probability

    rule_threshold = float(train["days_since_activity"].dropna().quantile(0.75))
    for split_name, split_frame, y in [
        ("validation", validation, y_validation),
        ("test", test, y_test),
    ]:
        rule_probability = (
            (split_frame["days_since_activity"].fillna(rule_threshold + 1) > rule_threshold)
            | (split_frame["missing_due_to_date"] > 0)
            | (split_frame["engagement_change"] < 0)
        ).astype(float)
        results.append(_evaluate("sql_rule_baseline", split_name, y, rule_probability.to_numpy()))
        if split_name == "test":
            test_probabilities["sql_rule_baseline"] = rule_probability.to_numpy()

    for name, estimator in models.items():
        pipeline = Pipeline([("prepare", _preprocessor()), ("model", estimator)])
        pipeline.fit(x_train, y_train)
        fitted[name] = pipeline
        for split_name, x, y in [
            ("validation", x_validation, y_validation),
            ("test", x_test, y_test),
        ]:
            probability = pipeline.predict_proba(x)[:, 1]
            results.append(_evaluate(name, split_name, y, probability))
            if split_name == "test":
                test_probabilities[name] = probability

    calibrated = CalibratedClassifierCV(
        fitted["logistic_regression"], method="sigmoid", cv="prefit"
    )
    calibrated.fit(x_validation, y_validation)
    fitted["calibrated_logistic_regression"] = calibrated
    calibrated_probability = calibrated.predict_proba(x_test)[:, 1]
    test_probabilities["calibrated_logistic_regression"] = calibrated_probability
    results.append(
        _evaluate(
            "calibrated_logistic_regression",
            "test",
            y_test,
            calibrated_probability,
        )
    )

    settings.ensure_output_directories()
    result_frame = pd.DataFrame(asdict(item) for item in results)
    result_frame.to_csv(settings.reports_dir / "tables" / "model_metrics.csv", index=False)

    prediction_columns = [
        "code_module",
        "code_presentation",
        "id_student",
        "course_week",
        "snapshot_day",
        "gender",
        "age_band",
        "disability",
        "imd_band",
        "next_assessment_due_day",
        "target_next_assessment_event",
    ]
    predictions = test[prediction_columns].copy()
    predictions["probability"] = calibrated_probability
    predictions["prediction"] = (calibrated_probability >= 0.5).astype(int)
    predictions["prediction_horizon_days"] = (
        predictions["next_assessment_due_day"] - predictions["snapshot_day"]
    )
    predictions.to_csv(settings.reports_dir / "tables" / "test_predictions.csv", index=False)

    confusion_rows: list[dict[str, int | str]] = []
    actual = y_test.to_numpy()
    for name, probability in test_probabilities.items():
        tn, fp, fn, tp = confusion_matrix(actual, probability >= 0.5).ravel()
        confusion_rows.append(
            {
                "model": name,
                "true_negative": int(tn),
                "false_positive": int(fp),
                "false_negative": int(fn),
                "true_positive": int(tp),
            }
        )
    pd.DataFrame(confusion_rows).to_csv(
        settings.reports_dir / "tables" / "confusion_matrices.csv", index=False
    )

    grouped_metrics: list[dict[str, Any]] = []
    for dimension in ["course_week", "code_module", "code_presentation", "gender", "age_band"]:
        for group, indices in predictions.groupby(dimension, dropna=False).groups.items():
            subset = predictions.loc[indices]
            if len(subset) < 100 or subset["target_next_assessment_event"].nunique() < 2:
                continue
            evaluation = _evaluate(
                "calibrated_logistic_regression",
                "test",
                subset["target_next_assessment_event"],
                subset["probability"].to_numpy(),
            )
            grouped_metrics.append(
                {"dimension": dimension, "group": str(group), **asdict(evaluation)}
            )
    pd.DataFrame(grouped_metrics).to_csv(
        settings.reports_dir / "tables" / "grouped_model_metrics.csv", index=False
    )

    calibration_source = predictions.copy()
    calibration_source["probability_bin"] = pd.qcut(
        calibration_source["probability"], q=10, duplicates="drop"
    )
    calibration = (
        calibration_source.groupby("probability_bin", observed=True)
        .agg(
            mean_predicted_probability=("probability", "mean"),
            observed_event_rate=("target_next_assessment_event", "mean"),
            records=("target_next_assessment_event", "size"),
        )
        .reset_index(drop=True)
    )
    calibration.to_csv(settings.reports_dir / "tables" / "calibration_bins.csv", index=False)

    thresholds: list[dict[str, float | int]] = []
    actual = predictions["target_next_assessment_event"].to_numpy()
    for threshold in np.linspace(0.1, 0.9, 17):
        predicted = (calibrated_probability >= threshold).astype(int)
        true_alerts = int(((predicted == 1) & (actual == 1)).sum())
        false_alerts = int(((predicted == 1) & (actual == 0)).sum())
        thresholds.append(
            {
                "threshold": float(threshold),
                "records_flagged": int(predicted.sum()),
                "flag_rate": float(predicted.mean()),
                "precision": float(precision_score(actual, predicted, zero_division=0)),
                "recall": float(recall_score(actual, predicted, zero_division=0)),
                "true_alerts": true_alerts,
                "false_alerts": false_alerts,
                "false_alerts_per_true_alert": (
                    float(false_alerts / true_alerts) if true_alerts else np.nan
                ),
                "median_true_alert_lead_days": (
                    float(
                        predictions.loc[
                            (predicted == 1) & (actual == 1),
                            "prediction_horizon_days",
                        ].median()
                    )
                    if true_alerts
                    else np.nan
                ),
            }
        )
    pd.DataFrame(thresholds).to_csv(
        settings.reports_dir / "tables" / "threshold_analysis.csv", index=False
    )

    logistic_pipeline = fitted["logistic_regression"]
    feature_names = logistic_pipeline.named_steps["prepare"].get_feature_names_out()
    coefficients = logistic_pipeline.named_steps["model"].coef_[0]
    pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": coefficients,
            "odds_ratio": np.exp(coefficients),
        }
    ).sort_values("coefficient").to_csv(
        settings.reports_dir / "tables" / "logistic_coefficients.csv", index=False
    )

    importance_sample = test.sample(
        n=min(5000, len(test)),
        random_state=settings.random_seed,
    )
    importance = permutation_importance(
        fitted["gradient_boosted_tree"],
        importance_sample[NUMERIC_FEATURES + CATEGORICAL_FEATURES],
        importance_sample["target_next_assessment_event"],
        scoring="average_precision",
        n_repeats=3,
        random_state=settings.random_seed,
        n_jobs=-1,
    )
    pd.DataFrame(
        {
            "feature": NUMERIC_FEATURES + CATEGORICAL_FEATURES,
            "importance_mean": importance.importances_mean,
            "importance_std": importance.importances_std,
        }
    ).sort_values("importance_mean", ascending=False).to_csv(
        settings.reports_dir / "tables" / "permutation_importance.csv", index=False
    )

    withdrawal_model = Pipeline(
        [
            ("prepare", _preprocessor()),
            (
                "model",
                LogisticRegression(
                    C=0.5,
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=settings.random_seed,
                ),
            ),
        ]
    )
    withdrawal_train = train["target_withdrawal_28d"].astype(int)
    withdrawal_validation = validation["target_withdrawal_28d"].astype(int)
    withdrawal_test = test["target_withdrawal_28d"].astype(int)
    withdrawal_model.fit(x_train, withdrawal_train)
    withdrawal_results = [
        _evaluate(
            "withdrawal_prevalence_baseline",
            split_name,
            target,
            np.full(len(target), float(withdrawal_train.mean())),
        )
        for split_name, target in [
            ("validation", withdrawal_validation),
            ("test", withdrawal_test),
        ]
    ]
    for split_name, features, target in [
        ("validation", x_validation, withdrawal_validation),
        ("test", x_test, withdrawal_test),
    ]:
        withdrawal_results.append(
            _evaluate(
                "withdrawal_logistic_regression",
                split_name,
                target,
                withdrawal_model.predict_proba(features)[:, 1],
            )
        )
    pd.DataFrame(asdict(item) for item in withdrawal_results).to_csv(
        settings.reports_dir / "tables" / "withdrawal_model_metrics.csv", index=False
    )
    fitted["withdrawal_logistic_regression"] = withdrawal_model

    joblib.dump(fitted, settings.reports_dir / "model_pipelines.joblib")
    metadata = {
        "target": "next assessment is missing by its due day or receives a score below 40",
        "train": sorted(train["code_presentation"].unique().tolist()),
        "validation": sorted(validation["code_presentation"].unique().tolist()),
        "test": sorted(test["code_presentation"].unique().tolist()),
        "rule_inactivity_threshold_days": rule_threshold,
        "random_seed": settings.random_seed,
    }
    (settings.reports_dir / "model-run.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return result_frame
