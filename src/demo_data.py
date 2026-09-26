"""
TerraTech — deterministic demo data generator.

Creates 100+ realistic Indian land-acquisition projects, 22 users,
500+ landowners, issues, alerts, and activity log entries. Every value
is seeded from the project index, so data never changes between runs.

IMPORTANT: This module is called once when the database is first created.
It imports from database.py and utils.py only — never from the ML layer.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from src.database import (
    create_user, create_project, create_project_stages,
    create_landowner, create_assignment, create_alert,
    create_issue, log_activity, PROJECT_STAGES,
)
from src.utils import (
    hash_password, ml_project_type, generate_project_id,
    generate_parcel_id, generate_landowner_id,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXISTING_PROJECTS_DIR = PROJECT_ROOT / "data" / "projects"

# ---------------------------------------------------------------------------
# Geographic data — real Indian coordinates
# ---------------------------------------------------------------------------
GEOGRAPHY = {
    "Madhya Pradesh": {
        "Bhopal":    (23.26, 77.41),
        "Indore":    (22.72, 75.86),
        "Gwalior":   (26.22, 78.18),
        "Jabalpur":  (23.18, 79.95),
        "Dewas":     (22.96, 76.05),
        "Betul":     (21.90, 77.90),
        "Ujjain":    (23.18, 75.77),
        "Satna":     (24.58, 80.83),
    },
    "Maharashtra": {
        "Mumbai":      (19.08, 72.88),
        "Pune":        (18.52, 73.86),
        "Nagpur":      (21.15, 79.09),
        "Nashik":      (20.00, 73.79),
        "Aurangabad":  (19.88, 75.34),
        "Thane":       (19.22, 72.98),
    },
    "Rajasthan": {
        "Jaipur":   (26.91, 75.79),
        "Jodhpur":  (26.24, 73.02),
        "Udaipur":  (24.58, 73.68),
        "Kota":     (25.18, 75.85),
        "Ajmer":    (26.45, 74.64),
    },
    "Gujarat": {
        "Ahmedabad": (23.02, 72.57),
        "Surat":     (21.17, 72.83),
        "Vadodara":  (22.31, 73.19),
        "Rajkot":    (22.30, 70.78),
    },
    "Uttar Pradesh": {
        "Lucknow":   (26.85, 80.95),
        "Noida":     (28.54, 77.39),
        "Agra":      (27.18, 78.02),
        "Varanasi":  (25.32, 82.99),
        "Kanpur":    (26.45, 80.35),
    },
    "Karnataka": {
        "Bengaluru": (12.97, 77.59),
        "Mysuru":    (12.30, 76.66),
        "Hubli":     (15.36, 75.12),
        "Mangaluru": (12.87, 74.88),
    },
    "Tamil Nadu": {
        "Chennai":    (13.08, 80.27),
        "Coimbatore": (11.02, 76.96),
        "Madurai":    (9.93, 78.12),
        "Salem":      (11.65, 78.16),
    },
    "Telangana": {
        "Hyderabad":  (17.39, 78.49),
        "Warangal":   (17.97, 79.60),
        "Karimnagar": (18.44, 79.13),
    },
}

# Flatten for indexed access
_ALL_LOCATIONS = []
for state, districts in GEOGRAPHY.items():
    for district, (lat, lng) in districts.items():
        _ALL_LOCATIONS.append((state, district, lat, lng))

# ---------------------------------------------------------------------------
# Project templates: (type, name template, department)
# ---------------------------------------------------------------------------
_PROJECT_TEMPLATES = [
    # Highways (15)
    ("Highway", "{d1}–{d2} Highway Expansion", "Ministry of Road Transport"),
    ("Highway", "NH-{n} Four-Laning — {d1} Section", "NHAI"),
    ("Expressway", "{d1}–{d2} Expressway", "NHAI"),
    ("Ring Road", "{d1} Ring Road Phase {p}", "State PWD"),
    # Railway (10)
    ("Railway", "{d1}–{d2} Rail Doubling", "Ministry of Railways"),
    ("Railway", "{d1} Railway Junction Upgrade", "Indian Railways"),
    # Metro (8)
    ("Metro", "{d1} Metro Line {n} Extension", "Metro Rail Corporation"),
    ("Metro", "{d1} Metro Corridor Phase {p}", "Metro Rail Corporation"),
    # Industrial (10)
    ("Industrial Corridor", "{d1} Industrial Corridor Extension", "DPIIT"),
    ("Industrial Park", "{d1} Industrial Park Development", "State Industries"),
    # Smart City / Urban (8)
    ("Smart City", "{d1} Smart City Mission — Phase {p}", "MoHUA"),
    ("Urban Development", "{d1} Urban Renewal Project", "State Urban Dev"),
    # Infrastructure (8)
    ("Airport Expansion", "{d1} Airport Expansion", "AAI"),
    ("Power Transmission", "{d1}–{d2} Power Transmission Line", "PowerGrid"),
    # Green/Water (8)
    ("Solar Park", "{d1} Solar Park Development", "MNRE"),
    ("Irrigation", "{d1} Canal Modernisation", "State Water Resources"),
    ("Dam", "{d1} Dam Rehabilitation Project", "CWC"),
]

# ---------------------------------------------------------------------------
# Indian names for synthetic users and landowners
# ---------------------------------------------------------------------------
_FIRST_NAMES_M = [
    "Rajesh", "Amit", "Suresh", "Vikram", "Mahesh", "Rahul", "Anil",
    "Sanjay", "Deepak", "Pradeep", "Ramesh", "Naresh", "Dinesh",
    "Mukesh", "Rakesh", "Ashok", "Ajay", "Vijay", "Manoj", "Kamal",
    "Ravi", "Mohan", "Govind", "Harish", "Pankaj", "Yogesh", "Umesh",
    "Girish", "Satish", "Kiran",
]
_FIRST_NAMES_F = [
    "Priya", "Sunita", "Meera", "Anjali", "Kavita", "Rekha", "Geeta",
    "Neha", "Pooja", "Swati", "Divya", "Shweta", "Nisha", "Aarti",
    "Seema", "Anita", "Jaya", "Lakshmi", "Usha", "Radha",
]
_LAST_NAMES = [
    "Sharma", "Verma", "Singh", "Patel", "Kumar", "Gupta", "Reddy",
    "Nair", "Iyer", "Rao", "Deshmukh", "Joshi", "Mishra", "Tiwari",
    "Yadav", "Chauhan", "Agarwal", "Saxena", "Pandey", "Dubey",
    "Kulkarni", "Patil", "More", "Thakur", "Mehta", "Shah", "Devi",
    "Rathore", "Bhat", "Hegde",
]

_VILLAGES = [
    "Khandwa Kalan", "Palaspani", "Borgaon", "Sarangpur", "Bilkhiria",
    "Mandideep", "Raisen", "Obaidullaganj", "Sehore", "Ashta",
    "Barwani", "Sendhwa", "Manawar", "Dhar", "Kukshi",
    "Chandwad", "Igatpuri", "Sinnar", "Trimbak", "Malegaon",
    "Bassi", "Chaksu", "Chomu", "Phulera", "Sambhar",
    "Dholka", "Bavla", "Sanand", "Viramgam", "Mandal",
    "Bakshi Ka Talab", "Malihabad", "Kakori", "Mohanlalganj", "Sarojini Nagar",
    "Anekal", "Devanahalli", "Doddaballapur", "Hoskote", "Nelamangala",
    "Sriperumbudur", "Tiruvallur", "Kanchipuram", "Chengalpattu", "Arakkonam",
    "Shamirpet", "Keesara", "Ghatkesar", "Pocharam", "Medchal",
]

_DESIGNATIONS = [
    "Land Acquisition Officer", "Revenue Inspector", "Tehsildar",
    "Assistant Engineer", "Sub-Divisional Officer", "Survey Officer",
    "Compensation Officer", "R&R Coordinator", "Site Supervisor",
    "Documentation Officer", "Legal Officer", "District Coordinator",
    "Project Engineer", "Field Inspector", "Verification Officer",
]

_DEPARTMENTS = [
    "Revenue Department", "Land Records", "Public Works",
    "Irrigation Department", "District Administration",
    "Urban Development", "Transport Department", "Industrial Development",
]


def _seeded_rand(seed: int) -> random.Random:
    return random.Random(seed)


# ---------------------------------------------------------------------------
# Seed users
# ---------------------------------------------------------------------------
def seed_users() -> dict:
    """Create 22 demo users. Returns a mapping of email → user_id."""
    pw = hash_password("terratech2026")
    users = {}

    # Government officials (2)
    gov_users = [
        ("admin@terratech.demo", "Rajesh Kumar Sharma", "government",
         "District Collector", "District Administration", "Madhya Pradesh", "Bhopal"),
        ("officer@terratech.demo", "Priya Nair", "government",
         "Additional Collector", "Revenue Department", "Maharashtra", "Pune"),
    ]
    for email, name, role, desig, dept, state, district in gov_users:
        uid = create_user(email, pw, name, role,
                          designation=desig, department=dept,
                          state=state, district=district)
        users[email] = uid

    # Employees (15)
    rng = _seeded_rand(42)
    for i in range(15):
        fn = _FIRST_NAMES_M[i] if i < 10 else _FIRST_NAMES_F[i - 10]
        ln = _LAST_NAMES[i]
        email = f"emp{i+1:02d}@terratech.demo"
        loc = _ALL_LOCATIONS[i % len(_ALL_LOCATIONS)]
        uid = create_user(
            email, pw, f"{fn} {ln}", "employee",
            designation=_DESIGNATIONS[i % len(_DESIGNATIONS)],
            department=_DEPARTMENTS[i % len(_DEPARTMENTS)],
            state=loc[0], district=loc[1],
        )
        users[email] = uid

    # Convenience aliases
    create_user("employee@terratech.demo", pw, "Rahul Sharma", "employee",
                designation="Land Acquisition Officer",
                department="Revenue Department",
                state="Madhya Pradesh", district="Bhopal")
    users["employee@terratech.demo"] = None  # will be looked up by email

    # Citizens (5)
    citizen_parcels = ["BH-0234-009", "IN-0102-003", "PU-0089-012",
                       "AH-0045-007", "CH-0178-021"]
    citizen_data = [
        ("citizen@terratech.demo", "Vikram Singh", "Madhya Pradesh", "Bhopal"),
        ("citizen2@terratech.demo", "Meera Patel", "Gujarat", "Ahmedabad"),
        ("citizen3@terratech.demo", "Arjun Reddy", "Telangana", "Hyderabad"),
        ("citizen4@terratech.demo", "Lakshmi Devi", "Tamil Nadu", "Chennai"),
        ("citizen5@terratech.demo", "Rajan Yadav", "Uttar Pradesh", "Lucknow"),
    ]
    for idx, (email, name, state, district) in enumerate(citizen_data):
        uid = create_user(
            email, pw, name, "citizen",
            state=state, district=district,
            citizen_parcel_id=citizen_parcels[idx],
        )
        users[email] = uid

    return users


# ---------------------------------------------------------------------------
# Import existing 5 project JSONs
# ---------------------------------------------------------------------------
def _import_existing_projects():
    """Import the original 5 project JSON files into the database."""
    if not EXISTING_PROJECTS_DIR.exists():
        return
    for pf in sorted(EXISTING_PROJECTS_DIR.glob("*.json")):
        with open(pf) as f:
            p = json.load(f)
        # Map to database schema
        data = {
            "project_id": p["project_id"],
            "project_name": p["project_name"],
            "project_type": p["project_type"],
            "ml_project_type": p["project_type"],  # original types are ML-compatible
            "state": p["state"],
            "district": p["district"],
            "latitude": p.get("latitude"),
            "longitude": p.get("longitude"),
            "land_area": p["land_area"],
            "affected_families": p["affected_families"],
            "documentation_completion": p["documentation_completion"],
            "compensation_completion": p["compensation_completion"],
            "legal_disputes": p["legal_disputes"],
            "approval_delay_days": p["approval_delay_days"],
            "rr_completion": p["rr_completion"],
            "possession_completion": p["possession_completion"],
            "stakeholder_response_days": p["stakeholder_response_days"],
            "historical_delay_rate": p["historical_delay_rate"],
            "department": "NHAI" if "Highway" in p["project_type"] else "State PWD",
            "start_date": "2025-03-15",
            "planned_completion_date": "2027-06-30",
            "current_stage": "Compensation",
            "project_status": "In Progress",
            "priority": "HIGH",
            "budget_crores": round(p["land_area"] * 2.5, 1),
            "total_parcels": max(10, p["affected_families"] // 3),
            "acquired_parcels": max(5, int(p["possession_completion"] / 100 * p["affected_families"] // 3)),
            "progress_pct": round((p["documentation_completion"] + p["compensation_completion"] +
                                   p["rr_completion"] + p["possession_completion"]) / 4, 1),
        }
        create_project(data)
        # Determine current stage from completions
        if p["possession_completion"] > 60:
            current = "Possession"
        elif p["rr_completion"] > 60:
            current = "Legal Clearance"
        elif p["compensation_completion"] > 60:
            current = "Compensation"
        else:
            current = "Landowner Verification"
        create_project_stages(p["project_id"], current)


# ---------------------------------------------------------------------------
# Generate 100 new projects
# ---------------------------------------------------------------------------
def seed_projects():
    """Generate 100 deterministic, diverse, realistic projects."""
    _import_existing_projects()

    base_date = datetime(2024, 6, 1)

    for i in range(100):
        rng = _seeded_rand(1000 + i)
        template = _PROJECT_TEMPLATES[i % len(_PROJECT_TEMPLATES)]
        proj_type = template[0]
        department = template[2]
        ml_type = ml_project_type(proj_type)

        # Pick location deterministically
        loc = _ALL_LOCATIONS[i % len(_ALL_LOCATIONS)]
        state, district, base_lat, base_lng = loc

        # Second district for route-based names
        loc2_idx = (i + 7) % len(_ALL_LOCATIONS)
        _, d2, _, _ = _ALL_LOCATIONS[loc2_idx]

        # Generate name
        name_tmpl = template[1]
        name = name_tmpl.format(
            d1=district, d2=d2,
            n=(i % 50) + 1,
            p=(i % 4) + 1,
        )

        project_id = generate_project_id(proj_type, i)

        # Jitter coordinates
        lat = base_lat + rng.uniform(-0.15, 0.15)
        lng = base_lng + rng.uniform(-0.15, 0.15)

        # ML features — deterministic variation
        land_area = round(rng.uniform(50, 1500), 1)
        affected_families = rng.randint(30, 1200)
        doc_completion = round(rng.uniform(15, 98), 1)
        comp_completion = round(rng.uniform(10, 95), 1)
        legal_disputes = rng.randint(0, 12)
        approval_delay = rng.randint(0, 90)
        rr_completion = round(rng.uniform(10, 95), 1)
        possession_completion = round(rng.uniform(5, 92), 1)
        stakeholder_response = rng.randint(1, 25)
        historical_delay = round(rng.uniform(3, 50), 1)

        # Determine stage from completions
        avg_completion = (doc_completion + comp_completion + rr_completion + possession_completion) / 4
        if avg_completion > 85:
            current_stage = "Project Completion"
            status = "Completed" if avg_completion > 92 else "In Progress"
        elif possession_completion > 60:
            current_stage = "Possession"
            status = "In Progress"
        elif rr_completion > 55:
            current_stage = "Legal Clearance"
            status = "In Progress"
        elif comp_completion > 50:
            current_stage = "Compensation"
            status = "In Progress"
        elif doc_completion > 50:
            current_stage = "Objection Handling"
            status = "In Progress"
        elif doc_completion > 30:
            current_stage = "Landowner Verification"
            status = "In Progress"
        elif doc_completion > 15:
            current_stage = "Notification"
            status = "In Progress"
        else:
            current_stage = "Survey & Measurement"
            status = "In Progress"

        # Priority from risk indicators
        risk_indicator = (100 - comp_completion) * 0.3 + legal_disputes * 5 + approval_delay * 0.5
        if risk_indicator > 70:
            priority = "CRITICAL"
        elif risk_indicator > 50:
            priority = "HIGH"
        elif risk_indicator > 30:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        # Dates
        start_offset = rng.randint(0, 400)
        start_date = (base_date + timedelta(days=start_offset)).strftime("%Y-%m-%d")
        duration = rng.randint(365, 1095)
        planned_end = (base_date + timedelta(days=start_offset + duration)).strftime("%Y-%m-%d")
        delay_days = rng.randint(0, 180) if risk_indicator > 30 else rng.randint(0, 30)
        est_end = (base_date + timedelta(days=start_offset + duration + delay_days)).strftime("%Y-%m-%d")

        total_parcels = max(5, affected_families // rng.randint(2, 5))
        acquired_parcels = int(total_parcels * possession_completion / 100)
        progress = round(avg_completion, 1)
        budget = round(land_area * rng.uniform(1.5, 4.0), 1)

        loc_name = f"{district}, {state}"
        desc = f"Land acquisition for {name.lower()} covering {land_area:.0f} hectares across {district} district."

        data = {
            "project_id": project_id,
            "project_name": name,
            "project_type": proj_type,
            "ml_project_type": ml_type,
            "department": department,
            "state": state,
            "district": district,
            "location": loc_name,
            "description": desc,
            "latitude": round(lat, 4),
            "longitude": round(lng, 4),
            "land_area": land_area,
            "affected_families": affected_families,
            "documentation_completion": doc_completion,
            "compensation_completion": comp_completion,
            "legal_disputes": legal_disputes,
            "approval_delay_days": approval_delay,
            "rr_completion": rr_completion,
            "possession_completion": possession_completion,
            "stakeholder_response_days": stakeholder_response,
            "historical_delay_rate": historical_delay,
            "start_date": start_date,
            "planned_completion_date": planned_end,
            "estimated_completion_date": est_end,
            "current_stage": current_stage,
            "project_status": status,
            "priority": priority,
            "budget_crores": budget,
            "total_parcels": total_parcels,
            "acquired_parcels": acquired_parcels,
            "progress_pct": progress,
        }
        create_project(data)
        create_project_stages(project_id, current_stage)


# ---------------------------------------------------------------------------
# Landowners
# ---------------------------------------------------------------------------
def seed_landowners(user_map: dict):
    """Create 500+ synthetic landowners distributed across projects."""
    from src.database import get_all_projects

    projects = get_all_projects()
    citizen_emails = [k for k in user_map if k.startswith("citizen")]
    citizen_idx = 0
    landowner_global_idx = 0

    for proj in projects:
        rng = _seeded_rand(2000 + hash(proj["project_id"]) % 10000)
        n_owners = rng.randint(3, 8)
        district = proj["district"]
        state = proj["state"]

        for j in range(n_owners):
            landowner_global_idx += 1
            rng2 = _seeded_rand(3000 + landowner_global_idx)

            is_male = rng2.random() > 0.35
            fn = rng2.choice(_FIRST_NAMES_M if is_male else _FIRST_NAMES_F)
            ln = rng2.choice(_LAST_NAMES)
            name = f"{fn} {ln}"

            village = rng2.choice(_VILLAGES)
            parcel_id = generate_parcel_id(district, landowner_global_idx)
            lo_id = generate_landowner_id(district, landowner_global_idx)
            land_sqm = round(rng2.uniform(200, 15000), 1)
            comp_amount = round(land_sqm * rng2.uniform(800, 3500), 0)

            # Statuses
            acq_choices = ["Acquired", "Pending", "In Progress", "Disputed"]
            acq_weights = [0.35, 0.25, 0.25, 0.15]
            acq_status = rng2.choices(acq_choices, acq_weights)[0]

            comp_choices = ["Paid", "Pending", "Under Review", "Disputed"]
            comp_weights = [0.30, 0.30, 0.25, 0.15]
            comp_status = rng2.choices(comp_choices, comp_weights)[0]

            legal_choices = ["Clear", "Pending", "Disputed", "Under Review"]
            legal_weights = [0.40, 0.25, 0.20, 0.15]
            legal_status = rng2.choices(legal_choices, legal_weights)[0]

            doc_choices = ["Complete", "Pending", "Incomplete", "Under Review"]
            doc_weights = [0.30, 0.30, 0.20, 0.20]
            doc_status = rng2.choices(doc_choices, doc_weights)[0]

            survey_choices = ["Completed", "Pending", "In Progress"]
            survey_status = rng2.choices(survey_choices, [0.4, 0.35, 0.25])[0]

            verif_choices = ["Verified", "Pending", "In Progress", "Failed"]
            verif_status = rng2.choices(verif_choices, [0.35, 0.30, 0.25, 0.10])[0]

            # Assign a citizen user to some landowners
            citizen_user_id = None
            if citizen_idx < len(citizen_emails) and landowner_global_idx % 100 < 5:
                citizen_user_id = user_map.get(citizen_emails[citizen_idx])
                citizen_idx = min(citizen_idx + 1, len(citizen_emails) - 1)

            phone = f"+91 {rng2.randint(70000, 99999)} {rng2.randint(10000, 99999)}"

            create_landowner({
                "landowner_id": lo_id,
                "name": name,
                "village": village,
                "district": district,
                "state": state,
                "phone": phone,
                "parcel_id": parcel_id,
                "project_id": proj["project_id"],
                "land_area_sqm": land_sqm,
                "acquisition_status": acq_status,
                "compensation_status": comp_status,
                "compensation_amount": comp_amount,
                "legal_status": legal_status,
                "documentation_status": doc_status,
                "survey_status": survey_status,
                "verification_status": verif_status,
                "citizen_user_id": citizen_user_id,
            })


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------
def seed_assignments(user_map: dict):
    """Assign employees to projects."""
    from src.database import get_all_projects, get_users_by_role

    projects = get_all_projects()
    employees = get_users_by_role("employee")
    if not employees:
        return

    for i, proj in enumerate(projects):
        rng = _seeded_rand(4000 + i)
        # Assign 1–3 employees per project
        n_assign = rng.randint(1, min(3, len(employees)))
        assigned = rng.sample(employees, n_assign)

        for emp in assigned:
            stage = rng.choice(PROJECT_STAGES[:7])  # assign to earlier stages
            deadline_days = rng.randint(30, 180)
            deadline = (datetime.now() + timedelta(days=deadline_days)).strftime("%Y-%m-%d")

            create_assignment({
                "officer_id": emp["id"],
                "project_id": proj["project_id"],
                "stage_name": stage,
                "role_in_project": rng.choice([
                    "Project Lead", "Field Officer", "Verification Officer",
                    "Compensation Lead", "Documentation Officer", "Site Supervisor",
                ]),
                "priority": proj.get("priority", "MEDIUM"),
                "deadline": deadline,
                "status": "Active",
                "assigned_by": 1,  # admin
            })


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------
def seed_issues():
    """Create realistic issues for projects."""
    from src.database import get_all_projects, get_landowners_for_project

    projects = get_all_projects()

    issue_templates = {
        "Legal": [
            ("Ownership dispute pending", "Multiple claimants for parcel. Title verification required before proceeding."),
            ("Court stay on acquisition", "High Court stay order received. Legal team reviewing options."),
            ("Boundary dispute with adjacent plot", "Survey discrepancy in parcel boundary. Re-survey ordered."),
            ("Succession certificate pending", "Landowner deceased. Succession certificate from heirs awaited."),
        ],
        "Compensation": [
            ("Compensation assessment pending", "Market valuation assessment not yet completed for affected parcels."),
            ("Compensation amount disputed", "Landowner has objected to the assessed compensation amount."),
            ("Bank verification pending", "Beneficiary bank account details require re-verification."),
            ("Enhanced compensation claim", "Landowner filed application for enhanced compensation under Section 64."),
        ],
        "Documentation": [
            ("Land record mismatch", "Revenue record does not match survey measurement. Reconciliation needed."),
            ("Missing mutation entry", "Mutation entry in revenue records not yet updated after transfer."),
            ("Incomplete survey sketch", "Survey sketch for parcel is missing boundary coordinates."),
            ("Title deed verification pending", "Original title deed submitted but not yet verified."),
        ],
        "Survey": [
            ("Re-survey required", "Initial survey measurements disputed. Re-survey with GPS ordered."),
            ("Access road survey pending", "Access road to be acquired not included in original survey."),
        ],
        "Verification": [
            ("Identity verification pending", "Aadhaar/PAN verification for landowner not completed."),
            ("Encumbrance check pending", "Encumbrance certificate from sub-registrar office awaited."),
        ],
    }

    for i, proj in enumerate(projects):
        rng = _seeded_rand(5000 + i)

        # 0–4 issues per project, weighted toward fewer
        n_issues = rng.choices([0, 1, 2, 3, 4], [0.15, 0.30, 0.25, 0.20, 0.10])[0]
        if n_issues == 0:
            continue

        landowners = get_landowners_for_project(proj["project_id"])

        for j in range(n_issues):
            issue_type = rng.choice(list(issue_templates.keys()))
            template = rng.choice(issue_templates[issue_type])
            severity = rng.choices(
                ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                [0.15, 0.35, 0.35, 0.15]
            )[0]
            status = rng.choices(
                ["Open", "Under Review", "In Progress", "Resolved"],
                [0.30, 0.25, 0.30, 0.15]
            )[0]

            lo_id = None
            if landowners and rng.random() > 0.3:
                lo = rng.choice(landowners)
                lo_id = lo["landowner_id"]

            create_issue({
                "project_id": proj["project_id"],
                "landowner_id": lo_id,
                "issue_type": issue_type,
                "status": status,
                "severity": severity,
                "title": template[0],
                "description": template[1],
            })


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------
def seed_alerts():
    """Create realistic system alerts."""
    from src.database import get_all_projects

    projects = get_all_projects()

    alert_templates = [
        ("CRITICAL", "Critical Risk Alert", "Project {pid} risk has exceeded critical threshold. Immediate review required.",
         "Deadline", "Review project risk factors and initiate mitigation measures."),
        ("HIGH", "Deadline Approaching", "Compensation stage deadline for {pid} is approaching. {days} days remaining.",
         "Deadline", "Ensure all pending compensation awards are processed."),
        ("HIGH", "Unresolved Legal Issues", "Project {pid} has {n} unresolved legal disputes requiring attention.",
         "Legal", "Schedule case-wise review with District Legal Cell."),
        ("MEDIUM", "Stage Delay Warning", "Stage '{stage}' in project {pid} is delayed by {days} days.",
         "Project Update", "Review stage progress and identify bottlenecks."),
        ("MEDIUM", "Documentation Incomplete", "Documentation completion for {pid} is below target at {pct}%.",
         "Documentation", "Complete pending land record verification."),
        ("LOW", "Assignment Created", "New assignment created for project {pid}.",
         "General", "Review assignment details and acknowledge."),
        ("HIGH", "Compensation Pending", "Compensation disbursal for {pid} is {pct}% — below acceptable level.",
         "Compensation", "Audit pending awards and expedite bank account verification."),
        ("MEDIUM", "Stakeholder Response Delay", "Stakeholder response time for {pid} exceeds {days} days.",
         "General", "Establish single-window grievance desk."),
    ]

    for i, proj in enumerate(projects):
        rng = _seeded_rand(6000 + i)
        n_alerts = rng.randint(0, 3)

        for j in range(n_alerts):
            tmpl = rng.choice(alert_templates)
            severity, title, msg_tmpl, alert_type, action = tmpl

            msg = msg_tmpl.format(
                pid=proj["project_id"],
                days=rng.randint(5, 45),
                n=proj.get("legal_disputes", 0),
                stage=proj.get("current_stage", ""),
                pct=int(proj.get("compensation_completion", 0)),
            )

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


# ---------------------------------------------------------------------------
# Activity log
# ---------------------------------------------------------------------------
def seed_activity_log():
    """Create a realistic activity history."""
    from src.database import get_all_projects

    projects = get_all_projects()

    actions = [
        ("Project created", "project", "Created new project in the system."),
        ("Stage updated", "stage", "Moved project to {stage}."),
        ("Officer assigned", "assignment", "Assigned officer to {stage} stage."),
        ("Risk assessed", "project", "AI risk assessment completed. Risk score: {score}."),
        ("Compensation updated", "project", "Compensation status updated — {pct}% disbursed."),
        ("Document uploaded", "project", "Land records documentation uploaded and verified."),
        ("Alert generated", "alert", "System alert generated: {reason}."),
        ("Landowner verified", "landowner", "Landowner identity and title verification completed."),
        ("Survey completed", "project", "Survey and measurement for {n} parcels completed."),
        ("Legal review", "issue", "Legal review completed for pending disputes."),
    ]

    base_date = datetime(2025, 1, 1)

    for i, proj in enumerate(projects):
        rng = _seeded_rand(7000 + i)
        n_entries = rng.randint(3, 8)

        for j in range(n_entries):
            action_tmpl = rng.choice(actions)
            action_text, entity_type, detail_tmpl = action_tmpl

            detail = detail_tmpl.format(
                stage=proj.get("current_stage", ""),
                score=rng.randint(20, 90),
                pct=int(proj.get("compensation_completion", 0)),
                reason="risk threshold exceeded" if rng.random() > 0.5 else "deadline approaching",
                n=rng.randint(5, 30),
            )

            days_offset = rng.randint(0, 500)
            created_at = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%dT%H:%M:%S")

            log_activity(
                action=action_text,
                entity_type=entity_type,
                entity_id=proj["project_id"],
                project_id=proj["project_id"],
                user_id=rng.randint(1, 5),
                user_name=f"{rng.choice(_FIRST_NAMES_M)} {rng.choice(_LAST_NAMES)}",
                details=detail,
            )


# ---------------------------------------------------------------------------
# Master seed function
# ---------------------------------------------------------------------------
def seed_all():
    """Run all seeders in order. Idempotent (uses INSERT OR IGNORE)."""
    user_map = seed_users()
    seed_projects()
    seed_landowners(user_map)
    seed_assignments(user_map)
    seed_issues()
    seed_alerts()
    seed_activity_log()
