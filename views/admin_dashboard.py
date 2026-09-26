"""Super Admin - Platform Dashboard."""

import streamlit as st
from src.database import get_db

def render():
    from src.ui import html, section, TEAL, GREEN, MARIGOLD, RUST
    
    section("Super Admin Dashboard", "Platform-wide intelligence and access control")
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users WHERE role='government'")
    officers_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM users WHERE role='employee'")
    employees_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM users WHERE role='citizen'")
    citizens_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM projects")
    projects_count = c.fetchone()[0]
    
    html(
        f'<div class="tt-kpis" style="margin-bottom:20px">'
        f'<div class="tt-kpi"><div class="num" style="color:{TEAL}">{projects_count}</div><div class="lbl">Total Projects</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{GREEN}">{officers_count}</div><div class="lbl">Government Officers</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{MARIGOLD}">{employees_count}</div><div class="lbl">Field Employees</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{RUST}">{citizens_count}</div><div class="lbl">Registered Citizens</div></div>'
        f'</div>'
    )
    
    st.markdown("### System Health")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.success("Database Status: Online")
    with c2:
        st.success("ML Predictor: Online")
    with c3:
        st.success("Email Service: Online")
        
    st.divider()
    st.markdown("""
    ### Welcome to the Super Admin Interface
    As a Super Admin, you have full control over the platform's hierarchy, user provisioning, and data.
    Use the navigation menu on the left to:
    - **Workforce Management:** Map employees to reporting officers and manage accounts.
    - **Citizen Management:** Manage and monitor registered citizens.
    - **Project 360 View:** View the entire ecosystem of a project, including who is working on it and who is affected.
    - **Portals:** Jump directly into the Government or Employee portals with elevated privileges.
    """)

    st.write("")
    st.markdown("### Global System Activity Log")
    st.caption("Real-time audit log of all actions performed by users across the platform.")
    
    c.execute("""
        SELECT l.timestamp, u.name, u.role, l.action, l.details, l.project_id
        FROM activity_log l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.timestamp DESC LIMIT 15
    """)
    logs = c.fetchall()
    if logs:
        import pandas as pd
        df = pd.DataFrame([{
            'Time': r['timestamp'][:16],
            'User': f"{r['name']} ({r['role'].title()})" if r['name'] else "System",
            'Action': r['action'],
            'Details': r['details'] or "—",
            'Project': r['project_id'] or "—"
        } for r in logs])
        st.dataframe(df, use_container_width=True, hide_index=True)
