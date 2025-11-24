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
    
    # Initialiseer data in sessie als die er is
    if st.session_state.license_key:
        data = load_progress()
        st.session_state.user_data = data

def is_authenticated():
    return st.session_state.get("license_key") is not None

def is_pro():
    key = st.session_state.get("license_key")
    if not key: return False
    if key == PRO_KEY_FIXED: return True
    # Check in opgeslagen data of PRO actief is
    data = load_progress()
    return data.get("is_pro", False)

# --- DEMO LIMIT & TIMERS ---
def get_days_remaining():
    """Geeft aantal resterende demo-dagen terug."""
    if is_pro(): return "∞"
    
    data = load_progress()
    start_date_str = data.get("start_date")
    
    if not start_date_str:
        # Als er geen startdatum is, zet hem op vandaag (fix voor oude users)
        save_progress(start_date=str(datetime.now().date()))
        return 14
        
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        days_used = (datetime.now().date() - start_date).days
        days_left = 14 - days_used
        return max(0, days_left)
    except:
        return 0

def is_demo_expired():
    """Checkt of de 14 dagen voorbij zijn."""
    if is_pro(): return False
    remaining = get_days_remaining()
    return remaining == 0

# --- PROGRESSIE & OPSLAG ---
def load_progress():
    key = st.session_state.get("license_key")
    if not key: return {}
    
    if not os.path.exists(USER_DB_FILE): return {}
    
    try:
        with open(USER_DB_FILE, 'r') as f:
            db = json.load(f)
            return db.get(key, {})
    except: return {}

def save_progress(**kwargs):
    key = st.session_state.get("license_key")
    if not key: return
    
    # 1. Laad bestaande data (om overschrijven te voorkomen)
    data = {}
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, 'r') as f:
                data = json.load(f)
        except: data = {}
    
    if key not in data: data[key] = {}
    
    # 2. Update met nieuwe waarden
    for k, v in kwargs.items():
        data[key][k] = v
        # Update ook direct de sessie state
        if k in st.session_state:
            st.session_state[k] = v
            
    # 3. Schrijf terug
    try:
        with open(USER_DB_FILE, 'w') as f:
            json.dump(data, f)
    except: pass

def check_daily_streak():
    user_data = load_progress()
    last_active_str = user_data.get("last_active_date", "")
    current_streak = user_data.get("streak", 0)
    
    if not last_active_str: return current_streak
    
    try:
        last_date = datetime.strptime(last_active_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        
        # Vandaag al actief geweest?
        if last_date == today: return current_streak
        
        # Gisteren actief geweest? (Streak behouden)
        if last_date == today - timedelta(days=1): return current_streak
        
        # Langer geleden? Streak gebroken.
        save_progress(streak=0)
        return 0
    except: return 0

# --- FEATURE ACCESS (Rewards) ---
def has_access(feature_name):
    if is_pro(): return True
    
    user_data = load_progress()
    trial_feat = user_data.get("active_trial_feature", "")
    trial_end = user_data.get("trial_end_time", "")
    
    if trial_feat == feature_name and trial_end:
        try:
            end_dt = datetime.strptime(trial_end, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < end_dt: return True
        except: pass
    return False

# --- SCRIPT LIBRARY ---
def save_script_to_library(topic, content, script_type="Viral"):
    key = st.session_state.get("license_key")
    if not key: return
    
    # Haal huidige library op uit database (niet alleen sessie)
    user_data = load_progress()
    library = user_data.get("library", [])
    
    new_script = {
        "id": str(uuid.uuid4()), 
        "date": str(datetime.now().strftime("%Y-%m-%d")), 
        "topic": topic, 
        "content": content, 
        "type": script_type, 
        "status": "Te Filmen"
    }
    
    library.insert(0, new_script)
    save_progress(library=library)

def get_user_library():
    data = load_progress()
    return data.get("library", [])

def delete_script(script_id):
    user_data = load_progress()
    library = user_data.get("library", [])
    new_lib = [s for s in library if s["id"] != script_id]
    save_progress(library=new_lib)

# --- LANDING & LOGIN ---
def save_lead(name, email, license_key):
    lead = {
        "id": str(uuid.uuid4()), 
        "ts": str(datetime.now()), 
        "name": name, 
        "email": email, 
        "license": license_key
    }
    
    # Sla lead op
    leads_data = []
    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE, 'r') as f:
                leads_data = json.load(f)
        except: pass
    leads_data.append(lead)
    with open(LEADS_FILE, 'w') as f:
        json.dump(leads_data, f)
        
    # Initialiseer direct de user_db met startdatum voor de trial
    save_progress_initial(license_key, start_date=str(datetime.now().date()))

def save_progress_initial(key, **kwargs):
    # Hulpfunctie om user_db te vullen zonder sessie state
    data = {}
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, 'r') as f:
                data = json.load(f)
        except: data = {}
    
    if key not in data: data[key] = {}
    for k, v in kwargs.items(): data[key][k] = v
    
    with open(USER_DB_FILE, 'w') as f:
        json.dump(data, f)

def render_landing_page():
    st.markdown("""
    <style>.stApp {background-color: white;}</style>
    <div style="text-align:center; max-width:500px; margin:60px auto 20px auto;">
        <div style="font-size:3.5rem;">🚀</div>
        <h1 style="color:#111827; font-size:2.2rem; margin:10px 0; font-weight:900;">Word een TikTok Pro</h1>
        <p style="color:#6b7280; line-height:1.6; font-size:1.1rem; margin-bottom:30px;">
            Start je <b>14-dagen gratis bootcamp</b>. <br>
            Geen creditcard nodig. De AI vertelt je wat je moet doen.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("lp_form", border=True):
            name = st.text_input("Voornaam")
            email = st.text_input("E-mailadres")
            if st.form_submit_button("🚀 Start Direct", type="primary", use_container_width=True):
                if "@" in email and len(name) > 1:
                    key = str(uuid.uuid4())[:8].upper()
                    save_lead(name, email, key)
                    st.session_state.license_key = key
                    st.query_params["license"] = key
                    st.rerun()
                else:
                    st.error("Vul een geldig e-mailadres in.")

def activate_pro(key_input):
    if key_input == PRO_KEY_FIXED or key_input == get_secret("PRO_LICENSE_KEY"):
        save_progress(is_pro=True)
        st.session_state.license_key = key_input # Update sessie indien nodig
        st.balloons()
        st.success("PRO Geactiveerd! 🎉")
        time.sleep(2)
        st.rerun()
    else:
        st.error("Ongeldige code.")