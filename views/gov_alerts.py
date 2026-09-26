"""Government Official — Alerts page with manual alert sending."""

import streamlit as st
from src.database import get_all_alerts, get_all_projects, get_all_employees, mark_alert_read
from src.alerts import send_manual_alert, generate_automatic_alerts
from src.utils import format_date


def render():
    from src.ui import html, section, PRIORITY_HEX, SEVERITY_EMOJI, MARIGOLD, RUST, TEAL

    section("Alert Center", "System alerts and manual notifications")

    # --- Send manual alert ---
    with st.expander("Send Manual Alert", expanded=False):
        projects = get_all_projects()
        employees = get_all_employees()

        with st.form("send_alert_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                alert_type = st.selectbox("Alert Type", [
                    "Urgent", "Project Update", "Deadline", "Legal",
                    "Compensation", "Documentation", "General",
                ])
                severity = st.selectbox("Severity", ["CRITICAL", "HIGH", "MEDIUM", "LOW"])
                title = st.text_input("Title *")
            with c2:
                project_id = st.selectbox(
                    "Project (optional)",
                    options=["—"] + [p["project_id"] for p in projects],
                )
                recipient_type = st.selectbox("Recipient", [
                    "All Employees", "All Government Officials",
                    "Specific Employee",
                ])
                specific_emp = None
                if recipient_type == "Specific Employee" and employees:
                    specific_emp = st.selectbox(
                        "Select Employee",
                        options=[e["id"] for e in employees],
                        format_func=lambda eid: next(
                            (e["name"] for e in employees if e["id"] == eid), str(eid)
                        ),
                    )

            message = st.text_area("Message *", height=100)

            if st.form_submit_button("Send Alert", type="primary"):
                if title and message:
                    user = st.session_state.get("user", {})
                    send_manual_alert(
                        sender_id=user.get("id"),
                        sender_name=user.get("name", ""),
                        alert_type=alert_type,
                        severity=severity,
                        title=title,
                        message=message,
                        project_id=None if project_id == "—" else project_id,
                        recipient_id=specific_emp,
                        recipient_role="employee" if recipient_type == "All Employees" else
                                      "government" if recipient_type == "All Government Officials" else None,
                    )
                    st.success("Alert sent successfully.")
                    st.rerun()
                else:
                    st.error("Title and message are required.")

    # --- Generate automatic alerts ---
    if st.button("Generate System Alerts"):
        count = generate_automatic_alerts()
        st.success(f"Generated {count} automatic alert(s).")
        st.rerun()

    # --- Alert list ---
    alerts = get_all_alerts(limit=50)

    # Filter
    f1, f2 = st.columns([1, 3])
    with f1:
        sev_filter = st.selectbox("Filter severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"], key="alert_sev_f")

    if sev_filter != "All":
        alerts = [a for a in alerts if a.get("severity") == sev_filter]

    html(f'<div style="font-size:12px;color:var(--ink-soft);margin-bottom:12px">'
         f'Showing {len(alerts)} alert(s)</div>')

    if alerts:
        for a in alerts:
            emoji = SEVERITY_EMOJI.get(a["severity"], "🔵")
            sev_color = PRIORITY_HEX.get(a["severity"], MARIGOLD)
            source = "Manual" if a.get("source") == "manual" else "System"
            read_class = " style='opacity:0.6'" if a.get("is_read") else ""

            html(
                f'<div class="tt-rec"{read_class}>'
                f'<div class="num" style="color:{sev_color}">{emoji}</div>'
                f'<div>'
                f'<div class="rf">{a["title"]}</div>'
                f'<div class="act">{a["message"]}</div>'
                f'<div class="meta">{source} · {a.get("alert_type", "")} · '
                f'{a.get("project_id", "")} · {format_date(a.get("created_at"))}'
                f'{" · Action: " + a["recommended_action"] if a.get("recommended_action") else ""}</div>'
                f'</div></div>'
            )
    else:
        html('<div class="tt-empty">No alerts match the current filter.</div>')
