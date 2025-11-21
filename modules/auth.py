import streamlit as st
import os
import time
import uuid
import json
import smtplib
from email.message import EmailMessage
from datetime import datetime

LEADS_FILE = "leads.json"
PRO_KEY_FIXED = "123-456-789"

def get_secret(key, default=None):
    """Haalt secret op uit OS (Render) of st.secrets (Lokaal)."""
    return os.getenv(key) or st.secrets.get(key, default)

def init_session():
    if "license_key" not in st.session_state:
        # Check URL param
        qp = st.query_params
        url_key = qp.get("license")
        st.session_state.license_key = url_key if url_key else None

def is_authenticated():
    return st.session_state.license_key is not None

def is_pro():
    key = st.session_state.license_key
    # Check vaste key of key uit env
    if key == PRO_KEY_FIXED: return True
    env_key = get_secret("PRO_LICENSE_KEY")
    if env_key and key == env_key: return True
    return False

# --- ECHTE EMAIL FUNCTIE ---
def send_license_email(name, email, license_key):
    server = get_secret("SMTP_SERVER")
    port = get_secret("SMTP_PORT")
    user = get_secret("SMTP_USER")
    password = get_secret("SMTP_PASSWORD")
    from_email = get_secret("FROM_EMAIL")

    if not server or not password:
        print("⚠️ SMTP gegevens ontbreken.")
        return False

    # Bouw de magic link
    # Let op: in productie 'app_url' goed zetten in Render env vars
    app_url = get_secret("APP_PUBLIC_URL", "https://postai.bouwmijnshop.nl")
    magic_link = f"{app_url}/?license={license_key}"

    msg = EmailMessage()
    msg['Subject'] = 'Je PostAi Demo Code 🚀'
    msg['From'] = from_email
    msg['To'] = email
    
    body = f"""Hoi {name},

Leuk dat je start met PostAi!

Jouw Demo Licentiecode: {license_key}

Klik hier om direct in te loggen:
{magic_link}

Succes met groeien!
Team PostAi
"""
    msg.set_content(body)

    try:
        s = smtplib.SMTP(server, int(port))
        s.starttls()
        s.login(user, password)
        s.send_message(msg)
        s.quit()
        return True
    except Exception as e:
        print(f"Fout bij mailen: {e}")
        return False

# --- OPSLAAN IN LEADS.JSON ---
def save_lead(name, email, license_key):
    lead = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "name": name,
        "email": email,
        "license": license_key
    }
    
    data = []
    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE, "r") as f:
                data = json.load(f)
        except: pass
    
    data.append(lead)
    with open(LEADS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def render_landing_page():
    """De EXACTE landingspagina van de oude app."""
    
    st.markdown("""
    <div style="margin-top:20px; margin-bottom:20px;">
        <h1 style="font-size: 2.4rem; font-weight: 800; line-height:1.1; color:#111827;">
            Dagelijkse TikTok ideeën voor jouw niche.
        </h1>
        <div style="display:flex; gap:10px; margin-top:15px; margin-bottom:20px; flex-wrap:wrap;">
            <span style="background:#ecfdf5; color:#166534; padding:4px 12px; border-radius:99px; font-weight:600; font-size:0.85rem;">✔ Gebruikt door creators & shops</span>
            <span style="background:#eff6ff; color:#1d4ed8; padding:4px 12px; border-radius:999px; font-size:0.85rem;">✔ Geen betaalgegevens nodig</span>
            <span style="background:#f3f4f6; color:#4b5563; padding:4px 12px; border-radius:999px; font-size:0.85rem;">✔ Privacy-proof</span>
        </div>
        <div style="font-size:1.1rem; margin-bottom:10px;">
            <b>14 dagen gratis toegang.</b> Geen kosten. Je kunt meteen starten.
        </div>
        <ul style="color:#374151; font-size:1rem; line-height:1.6; margin-bottom:20px;">
            <li><b>Zien wat werkt</b> voor jouw niche.</li>
            <li><b>Kant-en-klare video-ideeën</b> om direct op te nemen.</li>
            <li><b>Slimme posttijden</b> op basis van jouw account.</li>
        </ul>
        <div style="font-size:0.9rem; color:#6b7280; margin-bottom:20px;">
            Vul je gegevens in. Je krijgt direct je demo-code per mail en je demo start daarna meteen.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("landing_form"):
        name = st.text_input("Naam")
        email = st.text_input("E-mailadres")
        
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns([0.05, 0.95])
        with c1:
            agree = st.checkbox(" ", label_visibility="collapsed")
        with c2:
            st.markdown("Ik ga akkoord met de <a href='#'>privacyverklaring</a> en <a href='#'>voorwaarden</a>.", unsafe_allow_html=True)

        submitted = st.form_submit_button("Start mijn gratis demo", use_container_width=True)

        if submitted:
            if not agree:
                st.error("Je moet akkoord gaan met de voorwaarden.")
            elif "@" not in email:
                st.error("Vul een geldig e-mailadres in.")
            else:
                # Maak licentie en sla op
                new_license = str(uuid.uuid4())[:12].upper()
                
                # Opslaan lokaal
                save_lead(name, email, new_license)
                
                # Mailen
                with st.spinner("Licentie genereren en mailen..."):
                    success = send_license_email(name, email, new_license)
                
                # Direct inloggen
                st.session_state.license_key = new_license
                
                if success:
                    st.toast("Licentie gemaild! Je bent ingelogd.", icon="📧")
                else:
                    st.toast("Ingelogd! (Mail kon niet verstuurd worden)", icon="⚠️")
                
                time.sleep(1)
                st.rerun()