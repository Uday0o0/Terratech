"""Employee Portal — Dashboard."""

import streamlit as st
from src.database import get_assignments_for_officer, get_projects_for_officer, get_alerts_for_user
from src.analytics import compute_risk_for_project
from src.utils import format_date


def render():
    from src.ui import html, section, BAND_HEX, BAND_TEXT_HEX, RUST, MARIGOLD, GREEN, TEAL, render_progress_bar

    user = st.session_state.get("user", {})
    user_id = user.get("id")

    section("My Dashboard", f'Overview of your assignments, {user.get("name", "")}')

    # --- My assignments ---
    assignments = get_assignments_for_officer(user_id)
    projects = get_projects_for_officer(user_id)

    # KPIs
    active = [a for a in assignments if a.get("status") == "Active"]
    alerts = get_alerts_for_user(user_id, "employee", limit=20)
    unread = sum(1 for a in alerts if not a.get("is_read"))

    html(
        '<div class="tt-kpis">'
        f'<div class="tt-kpi"><div class="num" style="color:{TEAL}">{len(projects)}</div>'
        '<div class="lbl">Assigned Projects</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{MARIGOLD}">{len(active)}</div>'
        '<div class="lbl">Active Assignments</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{RUST}">{unread}</div>'
        '<div class="lbl">Unread Alerts</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{GREEN}">{len(assignments) - len(active)}</div>'
        '<div class="lbl">Completed</div></div>'
        '</div>'
    )

    st.write("")

    # --- My projects table ---
    section("My Projects", "Projects assigned to you")

    if projects:
        rows = ""
        for p in projects:
            risk = compute_risk_for_project(p)
            cat = risk["risk_category"]
            color = BAND_HEX.get(cat, RUST)
            badge = (f'<span class="tt-badge" style="color:{BAND_TEXT_HEX.get(cat, RUST)}">'
                     f'<i style="background:{color}"></i>{cat.title()}</span>')
            rows += (
                f'<tr>'
                f'<td><b>{p["project_name"]}</b><br>'
                f'<span style="font-size:11px;color:var(--ink-faint)">{p["project_id"]}</span></td>'
                f'<td>{p.get("current_stage", "—")}</td>'
                f'<td>{render_progress_bar(p.get("progress_pct", 0))} '
                f'<span style="font-size:11px">{p.get("progress_pct", 0):.0f}%</span></td>'
                f'<td>{badge}</td>'
                f'<td>{p.get("priority", "—")}</td>'
                f'<td>{format_date(p.get("planned_completion_date"))}</td>'
                f'</tr>'
            )
        html(
            '<table class="tt-table"><thead><tr>'
            '<th>Project</th><th>Stage</th><th>Progress</th>'
            '<th>Risk</th><th>Priority</th><th>Deadline</th>'
            '</tr></thead><tbody>' + rows + '</tbody></table>'
        )
        
        st.write("")
        c1, c2 = st.columns([1, 2])
        with c1:
            jump = st.selectbox(
                "Quick Navigate to Project Details", 
                options=["-- Select a Project to View --"] + [p["project_name"] for p in projects],
                key="emp_dash_jump"
            )
            if jump != "-- Select a Project to View --":
                selected_id = next(p["project_id"] for p in projects if p["project_name"] == jump)
                st.session_state.go_to_page = "My Projects"
                st.session_state.emp_selected_project_id = selected_id
                st.rerun()
    else:
        html('<div class="tt-empty">No projects assigned to you yet.</div>')

    # --- Recent alerts ---
    if alerts:
        st.write("")
        section("Recent Alerts", "Latest notifications for you")
        for a in alerts[:5]:
            from src.ui import SEVERITY_EMOJI, PRIORITY_HEX
            emoji = SEVERITY_EMOJI.get(a["severity"], "🔵")
            html(
                f'<div class="tt-alert">'
                f'<div class="sev" style="background:{PRIORITY_HEX.get(a["severity"], MARIGOLD)}"></div>'
                f'<div><div class="t">{a["title"]}</div>'
                f'<div class="ts">{a.get("project_id", "")} · {format_date(a.get("created_at"))}</div>'
                f'</div></div>'
            )
