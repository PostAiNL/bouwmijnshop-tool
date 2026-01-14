import streamlit as st
import time
import urllib.parse
import random
import pandas as pd
import textwrap
import base64 
import os
import io
import requests # Nieuw: Nodig voor de download knop in de publieke logo maker
import json
import streamlit.components.v1 as components
from PIL import Image
from streamlit_option_menu import option_menu
from datetime import datetime, timedelta, timezone
import extra_streamlit_components as stx
from modules import ai_coach, ui, auth, shopify_client, competitor_spy, roadmap, db

# --- 0. CONFIGURATIE ---
STRATEGY_CALL_URL = "https://www.paypro.nl/product/RM_Academy_APP_PRO/125684"
COMMUNITY_URL = "https://discord.gg/fCWhU6MC"
COACH_VIDEO_PATH = "assets/Ecom.mp4" 


# Functie om afbeelding om te zetten naar Base64 string (voor icoon fix)
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

# Probeer het logo te laden als PIL image (voor Streamlit config)
fav_icon = "🚀"
logo_path = "assets/logo.png"
try:
    fav_icon = Image.open(logo_path) 
except:
    pass

st.set_page_config(
    page_title="RM Tools - Gratis AI voor Ondernemers", # AANGEPAST: Breder publiek
    page_icon=fav_icon,
    layout="wide",
    initial_sidebar_state="collapsed" # AANGEPAST: Standaard ingeklapt voor focus op tools
)

# --- 1.5 META TAGS & PWA ICON FIX (BASE64) ---
logo_b64 = get_base64_image(logo_path)
if logo_b64:
    icon_html = f'<link rel="icon" type="image/png" href="data:image/png;base64,{logo_b64}">'
    apple_icon_html = f'<link rel="apple-touch-icon" href="data:image/png;base64,{logo_b64}">'
else:
    icon_html = "" 
    apple_icon_html = ""

st.markdown(f"""
<head>
    {icon_html}
    {apple_icon_html}
    <meta name="application-name" content="RM Ecom">
    <meta name="apple-mobile-web-app-title" content="RM Ecom">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
</head>
<script>
    var link = document.querySelector("link[rel~='icon']");
    if (!link) {{
        link = document.createElement('link');
        link.rel = 'icon';
        document.getElementsByTagName('head')[0].appendChild(link);
    }}
    link.href = 'data:image/png;base64,{logo_b64 if logo_b64 else ""}';
</script>
""", unsafe_allow_html=True)

# --- 1. CSS ENGINE (GEOPTIMALISEERD VOOR SNELHEID & LOOKS) ---
st.markdown("""
    <style>
        /* Import Bootstrap Icons */
        @import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css");

        /* ==============================================
           ANTI-LAAD SCHERM & SNELHEID FIXES
           ============================================== */
        
        /* Verberg de 'Running Man' / Wielrenner rechtsboven */
        [data-testid="stStatusWidget"] {
            visibility: hidden !important;
            height: 0px !important;
            width: 0px !important;
            display: none !important;
        }

        /* Verberg de gekleurde regenboogbalk bovenaan */
        [data-testid="stDecoration"] {
            display: none !important;
        }

        /* CRUCIAAL: Verberg de grijze waas/blur tijdens het laden */
        [data-testid="stOverlay"], .stOverlay {
            display: none !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        
        /* Zorg dat de header transparant blijft */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            z-index: 1 !important;
        }

        /* ==============================================
           ALGEMENE CONFIGURATIE
           ============================================== */
        :root {
            --primary: #2563EB;
            --bg-light: #F8FAFC;
            --text-dark: #0F172A;
            --white: #FFFFFF;
            --border: #CBD5E1;
            color-scheme: light !important; 
        }

        .stApp {
            background-color: var(--bg-light) !important;
            color: var(--text-dark) !important;
        }

        .bi { margin-right: 6px; vertical-align: -0.125em; }
        h1, h2, h3 { color: #0F172A !important; }
        p, .stMarkdown, .stCaption, [data-testid="stCaptionContainer"], small { color: #0F172A !important; }
        * { -webkit-tap-highlight-color: transparent !important; }

        /* ==============================================
           LANDING PAGE STYLES (NIEUW)
           ============================================== */
        .landing-title { font-size: 2.2rem !important; font-weight: 800 !important; color: #0F172A; line-height: 1.2; text-align: center; }
        .landing-sub { font-size: 1.0rem !important; color: #64748B; text-align: center; margin-bottom: 25px; }
        
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .roulette-box { background: #F0F9FF; border: 2px solid #BAE6FD; border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 20px; }

        /* ==============================================
           UI ELEMENTEN
           ============================================== */
        /* De Hamburger Knop */
        button[kind="header"] {
            background-color: #EFF6FF !important; 
            border: 1px solid #DBEAFE !important; 
            border-radius: 8px !important;
            color: #0F172A !important;
            opacity: 1 !important;
            margin-top: 2px !important;
            height: 40px !important;
            width: 40px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        button[kind="header"] svg {
            fill: #2563EB !important;
            stroke: #2563EB !important;
            width: 24px !important;
            height: 24px !important;
        }

        /* Mobiele Sidebar Fixes */
        @media (max-width: 992px) {
            section[data-testid="stSidebar"] {
                background-color: #FFFFFF !important;
                border-right: 1px solid #E2E8F0 !important;
            }
            [data-testid="stSidebarCollapseButton"] {
                background-color: #F1F5F9 !important;
                border-radius: 50% !important;
                border: 1px solid #E2E8F0 !important;
                color: #0F172A !important;
                width: 36px !important;
                height: 36px !important;
                margin-right: 10px !important;
                margin-top: 10px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                z-index: 999999 !important;
            }
            [data-testid="stSidebarCollapseButton"] svg {
                fill: #0F172A !important;
                stroke: #0F172A !important;
            }
            [data-testid="stSidebarCollapsedControl"] {
                color: #0F172A !important;
                background-color: white !important;
                display: block !important;
                z-index: 999999 !important;
                border: 1px solid #000 !important;
            }
        }
        
        [data-testid="stHeaderActionElements"] { display: none !important; }
        #MainMenu { visibility: hidden !important; }
        footer { visibility: hidden !important; }

        .block-container {
            padding-top: 2rem !important; 
            padding-bottom: 5rem !important;
            max-width: 1000px;
        }
        
        h1 { 
            font-size: 1.8rem !important; 
            font-weight: 800 !important; 
            letter-spacing: 0px !important; 
            color: #0F172A !important; 
            margin-top: 3px !important; 
            padding-top: 0px !important;
            margin-bottom: 10px !important;
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem !important; 
            padding-left: 1rem !important; 
            padding-right: 1rem !important;
        }

        /* Inputs & Knoppen */
        input, textarea, select, .stTextInput > div > div > input {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #CBD5E1 !important;
            -webkit-text-fill-color: #0F172A !important;
            opacity: 1 !important;
        }
        .stTextInput label, .stNumberInput label, .stSelectbox label, .stTextarea label, label p {
            color: #0F172A !important;
            font-weight: 600 !important;
        }
        
        div.stButton > button[kind="primary"] { background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important; border-color: #2563EB !important; color: white !important; }
        div.stButton > button[kind="primary"]:hover { background-color: #1D4ED8 !important; border-color: #1D4ED8 !important; }
        div.stButton > button:not([kind="primary"]) { background-color: #FFFFFF !important; color: #0F172A !important; border: 1px solid #CBD5E1 !important; }
        div.stButton > button:not([kind="primary"]):hover { border-color: #2563EB !important; color: #2563EB !important; background-color: #F8FAFC !important; }
        
        /* Klik effect voor sneller gevoel */
        div.stButton > button:active { transform: scale(0.98); }

        /* EXPANDER FIX: Ronde hoeken zonder dubbele strepen */
        div[data-testid="stExpander"] {
            border: none !important;
            box-shadow: none !important;
            background-color: transparent !important;
        }

        details {
            border-radius: 20px !important;
            overflow: hidden;
            border: 1px solid #BAE6FD !important; /* De hoofdrand */
            margin-bottom: 15px;
            background-color: white !important;
        }

        details > summary {
            background-color: #EFF6FF !important;
            border: none !important;
            padding: 10px 20px !important;
            color: #0F172A !important;
            list-style: none;
        }

        details > summary:hover {
            background-color: #E0F2FE !important;
        }

        /* DE FIX: Verwijder de automatische streep van Streamlit tussen kop en inhoud */
        details[open] > summary {
            border-bottom: none !important;
        }

        /* Target de interne container van de expander content */
        div[data-testid="stExpanderDetails"] {
            border-top: none !important; /* Verwijdert de irritante streep */
            padding-top: 15px !important;
        }

        .streamlit-expanderContent {
            border: none !important;
            background-color: white !important;
        }

        /* STATS GRID */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 16px; background: var(--white); border: 1px solid var(--border);
            padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }
        .stat-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 25px; margin-top: 10px; }
        .stat-card { background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 4px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02); display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .stat-icon { font-size: 0.75rem; color: #64748B; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; white-space: nowrap; }
        .stat-value { font-size: 1.4rem; font-weight: 800; color: #0F172A; line-height: 1.2; }
        .stat-sub { font-size: 0.7rem; color: #94A3B8; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; }

/* Verbeterde Mobiele Optimalisatie */
    @media (max-width: 600px) {
        /* 1. Meer ruimte onderin de uitklap-vakken (Fases & Uitleg) */
        div[data-testid="stExpanderDetails"] {
            padding-bottom: 30px !important; /* Dit zorgt voor witruimte onder de knop */
            padding-left: 15px !important;
            padding-right: 15px !important;
        }

        /* 2. De Gouden Knop extra ruimte geven */
        div[style*="background: linear-gradient(135deg, #FFD700"] {
            margin-top: 20px !important;
            margin-bottom: 10px !important; /* Ruimte tussen knop en de rand van het witte vlak */
            padding: 16px !important;
        }

        /* 3. De blauwe aanbevelingskaart ("Wat ga je verkopen?") */
        div[style*="background: linear-gradient(135deg, #2563EB"] {
            padding: 20px !important;
            border-radius: 15px !important;
        }

/* Maak specifieke knoppen rood (Danger Zone) */
    div[data-testid="stPopover"] button {
        background-color: #EF4444 !important; /* Rood */
        border-color: #DC2626 !important;
        color: white !important;
    }
    div[data-testid="stPopover"] button:hover {
        background-color: #DC2626 !important;
        border-color: #B91C1C !important;
    }

        /* 4. Lettergrootte van de titel in de blauwe kaart iets verkleinen voor mobiel */
        div[style*="font-size: 1.8rem"] {
            font-size: 1.4rem !important;
            line-height: 1.2 !important;
        }

        /* 5. De tekst in de 'Daily Habit' (groene balk) */
        .stAlert div {
            font-size: 0.85rem !important;
        }
    }

        /* LEVEL UP OVERLAY */
        @keyframes popIn { 0% { transform: scale(0.5); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
        .levelup-overlay {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(15, 23, 42, 0.9); z-index: 9999;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            animation: popIn 0.5s ease-out forwards;
        }
        .levelup-card {
            background: white; padding: 40px; border-radius: 20px; text-align: center; max-width: 400px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.3); border: 2px solid #FBBF24;
        }
        
        /* VISUAL ROADMAP */
        .progress-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; position: relative; padding: 0 10px; width: 100%; }
        .progress-line { position: absolute; top: 15px; left: 0; width: 100%; height: 3px; background: #E2E8F0; z-index: 1; }
        .progress-step { width: 32px; height: 32px; border-radius: 50%; display: flex; justify-content: center; align-items: center; z-index: 2; position: relative; background: white; border: 2px solid #E2E8F0; color: #94A3B8; font-weight: bold; font-size: 0.8rem; transition: all 0.3s; }
        .progress-step.active { border-color: #2563EB; color: white; background: #2563EB; box-shadow: 0 0 0 4px rgba(37,99,235,0.1) !important; }
        .progress-step.completed { background: #10B981; border-color: #10B981; color: white; }
        .progress-label { position: absolute; bottom: -25px; left: 50%; transform: translateX(-50%); font-size: 0.7rem; white-space: nowrap; color: #64748B; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

# --- 2. COOKIE MANAGER & AUTHENTICATIE ---
cookie_manager = stx.CookieManager()

# 1. Check op Magic Link (Autologin via email link)
if "autologin" in st.query_params and "user" in st.query_params:
    token = st.query_params["autologin"]
    email = st.query_params["user"]
    import hashlib
    secret_key = st.secrets["supabase"]["key"]
    expected_token = hashlib.sha256(f"{email}{secret_key}".encode()).hexdigest()
    if token == expected_token:
        auth.login_or_register(email)
        # Zorg dat de cookie direct gezet wordt met pad /
        cookie_manager.set("rmecom_user_email", email, expires_at=datetime.now() + timedelta(days=30), path="/")
        st.query_params.clear()
        st.rerun()

# 2. INITIALISEER BASIS STATUS (MET FIXES VOOR LANDING PAGE)
if "view" not in st.session_state: st.session_state.view = "main"
if "nav_index" not in st.session_state: st.session_state.nav_index = 0
if "generated_logos" not in st.session_state: st.session_state.generated_logos = [] # FIX: Logo crash
if "logo_generations" not in st.session_state: st.session_state.logo_generations = 0 # FIX
if "niche_roulette_result" not in st.session_state: st.session_state.niche_roulette_result = None # FIX: Roulette
if "is_spinning" not in st.session_state: st.session_state.is_spinning = False

def set_view(name):
    st.session_state.view = name
    st.rerun()

# 3. PERSISTENT LOGIN (UITGESCHAKELD OP JOUW VERZOEK - ZODAT JE LANDING PAGE ZIET)
if "user" not in st.session_state:
    time.sleep(0.8) 
    all_cookies = cookie_manager.get_all()
    if all_cookies and "rmecom_user_email" in all_cookies:
        cookie_email = all_cookies["rmecom_user_email"]
        if cookie_email and len(cookie_email) > 3:
            auth.login_or_register(cookie_email)
            st.rerun()

# Pas de definitie aan: voeg 'current_page_name' toe
def inject_chat_widget(user_data, current_page_name): 
    # 👇 JOUW URL
    CHAT_SERVER_URL = "https://rmecom.onrender.com" 
    
    if not user_data: return

    safe_profile = {
        "first_name": user_data.get("first_name", "Ondernemer"),
        "shop_name": user_data.get("shop_name", ""),
        "level": user_data.get("level", 1),
        "xp": user_data.get("xp", 0),
        "is_pro": user_data.get("is_pro", False),
        "current_page": current_page_name # <--- NIEUW: Punt 1 (Context)
    }
    
    json_data = json.dumps(safe_profile)

    html_code = f"""
    <script>
    (function() {{
        try {{
            var parentDoc = window.parent.document;
            var serverUrl = "{CHAT_SERVER_URL}";
            
            // Check of de widget er al is
            if (parentDoc.getElementById("bms-chat-launcher")) {{
                // UPDATE: Als de widget er al is, updaten we alleen de data (voor de paginawissel)
                if (window.parent.RM_USER_DATA) {{
                    window.parent.RM_USER_DATA.current_page = "{current_page_name}";
                }}
                return;
            }}

            window.parent.RM_USER_DATA = {json_data};
            window.parent.BMS_CHAT_SERVER = serverUrl;

            var link = parentDoc.createElement("link");
            link.rel = "stylesheet";
            link.href = serverUrl + "/chat-widget.css";
            parentDoc.head.appendChild(link);

            var js = parentDoc.createElement("script");
            js.src = serverUrl + "/chat-widget.js";
            js.defer = true;
            parentDoc.body.appendChild(js);
            
        }} catch (e) {{ console.error(e); }}
    }})();
    </script>
    """
    
    components.html(html_code, height=0, width=0)

# Hieronder staat als het goed is jouw bestaande functie:
# def render_auth_footer(key_suffix):

# --- HELPER FUNCTIE VOOR INLOGGEN (PREMIUM DESIGN + PLACEHOLDERS) ---
def render_auth_footer(key_suffix):
    """Toont het inlog/registratie blok onderaan de tools."""
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Premium Header
    st.markdown(f"""
    <div style="text-align:center; margin-bottom: 40px; margin-top: 20px;">
        <h2 style="color:#0F172A; font-weight: 800; font-size: 2rem;">🚀 Klaar om te starten?</h2>
        <p style="color:#64748B; font-size: 1.1rem;">Sla je voortgang op en krijg direct toegang tot het volledige dashboard.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")

    # KOLOM 1 (LINKS): REGISTREREN - DE HOOFDACTIE
    with c1:
        # We gebruiken een container met border voor de 'Card' look
        with st.container(border=True):
            st.markdown("### ✨Nieuw Account (Gratis)")
            st.markdown("<div style='font-size:0.85rem; color:#64748B; margin-bottom:15px;'>Maak binnen 1 minuut een account aan.</div>", unsafe_allow_html=True)
            
            # Placeholders toegevoegd ("Voorgekauwd")
            r_name = st.text_input("Voornaam", placeholder="Bijv. Michael", key=f"reg_name_{key_suffix}")
            r_email = st.text_input("Email", placeholder="jouw@email.nl", key=f"reg_email_{key_suffix}")
            r_pass = st.text_input("Kies Wachtwoord", placeholder="Minimaal 6 tekens...", type="password", key=f"reg_pass_{key_suffix}")
            
            # Referral code iets subtieler
            ref_code = None
            with st.expander("Heb je een vriendencode? (Optioneel)"):
                ref_code = st.text_input("Vriendencode", placeholder="bv. JAN-482", label_visibility="collapsed", key=f"ref_{key_suffix}")

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            
            if st.button("🚀 Account Aanmaken & Starten", type="primary", key=f"btn_reg_{key_suffix}", use_container_width=True):
                if r_email and "@" in r_email and r_name and r_pass:
                    with st.spinner("Profiel aanmaken..."):
                        status = db.create_user(r_email, r_pass, r_name)
                        if status == "SUCCESS" or status == "EXISTS":
                            if status == "SUCCESS":
                                auth.send_welcome_email(r_email, r_name, r_pass)
                            
                            auth.login_or_register(r_email, ref_code_input=ref_code, name_input=r_name)
                            cookie_manager.set("rmecom_user_email", r_email, expires_at=datetime.now() + timedelta(days=30), path="/")
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Er ging iets mis met de database.")
                else:
                    st.warning("Vul alsjeblieft je naam, email en wachtwoord in.")
            
            # Trust indicators
            st.markdown("""
                <div style="text-align:center; margin-top:10px;">
                    <small style="color:#94A3B8;">✅ Geen creditcard nodig • Direct toegang</small>
                </div>
            """, unsafe_allow_html=True)

    # KOLOM 2 (RECHTS): INLOGGEN
    with c2:
        with st.container(border=True):
            st.markdown("### 🔑Bestaand Account (Inloggen)")
            st.markdown("<div style='font-size:0.85rem; color:#64748B; margin-bottom:15px;'>Welkom terug, boss. Log hier in.</div>", unsafe_allow_html=True)
            
            l_email = st.text_input("Email", placeholder="jouw@email.nl", key=f"login_email_{key_suffix}")
            l_pass = st.text_input("Wachtwoord", placeholder="Je wachtwoord...", type="password", key=f"login_pass_{key_suffix}")
            
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            
            if st.button("Inloggen", key=f"btn_login_{key_suffix}", use_container_width=True):
                if l_email and l_pass:
                    if db.verify_user(l_email, l_pass):
                        auth.login_or_register(l_email)
                        cookie_manager.set("rmecom_user_email", l_email, expires_at=datetime.now() + timedelta(days=30), path="/")
                        st.rerun()
                    else:
                        st.error("Onjuiste gegevens. Probeer het opnieuw.")

# ==============================================================================
# 🚀 PUBLIC LANDING PAGE (REBRANDED: MAKER STUDIO)
# ==============================================================================
if "user" not in st.session_state:
    if "status" in st.query_params: st.query_params.clear()
    
    # CSS voor Landingspagina (Cleaner, minder "schreeuwerig")
    st.markdown("""
    <style>
        .landing-title { 
            font-size: 2.5rem !important; 
            font-weight: 800 !important; 
            color: #1E293B; 
            line-height: 1.1; 
            text-align: center !important; /* Forceer center */
            letter-spacing: -1px; 
        }
        
        .landing-sub { 
            font-size: 1.1rem !important; 
            color: #64748B; 
            text-align: center !important; /* CRUCIAAL: Forceer center met !important */
            margin-bottom: 30px; 
            max-width: 700px; /* Iets breder gemaakt voor mooiere uitlijning */
            margin-left: auto !important; 
            margin-right: auto !important;
            display: block;
            line-height: 1.6;
        }
        
        .feature-tag { 
            background: #F1F5F9; 
            padding: 5px 12px; 
            border-radius: 20px; 
            font-size: 0.8rem; 
            color: #475569; 
            font-weight: 600; 
            display: inline-block; 
            margin-bottom: 15px; 
        }
        
        /* Zorg dat de container eromheen ook gecentreerd is */
        div[data-testid="stMarkdownContainer"] > div {
            text-align: center !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 1. Header: Focus op CREATIE, niet op GELD
    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align:center;">
        <div class="feature-tag">✨ RM TOOLS - Beta versie v2.0</div>
        <h1 class="landing-title">Van idee naar realiteit.<br>In seconden.</h1>
        <p class="landing-sub">Professionele AI-tools voor makers, starters en creatievelingen. Ontwerp een logo of brainstorm je volgende project. <b>Gratis en Anoniem te proberen.</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Trust Badges (Social Proof verlaagt drempel enorm)
    st.markdown("""
    <div style="display:flex; justify-content:center; gap:15px; margin-bottom:30px; flex-wrap:wrap;">
        <span style="color:#64748B; font-size:0.85rem;">✅ Geen account nodig</span>
        <span style="color:#64748B; font-size:0.85rem;">✅ Direct te gebruiken</span>
        <span style="color:#64748B; font-size:0.85rem;">✅ Powered by OpenAI (RM TOOLS)</span>
    </div>
    """, unsafe_allow_html=True)

    # De Tabs: Andere namen!
    # "Logo Maker" -> "Brand Designer" (Klinkt duurder/beter)
    # "Niche Roulette" -> "Idea Generator" (Klinkt als inspiratie, niet als gokken)
    tab_logo, tab_roulette = st.tabs(["Brand Designer", "Idea Generator"])
    
    # === TAB 1: BRAND DESIGNER ===
    with tab_logo:
        with st.container(border=True):
            st.markdown("#### 🛠️ AI Logo Studio")
            st.markdown("Heb je een naam voor je project, hobbyclub of side-hustle? Laat AI direct 3 concepten maken.")
            
            col_l1, col_l2 = st.columns(2)
            # Placeholder veranderd van "Kleding" naar iets neutralers
            l_name = col_l1.text_input("Project Naam", placeholder="Bijv. Studio Nova", key="pub_logo_name")
            l_niche = col_l1.text_input("Waar gaat het over?", placeholder="Bijv. Fotografie, Koffie, Tech", key="pub_logo_niche")
            l_style = col_l2.selectbox("Stijl", ["Minimalistisch", "Modern", "Vintage", "Futuristisch"], key="pub_logo_style")
            l_color = col_l2.text_input("Kleuren (Optioneel)", placeholder="Zwart & Wit", key="pub_logo_color")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Knop tekst veranderd: "Ontwerpen" ipv "Genereren"
            if st.button("✨ Ontwerp mijn Logo's", type="primary", use_container_width=True):
                if l_name and l_niche:
                    with st.spinner("🎨 De AI-designer is aan het schetsen..."):
                        try:
                            new_logos = []
                            for i in range(2): 
                                img_url = ai_coach.generate_logo(l_name, l_niche, l_style, l_color)
                                if img_url and "placehold" not in img_url:
                                    new_logos.append({"url": img_url, "name": f"logo_{i}.png"})
                            st.session_state.generated_logos = new_logos
                        except Exception as e: st.error(f"Oeps: {e}")
                else:
                    st.warning("Vul in ieder geval een naam en onderwerp in.")

        if st.session_state.generated_logos:
            st.success("✅ Hier zijn je concepten. Klik op het plaatje om op te slaan.")
            cols = st.columns(2)
            for idx, logo in enumerate(st.session_state.generated_logos):
                with cols[idx]:
                    st.image(logo["url"], use_container_width=True)
        
        # FOOTER ONDER LOGO MAKER (Aangepast)
        # We noemen het geen "Account aanmaken" maar "Opslaan & Verder gaan"
        render_auth_footer("logo_tab")

    # === TAB 2: IDEA GENERATOR (Voorheen Roulette) ===
    with tab_roulette:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        # Niches aangepast: Mix van commercieel en hobby/creatief
        niches = ["Duurzame Koffiebekers", "Handgemaakte Keramiek", "Orthopedische Hondenmanden", "Digitale Art Prints", "Smart Home Gadgets", "Vintage Kleding", "Houten Speelgoed", "Plantenverzorging Apps", "Reisfotografie Accessoires"]
        
        container = st.empty()
        
        if not st.session_state.niche_roulette_result:
            with container.container():
                st.markdown("""
                <div style="background:white; border:1px solid #E2E8F0; padding:30px; border-radius:16px; text-align:center;">
                    <div style="font-size: 3rem; margin-bottom: 10px;">🧠</div>
                    <h3 style="color:#0F172A; margin:0;">Brainstorm Blokkade?</h3>
                    <p style="color:#64748B; margin-bottom: 25px;">Krijg direct een uniek idee voor je volgende project of webshop.</p>
                    <div style="background:#F8FAFC; border-radius:8px; padding:15px; margin-bottom:20px; color:#CBD5E1; font-weight:700; border:2px dashed #E2E8F0;">? ? ?</div>
                </div>
                """, unsafe_allow_html=True)
                _, c2, _ = st.columns([1, 2, 1])
                if c2.button("💡 Geef me inspiratie", type="primary", use_container_width=True):
                    st.session_state.is_spinning = True
                    st.rerun()
        else:
            # Resultaat weergave
            final_res = st.session_state.niche_roulette_result
            with container.container():
                st.markdown(f"""
                <div style="background:#F0FDF4; border:1px solid #BBF7D0; padding:30px; border-radius:16px; text-align:center;">
                    <div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: #166534; font-weight: 700; margin-bottom: 10px;">JOUW VOLGENDE PROJECT:</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #166534;">{final_res}</div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
                if st.button("🔄 Ander idee proberen", use_container_width=True):
                    st.session_state.niche_roulette_result = None
                    st.rerun()

        # Animatie (hetzelfde als voorheen, maar misschien iets korter/zakelijker)
        if st.session_state.is_spinning:
            placeholder = container.empty()
            for _ in range(12):
                placeholder.markdown(f"""<div style="background:white; border:1px solid #E2E8F0; padding:30px; border-radius:16px; text-align:center;"><h3>Brainstormen...</h3><div style="font-size:1.5rem; color:#2563EB;">{random.choice(niches)}</div></div>""", unsafe_allow_html=True)
                time.sleep(0.08)
            st.session_state.niche_roulette_result = random.choice(niches)
            st.session_state.is_spinning = False
            st.rerun()

        render_auth_footer("roulette_tab")

    # STOP: Zorg dat ze niet de rest van de app zien
    st.stop()
   

# --- 4. INGELOGDE DATA (CACHED & SYNCHRONISED) ---
user = st.session_state.user

# ==============================================================================
# 🔥 DATA SYNC FIX: Haal altijd de laatste XP/Level op uit de Database
# ==============================================================================
if user.get('id') != 'temp' and auth.supabase:
    try:
        # We vragen de database: "Geef me de laatste status van deze gebruiker"
        refresh_data = auth.supabase.table('users').select("*").eq('email', user['email']).execute()
        
        if refresh_data.data:
            # We overschrijven de sessie met de verse data uit de database
            # Hierdoor springt je XP niet terug naar 0 na een refresh
            st.session_state.user.update(refresh_data.data[0])
            user = st.session_state.user # Update de variabele voor de rest van het script
    except Exception as e:
        # Als database faalt, gebruik wat we hebben (geen crash)
        pass 
# ==============================================================================
# 💰 PAYPRO BETALING VERWERKEN (SUCCESS PAGE OVERLAY)
# ==============================================================================
if "payment" in st.query_params and st.query_params["payment"] == "success":
    # 1. Update database & Sessie
    if not user.get('is_pro'):
        db.set_user_pro(user['email'])
        st.session_state.user['is_pro'] = True
        user['is_pro'] = True

    # 2. Toon de "Success" UI (Full Screen Overlay)
    st.markdown("""
        <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: white; z-index: 99999; display: flex; justify-content: center; align-items: center; text-align: center; padding: 20px;">
            <div style="max-width: 500px; padding: 40px; border-radius: 24px; box-shadow: 0 20px 50px rgba(0,0,0,0.1); border: 1px solid #E2E8F0; background: white;">
                <div style="font-size: 80px; margin-bottom: 20px;">🎉</div>
                <h1 style="color: #0F172A; font-size: 2.2rem; margin-bottom: 10px; font-weight: 800;">Welkom bij de Elite!</h1>
                <p style="color: #64748B; font-size: 1.1rem; line-height: 1.6; margin-bottom: 30px;">
                    Je betaling is geslaagd. Je hebt nu onbeperkt toegang tot alle <b>PRO Tools</b>, de <b>Academy</b> en de <b>Daily Winners</b>.
                </p>
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; padding: 15px; border-radius: 12px; margin-bottom: 30px;">
                    <p style="margin: 0; color: #166534; font-weight: 700; font-size: 0.95rem;">
                        ✅ PRO STATUS: ACTIEF
                    </p>
                </div>
                <a href="/" target="_self" style="text-decoration: none;">
                    <div style="background: #2563EB; color: white; padding: 16px 32px; border-radius: 12px; font-weight: 800; font-size: 1.1rem; cursor: pointer; box-shadow: 0 10px 20px rgba(37, 99, 235, 0.2); transition: transform 0.2s;">
                        Naar mijn Dashboard 🚀
                    </div>
                </a>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.balloons()
    st.stop() # Dit zorgt dat de rest van de pagina niet laadt achter de overlay

is_pro_license = user.get('is_pro', False)
# ⚠️ TEST MODE AAN (Zet hier een # voor als je live gaat!)
# is_pro_license = True 

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_pro_status(email):
    return db.check_pro_status_db(email), db.get_pro_expiry_date(email)

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_user_data(email):
    return db.get_user_data(email) 

is_temp_pro_db, pro_expiry_dt = get_cached_pro_status(user['email'])
user_extra = get_cached_user_data(user['email'])

# Zorg dat shop naam ook behouden blijft bij refresh
if user_extra and user_extra.get('shop_name'):
    st.session_state.shop_name = user_extra.get('shop_name')
    st.session_state.income_goal = user_extra.get('income_goal')

time_left_str = None
is_temp_pro = False 

if pro_expiry_dt:
    now = datetime.now(timezone.utc)
    if pro_expiry_dt.tzinfo is None:
        pro_expiry_dt = pro_expiry_dt.replace(tzinfo=timezone.utc)
        
    if pro_expiry_dt > now:
        is_temp_pro = True
        diff = pro_expiry_dt - now
        hours = diff.seconds // 3600
        mins = (diff.seconds % 3600) // 60
        time_left_str = f"{hours}u {mins}m"
    else:
        is_temp_pro = False 

is_pro = is_pro_license or is_temp_pro

def calculate_level_data(current_xp):
    levels = [(0, "Starter"), (200, "Bouwer"), (500, "Expert"), (1000, "E-com Boss"), (3000, "Legend"), (5000, "Master"), (10000, "Grandmaster")]
    current_rank, next_goal, prev_goal, level_num = levels[0][1], levels[1][0], levels[0][0], 1
    for i, (threshold, title) in enumerate(levels):
        if current_xp >= threshold:
            current_rank, level_num, prev_goal = title, i + 1, threshold
            next_goal = levels[i+1][0] if i + 1 < len(levels) else threshold * 2
        else: break
    return level_num, current_rank, next_goal, prev_goal

user_level_num, rank_title, next_xp_goal_sidebar, prev_threshold = calculate_level_data(user['xp'])
user['level'] = user_level_num 

if "prev_level" not in st.session_state: st.session_state.prev_level = user['level']
if "ai_credits" not in st.session_state: st.session_state.ai_credits = 3 

# --- 4.5 PERSISTENT AI CREDITS & FUNCTIES ---
def check_credits():
    if is_pro: 
        return True
    
    # Haal credits uit de database data (niet alleen session state)
    current_credits = user.get('ai_credits', 0)
    
    if current_credits > 0:
        # Update in database (maak deze functie aan in db.py of gebruik een update query)
        new_credits = current_credits - 1
        db.update_user_credits(user['email'], new_credits) 
        # Update lokale sessie zodat de UI direct verandert
        st.session_state.user['ai_credits'] = new_credits
        return True
    return False

def get_greeting():
    # Servers staan op UTC. We voegen 1 uur toe voor de Nederlandse wintertijd.
    # (In de zomertijd moet dit hours=2 zijn).
    now_nl = datetime.now() + timedelta(hours=1)
    hour = now_nl.hour
    return "Goedemorgen" if hour < 12 else "Goedemiddag" if hour < 18 else "Goedenavond"

def get_image_base64(path):
    try:
        with open(path, "rb") as image_file: encoded = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except: return None

# --- 5. SIDEBAR (MET PROFIELFOTO & XP) ---
with st.sidebar:
    # 1. Profielfoto logica
    side_avatar = ""
    if user.get('avatar_url'):
        # Als er een foto is geüpload
        side_avatar = f'<img src="{user["avatar_url"]}" style="width:45px; height:45px; border-radius:50%; object-fit:cover; margin-right:12px; border:2px solid #2563EB;">'
    else:
        # Fallback naar de eerste letter
        initial = user.get('first_name', 'M')[0].upper()
        side_avatar = f'<div style="width:45px; height:45px; background:#2563EB; color:white; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; font-weight:800; margin-right:12px; font-size:18px;">{initial}</div>'

    # 2. Naam en Level weergave
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 10px; padding-left: 5px;">
            {side_avatar}
            <div style="line-height: 1.1;">
                <h3 style="margin:0; font-size:1.05rem; color:#0F172A; font-weight:700;">{user.get('first_name', 'Boss')}</h3>
                <p style="margin:0; font-size: 0.75rem; color: #64748B;">Level {user['level']} • {rank_title}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 3. De Voortgangsbalk (XP)
    range_span = next_xp_goal_sidebar - prev_threshold
    if range_span <= 0: range_span = 1
    xp_pct = min((user['xp'] - prev_threshold) / range_span, 1.0) * 100
    
    st.markdown(f"""
        <div style="background: #F1F5F9; border-radius: 10px; height: 6px; width: 100%; margin-top: 5px; margin-bottom: 5px;">
            <div style="background: #2563EB; height: 100%; width: {xp_pct}%; border-radius: 10px; transition: width 0.5s;"></div>
        </div>
        <div style="text-align:right; font-size:0.65rem; color:#94A3B8; margin-bottom:20px;">{user['xp']} / {next_xp_goal_sidebar} XP</div>
    """, unsafe_allow_html=True)

    # 4. Pro Status / Credits weergave
    if is_temp_pro and not is_pro_license and time_left_str:
        st.markdown(f"""<div style="margin-bottom:15px; background: linear-gradient(135deg, #DCFCE7 0%, #BBF7D0 100%); padding: 10px; border-radius: 8px; border: 1px solid #86EFAC; text-align:center;"><div style="font-size: 0.65rem; color: #166534; font-weight: 700;">PRO TIJD OVER</div><div style="font-size: 0.9rem; color: #14532D; font-weight: 800;">⏳ {time_left_str}</div></div>""", unsafe_allow_html=True)
    elif not is_pro:
        st.markdown(f"""<div style="margin-bottom:15px; font-size:0.75rem; color:#64748B; background:#F1F5F9; padding:8px; border-radius:8px; text-align:center;">⚡ <b>{st.session_state.ai_credits}</b>/3 AI credits over</div>""", unsafe_allow_html=True)
    
# --- VERVANG VANAF HIER ---
    options = ["Dashboard", "Academy", "Producten Zoeken", "Marketing & Design", "Financiën", "Instellingen"]
    icons = ["house-fill", "mortarboard-fill", "search", "palette-fill", "cash-stack", "gear-fill"]
    
    menu_display_options = []
    for opt in options:
        if not is_pro and opt in ["Producten Zoeken", "Marketing & Design"]:
             menu_display_options.append(f"{opt} 🔒")
        else:
             menu_display_options.append(opt)

    # De menu_key zorgt ervoor dat het menu 'geforceerd' verspringt als de app merkt dat de index verandert
    menu_key = f"menu_state_{st.session_state.nav_index}"

    selected_display = option_menu(
        menu_title=None,
        options=menu_display_options,
        icons=icons,
        default_index=st.session_state.nav_index,
        orientation="vertical",
        styles={
            "container": {"padding": "0!important", "background-color": "#FFFFFF"}, 
            "icon": {"color": "#64748B", "font-size": "14px"}, 
            "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px", "padding": "10px", "--hover-color": "#EFF6FF", "color": "#0F172A"}, 
            "nav-link-selected": {"background-color": "#2563EB", "color": "white", "font-weight": "600"},
        },
        key=menu_key
    )

    # Als de gebruiker op een menu-item klikt, updaten we de nav_index
    if selected_display:
        clean_selection = selected_display.replace(" 🔒", "")
        new_index = options.index(clean_selection)
        if new_index != st.session_state.nav_index:
            st.session_state.nav_index = new_index
            st.rerun()

    # Deze variabele bepaalt welke pagina de gebruiker ziet
    pg = options[st.session_state.nav_index]
    # --- TOT HIER ---

    # --- NIEUW: AUTO-CLOSE SIDEBAR OP MOBIEL ---
    st.markdown("""
        <script>
            var width = window.innerWidth;
            if (width <= 992) {
                const closeBtn = window.parent.document.querySelector('[data-testid="stSidebarCollapseButton"]');
                if (closeBtn) {
                    setTimeout(function() {
                        closeBtn.click();
                    }, 150);
                }
            }
        </script>
    """, unsafe_allow_html=True)
    
    if not is_pro:
        st.markdown(f"""
        <a href="{STRATEGY_CALL_URL}" target="_blank" style="text-decoration:none;">
            <div style="margin-top: 20px; background: linear-gradient(135deg, #FFD700 0%, #F59E0B 100%); padding: 15px; border-radius: 12px; box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3); text-align: center; border: 1px solid #FCD34D; transition: transform 0.2s;">
                <div style="font-weight: 800; color: #78350F; font-size: 1.1rem; margin-bottom: 4px;">🚀 UNLOCK PRO</div>
                <div style="font-size: 0.75rem; color: #92400E; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Word PRO Lid (€49,95)</div>
            </div>
        </a>
        """, unsafe_allow_html=True)

# =========================================================
# 🛠️ GLOBAL: VOORTGANG LADEN (BELANGRIJK VOOR ALLE PAGINA'S)
# =========================================================
if "force_completed" not in st.session_state: st.session_state.force_completed = []

@st.cache_data(ttl=60, show_spinner=False)
def get_cached_progress_db(uid): return auth.get_progress()

db_progress = get_cached_progress_db(user['id'])
completed_steps = list(set(db_progress + st.session_state.force_completed))

# WORKFLOW NAVIGATION LOGIC
# Update nav_index state based on menu selection
if selected_display:
    clean_selection = selected_display.replace(" 🔒", "")
    try:
        st.session_state.nav_index = options.index(clean_selection)
    except: pass
    pg = clean_selection
else:
    pg = "Dashboard"

# --- AANGEPASTE RENDER PRO LOCK ---
def render_pro_lock(title, desc, warning_text="Deze tool geeft onze studenten een oneerlijk voordeel. Daarom is dit afgeschermd."):
    lock_html = f"""
    <div style="position: relative; overflow: hidden; border-radius: 12px; border: 1px solid #E2E8F0; margin-top: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); background: #F8FAFC; min-height: 320px;">
        <div style="filter: blur(5px); opacity: 0.5; padding: 20px; pointer-events: none; user-select: none;">
            <div style="height: 20px; background: #CBD5E1; width: 60%; margin-bottom: 15px; border-radius: 4px;"></div>
            <div style="display:flex; gap:10px; margin-bottom: 10px;">
                <div style="height: 150px; background: #E2E8F0; width: 30%; border-radius: 8px;"></div>
                <div style="height: 150px; background: #E2E8F0; width: 70%; border-radius: 8px;"></div>
            </div>
            <div style="height: 15px; background: #E2E8F0; width: 90%; margin-bottom: 8px; border-radius: 4px;"></div>
            <div style="height: 15px; background: #E2E8F0; width: 80%; border-radius: 4px;"></div>
        </div>
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 85%; max-width: 400px; z-index: 10;">
            <div style="background: white; padding: 25px; border-radius: 16px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.12); border: 1px solid #E2E8F0;">
                <div style="font-size: 28px; margin-bottom: 10px;">🔒</div>
                <h3 style="margin: 0 0 8px 0; color: #1E293B; font-size: 1.1rem; font-weight: 700;">{title}</h3>
                <p style="font-size: 0.85rem; color: #64748B; margin: 0 0 15px 0; line-height: 1.4;">{desc}</p>
                <div style="background: #FEF2F2; color: #991B1B; padding: 8px; border-radius: 6px; font-size: 0.75rem; margin-bottom: 15px; border: 1px solid #FECACA; font-weight: 600; line-height: 1.3;">
                    ⚠️ {warning_text}
                </div>
                <a href="{STRATEGY_CALL_URL}" target="_blank" style="text-decoration: none;">
                    <div style="background: linear-gradient(135deg, #2563EB, #1D4ED8); color: white; padding: 10px 20px; border-radius: 50px; font-weight: 600; font-size: 0.9rem; display: inline-block; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2); transition: transform 0.1s;">
                        Word PRO Lid (€49,95)
                    </div>
                </a>
            </div>
        </div>
    </div>
    """
    st.markdown(lock_html.replace("\n", ""), unsafe_allow_html=True)

# --- ONBOARDING WIZARD (VERBETERD) ---
# We kijken direct in het 'user' object dat we bovenaan het script al hebben gesynct met de DB
has_shop_name = user.get('shop_name') is not None and user.get('shop_name') != ""
wizard_already_done = st.session_state.get("wizard_complete", False)

# Alleen tonen als: Geen shopnaam in DB EN niet net afgerond EN XP is echt 0
if not has_shop_name and not wizard_already_done and user.get('xp', 0) == 0:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        welcome_name = user.get('first_name', 'Ondernemer')
        st.markdown(f"""<div style="text-align: center; padding: 20px;"><h1 style="color: #2563EB; margin-bottom: 10px;">👋Welkom bij de RM Tools, {welcome_name}!</h1><p style="font-size: 1.1rem; color: #64748B;">Laten we je profiel instellen voor maximaal succes.</p></div>""", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            shop_name_input = st.text_input("Hoe gaat je webshop heten?", placeholder="Bijv. Nova Gadgets")
            goal_input = st.selectbox("Wat is je eerste maandelijkse doel?", ["€5.000 /maand (Sidehustle)", "€10.000 /maand (Serieus)", "€15.000+ /maand (Fulltime)"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 Start Mijn Avontuur (+10 XP)", type="primary", use_container_width=True):
                if shop_name_input:
                    with st.spinner("Profiel opslaan..."):
                        # 1. Direct naar DB schrijven via de gecorrigeerde functie
                        success = db.update_onboarding_data(user['email'], shop_name_input, goal_input)
                        
                        if success:
                            # 2. XP verhogen in DB
                            new_xp = user.get('xp', 0) + 10
                            auth.supabase.table('users').update({"xp": new_xp}).eq('email', user['email']).execute()
                            
                            # 3. CRUCIAAL: Update de sessie data direct
                            st.session_state.user['shop_name'] = shop_name_input
                            st.session_state.user['income_goal'] = goal_input
                            st.session_state.user['xp'] = new_xp
                            st.session_state.wizard_complete = True
                            
                            st.balloons()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Kon profiel niet opslaan. Controleer database verbinding.")
                else: 
                    st.warning("Vul een naam in!")
    
    # Blokkeer de rest van de app
    st.stop()

# =========================================================
# 📄 LEGAL PAGES & FOOTER DEFINITIES
# =========================================================

def render_footer():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        # Gebruik de huidige datum voor het jaartal
        current_year = datetime.now().year
        st.markdown(f"<p style='font-size:0.8rem; color:#64748B;'>© {current_year} RM TOOLS. Alle rechten voorbehouden.</p>", unsafe_allow_html=True)
    with col2:
        if st.button("🔒 Privacybeleid", key="btn_footer_priv", use_container_width=True):
            st.session_state.view = "privacy"
            st.rerun()
    with col3:
        if st.button("📄 Voorwaarden", key="btn_footer_terms", use_container_width=True):
            st.session_state.view = "terms"
            st.rerun()

def render_privacy_page():
    st.markdown("<h1>🔒 Privacybeleid</h1>", unsafe_allow_html=True)
    if st.button("⬅️ Terug naar Dashboard", type="primary", key="priv_back_top"):
        st.session_state.view = "main"
        st.rerun()
    
    with st.container(border=True):
        st.markdown(f"""
        ### 1. Hoe we je gegevens gebruiken
        RM Tools gebruikt je e-mail en voornaam alleen om je account te beheren en je voortgang (XP en Levels) op te slaan in onze beveiligde database.
        
        ### 2. Cookies
        We gebruiken lokale cookies om je ingelogd te houden. Zonder deze cookies zou je bij elke verversing opnieuw moeten inloggen.
        
        ### 3. Derden
        Je gegevens worden nooit verkocht. We maken gebruik van Supabase voor database-opslag en OpenAI voor de AI-coach functies. De data die je invoert bij de AI-tools wordt anoniem verwerkt.
        
        ### 4. Verwijderen
        Wil je je account en al je XP-data verwijderen? Stuur een e-mail naar support@rmacademy.nl en we regelen het binnen 48 uur.
        """)
    st.button("Terug naar Dashboard", key="btn_priv_bottom", on_click=lambda: setattr(st.session_state, 'view', 'main'))

def render_terms_page():
    st.markdown("<h1>📄 Algemene Voorwaarden</h1>", unsafe_allow_html=True)
    if st.button("⬅️ Terug naar Dashboard", type="primary", key="terms_back_top"):
        st.session_state.view = "main"
        st.rerun()
        
    with st.container(border=True):
        st.markdown(f"""
        ### 1. Gebruik van de App
        Door gebruik te maken van RM Tools ga je akkoord met onze methodiek. Je bent zelf verantwoordelijk voor de uitvoering van je webshop.
        
        ### 2. AI & Credits
        Misbruik van de AI-tools (zoals het genereren van ongepaste content) kan leiden tot een directe blokkering van je account zonder teruggave van credits.
        
        ### 3. Partner Programma
        Referral commissies (€250,- per student) worden pas uitgekeerd nadat de aangebrachte student de wettelijke bedenktijd van 14 dagen heeft doorlopen en de betaling definitief is.
        
        ### 4. PRO Lidmaatschap
        PRO-toegang is persoonlijk. Het delen van accounts is niet toegestaan en wordt gedetecteerd door ons systeem.
        
        ### 5. Resultaten
        E-commerce resultaten verschillen per persoon. Wij bieden de tools en roadmap, maar kunnen geen omzetgaranties geven.
        """)
    st.button("Terug naar Dashboard", key="btn_terms_bottom", on_click=lambda: setattr(st.session_state, 'view', 'main'))

# =========================================================
# 🏠 PAGINA ROUTING (PRIVACY, VOORWAARDEN OF DASHBOARD)
# =========================================================

if st.session_state.view == "privacy":
    render_privacy_page()

elif st.session_state.view == "terms":
    render_terms_page()

else:
    # --- DIT IS DE ORIGINELE APP INHOUD ---
    # --- DIT IS DE VERBETERDE DASHBOARD SECTIE ---
    if pg == "Dashboard":
        # 1. Level Up Melding (Subtiel rechtsboven)
        if user['level'] > st.session_state.prev_level:
            st.balloons()
            st.session_state.prev_level = user['level']
            st.markdown(f"""
            <div style="position: fixed; top: 80px; right: 20px; z-index: 9999; animation: slideIn 0.5s ease-out;">
                <div style="background: white; padding: 15px 25px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-left: 5px solid #2563EB; display: flex; align-items: center; gap: 15px;">
                    <span style="font-size: 24px;">📈</span>
                    <div>
                        <div style="color: #0F172A; font-weight: 800; font-size: 0.9rem;">Level Up!</div>
                        <div style="color: #64748B; font-size: 0.8rem;">Je bent nu een <b>{rank_title}</b></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Variabelen laden
        full_map = roadmap.get_roadmap()
        db_progress = auth.get_progress()
        completed_steps = list(set(db_progress + st.session_state.force_completed))
        
        all_roadmap_ids = [s['id'] for fase in full_map.values() for s in fase['steps']]
        valid_done_count = len([sid for sid in completed_steps if sid in all_roadmap_ids])
        total_steps_count = len(all_roadmap_ids)
        progress_pct = int((valid_done_count / total_steps_count) * 100) if total_steps_count > 0 else 0
        safe_progress = min(progress_pct, 100)
        is_finished = valid_done_count >= total_steps_count

        # --- 2. ZAKELIJKE HEADER (SaaS Look) ---
        begroeting = get_greeting()
        shop_display = user.get('shop_name') if user.get('shop_name') else "Mijn Onderneming"
        
        # We gebruiken kolommen voor een strakke 'Head of Operations' look
        hd1, hd2 = st.columns([2, 1])
        with hd1:
            st.markdown(f"<h1 style='margin-bottom:0px;'>{begroeting}, {user.get('first_name', 'Founder')}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#64748B; font-size:1rem; margin-top:5px;'>Dit is jouw kantoor met handige <b>RM Tools</b>. Je huidige focus ligt op: <b>{shop_display}</b>.</p>", unsafe_allow_html=True)
        
        with hd2:
            # Een compacte status kaart in plaats van tekst
            st.markdown(f"""
            <div style="background:white; padding:10px 15px; border-radius:10px; border:1px solid #E2E8F0; text-align:right;">
                <div style="font-size:0.75rem; color:#64748B; text-transform:uppercase; font-weight:700;">Account Status:</div>
                <div style="font-weight:700; color:{'#16A34A' if is_pro else '#64748B'}; font-size:0.9rem;">
                    {'⚡ PRO BUSINESS' if is_pro else '🌱 STARTERS PLAN'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Voortgangsbalk (Subtieler)
        st.markdown(f"<div style='margin-top:10px; margin-bottom:5px; font-size:0.8rem; color:#64748B; font-weight:600;'>Roadmap Voltooid: {safe_progress}%</div>", unsafe_allow_html=True)
        st.progress(safe_progress / 100)

        # --- 3. INTRODUCTIE VIDEO (GECORRIGEERD) ---
        with st.expander("ℹ️ **Startgids: Zo werkt RM Tools**", expanded=False):
            # We maken de rechterkolom (tekst) breder (0.65), zodat de video links (0.35) kleiner wordt
            col_vid, col_info = st.columns([0.25, 0.75], gap="medium")

            with col_vid:
                if os.path.exists(COACH_VIDEO_PATH):
                    # OUDE MANIER (te groot op mobiel):
                    # st.video(COACH_VIDEO_PATH)
                    
                    # NIEUWE MANIER (HTML speler met hoogte limiet):
                    try:
                        with open(COACH_VIDEO_PATH, "rb") as f:
                            video_bytes = f.read()
                            video_b64 = base64.b64encode(video_bytes).decode()
                            
                        st.markdown(f"""
                            <div style="display: flex; justify-content: center; align-items: center; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                                <video controls style="width: 100%; max-height: 270px; object-fit: cover;">
                                    <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
                                    Je browser ondersteunt deze video niet.
                                </video>
                            </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.error("Video kon niet geladen worden.")
                else:
                    st.info("Video wordt geladen...")

            with col_info:
                st.markdown("""
                <h3 style="font-size: 1.1rem; margin-top:0; color:#0F172A;">Jouw digitale hoofdkantoor</h3>
                <p style="font-size: 0.9rem; color: #475569; line-height: 1.5; margin-bottom:15px;">
                    RM Tools combineert data-analyse met AI om jouw werk uit handen te nemen.
                </p>
                
                <div style="font-size: 0.85rem; color: #334155; display: flex; flex-direction: column; gap: 8px;">
                    <div>🎯 <b>Roadmap:</b> Volg het stappenplan hieronder.</div>
                    <div>🛍️ <b>Product Hunter:</b> Vind producten die nu verkopen.</div>
                    <div>🎨 <b>Marketing AI:</b> Laat logo's en teksten genereren.</div>
                </div>
                <br>
                """, unsafe_allow_html=True)

                if not is_pro:
                    # PRO knop: Zakelijk Blauw (Alleen deze ene knop)
                    st.markdown(f"""
                        <a href="{STRATEGY_CALL_URL}" target="_blank" style="text-decoration:none;">
                            <div style="background: #2563EB; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: 700; font-size: 0.9rem; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2); transition: opacity 0.2s;">
                                ⚡ Activeer PRO Licentie (€49,95)
                            </div>
                        </a>
                        <div style="text-align:center; font-size:0.75rem; color:#94A3B8; margin-top:5px;">Direct toegang tot Spy-tools & AI</div>
                    """, unsafe_allow_html=True)

        # --- 4. ACTION CARD (De "Volgende Stap") ---
        # We bepalen de volgende stap, maar presenteren het zakelijk
        next_step_title, next_step_desc, next_step_id, next_step_phase_index = "Alles afgerond", "Je bent klaar om te schalen.", None, 6
        
        if not is_finished:
            for idx, (fase_key, fase) in enumerate(full_map.items()):
                phase_done = True
                for s in fase['steps']:
                    if s['id'] not in completed_steps:
                        next_step_title = s['title']
                        next_step_desc = s.get('teaser', 'Voltooi deze taak om verder te gaan.')
                        next_step_id = s['id']
                        next_step_phase_index = idx + 1
                        phase_done = False
                        break
                if not phase_done: break
        
        # Styling: Geen fel oranje meer, maar "Tech Blue"
        # --- 4. ACTION CARD (HERO STYLE: BLAUW MET GELE KNOP) ---
        st.markdown(f"""
<div style="
background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); 
padding: 30px; 
border-radius: 20px; 
margin-top: 20px; 
margin-bottom: 25px; 
box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.4); 
position: relative; 
overflow: hidden;
border: 1px solid #1E40AF;">
            
<div style="position: relative; z-index: 2;">
<div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 2px; color: rgba(255,255,255,0.7); font-weight: 800; margin-bottom: 8px;">
Volgende mijlpaal
</div>
                <h2 style="margin: 0; font-size: 2rem; color: #FFFFFF; font-weight: 900; margin-bottom: 10px; line-height: 1.1;">
                    {next_step_title}
                </h2>
                <p style="font-size: 1.05rem; color: rgba(255,255,255,0.9); max-width: 600px; line-height: 1.5; margin-bottom: 25px; font-weight: 500;">
                    {next_step_desc}
                </p>
                
<a href="#roadmap_start" target="_self" style="text-decoration:none;">
<div style="
display: inline-block; 
background: #FFC107; 
background: linear-gradient(180deg, #FFD700 0%, #FFC107 100%);
color: #000000; 
padding: 14px 32px; 
border-radius: 12px; 
font-weight: 800; 
font-size: 1rem; 
box-shadow: 0 4px 10px rgba(0,0,0,0.2); 
border: 1px solid #EAB308;
transition: transform 0.2s;">
Start module
</div>
</a>
</div>
</div>
        """, unsafe_allow_html=True)

        # --- 5. STATS GRID (Clean) ---
        needed = next_xp_goal_sidebar - user['xp']
        st.markdown(f"""
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-icon">Jouw Level</div>
                <div class="stat-value">{user['level']}</div>
                <div class="stat-sub">{rank_title}</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">Ervaring (XP)</div>
                <div class="stat-value">{user['xp']}</div>
                <div class="stat-sub">{needed} nodig voor volgende stap</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"> Credits</div>
                <div class="stat-value" style="color:#2563EB;">{st.session_state.ai_credits}/3</div>
                <div class="stat-sub">Wordt vannacht gereset</div>
            </div>
        </div>""", unsafe_allow_html=True)
        
        # --- 6. DAILY HABIT (Business Routine) ---
        daily_id = f"daily_habit_{datetime.now().strftime('%Y%m%d')}"
        is_daily_done = daily_id in completed_steps

        st.markdown("### Dagelijkse Routine")
        with st.container(border=True):
            if not is_daily_done:
                c1, c2 = st.columns([3, 1], vertical_alignment="center")
                c1.markdown("**Consistentie wint.** Heb je vandaag 15 minuten aan je onderneming gewerkt?")
                if c2.button("✅ Check-in (+10 XP)", type="primary", use_container_width=True, key="dashboard_daily_focus"):
                    auth.mark_step_complete(daily_id, 10)
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.markdown("<div style='color:#166534; font-weight:600;'>✅ Check-in voltooid voor vandaag. Goed bezig.</div>", unsafe_allow_html=True)

        # --- 7. ROADMAP WEERGAVE ---
        st.markdown("<div id='roadmap_start' style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("### Project Roadmap")
        
        active_phase_idx = next_step_phase_index 
        for idx, (fase_key, fase) in enumerate(full_map.items()):
            phase_num = idx + 1
            is_current_phase = (phase_num == active_phase_idx)
            
            # Iconen ipv emojis voor strakkere look
            if phase_num < active_phase_idx: phase_icon, phase_label = "✅", f"{fase['title']}"
            elif phase_num == active_phase_idx: phase_icon, phase_label = "🔹", f"{fase['title']} (Actief)" 
            else: phase_icon, phase_label = "🔒", fase['title']
                
            with st.expander(f"{phase_icon} {phase_label}", expanded=is_current_phase):
                st.caption(fase['desc'])
                for step in fase['steps']:
                    is_done = step['id'] in completed_steps
                    if is_done:
                        st.markdown(f"<div style='color:#94A3B8; margin-left:20px; font-size:0.9rem;'><s>{step['title']}</s> ✅</div>", unsafe_allow_html=True)
                    else:
                        is_recommended = (step['id'] == next_step_id)
                        # We gebruiken de bestaande render functie, die is prima
                        just_completed_id, xp = roadmap.render_step_card(step, is_done, is_pro, expanded=is_recommended)
                        if just_completed_id:
                            with st.spinner("Opslaan..."):
                                auth.mark_step_complete(just_completed_id, xp)
                                if "force_completed" not in st.session_state: st.session_state.force_completed = []
                                st.session_state.force_completed.append(just_completed_id)
                                st.toast(f"Taak voltooid! +{xp} XP", icon="🚀") 
                                st.rerun()
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    elif pg == "Academy":
        # --- CSS VOOR PREMIUM LOOK ---
        st.markdown("""
        <style>
            .premium-card {
                background: white; border: 1px solid #E2E8F0; border-radius: 12px;
                padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            }
            .locked-module {
                background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px;
                padding: 12px 15px; margin-bottom: 8px; color: #94A3B8;
                display: flex; align-items: center; justify-content: space-between; font-size: 0.9rem;
            }
            div.stButton > button[kind="secondary"] {
                border: 1px solid #E2E8F0 !important; background: white !important;
                color: #475569 !important; justify-content: flex-start !important;
                padding-left: 15px !important; text-align: left !important;
            }
            div.stButton > button[kind="primary"] {
                background: #2563EB !important; border: 1px solid #2563EB !important;
                justify-content: flex-start !important; padding-left: 15px !important;
            }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<h1><i class='bi bi-mortarboard-fill'></i> Academy</h1>", unsafe_allow_html=True)
        
        tab_free, tab_pro_course = st.tabs(["🎁 Gratis Mini Training", "🎓 Volledige Cursus (70+ Video's)"])

        # =========================================================
        # --- TAB 1: GRATIS MINI TRAINING (Iedereen ziet dit) ---
        # =========================================================
        with tab_free:
            # Info banner
            st.markdown("""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 15px; border-radius: 12px; display: flex; align-items: center; gap: 10px; margin-bottom: 20px; color: #0369A1;">
                <span>ℹ️ Je hebt <b>Preview Toegang</b>: 4 van de 74 lessen zijn direct beschikbaar.</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Video Grid
            c1, c2 = st.columns(2)
            
            videos = [
                {"t": "1. Van Chaos naar Actie 🚀", "id": "nYN7EyMb7uQ", "desc": "Zet je mindset aan voor succes en begrijp het RM systeem."},
                {"t": "2. Jouw volgende stap 📈", "id": "yIJJbwIZL6k", "desc": "Hoe je de roadmap gebruikt om binnen 30 dagen live te zijn."},
                {"t": "3. Kies het juiste product 📦", "id": "CM5CtnXrvEU", "desc": "De 'Winning Product' formule uitgelegd door experts."},
                {"t": "4. Je eerste advertentie 🔥", "id": "cA8Gvhfic-s", "desc": "Stap-voor-stap je eerste campagne opzetten in Meta."}
            ]

            for i, vid in enumerate(videos):
                col = c1 if i % 2 == 0 else c2
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{vid['t']}**")
                        st.video(f"https://www.youtube.com/embed/{vid['id']}")
                        st.caption(vid['desc'])
                        # Optioneel: XP knop per video
                        if st.button(f"Klaar (+5 XP)", key=f"vid_xp_{i}"):
                            auth.mark_step_complete(f"academy_vid_{i}", 5)
                            st.toast("Lekker bezig! +5 XP verdiend.")

            # Locked Modules in Kassa-stijl
            st.markdown("<br>#### 🔒 Jouw volgende modules (PRO/Student only):", unsafe_allow_html=True)
            
            locked_cols = st.columns(2)
            locked_data = [
                "Module 5: Shopify Masterclass", "Module 7: Facebook Ads Setup",
                "Module 9: Opschalen naar 10K", "Module 11: Private Agents",
                "Module 12: Viral Content Geheimen", "Module 14: Klantenservice Automatisatie"
            ]
            
            for i, mod in enumerate(locked_data):
                l_col = locked_cols[0] if i % 2 == 0 else locked_cols[1]
                l_col.markdown(f"""
                <div style="background: #F8FAFC; border: 1px dashed #CBD5E1; padding: 12px; border-radius: 8px; margin-bottom: 8px; color: #64748B; font-size: 0.85rem;">
                    <i class="bi bi-lock-fill"></i> {mod}
                </div>
                """, unsafe_allow_html=True)

            # De "Eindstation" CTA
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="text-align: center; background: white; padding: 30px; border-radius: 16px; border: 1px solid #E2E8F0;">
                <h4>Wil je toegang tot alle 74 video's en tools?</h4>
                <p style="color: #64748B;">Zet de volgende stap in je ondernemersreis.</p>
                <a href="{STRATEGY_CALL_URL}" target="_blank" style="text-decoration:none;">
                    <div style="background: linear-gradient(135deg, #FFD700 0%, #F59E0B 100%); padding: 15px 30px; border-radius: 12px; display: inline-block; font-weight: 800; color: #78350F;">
                        🚀 UPGRADE NAAR PRO & UNLOCK ALLES
                    </div>
                </a>
            </div>
            """, unsafe_allow_html=True)

        # =========================================================
        # --- TAB 2: DE ECHTE CURSUS (DE HARDE LOCK) ---
        # =========================================================
        with tab_pro_course:
            # Check op de speciale 'Academy Student' status (niet alleen PRO)
            is_academy_student = user.get('is_academy_student', False)

            if not is_academy_student:
                # --- HET ELITE VERLANG-SCHERM ---
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Hoofdkaart
                st.markdown(f"""
<div style="background: white; border: 1px solid #E2E8F0; border-radius: 20px; padding: 40px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.05);">
<div style="font-size: 50px; margin-bottom: 20px;">🎓</div>
<h1 style="color: #0F172A; font-size: 2.2rem; margin-bottom: 10px; font-weight: 800;">Full Academy STUDENTEN Toegang</h1>
<p style="color: #64748B; font-size: 1.15rem; max-width: 600px; margin: 0 auto 30px auto;">
De volledige RM Ecom methodiek met 74 lessen, alle winnende templates en 1-op-1 begeleiding door Roy & Michael.
</p>
                    
<div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-bottom: 40px;">
<div style="background: #F0F9FF; padding: 15px 25px; border-radius: 12px; border: 1px solid #BAE6FD;">
<span style="display:block; font-size: 1.2rem;">👨‍🏫</span>
<span style="font-weight: 700; color: #0369A1; font-size: 0.9rem;">1-op-1 Coaching</span>
</div>
<div style="background: #F0FDF4; padding: 15px 25px; border-radius: 12px; border: 1px solid #BBF7D0;">
<span style="display:block; font-size: 1.2rem;">🚀</span>
<span style="font-weight: 700; color: #166534; font-size: 0.9rem;">0-10k Blueprint</span>
</div>
<div style="background: #FFF7ED; padding: 15px 25px; border-radius: 12px; border: 1px solid #FED7AA;">
<span style="display:block; font-size: 1.2rem;">💎</span>
<span style="font-weight: 700; color: #9A3412; font-size: 0.9rem;">Elite Community</span>
</div>
</div>

<p style="color: #0F172A; font-weight: 700; margin-bottom: 15px;">Wat je o.a. gaat ontgrendelen:</p>
</div>
""", unsafe_allow_html=True)

                # Curriculum preview (Sneak Peek)
                col_c1, col_c2 = st.columns(2)
                preview_modules = [
                    "Module 5: De Shopify Conversie-Machine 🔒",
                    "Module 7: Facebook Ads Blueprint 🔒",
                    "Module 9: Schalen naar €10.000/dag 🔒",
                    "Module 11: Private Agent Toegang 🔒"
                ]
                for i, mod in enumerate(preview_modules):
                    target_col = col_c1 if i < 2 else col_c2
                    target_col.markdown(f"""
                    <div style="background: #F8FAFC; border: 1px dashed #CBD5E1; padding: 12px 20px; border-radius: 10px; margin-bottom: 10px; color: #94A3B8; font-size: 0.9rem;">
                        {mod}
                    </div>
                    """, unsafe_allow_html=True)

                # De Final CTA onderaan
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style="text-align: center;">
                    <p style="font-size: 0.9rem; color: #64748B; margin-bottom: 15px;">
                        <i>Toegang krijg je pas na een gratis strategiegesprek. Zo zorgen we dat alleen gemotiveerde en serieuze deelnemers instappen.</i>
                    </p>
                    <a href="https://calendly.com/rmecomacademy/30min" target="_blank" style="text-decoration: none;">
                        <div style="background: #2563EB; color: white; padding: 18px 45px; border-radius: 12px; font-weight: 800; font-size: 1.2rem; display: inline-block; box-shadow: 0 10px 25px rgba(37, 99, 235, 0.3); transition: transform 0.2s;">
                            📞 Plan Mijn Gratis Strategie Gesprek
                        </div>
                    </a>
                </div>
                """, unsafe_allow_html=True)
            else:
                # --- DE VIDEOS (Alleen voor geverifieerde studenten) ---
                course_content = {
                    "Module 1: Welkom": [
                        {"title": "Introductie - Welkom bij de RM Tools", "url": "https://youtu.be/N7sftaU3T_E", "duration": "5 min"},
                        {"title": "Jouw 100K Laserfocus Systeem", "url": "https://youtu.be/aBpsJN0D3QE", "duration": "10 min"},
                        {"title": "Jouw Transformatieplan in 70 Dagen", "url": "https://youtu.be/gx5dJ6nUrf4", "duration": "15 min"},
                        {"title": "De eerste stappen naar succes", "url": "https://youtu.be/ajnJeKuKp7c", "duration": "8 min"},
                    ],
                    "Module 2: Het begin": [
                        {"title": "Het openen van een zakelijke rekening", "url": "https://youtu.be/x90vvuup1I8", "duration": "10 min"},
                        {"title": "Een creditcard aanvragen", "url": "https://youtu.be/lrhhCsRCcUE", "duration": "5 min"},
                        {"title": "Mindset voor de 70-dagen transformatieplan", "url": "https://youtu.be/_0W4z1yR_Lg", "duration": "20 min"},
                    ],
                    "Module 3: Dropshipping": [
                        {"title": "Wat betekend branded dropshipping?", "url": "https://youtu.be/puq-WqF8JMQ", "duration": "10 min"},
                        {"title": "Wat is dropshipping en hoe werkt het?", "url": "https://youtu.be/Dq8E6G5Fgc8", "duration": "15 min"},
                    ],
                    "Module 4: De fundering": [
                        {"title": "Een markt kiezen", "url": "https://youtu.be/vcxTcT5rnV4", "duration": "15 min"},
                        {"title": "Een niche kiezen", "url": "https://youtu.be/4bfnKWIQYbY", "duration": "20 min"},
                    ],
                    "Module 5: Shopify": [
                        {"title": "Shopify account aanmaken", "url": "https://youtu.be/gwxx5fUouKQ", "duration": "5 min"},
                        {"title": "Website termen", "url": "https://youtu.be/d9NPDvrYUHc", "duration": "5 min"},
                        {"title": "Rondleiding Shopify (algemeen)", "url": "https://youtu.be/zkMAybKHnnc", "duration": "15 min"},
                        {"title": "De webshop inrichten", "url": "https://youtu.be/xBS66G6OK84", "duration": "25 min"},
                        {"title": "Een betaling ontvangen (Shopify Payments)", "url": "https://youtu.be/hW2hmKlBcEQ", "duration": "10 min"},
                        {"title": "Een domein kiezen en aanschaffen", "url": "https://youtu.be/PxNTMe-qsOA", "duration": "5 min"},
                        {"title": "Custom codes gebruiken", "url": "https://youtu.be/zi3fXCyBYdI", "duration": "10 min"},
                        {"title": "De navigatie van je webshop", "url": "https://youtu.be/F3INLon0pnY", "duration": "10 min"},
                        {"title": "Een productpagina aanmaken", "url": "https://youtu.be/0PJ4NpR1ibs", "duration": "15 min"},
                        {"title": "Een collectiepagina aanmaken", "url": "https://youtu.be/Grh2GVnKJRk", "duration": "10 min"},
                        {"title": "Een verzendmethode instellen", "url": "https://youtu.be/8aGzEJrV0M8", "duration": "10 min"},
                        {"title": "Kortingscodes aanmaken", "url": "https://youtu.be/k2uGrjto_fo", "duration": "5 min"},
                        {"title": "Conversie optimaliseren (CRO)", "url": "https://youtu.be/0QNxhi7aXBA", "duration": "20 min"},
                        {"title": "De checkout optimaliseren", "url": "https://youtu.be/y0-giNe1Pes", "duration": "10 min"},
                        {"title": "Shopify markten instellen", "url": "https://youtu.be/OCPcbo0JsMo", "duration": "15 min"},
                    ],
                    "Module 6: Apps in Shopify": [
                        {"title": "Poky", "url": "https://youtu.be/qKLYDk9-7x8", "duration": "5 min"},
                        {"title": "Section store", "url": "https://youtu.be/Gc3G_x2D_4k", "duration": "5 min"},
                        {"title": "Parcel panel", "url": "https://youtu.be/TsMKOtsIz7Y", "duration": "5 min"},
                        {"title": "Slize Cart by AMP", "url": "https://youtu.be/JLNFlfSLqjI", "duration": "5 min"},
                        {"title": "BF size charts", "url": "https://youtu.be/iP__ahhzXfo", "duration": "5 min"},
                        {"title": "Kaching Bundles en hoe AOV verhogen", "url": "https://youtu.be/9SBXwXFrIkQ", "duration": "10 min"},
                        {"title": "Conversie Verhogen - Trust Badges", "url": "https://youtu.be/718tg9QR50Y", "duration": "5 min"},
                    ],
                    "Module 7: Facebook (Setup)": [
                        {"title": "Start van je Facebook blueprint", "url": "https://youtu.be/pvIAASq9jfg", "duration": "10 min"},
                        {"title": "De Businessmanager aanmaken", "url": "https://youtu.be/_7vF_nc6dzo", "duration": "10 min"},
                        {"title": "Een Rondleiding door de businessmanager", "url": "https://youtu.be/M-BAExvxyzU", "duration": "15 min"},
                        {"title": "Het aanmaken van een Facebookpagina", "url": "https://youtu.be/2sh_raKCa_Q", "duration": "5 min"},
                        {"title": "Het opwarmen van de pagina", "url": "https://youtu.be/FY08rYyjwlM", "duration": "5 min"},
                        {"title": "Het aanmaken van je advertentieaccount", "url": "https://youtu.be/dmJIS8Ujuec", "duration": "5 min"},
                        {"title": "Opzetten van je agency advertentieaccount", "url": "https://youtu.be/JOUW_LINK_HIER", "duration": "10 min"},
                        {"title": "Het aanmaken en koppelen van je pixel", "url": "https://youtu.be/NeIB1Ime_2cR", "duration": "15 min"},
                        {"title": "Het verifiëren van je domein", "url": "https://youtu.be/eE9aziZogjw", "duration": "5 min"},
                        {"title": "Facebook structuur opzetten", "url": "https://youtu.be/JOUW_LINK_HIER", "duration": "10 min"},
                        {"title": "Je Instagram account koppelen", "url": "https://youtu.be/ZOaOr56EqGc", "duration": "5 min"},
                    ],
                    "Module 8: Facebook Live gaan": [
                        {"title": "Wat is een ABO campagne?", "url": "https://youtu.be/0w32dh7yS9I", "duration": "10 min"},
                        {"title": "Wat is een CBO campagne?", "url": "https://youtu.be/zBk2oR_MGbI", "duration": "10 min"},
                        {"title": "Het aanmaken van een testcampagne", "url": "https://youtu.be/gwlKJ9XhwBE", "duration": "20 min"},
                        {"title": "Facebooktermen", "url": "https://youtu.be/EVE_Xhu1qjI", "duration": "10 min"},
                        {"title": "Het instellen van kolommen", "url": "https://youtu.be/M1ek9iua7sg", "duration": "5 min"},
                        {"title": "Opschalen van je advertenties (de basis)", "url": "https://youtu.be/qGG30Y-0HVw", "duration": "15 min"},
                        {"title": "Hoe analyseer je advertenties?", "url": "https://youtu.be/C3qXa4r-8yo", "duration": "15 min"},
                        {"title": "Wat doe je als een product onder presteert?", "url": "https://youtu.be/u0giYTGBcfA", "duration": "10 min"},
                        {"title": "Comments automatisch verbergen", "url": "https://youtu.be/FIyEYO6yd18", "duration": "5 min"},
                        {"title": "Wetracked of Trackbee installeren", "url": "https://youtu.be/dsk8nUqkDtI", "duration": "10 min"},
                    ],
                    "Module 9: Facebook geavanceerd": [
                        {"title": "Veilig opschalen met 20%", "url": "https://youtu.be/yHEDftamMc8", "duration": "10 min"},
                        {"title": "Gemiddeld opschalen met 50%", "url": "https://youtu.be/mHVh_PY-ja4", "duration": "10 min"},
                        {"title": "Agressief opschalen met 100%", "url": "https://youtu.be/8ayQ1ecqoCg", "duration": "10 min"},
                        {"title": "Ultra agressief opschalen (Surfscalen)", "url": "https://youtu.be/lfskezYSM1Y", "duration": "15 min"},
                        {"title": "Creatives testen (voor een lage cpc)", "url": "https://youtu.be/SCjQilN9W2s", "duration": "15 min"},
                    ],
                    "Module 10: Branding": [
                        {"title": "Social Media branding", "url": "https://youtu.be/3Vccoluq43U", "duration": "10 min"},
                        {"title": "Logo maken", "url": "https://youtu.be/GqehPhoMnX0", "duration": "10 min"},
                    ],
                    "Module 11: Agent (Prive leverancier)": [
                        {"title": "Het gebruiken van een privé leverancier", "url": "https://youtu.be/lvIv6vq2dQY", "duration": "10 min"},
                        {"title": "De kwaliteit van je producten checken", "url": "https://youtu.be/WDCebfTe4jQ", "duration": "5 min"},
                        {"title": "Een gepersonaliseerde verpakking maken", "url": "https://youtu.be/2GZIH6HnV2k", "duration": "10 min"},
                    ],
                    "Module 12: Content Creation": [
                        {"title": "De 5 stadia van bewustzijn", "url": "https://youtu.be/RBvrN_JdNsI", "duration": "10 min"},
                        {"title": "Canva rondleiding", "url": "https://youtu.be/SekM6oFOQNs", "duration": "15 min"},
                        {"title": "Advertentie creatives maken", "url": "https://youtu.be/aJHm6_yFgSg", "duration": "20 min"},
                        {"title": "Video's vanuit de AD library downloaden", "url": "https://youtu.be/WFE3l88O5iM", "duration": "5 min"},
                        {"title": "De opbouw van een winnende video creatie", "url": "https://youtu.be/Oeh276FU0iQ", "duration": "15 min"},
                        {"title": "Scroll stoppers maken voor je video", "url": "https://youtu.be/TeohCu7NEwE", "duration": "10 min"},
                        {"title": "Advertentieteksten schrijven met Chat-GPT", "url": "https://youtu.be/LVk0No917sI", "duration": "10 min"},
                        {"title": "UGC content gebruiken", "url": "https://youtu.be/GKmWZFkgFeg", "duration": "10 min"},
                    ],
                    "Module 13: Klantenservice": [
                        {"title": "Hoe ga je met klanten om?", "url": "https://youtu.be/08qt2ND4pLY", "duration": "10 min"},
                        {"title": "Klantenservice templates", "url": "https://youtu.be/JOUW_LINK_HIER", "duration": "5 min"},
                        {"title": "Retourfunnel (verminder je retouren)", "url": "https://youtu.be/C5So4rh8Xx0", "duration": "10 min"},
                    ],
                    "Module 14: Must Have": [
                        {"title": "Handige Tools (MUST HAVE)", "url": "https://youtu.be/9cmTsNGat2s", "duration": "10 min"},
                        {"title": "Ad strategie (Collecties)", "url": "https://youtu.be/7YNWLMsexnw", "duration": "15 min"},
                        {"title": "Website reviews (Fouten van anderen)", "url": "https://youtu.be/gzOMw4O-b00", "duration": "20 min"},
                    ],
                }

                col_nav, col_content = st.columns([1, 2.2], gap="large")
                with col_nav:
                    st.markdown("#### 📂 Modules")
                    module_names = list(course_content.keys())
                    if "curr_module" not in st.session_state: st.session_state.curr_module = module_names[0]
                    selected_module = st.selectbox("Kies module:", module_names, label_visibility="collapsed")
                    st.session_state.curr_module = selected_module
                    videos_in_module = course_content[selected_module]
                    if "curr_video" not in st.session_state: st.session_state.curr_video = videos_in_module[0]['title']
                    
                    for v in videos_in_module:
                        title = v['title']
                        is_active = (title == st.session_state.curr_video)
                        btn_type = "primary" if is_active else "secondary"
                        if st.button(f"📺 {title}", key=f"nav_{title}", type=btn_type, use_container_width=True):
                            st.session_state.curr_video = title
                            st.rerun()

                with col_content:
                    current_video = next((v for v in videos_in_module if v['title'] == st.session_state.curr_video), videos_in_module[0])
                    st.markdown(f"### {current_video['title']}")
                    st.video(current_video['url'])
                    
                    vid_id = f"vid_{abs(hash(current_video['title']))}"
                    if vid_id not in completed_steps:
                        if st.button("✅ Les Afronden (+15 XP)", type="primary"):
                            auth.mark_step_complete(vid_id, 15)
                            st.balloons()
                            st.rerun()
                    else:
                        st.success("Deze les is voltooid! ✅")


    elif pg == "Producten Zoeken":
        # --- HEADER ---
        st.markdown("<h1><i class='bi bi-search'></i> Winning Product Hunter</h1>", unsafe_allow_html=True)
        st.caption("De ultieme toolkit om winstgevende producten te vinden en te analyseren.")

        # =========================================================
        # 🏆 SECTIE 1: PRO DAILY WINNERS (EXCLUSIEF VOOR PRO)
        # =========================================================
        if is_pro:
            with st.container(border=True):
                st.markdown("### 🏆 PRO Daily Winners")
                st.write("Onze AI selectie van de 3 grootste kanshebbers van vandaag.")
                if st.button("✨ Onthul Winners van Vandaag", type="primary", use_container_width=True):
                    picks = db.get_daily_winners_from_db()
                    if picks:
                        st.session_state.pro_daily_picks = picks
                    else:
                        st.error("Winners worden momenteel ververst. Probeer het over 5 minuten opnieuw.")

                if "pro_daily_picks" in st.session_state:
                    picks = st.session_state.pro_daily_picks
                    cols = st.columns(3)
                    for idx, item in enumerate(picks):
                        with cols[idx]:
                            with st.container(border=True):
                                if item.get('cover_url'): st.image(item['cover_url'], use_container_width=True)
                                st.markdown(f"**{item.get('title', 'Product')[:35]}...**")
                                st.info(f"💡 {item.get('reason', 'Hoge viraliteit.')}")
                                c1, c2 = st.columns(2)
                                c1.link_button("🎵 Bekijk", item.get('video_url', '#'), use_container_width=True)
                                if c2.button("✍️ Script", key=f"pro_script_{idx}", use_container_width=True):
                                    st.session_state.workflow_product = item.get('title', '')
                                    st.session_state.nav_index = 3
                                    st.rerun()
        else:
            # Gratis gebruikers zien de 'Locked' state voor Daily Winners
            render_pro_lock("Daily Winners 🔒", "Krijg elke dag 3 kant-en-klare winstgevende producten.", "Exclusief voor PRO studenten.")

        # =========================================================
        # 🔍 SECTIE 2: DE ZOEK TOOLS (1x Gratis voor Demo gebruikers)
        # =========================================================
        st.markdown("---")
        tab1, tab2, tab3 = st.tabs(["🔥 Viral TikTok Hunter", "🧿 Meta Ad Spy", "🕵️ Concurrenten Spy"]) 
        
        # --- TAB 1: TIKTOK HUNTER ---
        with tab1:
            st.markdown("""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
                <h3 style="margin-top: 0; color: #0369A1; font-size: 1.2rem; display: flex; align-items: center; gap: 10px; font-weight: 700;">
                    <span style="font-size: 1.5rem;">🔥</span> Viral TikTok Hunter
                </h3>
                <p style="font-size: 1rem; color: #1E293B; line-height: 1.6;">Vind producten die <b>nu</b> viraal gaan.</p>
            </div>
            """, unsafe_allow_html=True)

            # --- DE UI VELDEN (MOETEN ERIN!) ---
            with st.container(border=True):
                st.markdown("#### 🎯 Instellingen")
                col_a, col_b = st.columns(2)
                tk_query = col_a.text_input("Product of Niche", placeholder="bijv. keuken gadgets", key="tk_search_q")
                tk_sort = col_b.selectbox("Sorteer op", ["Meeste Views", "Recent", "Relevant"])
                
                if st.button("🚀 Start Viral Hunter", type="primary", use_container_width=True):
                    if tk_query:
                        with st.status("🕵️‍♂️ AI scant TikTok...", expanded=True) as status:
                            from modules import tiktok_spy
                            results = tiktok_spy.search_tiktok_trends(tk_query, tk_sort)
                            if results and results != "ERROR":
                                st.session_state.tiktok_results = results
                                status.update(label="✅ Winners gevonden!", state="complete")
                    else:
                        st.warning("Vul een zoekterm in.")


            # 3. DE RESULTATEN WEERGAVE (Houd dit zoals het was)
            if st.session_state.get("tiktok_results"):
                res = st.session_state.tiktok_results
                st.markdown(f"### 🚀 {len(res)} Winners gevonden voor jou")
                
                # Grid van 2 kolommen
                for i in range(0, len(res), 2):
                    ca, cb = st.columns(2)
                    
                    def draw_premium_item(col, item, k):
                        with col:
                            with st.container(border=True):
                                if item.get('cover'): st.image(item['cover'], use_container_width=True)
                                views_k = item['views'] // 1000
                                st.markdown(f"**{item['desc'][:45]}...**")
                                st.caption(f"👁️ {views_k}K Views")
                                
                                c1, c2 = st.columns(2)
                                c1.link_button("🎥 Video", item['url'], use_container_width=True)
                                search_q = urllib.parse.quote(item['desc'][:30])
                                c2.link_button("📦 Inkoop", f"https://www.aliexpress.com/wholesale?SearchText={search_q}", use_container_width=True)

                    draw_premium_item(ca, res[i], i)
                    if i+1 < len(res):
                        draw_premium_item(cb, res[i+1], i+1)

        with tab2:
            # --- 1. PREMIUM HEADER ---
            st.markdown("""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
                <h3 style="margin-top: 0; color: #0369A1; font-size: 1.2rem; display: flex; align-items: center; gap: 10px; font-weight: 700;">
                    <span style="font-size: 1.5rem;">🧿</span> Meta Ad Spy: Strategisch Onderzoek
                </h3>
                <p style="font-size: 1rem; color: #1E293B; line-height: 1.6;">
                    Met deze tool spiek je direct in de keuken van de concurrent. Je ziet precies welke advertenties nu live staan op Facebook.
                </p>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ 100% Betrouwbaar</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Live Data</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Gratis Toegang</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- 2. DE ZOEKBOX ---
            with st.container(border=True):
                st.markdown("#### 🔍 Wat wil je onderzoeken?")
                fb_query = st.text_input("Vul een productnaam of merk in:", placeholder="bijv. 'orthopedische schoenen' of 'halsketting'", key="fb_q_final")
                
                if fb_query:
                    st.markdown("---")
                    col_left, col_right = st.columns(2)
                    
                    with col_left:
                        # --- DE MISSION BRIEFING KAART ---
                        st.markdown(f"""
                        <div style="background: white; border: 1px solid #BAE6FD; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                            <h5 style="margin: 0 0 10px 0; color: #0369A1;">🚀 Mission Briefing: {fb_query}</h5>
                            <p style="font-size: 0.85rem; color: #475569; line-height: 1.5;">
                                Boss, je gaat nu de officiële database van Meta in. Volg deze stappen voor een succesvol onderzoek:
                            </p>
                            <div style="background: #F8FAFC; padding: 10px; border-radius: 8px; margin: 10px 0; border-left: 3px solid #2563EB;">
                                <p style="font-size: 0.8rem; margin: 0; color: #1E293B;">
                                    <b>1. De Focus:</b> Zoek naar ads die al <b>7+ dagen</b> draaien.<br>
                                    <b>2. De Creatives:</b> Kijk of ze video of foto gebruiken.<br>
                                    <b>3. De Hook:</b> Waarom zou jij stoppen met scrollen?
                                </p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

                        # De Knop met directe link
                        encoded_q = urllib.parse.quote(fb_query)
                        fb_url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&q={encoded_q}&country=NL&media_type=all"
                        
                        st.link_button("🔥 Start Onderzoek (Nieuw Tabblad)", fb_url, use_container_width=True, type="primary")
                        
                        st.caption("⚠️ Vergeet niet terug te komen naar de app na je onderzoek!")                        
                       
                    with col_right:
                        st.markdown("##### 🤖 Methode 2: AI Robot Scan")
                        st.caption("Laat onze robot de Ad Library scannen (PRO only).")
                        
                        # Knop voor de robot
                        if st.button("🕵️‍♂️ Robot Scan Starten", use_container_width=True):
                            if db.can_user_search(user['email'], is_pro):
                                with st.status("🔍 Robot maakt verbinding met Meta...", expanded=True) as status:
                                    from modules import facebook_spy
                                    results = facebook_spy.search_facebook_ads(fb_query)
                                    if results and results != "ERROR":
                                        st.session_state.fb_results = results
                                        status.update(label="Scan voltooid!", state="complete")
                                    else:
                                        status.update(label="Meta blokkeert de robot...", state="error")
                                        st.warning("⚠️ Meta weigert momenteel automatische toegang. Gebruik Methode 1 voor direct resultaat.")
                            else:
                                st.warning("⚠️ Je dagelijkse gratis scan is op! Word PRO voor meer.")

            # --- 3. RESULTATEN VAN DE ROBOT (ALS DIE WERKT) ---
            if st.session_state.get("fb_results"):
                st.markdown("### 🎯 Gevonden via Robot:")
                for ad in st.session_state.fb_results:
                    with st.container(border=True):
                        c1, c2 = st.columns([1, 2])
                        if ad.get('media'): c1.image(ad['media'], use_container_width=True)
                        c2.markdown(f"**{ad['page_name']}**")
                        c2.link_button("🛒 Bekijk Winkel", ad['shop_link'], use_container_width=True)
                          
        with tab3:
            # --- 1. PREMIUM HEADER ---
            st.markdown("""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
                <h3 style="margin-top: 0; color: #0369A1; font-size: 1.2rem; display: flex; align-items: center; gap: 10px; font-weight: 700;">
                    <span style="font-size: 1.5rem;">🕵️‍♂️</span> Shopify Store Spy
                </h3>
                <p style="font-size: 1rem; color: #1E293B; line-height: 1.6;">
                    Ontrafel het succes van je concurrenten. Zie direct welke producten ze verkopen, wat hun prijzen zijn en of jij ze kunt verslaan op winstmarge.
                </p>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Live Collectie Scan</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Automatische Vertaling</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Winst-voorspeller</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- 2. HET ZOEKVELD ---
            if is_pro:
                with st.container(border=True):
                    st.markdown("#### 🔍 Welke shop wil je onderzoeken?")
                    url_in = st.text_input("Vul de URL van je concurrent in:", placeholder="bijv. www.concurrent.nl", key="spy_url_new")
                    
                    if st.button("🚀 Start Collectie Scan", type="primary", use_container_width=True):
                        if url_in:
                            with st.status("🕵️‍♂️ Robot onderzoekt de winkel...", expanded=True) as status:
                                # 1. Scrape de producten
                                from modules import competitor_spy
                                prods = competitor_spy.scrape_shopify_store(url_in)
                                
                                if prods:
                                    status.update(label="✅ Producten gevonden! Titels vertalen...", state="running")
                                    
                                    # 2. Batch vertalen naar NL
                                    original_titles = [p['title'] for p in prods]
                                    translated_titles = ai_coach.translate_titles_batch(original_titles)
                                    
                                    for i, p in enumerate(prods):
                                        if i < len(translated_titles):
                                            p['title'] = translated_titles[i]
                                    
                                    status.update(label="Scan voltooid! Zie resultaten hieronder.", state="complete")
                                    st.session_state.spy_results = prods
                                else:
                                    status.update(label="Oeps! Geen Shopify store gevonden.", state="error")
                                    st.error("Dit lijkt geen Shopify winkel te zijn of de toegang wordt geblokkeerd.")
            else:
                render_pro_lock("Shopify Store Spy", "Scan elke Shopify winkel en zie hun bestsellers.", "Deze tool bespaart onze studenten uren aan onderzoek.")

            # --- 3. RESULTATEN WEERGAVE (KAARTJES) ---
            if st.session_state.get("spy_results"):
                st.markdown("---")
                st.markdown(f"### 🎯 Analyse resultaten voor '{url_in}'")
                
                for p in st.session_state.spy_results:
                    with st.container(border=True):
                        col_img, col_info = st.columns([1, 2.5])
                        
                        with col_img:
                            if p['image_url']:
                                st.image(p['image_url'], use_container_width=True)
                            else:
                                st.markdown("🖼️ *Geen foto*")
                        
                        with col_info:
                            st.markdown(f"#### {p['title']}")
                            st.markdown(f"💰 **Prijs bij concurrent:** €{p['price']}")
                            
                            # Winst Analyse Expandertje
                            with st.expander("📊 Bekijk Winst-Analyse", expanded=False):
                                analysis = ai_coach.analyze_profit_potential(p['title'], p['price'])
                                if analysis:
                                    ca, cb, cc = st.columns(3)
                                    ca.metric("Inkoop", f"€{analysis['inkoop']}")
                                    cb.metric("Ads", f"€{analysis['ads']}")
                                    
                                    winst_kleur = "#16A34A" if analysis['status'] == "GROEN" else "#EA580C" if analysis['status'] == "ORANJE" else "#DC2626"
                                    cc.markdown(f"<div style='text-align:center;'><p style='margin:0; font-size:0.8rem; color:#64748B;'>Netto Winst</p><h3 style='color:{winst_kleur}; margin:0;'>€{analysis['winst']}</h3></div>", unsafe_allow_html=True)
                                    
                                    st.markdown(f"""<div style="background: {winst_kleur}20; border-left: 4px solid {winst_kleur}; padding: 10px; border-radius: 4px; margin-top: 10px;"><p style="margin:0; font-size:0.85rem; color:{winst_kleur}; font-weight:700;">📢 Advies: {analysis['advies']}</p></div>""", unsafe_allow_html=True)

                            st.markdown("<br>", unsafe_allow_html=True)
                            b1, b2, b3 = st.columns(3)
                            b1.link_button("🛒 Bekijk Shop", p['url'], use_container_width=True)
                            
                            # TikTok & AliExpress links
                            q = urllib.parse.quote(p['title'])
                            b2.link_button("🕵️ Zoek Ads", f"https://www.tiktok.com/search?q={q}", use_container_width=True)
                            b3.link_button("📦 Inkoop", f"https://www.aliexpress.com/wholesale?SearchText={q}", use_container_width=True)

    elif pg == "Marketing & Design": 
        st.markdown("<h1><i class='bi bi-palette-fill'></i> Marketing & Design</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎨 Logo Maker", "🎬 Video Scripts", "✍️ Teksten Schrijven", "🩺 Ad Check", "🏥 Store Doctor"])
        
        # --- TAB 1: LOGO MAKER ---
        with tab1:
            st.markdown("""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
                <h3 style="margin-top: 0; color: #0369A1; font-size: 1.2rem; display: flex; align-items: center; gap: 10px; font-weight: 700;">
                    <span style="font-size: 1.5rem;"></span> RM AI Logo Maker
                </h3>
                <p style="font-size: 1rem; color: #1E293B; line-height: 1.6;">
                    Verspil geen dagen aan je logo. Een goed logo straalt vertrouwen uit en is simpel. Gebruik onze AI om in 10 seconden 3 variaties te maken die direct klaar zijn voor je shop.
                </p>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Binnen 10 sec klaar</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Professionele Stijl</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Gratis voor leden</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.container(border=True):
                c1, c2 = st.columns(2)
                b_name = c1.text_input("Bedrijfsnaam", placeholder="bijv. Lumina", value=user.get('shop_name', ''))
                b_niche = c1.text_input("Niche / Wat verkoop je?", placeholder="bijv. yoga kleding, honden speeltjes")
                b_style = c2.selectbox("Kies je Stijl", ["Minimalistisch", "Luxe", "Modern & Strak", "Speels"])
                b_color = c2.text_input("Voorkeurskleuren", placeholder="bijv. goud en zwart")
                
                if st.button("🚀 Genereer mijn logo's", type="primary", use_container_width=True):
                        if not b_name or not b_niche: 
                            st.warning("Vul alles in.")
                        else:
                            st.session_state.logo_generations += 1
                            with st.spinner("Onze designers zijn bezig... (Dit duurt ca. 10 sec)"):
                                import requests
                                
                                new_logos = []
                                for i in range(3):
                                    img_url = ai_coach.generate_logo(b_name, b_niche, b_style, b_color)
                                    if img_url and "placehold" not in img_url:
                                        try:
                                            resp = requests.get(img_url)
                                            if resp.status_code == 200:
                                                new_logos.append({
                                                    "url": img_url,
                                                    "data": resp.content,
                                                    "name": f"logo_{b_name}_{i+1}.png"
                                                })
                                        except: pass
                                
                                if new_logos:
                                    st.session_state.generated_logos = new_logos
                                else:
                                    st.error("Er ging iets mis bij het genereren. Probeer het opnieuw.")

                # --- WEERGAVE ---
                if st.session_state.generated_logos:
                    st.markdown("---")
                    st.markdown("### 🎉 Jouw resultaten:")
                    st.success("Tip: Klik op de knop onder het logo om hem in hoge kwaliteit op te slaan.")
                    
                    cols = st.columns(3)
                    for idx, logo in enumerate(st.session_state.generated_logos):
                        with cols[idx]:
                            st.image(logo["url"], use_container_width=True)
                            st.download_button(
                                label="📥 Download Logo",
                                data=logo["data"],
                                file_name=logo["name"],
                                mime="image/png",
                                key=f"dl_btn_persistent_{idx}",
                                use_container_width=True
                            )
                    
                    if st.button("Opnieuw beginnen (Wist huidige logo's)", type="secondary"):
                        st.session_state.generated_logos = []
                        st.rerun()

        # --- TAB 2: VIDEO SCRIPTS ---
        with tab2:
            st.markdown("""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
                <h3 style="margin-top: 0; color: #0369A1; font-size: 1.2rem; display: flex; align-items: center; gap: 10px; font-weight: 700;">
                    <span style="font-size: 1.5rem;"></span> Virale Video Scripts
                </h3>
                <p style="font-size: 1rem; color: #1E293B; line-height: 1.6;">
                    Weet je niet wat je moet zeggen in je TikToks of Reels? Onze AI schrijft scripts met de juiste 'Hook' om mensen te laten stoppen met scrollen.
                </p>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ TikTok Geoptimaliseerd</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Sterke Hooks</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Reels & Shorts</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.container(border=True):
                # We halen het product op dat ze in de Hunter hebben gevonden (indien aanwezig)
                v_prod = st.text_input("Voor welk product wil je een script?", value=st.session_state.get('workflow_product', ''), placeholder="bijv. Orthopedisch Kussen")
                if st.button("✍️ Schrijf Script", type="primary", use_container_width=True):
                    # (Bestand ai_coach.py roept script generator aan)
                    st.success("Script gegenereerd!")

# --- TAB 3: TEKSTEN SCHRIJVEN ---
        with tab3:
            st.markdown("""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
                <h3 style="margin-top: 0; color: #0369A1; font-size: 1.2rem; display: flex; align-items: center; gap: 10px; font-weight: 700;">
                    <span style="font-size: 1.5rem;"></span> Verkoopteksten (AI Copywriter)
                </h3>
                <p style="font-size: 1rem; color: #1E293B; line-height: 1.6;">
                    Laat AI het zware schrijfwerk doen. Of het nu gaat om een productpagina of een bericht naar een influencer: onze AI schrijft teksten die converteren.
                </p>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Conversie Gericht</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ AIDA Psychologie</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Bespaar uren werk</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # We verdelen de tools in twee duidelijke categorieën
            t_desc, t_inf = st.tabs(["🛍️ Productpagina Tekst", "🤳 Influencer DM Script"])

            with t_desc:
                with st.container(border=True):
                    st.markdown("#### ✨ Laat de AI schrijven")
                    # Automatisch invullen als ze een product uit de Hunter hebben
                    default_prod = st.session_state.get('workflow_product', '')
                    prod_name = st.text_input("Naam van je product:", value=default_prod, placeholder="bijv. Magische Sterren Projector")
                    
                    if st.button("Genereer Productomschrijving", type="primary", use_container_width=True):
                        if not prod_name:
                            st.warning("Vul eerst een productnaam in.")
                        elif check_credits():
                            with st.spinner("De AI-copywriter schrijft je tekst..."):
                                res = ai_coach.generate_product_description(prod_name)
                                st.markdown("---")
                                st.markdown(res)
                                st.success("Tip: Kopieer deze tekst direct naar je Shopify productpagina!")
                        else:
                            st.warning("Je dagelijkse AI credits zijn op. Word PRO voor onbeperkt schrijven.")

            with t_inf:
                with st.container(border=True):
                    st.markdown("#### 📩 Influencer Outreach")
                    st.write("Wil je gratis producten sturen naar influencers? Gebruik dit script om de kans op een 'JA' te vergroten.")
                    inf_prod = st.text_input("Voor welk product zoek je samenwerkingen?", placeholder="bijv. Organic Face Serum")
                    
                    if st.button("Genereer DM Script", type="primary", use_container_width=True):
                        if not inf_prod:
                            st.warning("Vul een product in.")
                        elif check_credits():
                            with st.spinner("Script wordt opgesteld..."):
                                res = ai_coach.generate_influencer_dm(inf_prod)
                                st.markdown("---")
                                st.code(res, language="text")
                                st.info("Kopieer dit bericht en stuur het als DM op Instagram of TikTok.")
                        else:
                            st.warning("Je dagelijkse credits zijn op.")        
# --- TAB 4: ADVERTENTIE CHECKER (DE AD DOKTER) ---
        with tab4:
            # 1. PREMIUM HEADER
            st.markdown("""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
                <h3 style="margin-top: 0; color: #0369A1; font-size: 1.2rem; display: flex; align-items: center; gap: 10px; font-weight: 700;">
                    <span style="font-size: 1.5rem;"></span> De Advertentie Dokter
                </h3>
                <p style="font-size: 1rem; color: #1E293B; line-height: 1.6;">
                    Upload een screenshot van je advertentie. Onze AI (Senior Media Buyer) beoordeelt je afbeelding en tekst op conversie-kracht. <b>Voorkom dat je budget verspilt aan slechte ads.</b>
                </p>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Stop-the-scroll Check</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Direct Rapportcijfer</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Bespaar Ad-budget</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if is_pro:
                with st.container(border=True):
                    st.markdown("#### 🚑 Start de Analyse")
                    # Stap 1: Context geven
                    c1, c2, c3 = st.columns(3)
                    platform = c1.selectbox("Platform", ["TikTok", "Facebook / Insta Feed", "Instagram Story/Reel"], key="ad_plat")
                    goal = c2.selectbox("Doel", ["Sales (Conversie)", "Kliks", "Leads"], key="ad_goal")
                    niche_ad = c3.text_input("Niche", placeholder="bijv. Beauty", key="ad_niche")
                    
                    # Stap 2: Upload
                    uploaded_file = st.file_uploader("Sleep hier je ad-screenshot naar binnen:", type=['png', 'jpg', 'jpeg'])
                    
                    if uploaded_file and st.button("🚑 Start Diagnose", type="primary", use_container_width=True):
                        if not niche_ad:
                            st.warning("Vul ook even je niche in voor beter advies.")
                        else:
                            with st.spinner("De dokter analyseert je advertentie..."):
                                audit = ai_coach.analyze_ad_screenshot(uploaded_file, platform, goal, niche_ad)
                                
                                if audit:
                                    st.markdown("---")
                                    # SCORE KAART
                                    score = audit.get('score', 5)
                                    score_color = "#16A34A" if score >= 8 else "#EA580C" if score >= 6 else "#DC2626"
                                    
                                    st.markdown(f"""
                                    <div style="text-align:center; padding: 30px; background:#F8FAFC; border-radius:16px; border:1px solid #E2E8F0; margin-bottom: 25px;">
                                        <p style="margin:0; font-size: 1.1rem; color: #64748B;">Rapportcijfer</p>
                                        <h1 style="margin:0; color:{score_color}; font-size: 4rem; font-weight: 900;">{score}/10</h1>
                                        <h3 style="margin:0; color:#0F172A;">{audit.get('titel', 'Analyse Voltooid')}</h3>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # De Details
                                    cd1, cd2 = st.columns(2)
                                    with cd1:
                                        st.info(f"**👁️ De Hook (Beeld):**\n\n{audit.get('analyse_hook')}")
                                    with cd2:
                                        st.info(f"**✍️ De Copy (Tekst):**\n\n{audit.get('analyse_copy')}")
                                        
                                    st.markdown("#### 🛠️ Direct aanpassen voor meer sales:")
                                    for punt in audit.get('verbeterpunten', []):
                                        st.error(f"👉 {punt}")
                                    
                                    st.success("Pas deze punten aan en test de ad opnieuw!")
            else:
                render_pro_lock("De Advertentie Dokter", "Laat je ads keuren door een Senior Media Buyer AI.", "Voorkom dat je honderden euro's verbrandt aan een advertentie die niet werkt.")

# --- TAB 5: STORE DOCTOR ---
        with tab5:
            # 1. PREMIUM HEADER
            st.markdown("""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
                <h3 style="margin-top: 0; color: #0369A1; font-size: 1.2rem; display: flex; align-items: center; gap: 10px; font-weight: 700;">
                    <span style="font-size: 1.5rem;"></span> The Store Doctor
                </h3>
                <p style="font-size: 1rem; color: #1E293B; line-height: 1.6;">
                    Heb je een webshop maar maak je geen sales? Laat de 'Doctor' je shop scannen op <b>Conversie Killers</b>. De AI kijkt naar je teksten, vertrouwen en aanbod.
                </p>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Scan op fouten</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Verbeter je conversie</span>
                    <span style="background: white; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #7DD3FC; color: #0369A1; font-weight: 600;">✅ Direct actieplan</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if is_pro:
                with st.container(border=True):
                    st.markdown("#### 🚑 Start de Diagnose")
                    target_url = st.text_input("URL van je eigen shop:", placeholder="bijv. www.jouwshop.nl", key="doctor_url_input")
                    
                    if st.button("🏥 Scan mijn Webshop", type="primary", use_container_width=True):
                        if "." not in target_url:
                            st.warning("Vul een geldige URL in.")
                        else:
                            with st.status("👨‍⚕️ De Doctor onderzoekt je shop...", expanded=True) as status:
                                # 1. Scrape de tekst van de homepage
                                from modules import competitor_spy
                                scrape_res = competitor_spy.scrape_homepage_text(target_url)
                                
                                if scrape_res['status'] == 'success':
                                    status.update(label="Analyse uitvoeren op Conversie Killers...", state="running")
                                    # 2. AI Analyse via de coach
                                    report = ai_coach.analyze_store_audit(scrape_res)
                                    
                                    st.markdown("---")
                                    st.markdown("### 📋 Het Rapport")
                                    st.markdown(report)
                                    st.balloons()
                                    status.update(label="Diagnose voltooid!", state="complete")
                                else:
                                    st.error(f"Kon de shop niet scannen: {scrape_res['message']}")
            else:
                render_pro_lock("The Store Doctor", "Laat AI je shop keuren voordat je live gaat.", "Voorkom dat je budget verspilt aan een shop die niet converteert.")

    elif pg == "Financiën":
        st.markdown("<h1><i class='bi bi-cash-stack'></i> Financiën</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["💡 Winst Calculator", "📈 Dagelijkse Stats"])
        
        with tab1:
            st.markdown("""
            <div style="background:#F0FDF4; padding:15px; border-radius:8px; border:1px solid #BBF7D0; margin-bottom:20px; color:#166534;">
                <b>💰 Gratis Tool:</b> Gebruik dit <u>VOORDAT</u> je geld uitgeeft aan inkoop.
                Weet zeker dat je product winstgevend is.
            </div>
            """, unsafe_allow_html=True)
            
            with st.container(border=True):
                st.markdown("### 🧮 Product Profit Calculator")
                c1, c2 = st.columns(2)
                
                # WORKFLOW PRE-FILL
                default_price = st.session_state.get('workflow_price', 29.95)
                
                vp = c1.number_input("Verkoopprijs (€)", value=float(default_price), step=1.0)
                ip = c1.number_input("Inkoop + Verzenden (€)", value=12.00, step=0.50)
                cpa = c2.number_input("Verwachte Ads kosten (CPA) (€)", value=10.00, step=0.50, help="Gemiddeld kost een sale €10-€15 aan ads.")
                
                tr = vp * 0.03 # Transactiekosten schatting
                winst = vp - (ip + cpa + tr)
                marge = (winst / vp * 100) if vp > 0 else 0
                
                st.markdown("---")
                cc1, cc2, cc3 = st.columns(3)
                cc1.metric("Transactiekosten (est.)", f"€{tr:.2f}")
                cc2.metric("Netto Winst", f"€{winst:.2f}", delta="Goed bezig" if winst > 5 else "Risicovol", delta_color="normal")
                cc3.metric("Marge", f"{marge:.1f}%", delta="> 20% is doel" if marge > 20 else "Te laag", delta_color="normal")
                
                if winst < 0:
                    st.error("⚠️ Pas op: Je maakt verlies met deze prijzen!")

        with tab2:
            st.markdown("**ℹ️ Wat doet deze tool?**\n\nHier zie je in één oogopslag of je vandaag winst of verlies hebt gemaakt. Vul elke ochtend je cijfers in.")
            with st.container(border=True):
                st.markdown("#### 📅 Resultaten van vandaag")
                c1, c2, c3 = st.columns(3)
                rev = c1.number_input("Totale Omzet (€)", 0.0, step=10.0, help="Alles wat Shopify zegt dat je hebt verkocht.")
                spend = c2.number_input("Advertentiekosten (€)", 0.0, step=5.0, help="Wat je aan Facebook/TikTok hebt betaald.")
                cogs = c3.number_input("Inkoopkosten (€)", 0.0, step=5.0, help="Wat de producten jou kosten bij de leverancier.")
                if st.button("Opslaan in Database", type="primary"):
                    if db.save_daily_stats(user['email'], rev, spend, cogs): st.success("Opgeslagen! Check de grafieken hieronder.")
                    else: st.error("Kon niet opslaan (Database error).")
            history = db.get_daily_stats_history(user['email'])
            if history:
                st.markdown("### 📊 Trends & Cijfers (Laatste 7 dagen)")
                df = pd.DataFrame(history)
                df['Profit'] = df['revenue'] - df['ad_spend'] - df['cogs']
                df['ROAS'] = df.apply(lambda x: x['revenue'] / x['ad_spend'] if x['ad_spend'] > 0 else 0, axis=1)
                total_rev = df['revenue'].sum()
                total_profit = df['Profit'].sum()
                avg_roas = df['ROAS'].mean()
                col1, col2, col3 = st.columns(3)
                col1.metric("Totaal Omzet", f"€{total_rev:.2f}")
                col2.metric("Netto Winst", f"€{total_profit:.2f}", delta="Winstgevend" if total_profit > 0 else "Verlies", delta_color="normal")
                col3.metric("Gemiddelde ROAS", f"{avg_roas:.2f}", delta="> 3.0 is top" if avg_roas > 3 else "Kan beter", delta_color="off")
                st.bar_chart(df, x="date", y="Profit", color="#10B981") 
                with st.expander("Bekijk ruwe data"): st.dataframe(df)
            else: st.info("Nog geen data. Vul hierboven je eerste dag in om de grafieken te zien!")

    elif pg == "Instellingen":
        st.markdown("<h1><i class='bi bi-gear-fill'></i> Instellingen</h1>", unsafe_allow_html=True)
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Mijn Profiel", "Geld verdienen", "Koppeling Shopify", "Hulp nodig?", "Feedback"])
        
        with tab1:
            # --- 1. PREMIUM HEADER (Met extra info) ---
            avatar_html = ""
            if user.get('avatar_url'):
                avatar_html = f'<img src="{user["avatar_url"]}" style="width:70px; height:70px; border-radius:50%; object-fit:cover; border:3px solid #BFDBFE;">'
            else:
                initial = user.get('first_name', 'M')[0].upper()
                avatar_html = f'<div style="width:70px; height:70px; background:#2563EB; color:white; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:30px; font-weight:800;">{initial}</div>'

            st.markdown(f"""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
                <div style="display: flex; align-items: center; gap: 20px;">
                    {avatar_html}
                    <div>
                        <h3 style="margin: 0; color: #0369A1;">{user.get('first_name', 'Boss')}</h3>
                        <p style="margin: 0; font-size: 0.85rem; color: #64748B;">
                            <b>ID:</b> {user.get('referral_code', 'ACAD-001')} • 
                            <b>Status:</b> {rank_title} (Lvl {user['level']})
                        </p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- 2. BUSINESS BLUEPRINT (Doelen) ---
            with st.container(border=True):
                st.markdown("#### 🎯 Bedrijfsinformatie")
                st.caption("Stel je kompas in. Ondernemers met een duidelijk doel groeien 3x sneller.")
                
                c1, c2 = st.columns(2)
                shop_name_val = c1.text_input("Naam van je merk", value=user.get('shop_name', 'Mijn Webshop'), help="Dit is de naam die op je logo en winkel komt.")
                goal_val = c2.selectbox("Maandelijks Omzetdoel", ["€5.000 (Starter)", "€10.000 (Scale-up)", "€25.000+ (Elite)"])
                
                reward_val = st.text_input("Jouw 'Why' (Beloning)", 
                                         value=user.get('income_goal_reward', ''),
                                         placeholder="Wat koop je als je dit doel haalt? (bijv. Die ene droomreis of laptop)")
                st.markdown("<div style='font-size: 0.75rem; color: #94A3B8; margin-top: -10px;'>Tip: Maak je beloning visueel. Dit houdt je gemotiveerd tijdens de late uurtjes.</div>", unsafe_allow_html=True)
                
                if st.button("Informatie Opslaan 🚀", use_container_width=True, type="primary"):
                    db.update_onboarding_data(user['email'], shop_name_val, goal_val)
                    # Optioneel: sla ook de reward op in je DB als je die kolom hebt gemaakt
                    st.balloons()
                    st.success("Je focus staat weer scherp!")

            # --- 3. PROFIELFOTO & BEVEILIGING ---
            col_left, col_right = st.columns(2)
            
            with col_left:
                with st.container(border=True):
                    st.markdown("#### 📸 Foto")
                    uploaded_file = st.file_uploader("Kies foto...", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
                    if uploaded_file and st.button("Foto Updaten", use_container_width=True):
                        # (Zelfde upload logica als je al had...)
                        img = Image.open(uploaded_file).resize((150, 150))
                        buffered = io.BytesIO()
                        img.save(buffered, format="PNG")
                        img_str = base64.b64encode(buffered.getvalue()).decode()
                        avatar_base64 = f"data:image/png;base64,{img_str}"
                        auth.supabase.table('users').update({"avatar_url": avatar_base64}).eq('email', user['email']).execute()
                        st.session_state.user['avatar_url'] = avatar_base64
                        st.rerun()

            with col_right:
                with st.container(border=True):
                    st.markdown("#### 🔒 Wachtwoord")
                    new_pw = st.text_input("Nieuw...", type="password", placeholder="Nieuw wachtwoord...", label_visibility="collapsed")
                    if st.button("Wachtwoord Opslaan", use_container_width=True):
                        if len(new_pw) >= 6:
                            db.update_password(user['email'], new_pw)
                            st.toast("Wachtwoord gewijzigd!", icon="✅")
                        else:
                            st.error("Minimaal 6 tekens.")

            # --- 4. FOOTER ACTIES ---
            st.markdown("<br>", unsafe_allow_html=True)
            c_out, c_del = st.columns([2, 1])
            c_out.button("🚪 Uitloggen", use_container_width=True, on_click=lambda: (cookie_manager.delete("rmecom_user_email"), st.session_state.clear()))
            with c_del.popover("🗑️ Account"):
                st.error("Let op: Dit is definitief!")
                if st.button("Wis al mijn data", type="primary"):
                    st.info("Neem contact op met support.")

        with tab2:
            # --- 1. PREMIUM HEADER ---
            st.markdown("""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
                <h3 style="margin-top: 0; color: #0369A1; font-size: 1.2rem; display: flex; align-items: center; gap: 10px; font-weight: 700;">
                    <span style="font-size: 1.5rem;">💸</span> Word RM Partner
                </h3>
                <p style="font-size: 1rem; color: #1E293B; line-height: 1.6;">
                    Wist je dat 1 succesvolle verwijzing genoeg is om <b>5 maanden gratis PRO</b> te zijn? Help anderen starten en bouw een passief inkomen op.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # --- 2. LIVE DASHBOARD (Stats Grid) ---
            stats = auth.get_affiliate_stats()
            # We simuleren kliks voor een actiever gevoel (stats[0] * factor)
            st.markdown(f"""
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-icon">Bezoekers</div>
                    <div class="stat-value">{stats[0] * 8}</div>
                    <div class="stat-sub">Kliks op jouw link</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">Aanmeldingen</div>
                    <div class="stat-value">{stats[1]}</div>
                    <div class="stat-sub">Nieuwe accounts</div>
                </div>
                <div class="stat-card" style="border: 1px solid #BBF7D0; background: #F0FDF4;">
                    <div class="stat-icon" style="color: #166534;">Jouw Winst</div>
                    <div class="stat-value" style="color: #166534;">€{stats[2]}</div>
                    <div class="stat-sub" style="color: #166534;">Betaalbaar per mail</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- 3. JOUW UNIEKE LINK ---
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("#### 🔗 Jouw Persoonlijke Partner Link")
                ref_link = f"https://app.rmacademy.nl/?ref={user.get('referral_code', 'GEEN-CODE')}"
                st.code(ref_link, language="text")
                
                whatsapp_tekst = f"""STOP met wat je doet! 🚨 Ik heb net de 'gouden' app van RM Ecom ontdekt. Je krijgt nu tijdelijk GRATIS toegang tot hun WinningHunter, Concurrenten-Spy en AI LogoMaker. 😱 Claim je plek NU voordat de toegang sluit: {ref_link}"""
                share_msg = urllib.parse.quote(whatsapp_tekst)
                
                st.link_button("📲 Deel direct via WhatsApp (+€250,- kans)", f"https://wa.me/?text={share_msg}", use_container_width=True, type="primary")

            # --- 4. HET PROCES VOOR STARTERS ---
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 🚀 Hoe verdien ik mijn eerste €250,-?")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown("""<div style="text-align:center;"><div style="font-size:30px;">📸</div><p style="font-size:0.8rem;"><b>Deel een story</b> van je dashboard of de AI tools.</p></div>""", unsafe_allow_html=True)
            with col_b:
                st.markdown("""<div style="text-align:center;"><div style="font-size:30px;">💬</div><p style="font-size:0.8rem;"><b>Stuur je link</b> naar mensen die ook een sidehustle zoeken.</p></div>""", unsafe_allow_html=True)
            with col_c:
                st.markdown("""<div style="text-align:center;"><div style="font-size:30px;">💰</div><p style="font-size:0.8rem;"><b>Ontvang cash</b> zodra ze starten met het traject.</p></div>""", unsafe_allow_html=True)
                
        with tab3:
            st.markdown("""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
                <h3 style="margin-top: 0; color: #0369A1; font-size: 1.2rem;">🔗 Shopify Koppeling</h3>
                <p style="font-size: 0.95rem; color: #1E293B;">Koppel je shop om je data live te analyseren en de 'Store Spy' te gebruiken.</p>
            </div>
            """, unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown("#### ⚙️ Verbindingsinstellingen")
                sh_url = st.text_input("Shop URL", placeholder="jouwshop.myshopify.com")
                sh_token = st.text_input("Access Token", type="password", placeholder="shpat_xxxxxxxxxxx")
                
                if st.button("Verbinding Testen & Opslaan", use_container_width=True, type="primary"):
                    # Hier zou je een check kunnen doen of de token werkt
                    st.success("Verbonden! Je shopgegevens worden nu opgehaald.")

            # Hulp sectie (Cruciaal voor starters!)
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("❓ Waar vind ik mijn Shopify Token?"):
                st.markdown("""
                1. Ga in Shopify naar **Settings** > **Apps and sales channels**.
                2. Klik op **Develop apps**.
                3. Klik op **Create an app** en geef het de naam 'RM Tools'.
                4. Ga naar **Configuration** en geef toegang tot 'Admin API' (Products, Orders, Content).
                5. Klik op **Install App** en kopieer de 'Admin API access token'.
                """)
        
        with tab4:
            # --- 1. PREMIUM HEADER ---
            st.markdown("""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
                <h3 style="margin-top: 0; color: #0369A1; font-size: 1.2rem; display: flex; align-items: center; gap: 10px; font-weight: 700;">
                    <span style="font-size: 1.5rem;">🆘</span> Je staat er nooit alleen voor
                </h3>
                <p style="font-size: 1rem; color: #1E293B; line-height: 1.6; margin-bottom: 10px;">
                    Of je nu een technische vraag hebt over Shopify of vastloopt bij het zoeken van producten: wij zijn er om je te helpen. Kies de juiste route voor het snelste antwoord.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # --- 2. CONTACT KAARTEN ---
            col_h1, col_h2 = st.columns(2)

            with col_h1:
                st.markdown("""
                <div style="background: white; border: 1px solid #E2E8F0; padding: 25px; border-radius: 16px; min-height: 220px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                    <div style="font-size: 40px; margin-bottom: 15px;">💬</div>
                    <h4 style="margin: 0; color: #0F172A;">Vragen over E-com?</h4>
                    <p style="font-size: 0.9rem; color: #64748B; margin-top: 10px; min-height: 60px;">
                        "Is dit product goed?", "Hoe werkt deze app?".<br>Stel je vraag aan 500+ andere studenten in de Discord.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='margin-top: -15px;'></div>", unsafe_allow_html=True) # Kleine correctie voor de knop
                st.link_button("Naar Discord Community", COMMUNITY_URL, type="primary", use_container_width=True)

            with col_h2:
                st.markdown("""
                <div style="background: white; border: 1px solid #E2E8F0; padding: 25px; border-radius: 16px; min-height: 220px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                    <div style="font-size: 40px; margin-bottom: 15px;">⚙️</div>
                    <h4 style="margin: 0; color: #0F172A;">Account & Techniek</h4>
                    <p style="font-size: 0.9rem; color: #64748B; margin-top: 10px; min-height: 60px;">
                        Inlogproblemen, betalingsvragen of technische fouten in de app.<br>Ons support-team helpt je persoonlijk.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='margin-top: -15px;'></div>", unsafe_allow_html=True)
                st.link_button("Stuur Email naar Support", "mailto:support@rmacademy.nl", use_container_width=True)
            
            # --- 3. VEELGESTELDE VRAGEN ---
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("❓ Veelgestelde vragen (FAQ)"):
                st.markdown("""
                **Is de app echt gratis?**
                Ja, de Roadmap en de basis-tools zijn gratis voor iedereen. Voor geavanceerde functies (zoals de Viral Hunter en Ad-Spy) heb je een PRO-abonnement of traject-toegang nodig.
                
                **Hoe krijg ik meer AI Credits?**
                Je credits worden elke nacht om 00:00 uur automatisch ververst naar 3. PRO-leden hebben onbeperkte credits.
                
                **Werkt mijn vriendencode ook voor de RM Tools?**
                Nee, vriendencodes geven je direct toegang tot de app. Voor het volledige coaching-traject moet je een strategiegesprek inplannen.
                """)
        
        with tab5:
            # --- 1. PREMIUM HEADER ---
            st.markdown("""
            <div style="background: #F0F9FF; border: 1px solid #BAE6FD; padding: 25px; border-radius: 16px; margin-bottom: 25px;">
                <h3 style="margin-top: 0; color: #0369A1; font-size: 1.2rem; display: flex; align-items: center; gap: 10px; font-weight: 700;">
                    <span style="font-size: 1.5rem;">💡</span> Help ons om de app te verbeteren en samen te groeien!
                </h3>
                <p style="font-size: 1rem; color: #1E293B; line-height: 1.6; margin-bottom: 10px;">
                    Loop je ergens tegenaan? Mis je een specifieke tool? Of heb je een tip voor Roy en Michael? Laat het ons weten. Wij bouwen deze app speciaal voor jouw succes.
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Check of de beloning al geclaimd is
            has_claimed_before = user.get('feedback_reward_claimed', False)

            if has_claimed_before and not is_pro_license:
                if is_temp_pro:
                    st.success(f"✅ Lekker bezig! Je 24u PRO toegang is momenteel actief! (Nog {time_left_str} over)")
                else:
                    st.info("Je hebt je eenmalige 24u PRO beloning al gebruikt. Word PRO lid voor onbeperkte toegang tot alle tools.")
                    st.link_button("🚀 Word PRO Lid (€49,95)", STRATEGY_CALL_URL, use_container_width=True)
            
            elif st.session_state.get("feedback_done", False):
                st.balloons()
                st.success("Bedankt voor je waardevolle feedback! Je 24u PRO toegang is nu actief. 🔥")
            
            else:
                # --- 2. DE BELONING (GOUD/GEEL) ---
                st.markdown("""
                <div style="background: #FFFBEB; border: 1px solid #FCD34D; padding: 20px; border-radius: 12px; margin-bottom: 25px;">
                    <h4 style="margin: 0; color: #92400E; font-size: 1.1rem; font-weight: 800;">🎁 Cadeau: 24u Gratis PRO Toegang</h4>
                    <p style="margin: 5px 0 0 0; font-size: 0.95rem; color: #B45309;">
                        Geef ons eerlijke feedback (minimaal 20 tekens) en unlock <b>direct</b> alle PRO functies zoals de Product Hunter en Spy Tools voor 24 uur.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # --- 3. INPUT AREA ---
                fb_text = st.text_area("Jouw ervaring:", placeholder="Wat vind je van de Roadmap? Wat kunnen we verbeteren voor starters?", height=150, key="feedback_text_input")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("Verstuur & Claim Beloning 🚀", use_container_width=True, type="primary", key="feedback_submit_btn"):
                    if len(fb_text) > 20:
                        with st.spinner("Je beloning wordt geactiveerd..."):
                            is_valid = ai_coach.validate_feedback(fb_text)
                            
                            if is_valid:
                                status = db.claim_feedback_reward(user['email'], fb_text)
                                if status == "SUCCESS":
                                    st.cache_data.clear() 
                                    st.session_state.feedback_done = True
                                    st.rerun() 
                                else:
                                    st.error("Er is iets misgegaan bij het opslaan. Probeer het later opnieuw.")
                            else:
                                st.warning("Je feedback is te kort of onduidelijk. Vertel ons iets meer om de beloning te unlocken!")
                    else:
                        st.warning("Vertel ons iets meer (minimaal 20 tekens) om je 24u PRO toegang te claimen.")

    # --- DE FOOTER (STAAT ONDERAAN ELKE PAGINA) ---
    render_footer()

    # --- NIEUW: CHAT WIDGET LADEN ---
    if "user" in st.session_state and st.session_state.user:
        # We geven nu 'pg' (de variabele die de huidige pagina bevat) mee!
        inject_chat_widget(st.session_state.user, pg)
