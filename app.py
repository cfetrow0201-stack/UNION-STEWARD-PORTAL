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
    /* Global Deep Cyber Theme with Glowing Grid Overlay */
    .stApp {
        background-color: #060913;
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(255, 215, 0, 0.08) 0%, transparent 60%),
            linear-gradient(rgba(255, 215, 0, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 215, 0, 0.04) 1px, transparent 1px);
        background-size: 100% 100%, 35px 35px, 35px 35px;
        color: #f8fafc;
    }
    
    /* Headers & Typography (High-Visibility USW Gold) */
    h1, h2, h3 {
        font-family: 'Courier New', Courier, monospace;
        letter-spacing: 1.5px;
        color: #FFD700 !important;
        text-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
    }
    
    /* Scrolling High-Tech Ticker Bar */
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
        0%   { transform: translate3d(100%, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }
    
    /* Industrial Glass Cards with Glowing Border */
    .tech-card {
        background: rgba(11, 17, 32, 0.92);
        border: 1px solid rgba(255, 215, 0, 0.3);
        border-left: 5px solid #FFD700;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.7), inset 0 0 15px rgba(255, 215, 0, 0.03);
    }
    
    /* USW Active Badge with Neon Glow */
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
    
    /* Streamlit Tabs Adjustments */
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

# --- 3. SESSION STATE INITIALIZATION (Must be early) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# --- 1. SETUP DATABASE & MIGRATIONS (with timeout for multi-device safety) ---
def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    
    cursor.execute('''
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
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authorized_emails (
            email TEXT PRIMARY KEY,
            pin TEXT
        )
    ''')
    
    cursor.execute("PRAGMA table_info(authorized_emails)")
    columns = [col[1] for col in cursor.fetchall()]
    if "pin" not in columns:
        cursor.execute("ALTER TABLE authorized_emails ADD COLUMN pin TEXT")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_documents (
            doc_type TEXT PRIMARY KEY,
            pdf_data BLOB,
            file_name TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM authorized_emails")
    count = cursor.fetchone()[0]
    if count == 0:
        default_data = [
            (ADMIN_EMAIL, ADMIN_PIN),
            ("admin@union.org", "1234"),
            ("steward1@union.org", "5678")
        ]
        for email, pin in default_data:
            cursor.execute("INSERT OR IGNORE INTO authorized_emails (email, pin) VALUES (?, ?)", (email, pin))
            
    cursor.execute("INSERT OR REPLACE INTO authorized_emails (email, pin) VALUES (?, ?)", (ADMIN_EMAIL.lower(), ADMIN_PIN))
    
    cursor.execute("SELECT email FROM authorized_emails WHERE pin IS NULL OR pin = ''")
    empty_pin_rows = cursor.fetchall()
    for row in empty_pin_rows:
        rand_pin = f"{random.randint(0, 9999):04d}"
        cursor.execute("UPDATE authorized_emails SET pin = ? WHERE email = ?", (rand_pin, row[0]))

    conn.commit()
    conn.close()

init_db()

def verify_credentials(email, pin):
    if not email or "@" not in email or not pin:
        return False
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("SELECT pin FROM authorized_emails WHERE email = ?", (email.strip().lower(),))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == pin.strip():
            return True
    except Exception:
        pass
    return False

def add_authorized_email(email):
    clean_email = email.strip().lower()
    random_pin = f"{random.randint(0, 9999):04d}"
    
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO authorized_emails (email, pin) VALUES (?, ?)", (clean_email, random_pin))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success

def save_document_to_db(doc_type, uploaded_file):
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    pdf_bytes = uploaded_file.getvalue()
    cursor.execute('''
        INSERT OR REPLACE INTO master_documents (doc_type, pdf_data, file_name, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (doc_type, pdf_bytes, uploaded_file.name))
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
    cursor.execute('''
        INSERT INTO grievances (user_email, grievant, occ_date, articles, step, steward, committeeman, facts, remedy, evidence_image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (email.strip().lower(), grievant, date, articles, step, steward, committeeman, facts, remedy, image_name))
    conn.commit()
    conn.close()

def update_grievance(g_id, grievant, date, articles, step, steward, committeeman, facts, remedy):
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE grievances 
        SET grievant = ?, occ_date = ?, articles = ?, step = ?, steward = ?, committeeman = ?, facts = ?, remedy = ?
        WHERE id = ?
    ''', (grievant, date, articles, step, steward, committeeman, facts, remedy, g_id))
    conn
