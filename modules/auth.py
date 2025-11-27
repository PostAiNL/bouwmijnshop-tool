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
from supabase import create_client, Client

# CONFIG
PRO_KEY_FIXED = "123-456-789"

# NIEUWE VERSIE (Werkt op Render én Lokaal)
@st.cache_resource
def init_supabase():
    # 1. Probeer eerst de Environment Variables (voor Render)
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    # 2. Als die niet bestaan, kijk dan in st.secrets (voor lokaal testen)
    if not url and "supabase" in st.secrets:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        
    # 3. Als we nog steeds niets hebben, geef geen foutmelding maar return None
    if not url or not key:
        print("⚠️ Waarschuwing: Supabase gegevens ontbreken.")
        return None

    return create_client(url, key)

# --- DATA MANAGEMENT (SUPABASE) ---

def load_progress():
    """Haalt data op uit Supabase JSONB kolom."""
    # Eerst kijken of we het al in de sessie hebben (snelheid)
    if "local_user_data" in st.session_state and st.session_state.local_user_data:
        return st.session_state.local_user_data

    key = st.session_state.get("license_key")
    if not key: return {}

    supabase = init_supabase()
    try:
        # Haal de rij op waar license_key matcht
        response = supabase.table("users").select("user_data").eq("license_key", key).execute()
        
        if response.data and len(response.data) > 0:
            data = response.data[0]["user_data"]
            st.session_state.local_user_data = data
            return data
        else:
            # Nieuwe gebruiker? Return leeg dict
            return {}
    except Exception as e:
        print(f"❌ DB Load Error: {e}")
        return {}

def save_progress(**kwargs):
    """Slaat data op (Upsert) in Supabase."""
    key = st.session_state.get("license_key")
    if not key: return

    # Update lokale sessie eerst
    if "local_user_data" not in st.session_state:
        st.session_state.local_user_data = load_progress()
    
    for k, v in kwargs.items():
        st.session_state.local_user_data[k] = v
        # Update ook direct de losse session states voor UI reactivity
        st.session_state[k] = v 

    supabase = init_supabase()
    try:
        # We slaan de hele user_data blob op in de 'user_data' kolom
        data_payload = {
            "license_key": key,
            "user_data": st.session_state.local_user_data,
            "updated_at": str(datetime.now())
        }
        # Upsert: Maakt aan als niet bestaat, anders updaten
        supabase.table("users").upsert(data_payload).execute()
    except Exception as e:
        print(f"❌ DB Save Error: {e}")

# --- AUTH & PRO LOGICA ---

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

# --- VERVANG DEZE FUNCTIE IN auth.py ---

# --- VERVANG DEZE HELE FUNCTIE IN auth.py ---

def render_landing_page():
    # Een wat hippere header
    st.markdown("""
        <div style='text-align:center; padding-bottom: 20px;'>
            <h1 style='color:#111827; margin-bottom:0;'>🚀 PostAi</h1>
            <p style='font-size:1.2rem; color:#6b7280;'>Jouw persoonlijke AI TikTok Coach</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1.2, 1])
    
    with c1:
        st.markdown("### 📈 Stop met gokken, start met groeien.")
        st.markdown("""
        PostAi is de enige tool die je **hele workflow** automatiseert:
        
        *   ✅ **Nooit meer inspiratieloos** (Dagelijkse trends & scripts)
        *   ✅ **AI Vision Analyse** (Weet precies waarom je video flopt)
        *   ✅ **Teleprompter & Visuals** (Film sneller en professioneler)
        *   ✅ **Clone My Voice** (Scripts in JOUW schrijfstijl)
        
        👇 **Probeer 14 dagen gratis, daarna €14,95 per maand (PRO)**
        """)
        st.info("💡 **Tip:** Nieuwe gebruikers krijgen direct toegang tot de demo omgeving.")

    with c2:
        with st.container(border=True):
            st.markdown("#### 👋 Start direct (Gratis)")
            
            tab_signup, tab_login = st.tabs(["Nieuw Account", "Inloggen"])
            
            # --- DE OPLOSSING VOOR FREEZE & DUBBELE KLIK ---
            def finish_signup():
                # 1. Haal waarden op uit de widget keys
                name = st.session_state.get("reg_name", "")
                email = st.session_state.get("reg_email", "")
                
                if name and email and "@" in email:
                    # 2. Maak account aan
                    key = "DEMO-" + str(uuid.uuid4())[:8]
                    
                    # 3. Update Session State DIRECT (Dit fixt de dubbele klik)
                    st.session_state.license_key = key
                    st.session_state.local_user_data = {"name": name, "email": email}
                    st.query_params["license"] = key 
                    
                    # 4. Opslaan in DB (Supabase)
                    save_progress(name=name, email=email, start_date=str(datetime.now().date()))
                    
                    # 5. Mail versturen (In een try-block zodat de app NOOIT vastloopt)
                    try:
                        send_login_email(email, name, key)
                    except Exception as e:
                        print(f"Mail error: {e}") # Faal stil, gebruiker is toch al binnen
                else:
                    st.session_state.login_error = "Vul alsjeblieft je naam en email in."

            with tab_signup:
                # We gebruiken geen st.form hier, dat werkt vlotter met callbacks
                st.write("Maak binnen 10 seconden een account aan.")
                st.text_input("Voornaam", key="reg_name") 
                st.text_input("Emailadres", key="reg_email")
                
                # De knop roept nu DIRECT de functie aan
                st.button("🚀 Start Gratis Demo", type="primary", use_container_width=True, on_click=finish_signup)

                if "login_error" in st.session_state:
                    st.error(st.session_state.login_error)
                    del st.session_state.login_error

            with tab_login:
                st.write("Welkom terug, creator!")
                # Login werkt prima zonder callback omdat er geen zware mail wordt verstuurd
                val_key = st.text_input("Jouw Licentiecode:", type="password")
                if st.button("Inloggen", type="secondary", use_container_width=True):
                    if val_key:
                        st.session_state.license_key = val_key
                        st.query_params["license"] = val_key
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

# --- STRATO EMAIL FUNCTIE ---

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

def save_feedback(text, approved):
    """Slaat feedback op in Supabase en voorkomt dubbel gebruik."""
    supabase = init_supabase()
    try:
        key = st.session_state.get("license_key", "unknown")
        status = "approved" if approved else "rejected"
        
        # 1. Feedback opslaan in de tabel
        supabase.table("feedback").insert({
            "license_key": key,
            "message": text,
            "rating": status
        }).execute()
        
        # 2. Beloning geven (ALLEEN als goedgekeurd)
        if approved:
            user_data = load_progress()
            
            # CHECK: Heeft deze gebruiker al feedback gegeven?
            if user_data.get("has_given_feedback", False):
                return False # Stop, ze proberen te cheaten of dubbel te klikken
            
            current_tickets = user_data.get("golden_tickets", 0)
            
            # Sla op: +1 Ticket EN zet het vinkje dat ze het gedaan hebben
            save_progress(
                golden_tickets=current_tickets + 1,
                has_given_feedback=True 
            )
            return True # Succes
            
    except Exception as e:
        print(f"Feedback save error: {e}")
        return False
