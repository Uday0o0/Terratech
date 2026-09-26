"""Employee Portal — My Tasks."""

import streamlit as st
from src.database import get_assignments_for_officer
from src.utils import format_date


def render():
    from src.ui import html, section, PRIORITY_HEX, MARIGOLD, RUST, GREEN, TEAL

    user = st.session_state.get("user", {})
    user_id = user.get("id")

    section("My Tasks", "Your stage assignments and responsibilities")

    assignments = get_assignments_for_officer(user_id)

    if not assignments:
        html('<div class="tt-empty">No tasks assigned to you.</div>')
        return

    # Extract unique projects from assignments for filtering
    unique_projects = list(set([a.get("project_name", "Unknown") for a in assignments]))
    unique_projects.sort()
    
    selected_project = st.selectbox("Filter by Project", ["All Projects"] + unique_projects)
    
    if selected_project != "All Projects":
        assignments = [a for a in assignments if a.get("project_name") == selected_project]

    active = [a for a in assignments if a.get("status") == "Active"]
    completed = [a for a in assignments if a.get("status") != "Active"]

    if active:
        html(f'<div style="font-size:13px;font-weight:600;margin-bottom:12px">'
             f'Active Tasks ({len(active)})</div>')

        for a in active:
            priority_color = PRIORITY_HEX.get(a.get("priority", "MEDIUM"), MARIGOLD)
            html(
                f'<div class="tt-rec">'
                f'<div class="num"><span class="tt-prio" style="background:{priority_color}">'
                f'{a.get("priority", "MEDIUM")}</span></div>'
                f'<div>'
                f'<div class="rf">{a.get("project_name", "—")}</div>'
                f'<div class="act">Stage: <b>{a.get("stage_name", "—")}</b> · '
                f'Role: {a.get("role_in_project", "—")}</div>'
                f'<div class="meta">Project: {a["project_id"]} · '
                f'Deadline: {format_date(a.get("deadline"))} · '
                f'District: {a.get("district", "—")}, {a.get("state", "—")}</div>'
                f'</div></div>'
            )

    if completed:
        st.write("")
        with st.expander(f"Completed Tasks ({len(completed)})"):
            for a in completed:
                html(
                    f'<div class="tt-alert" style="opacity:0.6">'
                    f'<div class="sev" style="background:{GREEN}"></div>'
                    f'<div><div class="t">{a.get("project_name", "—")} — {a.get("stage_name", "—")}</div>'
                    f'<div class="ts">{a["project_id"]} · {a.get("role_in_project", "")}</div>'
                    f'</div></div>'
                )
