"""Government Official — Dashboard page."""

import streamlit as st
from src.analytics import get_dashboard_stats, get_high_risk_projects
from src.database import get_all_alerts
from src.utils import extended_risk_category, format_date


def render():
    from src.ui import html, section, BAND_HEX, BAND_TEXT_HEX, PRIORITY_HEX, SEVERITY_EMOJI, RUST, MARIGOLD, GREEN, TEAL, render_badge, render_progress_bar

    section("Command Center", "What requires your attention today")

    stats = get_dashboard_stats()

    # --- Critical alerts banner ---
    if stats["critical_risk"] > 0:
        html(
            f'<div style="background:#8E3A1F;color:#fff;padding:12px 18px;border-radius:10px;'
            f'margin-bottom:18px;font-size:13px;font-weight:600">'
            f'{stats["critical_risk"]} project(s) at critical risk level — immediate attention required'
            f'</div>'
        )

    # --- KPI Grid ---
    html(
        '<div class="tt-kpis" style="grid-template-columns:repeat(7,1fr)">'
        f'<div class="tt-kpi"><div class="num" style="color:{TEAL}">{stats["total"]}</div>'
        '<div class="lbl">Total Projects</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{GREEN}">{stats["active"]}</div>'
        '<div class="lbl">Active</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{MARIGOLD}">'
        f'{stats["risk_counts"].get("HIGH", 0)}</div>'
        '<div class="lbl">High Risk</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{RUST}">'
        f'{stats["critical_risk"]}</div>'
        '<div class="lbl">Critical</div></div>'
        f'<div class="tt-kpi"><div class="num">{stats["avg_progress"]:.0f}%</div>'
        '<div class="lbl">Avg Progress</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{MARIGOLD}">{stats["avg_delay"]}d</div>'
        '<div class="lbl">Avg Delay</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{RUST}">{stats["open_issues"]}</div>'
        '<div class="lbl">Open Issues</div></div>'
        '</div>'
    )

    st.write("")

    # --- Two columns: High risk projects + Recent alerts ---
    left, right = st.columns([1.4, 1], gap="medium")

    with left:
        section("High-Risk Projects", "Projects requiring immediate intervention")

        high_risk = get_high_risk_projects(8)
        if high_risk:
            import pandas as pd
            df_data = []
            for p in high_risk:
                df_data.append({
                    "project_id": p["project_id"],
                    "Project": p["project_name"],
                    "Location": f"{p['district']}, {p['state']}",
                    "Score": p.get("risk_score", 0),
                    "Risk": p.get("risk_category", "MEDIUM"),
                    "Delay": f"{p.get('expected_delay_days', 0)}d",
                    "Stage": p.get("current_stage", "—")
                })
            df = pd.DataFrame(df_data)

            st.write("Click a project to view full details.")
            event = st.dataframe(
                df,
                column_config={
                    "project_id": None,
                    "Score": st.column_config.NumberColumn(format="%.1f"),
                },
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key="gov_dash_table"
            )

            if len(event.selection.rows) > 0:
                row_idx = event.selection.rows[0]
                selected_id = df.iloc[row_idx]["project_id"]
                st.session_state.go_to_page = "Project Detail"
                st.session_state.detail_project_id = selected_id
                st.rerun()
        else:
            html('<div class="tt-empty">No high-risk projects identified.</div>')

    with right:
        section("Recent Alerts", "Latest system and manual alerts")

        alerts = get_all_alerts(limit=8)
        if alerts:
            for a in alerts:
                emoji = SEVERITY_EMOJI.get(a["severity"], "🔵")
                html(
                    f'<div class="tt-alert">'
                    f'<div class="sev" style="background:{PRIORITY_HEX.get(a["severity"], MARIGOLD)}"></div>'
                    f'<div><div class="t">{a["title"]}</div>'
                    f'<div class="ts">{a.get("project_id", "")} · {format_date(a.get("created_at"))}</div>'
                    f'</div></div>'
                )
        else:
            html('<div class="tt-empty">No alerts at this time.</div>')

    st.write("")

    # --- Issue summary ---
    section("Issue Summary", "Pending issues across all projects")

    i1, i2, i3, i4 = st.columns(4)
    with i1:
        html(f'<div class="tt-panel"><h3>Legal</h3>'
             f'<div class="num" style="font-family:Fraunces,serif;font-size:28px;font-weight:700;'
             f'color:{RUST}">{stats["pending_legal"]}</div>'
             f'<div style="font-size:11.5px;color:var(--ink-soft)">Pending cases</div></div>')
    with i2:
        html(f'<div class="tt-panel"><h3>Compensation</h3>'
             f'<div class="num" style="font-family:Fraunces,serif;font-size:28px;font-weight:700;'
             f'color:{MARIGOLD}">{stats["pending_compensation"]}</div>'
             f'<div style="font-size:11.5px;color:var(--ink-soft)">Pending cases</div></div>')
    with i3:
        html(f'<div class="tt-panel"><h3>Documentation</h3>'
             f'<div class="num" style="font-family:Fraunces,serif;font-size:28px;font-weight:700;'
             f'color:{TEAL}">{stats["pending_documentation"]}</div>'
             f'<div style="font-size:11.5px;color:var(--ink-soft)">Pending cases</div></div>')
    with i4:
        html(f'<div class="tt-panel"><h3>Unread Alerts</h3>'
             f'<div class="num" style="font-family:Fraunces,serif;font-size:28px;font-weight:700;'
             f'color:{RUST}">{stats["unread_alerts"]}</div>'
             f'<div style="font-size:11.5px;color:var(--ink-soft)">Require attention</div></div>')

    # --- Risk distribution ---
    st.write("")
    section("Risk Distribution", "Current distribution of project risk levels")

    r1, r2, r3, r4 = st.columns(4)
    rc = stats["risk_counts"]
    total = max(stats["total"], 1)
    for col, cat in zip([r1, r2, r3, r4], ["LOW", "MEDIUM", "HIGH", "CRITICAL"]):
        with col:
            count = rc.get(cat, 0)
            pct = count / total * 100
            color = BAND_HEX[cat]
            html(
                f'<div class="tt-panel" style="text-align:center">'
                f'<div style="font-size:11px;font-weight:700;color:{color};'
                f'letter-spacing:.05em;margin-bottom:8px">{cat}</div>'
                f'<div style="font-family:Fraunces,serif;font-size:32px;font-weight:700;'
                f'color:{color}">{count}</div>'
                f'<div style="font-size:11px;color:var(--ink-soft);margin-top:4px">{pct:.0f}% of projects</div>'
                f'{render_progress_bar(pct, color)}'
                f'</div>'
            )
