import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime
from google import genai
from google.genai import types

# --- PAGE CONFIG ---
st.set_page_config(page_title="Union Steward Portal", page_icon="✊", layout="wide")

DB_NAME = "union_grievances.db"
ADMIN_EMAIL = "cfetrow0201@gmail.com"
MASTER_CONTRACT_PATH = "master_contract.pdf"

# --- 1. SETUP DATABASE ---
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
            facts TEXT,
            remedy TEXT,
            evidence_image TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authorized_emails (
            email TEXT PRIMARY KEY
        )
    ''')
    
    # Check if the table is completely empty before adding defaults
    cursor.execute("SELECT COUNT(*) FROM authorized_emails")
    count = cursor.fetchone()[0]
    if count == 0:
        default_emails = [ADMIN_EMAIL, "admin@union.org", "steward1@union.org"]
        for email in default_emails:
            cursor.execute("INSERT OR IGNORE INTO authorized_emails (email) VALUES (?)", (email,))
            
    conn.commit()
    conn.close()

init_db()

def is_email_authorized(email):
    if not email or "@" not in email:
        return False
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM authorized_emails WHERE email = ?", (email.strip().lower(),))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_grievance(email, grievant, date, articles, step, steward, facts, remedy, image_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO grievances (user_email, grievant, occ_date, articles, step, steward, facts, remedy, evidence_image)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (email.strip().lower(), grievant, date, articles, step, steward, facts, remedy, image_name))
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

# --- 4. LOGIN GATE ---
if not st.session_state.logged_in:
    st.title("✊ Union Steward Portal & Grievance Pipeline")
    st.markdown("### Secure Access Gateway")
    
    email_attempt = st.text_input("Enter your authorized email address:")
    if st.button("Access Portal", type="primary"):
        if is_email_authorized(email_attempt):
            st.session_state.logged_in = True
            st.session_state.user_email = email_attempt.strip().lower()
            st.rerun()
        else:
            st.error("❌ Access Denied: This email is not authorized on the whitelist.")
    st.stop()

# --- 5. MAIN APP INTERFACE ---
st.title("✊ Union Steward Portal & Grievance Pipeline")
st.success(f"🔓 Logged in as: **{st.session_state.user_email}**")

api_key = get_gemini_key()

tab1, tab2, tab3 = st.tabs(["📖 Contract Expert (AI Search)", "📋 Grievance Pipeline", "⚙️ Manage Access List"])

with tab1:
    st.subheader("Contract Expert - AI Search (Master Hub)")
    
    if st.session_state.user_email == ADMIN_EMAIL.lower():
        uploaded_pdf = st.file_uploader("Upload / Replace Master Contract CBA (PDF)", type=["pdf"])
        if uploaded_pdf is not None:
            with open(MASTER_CONTRACT_PATH, "wb") as f:
                f.write(uploaded_pdf.getbuffer())
            st.success("✅ Master contract updated successfully for all users!")
    
    if os.path.exists(MASTER_CONTRACT_PATH):
        st.info("📂 Active Master Contract loaded and shared globally for all stewards.")
    else:
        st.warning("⚠️ No master contract found yet. Admin needs to upload one.")

    question = st.text_area("Contract Question", placeholder="e.g., What is the deadline to file a Step 1 grievance?")
    
    if st.button("Search Contract", type="primary"):
        if not api_key:
            st.warning("⚠️ Gemini API key is missing. Please configure it in Streamlit Secrets.")
        elif not question:
            st.warning("⚠️ Please type a question.")
        elif not os.path.exists(MASTER_CONTRACT_PATH):
            st.warning("⚠️ No contract PDF available to search.")
        else:
            try:
                client = genai.Client(api_key=api_key.strip())
                contents = []
                with open(MASTER_CONTRACT_PATH, "rb") as f:
                    pdf_bytes = f.read()
                contents.append(types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"))
                contents.append(f"Question: {question}")
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction="You are an expert labor union contract analyst assisting shop stewards. Answer authoritatively with article citations.",
                        temperature=0.2
                    )
                )
                st.markdown("### Guidance & Citations:")
                st.write(response.text)
            except Exception as e:
                st.error(f"Error communicating with Gemini: {e}")

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Log New Grievance")
        with st.form("grievance_form"):
            g_name = st.text_input("Grievant Name & Department")
            g_date = st.text_input("Date of Occurrence")
            g_articles = st.text_input("Contract Article(s) Violated")
            g_step = st.selectbox("Current Step", ["Step 1 (Supervisor)", "Step 2 (HR / Dept Head)", "Step 3 (Plant Mgr)", "Arbitration"])
            g_steward = st.text_input("Assigned Steward")
            g_facts = st.text_area("Statement of Facts / Notes")
            g_remedy = st.text_area("Remedy Demanded")
            uploaded_image = st.file_uploader("Upload Photo of Notes / Evidence", type=["png", "jpg", "jpeg"])
            
            submitted = st.form_submit_button("Save Grievance & Evidence", type="primary")
            if submitted:
                if not g_name or not g_articles:
                    st.error("⚠️ Please provide at least the Grievant Name and Article(s) Violated.")
                else:
                    img_name = uploaded_image.name if uploaded_image else "No Image"
                    save_grievance(st.session_state.user_email, g_name, g_date, g_articles, g_step, g_steward, g_facts, g_remedy, img_name)
                    st.success(f"✅ Grievance logged successfully!")
                    st.rerun()

    with col2:
        st.subheader("Active Grievance Pipeline")
        df = load_grievances()
        if not df.empty:
            st.dataframe(df[["user_email", "grievant", "occ_date", "articles", "step", "steward", "timestamp"]], use_container_width=True)
        else:
            st.info("No grievances logged yet.")

with tab3:
    if st.session_state.user_email == ADMIN_EMAIL.lower():
        st.subheader("Manage Authorized Access List")
        new_email = st.text_input("New Steward/Office Email")
        if st.button("Authorize Email"):
            if not new_email or "@" not in new_email:
                st.error("⚠️ Please enter a valid email address.")
            else:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO authorized_emails (email) VALUES (?)", (new_email.strip().lower(),))
                    conn.commit()
                    st.success(f"✅ Successfully added {new_email}!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(f"⚠️ {new_email} is already on the list.")
                finally:
                    conn.close()
        
        st.markdown("---")
        st.markdown("#### Currently Authorized:")
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM authorized_emails")
        authorized_rows = cursor.fetchall()
        conn.close()
        
        for row in authorized_rows:
            email_addr = row[0]
            col_email, col_btn = st.columns([3, 1])
            with col_email:
                st.markdown(f"<p style='color: #FFD700; font-weight: bold;'>• {email_addr}</p>", unsafe_allow_html=True)
            with col_btn:
                if email_addr != ADMIN_EMAIL.lower():
                    if st.button("Revoke", key=f"revoke_{email_addr}"):
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM authorized_emails WHERE email = ?", (email_addr,))
                        conn.commit()
                        conn.close()
                        st.success(f"🚫 Revoked and deleted access for {email_addr}")
                        st.rerun()
                else:
                    st.text("(Master Admin)")
    else:
        st.warning("🔒 This tab is restricted to the master administrator.")
