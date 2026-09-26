"""Super Admin — Citizen Management."""

import streamlit as st
import pandas as pd
from src.database import get_db
from src.utils import hash_password

def render():
    from src.ui import html, section, RUST
    
    section("Citizen Management", "Register, manage, and monitor civilian landowners")
    
    conn = get_db()
    c = conn.cursor()
    
    tab1, tab2 = st.tabs(["Registered Citizens", "Manual Registration"])
    
    with tab1:
        c.execute("SELECT id, name, email, phone, state, district, citizen_parcel_id, created_at FROM users WHERE role='citizen'")
        citizens = c.fetchall()
        
        if citizens:
            df = pd.DataFrame([{
                "ID": r["id"],
                "Name": r["name"],
                "Email": r["email"],
                "Phone": r["phone"] or "—",
                "Parcel ID Link": r["citizen_parcel_id"] or "Not Linked",
                "Registered At": r["created_at"][:10]
            } for r in citizens])
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.write("")
            with st.expander("Delete Citizen Account", expanded=False):
                st.warning("Account deletion is permanent.")
                del_id = st.selectbox("Select Citizen to Delete", [f"{r['id']} - {r['name']}" for r in citizens])
                if st.button("Delete Account", type="primary"):
                    cid = int(del_id.split(" - ")[0])
                    c.execute("DELETE FROM users WHERE id=?", (cid,))
                    conn.commit()
                    st.success("Citizen account deleted.")
                    st.rerun()
        else:
            st.info("No citizens registered yet.")
            
    with tab2:
        st.markdown("### Manually Register a Citizen")
        st.caption("Admin override to manually register landowners who do not have internet access.")
        with st.form("new_cit"):
            col1, col2 = st.columns(2)
            with col1:
                c_name = st.text_input("Full Name")
                c_email = st.text_input("Email Address")
                c_pwd = st.text_input("Temporary Password", type="password")
            with col2:
                c_phone = st.text_input("Phone Number")
                c_parcel = st.text_input("Link to Parcel ID (Optional)")
            
            submit = st.form_submit_button("Register Citizen", type="primary", use_container_width=True)
            if submit:
                from src.database import create_user
                try:
                    create_user(c_email, hash_password(c_pwd), c_name, "citizen", phone=c_phone, citizen_parcel_id=c_parcel if c_parcel else None)
                    st.success("Citizen successfully registered.")
                except Exception as e:
                    st.error(f"Error: {e}")
