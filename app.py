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

# Custom CSS with Glowing Cyber Grid & High-Contrast Visuals
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

# --- 1. SETUP DATABASE & MIGRATIONS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT pin FROM authorized_emails WHERE email = ?", (email.strip().lower(),))
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0] == pin.strip():
        return True
    return False

def add_authorized_email(email):
    clean_email = email.strip().lower()
    random_pin = f"{random.randint(0, 9999):04d}"
    
    conn = sqlite3.connect(DB_NAME)
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    pdf_bytes = uploaded_file.getvalue()
    cursor.execute('''
        INSERT OR REPLACE INTO master_documents (doc_type, pdf_data, file_name, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (doc_type, pdf_bytes, uploaded_file.name))
    conn.commit()
    conn.close()

def delete_document_from_db(doc_type):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM master_documents WHERE doc_type = ?", (doc_type,))
    conn.commit()
    conn.close()

def get_document_from_db(doc_type):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT pdf_data, file_name FROM master_documents WHERE doc_type = ?", (doc_type,))
    row = cursor.fetchone()
    conn.close()
    return row

def save_grievance(email, grievant, date, articles, step, steward, committeeman, facts, remedy, image_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO grievances (user_email, grievant, occ_date, articles, step, steward, committeeman, facts, remedy, evidence_image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (email.strip().lower(), grievant, date, articles, step, steward, committeeman, facts, remedy, image_name))
    conn.commit()
    conn.close()

def update_grievance(g_id, grievant, date, articles, step, steward, committeeman, facts, remedy):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE grievances 
        SET grievant = ?, occ_date = ?, articles = ?, step = ?, steward = ?, committeeman = ?, facts = ?, remedy = ?
        WHERE id = ?
    ''', (grievant, date, articles, step, steward, committeeman, facts, remedy, g_id))
    conn.commit()
    conn.close()

def delete_grievance(g_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM grievances WHERE id = ?", (g_id,))
    conn.commit()
    conn.close()

def load_grievances():
    conn = sqlite3.connect(DB_NAME)
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

# --- 3. SESSION STATE FOR LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""

# --- 4. LOGIN GATE (USW Terminal Style) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>🛡️ UNITED STEELWORKERS // COMMAND 🛡️</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-family: monospace; color: #94a3b8;'>SECURE STEWARD PORTAL // AUTHENTICATION REQUIRED</p>", unsafe_allow_html=True)
    
    st.image("https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?auto=format&fit=crop&w=1200&q=80", use_container_width=True)
    
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

st.image("https://images.unsplash.com/photo-1504917595217-d4dc5ebe6122?auto=format&fit=crop&w=1400&q=80", use_container_width=True)
st.markdown("<br>", unsafe_allow_html=True)

api_key = get_gemini_key()

tab1, tab2, tab3 = st.tabs(["📖 AI INTELLIGENCE HUB", "📋 GRIEVANCE PIPELINE", "⚙️ SYSTEM ADMIN"])

with tab1:
    st.subheader("Neural Contract & Policy Analyzer")
    
    contract_rec = get_document_from_db("contract")
    handbook_rec = get_document_from_db("handbook")
    
    col_status1, col_status2 = st.columns(2)
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

    search_scope = st.selectbox(
        "QUERY TARGET SCOPE", 
        ["Master Contract Only", "Employee Handbook Only", "Both Documents Together"]
    )
    
    question = st.text_area("QUERY PARAMETERS", placeholder="e.g., What is the exact protocol for attendance point infractions?")
    
    if st.button("EXECUTE NEURAL QUERY", type="primary"):
        if not api_key:
            st.warning("⚠️ Gemini API key is missing. Please configure it in Streamlit Secrets.")
        elif not question:
            st.warning("⚠️ Please specify query parameters.")
        else:
            files_to_query = []
            if search_scope in ["Master Contract Only", "Both Documents Together"] and contract_rec:
                files_to_query.append(("Master Contract", contract_rec[0]))
            if search_scope in ["Employee Handbook Only", "Both Documents Together"] and handbook_rec:
                files_to_query.append(("Employee Handbook", handbook_rec[0]))
                
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
                            system_instruction="You are an advanced tactical USW union contract and policy analyst assisting shop stewards. Provide precise, authoritative answers with exact article and section citations.",
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

with tab3:
    if st.session_state.user_email == ADMIN_EMAIL.lower():
        st.subheader("⚙️ SYSTEM ADMIN // REPOSITORY CONTROL")
        
        col_doc1, col_doc2 = st.columns(2)
        
        with col_doc1:
            st.markdown("#### Master Contract (CBA)")
            c_rec = get_document_from_db("contract")
            if c_rec:
                st.success(f"📌 Synced: **{c_rec[1]}**")
                if st.button("🗑️ Purge Master Contract", key="del_contract"):
                    delete_document_from_db("contract")
                    st.success("✅ Contract purged.")
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
            if h_rec:
                st.success(f"📌 Synced: **{h_rec[1]}**")
                if st.button("🗑️ Purge Handbook", key="del_handbook"):
                    delete_document_from_db("handbook")
                    st.success("✅ Handbook purged.")
                    st.rerun()
            else:
                st.info("Repository Empty.")
            
            new_handbook = st.file_uploader("Upload / Overwrite Handbook (PDF)", type=["pdf"], key="upload_h")
            if new_handbook:
                save_document_to_db("handbook", new_handbook)
                st.success("✅ Employee Handbook locked into database!")
                st.rerun()
        
        st.markdown("---")
        st.subheader("⚙️ Pipeline Record Modification")
        
        df_grievances = load_grievances()
        if not df_grievances.empty:
            grievant_options = {f"ID {row['id']}: {row['grievant']} ({row['articles']})": row['id'] for index, row in df_grievances.iterrows()}
            selected_label = st.selectbox("Select Record to Modify", options=list(grievant_options.keys()))
            selected_id = grievant_options[selected_label]
            
            record = df_grievances[df_grievances['id'] == selected_id].iloc[0]
            
            with st.form("edit_grievance_form"):
                st.markdown(f"**Modifying Record ID: {selected_id}** (Origin: {record['user_email']})")
                e_name = st.text_input("Grievant Name & Department", value=record['grievant'])
                e_date = st.text_input("Date of Occurrence", value=record['occ_date'])
                e_articles = st.text_input("Contract Article(s) Violated", value=record['articles'])
                
                steps_list = ["Step 1 (Supervisor)", "Step 2 (HR / Dept Head)", "Step 3 (Plant Mgr)", "Arbitration"]
                default_step_idx = steps_list.index(record['step']) if record['step'] in steps_list else 0
                e_step = st.selectbox("Current Step", steps_list, index=default_step_idx)
                
                e_steward = st.text_input("Assigned Steward", value=record['steward'])
                e_committeeman = st.text_input("Assigned Grievance Committeeman", value=record['committeeman'] if record['committeeman'] else "")
                e_facts = st.text_area("Statement of Facts / Notes", value=record['facts'])
                e_remedy = st.text_area("Remedy Demanded", value=record['remedy'])
                
                col_update, col_delete = st.columns(2)
                with col_update:
                    update_submitted = st.form_submit_button("💾 UPDATE RECORD", type="primary")
                with col_delete:
                    delete_submitted = st.form_submit_button("🗑️ PURGE RECORD", type="secondary")
                
                if update_submitted:
                    update_grievance(selected_id, e_name, e_date, e_articles, e_step, e_steward, e_committeeman, e_facts, e_remedy)
                    st.success(f"✅ Record ID {selected_id} updated successfully!")
                    st.rerun()
                
                if delete_submitted:
                    delete_grievance(selected_id)
                    st.success(f"🗑️ Record ID {selected_id} purged from database!")
                    st.rerun()
        else:
            st.info("No records in pipeline to modify.")
        
        st.markdown("---")
        st.subheader("⚙️ Access Control Matrix & Assigned PINs")
        new_email = st.text_input("Authorize New IDENT (Email)")
        if st.button("AUTHORIZE IDENT"):
            if not new_email or "@" not in new_email:
                st.error("⚠️ Invalid email syntax.")
            else:
                if add_authorized_email(new_email):
                    st.success(f"✅ Authorized {new_email} with auto-generated PIN.")
                    st.rerun()
                else:
                    st.error(f"⚠️ {new_email} is already in the access matrix.")
        
        st.markdown("---")
        st.markdown("#### ACTIVE ACCESS MATRIX:")
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT email, pin FROM authorized_emails")
        authorized_rows = cursor.fetchall()
        conn.close()
        
        for row in authorized_rows:
            email_addr = row[0]
            pin_code = row[1] if row[1] else "4812"
            col_email, col_btn = st.columns([3, 1])
            with col_email:
                display_text = f"• {email_addr} &nbsp;&nbsp;|&nbsp;&nbsp; 🔑 PIN: **{pin_code}**"
                if email_addr == ADMIN_EMAIL.lower():
                    display_text += " [ROOT ADMIN]"
                st.markdown(f"<p style='color: #FFD700; font-weight: bold; font-family: monospace;'>{display_text}</p>", unsafe_allow_html=True)
            with col_btn:
                if email_addr != ADMIN_EMAIL.lower():
                    if st.button("REVOKE", key=f"revoke_{email_addr}"):
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM authorized_emails WHERE email = ?", (email_addr,))
                        conn.commit()
                        conn.close()
                        st.success(f"🚫 Revoked access for {email_addr}")
                        st.rerun()
                else:
                    st.text("")
    else:
        st.warning("🔒 RESTRICTED ZONE: Root Admin Privileges Required.")
