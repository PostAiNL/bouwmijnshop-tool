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
    value = os.getenv(key)
    if value is not None: return value
    try: return st.secrets.get(key, default)
    except: return default

def init_session():
    if "license_key" not in st.session_state:
        qp = st.query_params
        url_key = qp.get("license")
        st.session_state.license_key = url_key if url_key else None

def is_authenticated():
    return st.session_state.license_key is not None

def is_pro():
    key = st.session_state.license_key
    if key == PRO_KEY_FIXED: return True
    env_key = get_secret("PRO_LICENSE_KEY")
    if env_key and key == env_key: return True
    return False

# --- EMAIL FUNCTIE ---
def send_license_email(name, email, license_key):
    server = get_secret("SMTP_SERVER")
    port = get_secret("SMTP_PORT")
    user = get_secret("SMTP_USER")
    password = get_secret("SMTP_PASSWORD")
    from_email = get_secret("FROM_EMAIL")

    if not server or not password:
        return False

    app_url = get_secret("APP_PUBLIC_URL", "https://postai.bouwmijnshop.nl")
    magic_link = f"{app_url}/?license={license_key}"

    msg = EmailMessage()
    msg['Subject'] = 'Je PostAi Demo Code 🚀'
    msg['From'] = from_email
    msg['To'] = email
    
    body = f"""Hoi {name},

Hier is je toegang tot PostAi.

Demo Licentie: {license_key}

Klik hier om direct in te loggen:
{magic_link}

Succes!
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
    except:
        return False

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
            with open(LEADS_FILE, "r") as f: data = json.load(f)
        except: pass
    data.append(lead)
    with open(LEADS_FILE, "w") as f: json.dump(data, f, indent=2)

def render_landing_page():
    """De geoptimaliseerde compacte landingspagina."""
    
    # CSS: Minder witruimte, strakker op elkaar
    st.markdown("""
    <style>
        /* 1. Haal de standaard Streamlit witruimte weg bovenaan */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1rem !important;
            max-width: 700px !important; /* Iets smaller leest fijner */
        }
        
        /* 2. Header en Tekst compacter */
        .lp-header { 
            font-size: 1.8rem; /* Iets kleiner dan 2.4rem */
            font-weight: 800; 
            color: #111827; 
            line-height: 1.1; 
            margin-bottom: 10px; 
            text-align: center;
        }
        
        .lp-badges { 
            display: flex; gap: 8px; margin-bottom: 15px; 
            justify-content: center; flex-wrap: wrap; 
        }
        .lp-badge { 
            background: #ecfdf5; color: #065f46; padding: 2px 10px; 
            border-radius: 99px; font-size: 0.75rem; font-weight: 600; 
        }
        .lp-badge.blue { background: #eff6ff; color: #1e40af; }
        .lp-badge.gray { background: #f3f4f6; color: #374151; }

        .lp-subhead {
            font-size: 0.95rem; margin-bottom: 8px; text-align: center;
        }
        
        .lp-list { 
            color: #374151; font-size: 0.9rem; line-height: 1.4; 
            margin-bottom: 15px; padding-left: 20px;
            max-width: 90%; margin-left: auto; margin-right: auto;
        }
        .lp-list li { margin-bottom: 4px; }
        
        .lp-small { font-size: 0.8rem; color:#6b7280; text-align:center; margin-bottom: 15px; }

        /* 3. Formulier container strakker */
        div[data-testid="stForm"] {
            padding: 20px !important;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        }
        
        /* Input velden minder witruimte */
        .stTextInput { margin-bottom: -15px !important; }
        p { margin-bottom: 0.2rem !important; }
    </style>
    """, unsafe_allow_html=True)

    # Header Sectie
    st.markdown("""
    <div>
        <div class="lp-header">Dagelijkse TikTok ideeën voor jouw niche.</div>
        
        <div class="lp-badges">
            <span class="lp-badge">✔ Voor creators & shops</span>
            <span class="lp-badge blue">✔ Geen betaalgegevens</span>
            <span class="lp-badge gray">✔ Privacy-proof</span>
        </div>

        <div class="lp-subhead">
            <b>14 dagen gratis toegang.</b> Geen kosten. Je kunt meteen starten.
        </div>

        <ul class="lp-list">
            <li><b>Zien wat werkt</b> voor jouw niche.</li>
            <li><b>Kant-en-klare video-ideeën</b> om direct op te nemen.</li>
            <li><b>Slimme posttijden</b> op basis van jouw account.</li>
        </ul>
        
        <div class="lp-small">
            Vul je gegevens in. Je krijgt direct je demo-code per mail en start meteen.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Formulier (Geen kolommen meer nodig, gewoon strak onder elkaar)
    with st.form("landing_form"):
        name = st.text_input("Naam")
        email = st.text_input("E-mailadres")
        
        # Iets ruimte voor de checkbox, maar minder dan eerst
        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
        
        # Checkbox en tekst naast elkaar
        c_check, c_txt = st.columns([0.06, 0.94])
        with c_check:
            agree = st.checkbox(" ", label_visibility="collapsed")
        with c_txt:
            st.markdown("<div style='font-size:0.8rem; color:#4b5563; padding-top:2px;'>Ik ga akkoord met de <a href='?page=privacy' target='_self'>privacy</a> en <a href='?page=terms' target='_self'>voorwaarden</a>.</div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("🚀 Start mijn gratis demo", use_container_width=True)

        if submitted:
            if not agree:
                st.error("Akkoord vereist.")
            elif "@" not in email:
                st.error("Vul een geldig e-mailadres in.")
            else:
                new_license = str(uuid.uuid4())[:12].upper()
                save_lead(name, email, new_license)
                success = send_license_email(name, email, new_license)
                st.session_state.license_key = new_license
                
                if success:
                    st.toast("Licentie gemaild! Je bent ingelogd.", icon="📧")
                else:
                    st.toast("Ingelogd! (Mail mislukt)", icon="🚀")
                
                time.sleep(1)
                st.rerun()

def activate_pro(key):
    real_key = get_secret("PRO_LICENSE_KEY", PRO_KEY_FIXED)
    if key.strip() == PRO_KEY_FIXED or key.strip() == real_key:
        st.session_state.license_key = key
        st.toast("PRO Geactiveerd!", icon="🎉")
        time.sleep(1)
        st.rerun()
        return True
    else:
        st.error("Ongeldige sleutel.")
        return False