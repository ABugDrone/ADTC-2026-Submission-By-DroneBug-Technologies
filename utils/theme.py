import streamlit as st

_LIGHT = {
    "bg": "#FFFFFF",
    "bg2": "#F8FAFC",
    "surface": "#F1F5F9",
    "text": "#0F172A",
    "muted": "#64748B",
    "border": "#E2E8F0",
    "accent": "#4F46E5",
    "accentsoft": "#EEF2FF",
    "danger": "#DC2626",
    "warning": "#D97706",
    "success": "#16A34A",
}

_DARK = {
    "bg": "#0F172A",
    "bg2": "#1E293B",
    "surface": "#1E293B",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
    "border": "#334155",
    "accent": "#818CF8",
    "accentsoft": "#1E1B4B",
    "danger": "#EF4444",
    "warning": "#F59E0B",
    "success": "#10B981",
}

_NAV_ITEMS = [
    ("Home", "home", "app.py"),
    ("Meetings & Tasks", "calendar-event", "pages/1_Calendar_and_Tasks.py"),
    ("Chat & Knowledge Base", "messages", "pages/2_Chat_and_RAG.py"),
    ("Data & Charts", "chart-bar", "pages/3_Data_and_Charts.py"),
    ("Financial Analyst", "coin", "pages/4_Financial_Analyst.py"),
]

_EMOJI_ICONS = {
    "home": "\U0001f3e0",
    "calendar-event": "\U0001f4c5",
    "messages": "\U0001f4ac",
    "chart-bar": "\U0001f4ca",
    "coin": "\U0001fa99",
    "rocket": "\U0001f680",
    "file-upload": "\U0001f4c1",
    "table": "\U0001f4d3",
    "calendar-off": "\U0001f634",
    "send": "\u27a1\ufe0f",
    "check": "\u2705",
    "x": "\u274c",
    "trash": "\U0001f5d1\ufe0f",
    "edit": "\u270f\ufe0f",
    "cpu": "\U0001f5a5\ufe0f",
}

# Inline SVG icon paths (Tabler-style, 24x24 viewBox) so the app works fully offline.
_ICONS = {
    "home": "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6",
    "calendar-event": "M4 5a2 2 0 012-2h12a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm0 5h16M8 3v4M16 3v4M11 14h2v2h-2z",
    "messages": "M14 10h.01M10 14h.01M18 10h.01M6 14h.01M7 3h10a4 4 0 014 4v10a4 4 0 01-4 4H7a4 4 0 01-4-4V7a4 4 0 014-4z",
    "chart-bar": "M3 13a2 2 0 012-2h2a2 2 0 012 2v6H3v-6zm6-4a2 2 0 012-2h2a2 2 0 012 2v10H9V9zm6-3a2 2 0 012-2h2a2 2 0 012 2v13h-6V6z",
    "coin": "M12 2a10 10 0 100 20 10 10 0 000-20zm0 6a4 4 0 110 8 4 4 0 010-8z",
    "rocket": "M4.5 16.5c-1.5 1.5-1.5 3.5-1.5 3.5s2-.5 3.5-1.5l3-3M12 4s5 0 8 4c0 0-2 6-8 8-6-2-8-8-8-8 3-4 8-4 8-4zm0 5a2 2 0 110 4 2 2 0 010-4z",
    "file-upload": "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM12 11v6m-3-3l3 3 3-3",
    "table": "M3 5a2 2 0 012-2h14a2 2 0 012 2v14a2 2 0 01-2 2H5a2 2 0 01-2-2V5zm0 5h18M10 5v14",
    "calendar-off": "M4 5a2 2 0 012-2h12a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm0 5h16M8 3v4M16 3v4M3 3l18 18",
    "send": "M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z",
    "check": "M5 12l5 5L20 7",
    "x": "M6 6l12 12M6 18L18 6",
    "trash": "M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2",
    "edit": "M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z",
    "cpu": "M4 4h16v16H4zM9 9h6v6H9zM9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 15h3M1 9h3M1 15h3",
}


def icon(name: str, size: int = 20, color: str = "currentColor") -> str:
    """Return an inline SVG icon string. Works offline."""
    path = _ICONS.get(name, _ICONS["check"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" '
        f'stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-3px;">'
        f'<path d="{path}" /></svg>'
    )


def init_theme_state():
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True


def palette():
    init_theme_state()
    return _DARK if st.session_state.dark_mode else _LIGHT


def plotly_template():
    return "plotly_dark" if st.session_state.dark_mode else "plotly_white"


def theme_toggle_control():
    init_theme_state()
    value = st.toggle(
        "Light mode" if st.session_state.dark_mode else "Dark mode",
        value=not st.session_state.dark_mode,
        key="_theme_toggle",
        help="Toggle between dark and light themes",
    )
    st.session_state.dark_mode = not value


def _check_model_status() -> bool:
    """Check if the llama server is reachable."""
    try:
        import httpx
        from . import config
        resp = httpx.get(f"{config.LLAMA_HOST}/v1/models", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def _nav_url(path: str) -> str:
    """Map a page file path to its Streamlit URL slug."""
    if path == "app.py":
        return "/"
    name = path.split("/")[-1].replace(".py", "")
    if "_" in name and name.split("_")[0].isdigit():
        name = name.split("_", 1)[1]
    return f"/{name}"


def sidebar_nav(active_label: str = "Home"):
    init_theme_state()
    p = palette()

    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            <div style="width:28px;height:28px;border-radius:8px;background:{p['accent']};display:flex;align-items:center;justify-content:center;color:{p['bg']};font-weight:700;font-size:14px;">BP</div>
            <span style="font-size:16px;font-weight:600;letter-spacing:-0.2px;">BusinessPilot AI</span>
        </div>
        <p style="font-size:11px;color:{p['muted']};margin:0 0 12px;">Offline business copilot</p>
        """,
        unsafe_allow_html=True,
    )

    # Theme toggle
    is_dark = st.toggle("Dark mode", value=st.session_state.dark_mode, key="_theme_toggle")
    if is_dark != st.session_state.dark_mode:
        st.session_state.dark_mode = is_dark
        st.rerun()

    st.divider()

    # Nav items using st.page_link to avoid new tabs
    for label, icon_name, path in _NAV_ITEMS:
        st.page_link(
            path,
            label=label,
            icon=_EMOJI_ICONS.get(icon_name, ""),
        )

    st.divider()

    # Model status
    model_status = _check_model_status()
    status_color = p["success"] if model_status else p["danger"]
    status_text = "Connected" if model_status else "Not running"
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:8px;padding-top:8px;">
            <div style="width:8px;height:8px;border-radius:50%;background:{status_color};"></div>
            <span style="font-size:12px;color:{p['muted']};font-weight:500;">Model · {status_text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = ""):
    st.markdown(
        f"<h1 style='font-size:26px;font-weight:600;letter-spacing:-0.3px;margin:0 0 4px;'>{title}</h1>",
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f"<p style='font-size:14px;color:var(--muted);margin:0 0 20px;'>{subtitle}</p>",
            unsafe_allow_html=True,
        )
    st.write("")


def status_badge(label: str, kind: str = "accent") -> str:
    """Return an HTML status badge string."""
    return f'<span class="pill pill-{kind}">{label}</span>'


def empty_state(icon_name: str, title: str, message: str):
    """Render a centered empty-state block."""
    p = palette()
    st.markdown(
        f"""
        <div class="bp-empty">
            <div style="margin-bottom:12px;color:{p['muted']};">{icon(icon_name, size=40)}</div>
            <p style="font-size:15px;font-weight:600;margin:0 0 4px;color:{p['text']};">{title}</p>
            <p style="font-size:13px;color:{p['muted']};margin:0;max-width:320px;text-align:center;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def loading_skeleton(lines: int = 3):
    """Render a blocky loading skeleton."""
    html = '<div class="bp-skeleton">'
    for i in range(lines):
        width = "85%" if i % 2 == 0 else "60%"
        html += f'<div class="bp-skeleton-line" style="width:{width};"></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def inject_css():
    p = palette()
    st.markdown(
        f"""
        <style>
        :root {{
            --bg: {p['bg']};
            --bg2: {p['bg2']};
            --surface: {p['surface']};
            --text: {p['text']};
            --muted: {p['muted']};
            --border: {p['border']};
            --accent: {p['accent']};
            --accentsoft: {p['accentsoft']};
            --danger: {p['danger']};
            --warning: {p['warning']};
            --success: {p['success']};
        }}

        html, body, [class*="css"] {{
            font-family: "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}

        h1, h2, h3, h4, h5, h6 {{
            font-weight: 600 !important;
            letter-spacing: -0.3px;
        }}

        [data-testid="stAppViewContainer"] {{
            background: var(--bg) !important;
            color: var(--text) !important;
        }}

        [data-testid="stSidebar"] {{
            background: var(--bg2) !important;
            border-right: 1px solid var(--border) !important;
        }}

        [data-testid="stHeader"] {{ background: transparent !important; }}
        #MainMenu, footer, .stDeployButton, .stToolbar, div[data-testid="stDecoration"],
        [data-testid="stSidebarNav"] {{
            display: none !important;
        }}

        /* ---------- Cards (Streamlit bordered containers) ---------- */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 14px !important;
            padding: 0 !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.12), 0 4px 12px rgba(0,0,0,0.08) !important;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] > div {{
            padding: 1.25rem !important;
        }}

        /* ---------- Empty states ---------- */
        .bp-empty {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 48px 24px;
            border: 1px dashed var(--border);
            border-radius: 14px;
            background: var(--bg2);
        }}

        /* ---------- Skeleton ---------- */
        .bp-skeleton {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding: 16px;
        }}
        .bp-skeleton-line {{
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, var(--border) 25%, var(--surface) 50%, var(--border) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.4s infinite;
        }}
        @keyframes shimmer {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}

        /* ---------- Pills / badges ---------- */
        .pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
            line-height: 1.4;
        }}
        .pill-accent {{ background: var(--accentsoft); color: var(--accent); }}
        .pill-success {{ background: rgba(74,222,128,0.12); color: var(--success); }}
        .pill-danger  {{ background: rgba(248,113,113,0.12); color: var(--danger); }}
        .pill-warning {{ background: rgba(251,191,36,0.12); color: var(--warning); }}

        /* ---------- Sidebar nav items ---------- */
        .nav-item {{
            display: flex; align-items: center; gap: 10px;
            padding: 9px 12px; border-radius: 10px;
            font-size: 13.5px; color: var(--muted) !important;
            transition: all 0.15s ease;
            text-decoration: none !important;
            margin-bottom: 3px;
            font-weight: 500;
        }}
        .nav-item:hover {{ background: var(--accentsoft); color: var(--accent) !important; }}
        .nav-item.active {{ background: var(--accentsoft); color: var(--accent) !important; }}
        .nav-item-icon {{ display: inline-flex; width: 22px; justify-content: center; }}

        /* ---------- Page links (st.page_link) ---------- */
        [data-testid="stPageLink"] {{
            all: initial !important;
            font-family: inherit !important;
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
            padding: 9px 12px !important;
            border-radius: 10px !important;
            font-size: 13.5px !important;
            color: var(--muted) !important;
            transition: all 0.15s ease !important;
            text-decoration: none !important;
            margin-bottom: 3px !important;
            font-weight: 500 !important;
            border: none !important;
            background: transparent !important;
        }}
        [data-testid="stPageLink"]:hover {{
            background: var(--accentsoft) !important;
            color: var(--accent) !important;
        }}
        [aria-current="page"] {{
            background: var(--accentsoft) !important;
            color: var(--accent) !important;
        }}
        [data-testid="stPageLink"] [data-testid="stMarkdownContainer"] p {{
            color: inherit !important;
            margin: 0 !important;
            font-size: inherit !important;
        }}
        [data-testid="stPageLink"] > span {{
            color: inherit !important;
        }}

        /* ---------- Status dot ---------- */
        .status-dot {{
            width: 7px; height: 7px;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 0 0 rgba(74,222,128,0.4);
            animation: pulse-dot 2s infinite;
        }}
        @keyframes pulse-dot {{
            0% {{ box-shadow: 0 0 0 0 rgba(74,222,128,0.4); }}
            70% {{ box-shadow: 0 0 0 6px rgba(74,222,128,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(74,222,128,0); }}
        }}

        /* ---------- Buttons ---------- */
        div.stButton > button {{
            background: var(--accent) !important;
            color: #fff !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 7px 16px !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            transition: opacity 0.15s, transform 0.05s;
        }}
        div.stButton > button:hover {{ opacity: 0.88; }}
        div.stButton > button:active {{ transform: translateY(1px); }}
        div.stButton > button[kind="secondary"] {{
            background: var(--surface) !important;
            color: var(--text) !important;
            border: 1px solid var(--border) !important;
        }}
        div.stButton > button[kind="secondary"]:hover {{ background: var(--accentsoft) !important; color: var(--accent) !important; }}

        /* ---------- Metrics ---------- */
        [data-testid="stMetric"] {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 0.9rem 1rem;
            min-width: 0;
        }}
        [data-testid="stMetric"] label {{
            color: var(--muted) !important;
            font-size: 11px !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }}
        [data-testid="stMetric"] > div {{
            color: var(--text) !important;
            font-weight: 700 !important;
            font-size: 20px !important;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* ---------- DataFrames ---------- */
        [data-testid="stDataFrame"] {{
            border-radius: 12px; overflow: hidden;
            border: 1px solid var(--border);
        }}

        /* ---------- Dividers ---------- */
        hr, [data-testid="stDivider"] {{
            border-color: var(--border) !important;
        }}

        /* ---------- Expanders ---------- */
        .streamlit-expanderHeader {{
            font-weight: 500 !important;
            border-radius: 10px !important;
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
        }}
        details {{
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
        }}

        /* ---------- Chat ---------- */
        [data-testid="stChatMessage"] {{
            border-radius: 12px !important;
            padding: 0.75rem 1rem !important;
            border: 1px solid var(--border) !important;
            background: var(--surface) !important;
            margin: 6px 0 !important;
        }}
        .stChatInput {{
            border-radius: 12px !important;
            border: 1px solid var(--border) !important;
            background: var(--bg2) !important;
        }}

        /* ---------- Tabs ---------- */
        .stTabs [data-baseweb="tab-list"] {{
            border-bottom: 1px solid var(--border) !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            font-size: 13px !important;
            color: var(--muted) !important;
            font-weight: 500 !important;
            padding: 10px 14px !important;
        }}
        .stTabs [aria-selected="true"] {{
            color: var(--accent) !important;
            font-weight: 600 !important;
            border-bottom: 2px solid var(--accent) !important;
        }}

        /* ---------- File uploader ---------- */
        [data-testid="stFileUploader"] > section {{
            background: var(--bg2) !important;
            border: 1px dashed var(--border) !important;
            border-radius: 12px !important;
        }}
        [data-testid="stFileUploader"] > section * {{
            color: var(--text) !important;
        }}
        [data-testid="stFileUploader"] small {{
            color: var(--muted) !important;
        }}
        [data-testid="stFileUploader"] button {{
            background: var(--accent) !important;
            color: #fff !important;
            border: none !important;
        }}

        /* ---------- Text inputs / selects ---------- */
        .stTextInput input, .stNumberInput input, .stDateInput input, .stTimeInput input,
        .stSelectbox div[data-baseweb="select"] > div {{
            border-radius: 10px !important;
            border-color: var(--border) !important;
            background: var(--bg) !important;
            color: var(--text) !important;
        }}
        .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stTimeInput input:focus {{
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 1px var(--accent) !important;
        }}
        .stNumberInput > div > div > div button {{
            background: var(--bg) !important;
            color: var(--text) !important;
            border-color: var(--border) !important;
        }}
        .stSelectbox > div > div > div {{
            background: var(--bg) !important;
            color: var(--text) !important;
        }}
        .stSelectbox div[data-baseweb="select"] {{
            background: var(--bg) !important;
        }}
        .stSelectbox div[data-baseweb="popover"] {{
            background: var(--bg2) !important;
            color: var(--text) !important;
        }}

        /* ---------- Alerts ---------- */
        .stAlert, .stInfo, .stSuccess, .stWarning, .stError {{
            border-radius: 10px !important;
            border-left-width: 3px !important;
            background: var(--surface) !important;
            color: var(--text) !important;
        }}
        .stInfo {{ border-left-color: var(--accent) !important; }}
        .stSuccess {{ border-left-color: var(--success) !important; }}
        .stWarning {{ border-left-color: var(--warning) !important; }}
        .stError {{ border-left-color: var(--danger) !important; }}

        /* ---------- Section labels ---------- */
        .section-label {{
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: var(--muted);
            margin-bottom: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
