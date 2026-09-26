"""Government Official — Project Detail page (spec §25)."""

import json
import streamlit as st
import folium
from streamlit_folium import st_folium

from src.database import (
    get_all_projects, get_project, get_project_stages,
    get_landowners_for_project, get_issues_for_project,
    get_assignments_for_project, get_activity_log,
    update_project, log_activity, get_all_alerts,
)
from src.predictor import predict_project, STAGES as ML_STAGES
from src.explain import plain_language_explanation, top_contributors
from src.recommendations import generate_recommendations
from src.utils import extract_ml_dict, extended_risk_category, format_date
from src.analytics import compute_risk_for_project


def render():
    from src.ui import (
        html, section, gauge_svg, shap_bar_svg,
        BAND_HEX, BAND_TEXT_HEX, PRIORITY_HEX, SEVERITY_EMOJI,
        RUST, RUST_DEEP, MARIGOLD, MARIGOLD_DEEP, GREEN, TEAL, TEAL_DEEP,
        NAVY_DEEP, stage_band, render_badge, render_progress_bar,
    )

    # --- Project selector ---
    projects = get_all_projects()
    if not projects:
        html('<div class="tt-empty">No projects available.</div>')
        return

    project_options = {p["project_id"]: f'{p["project_id"]} — {p["project_name"]}' for p in projects}

    selected_id = st.selectbox(
        "Select project",
        options=list(project_options.keys()),
        format_func=lambda pid: project_options[pid],
        key="detail_project_id",
    )

    project = get_project(selected_id)
    if not project:
        html('<div class="tt-empty">Project not found.</div>')
        return

    # --- ML Analysis ---
    ml_dict = extract_ml_dict(project)
    try:
        result = predict_project(ml_dict)
        category = extended_risk_category(result["delay_probability"])
        contributors = result.get("top_contributors", [])
        explanation = plain_language_explanation(ml_dict)
        recommendations = generate_recommendations(ml_dict, top_contributors=contributors)
    except Exception as e:
        st.warning(f"ML inference unavailable: {e}")
        result = {"delay_probability": 0.5, "risk_score": 50, "expected_delay_days": 28,
                  "stage_risk": {}, "critical_stage": "Unknown"}
        category = "MEDIUM"
        contributors = []
        explanation = ""
        recommendations = []

    band_color = BAND_HEX.get(category, RUST)

    # =====================================================================
    # PROJECT HEADER
    # =====================================================================
    html(
        f'<div class="tt-detail" style="margin-bottom:20px">'
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px">'
        f'<div>'
        f'<div class="pname">{project["project_name"]}</div>'
        f'<div class="pmeta">{project["project_id"]} · {project["district"]}, {project["state"]} · '
        f'{project["project_type"]}</div>'
        f'</div>'
        f'<div class="tt-gauge-row" style="margin:0">'
        f'<div>{gauge_svg(result["risk_score"], band_color)}</div>'
        f'<div class="tt-metrics-mini">'
        f'<div><span>Risk level</span><b style="color:{band_color}">{category}</b></div>'
        f'<div><span>Delay probability</span><b>{result["delay_probability"] * 100:.1f}%</b></div>'
        f'<div><span>Expected delay</span><b>{result["expected_delay_days"]} days</b></div>'
        f'<div><span>Critical stage</span><b>{result.get("critical_stage", "—")}</b></div>'
        f'</div></div></div></div>'
    )

    # =====================================================================
    # TAB LAYOUT
    # =====================================================================
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Overview", "AI Risk Analysis", "Stage Progress",
        "Land & Landowners", "Recommendations", "Activity"
    ])

    # --- TAB 1: OVERVIEW ---
    with tab1:
        c1, c2 = st.columns([1, 1], gap="medium")
        with c1:
            html(
                f'<div class="tt-panel"><h3>Project Overview</h3><div class="tt-facts">'
                f'<div><span>Department</span><b>{project.get("department", "—")}</b></div>'
                f'<div><span>Status</span><b>{project.get("project_status", "—")}</b></div>'
                f'<div><span>Priority</span><b>{project.get("priority", "—")}</b></div>'
                f'<div><span>Budget</span><b>₹{project.get("budget_crores", 0):.1f} Cr</b></div>'
                f'<div><span>Start date</span><b>{format_date(project.get("start_date"))}</b></div>'
                f'<div><span>Planned completion</span><b>{format_date(project.get("planned_completion_date"))}</b></div>'
                f'<div><span>Est. completion</span><b>{format_date(project.get("estimated_completion_date"))}</b></div>'
                f'<div><span>Current stage</span><b>{project.get("current_stage", "—")}</b></div>'
                f'<div><span>Progress</span><b>{project.get("progress_pct", 0):.0f}%</b></div>'
                f'</div></div>'
            )

        with c2:
            html(
                f'<div class="tt-panel"><h3>Land Acquisition Summary</h3><div class="tt-facts">'
                f'<div><span>Land area</span><b>{project.get("land_area", 0):.0f} ha</b></div>'
                f'<div><span>Affected families</span><b>{project.get("affected_families", 0):,}</b></div>'
                f'<div><span>Total parcels</span><b>{project.get("total_parcels", 0)}</b></div>'
                f'<div><span>Acquired parcels</span><b>{project.get("acquired_parcels", 0)}</b></div>'
                f'<div><span>Documentation</span><b>{project.get("documentation_completion", 0):.0f}%</b></div>'
                f'<div><span>Compensation</span><b>{project.get("compensation_completion", 0):.0f}%</b></div>'
                f'<div><span>R&R completion</span><b>{project.get("rr_completion", 0):.0f}%</b></div>'
                f'<div><span>Possession</span><b>{project.get("possession_completion", 0):.0f}%</b></div>'
                f'<div><span>Legal disputes</span><b>{project.get("legal_disputes", 0)}</b></div>'
                f'</div></div>'
            )

        # Map
        if project.get("latitude") and project.get("longitude"):
            st.write("")
            html('<div class="tt-card-title">Project Location</div>')
            fmap = folium.Map(
                location=[project["latitude"], project["longitude"]],
                zoom_start=11, tiles="OpenStreetMap",
            )
            folium.CircleMarker(
                location=[project["latitude"], project["longitude"]],
                radius=12, color=band_color, weight=3,
                fill=True, fill_color=band_color, fill_opacity=0.85,
                tooltip=f'{project["project_id"]} — {category} risk',
            ).add_to(fmap)
            st_folium(fmap, height=330, use_container_width=True,
                      returned_objects=["last_object_clicked"])

        # Description
        if project.get("description"):
            st.write("")
            html(f'<div class="tt-plain">{project["description"]}</div>')

    # --- TAB 2: AI RISK ANALYSIS ---
    with tab2:
        section("AI Risk Assessment", "ML prediction with TreeSHAP explanation")

        # KPIs
        html(
            f'<div class="tt-kpis">'
            f'<div class="tt-kpi"><div class="num" style="color:{band_color}">'
            f'{result["delay_probability"] * 100:.1f}%</div>'
            f'<div class="lbl">Delay probability</div></div>'
            f'<div class="tt-kpi"><div class="num" style="color:{band_color}">'
            f'{category}</div><div class="lbl">Risk level</div></div>'
            f'<div class="tt-kpi"><div class="num" style="color:{MARIGOLD_DEEP}">'
            f'{result["expected_delay_days"]} days</div>'
            f'<div class="lbl">Expected delay</div></div>'
            f'<div class="tt-kpi"><div class="num" style="color:{TEAL}">'
            f'{result.get("critical_stage", "—")}</div>'
            f'<div class="lbl">Most at-risk stage</div></div>'
            f'</div>'
        )

        st.write("")

        # SHAP
        if contributors:
            c1, c2 = st.columns([1.3, 1], gap="medium")
            with c1:
                html(
                    f'<div class="tt-panel"><h3>Delay Risk Drivers (SHAP)</h3>'
                    f'{shap_bar_svg(contributors)}</div>'
                )
            with c2:
                html(f'<div class="tt-panel"><h3>Plain Language Explanation</h3>'
                     f'<div class="tt-plain">{explanation}</div></div>')

        # Stage risk
        stage_risk = result.get("stage_risk", {})
        if stage_risk:
            st.write("")
            section("Stage-wise Risk", "Rule-based risk indicators for each statutory stage")
            cards = ""
            for stage_name in ML_STAGES:
                score = stage_risk.get(stage_name, 0)
                band = stage_band(score)
                crit = " crit" if stage_name == result.get("critical_stage") else ""
                cards += (
                    f'<div class="tt-stage{crit}"><div class="n">{stage_name}</div>'
                    f'<div class="pct" style="color:{BAND_TEXT_HEX.get(band, RUST)}">{score:.1f}</div>'
                    f'<div class="barwrap"><div class="bar" style="width:{score}%;'
                    f'background:{BAND_HEX.get(band, RUST)}"></div></div></div>'
                )
            html(f'<div class="tt-funnel">{cards}</div>')
            html(
                '<div class="tt-note" style="margin-top:12px">Stage scores come from a transparent '
                "weighted rule over the project's raw parameters. They are an inspectable indicator, "
                "not a separately trained model.</div>"
            )

        # Risk threshold forecast
        st.write("")
        section("Risk Threshold Forecast", "When will this project cross a specified risk threshold?")

        fc1, fc2 = st.columns([1, 2])
        with fc1:
            threshold = st.slider("Risk threshold (%)", 50, 95, 75, key="risk_threshold")
        with fc2:
            current_risk = result["risk_score"]
            if current_risk >= threshold:
                html(
                    f'<div class="tt-panel" style="border-left:3px solid {RUST}">'
                    f'<h3>⚠ Threshold Already Exceeded</h3>'
                    f'<div class="tt-facts">'
                    f'<div><span>Current risk</span><b style="color:{RUST}">{current_risk:.1f}%</b></div>'
                    f'<div><span>Threshold</span><b>{threshold}%</b></div>'
                    f'</div>'
                    f'<div style="font-size:12px;color:var(--ink-soft);margin-top:8px">'
                    f'This project is already above the specified risk threshold.</div></div>'
                )
            else:
                gap = threshold - current_risk
                # Simple linear forecast based on gap
                est_days = max(5, int(gap * 2.5))
                html(
                    f'<div class="tt-panel" style="border-left:3px solid {MARIGOLD}">'
                    f'<h3>Threshold Forecast</h3>'
                    f'<div class="tt-facts">'
                    f'<div><span>Current risk</span><b>{current_risk:.1f}%</b></div>'
                    f'<div><span>Threshold</span><b>{threshold}%</b></div>'
                    f'<div><span>Gap</span><b>{gap:.1f} points</b></div>'
                    f'<div><span>Estimated crossing</span><b style="color:{MARIGOLD}">~{est_days} days</b></div>'
                    f'</div>'
                    f'<div style="font-size:12px;color:var(--ink-soft);margin-top:8px">'
                    f'Forecast based on current project trend. Not a scientifically validated prediction.</div></div>'
                )

    # --- TAB 3: STAGE PROGRESS ---
    with tab3:
        section("Project Timeline", "Nine-stage land acquisition pipeline")

        stages = get_project_stages(selected_id)
        if stages:
            timeline = ""
            for s in stages:
                status = s.get("status", "Pending")
                if status == "Completed":
                    cls = "completed"
                    icon = "✓"
                elif status == "In Progress":
                    cls = "active"
                    icon = "⚙"
                elif status == "Delayed":
                    cls = "delayed"
                    icon = "⚠"
                else:
                    cls = ""
                    icon = "○"

                progress = s.get("progress_pct", 0)
                meta = f'{status} · {progress:.0f}%'
                if s.get("assigned_to"):
                    meta += f' · Officer #{s["assigned_to"]}'

                timeline += (
                    f'<div class="tt-tl-item {cls}">'
                    f'<div class="tt-tl-title">{icon} {s["stage_name"]}</div>'
                    f'<div class="tt-tl-meta">{meta}</div>'
                    f'</div>'
                )
            html(f'<div class="tt-timeline">{timeline}</div>')
        else:
            html('<div class="tt-empty">No stage data available.</div>')

        # Update stage
        st.write("")
        with st.expander("Update Project Stage"):
            with st.form("update_stage_form"):
                new_stage = st.selectbox("Move to stage", [
                    "Land Identification", "Survey & Measurement", "Notification",
                    "Landowner Verification", "Objection Handling", "Compensation",
                    "Legal Clearance", "Possession", "Project Completion",
                ])
                new_status = st.selectbox("Project status", [
                    "In Progress", "On Hold", "Completed",
                ])
                new_progress = st.slider("Overall progress %", 0, 100,
                                        int(project.get("progress_pct", 0)))
                notes = st.text_area("Update notes")

                if st.form_submit_button("Update", type="primary"):
                    update_project(selected_id, {
                        "current_stage": new_stage,
                        "project_status": new_status,
                        "progress_pct": new_progress,
                    })
                    user = st.session_state.get("user", {})
                    log_activity(
                        action="Stage updated",
                        entity_type="project",
                        entity_id=selected_id,
                        project_id=selected_id,
                        user_id=user.get("id"),
                        user_name=user.get("name", ""),
                        details=f"Moved to {new_stage}. Status: {new_status}. {notes}",
                    )
                    st.success("Project updated.")
                    st.rerun()

    # --- TAB 4: LAND & LANDOWNERS ---
    with tab4:
        section("Landowners", "Affected landowners and parcel information")

        landowners = get_landowners_for_project(selected_id)
        if landowners:
            rows = ""
            for lo in landowners:
                rows += (
                    f'<tr>'
                    f'<td><b>{lo["name"]}</b><br>'
                    f'<span style="font-size:11px;color:var(--ink-faint)">{lo["landowner_id"]}</span></td>'
                    f'<td>{lo.get("village", "—")}</td>'
                    f'<td class="tt-mono">{lo.get("parcel_id", "—")}</td>'
                    f'<td>{lo.get("land_area_sqm", 0):.0f} sqm</td>'
                    f'<td>{lo.get("acquisition_status", "—")}</td>'
                    f'<td>{lo.get("compensation_status", "—")}</td>'
                    f'<td>{lo.get("legal_status", "—")}</td>'
                    f'<td>{lo.get("documentation_status", "—")}</td>'
                    f'</tr>'
                )
            html(
                '<table class="tt-table"><thead><tr>'
                '<th>Landowner</th><th>Village</th><th>Parcel</th><th>Area</th>'
                '<th>Acquisition</th><th>Compensation</th><th>Legal</th><th>Docs</th>'
                '</tr></thead><tbody>' + rows + '</tbody></table>'
            )
        else:
            html('<div class="tt-empty">No landowner records for this project.</div>')

        # Issues
        issues = get_issues_for_project(selected_id)
        if issues:
            st.write("")
            section("Issues", "Active legal, compensation, and documentation issues")
            for issue in issues:
                sev_color = PRIORITY_HEX.get(issue.get("severity", "MEDIUM"), MARIGOLD)
                html(
                    f'<div class="tt-rec">'
                    f'<div class="num" style="color:{sev_color}">●</div>'
                    f'<div>'
                    f'<div class="rf">{issue["title"]}</div>'
                    f'<div class="act">{issue.get("description", "")}</div>'
                    f'<div class="meta">Type: {issue["issue_type"]} · '
                    f'Status: {issue.get("status", "Open")} · '
                    f'Severity: {issue.get("severity", "MEDIUM")}'
                    f'{" · Landowner: " + issue["landowner_id"] if issue.get("landowner_id") else ""}</div>'
                    f'</div></div>'
                )

    # --- TAB 5: RECOMMENDATIONS ---
    with tab5:
        section("AI Recommendations", "Actions based on project conditions and model confirmation")

        if recommendations:
            for i, r in enumerate(recommendations, start=1):
                confirmed = ('<span class="tt-confirm">Model-confirmed</span>'
                             if r["model_confirmed"] else "")
                html(
                    f'<div class="tt-rec"><div class="num">{i:02d}</div><div>'
                    f'<div><span class="tt-prio" style="background:'
                    f'{PRIORITY_HEX.get(r["priority"], MARIGOLD)}">{r["priority"]}</span>'
                    f'<span class="rf">{r["risk_factor"]}</span>{confirmed}</div>'
                    f'<div class="act">{r["action"]}</div>'
                    f'<div class="meta">Owner: {r["stakeholder"]} · '
                    f'Current value: {r["current_value"]}</div></div></div>'
                )
        else:
            html('<div class="tt-empty">No recommendations — project within normal parameters.</div>')

        # Assigned officers
        assignments = get_assignments_for_project(selected_id)
        if assignments:
            st.write("")
            section("Assigned Officers", "Personnel assigned to this project")
            rows = ""
            for a in assignments:
                rows += (
                    f'<tr>'
                    f'<td><b>{a.get("officer_name", "—")}</b></td>'
                    f'<td>{a.get("designation", "—")}</td>'
                    f'<td>{a.get("stage_name", "—")}</td>'
                    f'<td>{a.get("role_in_project", "—")}</td>'
                    f'<td>{a.get("priority", "—")}</td>'
                    f'<td>{format_date(a.get("deadline"))}</td>'
                    f'<td>{a.get("status", "—")}</td>'
                    f'</tr>'
                )
            html(
                '<table class="tt-table"><thead><tr>'
                '<th>Officer</th><th>Designation</th><th>Stage</th>'
                '<th>Role</th><th>Priority</th><th>Deadline</th><th>Status</th>'
                '</tr></thead><tbody>' + rows + '</tbody></table>'
            )

    # --- TAB 6: ACTIVITY ---
    with tab6:
        section("Activity History", "Audit trail for this project")

        activities = get_activity_log(project_id=selected_id, limit=30)
        if activities:
            for a in activities:
                html(
                    f'<div class="tt-alert">'
                    f'<div class="sev" style="background:{TEAL}"></div>'
                    f'<div><div class="t"><b>{a["action"]}</b> — {a.get("details", "")}</div>'
                    f'<div class="ts">{a.get("user_name", "")} · {format_date(a.get("created_at"))}</div>'
                    f'</div></div>'
                )
        else:
            html('<div class="tt-empty">No activity recorded for this project.</div>')
