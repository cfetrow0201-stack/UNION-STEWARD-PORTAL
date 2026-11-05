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
    background: linear-gradient(135deg, #1e293b 0% , #0f172a 100%);
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
                INSERT OR REPLACE INTO master_documents (doc_type, pdf_data, file_name, updated_
