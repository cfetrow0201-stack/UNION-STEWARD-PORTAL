import streamlit as st
import sqlite3
import pandas as pd
import os
import random
from datetime import datetime
from google import genai
from google.genai import types

# --- PAGE CONFIG & TACTICAL HUD STYLING ---
st.set_page_config(page_title="USW // TACTICAL COMMAND", page_icon="⚡", layout="wide")

# Custom CSS: Military Command / Tony Stark HUD Interface
st.markdown("""
<style>
.stApp {
    background-color: #03050a;
    background-image: 
        radial-gradient(circle at 50% 20%, rgba(255, 170, 0, 0.05) 0%, transparent 70%),
        linear-gradient(rgba(255, 170, 0, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 170, 0, 0.02) 1px, transparent 1px);
    background-size: 100% 100%, 25px 25px, 25px 25px;
    color: #e2e8f0;
}
h1, h2, h3 {
    font-family: 'Courier New', Courier, monospace;
    letter-spacing: 2px;
    color: #ffb700 !important;
    text-transform: uppercase;
    text-shadow: 0 0 12px rgba(255, 183, 0, 0.5);
}
.ticker-wrap {
    width: 100%;
    overflow: hidden;
    background-color: rgba(10, 15, 25, 0.95);
    border-top: 2px solid #ffb700;
    border-bottom: 2px solid #ffb700;
    padding: 8px 0;
    margin-bottom: 25px;
    box-shadow: inset 0 0 15px rgba(255, 183, 0, 0.15), 0 4px 20px rgba(0,0,0,0.8);
}
.ticker {
    display: inline-block;
    white-space: nowrap;
    animation: marquee 30s linear infinite;
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
.tech-card {
    background: rgba(13, 19, 33, 0.85);
    border: 1px solid rgba(255, 183, 0, 0.35);
    border-top: 3px solid #ffb700;
    padding: 20px;
    border-radius: 4px;
    margin-bottom: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8);
}
.status-badge {
    background-color: rgba(255, 183, 0, 0.1);
    border: 1px solid #ffb700;
    color: #ffb700;
    padding: 6px 14px;
    border-radius: 2px;
    font-family: monospace;
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 1.5px;
    box-shadow: 0 0 10px rgba(255, 183, 0, 0.3);
}
/* Tactical Stark-style Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #ffb700 !important;
    color: #ffb700 !important;
    font-family: 'Courier New', Courier, monospace !important;
    font-weight: bold !important;
    letter-spacing: 1.5px !important;
    border-radius: 3px !important;
    box-shadow: 0 0 10px rgba(255, 183, 0, 0.2);
    transition: all 0.2s ease-in-out;
}
.stButton > button:hover {
    background: #ffb700 !important;
    color: #03050a !important;
    box-shadow: 0 0 20px rgba(255, 183, 0, 0.6);
    transform: translateY(-1px);
}
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(10, 15, 25, 0.95);
    padding: 10px;
    border-radius: 4px;
    border: 1px solid rgba(255, 183, 0, 0.3);
}
.stTabs [data-baseweb="tab"] {
    color: #94a3b8;
    font-family: monospace;
    font-weight: bold;
    letter-spacing: 1px;
}
.stTabs [aria-selected="true"] {
    background-color: #1e293b !important;
    color: #ffb700 !important;
    border-top: 2px solid #ffb700 !important;
    box-shadow: inset 0 0 10px rgba(255, 183, 0, 0.2);
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
        UPDATE grievances 
        SET grievant = ?, occ_date = ?, articles = ?, step = ?, steward = ?, committeeman = ?, facts = ?, remedy = ?
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
base_ticker = f"⚡ TACTICAL HUD ONLINE: NORTH CANTON, OH &nbsp;&nbsp;|&nbsp;&nbsp; LOCAL TIME: {current_time_str} &nbsp;&nbsp;|&nbsp;&nbsp; AMBIENT TEMP: 44°F (CLEAR) &nbsp;&nbsp;|&nbsp;&nbsp; SYSTEM STATUS: SECURE & OPERATIONAL ⚡"
ticker_text = (base_ticker + " &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; " + base_ticker) * 2

if not st.session_state.logged_in:
    st.markdown("<h1 style='
