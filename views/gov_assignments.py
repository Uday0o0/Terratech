"""Government Official — Assignments page."""

import streamlit as st
from src.database import (
    get_all_projects, get_all_employees, get_officer_workload,
    create_assignment, get_assignments_for_project, log_activity,
)
from src.utils import format_date


def render():
    from src.ui import html, section, TEAL, MARIGOLD, RUST, GREEN

    section("Officer Assignments", "Assign and manage employee responsibilities")

    # --- Assign officer form ---
    with st.expander("Create New Assignment", expanded=False):
        projects = get_all_projects()
        employees = get_all_employees()

        if not projects or not employees:
            st.warning("No projects or employees available.")
        else:
            with st.form("assign_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    proj = st.selectbox(
                        "Project",
                        options=[p["project_id"] for p in projects],
                        format_func=lambda pid: next(
                            (f'{p["project_id"]} — {p["project_name"]}' for p in projects if p["project_id"] == pid),
                            pid
                        ),
                    )
                    emp = st.selectbox(
                        "Officer",
                        options=[e["id"] for e in employees],
                        format_func=lambda eid: next(
                            (f'{e["name"]} ({e.get("designation","")})' for e in employees if e["id"] == eid),
                            str(eid)
                        ),
                    )
                with c2:
                    stage = st.selectbox("Stage", [
                        "Land Identification", "Survey & Measurement", "Notification",
                        "Landowner Verification", "Objection Handling", "Compensation",
                        "Legal Clearance", "Possession", "Project Completion",
                    ])
                    role = st.selectbox("Role", [
                        "Project Lead", "Field Officer", "Verification Officer",
                        "Compensation Lead", "Documentation Officer", "Site Supervisor",
                        "Legal Officer", "Survey Officer",
                    ])
                    priority = st.selectbox("Priority", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
                    deadline = st.date_input("Deadline")
                    notes = st.text_area("Notes", height=60)

                if st.form_submit_button("Assign", type="primary"):
                    create_assignment({
                        "officer_id": emp,
                        "project_id": proj,
                        "stage_name": stage,
                        "role_in_project": role,
                        "priority": priority,
                        "deadline": str(deadline),
                        "assigned_by": st.session_state.get("user", {}).get("id"),
                        "notes": notes,
                    })
                    emp_name = next((e["name"] for e in employees if e["id"] == emp), "")
                    user = st.session_state.get("user", {})
                    log_activity(
                        action="Officer assigned",
                        entity_type="assignment",
                        entity_id=proj,
                        project_id=proj,
                        user_id=user.get("id"),
                        user_name=user.get("name", ""),
                        details=f"Assigned {emp_name} to {stage} stage",
                    )
                    st.success(f"Officer assigned to {proj}.")
                    st.rerun()

    # --- Officer workload ---
    section("Officer Workload", "Current assignment distribution")

    workload = get_officer_workload()
    if workload:
        rows = ""
        for w in workload:
            load_color = RUST if w["active_count"] > 5 else (MARIGOLD if w["active_count"] > 3 else GREEN)
            rows += (
                f'<tr>'
                f'<td><b>{w["name"]}</b></td>'
                f'<td>{w.get("designation", "—")}</td>'
                f'<td>{w.get("department", "—")}</td>'
                f'<td class="tt-mono">{w["project_count"]}</td>'
                f'<td class="tt-mono">{w["assignment_count"]}</td>'
                f'<td class="tt-mono" style="color:{load_color}">{w["active_count"]}</td>'
                f'</tr>'
            )
        html(
            '<table class="tt-table"><thead><tr>'
            '<th>Officer</th><th>Designation</th><th>Department</th>'
            '<th>Projects</th><th>Total Tasks</th><th>Active</th>'
            '</tr></thead><tbody>' + rows + '</tbody></table>'
        )
    else:
        html('<div class="tt-empty">No assignment data available.</div>')
