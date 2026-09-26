"""
TerraTech — report generation.

CSV export for tables. PDF export is optional/future scope.
"""

import csv
import io
from src.database import get_all_projects, get_all_issues, get_officer_workload
from src.analytics import get_projects_with_risk


def export_projects_csv() -> str:
    """Export all projects with risk info as CSV string."""
    projects = get_projects_with_risk()
    if not projects:
        return ""

    output = io.StringIO()
    fields = [
        "project_id", "project_name", "project_type", "state", "district",
        "current_stage", "progress_pct", "project_status", "priority",
        "risk_score", "risk_category", "expected_delay_days",
        "land_area", "affected_families", "legal_disputes",
        "documentation_completion", "compensation_completion",
        "rr_completion", "possession_completion",
        "start_date", "planned_completion_date",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for p in projects:
        writer.writerow(p)
    return output.getvalue()


def export_issues_csv() -> str:
    """Export all issues as CSV string."""
    issues = get_all_issues()
    if not issues:
        return ""

    output = io.StringIO()
    fields = [
        "id", "project_id", "landowner_id", "issue_type", "status",
        "severity", "title", "description", "created_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for issue in issues:
        writer.writerow(issue)
    return output.getvalue()


def export_officer_workload_csv() -> str:
    """Export officer workload report as CSV string."""
    workload = get_officer_workload()
    if not workload:
        return ""

    output = io.StringIO()
    fields = [
        "name", "designation", "department",
        "project_count", "assignment_count", "active_count",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in workload:
        writer.writerow(row)
    return output.getvalue()
