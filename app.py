"""
TerraTech — AI-Powered Land Acquisition Intelligence & Project Monitoring Platform

Main application entry point. Handles:
1. Database initialization and demo data seeding
2. Authentication gate (login page)
3. Role-based navigation routing
"""

import streamlit as st
from src.database import init_db, db_exists
from src.auth import check_auth, login, logout, get_current_user, get_current_role
from src.ui import build_css, html, NAVY_DEEP, TEAL, MARIGOLD, RUST

# ---------------------------------------------------------------------------
# Page configuration — MUST be the FIRST Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="TerraTech | Land Acquisition Intelligence Platform",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Database bootstrap — only runs once
# ---------------------------------------------------------------------------
init_db()
if not db_exists():
    with st.spinner("Initializing demo data — first run only…"):
        from src.demo_data import seed_all
        seed_all()

# ===========================================================================
# NAVIGATION ROUTING
# ===========================================================================

def render():
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True

    html(build_css(st.session_state.dark_mode))

    if not check_auth():
        # Login page
        html(
            f'<div class="tt-login-box">'
            f'<div style="text-align:center;margin-bottom:24px">'
            f'<div style="width:54px;height:54px;border-radius:12px;margin:0 auto 12px;'
            f'background:linear-gradient(135deg,{TEAL},{NAVY_DEEP});color:#fff;'
            f'display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:700">T</div>'
            f'</div>'
            f'<div class="tt-login-title">TerraTech</div>'
            f'<div class="tt-login-sub">Land Acquisition Intelligence Platform</div>'
            f'</div>'
        )

        with st.container():
            c1, c2, c3 = st.columns([1, 1, 1])
            with c2:
                login_tab, signup_tab = st.tabs(["Sign In", "Citizen Sign Up"])
                
                with login_tab:
                    with st.form("login"):
                        email = st.text_input("Email", placeholder="admin@terratech.demo")
                        pwd = st.text_input("Password", type="password", placeholder="terratech2026")
                        submit = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    
                        if submit:
                            if login(email, pwd):
                                st.rerun()
                            else:
                                st.error("Invalid credentials.")
                
                with signup_tab:
                    with st.form("signup"):
                        s_name = st.text_input("Full Name")
                        s_email = st.text_input("Email Address")
                        s_pwd = st.text_input("Password", type="password")
                        s_phone = st.text_input("Phone Number")
                        s_submit = st.form_submit_button("Register as Citizen", type="primary", use_container_width=True)
                        
                        if s_submit:
                            if not s_name or not s_email or not s_pwd:
                                st.error("Please fill all required fields.")
                            else:
                                from src.database import create_user
                                from src.utils import hash_password
                                try:
                                    create_user(s_email, hash_password(s_pwd), s_name, "citizen", phone=s_phone)
                                    st.success("Registration successful! You can now log in.")
                                except Exception as e:
                                    st.error(f"Error: {e}")
                                
        return

    # --- Authenticated App ---
    user = get_current_user()
    role = get_current_role()

    # Routing mapping
    ROUTES = {
        "government": {
            "Dashboard": "views.gov_dashboard",
            "Projects": "views.gov_projects",
            "Project Detail": "views.gov_project_detail",
            "Analytics": "views.gov_analytics",
            "Risk Intelligence": "views.gov_risk",
            "Assignments": "views.gov_assignments",
            "Alerts": "views.gov_alerts",
            "Reports": "views.gov_reports",
            "Activity Log": "views.gov_activity",
        },
        "employee": {
            "Dashboard": "views.emp_dashboard",
            "My Projects": "views.emp_projects",
            "My Tasks": "views.emp_tasks",
            "Landowners": "views.emp_landowners",
            "Issues": "views.emp_issues",
            "Alerts": "views.emp_alerts",
        },
        "citizen": {
            "Home": "views.cit_home",
            "Local Projects": "views.cit_projects",
            "My Land": "views.cit_land",
            "Project Search": "views.cit_search",
            "Issues": "views.cit_issues",
        },
        "admin": {
            "Super Dashboard": "views.admin_dashboard",
            "Workforce Management": "views.admin_users",
            "Citizen Management": "views.admin_citizens",
            "Project 360 View": "views.admin_projects",
            "-- Government Portal --": "views.gov_dashboard",
            "Gov Projects": "views.gov_projects",
            "Project Detail": "views.gov_project_detail",
            "Gov Analytics": "views.gov_analytics",
            "Gov Risk": "views.gov_risk",
            "-- Employee Portal --": "views.emp_dashboard",
            "My Projects": "views.emp_projects",
            "Emp Tasks": "views.emp_tasks",
            "Emp Issues": "views.emp_issues",
        }
    }

    role_routes = ROUTES.get(role, {})
    if not role_routes:
        st.error("Unknown role.")
        return

    # Handle programmatic navigation (redirect)
    if "go_to_page" in st.session_state:
        st.session_state.nav_radio = st.session_state.go_to_page
        del st.session_state.go_to_page

    if "current_page" not in st.session_state:
        st.session_state.current_page = list(role_routes.keys())[0]

    # Handle role switch without proper page set
    if st.session_state.current_page not in role_routes:
        st.session_state.current_page = list(role_routes.keys())[0]

    # --- Sidebar Layout ---
    with st.sidebar:
        html(
            f'<div class="tt-brand">'
            f'<div class="tt-brand-mark"></div>'
            f'<div><div class="tt-brand-name">TerraTech</div>'
            f'<div class="tt-brand-role">{role.replace("_", " ").title()} Official' if role != 'citizen' else 'Citizen Portal' f'</div>'
            f'</div></div>'
        )

        st.session_state.current_page = st.radio(
            "Navigation",
            options=list(role_routes.keys()),
            label_visibility="collapsed",
            key="nav_radio"
        )

        st.write("")
        html('<div class="tt-side-label">Account</div>')
        html(
            f'<div style="font-size:12.5px;color:#D8E2DE;font-weight:500;margin-bottom:2px">'
            f'{user.get("name", "User")}</div>'
            f'<div style="font-size:11px;color:#7E9490;margin-bottom:18px">'
            f'{user.get("email", "")}</div>'
        )

        st.session_state.dark_mode = st.toggle("Dark mode", value=st.session_state.dark_mode)

        if st.button("Sign out"):
            logout()
            st.rerun()

    # --- Topbar Layout ---
    from src.database import get_alerts_for_user
    alerts = get_alerts_for_user(user.get("id"), role, limit=10) if role != "citizen" else []
    unread = sum(1 for a in alerts if not a.get("is_read"))

    top1, top2 = st.columns([1, 1])
    with top1:
        st.markdown(f"**Welcome, {user.get('name', 'User')}**  \n<span style='font-size:12px;color:gray'>{role.title()} • {unread} alerts</span>", unsafe_allow_html=True)
    with top2:
        html('<div style="text-align:right"><span class="tt-pill">Demo • synthetic data</span> <span class="tt-avatar">R</span></div>')

    st.write("---")

    # --- Page Render ---
    page_module = role_routes[st.session_state.current_page]
    try:
        import importlib
        mod = importlib.import_module(page_module)
        if hasattr(mod, "render"):
            mod.render()
        else:
            st.error(f"Module {page_module} missing render() function.")
    except Exception as e:
        st.error(f"Error loading page: {e}")

if __name__ == "__main__":
    render()
