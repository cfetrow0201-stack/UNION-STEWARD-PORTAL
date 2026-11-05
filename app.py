st.markdown("""
<style>
/* Full-Bleed Tactical Topographic Background */
.stApp {
    background-color: #020408;
    background-image: 
        linear-gradient(rgba(2, 4, 8, 0.82), rgba(2, 4, 8, 0.85)), 
        url("app/static/topo_bg.jpg");
    background-size: cover;
    background-position: center center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    color: #cbd5e1;
    font-family: 'Courier New', Courier, monospace;
}

/* Fallback base64 background method if Streamlit static path varies */
@supports not (background-image: url("app/static/topo_bg.jpg")) {
    .stApp {
        background-color: #020408;
    }
}

/* Tactical Headers */
h1, h2, h3 {
    font-family: 'Courier New', Courier, monospace;
    letter-spacing: 2.5px;
    color: #ffb700 !important;
    text-transform: uppercase;
    text-shadow: 0 0 15px rgba(255, 183, 0, 0.45);
}

/* HUD Telemetry Ticker */
.ticker-wrap {
    width: 100%;
    overflow: hidden;
    background-color: rgba(8, 12, 20, 0.95);
    border-top: 2px solid #ffb700;
    border-bottom: 2px solid #ffb700;
    padding: 8px 0;
    margin-bottom: 25px;
    box-shadow: inset 0 0 20px rgba(255, 183, 0, 0.2), 0 5px 25px rgba(0,0,0,0.9);
}
.ticker {
    display: inline-block;
    white-space: nowrap;
    animation: marquee 35s linear infinite;
    font-family: 'Courier New', Courier, monospace;
    color: #ffb700;
    font-weight: bold;
    font-size: 13px;
    letter-spacing: 3px;
}
@keyframes marquee {
    0%   { transform: translate3d(0, 0, 0); }
    100% { transform: translate3d(-50%, 0, 0); }
}

/* Sci-Fi Glass Panels */
.tech-card {
    background: linear-gradient(135deg, rgba(13, 19, 33, 0.88) 0%, rgba(5, 8, 15, 0.94) 100%);
    border: 1px solid rgba(255, 183, 0, 0.3);
    border-top: 3px solid #ffb700;
    padding: 22px;
    border-radius: 4px;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.85), inset 0 0 15px rgba(255, 183, 0, 0.05);
    backdrop-filter: blur(4px);
}

/* Status Badges */
.status-badge {
    background-color: rgba(255, 183, 0, 0.12);
    border: 1px solid #ffb700;
    color: #ffb700;
    padding: 6px 14px;
    border-radius: 2px;
    font-family: monospace;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 2px;
    box-shadow: 0 0 12px rgba(255, 183, 0, 0.35);
    display: inline-block;
}

/* Stark HUD Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1e293b 0%, #090d16 100%) !important;
    border: 1px solid #ffb700 !important;
    color: #ffb700 !important;
    font-family: 'Courier New', Courier, monospace !important;
    font-weight: bold !important;
    letter-spacing: 2px !important;
    border-radius: 2px !important;
    box-shadow: 0 0 12px rgba(255, 183, 0, 0.2);
    transition: all 0.25s ease-in-out;
}
.stButton > button:hover {
    background: #ffb700 !important;
    color: #020408 !important;
    box-shadow: 0 0 25px rgba(255, 183, 0, 0.7);
    transform: translateY(-1px);
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(8, 12, 20, 0.95);
    padding: 12px;
    border-radius: 4px;
    border: 1px solid rgba(255, 183, 0, 0.35);
}
.stTabs [data-baseweb="tab"] {
    color: #64748b;
    font-family: monospace;
    font-weight: bold;
    letter-spacing: 1.5px;
}
.stTabs [aria-selected="true"] {
    background-color: #1e293b !important;
    color: #ffb700 !important;
    border-top: 2px solid #ffb700 !important;
    box-shadow: inset 0 0 12px rgba(255, 183, 0, 0.25);
}
</style>
""", unsafe_allow_html=True)
