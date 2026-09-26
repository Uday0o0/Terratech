"""Employee Portal — Alerts."""

import streamlit as st
from src.database import get_alerts_for_user, mark_alert_read
from src.utils import format_date


def render():
    from src.ui import html, section, PRIORITY_HEX, SEVERITY_EMOJI, MARIGOLD

    user = st.session_state.get("user", {})
    user_id = user.get("id")

    section("Notification Center", "Alerts and messages for you")

    alerts = get_alerts_for_user(user_id, "employee", limit=30)

    if not alerts:
        html('<div class="tt-empty">No notifications at this time.</div>')
        return

    unread = [a for a in alerts if not a.get("is_read")]
    read = [a for a in alerts if a.get("is_read")]

    if unread:
        html(f'<div style="font-size:13px;font-weight:600;margin-bottom:12px">'
             f'New ({len(unread)})</div>')

        for a in unread:
            emoji = SEVERITY_EMOJI.get(a["severity"], "🔵")
            sev_color = PRIORITY_HEX.get(a["severity"], MARIGOLD)
            html(
                f'<div class="tt-rec">'
                f'<div class="num" style="color:{sev_color}">{emoji}</div>'
                f'<div>'
                f'<div class="rf">{a["title"]}</div>'
                f'<div class="act">{a["message"]}</div>'
                f'<div class="meta">{a.get("alert_type", "")} · '
                f'{a.get("project_id", "")} · {format_date(a.get("created_at"))}</div>'
                f'</div></div>'
            )

    if st.button("Mark all as read") and unread:
        for a in unread:
            mark_alert_read(a["id"])
        st.rerun()

    if read:
        with st.expander(f"Read ({len(read)})"):
            for a in read:
                html(
                    f'<div class="tt-alert" style="opacity:0.6">'
                    f'<div class="sev" style="background:{PRIORITY_HEX.get(a["severity"], MARIGOLD)}"></div>'
                    f'<div><div class="t">{a["title"]}</div>'
                    f'<div class="ts">{a.get("project_id", "")} · {format_date(a.get("created_at"))}</div>'
                    f'</div></div>'
                )
