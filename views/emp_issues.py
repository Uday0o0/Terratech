"""Employee Portal — Issues for assigned projects."""

import streamlit as st
from src.database import get_projects_for_officer, get_issues_for_project
from src.utils import format_date


def render():
    from src.ui import html, section, PRIORITY_HEX, MARIGOLD

    user = st.session_state.get("user", {})
    user_id = user.get("id")

    section("Project Issues", "Legal, compensation, and documentation issues")

    projects = get_projects_for_officer(user_id)

    if not projects:
        html('<div class="tt-empty">No projects assigned — no issues to show.</div>')
        return

    # Collect all issues
    all_issues = []
    unique_projects = []
    for p in projects:
        unique_projects.append(p["project_name"])
        issues = get_issues_for_project(p["project_id"])
        for issue in issues:
            issue["project_name"] = p["project_name"]
        all_issues.extend(issues)

    unique_projects.sort()
    selected_project = st.selectbox("Filter by Project", ["All Projects"] + unique_projects)
    
    if selected_project != "All Projects":
        all_issues = [i for i in all_issues if i.get("project_name") == selected_project]

    if all_issues:
        html(f'<div style="font-size:12px;color:var(--ink-soft);margin-bottom:12px">'
             f'{len(all_issues)} issue(s) across your projects</div>')

        for issue in all_issues:
            sev_color = PRIORITY_HEX.get(issue.get("severity", "MEDIUM"), MARIGOLD)
            html(
                f'<div class="tt-rec">'
                f'<div class="num" style="color:{sev_color}">●</div>'
                f'<div>'
                f'<div class="rf">{issue["title"]}</div>'
                f'<div class="act">{issue.get("description", "")}</div>'
                f'<div class="meta">Type: {issue["issue_type"]} · '
                f'Status: {issue.get("status", "Open")} · '
                f'Severity: {issue.get("severity", "MEDIUM")} · '
                f'Project: {issue.get("project_name", issue["project_id"])}'
                f'{" · Landowner: " + issue["landowner_id"] if issue.get("landowner_id") else ""}</div>'
                f'</div></div>'
            )
    else:
        html('<div class="tt-empty">No issues found for your projects.</div>')
