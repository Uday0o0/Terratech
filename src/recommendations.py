"""
TerraTech — recommendation layer.

Deterministic rules over the project's actual values. Priority is escalated when
SHAP confirms the feature is among the model's real risk drivers.
No LLM, no randomness: the same project always yields the same output.
"""

PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

# Each rule: (feature, test, base priority, risk factor, action, stakeholder)
RULES = [
    (
        "compensation_completion",
        lambda p: p["compensation_completion"] < 50,
        "CRITICAL",
        "Compensation disbursal significantly behind",
        "Convene a compensation review; audit pending awards and bank-account "
        "verification for unpaid beneficiaries.",
        "Competent Authority / Land Acquisition Officer",
    ),
    (
        "compensation_completion",
        lambda p: 50 <= p["compensation_completion"] < 75,
        "HIGH",
        "Compensation disbursal incomplete",
        "Identify beneficiaries with unresolved title or account issues and "
        "clear them in a dedicated camp.",
        "Land Acquisition Officer",
    ),
    (
        "legal_disputes",
        lambda p: p["legal_disputes"] >= 8,
        "CRITICAL",
        "High volume of unresolved legal disputes",
        "Prioritise case-wise legal review; pursue Lok Adalat or negotiated "
        "settlement for objections that can be resolved out of court.",
        "District Legal Cell / Government Pleader",
    ),
    (
        "legal_disputes",
        lambda p: 4 <= p["legal_disputes"] < 8,
        "HIGH",
        "Active legal disputes pending",
        "Track each pending objection with a named officer and a target "
        "resolution date.",
        "District Legal Cell",
    ),
    (
        "rr_completion",
        lambda p: p["rr_completion"] < 50,
        "CRITICAL",
        "Rehabilitation and resettlement substantially pending",
        "Review pending R&R entitlements; confirm resettlement site readiness "
        "before seeking possession.",
        "R&R Administrator",
    ),
    (
        "rr_completion",
        lambda p: 50 <= p["rr_completion"] < 75,
        "HIGH",
        "R&R obligations incomplete",
        "Publish the pending-entitlement list and schedule disbursal against "
        "fixed dates.",
        "R&R Administrator",
    ),
    (
        "possession_completion",
        lambda p: p["possession_completion"] < 50,
        "HIGH",
        "Physical possession lagging",
        "Sequence possession handover for encumbrance-free parcels first; "
        "do not wait for full-stretch clearance.",
        "Revenue Officer / Executing Agency",
    ),
    (
        "documentation_completion",
        lambda p: p["documentation_completion"] < 70,
        "HIGH",
        "Land records and documentation incomplete",
        "Complete mutation, survey verification and title reconciliation for "
        "outstanding parcels.",
        "Tehsildar / Revenue Records Office",
    ),
    (
        "documentation_completion",
        lambda p: 70 <= p["documentation_completion"] < 85,
        "MEDIUM",
        "Documentation partially pending",
        "Close remaining record discrepancies before the next award milestone.",
        "Revenue Records Office",
    ),
    (
        "approval_delay_days",
        lambda p: p["approval_delay_days"] >= 30,
        "HIGH",
        "Statutory approvals delayed",
        "Escalate pending approvals to the district review committee with a "
        "file-wise ageing report.",
        "District Collector's Office",
    ),
    (
        "approval_delay_days",
        lambda p: 14 <= p["approval_delay_days"] < 30,
        "MEDIUM",
        "Approval turnaround slower than target",
        "Review file movement and fix accountability for stages exceeding the "
        "prescribed timeline.",
        "Project Nodal Officer",
    ),
    (
        "stakeholder_response_days",
        lambda p: p["stakeholder_response_days"] >= 10,
        "MEDIUM",
        "Slow stakeholder response cycle",
        "Establish a single-window grievance desk with a published response "
        "commitment.",
        "Project Nodal Officer",
    ),
    (
        "historical_delay_rate",
        lambda p: p["historical_delay_rate"] >= 35,
        "MEDIUM",
        "District has an elevated historical delay rate",
        "Apply enhanced monitoring cadence; review recurring causes from prior "
        "acquisitions in this district.",
        "District Collector's Office",
    ),
]


def _escalate(priority: str) -> str:
    """Raise a priority one level. CRITICAL is already the ceiling."""
    ladder = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    idx = ladder.index(priority)
    return ladder[min(idx + 1, len(ladder) - 1)]


def generate_recommendations(project: dict, top_contributors=None) -> list:
    """
    Apply every rule whose condition holds for this project.

    If top_contributors is supplied, any rule whose feature appears there with a
    positive (risk-increasing) SHAP value is escalated one priority level. This
    is how the deterministic rules and the model's actual attributions are
    reconciled without the model ever generating text.
    """
    driver_features = set()
    if top_contributors:
        driver_features = {
            c["feature"] for c in top_contributors if c.get("shap", 0) > 0
        }

    recommendations = []
    for feature, condition, priority, risk_factor, action, stakeholder in RULES:
        if not condition(project):
            continue

        final_priority = priority
        model_confirmed = feature in driver_features
        if model_confirmed:
            final_priority = _escalate(priority)

        recommendations.append({
            "priority": final_priority,
            "feature": feature,
            "current_value": project.get(feature),
            "risk_factor": risk_factor,
            "action": action,
            "stakeholder": stakeholder,
            "model_confirmed": model_confirmed,
        })

    recommendations.sort(key=lambda r: (PRIORITY_ORDER[r["priority"]], r["feature"]))
    return recommendations