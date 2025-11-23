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
    # Gebruik .get() om crashes te voorkomen
    return st.session_state.get("license_key") is not None

def is_pro():
    key = st.session_state.get("license_key")
    if not key: return False
    if key == PRO_KEY_FIXED: return True
    return key == get_secret("PRO_LICENSE_KEY")

# --- PROGRESSIE & OPSLAG ---
def load_progress():
    key = st.session_state.license_key
    if not key: return {}
    if not os.path.exists(USER_DB_FILE): return {}
    try:
        with open(USER_DB_FILE, 'r') as f:
            db = json.load(f)
            return db.get(key, {})
    except: return {}

def save_progress(xp=None, streak=None, challenge_day=None, last_active=None, 
                  golden_tickets=None, unclaimed_reward=None, 
                  active_trial_feature=None, trial_end_time=None, **kwargs):
    key = st.session_state.get("license_key")
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
    if streak is not None: data[key]["streak"] = streak
    if challenge_day is not None: data[key]["challenge_day"] = challenge_day
    if last_active is not None: data[key]["last_active"] = last_active
    if golden_tickets is not None: data[key]["golden_tickets"] = golden_tickets
    if unclaimed_reward is not None: data[key]["unclaimed_reward"] = unclaimed_reward
    if active_trial_feature is not None: data[key]["trial_feature"] = active_trial_feature
    if trial_end_time is not None: data[key]["trial_end"] = trial_end_time
    
    for k, v in kwargs.items(): data[key][k] = v
    
    try:
        with open(USER_DB_FILE, 'w') as f:
            json.dump(data, f)
    except:
        pass

def check_daily_streak():
    user_data = load_progress()
    last_active_str = user_data.get("last_active", "")
    current_streak = user_data.get("streak", 0)
    
    if not last_active_str: return current_streak
    
    try:
        last_date = datetime.strptime(last_active_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        
        if last_date == today: return current_streak
        if last_date == today - timedelta(days=1): return current_streak
        
        # Streak gebroken -> Reset naar 0, maar behoud wel andere data
        save_progress(streak=0)
        return 0
    except: return 0

# --- FEATURE ACCESS & TIMER ---
def has_access(feature_name):
    if is_pro(): return True
    user_data = load_progress()
    trial_feat = user_data.get("trial_feature", "")
    trial_end = user_data.get("trial_end", "")
    
    if trial_feat == feature_name and trial_end:
        try:
            end_dt = datetime.strptime(trial_end, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < end_dt: return True
        except: pass
    return False

def get_trial_remaining_time():
    user_data = load_progress()
    trial_end = user_data.get("trial_end", "")
    if not trial_end: return None
    try:
        end_dt = datetime.strptime(trial_end, "%Y-%m-%d %H:%M:%S")
        diff = end_dt - datetime.now()
        if diff.total_seconds() > 0:
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours}u {minutes}m"
    except: pass
    return None

# --- SCRIPT LIBRARY ---
def save_script_to_library(topic, content, script_type="Viral"):
    key = st.session_state.get("license_key")
    if not key: return
    
    new_script = {
        "id": str(uuid.uuid4()), 
        "date": str(datetime.now().strftime("%Y-%m-%d")), 
        "topic": topic, 
        "content": content, 
        "type": script_type, 
        "status": "Te Filmen"
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
    
    data[key]["library"].insert(0, new_script)
    
    try:
        with open(USER_DB_FILE, 'w') as f:
            json.dump(data, f)
    except:
        pass

def get_user_library():
    data = load_progress()
    return data.get("library", [])

def update_script_status(script_id, new_status):
    key = st.session_state.get("license_key")
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
    key = st.session_state.get("license_key")
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

# --- MAIL ---
def _send_mail_raw(to_email, subject, body): 
    return True

def save_lead(name, email, license_key):
    lead = {"id": str(uuid.uuid4()), "ts": str(datetime.now()), "name": name, "email": email, "license": license_key}
    try:
        data = []
        if os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, 'r') as f:
                data = json.load(f)
        data.append(lead)
        with open(LEADS_FILE, 'w') as f:
            json.dump(data, f)
    except: pass

def render_landing_page():
    st.markdown("""
    <style>.stApp {background-color: white;}</style>
    <div style="text-align:center; max-width:500px; margin:40px auto 20px auto;">
        <div style="font-size:3rem;">🚀</div>
        <h1 style="color:#111827; font-size:2rem; margin:10px 0; font-weight:900;">Word een TikTok Pro in 30 Dagen</h1>
        <p style="color:#6b7280; line-height:1.6; font-size:1.1rem;">Geen ervaring? Geen probleem.<br>De AI vertelt je precies wat je moet zeggen.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("lp_form"):
        name = st.text_input("Je Naam")
        email = st.text_input("Je E-mailadres")
        if st.form_submit_button("🚀 Start mijn Groei Challenge", use_container_width=True):
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
    else:
        st.error("Ongeldige code.")