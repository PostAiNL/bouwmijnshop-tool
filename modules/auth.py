import streamlit as st
import os
import json
import uuid
import time
import datetime
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from supabase import create_client, Client

@st.cache_resource
def init_supabase():
    # Hybride check: Eerst env (Render), dan secrets (Lokaal)
    url = os.getenv("SUPABASE_URL")
    if not url:
        try:
            url = st.secrets["supabase"]["url"]
        except:
            pass
        
    key = os.getenv("SUPABASE_KEY")
    if not key:
        try:
            key = st.secrets["supabase"]["key"]
        except:
            pass
        
    if not url or not key:
        return None
    return create_client(url, key)

# --- DATA MANAGEMENT ---

def load_progress():
    # 1. Check geheugen (snelle check)
    local_data = st.session_state.get("local_user_data", {})
    
    # Als het geheugen zegt dat je PRO bent, geloven we dat direct.
    if local_data and local_data.get("is_pro", False) == True:
        return local_data

    # 2. Check Database (De grondige check)
    key = st.session_state.get("license_key")
    if not key: return {}
    
    supabase = init_supabase()
    try:
        if supabase:
            # BELANGRIJK: We halen nu de JSON 'user_data' EN de kolom 'is_pro' op!
            response = supabase.table("users").select("user_data, is_pro").eq("license_key", key).execute()
            
            if response.data and len(response.data) > 0:
                row = response.data[0]       # Dit is de hele rij
                data = row["user_data"]      # Dit is de JSON (instellingen, XP etc)
                db_is_pro = row["is_pro"]    # Dit is het vinkje dat Make aanzet
                
                # DE CRUCIALE FIX:
                # Als het vinkje in de database (door Make) op TRUE staat...
                # ...dan forceren we de app ook op TRUE, ongeacht wat de JSON zegt.
                if db_is_pro == True:
                    data["is_pro"] = True
                
                # We slaan de geüpdatete status op in het geheugen
                st.session_state.local_user_data = data
                return data
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
        if supabase:
            data_payload = {
                "license_key": key,
                "user_data": st.session_state.local_user_data,
                "email": st.session_state.local_user_data.get("email"), 
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
    # Beveiliging update: Vaste key verwijderd
    data = load_progress()
    return data.get("is_pro", False)

# --- HELPER FUNCTIES ---

def get_secret(key, default=None):
    # 1. Probeer Environment (Render)
    val = os.getenv(key)
    if val: return val
    # 2. Probeer Secrets (Lokaal)
    try:
        if key in st.secrets:
            return st.secrets[key]
    except: pass
    return default

# --- LIMITS & STREAK LOGICA ---

def check_ai_limit():
    user_data = load_progress()
    last_date = user_data.get("ai_last_date", "")
    today = str(datetime.now().date())
    current_count = user_data.get("ai_daily_count", 0)
    
    # Reset teller als het een nieuwe dag is
    if last_date != today:
        current_count = 0
        save_progress(ai_last_date=today, ai_daily_count=0)
    
    # Limieten: 50 voor PRO, 10 voor DEMO
    limit = 50 if is_pro() else 10
    
    return current_count < limit

def track_ai_usage():
    user_data = load_progress()
    current = user_data.get("ai_daily_count", 0)
    save_progress(ai_daily_count=current + 1)

def get_ai_usage_text():
    user_data = load_progress()
    limit = 50 if is_pro() else 10
    current = user_data.get("ai_daily_count", 0)
    return f"{current}/{limit}"

# --- NIEUWE FUNCTIES VOOR DE 'DURE' CALLS (Images/Vision) ---

def check_expensive_limit():
    """
    Checkt limiet voor DALL-E en Vision (GPT-4o).
    DEMO: Max 2 per dag.
    PRO: Max 50 per dag.
    """
    user_data = load_progress()
    last_date = user_data.get("ai_last_date", "")
    today = str(datetime.now().date())
    
    # Reset tellers als het een nieuwe dag is (voor de zekerheid hier ook checken)
    if last_date != today:
        save_progress(ai_last_date=today, ai_daily_count=0, ai_expensive_count=0)
        return True # Nieuwe dag, dus sowieso toegang
    
    # Haal de dure teller op
    current_exp_count = user_data.get("ai_expensive_count", 0)
    
    # Limieten: 50 voor PRO, maar slechts 2 voor DEMO
    limit = 50 if is_pro() else 2
    
    return current_exp_count < limit

def track_expensive_usage():
    """Verhoogt de teller voor dure calls."""
    user_data = load_progress()
    current_exp = user_data.get("ai_expensive_count", 0)
    # We verhogen OOK de algemene teller, zodat ze niet oneindig doorgaan
    current_total = user_data.get("ai_daily_count", 0)
    
    save_progress(ai_expensive_count=current_exp + 1, ai_daily_count=current_total + 1)

def get_expensive_usage_text():
    user_data = load_progress()
    limit = 50 if is_pro() else 2
    current = user_data.get("ai_expensive_count", 0)
    return f"{current}/{limit}"

# ---------------------------------------------

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

# --- MAIL FUNCTIE (HYBRIDE: RENDER + LOKAAL - SSL VERSIE) ---

def send_login_email(to_email, name, license_key):
    # Helper om config op te halen (eerst Env, dan Secrets)
    def get_conf(key, default=None):
        val = os.getenv(key)
        if val: return val
        try: return st.secrets.get(key, default)
        except: return default

    smtp_server = get_conf("SMTP_SERVER", "smtp.strato.com")
    smtp_port = int(get_conf("SMTP_PORT", 465))
    smtp_user = get_conf("SMTP_EMAIL")
    smtp_password = get_conf("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        print("⚠️ SMTP gegevens ontbreken (Check Render Env of secrets.toml)!")
        return False

    base_url = os.getenv("APP_PUBLIC_URL") or "https://postaiapp.onrender.com"
    magic_link = f"{base_url}/?license={license_key}"

    # 2. Email samenstellen
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚀 Jouw toegang tot PostAi"
    msg["From"] = f"PostAi Support <{smtp_user}>"
    msg["To"] = to_email

    # --- HIER IS DE NIEUWE EMAIL HTML, GOED GEÏNDENTEERD ---
    html_body = f"""
    <html>
      <body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f3f4f6;">
        <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); border: 1px solid #e5e7eb;">
            
            <!-- HEADER -->
            <div style="background-color: #10b981; padding: 30px 20px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">🚀 PostAi</h1>
            </div>

            <!-- CONTENT -->
            <div style="padding: 40px 30px; color: #374151;">
                <h2 style="margin-top: 0; color: #111827; font-size: 22px; font-weight: 700;">Welkom bij de club, {name}! 👋</h2>
                <p style="font-size: 16px; line-height: 1.6; margin-bottom: 25px; color: #4b5563;">
                    Tof dat je start! Je account is aangemaakt. Je kunt nu direct inloggen en je eerste virale script laten schrijven door de AI.
                </p>

                <!-- MAIN BUTTON -->
                <div style="text-align: center; margin: 35px 0;">
                    <a href="{magic_link}" style="background-color: #10b981; color: #ffffff; padding: 16px 32px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 16px; display: inline-block; box-shadow: 0 4px 6px rgba(16, 185, 129, 0.4);">
                        🚀 Direct inloggen & Starten
                    </a>
                </div>

                <!-- LICENSE KEY BOX -->
                <div style="background-color: #f9fafb; border: 2px dashed #d1d5db; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 30px;">
                    <p style="margin: 0 0 8px 0; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #6b7280; font-weight: 700;">Jouw persoonlijke toegangscode</p>
                    <code style="font-family: 'Courier New', monospace; font-size: 20px; color: #111827; font-weight: 800; letter-spacing: 1px;">{license_key}</code>
                    <p style="margin: 5px 0 0 0; font-size: 12px; color: #9ca3af;">(Bewaar deze goed!)</p>
                </div>

                <!-- MOBILE APP TIP -->
                <div style="background-color: #eff6ff; border-left: 5px solid #3b82f6; padding: 20px; border-radius: 4px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 10px 0; color: #1e40af; font-size: 16px; font-weight: 700;">📱 Tip: Installeer als app</h3>
                    <p style="margin: 0; font-size: 14px; line-height: 1.5; color: #1e3a8a;">
                        PostAi werkt het snelst vanaf je startscherm. Open de link hierboven op je mobiel en doe dit:
                        <br><br>
                        <strong>iPhone (Safari):</strong><br>
                        Klik op het 'Delen' icoon <span style="font-size:16px">📤</span> en kies <b>"Zet op beginscherm"</b>.
                        <br><br>
                        <strong>Android (Chrome):</strong><br>
                        Klik op het menu <span style="font-size:16px">⋮</span> en kies <b>"Toevoegen aan startscherm"</b>.
                    </p>
                </div>
                
                <p style="font-size: 14px; color: #6b7280; margin-top: 30px; border-top: 1px solid #e5e7eb; padding-top: 20px;">
                    Heel veel succes met groeien!<br>
                    <strong>Team PostAi</strong>
                </p>
            </div>
            
            <!-- FOOTER -->
            <div style="background-color: #f9fafb; padding: 15px; text-align: center; font-size: 12px; color: #9ca3af;">
                &copy; 2025 PostAi. Alle rechten voorbehouden.
            </div>
        </div>
      </body>
    </html>
    """
    
    msg.attach(MIMEText(html_body, "html"))

    # 3. Versturen via Strato (SSL)
    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
            
        print(f"✅ Mail verzonden via Strato (SSL) naar {to_email}")
        return True
    except Exception as e:
        print(f"❌ SMTP Fout: {e}")
        return False

# --- LANDING PAGE ---
# --- IN auth.py (Vervang de hele functie render_landing_page) ---

# --- IN auth.py ---

def render_landing_page():
    # 1. De Hoofdkop (Zoals gevraagd)
    st.markdown("""
        <div style='text-align:center; padding-bottom: 10px; padding-top: 0px;'>
            <h1 style='color:#111827; margin-bottom:0; font-size: 2rem;'>🚀 PostAi</h1>
            <p style='font-size:1rem; color:#6b7280; margin-top: 0px;'>Jouw persoonlijke Ai TikTokcoach.</p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1.2]) 
    
    with c1:
        with st.container(border=True):
            
            # Check of iemand net betaald heeft (De groene balk)
            if st.session_state.get("just_paid", False):
                st.success("✅ Betaling geslaagd! Log in om je PRO tools te ontgrendelen.")
                st.session_state.just_paid = False
            
            # Tabbladen
            st.markdown("#### 👋 Start jouw groei (Gratis)")
            
            if "signup_msg" in st.session_state and st.session_state.signup_msg:
                 st.success(st.session_state.signup_msg)

            tab_signup, tab_login = st.tabs(["Nieuw account", "Inloggen"])
            
            def finish_signup():
                name = st.session_state.get("reg_name", "")
                email = st.session_state.get("reg_email", "")
                
                if name and email and "@" in email:
                    key = "LID-" + str(uuid.uuid4())[:8]
                    st.session_state.license_key = key
                    st.session_state.local_user_data = {"name": name, "email": email}
                    st.query_params["license"] = key
                    save_progress(name=name, email=email, start_date=str(datetime.now().date()))
                    
                    email_thread = threading.Thread(target=send_login_email, args=(email, name, key))
                    email_thread.start()
                    
                    st.session_state.signup_msg = f"✅ De email is verzonden naar {email}! Check je inbox (en spam)."
                else:
                    st.session_state.login_error = "Vul alsjeblieft je naam en een geldig emailadres in."

            with tab_signup:
                st.write("Ontvang binnen 10 sec. toegang tot de AI Coach.")
                st.text_input("Voornaam", key="reg_name", placeholder="Bijv. Mark") 
                st.text_input("Emailadres", key="reg_email", placeholder="jouw@email.nl")
                
                # Actiegerichte knop
                st.button("🚀 Start nu gratis", type="primary", use_container_width=True, on_click=finish_signup)

                if "login_error" in st.session_state:
                    st.error(st.session_state.login_error)
                    del st.session_state.login_error

            with tab_login:
                st.write("Welkom terug, creator!")
                val_key = st.text_input("Jouw toegangscode:", type="password")
                
                st.caption("🔑 Code kwijt? Zoek in je mail op 'PostAi' of mail support@postaiapp.nl")

                if st.button("Inloggen", type="secondary", use_container_width=True):
                    if val_key:
                        st.session_state.license_key = val_key
                        st.query_params["license"] = val_key
                        if "local_user_data" in st.session_state:
                            del st.session_state.local_user_data
                        st.rerun()

    with c2:
        # Social Proof & Urgentie
        st.info("🔥 **HOT:** Het geheime wapen dat 350+ creators al gebruiken.")
        
        # De Verkooptekst
        st.markdown("### 📈 Stop met gokken. Start met groeien.")
        
        # De pijnpunten oplossen
        st.markdown("""
        PostAi automatiseert het saaie werk, zodat jij viral kan gaan:
        
        *   🧠 **Nooit meer inspiratieloos**  
            *Elke ochtend 3 nieuwe, virale script-ideeën klaarstaan.*
        *   🕵️ **Hack het algoritme**  
            *Snap eindelijk waarom je views stoppen (en hoe je dat fixt).*
        *   🎥 **Opnemen zonder stress**  
            *Dankzij de teleprompter film je alles in 1 take.*
        *   🧬 **100% Authentiek**  
            *AI die schrijft zoals JIJ praat (geen saaie robot-taal).*
        
        👇 **Probeer het nu 14 dagen gratis**
        """)

def activate_pro(key_input):
    if len(key_input) > 5: 
        save_progress(is_pro=True)
        st.balloons()
        st.success("PRO geactiveerd!")
        time.sleep(2); st.rerun()
    else: st.error("Ongeldige code")

def save_feedback(text, approved):
    supabase = init_supabase()
    try:
        if supabase:
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
        return False
    except Exception as e:
        print(f"Feedback save error: {e}")
        return False

# --- IN auth.py (helemaal onderaan toevoegen) ---

def delete_script_from_library(script_id):
    user_data = load_progress()
    library = user_data.get("library", [])
    # Filter de lijst: behoud alles BEHALVE degene met dit ID
    new_library = [item for item in library if item.get("id") != script_id]
    save_progress(library=new_library)