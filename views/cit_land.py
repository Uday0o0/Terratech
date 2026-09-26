"""Citizen Portal — My Land tracking."""

import streamlit as st
from src.database import (
    get_landowner_by_parcel, get_landowners_for_citizen,
    get_issues_for_landowner, get_project, get_assignments_for_project,
)
from src.utils import format_date


def render():
    from src.ui import html, section, GREEN, TEAL, MARIGOLD, RUST

    user = st.session_state.get("user", {})

    section("My Land", "Track your land acquisition status")

    # Parcel ID search
    default_parcel = user.get("citizen_parcel_id", "")
    parcel_id = st.text_input(
        "Enter your Parcel ID",
        value=default_parcel,
        placeholder="e.g. BH-0234-009",
        key="cit_parcel_search",
    )

    if not parcel_id:
        html('<div class="tt-empty">Enter your Parcel ID above to view your land status.</div>')
        return

    # Look up by parcel
    landowner = get_landowner_by_parcel(parcel_id.strip())

    # Also check citizen's linked records
    if not landowner and user.get("id"):
        citizen_records = get_landowners_for_citizen(user["id"])
        if citizen_records:
            landowner = citizen_records[0]

    if not landowner:
        html(f'<div class="tt-empty">No records found for Parcel ID: <b>{parcel_id}</b>. '
             f'Please verify your Parcel ID or contact your local revenue office.</div>')
        return

    # Status colors
    def status_color(status):
        positive = ["Acquired", "Paid", "Clear", "Complete", "Completed", "Verified"]
        negative = ["Disputed", "Failed"]
        return GREEN if status in positive else (RUST if status in negative else MARIGOLD)

    # --- Land details ---
    html(
        f'<div class="tt-panel" style="margin-bottom:16px">'
        f'<h3>Land Record — {landowner.get("parcel_id", "")}</h3>'
        f'<div class="tt-facts">'
        f'<div><span>Landowner</span><b>{landowner["name"]}</b></div>'
        f'<div><span>Landowner ID</span><b>{landowner["landowner_id"]}</b></div>'
        f'<div><span>Village</span><b>{landowner.get("village", "—")}</b></div>'
        f'<div><span>District</span><b>{landowner.get("district", "—")}, {landowner.get("state", "—")}</b></div>'
        f'<div><span>Land area</span><b>{landowner.get("land_area_sqm", 0):.0f} sq.m.</b></div>'
        f'</div></div>'
    )

    # --- Status grid ---
    c1, c2 = st.columns(2, gap="medium")

    with c1:
        acq = landowner.get("acquisition_status", "Pending")
        comp = landowner.get("compensation_status", "Pending")
        html(
            f'<div class="tt-panel"><h3>Acquisition & Compensation</h3><div class="tt-facts">'
            f'<div><span>Acquisition status</span>'
            f'<b style="color:{status_color(acq)}">{acq}</b></div>'
            f'<div><span>Compensation status</span>'
            f'<b style="color:{status_color(comp)}">{comp}</b></div>'
            f'<div><span>Compensation amount</span>'
            f'<b>₹{landowner.get("compensation_amount", 0):,.0f}</b></div>'
            f'</div></div>'
        )

    with c2:
        legal = landowner.get("legal_status", "Pending")
        doc = landowner.get("documentation_status", "Pending")
        survey = landowner.get("survey_status", "Pending")
        verif = landowner.get("verification_status", "Pending")
        html(
            f'<div class="tt-panel"><h3>Documentation & Legal</h3><div class="tt-facts">'
            f'<div><span>Legal status</span>'
            f'<b style="color:{status_color(legal)}">{legal}</b></div>'
            f'<div><span>Documentation</span>'
            f'<b style="color:{status_color(doc)}">{doc}</b></div>'
            f'<div><span>Survey status</span>'
            f'<b style="color:{status_color(survey)}">{survey}</b></div>'
            f'<div><span>Verification</span>'
            f'<b style="color:{status_color(verif)}">{verif}</b></div>'
            f'</div></div>'
        )

    # --- Project info ---
    if landowner.get("project_id"):
        project = get_project(landowner["project_id"])
        if project:
            st.write("")
            html(
                f'<div class="tt-panel"><h3>Related Project</h3><div class="tt-facts">'
                f'<div><span>Project</span><b>{project["project_name"]}</b></div>'
                f'<div><span>Project ID</span><b>{project["project_id"]}</b></div>'
                f'<div><span>Current stage</span><b>{project.get("current_stage", "—")}</b></div>'
                f'<div><span>Progress</span><b>{project.get("progress_pct", 0):.0f}%</b></div>'
                f'<div><span>Expected completion</span>'
                f'<b>{format_date(project.get("estimated_completion_date"))}</b></div>'
                f'</div></div>'
            )

            # Responsible department/officer
            assignments = get_assignments_for_project(project["project_id"])
            if assignments:
                st.write("")
                html('<div class="tt-panel"><h3>Responsible Department</h3>')
                for a in assignments[:3]:
                    html(
                        f'<div style="padding:6px 0;border-bottom:1px dashed var(--rule);'
                        f'font-size:12.5px;color:var(--ink-soft)">'
                        f'<b style="color:var(--ink)">{a.get("officer_name", "—")}</b> · '
                        f'{a.get("designation", "")} · {a.get("department", "")}'
                        f'</div>'
                    )
                html('</div>')

    # --- Issues ---
    issues = get_issues_for_landowner(landowner["landowner_id"])
    if issues:
        st.write("")
        section("Issues", "Issues related to your land")
        for issue in issues:
            sev_color = RUST if issue.get("severity") in ("HIGH", "CRITICAL") else MARIGOLD
            html(
                f'<div class="tt-panel" style="margin-bottom:10px;border-left:3px solid {sev_color}">'
                f'<div style="font-size:13px;font-weight:600;margin-bottom:4px">'
                f'{issue["issue_type"]} Issue — {issue.get("status", "Open")}</div>'
                f'<div style="font-size:13px;color:var(--ink)">{issue["title"]}</div>'
                f'<div style="font-size:12px;color:var(--ink-soft);margin-top:4px">'
                f'{issue.get("description", "")}</div>'
                f'</div>'
            )

    st.write("")
    html('<div class="tt-note">This information is from the project\'s demo database. '
         'For official records, please contact your local Tehsildar or District Revenue Office.</div>')
