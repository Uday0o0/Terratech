"""Employee Portal — Landowners for assigned projects."""

import streamlit as st
from src.database import get_projects_for_officer, get_landowners_for_project


def render():
    from src.ui import html, section

    user = st.session_state.get("user", {})
    user_id = user.get("id")

    section("Landowner Records", "Landowners for your assigned projects")

    projects = get_projects_for_officer(user_id)

    if not projects:
        html('<div class="tt-empty">No projects assigned — no landowner data to show.</div>')
        return

    project_id = st.selectbox(
        "Select Project",
        options=[p["project_id"] for p in projects],
        format_func=lambda pid: next(
            (f'{p["project_id"]} — {p["project_name"]}' for p in projects if p["project_id"] == pid),
            pid
        ),
    )

    landowners = get_landowners_for_project(project_id)

    if landowners:
        html(f'<div style="font-size:12px;color:var(--ink-soft);margin-bottom:12px">'
             f'{len(landowners)} landowner(s) for this project</div>')

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
                f'<td>{lo.get("survey_status", "—")}</td>'
                f'<td>{lo.get("verification_status", "—")}</td>'
                f'</tr>'
            )
        html(
            '<table class="tt-table"><thead><tr>'
            '<th>Landowner</th><th>Village</th><th>Parcel</th><th>Area</th>'
            '<th>Acquisition</th><th>Compensation</th><th>Survey</th><th>Verification</th>'
            '</tr></thead><tbody>' + rows + '</tbody></table>'
        )
    else:
        html('<div class="tt-empty">No landowner records for this project.</div>')
