"""
TerraTech — alert engine.

Generates automatic system alerts based on project conditions. Also provides
the manual alert API used by government officials.
"""

from src.database import (
    create_alert, get_all_projects, get_project,
    log_activity,
)


# ---------------------------------------------------------------------------
# Automatic alert generation
# ---------------------------------------------------------------------------
_AUTO_RULES = [
    # (condition, severity, title_template, message_template, alert_type, action)
    (
        lambda p: p.get("compensation_completion", 100) < 40,
        "CRITICAL",
        "Critical: Compensation Severely Behind",
        "Compensation disbursal for {project_id} is only {compensation_completion:.0f}%. Urgent intervention required.",
        "Compensation",
        "Convene emergency compensation review and audit all pending awards.",
    ),
    (
        lambda p: 0 < p.get("legal_disputes", 0) >= 8,
        "CRITICAL",
        "Critical: High Volume Legal Disputes",
        "Project {project_id} has {legal_disputes} unresolved legal disputes.",
        "Legal",
        "Prioritise case-wise legal review; pursue Lok Adalat settlements.",
    ),
    (
        lambda p: p.get("rr_completion", 100) < 40,
        "HIGH",
        "R&R Obligations Substantially Pending",
        "R&R completion for {project_id} is at {rr_completion:.0f}%. Resettlement site readiness must be confirmed.",
        "Compensation",
        "Review pending R&R entitlements; schedule disbursal camp.",
    ),
    (
        lambda p: p.get("possession_completion", 100) < 30,
        "HIGH",
        "Possession Progress Critical",
        "Physical possession for {project_id} is at {possession_completion:.0f}%. Project timeline at risk.",
        "Deadline",
        "Sequence possession for encumbrance-free parcels first.",
    ),
    (
        lambda p: p.get("documentation_completion", 100) < 50,
        "HIGH",
        "Documentation Incomplete",
        "Documentation completion for {project_id} is below 50% at {documentation_completion:.0f}%.",
        "Documentation",
        "Complete mutation, survey verification and title reconciliation.",
    ),
    (
        lambda p: p.get("approval_delay_days", 0) >= 45,
        "HIGH",
        "Statutory Approvals Severely Delayed",
        "Approval delay for {project_id} is {approval_delay_days} days — well above target.",
        "Deadline",
        "Escalate pending approvals to district review committee.",
    ),
    (
        lambda p: 30 <= p.get("approval_delay_days", 0) < 45,
        "MEDIUM",
        "Approval Delay Warning",
        "Approval turnaround for {project_id} is {approval_delay_days} days.",
        "Deadline",
        "Review file movement and fix accountability.",
    ),
    (
        lambda p: p.get("stakeholder_response_days", 0) >= 15,
        "MEDIUM",
        "Slow Stakeholder Response",
        "Stakeholder response time for {project_id} is {stakeholder_response_days} days.",
        "General",
        "Establish single-window grievance desk.",
    ),
]


def generate_automatic_alerts(project_id: str = None):
    """
    Run all automatic alert rules for one project or all projects.

    Called on-demand (not on every page load) to avoid alert flooding.
    """
    if project_id:
        projects = [get_project(project_id)]
        projects = [p for p in projects if p]
    else:
        projects = get_all_projects()

    created = 0
    for proj in projects:
        for rule in _AUTO_RULES:
            condition, severity, title, msg_tmpl, alert_type, action = rule
            try:
                if condition(proj):
                    msg = msg_tmpl.format(**proj)
                    create_alert({
                        "alert_type": alert_type,
                        "severity": severity,
                        "title": title,
                        "message": msg,
                        "project_id": proj["project_id"],
                        "stage_name": proj.get("current_stage"),
                        "source": "system",
                        "recipient_role": "government",
                        "recommended_action": action,
                    })
                    created += 1
            except Exception:
                continue
    return created


# ---------------------------------------------------------------------------
# Manual alert
# ---------------------------------------------------------------------------
def send_manual_alert(
    sender_id: int,
    sender_name: str,
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    project_id: str = None,
    recipient_id: int = None,
    recipient_role: str = None,
) -> int:
    """Send a manual alert from a government official."""
    alert_id = create_alert({
        "alert_type": alert_type,
        "severity": severity,
        "title": title,
        "message": message,
        "project_id": project_id,
        "source": "manual",
        "sender_id": sender_id,
        "recipient_id": recipient_id,
        "recipient_role": recipient_role,
        "recommended_action": None,
    })

    log_activity(
        action="Alert sent",
        entity_type="alert",
        entity_id=str(alert_id),
        project_id=project_id,
        user_id=sender_id,
        user_name=sender_name,
        details=f"Manual alert: {title}",
    )
    return alert_id
