"""
Block 3 verification script.

Runs the full inference -> explanation -> recommendation path on the demo
project and asserts the invariants that Block 4 will depend on.

Run from the project root:  python test_block3.py
"""

import json
from pathlib import Path

from src.predictor import (
    load_artifacts, predict_project, prepare_features, risk_category,
)
from src.explain import explain_project, plain_language_explanation
from src.recommendations import generate_recommendations

DEMO_PATH = Path(__file__).resolve().parent / "data" / "demo_project.json"


def section(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main():
    with open(DEMO_PATH) as f:
        project = json.load(f)

    # --- 1. Artifacts -------------------------------------------------------
    section("1. ARTIFACTS")
    artifacts = load_artifacts()
    meta = artifacts["metadata"]
    print("Features (from metadata):", meta["features"])
    print("Risk bands:", meta["risk_bands"])
    print("Training records:", meta.get("n_training_records"))
    print("Stored test metrics:", meta.get("test_metrics"))
    print("Typical delay (median days, delayed only):", artifacts["typical_delay_days"])

    # --- 2. Feature ordering ------------------------------------------------
    section("2. FEATURE ORDERING")
    row = prepare_features(project)
    assert list(row.columns) == meta["features"], "Feature order does not match metadata"
    print("Column order matches metadata exactly.")
    print(row.T)

    # --- 3. Prediction ------------------------------------------------------
    section("3. PREDICTION — NH-47-024")
    result = predict_project(project)
    print("Delay probability :", result["delay_probability"])
    print("Risk score        :", result["risk_score"])
    print("Risk category     :", result["risk_category"])
    print("Expected delay    :", result["expected_delay_days"], "days")
    print("Critical stage    :", result["critical_stage"])

    assert 0.0 <= result["delay_probability"] <= 1.0
    assert result["risk_category"] in ("LOW", "MEDIUM", "HIGH")
    assert result["risk_category"] == risk_category(result["delay_probability"])

    # --- 4. Stage-wise risk -------------------------------------------------
    section("4. STAGE-WISE RISK (rule layer, not a trained model)")
    for stage, score in result["stage_risk"].items():
        marker = "  <-- CRITICAL" if stage == result["critical_stage"] else ""
        print(f"  {stage:<15} {score:>6.1f}{marker}")

    assert len(result["stage_risk"]) == 5
    assert all(0 <= v <= 100 for v in result["stage_risk"].values())
    assert result["critical_stage"] == max(result["stage_risk"], key=result["stage_risk"].get)

    # --- 5. SHAP ------------------------------------------------------------
    section("5. SHAP EXPLANATION")
    exp = explain_project(project)
    print(f"Base value (log-odds)   : {exp['base_value']}")
    print(f"Model probability       : {exp['model_probability']}")
    print(f"Reconstructed from SHAP : {exp['reconstructed_probability']}")
    print(f"Reconciliation error    : {exp['reconciliation_error']}")

    print("\nTop contributors:")
    for c in exp["contributions"][:6]:
        print(f"  {c['label']:<28} value={str(c['value']):<8} shap={c['shap']:+.4f}  ({c['direction']})")

    assert exp["reconciliation_error"] < 1e-5, "SHAP does not reconcile with predict_proba"
    assert len(exp["contributions"]) == len(meta["features"]), "Contributions not aggregated correctly"
    print("\nSHAP reconciles with the model prediction.")

    print("\nPlain language:")
    print(" ", plain_language_explanation(project))

    # --- 6. Recommendations -------------------------------------------------
    section("6. RECOMMENDATIONS")
    recs = generate_recommendations(project, top_contributors=exp["contributions"][:5])
    for r in recs:
        flag = " [model-confirmed]" if r["model_confirmed"] else ""
        print(f"\n  [{r['priority']}]{flag} {r['risk_factor']}")
        print(f"    current value : {r['current_value']}")
        print(f"    action        : {r['action']}")
        print(f"    stakeholder   : {r['stakeholder']}")

    assert len(recs) > 0, "No recommendations generated for a MEDIUM/HIGH-risk project"
    priorities = [r["priority"] for r in recs]
    assert priorities == sorted(priorities, key=lambda p: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}[p])
    print(f"\n  Total recommendations: {len(recs)}")

    # --- 7. Determinism -----------------------------------------------------
    section("7. DETERMINISM")
    second = predict_project(project)
    assert second["delay_probability"] == result["delay_probability"]
    assert second["stage_risk"] == result["stage_risk"]
    assert generate_recommendations(project, exp["contributions"][:5]) == recs
    print("Repeated calls produced identical output.")

    section("BLOCK 3 VERIFICATION PASSED")


if __name__ == "__main__":
    main()