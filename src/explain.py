"""
TerraTech — explainability layer.

Exact TreeSHAP attributions for a single project. Nothing here is hardcoded;
every value is computed from the trained XGBoost model.
"""

import numpy as np
import shap

from src.predictor import load_artifacts, transform_features

# Cached explainer: building it walks the tree ensemble, so do it once
_EXPLAINER = None

# Human-readable labels for the dashboard
FEATURE_LABELS = {
    "project_type": "Project type",
    "land_area": "Land area (ha)",
    "affected_families": "Affected families",
    "documentation_completion": "Documentation completion",
    "compensation_completion": "Compensation completion",
    "legal_disputes": "Legal disputes",
    "approval_delay_days": "Approval delay (days)",
    "rr_completion": "R&R completion",
    "possession_completion": "Possession completion",
    "stakeholder_response_days": "Stakeholder response (days)",
    "historical_delay_rate": "Historical delay rate",
}


def get_explainer():
    """Build the TreeExplainer once and reuse it."""
    global _EXPLAINER
    if _EXPLAINER is None:
        _EXPLAINER = shap.TreeExplainer(load_artifacts()["model"])
    return _EXPLAINER


def _base_feature(encoded_name: str) -> str:
    """Map an encoded column back to its original feature name."""
    if encoded_name.startswith("project_type_"):
        return "project_type"
    return encoded_name


def explain_project(project: dict) -> dict:
    """
    Compute exact SHAP values for one project.

    SHAP values are on the LOG-ODDS scale, matching Block 2. The one-hot
    project_type columns are summed back into a single contribution.
    """
    artifacts = load_artifacts()
    encoded_names = artifacts["metadata"]["encoded_feature_names"]

    X = transform_features(project)
    explainer = get_explainer()

    shap_values = np.asarray(explainer.shap_values(X))[0]
    base_value = float(np.ravel(explainer.expected_value)[0])

    # Aggregate encoded columns back to original features
    aggregated = {}
    for name, value in zip(encoded_names, shap_values):
        base = _base_feature(name)
        aggregated[base] = aggregated.get(base, 0.0) + float(value)

    contributions = [
        {
            "feature": feat,
            "label": FEATURE_LABELS.get(feat, feat),
            "value": project.get(feat),
            "shap": round(shap_val, 4),
            "direction": "increases risk" if shap_val > 0 else "reduces risk",
        }
        for feat, shap_val in aggregated.items()
    ]
    contributions.sort(key=lambda c: abs(c["shap"]), reverse=True)

    # Faithfulness check: base + sum(shap) -> logistic must equal predict_proba
    total_logodds = base_value + float(shap_values.sum())
    reconstructed = 1.0 / (1.0 + np.exp(-total_logodds))
    model_proba = float(artifacts["model"].predict_proba(X)[0, 1])

    return {
        "base_value": round(base_value, 4),
        "contributions": contributions,
        "reconstructed_probability": round(float(reconstructed), 6),
        "model_probability": round(model_proba, 6),
        "reconciliation_error": round(abs(float(reconstructed) - model_proba), 9),
    }


def top_contributors(project: dict, n: int = 5) -> list:
    """The n features with the largest absolute SHAP magnitude."""
    return explain_project(project)["contributions"][:n]


def plain_language_explanation(project: dict, n_up: int = 3, n_down: int = 2) -> str:
    """Generate a readable summary from the ACTUAL top contributors."""
    result = explain_project(project)
    contributions = result["contributions"]

    raising = [c for c in contributions if c["shap"] > 0][:n_up]
    lowering = [c for c in contributions if c["shap"] < 0][:n_down]

    lines = []
    if raising:
        parts = [f"{c['label']} ({c['value']})" for c in raising]
        lines.append("Risk is driven primarily by " + ", ".join(parts) + ".")
    if lowering:
        parts = [f"{c['label']} ({c['value']})" for c in lowering]
        lines.append("Risk is partially offset by " + ", ".join(parts) + ".")

    return " ".join(lines) if lines else "No dominant risk drivers identified."