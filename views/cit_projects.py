"""Citizen Portal — Local Projects."""

import streamlit as st
from src.database import get_projects_filtered, get_distinct_values
from src.utils import format_date


def render():
    from src.ui import html, section, GREEN, TEAL, MARIGOLD, render_progress_bar

    section("Local Projects", "Public land acquisition projects in your area")

    # Filters
    c1, c2, c3 = st.columns(3)
    with c1:
        states = ["All"] + get_distinct_values("state")
        f_state = st.selectbox("State", states, key="cit_f_state")
    with c2:
        districts = ["All"] + get_distinct_values("district")
        f_district = st.selectbox("District", districts, key="cit_f_district")
    with c3:
        types = ["All"] + get_distinct_values("project_type")
        f_type = st.selectbox("Project Type", types, key="cit_f_type")

    projects = get_projects_filtered(
        state=None if f_state == "All" else f_state,
        district=None if f_district == "All" else f_district,
        project_type=None if f_type == "All" else f_type,
    )

    html(f'<div style="font-size:12px;color:var(--ink-soft);margin-bottom:12px">'
         f'{len(projects)} project(s) found</div>')

    if not projects:
        html('<div class="tt-empty">No projects found for the selected filters.</div>')
        return

    # Project cards (citizen-friendly, no internal risk scores)
    for p in projects:
        progress = p.get("progress_pct", 0)
        status = p.get("project_status", "In Progress")
        status_color = GREEN if status == "Completed" else (TEAL if status == "In Progress" else MARIGOLD)

        html(
            f'<div class="tt-panel" style="margin-bottom:12px">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px">'
            f'<div>'
            f'<h3 style="margin:0">{p["project_name"]}</h3>'
            f'<div style="font-size:12px;color:var(--ink-soft);margin-top:4px">'
            f'{p["project_type"]} · {p["district"]}, {p["state"]}</div>'
            f'</div>'
            f'<div style="text-align:right">'
            f'<div style="font-size:11px;font-weight:700;color:{status_color};'
            f'letter-spacing:.04em">{status.upper()}</div>'
            f'</div></div>'
            f'<div style="margin-top:14px;display:grid;grid-template-columns:repeat(3,1fr);gap:14px">'
            f'<div><div style="font-size:11px;color:var(--ink-soft)">Progress</div>'
            f'<div style="font-family:Fraunces,serif;font-size:22px;font-weight:700">{progress:.0f}%</div>'
            f'{render_progress_bar(progress)}</div>'
            f'<div><div style="font-size:11px;color:var(--ink-soft)">Current Stage</div>'
            f'<div style="font-size:14px;font-weight:600;margin-top:4px">{p.get("current_stage", "—")}</div></div>'
            f'<div><div style="font-size:11px;color:var(--ink-soft)">Expected Completion</div>'
            f'<div style="font-size:14px;font-weight:600;margin-top:4px">'
            f'{format_date(p.get("estimated_completion_date"))}</div></div>'
            f'</div></div>'
        )
