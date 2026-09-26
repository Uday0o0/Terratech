"""Citizen Portal — Project Search."""

import streamlit as st
from src.database import get_projects_filtered
from src.utils import format_date


def render():
    from src.ui import html, section, GREEN, TEAL, MARIGOLD, render_progress_bar

    section("Project Search", "Find land acquisition projects by name, ID, or location")

    search = st.text_input(
        "Search",
        placeholder="Enter project name, ID, or district...",
        key="cit_search_query",
    )

    if not search:
        html('<div class="tt-empty">Enter a search term above to find projects.</div>')
        return

    projects = get_projects_filtered(search=search)

    if not projects:
        html(f'<div class="tt-empty">No projects found for "<b>{search}</b>".</div>')
        return

    html(f'<div style="font-size:12px;color:var(--ink-soft);margin-bottom:12px">'
         f'{len(projects)} result(s)</div>')

    for p in projects:
        progress = p.get("progress_pct", 0)
        status = p.get("project_status", "In Progress")
        html(
            f'<div class="tt-panel" style="margin-bottom:10px">'
            f'<h3 style="margin:0 0 4px">{p["project_name"]}</h3>'
            f'<div style="font-size:12px;color:var(--ink-soft)">'
            f'{p["project_id"]} · {p["project_type"]} · {p["district"]}, {p["state"]}</div>'
            f'<div style="display:flex;gap:24px;margin-top:12px;font-size:13px">'
            f'<div><span style="color:var(--ink-soft)">Progress</span> '
            f'<b>{progress:.0f}%</b></div>'
            f'<div><span style="color:var(--ink-soft)">Stage</span> '
            f'<b>{p.get("current_stage", "—")}</b></div>'
            f'<div><span style="color:var(--ink-soft)">Status</span> '
            f'<b>{status}</b></div>'
            f'<div><span style="color:var(--ink-soft)">Completion</span> '
            f'<b>{format_date(p.get("estimated_completion_date"))}</b></div>'
            f'</div></div>'
        )
