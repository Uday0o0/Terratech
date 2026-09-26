"""Government Official — Risk Intelligence page with map."""

import streamlit as st
import folium
from streamlit_folium import st_folium

from src.analytics import get_projects_with_risk, get_high_risk_projects
from src.utils import extended_risk_category


def render():
    from src.ui import html, section, BAND_HEX, BAND_TEXT_HEX, RUST, MARIGOLD, GREEN, TEAL, render_badge

    section("Risk Intelligence", "AI-powered risk assessment across all projects")

    # --- Risk heatmap ---
    html('<div class="tt-panel"><h3>Project Risk Map</h3></div>')

    projects = get_projects_with_risk()

    # Build map centered on India
    risk_map = folium.Map(location=[22.5, 78.5], zoom_start=5, tiles="OpenStreetMap")

    for p in projects:
        lat = p.get("latitude")
        lng = p.get("longitude")
        if not lat or not lng:
            continue

        cat = p.get("risk_category", "MEDIUM")
        color = BAND_HEX.get(cat, RUST)
        score = p.get("risk_score", 50)

        folium.CircleMarker(
            location=[lat, lng],
            radius=max(6, min(14, score / 8)),
            color=color, weight=2,
            fill=True, fill_color=color, fill_opacity=0.7,
            tooltip=f'{p["project_id"]} — {p["project_name"]} ({cat})',
            popup=folium.Popup(
                f'<b>{p["project_name"]}</b><br>'
                f'{p["district"]}, {p["state"]}<br>'
                f'Risk: {score:.0f}/100 ({cat})<br>'
                f'Stage: {p.get("current_stage", "—")}',
                max_width=280,
            ),
        ).add_to(risk_map)

    st_folium(risk_map, height=450, use_container_width=True,
              returned_objects=["last_object_clicked"])

    # Legend
    html(
        '<div style="display:flex; gap:18px; margin-top:10px; font-size:11.5px; color:var(--ink-soft);">'
        + "".join(
            f'<span style="display:inline-flex;align-items:center;gap:5px;">'
            f'<i style="width:10px;height:10px;border-radius:50%;display:inline-block;'
            f'background:{BAND_HEX[b]}"></i>{b.title()} risk</span>'
            for b in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        )
        + '</div>'
    )

    st.write("")

    # --- Top risk projects ---
    section("Highest Risk Projects", "Top 15 projects by ML risk score")

    high = get_high_risk_projects(15)
    if high:
        rows = ""
        for p in high:
            cat = p.get("risk_category", "MEDIUM")
            badge = render_badge(cat)
            rows += (
                f'<tr>'
                f'<td><b>{p["project_name"]}</b><br>'
                f'<span style="font-size:11px;color:var(--ink-faint)">{p["project_id"]}</span></td>'
                f'<td>{p["district"]}, {p["state"]}</td>'
                f'<td>{p["project_type"]}</td>'
                f'<td class="tt-mono">{p.get("risk_score", 0):.1f}</td>'
                f'<td>{badge}</td>'
                f'<td class="tt-mono">{p.get("expected_delay_days", 0)}d</td>'
                f'<td>{p.get("current_stage", "—")}</td>'
                f'</tr>'
            )
        html(
            '<table class="tt-table"><thead><tr>'
            '<th>Project</th><th>Location</th><th>Type</th>'
            '<th>Score</th><th>Risk</th><th>Delay</th><th>Stage</th>'
            '</tr></thead><tbody>' + rows + '</tbody></table>'
        )

    # --- Early warning ---
    st.write("")
    section("Early Warning", "Projects approaching critical thresholds")

    approaching = [p for p in projects if 60 <= p.get("risk_score", 0) < 85]
    approaching.sort(key=lambda x: x.get("risk_score", 0), reverse=True)

    if approaching:
        for p in approaching[:8]:
            score = p.get("risk_score", 0)
            days_to_critical = max(3, int((85 - score) * 2.5))
            html(
                f'<div class="tt-alert">'
                f'<div class="sev" style="background:{MARIGOLD}"></div>'
                f'<div><div class="t"><b>{p["project_name"]}</b> — '
                f'Risk {score:.0f}%, projected to reach critical in ~{days_to_critical} days</div>'
                f'<div class="ts">{p["project_id"]} · {p["district"]}, {p["state"]}</div>'
                f'</div></div>'
            )
        html('<div class="tt-note" style="margin-top:12px">Forecasts are linear extrapolations '
             'from current project conditions. Not scientifically validated predictions.</div>')
    else:
        html('<div class="tt-empty">No projects approaching critical threshold at this time.</div>')
