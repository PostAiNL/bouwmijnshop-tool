import streamlit as st
import os
import uuid
import json
import time
from datetime import datetime, timedelta

# CONFIG
PRO_KEY_FIXED = "123-456-789"
USER_DB_FILE = "user_db.json"
LEADS_FILE = "leads.json"

def get_secret(key, default=None):
    val = os.getenv(key)
    if val: return val
    try: return st.secrets.get(key, default)
    except: return default

def init_session():
    if "license_key" not in st.session_state:
        qp = st.query_params
        st.session_state.license_key = qp.get("license")
    if st.session_state.license_key:
        load_progress()

def is_authenticated():
    return st.session_state.get("license_key") is not None

def is_pro():
    key = st.session_state.get("license_key")
    if not key: return False
    if key == PRO_KEY_FIXED: return True
    data = load_progress()
    return data.get("is_pro", False)

# --- DATA MANAGEMENT ---
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
    data = {}
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, 'r') as f: data = json.load(f)
        except: data = {}
    
    if key not in data: data[key] = {}
    for k, v in kwargs.items():
        data[key][k] = v
        if k in st.session_state: st.session_state[k] = v
            
    try:
        with open(USER_DB_FILE, 'w') as f: json.dump(data, f)
    except: pass

# --- STREAK & TICKETS LOGICA ---
def check_daily_streak():
    user_data = load_progress()
    last_active_str = user_data.get("last_active_date", "")
    current_streak = user_data.get("streak", 0)
    if not last_active_str: return current_streak
    try:
        last_date = datetime.strptime(last_active_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        if last_date == today: return current_streak
        if last_date == today - timedelta(days=1): return current_streak
        return 0
    except: return 0

def handle_daily_streak():
    user_data = load_progress()
    last_active_str = user_data.get("last_active_date", "")
    current_streak = user_data.get("streak", 0)
    today = datetime.now().date()
    today_str = str(today)
    
    if last_active_str == today_str: return

    try:
        if last_active_str:
            last_date = datetime.strptime(last_active_str, "%Y-%m-%d").date()
            if last_date == today - timedelta(days=1): current_streak += 1
            else: current_streak = 1
        else: current_streak = 1
    except: current_streak = 1
        
    unclaimed = user_data.get("unclaimed_reward", False)
    if current_streak > 0 and current_streak % 5 == 0: unclaimed = True
        
    save_progress(streak=current_streak, last_active_date=today_str, unclaimed_reward=unclaimed)
    st.session_state.streak = current_streak

def use_ticket():
    user_data = load_progress()
    tickets = user_data.get("golden_tickets", 0)
    if tickets > 0:
        new_tickets = tickets - 1
        save_progress(golden_tickets=new_tickets)
        st.session_state.golden_tickets = new_tickets
        return True
    else:
        st.error("Geen Golden Tickets meer!")
        return False

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

# --- HELPERS ---
def save_script_to_library(topic, content):
    key = st.session_state.get("license_key")
    if not key: return
    user_data = load_progress()
    library = user_data.get("library", [])
    library.insert(0, {"id": str(uuid.uuid4()), "date": str(datetime.now().date()), "topic": topic, "content": content})
    save_progress(library=library)

def is_tiktok_connected():
    return load_progress().get("tiktok_connected", False)

def connect_tiktok():
    save_progress(tiktok_connected=True)

def save_lead(name, email, license_key):
    save_progress_initial(license_key, start_date=str(datetime.now().date()))

def save_progress_initial(key, **kwargs):
    data = {}
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, 'r') as f: data = json.load(f)
        except: pass
    if key not in data: data[key] = {}
    for k, v in kwargs.items(): data[key][k] = v
    try:
        with open(USER_DB_FILE, 'w') as f: json.dump(data, f)
    except: pass

def render_landing_page():
    st.markdown("<h1 style='text-align:center;'>🚀 PostAi</h1>", unsafe_allow_html=True)
    with st.form("lp"):
        name = st.text_input("Naam")
        email = st.text_input("Email")
        if st.form_submit_button("Start"):
            key = str(uuid.uuid4())[:8]
            save_lead(name, email, key)
            st.session_state.license_key = key
            st.query_params["license"] = key
            st.rerun()

def activate_pro(key_input):
    if key_input == PRO_KEY_FIXED:
        save_progress(is_pro=True)
        st.balloons()
        st.success("PRO Geactiveerd!")
        time.sleep(2); st.rerun()
    else: st.error("Ongeldige code")