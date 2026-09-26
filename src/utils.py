"""
TerraTech — shared utilities.

Risk-band extension, date formatting, ID generation, ML feature extraction.
Nothing here touches the database or the model directly.
"""

import hashlib
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Project type mapping: display name → ML model's known type
# ---------------------------------------------------------------------------
ML_TYPE_MAP = {
    "Highway": "Highway",
    "Expressway": "Highway",
    "Ring Road": "Highway",
    "Railway": "Railway",
    "Metro": "Urban Infrastructure",
    "Smart City": "Urban Infrastructure",
    "Urban Development": "Urban Infrastructure",
    "Industrial Corridor": "Industrial Corridor",
    "Industrial Park": "Industrial Corridor",
    "Airport Expansion": "Industrial Corridor",
    "Power Transmission": "Industrial Corridor",
    "Solar Park": "Industrial Corridor",
    "Irrigation": "Irrigation",
    "Dam": "Irrigation",
}

ALL_PROJECT_TYPES = sorted(ML_TYPE_MAP.keys())


def ml_project_type(display_type: str) -> str:
    """Map a display project type to the ML model's known type."""
    return ML_TYPE_MAP.get(display_type, "Highway")


# ---------------------------------------------------------------------------
# Extended risk banding — adds CRITICAL above HIGH
# ---------------------------------------------------------------------------
def extended_risk_category(probability: float) -> str:
    """
    Four-band risk category used in the UI.

    The trained model defines LOW/MEDIUM/HIGH. This wrapper splits HIGH into
    HIGH (0.70–0.85) and CRITICAL (0.85–1.0). The underlying model and
    src/predictor.py remain untouched.
    """
    if probability >= 0.85:
        return "CRITICAL"
    if probability >= 0.70:
        return "HIGH"
    if probability >= 0.40:
        return "MEDIUM"
    return "LOW"


RISK_COLORS = {
    "LOW": "#3B7A57",
    "MEDIUM": "#E2A83C",
    "HIGH": "#B5502C",
    "CRITICAL": "#8E3A1F",
}

RISK_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


# ---------------------------------------------------------------------------
# ML feature extraction from a project dict (database or JSON)
# ---------------------------------------------------------------------------
ML_FEATURES = [
    "project_type", "land_area", "affected_families",
    "documentation_completion", "compensation_completion",
    "legal_disputes", "approval_delay_days", "rr_completion",
    "possession_completion", "stakeholder_response_days",
    "historical_delay_rate",
]


def extract_ml_dict(project: dict) -> dict:
    """
    Extract the 11 features the ML model expects from a project record.

    Uses ml_project_type for the project_type field so the model receives
    one of its five known categories.
    """
    ml_type = project.get("ml_project_type", project.get("project_type", "Highway"))
    return {
        "project_id": project.get("project_id", "UNKNOWN"),
        "project_name": project.get("project_name", ""),
        "project_type": ml_type,
        "state": project.get("state", ""),
        "district": project.get("district", ""),
        "latitude": project.get("latitude", 0),
        "longitude": project.get("longitude", 0),
        "land_area": float(project.get("land_area", 0)),
        "affected_families": int(project.get("affected_families", 0)),
        "documentation_completion": float(project.get("documentation_completion", 0)),
        "compensation_completion": float(project.get("compensation_completion", 0)),
        "legal_disputes": int(project.get("legal_disputes", 0)),
        "approval_delay_days": int(project.get("approval_delay_days", 0)),
        "rr_completion": float(project.get("rr_completion", 0)),
        "possession_completion": float(project.get("possession_completion", 0)),
        "stakeholder_response_days": int(project.get("stakeholder_response_days", 0)),
        "historical_delay_rate": float(project.get("historical_delay_rate", 0)),
    }


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------
def format_date(dt_str: str | None, fmt: str = "%d %b %Y") -> str:
    """Format an ISO date string for display. Returns '—' for None."""
    if not dt_str:
        return "—"
    try:
        return datetime.fromisoformat(dt_str).strftime(fmt)
    except (ValueError, TypeError):
        return str(dt_str)


def days_between(d1: str, d2: str) -> int | None:
    """Number of days between two ISO date strings."""
    try:
        return abs((datetime.fromisoformat(d2) - datetime.fromisoformat(d1)).days)
    except (ValueError, TypeError):
        return None


def time_ago(dt_str: str) -> str:
    """Human-readable time ago string."""
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str)
        diff = datetime.utcnow() - dt
        if diff.days > 365:
            return f"{diff.days // 365}y ago"
        if diff.days > 30:
            return f"{diff.days // 30}mo ago"
        if diff.days > 0:
            return f"{diff.days}d ago"
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours}h ago"
        return "just now"
    except (ValueError, TypeError):
        return ""


# ---------------------------------------------------------------------------
# ID generation — deterministic, collision-resistant
# ---------------------------------------------------------------------------
_TYPE_PREFIX = {
    "Highway": "NH", "Expressway": "EX", "Ring Road": "RR",
    "Railway": "RW", "Metro": "MT", "Smart City": "SC",
    "Urban Development": "UD", "Industrial Corridor": "IC",
    "Industrial Park": "IP", "Airport Expansion": "AP",
    "Power Transmission": "PT", "Solar Park": "SP",
    "Irrigation": "IR", "Dam": "DM",
}


def generate_project_id(project_type: str, index: int) -> str:
    """Generate a deterministic project ID like NH-07-042."""
    prefix = _TYPE_PREFIX.get(project_type, "TT")
    segment = (index % 20) + 1
    seq = index + 1
    return f"{prefix}-{segment:02d}-{seq:03d}"


def generate_parcel_id(district: str, index: int) -> str:
    """Generate a deterministic parcel ID like BH-0234-009."""
    prefix = district[:2].upper()
    return f"{prefix}-{index:04d}-{(index % 50) + 1:03d}"


def generate_landowner_id(district: str, index: int) -> str:
    """Generate a deterministic landowner ID like LO-BH-0001."""
    prefix = district[:2].upper()
    return f"LO-{prefix}-{index:04d}"


# ---------------------------------------------------------------------------
# Password hashing (stdlib only — no bcrypt dependency)
# ---------------------------------------------------------------------------
_SALT = b"terratech_demo_salt_2026"


def hash_password(password: str) -> str:
    """PBKDF2-SHA256 hash. Demo-grade, not production security."""
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), _SALT, 100_000
    ).hex()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash
