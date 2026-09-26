"""Super Admin — Workforce Management."""

import streamlit as st
import pandas as pd
from src.database import get_db
from src.utils import hash_password

def render():
    from src.ui import html, section, TEAL
    
    section("Workforce Management", "Manage platform access and organizational hierarchy")
    
    conn = get_db()
    c = conn.cursor()
    
    tab1, tab2, tab3 = st.tabs(["Employee Hierarchy", "Create New User", "Manage Users"])
    
    with tab1:
        st.markdown("### Organizational Structure")
        st.caption("Map employees (field staff) to government officers (managers) and view their current assignments.")
        
        # Get all officers
        c.execute("SELECT id, name, department, designation FROM users WHERE role='government'")
        officers = c.fetchall()
        
        # Get all employees
        c.execute("SELECT id, name, manager_id FROM users WHERE role='employee'")
        employees = c.fetchall()
        
        if officers and employees:
            officer_opts = {o["id"]: f"{o['name']} ({o['designation']})" for o in officers}
            officer_opts[None] = "Unassigned"
            
            with st.container(border=True):
                c1, c2 = st.columns([2, 1])
                with c1:
                    emp_to_edit = st.selectbox("Select Employee to Reassign", [e["name"] for e in employees])
                    selected_emp = next((e for e in employees if e["name"] == emp_to_edit), None)
                with c2:
                    if selected_emp:
                        current_mgr = selected_emp["manager_id"]
                        new_mgr = st.selectbox("Assign to Officer", options=list(officer_opts.keys()), format_func=lambda x: officer_opts[x], index=list(officer_opts.keys()).index(current_mgr) if current_mgr in officer_opts else 0)
                        if st.button("Update Assignment", type="primary", use_container_width=True):
                            c.execute("UPDATE users SET manager_id=? WHERE id=?", (new_mgr, selected_emp["id"]))
                            conn.commit()
                            st.success("Hierarchy updated!")
                            st.rerun()
            
            st.write("")
            st.markdown("#### Workforce & Project Assignments")
            
            # Fetch all assignments
            c.execute("""
                SELECT u.name, u.role, u.department, 
                       (SELECT name FROM users WHERE id = u.manager_id) as manager_name,
                       GROUP_CONCAT(a.project_id, ', ') as projects
                FROM users u
                LEFT JOIN assignments a ON u.id = a.officer_id
                WHERE u.role IN ('government', 'employee')
                GROUP BY u.id
                ORDER BY u.role DESC, u.name ASC
            """)
            rows = c.fetchall()
            
            df = pd.DataFrame([{
                "Name": r["name"],
                "Role": r["role"].title(),
                "Department": r["department"],
                "Reporting To": r["manager_name"] or "—",
                "Assigned Projects": r["projects"] or "None"
            } for r in rows])
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
        else:
            st.info("Insufficient users to build a hierarchy.")
            
    with tab2:
        st.markdown("### Provision New Workforce User")
        with st.form("new_user"):
            col1, col2 = st.columns(2)
            with col1:
                n_name = st.text_input("Full Name")
                n_email = st.text_input("Email Address")
                n_pwd = st.text_input("Temporary Password", type="password")
            with col2:
                n_role = st.selectbox("Role", ["government", "employee"])
                n_dept = st.text_input("Department")
                n_desig = st.text_input("Designation")
            
            submit = st.form_submit_button("Create User", type="primary")
            if submit:
                from src.database import create_user
                try:
                    create_user(n_email, hash_password(n_pwd), n_name, n_role, department=n_dept, designation=n_desig)
                    st.success("User successfully provisioned.")
                except Exception as e:
                    st.error(f"Error: {e}")
                    
    with tab3:
        st.markdown("### Update or Delete Users")
        c.execute("SELECT id, name, email, role, department, designation FROM users WHERE role IN ('government', 'employee')")
        all_workforce = c.fetchall()
        
        if all_workforce:
            user_opts = {r["id"]: f"{r['name']} ({r['role'].title()})" for r in all_workforce}
            sel_id = st.selectbox("Select User to Manage", list(user_opts.keys()), format_func=lambda x: user_opts[x])
            
            if sel_id:
                u = next(r for r in all_workforce if r["id"] == sel_id)
                with st.form("edit_user"):
                    e_name = st.text_input("Name", value=u["name"])
                    e_email = st.text_input("Email", value=u["email"])
                    e_dept = st.text_input("Department", value=u["department"] or "")
                    e_desig = st.text_input("Designation", value=u["designation"] or "")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        update_btn = st.form_submit_button("Update Details", type="primary")
                    with c2:
                        pass
                    
                    if update_btn:
                        c.execute("UPDATE users SET name=?, email=?, department=?, designation=? WHERE id=?", 
                                  (e_name, e_email, e_dept, e_desig, sel_id))
                        conn.commit()
                        st.success("User updated successfully!")
                        st.rerun()
                
                st.write("")
                with st.expander("Danger Zone - Delete User"):
                    st.warning("Deleting this user will remove their access permanently.")
                    if st.button("Delete User Account", type="primary"):
                        c.execute("DELETE FROM users WHERE id=?", (sel_id,))
                        conn.commit()
                        st.success("User deleted.")
                        st.rerun()
        else:
            st.info("No workforce users found.")
