import streamlit as st
import sqlite3
import pandas as pd
import os
import random
from datetime import datetime
from google import genai
from google.genai import types

# --- PAGE CONFIG & ENHANCED CYBER STYLING ---
st.set_page_config(page_title="USW // COMMAND CENTER", page_icon="🛡️", layout="wide")

# Custom CSS with Scrolling Marquee Ticker & Glowing Cyber Grid
st.markdown("""
<style>
.stApp {
    background-color: #060913;
    background-image: radial-gradient(circle at 50% 0%, rgba(255, 215, 0, 0.08) 0%, transparent 60%), linear-gradient(rgba(255, 215, 0, 0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 215, 0, 0.04) 1px, transparent 1px);
    background-size: 100% 100%, 35px 35px, 35px 35px;
    color: #f8fafc;
}
h1, h2, h3 {
    font-family: 'Courier New', Courier, monospace;
    letter-spacing: 1.5px;
    color: #FFD700 !important;
    text-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
}
.ticker-wrap {
    width: 100%;
    overflow: hidden;
    background-color: rgba(11, 17, 32, 0.95);
    border: 1px solid rgba(255, 215, 0, 0.4);
    border-left: 5px solid #FFD700;
    border-right: 5px solid #FFD700;
    padding: 10px 0;
    border-radius: 6px;
    margin-bottom: 25px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.6);
}
.ticker {
    display: inline-block;
    white-space: nowrap;
    animation: marquee 25s linear infinite;
    font-family: 'Courier New', Courier, monospace;
    color: #FFD700;
    font-weight: bold;
    font-size: 14px;
    letter-spacing: 2px;
}
@keyframes marquee {
    0%   { transform: translate3d(0, 0, 0); }
    100% { transform: translate3d(-50%, 0, 0); }
}
.tech-card {
    background: rgba(11, 17, 32, 0.92);
    border: 1px solid rgba(255, 215, 0, 0.3);
    border-left: 5px solid #FFD700;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.7), inset 0 0 15px rgba(255, 215, 0, 0.03);
}
.status-badge {
    background-color: rgba(255, 215, 0, 0.15);
    border: 1px solid #FFD700;
    color: #FFD700;
    padding: 6px 14px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 13px;
    font-weight: bold;
    box-shadow: 0 0 12px rgba(255, 215, 0, 0.25);
}
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
    background-color: rgba(11, 17, 32, 0.95);
    padding: 10px;
    border-radius: 8px;
    border: 1px solid rgba(255, 215, 0, 0.2);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}
.stTabs [data-baseweb="tab"] {
    color: #94a3b8;
    font-family: monospace;
    font-weight: bold;
}
.stTabs [aria-selected="true"] {
    background-color: #1e293b !important;
    color: #FFD700 !important;
    border-bottom: 2px solid #FFD700 !important;
    box-shadow: 0 0 15px rgba(255, 215, 0, 0.3);
}
</style>
""", unsafe_allow_html=True)

DB_NAME = "union_grievances.db"
ADMIN_EMAIL = "cfetrow0201@gmail.com"
ADMIN_PIN = "4812"

# Robust absolute pathing for root-level backup file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BACKUP_FILE = os.path.join(BASE_DIR, "grievance_backup.xlsx")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

def sync_db_to_excel():
    """Dumps all current database records into grievance_backup.xlsx automatically"""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        df = pd.read_sql_query("SELECT * FROM grievances", conn)
        conn.close()
        df.to_excel(BACKUP_FILE, index=False)
    except Exception as e:
        print(f"Error syncing to Excel: {e}")

def restore_db_from_excel():
    """Pulls all rows from grievance_backup.xlsx and re-inserts them into SQLite"""
    if os.path.exists(BACKUP_FILE):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            cursor = conn.cursor()
            df_backup = pd.read_excel(BACKUP_FILE)
            for _, row in df_backup.iterrows():
                # Check if this grievance already exists by checking details to avoid exact duplicates
                cursor.execute("""
                    SELECT COUNT(*) FROM grievances 
                    WHERE grievant = ? AND occ_date = ? AND articles = ?
                """, (str(row.get("grievant", "")), str(row.get("occ_date", "")), str(row.get("articles", ""))))
                
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                        INSERT INTO grievances (user_email, grievant, occ_date, articles, step, steward, committeeman, facts, remedy, evidence_image, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row.get("user_email", "")),
                        str(row.get("grievant", "")),
                        str(row.get("occ_date", "")),
                        str(row.get("articles", "")),
                        str(row.get("step", "")),
                        str(row.get("steward", "")),
                        str(row.get("committeeman", "")),
                        str(row.get("facts", "")),
                        str(row.get("remedy", "")),
                        str(row.get("evidence_image", "No Image")),
                        str(row.get("timestamp", datetime.now()))
                    ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error restoring from Excel: {e}")
            return False

def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grievances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            grievant TEXT,
            occ_date TEXT,
            articles TEXT,
            step TEXT,
            steward TEXT,
            committeeman TEXT,
            facts TEXT,
            remedy TEXT,
            evidence_image TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Auto-recovery on boot
    cursor.execute("SELECT COUNT(*) FROM grievances")
    if cursor.fetchone()[0] == 0:
        restore_db_from_excel()
        
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS master_documents (
            doc_type TEXT PRIMARY KEY,
            pdf_data BLOB,
            file_name TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM master_documents WHERE doc_type = 'contract'")
    if cursor.fetchone()[0] == 0:
        potential_contract_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith(".pdf") and ("bla" in f.lower() or "contract" in f.lower())]
        if potential_contract_files:
            c_file = potential_contract_files[0]
            with open(os.path.join(BASE_DIR, c_file), "rb") as f:
                pdf_bytes = f.read()
            cursor.execute("""
                INSERT OR REPLACE INTO master_documents (doc_type, pdf_data, file_name, updated_at)
                VALUES ('contract', ?, ?, CURRENT_TIMESTAMP)
            """, (pdf_bytes, c_file))
            
    cursor.execute("SELECT COUNT(*) FROM master_documents WHERE doc_type = 'handbook'")
    if cursor.fetchone()[0] == 0:
        potential_handbook_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith(".pdf") and "handbook" in f.lower()]
        if potential_handbook_files:
            h_file = potential_handbook_files[0]
            with open(os.path.join(BASE_DIR, h_file), "rb") as f:
                pdf_bytes = f.read()
            cursor.execute("""
                INSERT OR REPLACE INTO master_documents (doc_type, pdf_data, file_name, updated_at)
                VALUES ('handbook', ?, ?, CURRENT_TIMESTAMP)
            """, (pdf_bytes, h_file))
            
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
    cursor.execute("""
        INSERT OR REPLACE INTO master_documents (doc_type, pdf_data, file_name, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (doc_type, pdf_bytes, uploaded_file.name))
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
    cursor.execute("""
        INSERT INTO grievances (user_email, grievant, occ_date, articles, step, steward, committeeman, facts, remedy, evidence_image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (email.strip().lower(), grievant, date, articles, step, steward, committeeman, facts, remedy, image_name))
    conn.commit()
    conn.close()
    sync_db_to_excel()

def update_grievance(g_id, grievant, date, articles, step, steward, committeeman, facts, remedy):
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE grievances SET grievant = ?, occ_date = ?, articles = ?, step = ?, steward = ?, committeeman = ?, facts = ?, remedy = ?
        WHERE id = ?
    """, (grievant, date, articles, step, steward, committeeman, facts, remedy, g_id))
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
base_ticker = f"⚡ LIVE TELEMETRY: NORTH CANTON, OH &nbsp;&nbsp;|&nbsp;&nbsp; LOCAL TIME: {current_time_str} &nbsp;&nbsp;|&nbsp;&nbsp; AMBIENT TEMP: 44°F (CLEAR) &nbsp;&nbsp;|&nbsp;&nbsp; SYSTEM STATUS: SECURE & OPERATIONAL ⚡"
ticker_text = (base_ticker + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; " + base_ticker) * 2

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>🛡️ UNITED STEELWORKERS // COMMAND 🛡️</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-family: monospace; color: #94a3b8;'>SECURE STEWARD PORTAL // AUTHENTICATION REQUIRED</p>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ticker-wrap">
        <div class="ticker">{ticker_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            email_attempt = st.text_input("IDENT (Authorized Email):")
            pin_attempt = st.text_input("ACCESS PIN (4-Digit):", type="password", max_chars=4)
            login_submitted = st.form_submit_button("INITIALIZE SECURE SESSION", type="primary", use_container_width=True)
            if login_submitted:
                if verify_credentials(email_attempt, pin_attempt):
                    st.session_state.logged_in = True
                    st.session_state.user_email = email_attempt.strip().lower()
                    st.rerun()
                else:
                    st.error("[ERROR] Access Denied: Invalid credentials.")
    st.stop()

st.markdown("<h1 style='color: #FFD700;'>🛡️ USW // STEWARD COMMAND CENTER</h1>", unsafe_allow_html=True)
st.markdown("<span class='status-badge'>🟢 ACTIVE SESSION // " + st.session_state.user_email.upper() + "</span>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div class="ticker-wrap">
    <div class="ticker">{ticker_text}</div>
</div>
""", unsafe_allow_html=True)

api_key = get_gemini_key()
tab1, tab2, tab_safety, tab3 = st.tabs(["📖 AI INTELLIGENCE HUB", "📋 GRIEVANCE PIPELINE", "👥 Union Safety Rep & Union Safety Committee", "⚙️ SYSTEM ADMIN"])
