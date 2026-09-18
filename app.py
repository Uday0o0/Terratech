"""
TerraTech — Land Acquisition Risk Intelligence
Smart India Hackathon proof-of-concept | Single-project demonstration

UI LAYER ONLY.

Every ML-derived number on screen comes from src/. Nothing here recomputes,
re-derives or hardcodes a prediction, a SHAP value, a risk band or a
recommendation. This module is responsible for page config, layout, styling,
session state and rendering — nothing else.

Visual reference: terratech-unified-1.html (recreated natively in Streamlit;
no iframe, no embedded page, no government template assets).
"""

import json
from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium

from src.predictor import STAGES, load_artifacts, predict_project
from src.explain import plain_language_explanation
from src.recommendations import generate_recommendations

# ---------------------------------------------------------------------------
# Page configuration — must be the FIRST Streamlit call in the script
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="TerraTech | Land Acquisition Intelligence Platform",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_ROOT = Path(__file__).resolve().parent
DEMO_PROJECT_PATH = PROJECT_ROOT / "data" / "demo_project.json"


# ===========================================================================
# DESIGN TOKENS — taken directly from terratech-unified-1.html
# ===========================================================================
# Brand colours are constant across both themes.
NAVY = "#0F2A3D"
NAVY_DEEP = "#081826"
NAVY_SOFT = "#1B4459"
TEAL = "#1F6F6B"
TEAL_DEEP = "#144F4C"
MARIGOLD = "#E2A83C"
MARIGOLD_DEEP = "#B9821E"
RUST = "#B5502C"
RUST_DEEP = "#8E3A1F"
GREEN = "#3B7A57"

# Surface/ink tokens flip between the HTML's light and dark token sets.
LIGHT_TOKENS = {
    "cream": "#F7F3E8",
    "cream-2": "#EFE7D2",
    "paper": "#FFFDF8",
    "ink": "#1E2A2F",
    "ink-soft": "#5B6A6C",
    "ink-faint": "#8B9B9C",
    "rule": "#E1D8C0",
    "rule-soft": "#ECE4CF",
    "teal-soft": "#E4EFEE",
    "accent-ink": "#144F4C",
}
DARK_TOKENS = {
    "cream": "#0F1815",
    "cream-2": "#16211D",
    "paper": "#131E1A",
    "ink": "#EAE6D7",
    "ink-soft": "#AEBBAF",
    "ink-faint": "#7E8C81",
    "rule": "#28352D",
    "rule-soft": "#20291F",
    "teal-soft": "#132824",
    "accent-ink": "#7FC4BC",
}

# The HTML's three risk bands. Mapped to OUR model's LOW/MEDIUM/HIGH bands,
# which are defined in feature_metadata.joblib and never redefined here.
BAND_HEX = {"LOW": GREEN, "MEDIUM": MARIGOLD, "HIGH": RUST}
BAND_TEXT_HEX = {"LOW": GREEN, "MEDIUM": MARIGOLD_DEEP, "HIGH": RUST}
PRIORITY_HEX = {
    "CRITICAL": RUST,
    "HIGH": RUST_DEEP,
    "MEDIUM": MARIGOLD_DEEP,
    "LOW": GREEN,
}
# Thresholds used purely to colour the stage-risk cards. Presentation only —
# the stage scores themselves come from the rule layer in src/predictor.py.
STAGE_BAND_CUTOFFS = (35.0, 60.0)


def stage_band(score: float) -> str:
    """Colour band for a stage card. Display concern only."""
    low, high = STAGE_BAND_CUTOFFS
    if score >= high:
        return "HIGH"
    if score >= low:
        return "MEDIUM"
    return "LOW"


# ===========================================================================
# STYLESHEET
# ===========================================================================
def build_css(dark: bool) -> str:
    tokens = DARK_TOKENS if dark else LIGHT_TOKENS
    token_lines = "".join(f"--{k}:{v};" for k, v in tokens.items())
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {{
    {token_lines}
    --navy:{NAVY}; --navy-deep:{NAVY_DEEP}; --navy-soft:{NAVY_SOFT};
    --teal:{TEAL}; --teal-deep:{TEAL_DEEP};
    --marigold:{MARIGOLD}; --marigold-deep:{MARIGOLD_DEEP};
    --rust:{RUST}; --rust-deep:{RUST_DEEP}; --green:{GREEN};
    --shadow-sm:0 2px 10px -4px rgba(15,42,61,.14);
    --shadow-md:0 14px 34px -18px rgba(15,42,61,.32);
    --shadow-lg:0 24px 60px -22px rgba(15,42,61,.4);
}}

/* ---------- Base canvas ---------- */
.stApp {{
    background: var(--cream);
    color: var(--ink);
    font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif;
    font-size: 14.5px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
}}
.block-container {{ padding: 1.6rem 2.2rem 5rem; max-width: 1280px; }}
h1, h2, h3 {{ font-family: 'Fraunces', Georgia, serif; font-weight: 600; color: var(--ink) !important; }}
.tt-mono {{ font-family: 'JetBrains Mono', ui-monospace, monospace; }}
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
div[data-testid="stToolbar"] {{ display: none; }}
div[data-testid="stDecoration"] {{ display: none; }}
::selection {{ background: var(--marigold); color: #2A2109; }}

/* ---------- Sidebar: the HTML's dark navy rail ---------- */
section[data-testid="stSidebar"] {{
    background: var(--navy-deep);
    border-right: none;
}}
section[data-testid="stSidebar"] * {{ color: #E7EDEB; }}
section[data-testid="stSidebar"] .block-container {{ padding-top: 1.2rem; }}

.tt-brand {{ display:flex; align-items:center; gap:10px; padding-bottom:16px; border-bottom:1px solid rgba(255,255,255,.1); margin-bottom:18px; }}
.tt-brand-mark {{ width:34px; height:34px; border-radius:9px; background:linear-gradient(135deg,var(--teal),var(--navy)); flex:none; }}
.tt-brand-name {{ font-family:'Fraunces',serif; font-size:19px; font-weight:700; color:#fff !important; line-height:1.1; }}
.tt-brand-role {{ font-size:10.5px; color:#8FA6A0 !important; margin-top:2px; }}

/* Radio rendered as the HTML's side-nav buttons */
section[data-testid="stSidebar"] div[role="radiogroup"] {{ gap:2px; }}
section[data-testid="stSidebar"] div[role="radiogroup"] label {{
    display:flex; align-items:center; gap:10px;
    padding:10px 11px; border-radius:8px; width:100%;
    font-size:13.5px; font-weight:500; color:#C3D0CD !important;
    background:transparent; cursor:pointer;
    transition: background .15s ease, color .15s ease;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{ background:rgba(255,255,255,.06); }}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{ background:rgba(255,255,255,.10); }}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {{ color:#fff !important; font-weight:600; }}
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {{ display:none; }}
section[data-testid="stSidebar"] div[role="radiogroup"] p {{ font-size:13.5px; }}

.tt-side-label {{
    font-size:10.5px; font-weight:700; color:#7E9490 !important;
    letter-spacing:.06em; margin:22px 0 8px; padding-top:14px;
    border-top:1px solid rgba(255,255,255,.1);
}}
.tt-param-row {{ display:flex; justify-content:space-between; align-items:baseline; gap:10px; padding:6px 0; border-bottom:1px dashed rgba(255,255,255,.10); }}
.tt-param-row span {{ font-size:11.5px; color:#9FB2AD !important; }}
.tt-param-row b {{ font-family:'JetBrains Mono',monospace; font-size:11.5px; font-weight:500; color:#F0DFB4 !important; }}
.tt-side-foot {{ font-size:10.5px; color:#7E9490 !important; border-top:1px solid rgba(255,255,255,.1); padding-top:12px; margin-top:18px; }}

/* Sidebar button = the HTML's rust primary action */
section[data-testid="stSidebar"] .stButton > button {{
    width:100%; background:var(--rust); color:#fff !important; border:none;
    border-radius:12px; padding:12px 20px; font-weight:700; font-size:13.5px;
    box-shadow:var(--shadow-sm); transition: background .15s ease, transform .1s ease;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{ background:var(--rust-deep); }}
section[data-testid="stSidebar"] .stButton > button:active {{ transform:scale(.97); }}

/* ---------- Sidebar collapse / expand control ---------- */
/* Collapsed: the control sits over the cream canvas, so it needs its own
   card treatment — otherwise it inherits white-on-cream and disappears. */
[data-testid="stSidebarCollapsedControl"] {{ z-index: 60; }}
[data-testid="stSidebarCollapsedControl"] button {{
    background: var(--paper) !important;
    border: 1px solid var(--rule) !important;
    border-radius: 10px;
    width: 38px; height: 38px;
    color: var(--ink) !important;
    box-shadow: var(--shadow-sm);
    transition: background .15s ease, color .15s ease;
}}
[data-testid="stSidebarCollapsedControl"] button:hover {{
    background: var(--cream-2) !important;
    color: var(--rust) !important;
}}
[data-testid="stSidebarCollapsedControl"] button svg {{ fill: currentColor; width: 18px; height: 18px; }}

/* Expanded: the control sits on the navy rail. */
[data-testid="stSidebarCollapseButton"] button {{
    background: rgba(255,255,255,.08) !important;
    border: 1px solid rgba(255,255,255,.14) !important;
    border-radius: 8px;
    color: #C3D0CD !important;
    transition: background .15s ease, color .15s ease;
}}
[data-testid="stSidebarCollapseButton"] button:hover {{
    background: rgba(255,255,255,.18) !important;
    color: #fff !important;
}}
[data-testid="stSidebarCollapseButton"] button svg {{ fill: currentColor; }}

/* ---------- Topbar ---------- */
.tt-topbar {{
    display:flex; align-items:center; justify-content:space-between; gap:16px;
    background:var(--paper); border:1px solid var(--rule); border-radius:14px;
    padding:14px 20px; margin-bottom:22px; flex-wrap:wrap;
}}
.tt-greet {{ font-size:15px; font-weight:600; color:var(--ink); }}
.tt-greet-sub {{ font-size:11.5px; color:var(--ink-soft); font-weight:400; margin-top:1px; }}
.tt-pill {{
    display:inline-flex; align-items:center; gap:6px; font-size:11.5px; font-weight:600;
    color:var(--accent-ink); background:var(--teal-soft); border:1px solid var(--rule);
    padding:6px 13px; border-radius:20px;
}}
.tt-avatar {{
    width:38px; height:38px; border-radius:10px; flex:none;
    background:linear-gradient(135deg,var(--marigold),var(--rust)); color:#fff;
    display:flex; align-items:center; justify-content:center; font-weight:700; font-size:14px;
}}

/* ---------- Section headings ---------- */
.tt-section h2 {{ font-size:18px; margin:0; }}
.tt-section p {{ font-size:12.5px; color:var(--ink-soft); margin:3px 0 0 !important; }}
.tt-section {{ margin:26px 0 14px; }}
.tt-section:first-child {{ margin-top:0; }}

/* ---------- Cards ---------- */
.tt-panel {{ background:var(--paper); border:1px solid var(--rule); border-radius:14px; padding:18px; }}
.tt-panel h3 {{ font-size:15px; margin:0 0 12px; }}
.tt-kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:1px; background:var(--rule); border:1px solid var(--rule); border-radius:12px; overflow:hidden; }}
.tt-kpi {{ background:var(--paper); padding:18px; }}
.tt-kpi .num {{ font-family:'Fraunces',serif; font-size:26px; font-weight:700; line-height:1.15; }}
.tt-kpi .lbl {{ font-size:11.5px; color:var(--ink-soft); margin-top:4px; }}

.tt-funnel {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; }}
.tt-stage {{ background:var(--paper); border:1px solid var(--rule); border-radius:12px; padding:14px 12px; }}
.tt-stage .n {{ font-size:11px; color:var(--ink-soft); margin-bottom:6px; }}
.tt-stage .pct {{ font-family:'JetBrains Mono',monospace; font-size:20px; font-weight:600; }}
.tt-stage .barwrap {{ height:5px; background:var(--cream-2); border-radius:3px; margin-top:8px; overflow:hidden; }}
.tt-stage .bar {{ height:100%; border-radius:3px; }}
.tt-stage.crit {{ border-color:var(--rust); box-shadow:0 0 0 3px rgba(181,80,44,.10); }}

.tt-facts div {{ display:flex; justify-content:space-between; gap:12px; padding:7px 0; border-bottom:1px dashed var(--rule); font-size:12.5px; color:var(--ink-soft); }}
.tt-facts div:last-child {{ border-bottom:none; }}
.tt-facts b {{ font-family:'JetBrains Mono',monospace; font-weight:500; color:var(--ink); text-align:right; }}

/* ---------- Dark detail panel (project explanation) ---------- */
.tt-detail {{ background:var(--navy-deep); color:#EAE6D7; border-radius:14px; padding:18px; }}
.tt-detail .pname {{ font-family:'Fraunces',serif; font-size:17px; font-weight:700; color:#fff; }}
.tt-detail .pmeta {{ font-size:11.5px; color:#9AB0AA; margin-top:3px; }}
.tt-gauge-row {{ display:flex; align-items:center; gap:14px; margin:14px 0; flex-wrap:wrap; }}
.tt-metrics-mini {{ display:flex; flex-direction:column; gap:7px; font-size:12px; flex:1; min-width:180px; }}
.tt-metrics-mini div {{ display:flex; justify-content:space-between; gap:10px; border-bottom:1px dashed rgba(255,255,255,.14); padding-bottom:5px; }}
.tt-metrics-mini span {{ color:#9AB0AA; }}
.tt-metrics-mini b {{ font-family:'JetBrains Mono',monospace; color:#F0DFB4; font-weight:500; }}
.tt-drivers-head {{ font-size:11.5px; color:#9AB0AA; margin:4px 0 8px; }}
.tt-driver {{ font-size:11.5px; margin-bottom:9px; }}
.tt-driver .dl {{ display:flex; justify-content:space-between; gap:10px; margin-bottom:4px; color:#D8E2DE; }}
.tt-driver .dl b {{ font-family:'JetBrains Mono',monospace; font-weight:500; }}
.tt-driver .db {{ height:6px; background:rgba(255,255,255,.10); border-radius:3px; overflow:hidden; }}
.tt-driver .db i {{ display:block; height:100%; border-radius:3px; }}

/* ---------- Register table ---------- */
.tt-table {{ width:100%; border-collapse:separate; border-spacing:0; background:var(--paper); border:1px solid var(--rule); border-radius:14px; overflow:hidden; font-size:13px; }}
.tt-table th {{ text-align:left; font-size:11px; font-weight:700; color:var(--ink-soft); padding:12px 14px; background:var(--cream-2); border-bottom:1px solid var(--rule); }}
.tt-table td {{ padding:13px 14px; color:var(--ink); border-bottom:1px solid var(--rule-soft); }}
.tt-table tr:last-child td {{ border-bottom:none; }}
.tt-badge {{ display:inline-flex; align-items:center; gap:6px; font-size:11.5px; font-weight:700; padding:4px 10px; border-radius:20px; background:var(--cream-2); }}
.tt-badge i {{ width:9px; height:9px; border-radius:50%; display:inline-block; }}

/* ---------- Alerts + recommendations ---------- */
.tt-alert {{ display:flex; gap:10px; padding:11px 12px; border-radius:10px; background:var(--cream-2); margin-bottom:8px; }}
.tt-alert .sev {{ width:8px; height:8px; border-radius:50%; margin-top:6px; flex:none; }}
.tt-alert .t {{ font-size:12.5px; line-height:1.45; color:var(--ink); }}
.tt-alert .ts {{ font-size:10.5px; color:var(--ink-faint); margin-top:2px; }}

.tt-rec {{ display:flex; gap:12px; padding:14px; border:1px solid var(--rule); border-radius:12px; background:var(--paper); margin-bottom:10px; }}
.tt-rec .num {{ font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:600; color:var(--ink-faint); flex:none; padding-top:2px; }}
.tt-rec .rf {{ font-size:13.5px; font-weight:600; color:var(--ink); }}
.tt-rec .act {{ font-size:12.5px; color:var(--ink-soft); margin-top:5px; }}
.tt-rec .meta {{ font-size:11.5px; color:var(--ink-faint); margin-top:7px; }}
.tt-prio {{ display:inline-block; font-size:10px; font-weight:800; letter-spacing:.06em; color:#fff; padding:3px 9px; border-radius:6px; margin-right:8px; vertical-align:2px; }}
.tt-confirm {{ display:inline-block; font-size:10px; font-weight:700; color:var(--accent-ink); background:var(--teal-soft); border:1px solid var(--rule); padding:2px 8px; border-radius:6px; margin-left:6px; }}

/* ---------- Notices ---------- */
.tt-note {{ background:var(--teal-soft); border:1px solid var(--rule); border-left:3px solid var(--teal); border-radius:10px; padding:11px 14px; font-size:12px; color:var(--ink-soft); }}
.tt-plain {{ background:var(--cream-2); border-radius:12px; padding:16px 18px; font-size:13.5px; line-height:1.6; color:var(--ink); }}
.tt-empty {{ padding:26px; text-align:center; color:var(--ink-faint); font-size:12.5px; background:var(--paper); border:1px dashed var(--rule); border-radius:12px; }}

/* ---------- Main-area buttons ---------- */
div[data-testid="stMain"] .stButton > button {{
    background:var(--paper); color:var(--ink); border:1.5px solid var(--rule);
    border-radius:12px; padding:9px 18px; font-weight:600; font-size:13px;
}}
div[data-testid="stMain"] .stButton > button:hover {{ border-color:var(--teal); color:var(--ink); }}

/* ---------- Streamlit bordered container = reference card ---------- */
.tt-card-title {{ font-family:'Fraunces',Georgia,serif; font-size:15px; font-weight:600; color:var(--ink); margin-bottom:12px; }}

/* ---------- Map ---------- */
/* Fixed to a hard height (not just min-height) so the component's iframe
   can never leave an oversized empty region below the visible tiles. */
iframe[title="streamlit_folium.st_folium"] {{
    border-radius:10px; border:1px solid var(--rule);
    height:330px !important; max-height:330px !important;
    width:100% !important; overflow:hidden;
}}

/* ---------- Responsive ---------- */
@media (max-width: 900px) {{
    .tt-kpis {{ grid-template-columns:repeat(2,1fr); }}
    .tt-funnel {{ grid-template-columns:repeat(2,1fr); }}
    .block-container {{ padding:1.2rem 1rem 4rem; }}
}}
@media (prefers-reduced-motion: reduce) {{
    * {{ transition:none !important; animation:none !important; }}
}}
</style>
"""


def html(fragment: str) -> None:
    """
    Render an HTML fragment.

    Streamlit's markdown parser stops treating a block as raw HTML the moment
    it hits a blank line, so every fragment is flattened to a single line
    before it is handed over.
    """
    st.markdown(" ".join(fragment.split()), unsafe_allow_html=True)


def section(title: str, subtitle: str) -> None:
    html(f'<div class="tt-section"><h2>{title}</h2><p>{subtitle}</p></div>')


# ===========================================================================
# BACKEND ACCESS — cached, but logic untouched
# ===========================================================================
@st.cache_resource(show_spinner=False)
def cached_artifacts():
    """Load the Block 2 artifacts once per Streamlit process."""
    return load_artifacts()


@st.cache_data(show_spinner=False)
def run_analysis(project_json: str) -> dict:
    """
    Full analysis for one project, cached on the project's JSON.

    Calls the existing backend only. Keyed on a string because the project is
    a plain dict; the backend is deterministic, so caching cannot change a
    result — it only avoids recomputing an identical one.
    """
    project = json.loads(project_json)
    result = predict_project(project)
    return {
        "result": result,
        "explanation": plain_language_explanation(project),
        "recommendations": generate_recommendations(
            project, top_contributors=result["top_contributors"]
        ),
    }


@st.cache_data(show_spinner=False)
def load_demo_project() -> dict:
    with open(DEMO_PROJECT_PATH) as f:
        return json.load(f)


# ===========================================================================
# SVG PIECES — same geometry as the reference HTML
# ===========================================================================
def gauge_svg(score: float, color: str) -> str:
    """Circular risk gauge. Arc maths copied from the reference markup."""
    r = 36.0
    circ = 2 * 3.141592653589793 * r
    offset = circ - (max(0.0, min(score, 100.0)) / 100.0) * circ
    return (
        '<svg viewBox="0 0 88 88" width="88" height="88" role="img" '
        f'aria-label="Risk score {score:.1f} out of 100">'
        f'<circle cx="44" cy="44" r="{r}" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="8"/>'
        f'<circle cx="44" cy="44" r="{r}" fill="none" stroke="{color}" stroke-width="8" '
        f'stroke-linecap="round" stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}" '
        'transform="rotate(-90 44 44)"/>'
        '<text x="44" y="49" text-anchor="middle" font-family="Fraunces,serif" font-size="20" '
        f'font-weight="700" fill="#fff">{score:.0f}</text>'
        "</svg>"
    )


def shap_bar_svg(contributors: list) -> str:
    """
    Diverging SHAP bar chart, drawn in the reference's flat SVG style.

    Widths are proportional to the real log-odds values returned by
    src/explain.py — no rescaling of the underlying numbers.
    """
    if not contributors:
        return '<div class="tt-empty">No contributors returned.</div>'

    w, bar_h, gap, top_pad = 520, 20, 16, 6
    label_w, value_w = 168, 56
    track_w = w - label_w - value_w
    mid = label_w + track_w / 2
    half = track_w / 2
    peak = max(abs(c["shap"]) for c in contributors) or 1.0
    height = top_pad * 2 + len(contributors) * (bar_h + gap) - gap

    rows = [
        f'<line x1="{mid}" y1="{top_pad}" x2="{mid}" y2="{height - top_pad}" '
        'stroke="var(--rule)" stroke-width="1"/>'
    ]
    for i, c in enumerate(contributors):
        y = top_pad + i * (bar_h + gap)
        value = c["shap"]
        bar_w = max(2.0, abs(value) / peak * (half - 8))
        x = mid if value > 0 else mid - bar_w
        color = RUST if value > 0 else GREEN
        label = c["label"] if len(c["label"]) <= 24 else c["label"][:23] + "…"
        rows.append(
            f'<text x="{label_w - 12}" y="{y + bar_h / 2 + 4}" text-anchor="end" font-size="11" '
            f'fill="var(--ink-soft)" font-family="Inter,sans-serif">{label}</text>'
            f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_h}" rx="5" fill="{color}"/>'
            f'<text x="{w - value_w + 8}" y="{y + bar_h / 2 + 4}" font-size="11.5" font-weight="600" '
            f'fill="var(--ink)" font-family="JetBrains Mono,monospace">{value:+.3f}</text>'
        )
    return (
        f'<svg viewBox="0 0 {w} {height}" width="100%" height="{height}" role="img" '
        'aria-label="SHAP contributions to delay risk">' + "".join(rows) + "</svg>"
    )


# ===========================================================================
# SIDEBAR
# ===========================================================================
project = load_demo_project()

PARAMETER_FIELDS = [
    ("Project type", project["project_type"], ""),
    ("Land area", project["land_area"], "ha"),
    ("Affected families", project["affected_families"], ""),
    ("Documentation", project["documentation_completion"], "%"),
    ("Compensation", project["compensation_completion"], "%"),
    ("Legal disputes", project["legal_disputes"], ""),
    ("Approval delay", project["approval_delay_days"], "d"),
    ("R&R completion", project["rr_completion"], "%"),
    ("Possession", project["possession_completion"], "%"),
    ("Stakeholder response", project["stakeholder_response_days"], "d"),
    ("Historical delay rate", project["historical_delay_rate"], "%"),
]

NAV_ITEMS = ["Overview", "Risk map & project", "Alerts & recommendations"]

with st.sidebar:
    html(
        '<div class="tt-brand"><div class="tt-brand-mark"></div>'
        '<div><div class="tt-brand-name">TerraTech</div>'
        '<div class="tt-brand-role">Officer console</div></div></div>'
    )

    nav = st.radio("Navigation", NAV_ITEMS, label_visibility="collapsed", key="nav")

    html('<div class="tt-side-label">Project parameters</div>')
    html(
        "".join(
            f'<div class="tt-param-row"><span>{label}</span>'
            f'<b>{value}{(" " + unit) if unit else ""}</b></div>'
            for label, value, unit in PARAMETER_FIELDS
        )
    )
    st.write("")
    analyze_clicked = st.button("Run risk analysis", use_container_width=True)

    html('<div class="tt-side-label">Display</div>')
    dark_mode = st.toggle("Dark mode", value=False, key="dark_mode")

    html(
        '<div class="tt-side-foot">Synthetic prototype data. '
        "Not a real government record.</div>"
    )

# Stylesheet depends on the toggle, so it is injected after the sidebar runs.
st.markdown(build_css(dark_mode), unsafe_allow_html=True)


# ===========================================================================
# TOPBAR
# ===========================================================================
html(
    '<div class="tt-topbar">'
    '<div><div class="tt-greet">Land acquisition risk intelligence</div>'
    '<div class="tt-greet-sub">Officer command center · '
    f'{project["project_name"]}</div></div>'
    '<div style="display:flex; align-items:center; gap:12px;">'
    '<span class="tt-pill">Prototype · synthetic data</span>'
    '<div class="tt-avatar">T</div></div></div>'
)


# ===========================================================================
# ANALYSIS STATE
# ===========================================================================
if analyze_clicked:
    with st.spinner("Running model inference…"):
        st.session_state["analysis"] = run_analysis(json.dumps(project, sort_keys=True))

if "analysis" not in st.session_state:
    html(
        '<div class="tt-empty">Select <b>Run risk analysis</b> in the sidebar to score '
        f'{project["project_id"]} with the trained model.</div>'
    )
    st.stop()

analysis = st.session_state["analysis"]
result = analysis["result"]
category = result["risk_category"]
band_color = BAND_HEX[category]
contributors = result["top_contributors"]
recommendations = analysis["recommendations"]
metadata = cached_artifacts()["metadata"]


# ===========================================================================
# TAB 1 — OVERVIEW
# ===========================================================================
if nav == NAV_ITEMS[0]:
    html(
        '<div class="tt-kpis">'
        f'<div class="tt-kpi"><div class="num" style="color:{band_color}">'
        f'{result["delay_probability"] * 100:.1f}%</div>'
        '<div class="lbl">Delay probability</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{BAND_TEXT_HEX[category]}">'
        f'{category.title()}</div><div class="lbl">Risk band</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{MARIGOLD_DEEP}">'
        f'{result["expected_delay_days"]} days</div>'
        '<div class="lbl">Expected delay</div></div>'
        f'<div class="tt-kpi"><div class="num" style="color:{TEAL}">'
        f'{result["critical_stage"]}</div>'
        '<div class="lbl">Most at-risk stage</div></div>'
        "</div>"
    )

    section(
        "Stage-wise risk",
        "Where this acquisition is most likely to stall, across the five statutory stages.",
    )
    stage_risk = result["stage_risk"]
    cards = ""
    for stage in STAGES:
        score = stage_risk[stage]
        band = stage_band(score)
        crit = " crit" if stage == result["critical_stage"] else ""
        cards += (
            f'<div class="tt-stage{crit}"><div class="n">{stage}</div>'
            f'<div class="pct" style="color:{BAND_TEXT_HEX[band]}">{score:.1f}</div>'
            f'<div class="barwrap"><div class="bar" style="width:{score}%;'
            f'background:{BAND_HEX[band]}"></div></div></div>'
        )
    html(f'<div class="tt-funnel">{cards}</div>')
    st.write("")
    html(
        '<div class="tt-note">Stage scores come from a transparent weighted rule over '
        "the project's raw parameters. They are an inspectable indicator, not a "
        "separately trained model, and are scored 0–100.</div>"
    )

    section(
        "Project and model",
        "The record under assessment, and the model that scored it.",
    )
    left, right = st.columns([1.15, 1], gap="medium")
    with left:
        html(
            '<div class="tt-panel"><h3>Project record</h3><div class="tt-facts">'
            f'<div><span>Project ID</span><b>{project["project_id"]}</b></div>'
            f'<div><span>Type</span><b>{project["project_type"]}</b></div>'
            f'<div><span>District</span><b>{project["district"]}, {project["state"]}</b></div>'
            f'<div><span>Land area</span><b>{project["land_area"]:.0f} ha</b></div>'
            f'<div><span>Affected families</span><b>{project["affected_families"]:,}</b></div>'
            f'<div><span>Risk score</span><b>{result["risk_score"]:.1f} / 100</b></div>'
            "</div></div>"
        )
    with right:
        metrics = metadata.get("test_metrics", {})
        rows = "".join(
            f"<div><span>{name}</span><b>{metrics[key]:.4f}</b></div>"
            for key, name in [
                ("roc_auc", "ROC-AUC"),
                ("accuracy", "Accuracy"),
                ("precision", "Precision"),
                ("recall", "Recall"),
                ("f1", "F1"),
            ]
            if key in metrics
        )
        html(
            '<div class="tt-panel"><h3>Model card</h3><div class="tt-facts">'
            f'<div><span>Training records</span><b>{metadata.get("n_training_records"):,}</b></div>'
            f"{rows}</div></div>"
        )
        st.caption("Held-out test split only. Synthetic dataset.")


# ===========================================================================
# TAB 2 — RISK MAP & PROJECT
# ===========================================================================
elif nav == NAV_ITEMS[1]:
    section(
        "Risk map and project register",
        "The acquisition under assessment, with the model's explanation for its score.",
    )

    map_col, detail_col = st.columns([1.3, 1], gap="medium")

    with map_col:
        html('<div class="tt-card-title">Project location</div>')
        fmap = folium.Map(
            location=[project["latitude"], project["longitude"]],
            zoom_start=10,
            tiles="OpenStreetMap",
            control_scale=True,
        )
        folium.CircleMarker(
            location=[project["latitude"], project["longitude"]],
            radius=11,
            color=band_color,
            weight=3,
            fill=True,
            fill_color=band_color,
            fill_opacity=0.85,
            tooltip=f'{project["project_id"]} — {category.title()} risk',
            popup=folium.Popup(
                f'<b>{project["project_name"]}</b><br>'
                f'{project["district"]}, {project["state"]}<br>'
                f'Risk score {result["risk_score"]:.1f}/100',
                max_width=260,
            ),
        ).add_to(fmap)
        # returned_objects carries a minimal payload so the component's
        # auto-resize channel keeps firing; without it the iframe can fall
        # back to an oversized default height (the "black box" bug).
        st_folium(
            fmap,
            height=330,
            use_container_width=True,
            returned_objects=["last_object_clicked"],
        )
        html(
            '<div style="display:flex; gap:14px; margin-top:10px; font-size:11.5px; '
            'color:var(--ink-soft);">'
            + "".join(
                f'<span style="display:inline-flex; align-items:center; gap:5px;">'
                f'<i style="width:9px;height:9px;border-radius:50%;display:inline-block;'
                f'background:{BAND_HEX[b]}"></i>{b.title()} risk</span>'
                for b in ("LOW", "MEDIUM", "HIGH")
            )
            + "</div>"
        )

    with detail_col:
        peak = max(abs(c["shap"]) for c in contributors) or 1.0
        drivers = ""
        for c in contributors:
            width = abs(c["shap"]) / peak * 100
            color = RUST if c["shap"] > 0 else GREEN
            drivers += (
                f'<div class="tt-driver"><div class="dl"><span>{c["label"]}</span>'
                f'<b>{c["shap"]:+.3f}</b></div>'
                f'<div class="db"><i style="width:{width:.1f}%; background:{color}"></i></div></div>'
            )
        html(
            '<div class="tt-detail">'
            f'<div class="pname">{project["project_name"]}</div>'
            f'<div class="pmeta">{project["district"]}, {project["state"]} · '
            f'Most at-risk stage: {result["critical_stage"]}</div>'
            f'<div class="tt-gauge-row"><div>{gauge_svg(result["risk_score"], band_color)}</div>'
            '<div class="tt-metrics-mini">'
            f'<div><span>Risk band</span><b style="color:{band_color}">{category.title()}</b></div>'
            f'<div><span>Delay probability</span><b>{result["delay_probability"] * 100:.1f}%</b></div>'
            f'<div><span>Expected delay</span><b>{result["expected_delay_days"]} days</b></div>'
            "</div></div>"
            '<div class="tt-drivers-head">Top delay drivers (SHAP, log-odds)</div>'
            f"{drivers}</div>"
        )

    section(
        "Project register",
        "Single-project demonstration. One record is scored end to end.",
    )
    html(
        '<table class="tt-table"><thead><tr>'
        "<th>Project</th><th>State</th><th>Most at-risk stage</th>"
        "<th>Risk band</th><th>Score</th><th>Delay probability</th>"
        "</tr></thead><tbody><tr>"
        f'<td><b>{project["project_name"]}</b></td>'
        f'<td>{project["state"]}</td>'
        f'<td>{result["critical_stage"]}</td>'
        f'<td><span class="tt-badge" style="color:{BAND_TEXT_HEX[category]}">'
        f'<i style="background:{band_color}"></i>{category.title()}</span></td>'
        f'<td class="tt-mono">{result["risk_score"]:.1f}/100</td>'
        f'<td class="tt-mono">{result["delay_probability"] * 100:.1f}%</td>'
        "</tr></tbody></table>"
    )

    section(
        "Why this score",
        "Exact TreeSHAP attributions, aggregated back to the original features.",
    )
    panel_left, panel_right = st.columns([1.25, 1], gap="medium")
    with panel_left:
        html(
            '<div class="tt-panel"><h3>Contribution to delay risk</h3>'
            f'{shap_bar_svg(contributors)}</div>'
        )
    with panel_right:
        html(f'<div class="tt-panel"><h3>In plain language</h3>'
             f'<div class="tt-plain">{analysis["explanation"]}</div></div>')


# ===========================================================================
# TAB 3 — ALERTS & RECOMMENDATIONS
# ===========================================================================
else:
    section(
        "Alerts and recommendations",
        f'Every item below is triggered by {project["project_id"]}\'s own parameters.',
    )

    alerts_col, recs_col = st.columns([1, 1.35], gap="medium")

    with alerts_col:
        urgent = [r for r in recommendations if r["priority"] in ("CRITICAL", "HIGH")]
        if urgent:
            rows = ""
            for r in urgent:
                rows += (
                    f'<div class="tt-alert"><div class="sev" style="background:'
                    f'{PRIORITY_HEX[r["priority"]]}"></div>'
                    f'<div><div class="t">{r["risk_factor"]}</div>'
                    f'<div class="ts">{r["feature"].replace("_", " ")} = '
                    f'{r["current_value"]}</div></div></div>'
                )
            body = rows
        else:
            body = '<div class="tt-empty">No high-priority alerts for this project.</div>'
        html(f'<div class="tt-panel"><h3>Live alerts</h3>{body}</div>')
        st.caption(
            "Alerts are the critical and high-priority rules that fired — not a "
            "separate notification service."
        )

    with recs_col:
        if recommendations:
            cards = ""
            for i, r in enumerate(recommendations, start=1):
                confirmed = (
                    '<span class="tt-confirm">Model-confirmed</span>'
                    if r["model_confirmed"]
                    else ""
                )
                cards += (
                    f'<div class="tt-rec"><div class="num">{i:02d}</div><div>'
                    f'<div><span class="tt-prio" style="background:'
                    f'{PRIORITY_HEX[r["priority"]]}">{r["priority"]}</span>'
                    f'<span class="rf">{r["risk_factor"]}</span>{confirmed}</div>'
                    f'<div class="act">{r["action"]}</div>'
                    f'<div class="meta">Owner: {r["stakeholder"]} · '
                    f'Current value: {r["current_value"]}</div></div></div>'
                )
            body = cards
        else:
            body = (
                '<div class="tt-empty">No rules fired. This project sits within '
                "normal parameters.</div>"
            )
        html(f'<div class="tt-panel"><h3>Recommended actions</h3>{body}</div>')
        st.caption(
            "Deterministic rules over the project's real values. Priority is raised "
            "one level when SHAP confirms the feature is a genuine risk driver."
        )