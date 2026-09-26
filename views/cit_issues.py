"""Citizen Portal — Issues page."""

import streamlit as st
from src.database import get_landowners_for_citizen, get_issues_for_landowner


def render():
    from src.ui import html, section, MARIGOLD, RUST

    user = st.session_state.get("user", {})
    user_id = user.get("id")

    section("My Issues", "Legal, compensation, and documentation issues related to your land")

    # Get citizen's landowner records
    landowner_records = get_landowners_for_citizen(user_id)

    if not landowner_records:
        html('<div class="tt-empty">No land records linked to your account. '
             'Visit <b>My Land</b> to look up your parcel.</div>')
        return

    all_issues = []
    for lo in landowner_records:
        issues = get_issues_for_landowner(lo["landowner_id"])
        for issue in issues:
            issue["landowner_name"] = lo["name"]
            issue["parcel_id"] = lo.get("parcel_id", "")
        all_issues.extend(issues)

    if not all_issues:
        html('<div class="tt-empty">No issues found for your land records.</div>')
        return

    for issue in all_issues:
        sev_color = RUST if issue.get("severity") in ("HIGH", "CRITICAL") else MARIGOLD
        html(
            f'<div class="tt-panel" style="margin-bottom:10px;border-left:3px solid {sev_color}">'
            f'<div style="font-size:13px;font-weight:600">'
            f'{issue["issue_type"]} Issue — '
            f'<span style="color:{sev_color}">{issue.get("status", "Open")}</span></div>'
            f'<div style="font-size:13px;color:var(--ink);margin-top:6px">{issue["title"]}</div>'
            f'<div style="font-size:12px;color:var(--ink-soft);margin-top:4px">'
            f'{issue.get("description", "")}</div>'
            f'<div style="font-size:11px;color:var(--ink-faint);margin-top:6px">'
            f'Parcel: {issue.get("parcel_id", "—")} · '
            f'Landowner: {issue.get("landowner_name", "—")}</div>'
            f'</div>'
        )
