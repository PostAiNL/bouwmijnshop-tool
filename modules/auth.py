import streamlit as st
import os
import uuid
import json
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

# CONFIG
PRO_KEY_FIXED = "123-456-789"
LEADS_FILE = "leads.json"
USER_DB_FILE = "user_db.json" 

def get_secret(key, default=None):
    val = os.getenv(key)
    if val: return val
    try: return st.secrets.get(key, default)
    except: return default

def init_session():
    if "license_key" not in st.session_state:
        qp = st.query_params
        st.session_state.license_key = qp.get("license")

def is_authenticated():
    return st.session_state.license_key is not None

def is_pro():
    key = st.session_state.license_key
    if not key: return False
    if key == PRO_KEY_FIXED: return True
    return key == get_secret("PRO_LICENSE_KEY")

# --- DATABASE LOGICA (OPSLAAN & LADEN) ---
def load_progress():
    key = st.session_state.license_key
    if not key: return {}
    if not os.path.exists(USER_DB_FILE): return {}
    try:
        with open(USER_DB_FILE, 'r') as f:
            db = json.load(f)
            return db.get(key, {})
    except: return {}

def save_progress(xp=None, level=None, niche=None, streak=None, my_style=None):
    key = st.session_state.license_key
    if not key: return
    
    data = {}
    if os.path.exists(USER_DB_FILE):
        try: 
            with open(USER_DB_FILE, 'r') as f: 
                data = json.load(f)
        except: 
            data = {}
    
    if key not in data: data[key] = {}
    
    if xp is not None: data[key]["xp"] = xp
    if level is not None: data[key]["level"] = level
    if niche is not None: data[key]["niche"] = niche
    if my_style is not None: data[key]["my_style"] = my_style
    if streak is not None: 
        data[key]["streak"] = streak
        data[key]["last_active"] = str(datetime.now().date())
    
    try: 
        with open(USER_DB_FILE, 'w') as f: 
            json.dump(data, f)
    except: 
        pass

# --- SCRIPT LIBRARY FUNCTIES (NIEUW) ---
def save_script_to_library(topic, content, script_type="Viral"):
    """Slaat een gegenereerd script op in de library."""
    key = st.session_state.license_key
    if not key: return
    
    new_script = {
        "id": str(uuid.uuid4()),
        "date": str(datetime.now().strftime("%Y-%m-%d")),
        "topic": topic,
        "content": content,
        "type": script_type,
        "status": "Te Filmen" # Statussen: Te Filmen -> Gefilmd -> Gepost
    }

    data = {}
    if os.path.exists(USER_DB_FILE):
        try: 
            with open(USER_DB_FILE, 'r') as f: 
                data = json.load(f)
        except: 
            data = {}
        
    if key not in data: data[key] = {}
    if "library" not in data[key]: data[key]["library"] = []
    
    data[key]["library"].insert(0, new_script) # Nieuwste bovenaan
    
    try: 
        with open(USER_DB_FILE, 'w') as f: 
            json.dump(data, f)
    except: 
        pass

def get_user_library():
    """Haalt alle opgeslagen scripts op."""
    data = load_progress()
    return data.get("library", [])

def update_script_status(script_id, new_status):
    """Update de status (bv van Te Filmen naar Gepost)."""
    key = st.session_state.license_key
    if not os.path.exists(USER_DB_FILE): return
    
    try:
        with open(USER_DB_FILE, 'r') as f: 
            data = json.load(f)
        
        if key in data and "library" in data[key]:
            for s in data[key]["library"]:
                if s["id"] == script_id:
                    s["status"] = new_status
                    break
        
        with open(USER_DB_FILE, 'w') as f: 
            json.dump(data, f)
    except: 
        pass

def delete_script(script_id):
    """Verwijdert een script."""
    key = st.session_state.license_key
    if not os.path.exists(USER_DB_FILE): return
    
    try:
        with open(USER_DB_FILE, 'r') as f: 
            data = json.load(f)
        
        if key in data and "library" in data[key]:
            data[key]["library"] = [s for s in data[key]["library"] if s["id"] != script_id]
        
        with open(USER_DB_FILE, 'w') as f: 
            json.dump(data, f)
    except: 
        pass

# --- EMAIL & LEADS ---
def _send_mail_raw(to_email, subject, body):
    server = get_secret("SMTP_SERVER")
    port = get_secret("SMTP_PORT")
    user = get_secret("SMTP_USER")
    pw = get_secret("SMTP_PASSWORD")
    from_email = get_secret("FROM_EMAIL")

    if not server or not pw: return False
    msg = EmailMessage()
    msg['Subject'] = subject; msg['From'] = from_email; msg['To'] = to_email
    msg.set_content(body)
    try:
        s = smtplib.SMTP(server, int(port))
        s.starttls(); s.login(user, pw); s.send_message(msg); s.quit()
        return True
    except: return False

def save_lead(name, email, license_key):
    lead = {"id": str(uuid.uuid4()), "ts": str(datetime.now()), "name": name, "email": email, "license": license_key}
    try:
        data = []
        if os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, 'r') as f: data = json.load(f)
        data.append(lead)
        with open(LEADS_FILE, 'w') as f: json.dump(data, f)
    except: pass
    admin = get_secret("ADMIN_EMAIL")
    if admin: _send_mail_raw(admin, f"🔥 Nieuwe User: {name}", f"Key: {license_key}")

def render_landing_page():
    st.markdown("""
    <style>.stApp {background-color: white;}</style>
    <div style="text-align:center; max-width:500px; margin:40px auto 20px auto;">
        <div style="font-size:3rem;">🚀</div>
        <h1 style="color:#111827; font-size:1.8rem; margin:10px 0;">Jouw AI Video Coach</h1>
        <p style="color:#6b7280; line-height:1.5;">Krijg elke dag een kant-en-klaar script.<br>Speciaal voor starters. Geen ervaring nodig.</p>
    </div>
    """, unsafe_allow_html=True)
    with st.form("lp_form"):
        name = st.text_input("Je Naam")
        email = st.text_input("Je E-mailadres")
        if st.form_submit_button("🚀 Start Gratis", use_container_width=True):
            if "@" in email and len(name) > 1:
                key = str(uuid.uuid4())[:8].upper()
                save_lead(name, email, key)
                st.session_state.license_key = key
                st.query_params["license"] = key
                st.rerun()

def activate_pro(key_input):
    if key_input == PRO_KEY_FIXED or key_input == get_secret("PRO_LICENSE_KEY"):
        st.session_state.license_key = key_input
        st.query_params["license"] = key_input
        st.success("PRO Geactiveerd! 🎉")
        st.rerun()
    else: st.error("Ongeldige code.")