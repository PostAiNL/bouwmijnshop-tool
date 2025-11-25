import streamlit as st
import os
import json
import uuid
import time
import datetime
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gspread
from google.oauth2.service_account import Credentials

# CONFIG
PRO_KEY_FIXED = "123-456-789" 

# --- GOOGLE SHEETS VERBINDING (MET CACHE) ---
@st.cache_resource(ttl=600)
def get_db_connection():
    """Maakt verbinding met Google Sheets. Cached voor 10 min."""
    if "gcp_service_account" not in st.secrets:
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
        sheet = client.open("PostAi Database").worksheet("Users") 
        return sheet
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return None

# --- DATA MANAGEMENT (OPTIMIZED) ---

def load_progress():
    """
    SNELHEIDS-OPTIMALISATIE:
    Kijkt eerst in st.session_state. Alleen als daar niks is,
    haalt hij het op van Google Sheets.
    """
    if "local_user_data" in st.session_state and st.session_state.local_user_data:
        return st.session_state.local_user_data

    key = st.session_state.get("license_key")
    if not key: return {}

    sheet = get_db_connection()
    if not sheet: return {}

    try:
        cell = sheet.find(key)
        if cell:
            data_str = sheet.cell(cell.row, 2).value
            data = json.loads(data_str) if data_str else {}
            st.session_state.local_user_data = data
            return data
        else:
            return {}
    except Exception as e:
        print(f"⚠️ Load Error: {e}")
        return {}

def save_progress(**kwargs):
    key = st.session_state.get("license_key")
    if not key: return

    if "local_user_data" not in st.session_state:
        st.session_state.local_user_data = load_progress()
    
    for k, v in kwargs.items():
        st.session_state.local_user_data[k] = v
        st.session_state[k] = v 

    sheet = get_db_connection()
    if sheet:
        try:
            json_data = json.dumps(st.session_state.local_user_data)
            try:
                cell = sheet.find(key)
                sheet.update_cell(cell.row, 2, json_data)
            except gspread.exceptions.CellNotFound:
                sheet.append_row([key, json_data])
        except Exception as e:
            print(f"❌ Save Error: {e}")

# --- AUTHENTICATIE ---

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

# --- LANDING PAGE MET EMAIL LOGICA ---
def render_landing_page():
    st.markdown("<h1 style='text-align:center;'>🚀 PostAi - Dé TikTokgroeier</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.info("👋 **Nieuw hier?**")
        with st.form("lp"):
            name = st.text_input("Naam")
            email = st.text_input("Email")
            submitted = st.form_submit_button("Start Gratis Demo")
            
            if submitted:
                if name and email and "@" in email:
                    # 1. Genereer Key
                    key = "DEMO-" + str(uuid.uuid4())[:8]
                    st.session_state.license_key = key
                    
                    # 2. Sla op in database
                    save_progress(name=name, email=email, start_date=str(datetime.now().date()))
                    
                    # 3. Verstuur mail (met feedback)
                    with st.spinner("📧 Account aanmaken en mail versturen..."):
                        email_sent = send_login_email(email, name, key)
                    
                    if email_sent:
                        st.toast("✅ Mail verstuurd! Check je inbox.", icon="📩")
                    else:
                        st.warning("⚠️ Kon mail niet versturen (check spam), maar je bent wel ingelogd. Bewaar je code!")

                    # 4. Login en refresh
                    time.sleep(1.5)
                    st.query_params["license"] = key
                    st.rerun()
                else:
                    st.error("Vul alsjeblieft een naam en een geldig e-mailadres in.")

    with c2:
        st.success("🔑 **Heb je al een account?**")
        exist_key = st.text_input("Plak je licentiecode:")
        if st.button("Inloggen"):
            if exist_key:
                st.session_state.license_key = exist_key
                st.query_params["license"] = exist_key
                if "local_user_data" in st.session_state:
                    del st.session_state.local_user_data
                st.rerun()

def activate_pro(key_input):
    if len(key_input) > 5: 
        save_progress(is_pro=True)
        st.balloons()
        st.success("PRO Geactiveerd!")
        time.sleep(2); st.rerun()
    else: st.error("Ongeldige code")

# --- HELPERS ---
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

# --- STRATO EMAIL FUNCTIE (AANGEPAST MET TIP) ---

def send_login_email(to_email, name, license_key):
    # 1. Haal variabelen op uit environment
    smtp_server = os.getenv("SMTP_SERVER")           
    smtp_port_str = os.getenv("SMTP_PORT", "587")    
    smtp_user = os.getenv("SMTP_USER")               
    smtp_password = os.getenv("SMTP_PASSWORD")       
    from_email = os.getenv("FROM_EMAIL") or smtp_user 
    
    # Haal base_url op
    base_url = os.getenv("APP_PUBLIC_URL") or os.getenv("BASE_URL") or "http://localhost:8501"

    if not smtp_server or not smtp_user or not smtp_password:
        print(f"⚠️ SMTP Config mist")
        return False

    try:
        smtp_port = int(smtp_port_str)
    except:
        smtp_port = 587

    # De magische link
    magic_link = f"{base_url}/?license={license_key}"

    msg = MIMEMultipart()
    msg['From'] = f"PostAi <{from_email}>"
    msg['To'] = to_email
    msg['Subject'] = "🚀 Jouw toegang tot PostAi"

    # HTML body met App Tip
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
            <h2 style="color: #10b981;">Welkom bij PostAi, {name}! 👋</h2>
            <p>Leuk dat je de demo start! Je account is aangemaakt.</p>
            
            <p>Gebruik onderstaande knop om direct in te loggen:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{magic_link}" style="background-color: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Direct Inloggen & Starten</a>
            </div>

            <div style="background: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; border: 1px solid #ffeeba; font-size: 0.9em; margin-bottom: 20px;">
                📱 <strong>Tip voor de beste ervaring:</strong><br><br>
                1. Klik op de knop hierboven.<br>
                2. Als de app opent in je browser, tik dan op <em>'Delen'</em> (iOS) of de <em>'3 puntjes'</em> (Android).<br>
                3. Kies <strong>"Zet op beginscherm"</strong> (Add to Home Screen).<br><br>
                Zo maak je een "App Icoontje" aan waarmee je voortaan <strong>altijd direct ingelogd</strong> bent!
            </div>

            <p>Of gebruik je code handmatig:</p>
            <div style="background: #f3f4f6; padding: 10px; text-align: center; font-family: monospace; font-size: 1.2em; border-radius: 5px;">
                {license_key}
            </div>

            <hr style="border: none; border-top: 1px solid #eee; margin-top: 30px;">
            <p style="font-size: 0.8em; color: #999;">PostAi Team</p>
        </div>
      </body>
    </html>
    """

    msg.attach(MIMEText(html_body, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Strato Email Error: {e}")
        return False