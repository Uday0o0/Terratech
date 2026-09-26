"""Employee Portal — My Projects."""

import streamlit as st
from src.database import get_projects_for_officer, get_project_stages
from src.analytics import compute_risk_for_project
from src.utils import format_date


def render():
    from src.ui import html, section, BAND_HEX, BAND_TEXT_HEX, RUST, MARIGOLD, GREEN, TEAL, render_progress_bar

    user = st.session_state.get("user", {})
    user_id = user.get("id")

    section("My Projects", "Detailed view of projects assigned to you")

    projects = get_projects_for_officer(user_id)

    if not projects:
        html('<div class="tt-empty">No projects assigned to you.</div>')
        return

    # Create dataframe for interactive selection
    import pandas as pd
    df_data = []
    for p in projects:
        risk = compute_risk_for_project(p)
        df_data.append({
            "project_id": p["project_id"],
            "Project": p["project_name"],
            "Location": f"{p['district']}, {p['state']}",
            "Risk": risk["risk_category"],
            "Score": risk.get("risk_score", 0),
            "Progress": p.get("progress_pct", 0),
            "Stage": p.get("current_stage", "—")
        })
    df = pd.DataFrame(df_data)

    st.write("Select a project from the list below to view its details:")
    event = st.dataframe(
        df,
        column_config={
            "project_id": None,
            "Score": st.column_config.NumberColumn(format="%.1f"),
            "Progress": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
        },
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="emp_proj_table"
    )

    selected_id = None
    if len(event.selection.rows) > 0:
        row_idx = event.selection.rows[0]
        selected_id = df.iloc[row_idx]["project_id"]
        # Clear external routing if user manually selects something else
        if "emp_selected_project_id" in st.session_state:
            del st.session_state["emp_selected_project_id"]
    elif st.session_state.get("emp_selected_project_id"):
        selected_id = st.session_state["emp_selected_project_id"]
        
    if selected_id:
        # Find the selected project
        p = next((proj for proj in projects if proj["project_id"] == selected_id), None)
        if p:
            st.write("")
            st.markdown(f"<h3 style='font-family:Fraunces,serif;color:var(--ink)'>Project Blueprint</h3>", unsafe_allow_html=True)
            
            risk = compute_risk_for_project(p)
            cat = risk["risk_category"]
            
            with st.container(border=True):
                # Header row
                h1, h2 = st.columns([3, 1])
                with h1:
                    st.markdown(f"<h2 style='margin-bottom:0;color:{TEAL}'>{p['project_name']}</h2>", unsafe_allow_html=True)
                    st.caption(f"**ID:** {p['project_id']} &nbsp;&nbsp;|&nbsp;&nbsp; **Location:** {p['district']}, {p['state']} &nbsp;&nbsp;|&nbsp;&nbsp; **Priority:** {p.get('priority', 'Medium')}")
                with h2:
                    import plotly.graph_objects as go
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=p.get('progress_pct', 0),
                        number={'suffix': "%", 'font': {'size': 24, 'color': TEAL, 'family': 'Inter'}},
                        gauge={
                            'axis': {'range': [None, 100], 'visible': False},
                            'bar': {'color': TEAL},
                            'bgcolor': "rgba(0,0,0,0)",
                            'borderwidth': 0,
                        }
                    ))
                    fig.update_layout(height=100, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                st.divider()

                from src.database import get_issues_for_project
                issues = get_issues_for_project(selected_id)
                open_issues = [i for i in issues if i.get("status") != "Resolved"]
                
                # Top Key Metrics
                html(
                    '<div class="tt-kpis" style="grid-template-columns:repeat(4,1fr);margin-bottom:15px">'
                    f'<div class="tt-kpi"><div class="num" style="color:{BAND_HEX.get(cat, RUST)}">{risk.get("risk_score", 0):.0f}%</div>'
                    f'<div class="lbl">Overall Risk ({cat})</div></div>'
                    f'<div class="tt-kpi"><div class="num" style="color:var(--ink)">{risk.get("expected_delay_days", 0)}</div>'
                    f'<div class="lbl">Expected Delay (Days)</div></div>'
                    f'<div class="tt-kpi"><div class="num" style="font-size:18px;color:var(--ink);margin-top:6px">{p.get("current_stage", "—")}</div>'
                    f'<div class="lbl">Current Stage</div></div>'
                    f'<div class="tt-kpi"><div class="num" style="color:{"#E84855" if len(open_issues) > 0 else "#2E8B57"}">{len(open_issues)}</div>'
                    f'<div class="lbl">Active Issues</div></div>'
                    '</div>'
                )
                
                # Project Specs
                html(
                    '<div class="tt-kpis" style="grid-template-columns:repeat(4,1fr)">'
                    f'<div class="tt-kpi" style="padding-top:10px;padding-bottom:10px;background:transparent;border:1px dashed var(--border)"><div class="num" style="font-size:22px;color:{TEAL}">₹{p.get("budget_crores", 0):.0f} Cr</div>'
                    f'<div class="lbl">Budget</div></div>'
                    f'<div class="tt-kpi" style="padding-top:10px;padding-bottom:10px;background:transparent;border:1px dashed var(--border)"><div class="num" style="font-size:22px;color:var(--ink)">{p.get("land_area", 0):.1f}</div>'
                    f'<div class="lbl">Area (Hectares)</div></div>'
                    f'<div class="tt-kpi" style="padding-top:10px;padding-bottom:10px;background:transparent;border:1px dashed var(--border)"><div class="num" style="font-size:22px;color:var(--ink)">{p.get("affected_families", 0)}</div>'
                    f'<div class="lbl">Affected Families</div></div>'
                    f'<div class="tt-kpi" style="padding-top:10px;padding-bottom:10px;background:transparent;border:1px dashed var(--border)"><div class="num" style="font-size:22px;color:var(--ink)">{p.get("acquired_parcels", 0)} / {p.get("total_parcels", 0)}</div>'
                    f'<div class="lbl">Parcels Acquired</div></div>'
                    '</div>'
                )

                st.write("")
                
                # Active Issues warnings
                if open_issues:
                    issue_tags = "".join([f'<span style="background:{RUST};color:white;padding:2px 8px;border-radius:4px;font-size:11px;margin-right:6px;">{i["title"]}</span>' for i in open_issues[:3]])
                    if len(open_issues) > 3:
                        issue_tags += f'<span style="font-size:11px;color:var(--ink-soft)">+{len(open_issues)-3} more</span>'
                    html(f'<div style="margin-bottom:20px;"><b>Critical Roadblocks:</b> {issue_tags}</div>')

                # Split bottom half into Left (Timeline) and Right (SHAP + Map)
                left, right = st.columns([1, 1], gap="large")
                
                with left:
                    st.markdown("#### Execution Timeline")
                    stages = get_project_stages(p["project_id"])
                    if stages:
                        timeline = ""
                        for s in stages:
                            status = s.get("status", "Pending")
                            icon = "✓" if status == "Completed" else ("⚙" if status == "In Progress" else "○")
                            cls = "completed" if status == "Completed" else ("active" if status == "In Progress" else "")
                            timeline += (
                                f'<div class="tt-tl-item {cls}">'
                                f'<div class="tt-tl-title">{icon} {s["stage_name"]}</div>'
                                f'<div class="tt-tl-meta">{status} · {s.get("progress_pct", 0):.0f}%</div>'
                                f'</div>'
                            )
                        html(f'<div class="tt-timeline">{timeline}</div>')
                        
                with right:
                    st.markdown("#### Delay Risk Drivers (SHAP)")
                    try:
                        from src.predictor import predict_project
                        from src.utils import extract_ml_dict
                        from src.ui import shap_bar_svg
                        
                        ml_dict = extract_ml_dict(p)
                        result = predict_project(ml_dict)
                        contributors = result.get("top_contributors", [])
                        
                        if contributors:
                            html(f'<div style="margin-bottom:20px;">{shap_bar_svg(contributors)}</div>')
                        else:
                            st.info("No primary risk drivers identified.")
                    except Exception as e:
                        st.warning(f"AI Risk analysis unavailable.")
                    
                    st.markdown("#### GIS Location")
                    lat = p.get("latitude")
                    lng = p.get("longitude")
                    if lat and lng:
                        import folium
                        from streamlit_folium import st_folium
                        m = folium.Map(location=[lat, lng], zoom_start=9, tiles="OpenStreetMap")
                        folium.Marker(
                            [lat, lng],
                            tooltip=p["project_name"],
                            icon=folium.Icon(color="red", icon="info-sign")
                        ).add_to(m)
                        st_folium(m, height=350, use_container_width=True, key=f"map_{p['project_id']}")
                    else:
                        st.info("No spatial data available for this project.")
                
                st.write("")
                st.divider()
                st.markdown("#### Landowners & Parcels")
                from src.database import get_landowners_for_project
                landowners = get_landowners_for_project(selected_id)
                if landowners:
                    import pandas as pd
                    lo_data = []
                    for lo in landowners:
                        lo_data.append({
                            "Name": lo["name"],
                            "ID": lo["landowner_id"],
                            "Village": lo.get("village", "—"),
                            "Parcel": lo.get("parcel_id", "—"),
                            "Area (sqm)": lo.get("land_area_sqm", 0),
                            "Acquisition": lo.get("acquisition_status", "—"),
                            "Compensation": lo.get("compensation_status", "—"),
                        })
                    lo_df = pd.DataFrame(lo_data)
                    st.dataframe(lo_df, use_container_width=True, hide_index=True)
                else:
                    html('<div class="tt-empty">No landowner records for this project.</div>')
