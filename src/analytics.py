"""
TerraTech — analytics aggregation.

Pre-computed statistics for the government dashboard and analytics pages.
All functions read from the database; none modify data.
"""

from src.database import (
    get_all_projects, get_project_stats, get_projects_by_state,
    get_projects_by_type, get_projects_by_status, get_stage_distribution,
    get_officer_workload, get_issue_stats, get_all_alerts,
)
from src.utils import extended_risk_category, extract_ml_dict

# Cache for risk scores to avoid recomputing on every page load
_risk_cache: dict[str, dict] = {}


def compute_risk_for_project(project: dict) -> dict:
    """
    Run the ML model on a project and return risk info.

    Results are cached in-memory for the process lifetime.
    """
    pid = project["project_id"]
    if pid in _risk_cache:
        return _risk_cache[pid]

    try:
        from src.predictor import predict_project
        ml_dict = extract_ml_dict(project)
        result = predict_project(ml_dict, include_contributors=False)
        risk_info = {
            "delay_probability": result["delay_probability"],
            "risk_score": result["risk_score"],
            "risk_category": extended_risk_category(result["delay_probability"]),
            "expected_delay_days": result["expected_delay_days"],
            "stage_risk": result["stage_risk"],
            "critical_stage": result["critical_stage"],
        }
    except Exception:
        # Fallback for projects that can't be scored
        risk_info = {
            "delay_probability": 0.5,
            "risk_score": 50.0,
            "risk_category": "MEDIUM",
            "expected_delay_days": 28,
            "stage_risk": {},
            "critical_stage": "Unknown",
        }
    _risk_cache[pid] = risk_info
    return risk_info


def clear_risk_cache(project_id: str = None):
    """Clear cached risk scores (e.g. after project update)."""
    if project_id:
        _risk_cache.pop(project_id, None)
    else:
        _risk_cache.clear()


def get_dashboard_stats() -> dict:
    """Aggregate KPIs for the government dashboard."""
    projects = get_all_projects()
    stats = get_project_stats()
    issue_stats = get_issue_stats()

    risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    total_progress = 0
    total_delay = 0
    n_scored = 0

    for p in projects:
        risk = compute_risk_for_project(p)
        cat = risk["risk_category"]
        risk_counts[cat] = risk_counts.get(cat, 0) + 1
        total_progress += p.get("progress_pct", 0)
        total_delay += risk.get("expected_delay_days", 0)
        n_scored += 1

    avg_progress = round(total_progress / max(len(projects), 1), 1)
    avg_delay = round(total_delay / max(n_scored, 1), 0)

    # Alerts
    alerts = get_all_alerts(limit=500)
    unread_alerts = sum(1 for a in alerts if not a.get("is_read"))

    return {
        **stats,
        "risk_counts": risk_counts,
        "high_risk": risk_counts["HIGH"] + risk_counts["CRITICAL"],
        "critical_risk": risk_counts["CRITICAL"],
        "avg_progress": avg_progress,
        "avg_delay": int(avg_delay),
        "pending_legal": issue_stats["by_type"].get("Legal", 0),
        "pending_compensation": issue_stats["by_type"].get("Compensation", 0),
        "pending_documentation": issue_stats["by_type"].get("Documentation", 0),
        "total_issues": issue_stats["total"],
        "open_issues": issue_stats["open"],
        "unread_alerts": unread_alerts,
    }


def get_risk_distribution() -> dict:
    """Count projects by risk category."""
    projects = get_all_projects()
    dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for p in projects:
        risk = compute_risk_for_project(p)
        dist[risk["risk_category"]] += 1
    return dist


def get_delay_distribution() -> list[dict]:
    """Group projects by expected delay buckets."""
    projects = get_all_projects()
    buckets = {"0-15 days": 0, "16-30 days": 0, "31-60 days": 0,
               "61-90 days": 0, "90+ days": 0}
    for p in projects:
        risk = compute_risk_for_project(p)
        days = risk.get("expected_delay_days", 0)
        if days <= 15:
            buckets["0-15 days"] += 1
        elif days <= 30:
            buckets["16-30 days"] += 1
        elif days <= 60:
            buckets["31-60 days"] += 1
        elif days <= 90:
            buckets["61-90 days"] += 1
        else:
            buckets["90+ days"] += 1
    return [{"bucket": k, "count": v} for k, v in buckets.items()]


def get_projects_with_risk() -> list[dict]:
    """Return all projects augmented with risk info."""
    projects = get_all_projects()
    result = []
    for p in projects:
        risk = compute_risk_for_project(p)
        result.append({**p, **risk})
    return result


def get_high_risk_projects(limit: int = 10) -> list[dict]:
    """Top N projects by risk score, descending."""
    all_p = get_projects_with_risk()
    all_p.sort(key=lambda x: x.get("risk_score", 0), reverse=True)
    return all_p[:limit]


def get_stage_bottleneck_analysis() -> list[dict]:
    """Identify which stages have the most delayed projects."""
    from src.database import get_stage_distribution
    return get_stage_distribution()


def get_district_comparison() -> list[dict]:
    """Compare districts by project count and average progress."""
    projects = get_all_projects()
    district_data = {}
    for p in projects:
        d = p["district"]
        if d not in district_data:
            district_data[d] = {"district": d, "state": p["state"],
                                "count": 0, "total_progress": 0, "total_risk": 0}
        district_data[d]["count"] += 1
        district_data[d]["total_progress"] += p.get("progress_pct", 0)
        risk = compute_risk_for_project(p)
        district_data[d]["total_risk"] += risk.get("risk_score", 0)

    result = []
    for d in district_data.values():
        d["avg_progress"] = round(d["total_progress"] / max(d["count"], 1), 1)
        d["avg_risk"] = round(d["total_risk"] / max(d["count"], 1), 1)
        result.append(d)
    result.sort(key=lambda x: x["count"], reverse=True)
    return result
