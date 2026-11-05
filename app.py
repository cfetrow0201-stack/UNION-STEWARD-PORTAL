import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime
from google import genai
from google.genai import types

# --- PAGE CONFIG & TACTICAL HUD STYLING ---
st.set_page_config(
    page_title="USW // TACTICAL COMMAND NETWORK", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Special Ops / Tony Stark HUD CSS with Background Image
st.markdown("""
<style>
/* Full-Bleed Tactical Topographic Background using background tele.png */
.stApp {
    background-color: #020408;
    background-image: 
        linear-gradient(rgba(2, 4, 8, 0.82), rgba(2, 4, 8, 0.85)), 
        url("background tele.png");
    background-size: cover;
    background-position: center center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    color: #cbd5e1;
    font-family: 'Courier New', Courier, monospace;
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

DB_NAME = "union_grievances.db"
ADMIN_EMAIL = "cfetrow0201@gmail.com"
ADMIN_PIN = "4812"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BACKUP_FILE = os.path.join(BASE_DIR, "grievance_backup.xlsx")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

def sync_db_to_excel():
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        df = pd.read_sql_query("SELECT * FROM grievances", conn)
        conn.close()
        df.to_excel(BACKUP_FILE, index=False)
    except Exception as e:
        print(f"Error syncing to Excel: {e}")

def restore_db_from_excel():
    if os.path.exists(BACKUP_FILE):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            cursor = conn.cursor()
            df_backup = pd.read_excel(BACKUP_FILE)
            for _, row in df_backup.iterrows():
                cursor.execute("SELECT COUNT(*) FROM grievances WHERE grievant = ? AND occ_date = ? AND articles = ?", (str(row.get("grievant", "")), str(row.get("occ_date", "")), str(row.get("articles", ""))))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("INSERT INTO grievances (user_email, grievant, occ_date, articles, step, steward, committeeman, facts, remedy, evidence_image, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (str(row.get("user_email", "")), str(row.get("grievant", "")), str(row.get("occ_date", "")), str(row.get("articles", "")), str(row.get("step", "")), str(row.get("steward", "")), str(row.get("committeeman", "")), str(row.get("facts", "")), str(row.get("remedy", "")), str(row.get("evidence_image", "No Image")), str(row.get("timestamp", datetime.now()))))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error restoring from Excel: {e}")
            return False
    return False

def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS grievances (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, grievant TEXT, occ_date TEXT, articles TEXT, step TEXT, steward TEXT, committeeman TEXT, facts TEXT, remedy TEXT, evidence_image TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("SELECT COUNT(*) FROM grievances")
    if cursor.fetchone()[0] == 0:
        restore_db_from_excel()
    cursor.execute("CREATE TABLE IF NOT EXISTS master_documents (doc_type TEXT PRIMARY KEY, pdf_data BLOB, file_name TEXT, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("SELECT COUNT(*) FROM master_documents WHERE doc_type = 'contract'")
    if cursor.fetchone()[0] == 0:
        potential_contract_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith(".pdf") and ("bla" in f.lower() or "contract" in f.lower())]
        if potential_contract_files:
            c_file = potential_contract_files[0]
            with open(os.path.join(BASE_DIR, c_file), "rb") as f:
                pdf_bytes = f.read()
            cursor.execute("INSERT OR REPLACE INTO master_documents (doc_type, pdf_data, file_name, updated_at) VALUES ('contract', ?, ?, CURRENT_TIMESTAMP)", (pdf_bytes, c_file))
    cursor.execute("SELECT COUNT(*) FROM master_documents WHERE doc_type = 'handbook'")
    if cursor.fetchone()[0] == 0:
        potential_handbook_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith(".pdf") and "handbook" in f.lower()]
        if potential_handbook_files:
            h_file = potential_handbook_files[0]
            with open(os.path.join(BASE_DIR, h_file), "rb") as f:
                pdf_bytes = f.read()
            cursor.execute("INSERT OR REPLACE INTO master_documents (doc_type, pdf_data, file_name, updated_at) VALUES ('handbook', ?, ?, CURRENT_TIMESTAMP)", (pdf_bytes, h_file))
    conn.commit()
    conn.close()

init_db()

def get_authorized_users_df():
    users_data = {ADMIN_EMAIL.lower(): ADMIN_PIN}
    access_file = os.path.join(BASE_DIR, "apps.access.xlsx")
    if os.path.exists(access_file):
        try:
            df_access = pd.read_excel(access_file)
            df_access.columns = [str(c).strip().lower() for c in df_access.columns]
            email_col = next((c for c in df_access.columns if 'email' in c), df_access.columns[0])
            pin_col = next((c for c in df_access.columns if 'pin' in c or 'code' in c), df_access.columns[1] if len(df_access.columns) > 1 else None)
            for _, row in df_access.iterrows():
                em = str(row[email_col]).strip().lower()
                if "@" in em:
                    pi = str(row[pin_col]).strip() if pin_col and pd.notna(row[pin_col]) else "1234"
                    if pi.endswith('.0'):
                        pi = pi[:-2]
                    users_data[em] = pi
        except Exception as e:
            print(f"Error reading apps.access.xlsx: {e}")
    return users_data

def verify_credentials(email, pin):
    if not email or "@" not in email or not pin:
        return False
    users_dict = get_authorized_users_df()
    clean_email = email.strip().lower()
    if clean_email in users_dict and users_dict[clean_email] == pin.strip():
        return True
    return False

def save_document_to_db(doc_type, uploaded_file):
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    pdf_bytes = uploaded_file.getvalue()
    cursor.execute("INSERT OR REPLACE INTO master_documents (doc_type, pdf_data, file_name, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)", (doc_type, pdf_bytes, uploaded_file.name))
    conn.commit()
    conn.close()

def delete_document_from_db(doc_type):
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM master_documents WHERE doc_type = ?", (doc_type,))
    conn.commit()
    conn.close()

def get_document_from_db(doc_type):
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("SELECT pdf_data, file_name FROM master_documents WHERE doc_type = ?", (doc_type,))
    row = cursor.fetchone()
    conn.close()
    return row

def save_grievance(email, grievant, date, articles, step, steward, committeeman, facts, remedy, image_name):
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO grievances (user_email, grievant, occ_date, articles, step, steward, committeeman, facts, remedy, evidence_image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (email.strip().lower(), grievant, date, articles, step, steward, committeeman, facts, remedy, image_name))
    conn.commit()
    conn.close()
    sync_db_to_excel()

def update_grievance(g_id, grievant, date, articles, step, steward, committeeman, facts, remedy):
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("UPDATE grievances SET grievant = ?, occ_date = ?, articles = ?, step = ?, steward = ?, committeeman = ?, facts = ?, remedy = ? WHERE id = ?", (grievant, date, articles, step, steward, committeeman, facts, remedy, g_id))
    conn.commit()
    conn.close()
    sync_db_to_excel()

def delete_grievance(g_id):
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM grievances WHERE id = ?", (g_id,))
    conn.commit()
    conn.close()
    sync_db_to_excel()

def load_grievances():
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    df = pd.read_sql_query("SELECT * FROM grievances ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def get_gemini_key():
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ.get("GEMINI_API_KEY")
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return st.sidebar.text_input("🔑 Gemini API Key (Admin Override)", type="password", value="")

current_time_str = datetime.now().strftime("%B %d, %Y — %I:%M:%S %p")
base_ticker = f"⚡ TACTICAL NET // NORTH CANTON, OH // LAT: 40.8786° N, LON: 81.4057° W // LOCAL TIME: {current_time_str} // SYSTEM CLEARANCE: SECURE ⚡"
ticker_text = (base_ticker + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; " + base_ticker) * 2

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #ffb700;'>⚡ USW // SPECIAL OPS TACTICAL COMMAND ⚡</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-family: monospace; color: #94a3b8; letter-spacing: 2px;'>RESTRICTED ACCESS // AUTHORIZED PERSONNEL ONLY</p>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ticker-wrap">
        <div class="ticker">{ticker_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='tech-card'>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("### 🔐 SECURE AUTHENTICATION GATEWAY")
            email_attempt = st.text_input("IDENT (Authorized Email):")
            pin_attempt = st.text_input("ACCESS PIN (4-Digit):", type="password", max_chars=4)
            login_submitted = st.form_submit_button("INITIALIZE SECURE LINK", type="primary", use_container_width=True)
            if login_submitted:
                if verify_credentials(email_attempt, pin_attempt):
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_attempt.strip().lower()
                    st.rerun()
                else:
                    st.error("[ERROR] Access Denied: Invalid credentials or unverified node.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- HEADER & TELEMETRY ---
st.markdown("<h1 style='color: #ffb700;'>⚡ USW // TACTICAL COMMAND CENTER</h1>", unsafe_allow_html=True)
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.markdown("<span class='status-badge'>🟢 ACTIVE NODE // " + st.session_state.user_email.upper() + " // LEVEL 5 CLEARANCE</span>", unsafe_allow_html=True)
with col_head2:
    if st.button("🔒 TERMINATE SESSION", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div class="ticker-wrap">
    <div class="ticker">{ticker_text}</div>
</div>
""", unsafe_allow_html=True)

api_key = get_gemini_key()
tab1, tab2, tab_safety, tab3 = st.tabs([
    "📖 AI INTELLIGENCE HUB", 
    "📋 GRIEVANCE PIPELINE", 
    "👥 SAFETY REPS & COMMITTEE", 
    "⚙️ SYSTEM ADMIN"
])

with tab1:
    st.subheader("Neural Contract & Policy Analyzer")
    contract_rec = get_document_from_db("contract")
    handbook_rec = get_document_from_db("handbook")
    benefits_rec = get_document_from_db("employee_benefits")
    
    col_status1, col_status2, col_status3 = st.columns(3)
    with col_status1:
        if contract_rec:
            st.markdown(f"<div class='tech-card'><b>Master Contract:</b><br><span style='color: #ffb700;'>{contract_rec[1]}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='tech-card' style='border-left: 3px solid #ef4444;'><b>Master Contract:</b> Not Synced</div>", unsafe_allow_html=True)
    with col_status2:
        if handbook_rec:
            st.markdown(f"<div class='tech-card'><b>Employee Handbook:</b><br><span style='color: #ffb700;'>{handbook_rec[1]}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='tech-card' style='border-left: 3px solid #64748b;'><b>Employee Handbook:</b> Optional Offline</div>", unsafe_allow_html=True)
    with col_status3:
        if benefits_rec:
            st.markdown(f"<div class='tech-card'><b>Employee Benefits:</b><br><span style='color: #ffb700;'>{benefits_rec[1]}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='tech-card' style='border-left: 3px solid #64748b;'><b>Employee Benefits:</b> Optional Offline</div>", unsafe_allow_html=True)

    search_scope = st.selectbox(
        "QUERY TARGET SCOPE",
        ["Master Contract Only", "Employee Handbook Only", "Employee Benefits Only", "All Documents Together"]
    )
    question = st.text_area("QUERY PARAMETERS", placeholder="e.g., What is the exact protocol for attendance point infractions or medical deductible coverage?")
    
    if st.button("EXECUTE NEURAL QUERY", type="primary"):
        if not api_key:
            st.warning("⚠️ Gemini API key is missing. Please configure it in Render Environment Variables.")
        elif not question:
            st.warning("⚠️ Please specify query parameters.")
        else:
            files_to_query = []
            if search_scope in ["Master Contract Only", "All Documents Together"] and contract_rec:
                files_to_query.append(("Master Contract", contract_rec[0]))
            if search_scope in ["Employee Handbook Only", "All Documents Together"] and handbook_rec:
                files_to_query.append(("Employee Handbook", handbook_rec[0]))
            if search_scope in ["Employee Benefits Only", "All Documents Together"] and benefits_rec:
                files_to_query.append(("Employee Benefits", benefits_rec[0]))
                
            if not files_to_query:
                st.warning("⚠️ Target document databases are empty.")
            else:
                try:
                    client = genai.Client(api_key=api_key.strip())
                    contents = []
                    for doc_label, pdf_bytes in files_to_query:
                        contents.append(types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"))
                        contents.append(f"[{doc_label} Attached]")
                    contents.append(f"Question: {question}")
                    
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
