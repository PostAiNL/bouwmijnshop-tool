import streamlit as st
import os
import json
import uuid
import time
import datetime
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# CONFIG
PRO_KEY_FIXED = "123-456-789" # Dev/Admin sleutel

# --- GOOGLE SHEETS VERBINDING (MET CACHE) ---
@st.cache_resource(ttl=600)
def get_db_connection():
    """Maakt verbinding met Google Sheets via st.secrets"""
    if "gcp_service_account" not in st.secrets:
        print("⚠️ LET OP: Geen Google Credentials gevonden in secrets.toml")
        return None

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds_dict = dict(st.secrets["gcp_service_account"])
        
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Zorg dat de sheet naam exact klopt!
        sheet = client.open("PostAi Database").worksheet("Users") 
        return sheet
        
    except Exception as e:
        print(f"❌ DB Connectie Fout: {e}")
        return None

# --- DATA MANAGEMENT (CRUD) ---

def load_progress():
    """Laadt data uit Google Sheets op basis van licentie."""
    key = st.session_state.get("license_key")
    if not key: return {}

    sheet = get_db_connection()
    
    if not sheet:
        return st.session_state.get("local_user_data", {})

    try:
        # Zoek de cel met de licentiesleutel
        cell = sheet.find(key)
        
        if cell:
            # Gevonden! Haal data op uit kolom 2
            data_str = sheet.cell(cell.row, 2).value
            return json.loads(data_str) if data_str else {}
        else:
            # Niet gevonden
            return {}
            
    except Exception as e:
        print(f"⚠️ Load Error: {e}")
        return st.session_state.get("local_user_data", {})

def save_progress(**kwargs):
    """Slaat data op in Google Sheets."""
    key = st.session_state.get("license_key")
    if not key: return

    if "local_user_data" not in st.session_state:
        st.session_state.local_user_data = {}
    
    current_data = load_progress()
    if not current_data: current_data = {}
    
    for k, v in kwargs.items():
        current_data[k] = v
        st.session_state[k] = v 
        st.session_state.local_user_data[k] = v

    sheet = get_db_connection()
    if sheet:
        try:
            json_data = json.dumps(current_data)
            
            # Zoek de sleutel
            cell = sheet.find(key)
            
            if cell:
                # BESTAAT AL: Update de rij
                sheet.update_cell(cell.row, 2, json_data)
            else:
                # BESTAAT NIET: Nieuwe rij toevoegen
                sheet.append_row([key, json_data])
                print(f"✅ Nieuwe gebruiker geregistreerd: {key}")
                
        except Exception as e:
            print(f"❌ Save Error: {e}")

# --- AUTHENTICATIE ---

def init_session():
    if "license_key" not in st.session_state:
        qp = st.query_params
        st.session_state.license_key = qp.get("license")
    
    if st.session_state.license_key:
        data = load_progress()
        st.session_state.local_user_data = data

def is_authenticated():
    return st.session_state.get("license_key") is not None

def is_pro():
    key = st.session_state.get("license_key")
    if not key: return False
    if key == PRO_KEY_FIXED: return True
    
    data = load_progress()
    return data.get("is_pro", False)

def render_landing_page():
    st.markdown("<h1 style='text-align:center;'>🚀 PostAi - Dé TikTokgroeier</h1>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.info("👋 **Nieuw hier?**")
        st.markdown("Start direct met een demo-account.")
        with st.form("lp"):
            name = st.text_input("Naam")
            email = st.text_input("Email")
            if st.form_submit_button("Start Gratis Demo"):
                key = "DEMO-" + str(uuid.uuid4())[:8]
                st.session_state.license_key = key
                save_progress(name=name, email=email, start_date=str(datetime.now().date()))
                st.query_params["license"] = key
                st.rerun()
                
    with c2:
        st.success("🔑 **Heb je al een account?**")
        exist_key = st.text_input("Plak je licentiecode:")
        if st.button("Inloggen"):
            if exist_key:
                st.session_state.license_key = exist_key
                st.query_params["license"] = exist_key
                st.rerun()

def activate_pro(key_input):
    if len(key_input) > 5: 
        save_progress(is_pro=True)
        st.balloons()
        st.success("PRO Geactiveerd! Welkom bij de club.")
        time.sleep(2); st.rerun()
    else: st.error("Ongeldige code")

# --- FUNCTIE HELPERS ---
def get_secret(key, default=None):
    val = os.getenv(key)
    if val: return val
    try: return st.secrets.get(key, default)
    except: return default

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
        save_progress(golden_tickets=tickets - 1)
        return True
    else:
        st.error("Geen Golden Tickets meer!")
        return False

def has_access(feature_name):
    if is_pro(): return True
    return False 

def save_script_to_library(topic, content):
    user_data = load_progress()
    library = user_data.get("library", [])
    library.insert(0, {"id": str(uuid.uuid4()), "date": str(datetime.now().date()), "topic": topic, "content": content})
    save_progress(library=library)

def check_ai_limit():
    user_data = load_progress()
    last_date = user_data.get("ai_last_date", "")
    today = str(datetime.now().date())
    current_count = user_data.get("ai_daily_count", 0)
    if last_date != today:
        current_count = 0
        save_progress(ai_last_date=today, ai_daily_count=0)
    limit = 80 if is_pro() else 10
    return current_count < limit

def track_ai_usage():
    user_data = load_progress()
    current = user_data.get("ai_daily_count", 0)
    save_progress(ai_daily_count=current + 1)

def get_ai_usage_text():
    user_data = load_progress()
    limit = 50 if is_pro() else 5
    current = user_data.get("ai_daily_count", 0)
    return f"{current}/{limit}"