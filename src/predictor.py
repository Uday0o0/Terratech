"""
TerraTech — inference layer.

Loads the Block 2 artifacts and produces a complete risk assessment for one
land-acquisition project. No training happens here.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths — src/ sits inside the project root, so step up one level
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"

MODEL_PATH = MODEL_DIR / "classifier.joblib"
PREPROCESSOR_PATH = MODEL_DIR / "preprocessing.joblib"
METADATA_PATH = MODEL_DIR / "feature_metadata.joblib"
HISTORICAL_CSV = DATA_DIR / "historical_projects.csv"

# Module-level cache: artifacts are loaded from disk exactly once per process
_ARTIFACTS = None

# Fallback used only if the historical CSV is unavailable
_DEFAULT_TYPICAL_DELAY_DAYS = 180.0


# ---------------------------------------------------------------------------
# Artifact loading
# ---------------------------------------------------------------------------
def _typical_delay_days():
    """
    Median slippage among historically delayed projects.

    This is a descriptive statistic read from the synthetic dataset, NOT a
    trained regression. It is used only to scale the expected-delay estimate.
    """
    try:
        df = pd.read_csv(HISTORICAL_CSV, usecols=["delayed", "actual_delay_days"])
        delayed_only = df.loc[df["delayed"] == 1, "actual_delay_days"]
        if len(delayed_only) == 0:
            return _DEFAULT_TYPICAL_DELAY_DAYS
        return float(delayed_only.median())
    except Exception:
        return _DEFAULT_TYPICAL_DELAY_DAYS


def load_artifacts():
    """Load model, preprocessor and metadata once, then reuse the cached copy."""
    global _ARTIFACTS
    if _ARTIFACTS is None:
        for path in (MODEL_PATH, PREPROCESSOR_PATH, METADATA_PATH):
            if not path.exists():
                raise FileNotFoundError(
                    f"Missing artifact: {path}. Run the Block 2 notebook first."
                )

        _ARTIFACTS = {
            "model": joblib.load(MODEL_PATH),
            "preprocessor": joblib.load(PREPROCESSOR_PATH),
            "metadata": joblib.load(METADATA_PATH),
            "typical_delay_days": _typical_delay_days(),
        }
    return _ARTIFACTS


# ---------------------------------------------------------------------------
# Feature preparation
# ---------------------------------------------------------------------------
def prepare_features(project: dict) -> pd.DataFrame:
    """
    Build a one-row DataFrame using FEATURES from metadata, in the saved order.

    The order is taken from the artifact, never hand-written here.
    """
    artifacts = load_artifacts()
    features = artifacts["metadata"]["features"]

    missing = [f for f in features if f not in project]
    if missing:
        raise KeyError(f"Project is missing required features: {missing}")

    return pd.DataFrame([{f: project[f] for f in features}], columns=features)


def transform_features(project: dict) -> np.ndarray:
    """Apply the fitted preprocessor. transform() only — never fit_transform()."""
    artifacts = load_artifacts()
    return artifacts["preprocessor"].transform(prepare_features(project))


# ---------------------------------------------------------------------------
# Risk banding
# ---------------------------------------------------------------------------
def risk_category(probability: float) -> str:
    """Apply the LOW/MEDIUM/HIGH bands stored in feature_metadata.joblib."""
    bands = load_artifacts()["metadata"]["risk_bands"]
    for name in ("LOW", "MEDIUM", "HIGH"):
        low, high = bands[name]
        if name == "HIGH":
            if probability >= low:
                return "HIGH"
        elif low <= probability < high:
            return name
    return "HIGH"


# ---------------------------------------------------------------------------
# Stage-wise risk — TRANSPARENT RULE LAYER, NOT A TRAINED MODEL
# ---------------------------------------------------------------------------
STAGES = ["Notification", "Documentation", "Compensation", "R&R", "Possession"]


def _gap(pct: float) -> float:
    """Incompleteness of a stage: 100% complete -> 0 risk contribution."""
    return float(np.clip(100.0 - pct, 0.0, 100.0))


def _scale(value: float, lo: float, hi: float) -> float:
    """Map a raw count/duration onto a 0-100 scale, clipped at both ends."""
    return float(np.clip((value - lo) / (hi - lo), 0.0, 1.0) * 100.0)


def stage_wise_risk(project: dict) -> dict:
    """
    Score each acquisition stage 0-100 from the raw project features.

    These weights are an explicit, inspectable rule layer. They are NOT learned
    and NOT derived from the XGBoost model. Documented as such throughout.
    """
    disputes = _scale(project["legal_disputes"], 0, 12)
    families = _scale(project["affected_families"], 0, 1200)

    scores = {
        "Notification": (
            0.55 * _scale(project["approval_delay_days"], 0, 90)
            + 0.45 * _scale(project["stakeholder_response_days"], 0, 25)
        ),
        "Documentation": (
            0.70 * _gap(project["documentation_completion"])
            + 0.30 * disputes
        ),
        "Compensation": (
            0.60 * _gap(project["compensation_completion"])
            + 0.25 * disputes
            + 0.15 * families
        ),
        "R&R": (
            0.70 * _gap(project["rr_completion"])
            + 0.30 * families
        ),
        "Possession": (
            0.60 * _gap(project["possession_completion"])
            + 0.25 * _gap(project["rr_completion"])
            + 0.15 * disputes
        ),
    }
    return {stage: round(float(np.clip(score, 0, 100)), 1) for stage, score in scores.items()}


def critical_stage(stage_scores: dict) -> str:
    """The stage carrying the highest rule-based risk score."""
    return max(stage_scores, key=stage_scores.get)


# ---------------------------------------------------------------------------
# Expected delay
# ---------------------------------------------------------------------------
def expected_delay_days(probability: float) -> int:
    """
    First-order expectation: P(delayed) x typical historical slippage.

    This is a transparent heuristic, not a trained duration model. A calibrated
    survival or regression model is future scope.
    """
    typical = load_artifacts()["typical_delay_days"]
    return int(round(probability * typical))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def predict_project(project: dict, include_contributors: bool = True) -> dict:
    """
    Full risk assessment for one project.

    Returns delay probability, risk score, risk category, expected delay,
    stage-wise risk, critical stage and (optionally) SHAP top contributors.
    """
    artifacts = load_artifacts()
    model = artifacts["model"]

    X = transform_features(project)
    probability = float(model.predict_proba(X)[0, 1])

    stages = stage_wise_risk(project)

    result = {
        "project_id": project.get("project_id", "UNKNOWN"),
        "delay_probability": round(probability, 4),
        "risk_score": round(probability * 100, 1),
        "risk_category": risk_category(probability),
        "expected_delay_days": expected_delay_days(probability),
        "stage_risk": stages,
        "critical_stage": critical_stage(stages),
        "model_version": {
            "n_training_records": artifacts["metadata"].get("n_training_records"),
            "test_metrics": artifacts["metadata"].get("test_metrics"),
        },
        "data_note": "Synthetic prototype data. Not a real government record.",
    }

    if include_contributors:
        from src.explain import top_contributors  # imported here to avoid a cycle
        result["top_contributors"] = top_contributors(project, n=5)

    return result