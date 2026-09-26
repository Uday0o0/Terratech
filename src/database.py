"""
TerraTech — SQLite data layer.

Manages all persistent state: users, projects, stages, landowners,
assignments, alerts, issues, activity log. No business logic lives here;
this module is purely CRUD + schema.

Database file: data/terratech.db (auto-created on first run).
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "terratech.db"

# Nine-stage pipeline for land acquisition projects
PROJECT_STAGES = [
    "Land Identification",
    "Survey & Measurement",
    "Notification",
    "Landowner Verification",
    "Objection Handling",
    "Compensation",
    "Legal Clearance",
    "Possession",
    "Project Completion",
]


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
def get_db() -> sqlite3.Connection:
    """Return a connection with WAL mode, foreign keys, and Row factory."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    name            TEXT NOT NULL,
    role            TEXT NOT NULL CHECK(role IN ('admin','government','employee','citizen')),
    department      TEXT,
    designation     TEXT,
    phone           TEXT,
    district        TEXT,
    state           TEXT,
    citizen_parcel_id TEXT,
    manager_id      INTEGER REFERENCES users(id),
    is_active       INTEGER DEFAULT 1,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS projects (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id                TEXT UNIQUE NOT NULL,
    project_name              TEXT NOT NULL,
    project_type              TEXT NOT NULL,
    ml_project_type           TEXT NOT NULL,
    department                TEXT,
    state                     TEXT NOT NULL,
    district                  TEXT NOT NULL,
    location                  TEXT,
    description               TEXT,
    latitude                  REAL,
    longitude                 REAL,
    land_area                 REAL NOT NULL DEFAULT 0,
    affected_families         INTEGER NOT NULL DEFAULT 0,
    documentation_completion  REAL NOT NULL DEFAULT 0,
    compensation_completion   REAL NOT NULL DEFAULT 0,
    legal_disputes            INTEGER NOT NULL DEFAULT 0,
    approval_delay_days       INTEGER NOT NULL DEFAULT 0,
    rr_completion             REAL NOT NULL DEFAULT 0,
    possession_completion     REAL NOT NULL DEFAULT 0,
    stakeholder_response_days INTEGER NOT NULL DEFAULT 0,
    historical_delay_rate     REAL NOT NULL DEFAULT 0,
    start_date                TEXT,
    planned_completion_date   TEXT,
    estimated_completion_date TEXT,
    current_stage             TEXT DEFAULT 'Land Identification',
    project_status            TEXT DEFAULT 'In Progress'
        CHECK(project_status IN ('Not Started','In Progress','On Hold','Completed','Cancelled')),
    priority                  TEXT DEFAULT 'MEDIUM'
        CHECK(priority IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    budget_crores             REAL,
    total_parcels             INTEGER DEFAULT 0,
    acquired_parcels          INTEGER DEFAULT 0,
    progress_pct              REAL DEFAULT 0,
    created_by                INTEGER REFERENCES users(id),
    created_at                TEXT DEFAULT (datetime('now')),
    updated_at                TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS project_stages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(project_id),
    stage_name      TEXT NOT NULL,
    stage_order     INTEGER NOT NULL,
    status          TEXT DEFAULT 'Pending'
        CHECK(status IN ('Pending','In Progress','Completed','Delayed','Skipped')),
    progress_pct    REAL DEFAULT 0,
    start_date      TEXT,
    target_date     TEXT,
    completion_date TEXT,
    assigned_to     INTEGER REFERENCES users(id),
    notes           TEXT,
    UNIQUE(project_id, stage_name)
);

CREATE TABLE IF NOT EXISTS landowners (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    landowner_id          TEXT UNIQUE NOT NULL,
    name                  TEXT NOT NULL,
    village               TEXT,
    district              TEXT,
    state                 TEXT,
    phone                 TEXT,
    parcel_id             TEXT,
    project_id            TEXT REFERENCES projects(project_id),
    land_area_sqm         REAL,
    acquisition_status    TEXT DEFAULT 'Pending',
    compensation_status   TEXT DEFAULT 'Pending',
    compensation_amount   REAL,
    legal_status          TEXT DEFAULT 'Clear',
    documentation_status  TEXT DEFAULT 'Pending',
    survey_status         TEXT DEFAULT 'Pending',
    verification_status   TEXT DEFAULT 'Pending',
    assigned_officer_id   INTEGER REFERENCES users(id),
    citizen_user_id       INTEGER REFERENCES users(id),
    created_at            TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS assignments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    officer_id      INTEGER NOT NULL REFERENCES users(id),
    project_id      TEXT NOT NULL REFERENCES projects(project_id),
    stage_name      TEXT,
    role_in_project TEXT,
    priority        TEXT DEFAULT 'MEDIUM',
    deadline        TEXT,
    status          TEXT DEFAULT 'Active',
    assigned_by     INTEGER REFERENCES users(id),
    assigned_at     TEXT DEFAULT (datetime('now')),
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type      TEXT NOT NULL,
    severity        TEXT NOT NULL,
    title           TEXT NOT NULL,
    message         TEXT NOT NULL,
    project_id      TEXT REFERENCES projects(project_id),
    stage_name      TEXT,
    source          TEXT DEFAULT 'system',
    sender_id       INTEGER REFERENCES users(id),
    recipient_id    INTEGER REFERENCES users(id),
    recipient_role  TEXT,
    is_read         INTEGER DEFAULT 0,
    recommended_action TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS issues (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      TEXT NOT NULL REFERENCES projects(project_id),
    landowner_id    TEXT REFERENCES landowners(landowner_id),
    issue_type      TEXT NOT NULL
        CHECK(issue_type IN ('Legal','Compensation','Documentation','Survey','Verification','Other')),
    status          TEXT DEFAULT 'Open'
        CHECK(status IN ('Open','Under Review','In Progress','Resolved','Closed')),
    severity        TEXT DEFAULT 'MEDIUM',
    title           TEXT NOT NULL,
    description     TEXT,
    assigned_to     INTEGER REFERENCES users(id),
    resolved_at     TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS activity_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    action          TEXT NOT NULL,
    entity_type     TEXT,
    entity_id       TEXT,
    project_id      TEXT,
    user_id         INTEGER REFERENCES users(id),
    user_name       TEXT,
    details         TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);
"""


def init_db():
    """Create all tables. Safe to call repeatedly (IF NOT EXISTS)."""
    conn = get_db()
    conn.executescript(_SCHEMA)
    conn.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _row_to_dict(row) -> dict | None:
    if row is None:
        return None
    return dict(row)


def _rows_to_list(rows) -> list[dict]:
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
def create_user(email: str, password_hash: str, name: str, role: str, **kwargs) -> int:
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT OR IGNORE INTO users
               (email, password_hash, name, role, department, designation,
                phone, district, state, citizen_parcel_id)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (email, password_hash, name, role,
             kwargs.get("department"), kwargs.get("designation"),
             kwargs.get("phone"), kwargs.get("district"),
             kwargs.get("state"), kwargs.get("citizen_parcel_id")),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def get_users_by_role(role: str) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM users WHERE role = ? AND is_active = 1 ORDER BY name", (role,)
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_all_employees() -> list[dict]:
    return get_users_by_role("employee")


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
def create_project(data: dict) -> str:
    conn = get_db()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO projects
               (project_id, project_name, project_type, ml_project_type,
                department, state, district, location, description,
                latitude, longitude,
                land_area, affected_families, documentation_completion,
                compensation_completion, legal_disputes, approval_delay_days,
                rr_completion, possession_completion, stakeholder_response_days,
                historical_delay_rate,
                start_date, planned_completion_date, estimated_completion_date,
                current_stage, project_status, priority, budget_crores,
                total_parcels, acquired_parcels, progress_pct, created_by)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data["project_id"], data["project_name"],
                data["project_type"], data.get("ml_project_type", data["project_type"]),
                data.get("department"), data["state"], data["district"],
                data.get("location"), data.get("description"),
                data.get("latitude"), data.get("longitude"),
                data.get("land_area", 0), data.get("affected_families", 0),
                data.get("documentation_completion", 0),
                data.get("compensation_completion", 0),
                data.get("legal_disputes", 0), data.get("approval_delay_days", 0),
                data.get("rr_completion", 0), data.get("possession_completion", 0),
                data.get("stakeholder_response_days", 0),
                data.get("historical_delay_rate", 0),
                data.get("start_date"), data.get("planned_completion_date"),
                data.get("estimated_completion_date"),
                data.get("current_stage", "Land Identification"),
                data.get("project_status", "In Progress"),
                data.get("priority", "MEDIUM"),
                data.get("budget_crores"),
                data.get("total_parcels", 0), data.get("acquired_parcels", 0),
                data.get("progress_pct", 0), data.get("created_by"),
            ),
        )
        conn.commit()
        return data["project_id"]
    finally:
        conn.close()


def get_project(project_id: str) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM projects WHERE project_id = ?", (project_id,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def get_all_projects() -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM projects ORDER BY project_id"
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_projects_filtered(
    state: str = None, district: str = None, project_type: str = None,
    status: str = None, priority: str = None, risk_level: str = None,
    search: str = None, department: str = None,
) -> list[dict]:
    """Filter projects. risk_level is not in DB — caller must post-filter."""
    conn = get_db()
    try:
        clauses, params = [], []
        if state:
            clauses.append("state = ?")
            params.append(state)
        if district:
            clauses.append("district = ?")
            params.append(district)
        if project_type:
            clauses.append("project_type = ?")
            params.append(project_type)
        if status:
            clauses.append("project_status = ?")
            params.append(status)
        if priority:
            clauses.append("priority = ?")
            params.append(priority)
        if department:
            clauses.append("department = ?")
            params.append(department)
        if search:
            clauses.append(
                "(project_id LIKE ? OR project_name LIKE ? OR district LIKE ?)"
            )
            s = f"%{search}%"
            params.extend([s, s, s])
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = conn.execute(
            f"SELECT * FROM projects{where} ORDER BY project_id", params
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def update_project(project_id: str, data: dict):
    """Update arbitrary project columns."""
    if not data:
        return
    conn = get_db()
    try:
        sets = ", ".join(f"{k} = ?" for k in data)
        vals = list(data.values()) + [project_id]
        conn.execute(
            f"UPDATE projects SET {sets}, updated_at = datetime('now') WHERE project_id = ?",
            vals,
        )
        conn.commit()
    finally:
        conn.close()


def get_projects_for_officer(officer_id: int) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT DISTINCT p.* FROM projects p
               JOIN assignments a ON a.project_id = p.project_id
               WHERE a.officer_id = ? AND a.status = 'Active'
               ORDER BY p.project_id""",
            (officer_id,),
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_project_stats() -> dict:
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        active = conn.execute(
            "SELECT COUNT(*) FROM projects WHERE project_status = 'In Progress'"
        ).fetchone()[0]
        completed = conn.execute(
            "SELECT COUNT(*) FROM projects WHERE project_status = 'Completed'"
        ).fetchone()[0]
        on_hold = conn.execute(
            "SELECT COUNT(*) FROM projects WHERE project_status = 'On Hold'"
        ).fetchone()[0]
        return {
            "total": total, "active": active, "completed": completed,
            "on_hold": on_hold,
        }
    finally:
        conn.close()


def get_distinct_values(column: str) -> list[str]:
    """Get distinct non-null values for a project column (for filter dropdowns)."""
    conn = get_db()
    try:
        rows = conn.execute(
            f"SELECT DISTINCT {column} FROM projects WHERE {column} IS NOT NULL ORDER BY {column}"
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Project Stages
# ---------------------------------------------------------------------------
def create_project_stages(project_id: str, current_stage: str = "Land Identification"):
    """Insert all nine stages for a project, marking completed/in-progress."""
    conn = get_db()
    try:
        current_idx = PROJECT_STAGES.index(current_stage) if current_stage in PROJECT_STAGES else 0
        for i, stage in enumerate(PROJECT_STAGES):
            if i < current_idx:
                status = "Completed"
                progress = 100.0
            elif i == current_idx:
                status = "In Progress"
                progress = 50.0
            else:
                status = "Pending"
                progress = 0.0
            conn.execute(
                """INSERT OR IGNORE INTO project_stages
                   (project_id, stage_name, stage_order, status, progress_pct)
                   VALUES (?,?,?,?,?)""",
                (project_id, stage, i + 1, status, progress),
            )
        conn.commit()
    finally:
        conn.close()


def get_project_stages(project_id: str) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM project_stages WHERE project_id = ? ORDER BY stage_order",
            (project_id,),
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def update_stage(project_id: str, stage_name: str, data: dict):
    if not data:
        return
    conn = get_db()
    try:
        sets = ", ".join(f"{k} = ?" for k in data)
        vals = list(data.values()) + [project_id, stage_name]
        conn.execute(
            f"UPDATE project_stages SET {sets} WHERE project_id = ? AND stage_name = ?",
            vals,
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Landowners
# ---------------------------------------------------------------------------
def create_landowner(data: dict) -> str:
    conn = get_db()
    try:
        conn.execute(
            """INSERT OR IGNORE INTO landowners
               (landowner_id, name, village, district, state, phone,
                parcel_id, project_id, land_area_sqm,
                acquisition_status, compensation_status, compensation_amount,
                legal_status, documentation_status, survey_status,
                verification_status, assigned_officer_id, citizen_user_id)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data["landowner_id"], data["name"],
                data.get("village"), data.get("district"), data.get("state"),
                data.get("phone"), data.get("parcel_id"),
                data.get("project_id"), data.get("land_area_sqm"),
                data.get("acquisition_status", "Pending"),
                data.get("compensation_status", "Pending"),
                data.get("compensation_amount"),
                data.get("legal_status", "Clear"),
                data.get("documentation_status", "Pending"),
                data.get("survey_status", "Pending"),
                data.get("verification_status", "Pending"),
                data.get("assigned_officer_id"),
                data.get("citizen_user_id"),
            ),
        )
        conn.commit()
        return data["landowner_id"]
    finally:
        conn.close()


def get_landowners_for_project(project_id: str) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM landowners WHERE project_id = ? ORDER BY landowner_id",
            (project_id,),
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_landowner(landowner_id: str) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM landowners WHERE landowner_id = ?", (landowner_id,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def get_landowner_by_parcel(parcel_id: str) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM landowners WHERE parcel_id = ?", (parcel_id,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


def get_landowners_for_citizen(citizen_user_id: int) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM landowners WHERE citizen_user_id = ?", (citizen_user_id,)
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def update_landowner(landowner_id: str, data: dict):
    if not data:
        return
    conn = get_db()
    try:
        sets = ", ".join(f"{k} = ?" for k in data)
        vals = list(data.values()) + [landowner_id]
        conn.execute(f"UPDATE landowners SET {sets} WHERE landowner_id = ?", vals)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------
def create_assignment(data: dict) -> int:
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO assignments
               (officer_id, project_id, stage_name, role_in_project,
                priority, deadline, status, assigned_by, notes)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                data["officer_id"], data["project_id"],
                data.get("stage_name"), data.get("role_in_project"),
                data.get("priority", "MEDIUM"), data.get("deadline"),
                data.get("status", "Active"), data.get("assigned_by"),
                data.get("notes"),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_assignments_for_officer(officer_id: int) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT a.*, p.project_name, p.state, p.district,
                      p.current_stage, p.progress_pct, p.priority as proj_priority
               FROM assignments a
               JOIN projects p ON p.project_id = a.project_id
               WHERE a.officer_id = ? ORDER BY a.assigned_at DESC""",
            (officer_id,),
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_assignments_for_project(project_id: str) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT a.*, u.name as officer_name, u.designation, u.department
               FROM assignments a
               JOIN users u ON u.id = a.officer_id
               WHERE a.project_id = ? ORDER BY a.assigned_at DESC""",
            (project_id,),
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def update_assignment(assignment_id: int, data: dict):
    if not data:
        return
    conn = get_db()
    try:
        sets = ", ".join(f"{k} = ?" for k in data)
        vals = list(data.values()) + [assignment_id]
        conn.execute(f"UPDATE assignments SET {sets} WHERE id = ?", vals)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
def create_alert(data: dict) -> int:
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO alerts
               (alert_type, severity, title, message, project_id, stage_name,
                source, sender_id, recipient_id, recipient_role,
                recommended_action)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                data["alert_type"], data["severity"],
                data["title"], data["message"],
                data.get("project_id"), data.get("stage_name"),
                data.get("source", "system"), data.get("sender_id"),
                data.get("recipient_id"), data.get("recipient_role"),
                data.get("recommended_action"),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_alerts_for_user(user_id: int, role: str = None, limit: int = 50) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT * FROM alerts
               WHERE recipient_id = ? OR recipient_role = ?
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, role, limit),
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_all_alerts(limit: int = 100) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def mark_alert_read(alert_id: int):
    conn = get_db()
    try:
        conn.execute("UPDATE alerts SET is_read = 1 WHERE id = ?", (alert_id,))
        conn.commit()
    finally:
        conn.close()


def get_unread_alert_count(user_id: int, role: str = None) -> int:
    conn = get_db()
    try:
        row = conn.execute(
            """SELECT COUNT(*) FROM alerts
               WHERE (recipient_id = ? OR recipient_role = ?) AND is_read = 0""",
            (user_id, role),
        ).fetchone()
        return row[0]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------
def create_issue(data: dict) -> int:
    conn = get_db()
    try:
        cur = conn.execute(
            """INSERT INTO issues
               (project_id, landowner_id, issue_type, status, severity,
                title, description, assigned_to)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                data["project_id"], data.get("landowner_id"),
                data["issue_type"], data.get("status", "Open"),
                data.get("severity", "MEDIUM"),
                data["title"], data.get("description"),
                data.get("assigned_to"),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_issues_for_project(project_id: str) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM issues WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_issues_for_landowner(landowner_id: str) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM issues WHERE landowner_id = ? ORDER BY created_at DESC",
            (landowner_id,),
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_all_issues(status: str = None) -> list[dict]:
    conn = get_db()
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM issues WHERE status = ? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM issues ORDER BY created_at DESC"
            ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def update_issue(issue_id: int, data: dict):
    if not data:
        return
    conn = get_db()
    try:
        sets = ", ".join(f"{k} = ?" for k in data)
        vals = list(data.values()) + [issue_id]
        conn.execute(f"UPDATE issues SET {sets} WHERE id = ?", vals)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Activity Log
# ---------------------------------------------------------------------------
def log_activity(
    action: str, entity_type: str = None, entity_id: str = None,
    project_id: str = None, user_id: int = None, user_name: str = None,
    details: str = None,
):
    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO activity_log
               (action, entity_type, entity_id, project_id,
                user_id, user_name, details)
               VALUES (?,?,?,?,?,?,?)""",
            (action, entity_type, entity_id, project_id,
             user_id, user_name, details),
        )
        conn.commit()
    finally:
        conn.close()


def get_activity_log(project_id: str = None, limit: int = 100) -> list[dict]:
    conn = get_db()
    try:
        if project_id:
            rows = conn.execute(
                "SELECT * FROM activity_log WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
                (project_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM activity_log ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Aggregate queries (for analytics)
# ---------------------------------------------------------------------------
def get_projects_by_state() -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT state, COUNT(*) as count,
                      AVG(progress_pct) as avg_progress
               FROM projects GROUP BY state ORDER BY count DESC"""
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_projects_by_type() -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT project_type, COUNT(*) as count
               FROM projects GROUP BY project_type ORDER BY count DESC"""
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_projects_by_status() -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT project_status, COUNT(*) as count
               FROM projects GROUP BY project_status"""
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_stage_distribution() -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT current_stage, COUNT(*) as count
               FROM projects GROUP BY current_stage ORDER BY count DESC"""
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_officer_workload() -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT u.id, u.name, u.designation, u.department,
                      COUNT(DISTINCT a.project_id) as project_count,
                      COUNT(a.id) as assignment_count,
                      SUM(CASE WHEN a.status='Active' THEN 1 ELSE 0 END) as active_count
               FROM users u
               LEFT JOIN assignments a ON a.officer_id = u.id
               WHERE u.role = 'employee' AND u.is_active = 1
               GROUP BY u.id ORDER BY project_count DESC"""
        ).fetchall()
        return _rows_to_list(rows)
    finally:
        conn.close()


def get_issue_stats() -> dict:
    conn = get_db()
    try:
        total = conn.execute("SELECT COUNT(*) FROM issues").fetchone()[0]
        open_count = conn.execute(
            "SELECT COUNT(*) FROM issues WHERE status IN ('Open','Under Review','In Progress')"
        ).fetchone()[0]
        by_type = conn.execute(
            "SELECT issue_type, COUNT(*) as count FROM issues GROUP BY issue_type"
        ).fetchall()
        return {
            "total": total,
            "open": open_count,
            "resolved": total - open_count,
            "by_type": {r["issue_type"]: r["count"] for r in by_type},
        }
    finally:
        conn.close()


def db_exists() -> bool:
    """Check if the database file exists and has the projects table populated."""
    if not DB_PATH.exists():
        return False
    try:
        conn = get_db()
        count = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False
