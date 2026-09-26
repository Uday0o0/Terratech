"""
TerraTech — Shared UI Components and Design Tokens.
Extracted from app.py to prevent circular import issues.
"""

import streamlit as st

# ===========================================================================
# DESIGN TOKENS
# ===========================================================================
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

LIGHT_TOKENS = {
    "cream": "#F7F3E8", "cream-2": "#EFE7D2", "paper": "#FFFDF8",
    "ink": "#1E2A2F", "ink-soft": "#5B6A6C", "ink-faint": "#8B9B9C",
    "rule": "#E1D8C0", "rule-soft": "#ECE4CF",
    "teal-soft": "#E4EFEE", "accent-ink": "#144F4C",
}
DARK_TOKENS = {
    "cream": "#0F1815", "cream-2": "#16211D", "paper": "#131E1A",
    "ink": "#EAE6D7", "ink-soft": "#AEBBAF", "ink-faint": "#7E8C81",
    "rule": "#28352D", "rule-soft": "#20291F",
    "teal-soft": "#132824", "accent-ink": "#7FC4BC",
}

BAND_HEX = {"LOW": GREEN, "MEDIUM": MARIGOLD, "HIGH": RUST, "CRITICAL": RUST_DEEP}
BAND_TEXT_HEX = {"LOW": GREEN, "MEDIUM": MARIGOLD_DEEP, "HIGH": RUST, "CRITICAL": RUST_DEEP}
PRIORITY_HEX = {"CRITICAL": RUST_DEEP, "HIGH": RUST, "MEDIUM": MARIGOLD_DEEP, "LOW": GREEN}

SEVERITY_EMOJI = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢", "INFO": "🔵"}
STAGE_BAND_CUTOFFS = (35.0, 60.0)


def stage_band(score: float) -> str:
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

@keyframes ttFadeInUp {{
    0% {{ opacity: 0; transform: translateY(12px); }}
    100% {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes ttFadeIn {{
    0% {{ opacity: 0; }}
    100% {{ opacity: 1; }}
}}

:root {{
    {token_lines}
    --navy:{NAVY}; --navy-deep:{NAVY_DEEP}; --navy-soft:{NAVY_SOFT};
    --teal:{TEAL}; --teal-deep:{TEAL_DEEP};
    --marigold:{MARIGOLD}; --marigold-deep:{MARIGOLD_DEEP};
    --rust:{RUST}; --rust-deep:{RUST_DEEP}; --green:{GREEN};
    --shadow-sm:0 2px 10px -4px rgba(15,42,61,.14);
    --shadow-md:0 14px 34px -18px rgba(15,42,61,.32);
}}

.stApp {{
    animation: ttFadeIn 0.3s ease-out;
    background: var(--cream);
    color: var(--ink);
    font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif;
    font-size: 14.5px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
}}
.block-container {{ padding: 1.6rem 2.2rem 5rem; max-width: 1320px; }}
h1, h2, h3 {{ font-family: 'Fraunces', Georgia, serif; font-weight: 600; color: var(--ink) !important; }}
.tt-mono {{ font-family: 'JetBrains Mono', ui-monospace, monospace; }}
#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
div[data-testid="stToolbar"] {{ display: none; }}
div[data-testid="stDecoration"] {{ display: none; }}
::selection {{ background: var(--marigold); color: #2A2109; }}

/* Sidebar: dark navy rail */
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

/* Radio nav buttons */
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
.tt-side-foot {{ font-size:10.5px; color:#7E9490 !important; border-top:1px solid rgba(255,255,255,.1); padding-top:12px; margin-top:18px; }}

/* Sidebar button */
section[data-testid="stSidebar"] .stButton > button {{
    width:100%; background:var(--rust); color:#fff !important; border:none;
    border-radius:12px; padding:12px 20px; font-weight:700; font-size:13.5px;
    box-shadow:var(--shadow-sm); transition: background .15s ease, transform .1s ease;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{ background:var(--rust-deep); }}
section[data-testid="stSidebar"] .stButton > button:active {{ transform:scale(.97); }}

/* Collapse controls */
[data-testid="stSidebarCollapsedControl"] {{ z-index: 60; }}
[data-testid="stSidebarCollapsedControl"] button {{
    background: var(--paper) !important;
    border: 1px solid var(--rule) !important;
    border-radius: 10px;
    width: 38px; height: 38px;
    color: var(--ink) !important;
    box-shadow: var(--shadow-sm);
}}
[data-testid="stSidebarCollapseButton"] button {{
    background: rgba(255,255,255,.08) !important;
    border: 1px solid rgba(255,255,255,.14) !important;
    border-radius: 8px;
    color: #C3D0CD !important;
}}

/* Topbar */
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

/* Cards & Panels */
.tt-section h2 {{ font-size:18px; margin:0; }}
.tt-section p {{ font-size:12.5px; color:var(--ink-soft); margin:3px 0 0 !important; }}
.tt-section {{ margin:26px 0 14px; }}
.tt-section:first-child {{ margin-top:0; }}

.tt-panel {{
    animation: ttFadeInUp 0.4s ease-out forwards;
    background:var(--paper); border:1px solid var(--rule); border-radius:14px; padding:18px; 
}}
.tt-panel h3 {{ font-size:15px; margin:0 0 12px; }}
.tt-kpis {{
    animation: ttFadeInUp 0.5s ease-out forwards;
    display:grid; grid-template-columns:repeat(4,1fr); gap:1px; background:var(--rule); border:1px solid var(--rule); border-radius:12px; overflow:hidden; 
}}
.tt-kpi {{
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    background:var(--paper); padding:18px; 
}}
.tt-kpi:hover {{
    transform: translateY(-2px); 
    box-shadow: 0 6px 14px rgba(0,0,0,0.05); 
}}
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

/* Detail panel (dark) */
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

/* Table */
.tt-table {{ width:100%; border-collapse:separate; border-spacing:0; background:var(--paper); border:1px solid var(--rule); border-radius:14px; overflow:hidden; font-size:13px; }}
.tt-table th {{ text-align:left; font-size:11px; font-weight:700; color:var(--ink-soft); padding:12px 14px; background:var(--cream-2); border-bottom:1px solid var(--rule); }}
.tt-table td {{ padding:13px 14px; color:var(--ink); border-bottom:1px solid var(--rule-soft); }}
.tt-table tr:last-child td {{ border-bottom:none; }}
.tt-table tr:hover td {{ background:var(--cream-2); }}
.tt-badge {{ display:inline-flex; align-items:center; gap:6px; font-size:11.5px; font-weight:700; padding:4px 10px; border-radius:20px; background:var(--cream-2); }}
.tt-badge i {{ width:9px; height:9px; border-radius:50%; display:inline-block; }}

/* Alerts */
.tt-alert {{ display:flex; gap:10px; padding:11px 12px; border-radius:10px; background:var(--cream-2); margin-bottom:8px; }}
.tt-alert .sev {{ width:8px; height:8px; border-radius:50%; margin-top:6px; flex:none; }}
.tt-alert .t {{ font-size:12.5px; line-height:1.45; color:var(--ink); }}
.tt-alert .ts {{ font-size:10.5px; color:var(--ink-faint); margin-top:2px; }}

/* Recommendations */
.tt-rec {{ display:flex; gap:12px; padding:14px; border:1px solid var(--rule); border-radius:12px; background:var(--paper); margin-bottom:10px; }}
.tt-rec .num {{ font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:600; color:var(--ink-faint); flex:none; padding-top:2px; }}
.tt-rec .rf {{ font-size:13.5px; font-weight:600; color:var(--ink); }}
.tt-rec .act {{ font-size:12.5px; color:var(--ink-soft); margin-top:5px; }}
.tt-rec .meta {{ font-size:11.5px; color:var(--ink-faint); margin-top:7px; }}
.tt-prio {{ display:inline-block; font-size:10px; font-weight:800; letter-spacing:.06em; color:#fff; padding:3px 9px; border-radius:6px; margin-right:8px; vertical-align:2px; }}
.tt-confirm {{ display:inline-block; font-size:10px; font-weight:700; color:var(--accent-ink); background:var(--teal-soft); border:1px solid var(--rule); padding:2px 8px; border-radius:6px; margin-left:6px; }}

/* Notices */
.tt-note {{ background:var(--teal-soft); border:1px solid var(--rule); border-left:3px solid var(--teal); border-radius:10px; padding:11px 14px; font-size:12px; color:var(--ink-soft); }}
.tt-plain {{ background:var(--cream-2); border-radius:12px; padding:16px 18px; font-size:13.5px; line-height:1.6; color:var(--ink); }}
.tt-empty {{ padding:26px; text-align:center; color:var(--ink-faint); font-size:12.5px; background:var(--paper); border:1px dashed var(--rule); border-radius:12px; }}

/* Main buttons */
div[data-testid="stMain"] .stButton > button {{
    background:var(--paper); color:var(--ink); border:1.5px solid var(--rule);
    border-radius:12px; padding:9px 18px; font-weight:600; font-size:13px;
}}
div[data-testid="stMain"] .stButton > button:hover {{ border-color:var(--teal); color:var(--ink); }}

/* Timeline */
.tt-timeline {{ position:relative; padding-left:24px; }}
.tt-timeline::before {{ content:''; position:absolute; left:8px; top:0; bottom:0; width:2px; background:var(--rule); }}
.tt-tl-item {{
    animation: ttFadeInUp 0.6s ease-out forwards;
    position:relative; margin-bottom:16px; 
}}
.tt-tl-item::before {{ content:''; position:absolute; left:-20px; top:6px; width:10px; height:10px; border-radius:50%; border:2px solid var(--teal); background:var(--paper); }}
.tt-tl-item.completed::before {{ background:var(--green); border-color:var(--green); }}
.tt-tl-item.active::before {{ background:var(--marigold); border-color:var(--marigold); }}
.tt-tl-item.delayed::before {{ background:var(--rust); border-color:var(--rust); }}
.tt-tl-title {{ font-size:13px; font-weight:600; color:var(--ink); }}
.tt-tl-meta {{ font-size:11px; color:var(--ink-soft); margin-top:2px; }}

/* Map */
iframe[title="streamlit_folium.st_folium"] {{
    border-radius:10px; border:1px solid var(--rule);
    height:380px !important; max-height:380px !important;
    width:100% !important; overflow:hidden;
}}

/* Login page */
.tt-login-box {{
    max-width:400px; margin:80px auto; padding:40px;
    background:var(--paper); border:1px solid var(--rule);
    border-radius:16px; box-shadow:var(--shadow-md);
}}
.tt-login-title {{
    font-family:'Fraunces',serif; font-size:24px; font-weight:700;
    text-align:center; margin-bottom:6px;
}}
.tt-login-sub {{
    font-size:12.5px; color:var(--ink-soft); text-align:center; margin-bottom:28px;
}}

/* Progress bar */
.tt-progress {{ height:6px; background:var(--cream-2); border-radius:3px; overflow:hidden; }}
.tt-progress-bar {{ height:100%; border-radius:3px; transition:width .3s ease; }}

/* Responsive */
@media (max-width: 900px) {{
    .tt-kpis {{
        grid-template-columns:repeat(2,1fr); 
    }}
    .tt-funnel {{ grid-template-columns:repeat(2,1fr); }}
    .block-container {{ padding:1.2rem 1rem 4rem; }}
}}
@media (prefers-reduced-motion: reduce) {{
    * {{ transition:none !important; animation:none !important; }}
}}
</style>
"""


# ===========================================================================
# HTML HELPERS
# ===========================================================================
def html(fragment: str) -> None:
    st.markdown(" ".join(fragment.split()), unsafe_allow_html=True)


def section(title: str, subtitle: str) -> None:
    html(f'<div class="tt-section"><h2>{title}</h2><p>{subtitle}</p></div>')


def render_badge(category: str) -> str:
    color = BAND_HEX.get(category, RUST)
    text_color = BAND_TEXT_HEX.get(category, RUST)
    return (f'<span class="tt-badge" style="color:{text_color}">'
            f'<i style="background:{color}"></i>{category.title()}</span>')


def render_progress_bar(pct: float, color: str = None) -> str:
    if color is None:
        if pct >= 75:
            color = GREEN
        elif pct >= 40:
            color = MARIGOLD
        else:
            color = RUST
    return (f'<div class="tt-progress">'
            f'<div class="tt-progress-bar" style="width:{pct:.0f}%;background:{color}"></div></div>')


# ===========================================================================
# SVG VISUALIZATIONS
# ===========================================================================
def gauge_svg(score: float, color: str) -> str:
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
