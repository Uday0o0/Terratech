"""Super Admin — Project 360 View."""

import streamlit as st
import pandas as pd
from src.database import get_db, get_all_projects

def render():
    from src.ui import html, section, TEAL, GREEN, MARIGOLD, RUST
    
    section("Project 360 Ecosystem", "Complete overview of all parties involved in a project")
    
    conn = get_db()
    c = conn.cursor()
    
    projects = get_all_projects()
    if not projects:
        st.info("No projects available.")
        return
        
    project_opts = {p["project_id"]: f"{p['project_id']} — {p['project_name']}" for p in projects}
    selected_id = st.selectbox("Select Project for Ecosystem View", list(project_opts.keys()), format_func=lambda x: project_opts[x])
    
    if selected_id:
        p = next(p for p in projects if p["project_id"] == selected_id)
        
        st.write("")
        html(
            f'<div class="tt-panel" style="margin-bottom:20px;border-left:3px solid {TEAL}">'
            f'<h3>{p["project_name"]}</h3>'
            f'<div style="color:var(--ink-soft);font-size:14px">{p["district"]}, {p["state"]}</div>'
            f'<div style="margin-top:10px;display:flex;gap:15px;font-size:13px">'
            f'<span><b>Type:</b> {p["project_type"]}</span>'
            f'<span><b>Status:</b> {p.get("project_status", "—")}</span>'
            f'<span><b>Stage:</b> {p.get("current_stage", "—")}</span>'
            f'</div></div>'
        )
        
        # 1. Government Officers Assigned
        st.markdown("### 🏛️ Government Officers Assigned")
        c.execute("""
            SELECT u.name, u.designation, u.department, a.role_in_project
            FROM assignments a
            JOIN users u ON a.officer_id = u.id
            WHERE a.project_id = ? AND u.role = 'government'
        """, (selected_id,))
        officers = c.fetchall()
        
        if officers:
            df_off = pd.DataFrame([dict(r) for r in officers])
            st.dataframe(df_off, use_container_width=True, hide_index=True)
        else:
            st.info("No Government Officers explicitly assigned via assignments table.")
            
        # 2. Employees Working
        st.markdown("### 👷 Field Employees Attached")
        # Employees are attached if they report to one of the officers assigned to this project
        c.execute("""
            SELECT u.name, u.designation, u.department, 
                   (SELECT name FROM users WHERE id = u.manager_id) as reporting_to
            FROM users u
            WHERE u.role = 'employee' AND u.manager_id IN (
                SELECT officer_id FROM assignments WHERE project_id = ?
            )
        """, (selected_id,))
        employees = c.fetchall()
        
        if employees:
            df_emp = pd.DataFrame([dict(r) for r in employees])
            st.dataframe(df_emp, use_container_width=True, hide_index=True)
        else:
            st.info("No Field Employees are reporting to the officers assigned to this project.")
            
        # 3. Affected Citizens
        st.markdown("### 🧑‍🤝‍🧑 Affected Citizens (Registered)")
        # Citizens whose parcel is in the landowners table for this project, OR whose citizen_parcel_id matches
        c.execute("""
            SELECT u.name, u.email, u.phone, u.citizen_parcel_id
            FROM users u
            WHERE u.role = 'citizen' AND u.citizen_parcel_id IN (
                SELECT parcel_id FROM landowners WHERE project_id = ?
            )
        """, (selected_id,))
        citizens = c.fetchall()
        
        if citizens:
            df_cit = pd.DataFrame([dict(r) for r in citizens])
            st.dataframe(df_cit, use_container_width=True, hide_index=True)
        else:
            st.info("No registered citizens are linked to parcels in this project.")
