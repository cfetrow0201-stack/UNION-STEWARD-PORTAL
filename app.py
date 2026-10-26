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

# --- 3. SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# --- 1. SETUP DATABASE & AUTO-SYNC REPOSITORY PDFs ---
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
    
    # Auto-seed default authorized emails
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

# Auto-sync repository PDFs if they exist locally and aren't in the DB yet
def auto_sync_repo_files():
    repo_files = {
        "contract": "contract.pdf",
        "handbook": "handbook.pdf",
        "employee_benefits": "employee_benefits.pdf"
    }
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    for doc_type, filename in repo_files.items():
        cursor.execute("SELECT pdf_data FROM master_documents WHERE doc_type = ?", (doc_type,))
        res = cursor.fetchone()
        if not res and os.path.exists(filename):
            with open(filename, "rb") as f:
                pdf_bytes = f.read()
            cursor.execute('''
                INSERT OR REPLACE INTO master_documents (doc_type, pdf_data, file_name, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (doc_type, pdf_bytes, filename))
    conn.commit()
    conn.close()

auto_sync_repo_files()

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
    conn.commit()
    conn.close()

def delete_grievance(g_id):
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM grievances WHERE id = ?", (g_id,))
    conn.commit()
    conn.close()

def load_grievances():
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    df = pd.read_sql_query("SELECT * FROM grievances ORDER BY timestamp DESC", conn)
    conn.close()
    return df

# --- 2. GET API KEY SECURELY ---
def get_gemini_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return st.sidebar.text_input("🔑 Gemini API Key (Admin Override)", type="password", value="")

# Get live current time and formatted telemetry string
current_time_str = datetime.now().strftime("%B %d, %Y — %I:%M:%S %p")
ticker_text = f"⚡ LIVE TELEMETRY: NORTH CANTON, OH &nbsp;&nbsp;|&nbsp;&nbsp; LOCAL TIME: {current_time_str} &nbsp;&nbsp;|&nbsp;&nbsp; AMBIENT TEMP: 44°F (CLEAR) &nbsp;&nbsp;|&nbsp;&nbsp; SYSTEM STATUS: SECURE & OPERATIONAL ⚡"

# --- 4. LOGIN GATE (USW Terminal Style) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>🛡️ UNITED STEELWORKERS // COMMAND 🛡️</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-family: monospace; color: #94a3b8;'>SECURE STEWARD PORTAL // AUTHENTICATION REQUIRED</p>", unsafe_allow_html=True)
    
    st.markdown(f'''
        <div class="ticker-wrap">
            <div class="ticker">{ticker_text}</div>
        </div>
    ''', unsafe_allow_html=True)
    
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

# --- 5. MAIN APP INTERFACE ---
st.markdown("<h1 style='color: #FFD700;'>🛡️ USW // STEWARD COMMAND CENTER</h1>", unsafe_allow_html=True)
st.markdown(f"<span class='status-badge'>🟢 ACTIVE SESSION // {st.session_state.user_email.upper()}</span>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

st.markdown(f'''
    <div class="ticker-wrap">
        <div class="ticker">{ticker_text}</div>
    </div>
''', unsafe_allow_html=True)

api_key = get_gemini_key()

tab1, tab2, tab_safety, tab3 = st.tabs([
    "📖 AI INTELLIGENCE HUB", 
    "📋 GRIEVANCE PIPELINE", 
    "👥 Union Safety Rep & Union Safety Committee", 
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
            st.markdown(f"<div class='tech-card'>📂 <b>Master Contract:</b><br>{contract_rec[1]}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='tech-card' style='border-left-color: #ef4444;'>⚠️ <b>Master Contract:</b> Not Synced</div>", unsafe_allow_html=True)
            
    with col_status2:
        if handbook_rec:
            st.markdown(f"<div class='tech-card'>📂 <b>Employee Handbook:</b><br>{handbook_rec[1]}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='tech-card' style='border-left-color: #94a3b8;'>ℹ️ <b>Employee Handbook:</b> Optional Offline</div>", unsafe_allow_html=True)

    with col_status3:
        if benefits_rec:
            st.markdown(f"<div class='tech-card'>📂 <b>Employee Benefits:</b><br>{benefits_rec[1]}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='tech-card' style='border-left-color: #94a3b8;'>ℹ️ <b>Employee Benefits:</b> Optional Offline</div>", unsafe_allow_html=True)

    search_scope = st.selectbox(
        "QUERY TARGET SCOPE", 
        ["Master Contract Only", "Employee Handbook Only", "Employee Benefits Only", "All Documents Together"]
    )
    
    question = st.text_area("QUERY PARAMETERS", placeholder="e.g., What is the exact protocol for attendance point infractions or medical deductible coverage?")
    
    if st.button("EXECUTE NEURAL QUERY", type="primary"):
        if not api_key:
            st.warning("⚠️ Gemini API key is missing. Please configure it in Streamlit Secrets.")
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
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction="You are an advanced tactical USW union contract and policy analyst assisting shop stewards. Provide precise, authoritative answers with exact article, section, and benefit plan citations.",
                            temperature=0.2
                        )
                    )
                    st.markdown("### INTELLIGENCE OUTPUT:")
                    st.markdown(f"<div class='tech-card'>{response.text}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Neural connection error: {e}")

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Log New Grievance Record")
        with st.form("grievance_form"):
            g_name = st.text_input("Grievant Name & Department")
            g_date = st.text_input("Date of Occurrence")
            g_articles = st.text_input("Contract Article(s) Violated")
            g_step = st.selectbox("Current Step", ["Step 1 (Supervisor)", "Step 2 (HR / Dept Head)", "Step 3 (Plant Mgr)", "Arbitration"])
            g_steward = st.text_input("Assigned Steward")
            g_committeeman = st.text_input("Assigned Grievance Committeeman")
            g_facts = st.text_area("Statement of Facts / Notes")
            g_remedy = st.text_area("Remedy Demanded")
            uploaded_image = st.file_uploader("Upload Evidence / Documentation", type=["png", "jpg", "jpeg"])
            
            submitted = st.form_submit_button("COMMIT TO PIPELINE", type="primary")
            if submitted:
                if not g_name or not g_articles:
                    st.error("⚠️ Grievant Name and Article(s) are required fields.")
                else:
                    img_name = uploaded_image.name if uploaded_image else "No Image"
                    save_grievance(st.session_state.user_email, g_name, g_date, g_articles, g_step, g_steward, g_committeeman, g_facts, g_remedy, img_name)
                    st.success(f"✅ Grievance logged successfully!")
                    st.rerun()

    with col2:
        st.subheader("Active Pipeline Telemetry")
        df = load_grievances()
        if not df.empty:
            st.dataframe(df[["id", "user_email", "grievant", "occ_date", "articles", "step", "steward", "committeeman", "timestamp"]], use_container_width=True)
        else:
            st.info("Pipeline telemetry empty.")

with tab_safety:
    st.subheader("👥 Union Safety Rep & Union Safety Committee")
    st.markdown("<p style='color: #94a3b8; font-family: monospace;'>Official Plant Safety Committee Directory & Plant FAP Contacts (Rev. 8/31/2026)</p>", unsafe_allow_html=True)
    
    safety_data = [
        # Harrison Steel Plant "HSP" (1835 Dueber Avenue S.W., Canton OH 44706)
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Sean Els - Safety Committee Chair - USR, Training", "Clock #": "001-002", "Turn": "Days", "Crew": "", "Phone": "(330) 495-7614", "Email": "sean.l.els@metallus.com (Work ext. 2913)"},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Scott Mathie - USR, Training", "Clock #": "001-800", "Turn": "Days", "Crew": "", "Phone": "(330) 412-6508", "Email": "robert.s.mathie@metallus.com (Work ext. 3967)"},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Curtis Green - USR, Compliance", "Clock #": "001-502", "Turn": "Days", "Crew": "", "Phone": "(330) 949-5148", "Email": "curtis.e.green@metallus.com (Work ext. 4716)"},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Tim Johnson - USR, Plant & Shops", "Clock #": "001-003", "Turn": "Days", "Crew": "", "Phone": "(330) 933-0824", "Email": "timothy.j.johnson@metallus.com (Work ext. 5026)"},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Chad Steiner - Machine Shop", "Clock #": "181-062", "Turn": "Days", "Crew": "", "Phone": "(740) 391-0555", "Email": ""},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Dave Ramsey - Finishing", "Clock #": "133-022", "Turn": "4", "Crew": "B", "Phone": "(330) 265-7701", "Email": ""},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Brad Holston - Equipment Rebuild", "Clock #": "181-001", "Turn": "Days", "Crew": "", "Phone": "(330) 347-1188", "Email": ""},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Steve Carlisle - Weld Shop", "Clock #": "181-505", "Turn": "Days", "Crew": "", "Phone": "(330) 340-0876", "Email": ""},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Seth McKenzie - Finishing", "Clock #": "133-029", "Turn": "4", "Crew": "C", "Phone": "(330) 232-5536", "Email": ""},

        # Faircrest Steel Plant "FSP" (4511 Faircrest Street S.W., Canton OH 44706)
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "John Lidderdale - USR, Steelmaking", "Clock #": "001-801", "Turn": "Days", "Crew": "", "Phone": "(330) 209-1254", "Email": "john.t.lidderdale@metallus.com (Work ext. 4682)"},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Mike Henderson - USR, Steel Processing", "Clock #": "001-804", "Turn": "Days", "Crew": "", "Phone": "(330) 428-2503", "Email": "michael.l.henderson@metallus.com (Work ext. 7360)"},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Chuck Fetrow - BC", "Clock #": "250-084", "Turn": "3", "Crew": "C", "Phone": "(330) 488-4765", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Mike Kiser - Mech. Maint. Rolling Mill", "Clock #": "282-012", "Turn": "4", "Crew": "B", "Phone": "(330) 934-1190", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Jeff Thomas - Rolling Mill", "Clock #": "282-040", "Turn": "4", "Crew": "B", "Phone": "(330) 446-8285", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Adam Holland - Caster", "Clock #": "227-025", "Turn": "Days", "Crew": "", "Phone": "(330) 904-8489", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Daryl Smith - BC", "Clock #": "250-025", "Turn": "3", "Crew": "C", "Phone": "(330) 418-6012", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Alan Tack - Chem Lab", "Clock #": "008-003", "Turn": "4", "Crew": "B", "Phone": "(330) 323-5315", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Alex Rue - EAF", "Clock #": "218-054", "Turn": "4", "Crew": "C", "Phone": "(330) 606-5792", "Email": ""},
        {"Plant / Location": "Faircrest Steel Plant (FSP)", "Name / Area": "Brandon Bartrug - EAF", "Clock #": "218-058", "Turn": "Days", "Crew": "", "Phone": "(740) 391-0109", "Email": ""},

        # Gambrinus Steel Plant "GSP" (2401 Gambrinus Road S.W., Canton OH 44706)
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Brock McDevitt - USR, Tube Mills & Thermal Treat", "Clock #": "001-500", "Turn": "Days", "Crew": "", "Phone": "(330) 432-0705", "Email": "brock.a.mcdevitt@metallus.com (Work ext. 4249)"},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Shawn Lindner - USR, Finishing & Logistics", "Clock #": "001-501", "Turn": "Days", "Crew": "", "Phone": "(330) 575-4435", "Email": "shawn.lindner@metallus.com (Work ext. 5083)"},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Carrie Holland - IFL", "Clock #": "752-408", "Turn": "4", "Crew": "D", "Phone": "(330) 933-6620", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Mike Kemp - 5 Tube Mill", "Clock #": "750-041", "Turn": "3", "Crew": "A", "Phone": "(330) 268-6375", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Jason Ensinger - 3TM", "Clock #": "750-306", "Turn": "2", "Crew": "H", "Phone": "(330) 956-0178", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Ed Smith - IFL", "Clock #": "752-002", "Turn": "Days", "Crew": "", "Phone": "(330) 949-7623", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Jon Burdge - Logistics, Shipping", "Clock #": "190-078", "Turn": "Days", "Crew": "", "Phone": "(330) 224-2778", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Marty Gugov - Logistics, Shipping", "Clock #": "190-019", "Turn": "2", "Crew": "B", "Phone": "(330) 437-5967", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Ken Rayburn - Logistics, Shipping", "Clock #": "190-036", "Turn": "4", "Crew": "C", "Phone": "(330) 809-3183", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Alex Hunt - Quench/Temper", "Clock #": "756-025", "Turn": "3", "Crew": "B", "Phone": "(330) 413-4839", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Joe Plott - Thermal Treat, Islands", "Clock #": "185-527", "Turn": "4", "Crew": "C", "Phone": "(330) 428-17
