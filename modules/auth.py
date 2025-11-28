# --- FILE: auth.py ---
import streamlit as st
import os
import json
import uuid
import time
import datetime
import threading
from datetime import datetime, timedelta
from supabase import create_client, Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# CONFIG
PRO_KEY_FIXED = "123-456-789"

@st.cache_resource
def init_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url and "supabase" in st.secrets:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    if not url or not key:
        return None
    return create_client(url, key)

# --- DATA MANAGEMENT ---

def load_progress():
    if "local_user_data" in st.session_state and st.session_state.local_user_data:
        return st.session_state.local_user_data
    key = st.session_state.get("license_key")
    if not key: return {}
    supabase = init_supabase()
    try:
        response = supabase.table("users").select("user_data").eq("license_key", key).execute()
        if response.data and len(response.data) > 0:
            data = response.data[0]["user_data"]
            st.session_state.local_user_data = data
            return data
        else:
            return {}
    except Exception as e:
        print(f"❌ DB Load Error: {e}")
        return {}

def save_progress(**kwargs):
    key = st.session_state.get("license_key")
    if not key: return
    if "local_user_data" not in st.session_state:
        st.session_state.local_user_data = load_progress()
    for k, v in kwargs.items():
        st.session_state.local_user_data[k] = v
        st.session_state[k] = v 
    supabase = init_supabase()
    try:
        data_payload = {
            "license_key": key,
            "user_data": st.session_state.local_user_data,
            "updated_at": str(datetime.now())
        }
        supabase.table("users").upsert(data_payload).execute()
    except Exception as e:
        print(f"❌ DB Save Error: {e}")

# --- AUTH LOGICA ---

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

# --- HELPER FUNCTIES ---

def get_secret(key, default=None):
    val = os.getenv(key)
    if val: return val
    try: return st.secrets.get(key, default)
    except: return default

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
    limit = 80 if is_pro() else 10
    current = user_data.get("ai_daily_count", 0)
    return f"{current}/{limit}"

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

def send_login_email(to_email, name, license_key):
    # 1. Gegevens ophalen uit Render Environment Variables
    smtp_server = os.getenv("SMTP_SERVER", "smtp.strato.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587")) # Nu standaard op 587
    smtp_user = os.getenv("SMTP_EMAIL")     # Hier komt dus support@postaiapp.nl
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        print("⚠️ SMTP gegevens ontbreken in Render settings!")
        return False

    base_url = os.getenv("APP_PUBLIC_URL") or "https://postaiapp.onrender.com"
    magic_link = f"{base_url}/?license={license_key}"

    # 2. Email samenstellen
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚀 Jouw toegang tot PostAi"
    msg["From"] = f"PostAi Support <{smtp_user}>" # Dit wordt: PostAi Support <support@postaiapp.nl>
    msg["To"] = to_email

    html_body = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
            <h2 style="color: #10b981;">Welkom bij PostAi, {name}! 👋</h2>
            <p>Leuk dat je de demo start! Je account is aangemaakt.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{magic_link}" style="background-color: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Direct Inloggen & Starten</a>
            </div>
            <p>Of gebruik je code handmatig:</p>
            <div style="background: #f3f4f6; padding: 10px; text-align: center; font-family: monospace; font-size: 1.2em; border-radius: 5px;">{license_key}</div>
            <p style="font-size: 0.8em; color: #999;">PostAi Team</p>
        </div>
    </body></html>
    """
    
    msg.attach(MIMEText(html_body, "html"))

    # 3. Versturen via Poort 587 (STARTTLS)
    try:
        # Let op: Hier gebruiken we .SMTP() in plaats van .SMTP_SSL()
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(0) # Zet op 1 als je foutmeldingen wilt zien in de logs
        
        # De beveiligde verbinding starten
        server.starttls() 
        
        # Inloggen
        server.login(smtp_user, smtp_password)
        
        # Versturen
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
            
        print(f"✅ Mail verzonden via Strato (587) naar {to_email}")
        return True
    except Exception as e:
        print(f"❌ SMTP Fout: {e}")
        return False

# --- LANDING PAGE (VOLGORDE: FORMULIER EERST) ---
def render_landing_page():
    # Compactere header
    st.markdown("""
        <div style='text-align:center; padding-bottom: 10px; padding-top: 0px;'>
            <h1 style='color:#111827; margin-bottom:0; font-size: 2rem;'>🚀 PostAi</h1>
            <p style='font-size:1rem; color:#6b7280; margin-top: 0px;'>Jouw persoonlijke AI TikTok Coach</p>
        </div>
    """, unsafe_allow_html=True)

    # LET OP: We zetten c1 (Formulier) EERST in de lijst
    c1, c2 = st.columns([1, 1.2]) 
    
    # 1. HET FORMULIER (In kolom c1, dus links/boven)
    with c1:
        with st.container(border=True):
            st.markdown("#### 👋 Start direct (Gratis)")
            
            tab_signup, tab_login = st.tabs(["Nieuw Account", "Inloggen"])
            
            def finish_signup():
                name = st.session_state.get("reg_name", "")
                email = st.session_state.get("reg_email", "")
                
                if name and email and "@" in email:
                    key = "DEMO-" + str(uuid.uuid4())[:8]
                    st.session_state.license_key = key
                    st.session_state.local_user_data = {"name": name, "email": email}
                    st.query_params["license"] = key
                    save_progress(name=name, email=email, start_date=str(datetime.now().date()))
                    
                    email_thread = threading.Thread(target=send_login_email, args=(email, name, key))
                    email_thread.start()
                else:
                    st.session_state.login_error = "Vul alsjeblieft je naam en een geldig emailadres in."

            with tab_signup:
                st.write("Maak binnen 10 sec een account aan.")
                st.text_input("Voornaam", key="reg_name") 
                st.text_input("Emailadres", key="reg_email")
                # Directe callback op de knop
                st.button("🚀 Start Gratis Demo", type="primary", use_container_width=True, on_click=finish_signup)

                if "login_error" in st.session_state:
                    st.error(st.session_state.login_error)
                    del st.session_state.login_error

            with tab_login:
                st.write("Welkom terug!")
                val_key = st.text_input("Jouw Licentiecode:", type="password")
                if st.button("Inloggen", type="secondary", use_container_width=True):
                    if val_key:
                        st.session_state.license_key = val_key
                        st.query_params["license"] = val_key
                        if "local_user_data" in st.session_state:
                            del st.session_state.local_user_data
                        st.rerun()

    # 2. DE TEKST (In kolom c2, dus rechts/onder)
    with c2:
        # Tip onderaan de tekst kolom
        st.info("💡 **Tip:** Nieuwe gebruikers krijgen direct toegang.")
        
        st.markdown("### 📈 Stop met gokken.")
        st.markdown("""
        PostAi automatiseert je hele workflow:
        
        *   ✅ **Nooit meer inspiratieloos** (Dagelijkse trends)
        *   ✅ **AI Vision Analyse** (Waarom flopt je video?)
        *   ✅ **Teleprompter & Visuals**
        *   ✅ **Clone My Voice** (Jouw schrijfstijl)
        
        👇 **Probeer 14 dagen gratis, daarna €14,95/mnd**
        """)

def activate_pro(key_input):
    if len(key_input) > 5: 
        save_progress(is_pro=True)
        st.balloons()
        st.success("PRO Geactiveerd!")
        time.sleep(2); st.rerun()
    else: st.error("Ongeldige code")

def save_feedback(text, approved):
    supabase = init_supabase()
    try:
        key = st.session_state.get("license_key", "unknown")
        status = "approved" if approved else "rejected"
        supabase.table("feedback").insert({
            "license_key": key,
            "message": text,
            "rating": status
        }).execute()
        if approved:
            user_data = load_progress()
            if user_data.get("has_given_feedback", False): return False 
            current_tickets = user_data.get("golden_tickets", 0)
            save_progress(golden_tickets=current_tickets + 1, has_given_feedback=True)
            return True 
    except Exception as e:
        print(f"Feedback save error: {e}")
        return False