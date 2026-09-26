"""Government Official — Projects list with filters, search, and create."""

import streamlit as st
from src.database import (
    get_all_projects, get_projects_filtered, get_distinct_values,
    create_project, create_project_stages, log_activity,
)
from src.analytics import compute_risk_for_project
from src.utils import ml_project_type, ALL_PROJECT_TYPES, generate_project_id


def render():
    from src.ui import html, section, BAND_HEX, BAND_TEXT_HEX, RUST, MARIGOLD, GREEN, TEAL, render_progress_bar

    section("Project Registry", "All land acquisition projects across districts")

    # --- Filters ---
    with st.expander("Filters & Search", expanded=False):
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            states = ["All"] + get_distinct_values("state")
            f_state = st.selectbox("State", states, key="proj_f_state")
        with fc2:
            districts = ["All"] + get_distinct_values("district")
            f_district = st.selectbox("District", districts, key="proj_f_district")
        with fc3:
            types = ["All"] + get_distinct_values("project_type")
            f_type = st.selectbox("Project Type", types, key="proj_f_type")
        with fc4:
            statuses = ["All", "In Progress", "Completed", "On Hold", "Not Started", "Cancelled"]
            f_status = st.selectbox("Status", statuses, key="proj_f_status")

        search = st.text_input("Search by project ID, name, or district", key="proj_search")

    # Fetch filtered projects
    projects = get_projects_filtered(
        state=None if f_state == "All" else f_state,
        district=None if f_district == "All" else f_district,
        project_type=None if f_type == "All" else f_type,
        status=None if f_status == "All" else f_status,
        search=search or None,
    )

    # --- Create new project ---
    with st.expander("Create New Project", expanded=False):
        with st.form("create_project_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                p_name = st.text_input("Project Name *")
                p_type = st.selectbox("Project Type *", ALL_PROJECT_TYPES)
                p_state = st.text_input("State *", value="Madhya Pradesh")
                p_district = st.text_input("District *", value="Bhopal")
                p_dept = st.text_input("Department")
            with c2:
                p_land = st.number_input("Land Area (ha)", min_value=0.0, value=100.0)
                p_families = st.number_input("Affected Families", min_value=0, value=50)
                p_budget = st.number_input("Budget (₹ Crore)", min_value=0.0, value=50.0)
                p_priority = st.selectbox("Priority", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
                p_desc = st.text_area("Description", height=80)

            submitted = st.form_submit_button("Create Project", type="primary")
            if submitted and p_name and p_state and p_district:
                pid = generate_project_id(p_type, len(projects) + 200)
                data = {
                    "project_id": pid,
                    "project_name": p_name,
                    "project_type": p_type,
                    "ml_project_type": ml_project_type(p_type),
                    "department": p_dept,
                    "state": p_state,
                    "district": p_district,
                    "description": p_desc,
                    "land_area": p_land,
                    "affected_families": p_families,
                    "budget_crores": p_budget,
                    "priority": p_priority,
                    "project_status": "Not Started",
                    "current_stage": "Land Identification",
                }
                create_project(data)
                create_project_stages(pid, "Land Identification")
                user = st.session_state.get("user", {})
                log_activity(
                    action="Project created",
                    entity_type="project",
                    entity_id=pid,
                    project_id=pid,
                    user_id=user.get("id"),
                    user_name=user.get("name", ""),
                    details=f"Created project: {p_name}",
                )
                st.success(f"Project **{pid}** created successfully.")
                st.rerun()

    # --- Project count ---
    html(f'<div style="font-size:12px;color:var(--ink-soft);margin-bottom:12px">'
         f'Showing {len(projects)} project(s)</div>')

    # --- Projects table ---
    if not projects:
        html('<div class="tt-empty">No projects match the current filters.</div>')
        return

    import pandas as pd
    
    df_data = []
    for p in projects:
        risk = compute_risk_for_project(p)
        df_data.append({
            "project_id": p["project_id"],
            "Project Name": p["project_name"],
            "Type": p["project_type"],
            "Location": f"{p['district']}, {p['state']}",
            "Stage": p.get("current_stage", "—"),
            "Risk": risk["risk_category"],
            "Score": risk.get("risk_score", 0),
            "Progress": p.get("progress_pct", 0),
            "Status": p.get("project_status", "—"),
        })
    df = pd.DataFrame(df_data)

    st.write("Click a row to view full project details.")
    event = st.dataframe(
        df,
        column_config={
            "project_id": None, # hide the ID column
            "Score": st.column_config.NumberColumn(format="%.1f"),
            "Progress": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
        },
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="gov_proj_table"
    )

    if len(event.selection.rows) > 0:
        row_idx = event.selection.rows[0]
        selected_id = df.iloc[row_idx]["project_id"]
        st.session_state.go_to_page = "Project Detail"
        st.session_state.detail_project_id = selected_id
        st.rerun()
