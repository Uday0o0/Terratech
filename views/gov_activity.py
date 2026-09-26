"""Government Official — Activity Log page."""

import streamlit as st
from src.database import get_activity_log
from src.utils import format_date


def render():
    from src.ui import html, section, TEAL

    section("Activity Log", "Audit trail of all system actions")

    activities = get_activity_log(limit=100)

    if activities:
        html(f'<div style="font-size:12px;color:var(--ink-soft);margin-bottom:12px">'
             f'Showing {len(activities)} most recent entries</div>')

        rows = ""
        for a in activities:
            rows += (
                f'<tr>'
                f'<td>{format_date(a.get("created_at"))}</td>'
                f'<td><b>{a["action"]}</b></td>'
                f'<td>{a.get("entity_type", "—")}</td>'
                f'<td class="tt-mono">{a.get("project_id", "—")}</td>'
                f'<td>{a.get("user_name", "—")}</td>'
                f'<td style="font-size:12px;color:var(--ink-soft)">{a.get("details", "—")}</td>'
                f'</tr>'
            )
        html(
            '<table class="tt-table"><thead><tr>'
            '<th>Date</th><th>Action</th><th>Type</th>'
            '<th>Project</th><th>User</th><th>Details</th>'
            '</tr></thead><tbody>' + rows + '</tbody></table>'
        )
    else:
        html('<div class="tt-empty">No activity recorded.</div>')
