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
base_ticker = f"⚡ TACTICAL HUD ONLINE: NORTH CANTON, OH | LOCAL TIME: {current_time_str} | AMBIENT TEMP: 44°F (CLEAR) | SYSTEM STATUS: SECURE & OPERATIONAL ⚡"
ticker_text = (base_ticker + "        " + base_ticker) * 2

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #ffb700;'>⚡ USW // TACTICAL COMMAND ⚡</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-family: monospace; color: #94a3b8;'>SECURE STEWARD PORTAL // AUTHORIZATION REQUIRED</p>", unsafe_allow_html=True)
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

st.markdown("<h1 style='color: #ffb700;'>⚡ USW // TACTICAL COMMAND CENTER</h1>", unsafe_allow_html=True)
st.markdown("<span class='status-badge'>🟢 ACTIVE SESSION // " + st.session_state.user_email.upper() + "</span>", unsafe_allow_html=True)
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
            st.markdown(f"<div class='tech-card'><b>Master Contract:</b><br>{contract_rec[1]}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='tech-card' style='border-left-color: #ef4444;'><b>Master Contract:</b> Not Synced</div>", unsafe_allow_html=True)
    with col_status2:
        if handbook_rec:
            st.markdown(f"<div class='tech-card'><b>Employee Handbook:</b><br>{handbook_rec[1]}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='tech-card' style='border-left-color: #94a3b8;'><b>Employee Handbook:</b> Optional Offline</div>", unsafe_allow_html=True)
    with col_status3:
        if benefits_rec:
            st.markdown(f"<div class='tech-card'><b>Employee Benefits:</b><br>{benefits_rec[1]}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='tech-card' style='border-left-color: #94a3b8;'><b>Employee Benefits:</b> Optional Offline</div>", unsafe_allow_html=True)

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
                    img_name = uploaded_image.name if uploaded_image is not None else "No Image"
                    save_grievance(st.session_state.user_email, g_name, g_date, g_articles, g_step, g_steward, g_committeeman, g_facts, g_remedy, img_name)
                    st.success("✅ Grievance logged & automatically backed up to Excel!")
                    st.rerun()

    with col2:
        st.subheader("Active Pipeline Telemetry")
        if st.button("🔄 Sync Pipeline from Excel Backup"):
            if restore_db_from_excel():
                st.success("✅ Successfully pulled all records from 'grievance_backup.xlsx'!")
                st.rerun()
            else:
                st.warning("⚠️ No valid 'grievance_backup.xlsx' file found in root.")
                
        df = load_grievances()
        if not df.empty:
            st.dataframe(df[["id", "user_email", "grievant", "occ_date", "articles", "step", "steward", "committeeman", "timestamp"]], use_container_width=True)
        else:
            st.info("Pipeline telemetry empty.")

with tab_safety:
    st.subheader("👥 Union Safety Rep & Union Safety Committee")
    st.markdown("Official Plant Safety Committee Directory & Plant FAP Contacts (Rev. 8/31/2026)")
    safety_data = [
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Sean Els - Safety Committee Chair - USR, Training", "Clock #": "001-002", "Turn": "Days", "Crew": "", "Phone": "(330) 495-7614", "Email": "sean.l.els@metallus.com (Work ext. 2913)"},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Scott Mathie - USR, Training", "Clock #": "001-800", "Turn": "Days", "Crew": "", "Phone": "(330) 412-6508", "Email": "robert.s.mathie@metallus.com (Work ext. 3967)"},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Curtis Green - USR, Compliance", "Clock #": "001-502", "Turn": "Days", "Crew": "", "Phone": "(330) 949-5148", "Email": "curtis.e.green@metallus.com (Work ext. 4716)"},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Tim Johnson - USR, Plant & Shops", "Clock #": "001-003", "Turn": "Days", "Crew": "", "Phone": "(330) 933-0824", "Email": "timothy.j.johnson@metallus.com (Work ext. 5026)"},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Chad Steiner - Machine Shop", "Clock #": "181-062", "Turn": "Days", "Crew": "", "Phone": "(740) 391-0555", "Email": ""},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Dave Ramsey - Finishing", "Clock #": "133-022", "Turn": "4", "Crew": "B", "Phone": "(330) 265-7701", "Email": ""},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Brad Holston - Equipment Rebuild", "Clock #": "181-001", "Turn": "Days", "Crew": "", "Phone": "(330) 347-1188", "Email": ""},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Steve Carlisle - Weld Shop", "Clock #": "181-505", "Turn": "Days", "Crew": "", "Phone": "(330) 340-0876", "Email": ""},
        {"Plant / Location": "Harrison Steel Plant (HSP)", "Name / Area": "Seth McKenzie - Finishing", "Clock #": "133-029", "Turn": "4", "Crew": "C", "Phone": "(330) 232-5536", "Email": ""},
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
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Joe Plott - Thermal Treat, Islands", "Clock #": "185-527", "Turn": "4", "Crew": "C", "Phone": "(330) 428-1716", "Email": ""},
        {"Plant / Location": "Gambrinus Steel Plant (GSP)", "Name / Area": "Marc Armstead - Met Lab", "Clock #": "007-021", "Turn": "2", "Crew": "Midnights", "Phone": "(330) 844-6363", "Email": ""},
        {"Plant / Location": "FAP Leads - Plant", "Name / Area": "Carrie Holland - GSP, IFL", "Clock #": "752-408", "Turn": "Days", "Crew": "", "Phone": "(330) 933-6620", "Email": ""},
        {"Plant / Location": "FAP Leads - Plant", "Name / Area": "Chuck Fetrow - FSP, BC", "Clock #": "250-084", "Turn": "3", "Crew": "A", "Phone": "(330) 488-4765", "Email": ""},
        {"Plant / Location": "FAP Leads - Plant", "Name / Area": "Greg Smith - HSP, Machine Shop", "Clock #": "181-025", "Turn": "Days", "Crew": "", "Phone": "(330) 437-8015", "Email": ""}
    ]
    df_safety = pd.DataFrame(safety_data)
    search_term = st.text_input("🔍 Search Directory by Name, Plant, or Area:", "")
    if search_term:
        mask = df_safety.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
        df_filtered = df_safety[mask]
    else:
        df_filtered = df_safety
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

with tab3:
    if st.session_state.user_email == ADMIN_EMAIL.lower():
        st.subheader("⚙️ SYSTEM ADMIN // REPOSITORY CONTROL")
        st.markdown("#### Pipeline Data Backup Status")
        st.markdown(f"The app automatically syncs all grievances live to `{BACKUP_FILE}` in the server root whenever a record is logged, updated, or deleted.")
        
        df_all_grievances = load_grievances()
        if not df_all_grievances.empty:
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_all_grievances.to_excel(writer, index=False, sheet_name='Grievances')
            excel_data = output.getvalue()
            st.download_button(
                label="📥 DOWNLOAD MANUAL BACKUP COPY",
                data=excel_data,
                file_name="grievance_backup.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.info("No grievances logged yet.")
            
        st.markdown("---")
        col_doc1, col_doc2, col_doc3 = st.columns(3)
        with col_doc1:
            st.markdown("#### Master Contract (CBA)")
            c_rec = get_document_from_db("contract")
            if c_rec:
                st.success(f"✅ Synced: **{c_rec[1]}**")
                if st.button("🗑️ Purge Master Contract", key="del_contract"):
                    delete_document_from_db("contract")
                    st.success("Contract purged.")
                    st.rerun()
            else:
                st.warning("Repository Empty.")
            new_contract = st.file_uploader("Upload / Overwrite Master Contract (PDF)", type=["pdf"], key="upload_c")
            if new_contract:
                save_document_to_db("contract", new_contract)
                st.success("✅ Master Contract locked into database!")
                st.rerun()
                
        with col_doc2:
            st.markdown("#### Employee Handbook")
            h_rec = get_document_from_db("handbook")
            if
