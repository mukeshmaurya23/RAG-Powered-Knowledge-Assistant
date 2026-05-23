import streamlit as st

st.set_page_config(
    page_title="RAG Chatbot",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
/* Fix top margin cut-off on tabs and main content */
.block-container {
    padding-top: 2.5rem !important;
    padding-bottom: 1rem;
    max-width: 1200px;
}

/* Tab content area - prevent cut-off */
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1rem;
}

/* Tabs bar */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1px solid #333;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px 6px 0 0;
    padding: 10px 20px;
    font-weight: 500;
}

/* Chat message containers */
.stChatMessage {
    border-radius: 8px;
    margin-bottom: 4px;
}

/* Sidebar */
section[data-testid="stSidebar"] > div {
    padding-top: 1.5rem;
}

/* Metric cards */
div[data-testid="stMetric"] {
    background: #1a1f2e;
    border: 1px solid #2d3348;
    padding: 1rem;
    border-radius: 8px;
}
div[data-testid="stMetric"] label {
    color: #9ca3af !important;
    font-size: 0.85rem !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #f0f0f0 !important;
    font-size: 1.6rem !important;
}

/* Confidence indicator */
.conf-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.conf-high { background: #14532d; color: #4ade80; }
.conf-medium { background: #713f12; color: #fbbf24; }
.conf-low { background: #7f1d1d; color: #f87171; }
.conf-none { background: #1f2937; color: #9ca3af; }

/* Source box */
.source-item {
    border-left: 3px solid #334155;
    padding: 6px 12px;
    margin: 6px 0;
    font-size: 0.85rem;
    color: #cbd5e1;
}

/* Remove extra whitespace from iframes (voice component) */
iframe {
    border: none !important;
}

/* Download button alignment */
.stDownloadButton > button {
    font-size: 0.8rem;
    padding: 4px 12px;
}
</style>
""", unsafe_allow_html=True)


# ── Session State ───────────────────────────────────────────────────
defaults = {
    "messages": [],
    "session_id": None,
    "documents": [],
    "active_file_id": None,
    "language": "English",
    "backend_ok": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ── Layout ──────────────────────────────────────────────────────────
from sidebar import display_sidebar
from chat_interface import display_chat_interface
from analytics_page import display_analytics

display_sidebar()

tab_chat, tab_analytics = st.tabs(["Chat", "Analytics"])

with tab_chat:
    display_chat_interface()

with tab_analytics:
    display_analytics()
