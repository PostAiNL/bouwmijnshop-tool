import streamlit as st
import time
import urllib.parse
import random
import pandas as pd
import textwrap
import base64 
import os
from PIL import Image
from streamlit_option_menu import option_menu
from datetime import datetime, timedelta, timezone
import extra_streamlit_components as stx
from modules import ai_coach, ui, auth, shopify_client, competitor_spy, roadmap, db

# --- 0. CONFIGURATIE ---
STRATEGY_CALL_URL = "https://calendly.com/rmecomacademy/30min"
COMMUNITY_URL = "https://discord.com"
COACH_VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 

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
    page_title="RM Ecom Academy",
    page_icon=fav_icon,
    layout="wide",
    initial_sidebar_state="auto"
)

# --- 1.5 META TAGS & PWA ICON FIX (BASE64) ---
# We injecteren het icoon als code, zodat het altijd werkt (ook op mobiel)
logo_b64 = get_base64_image(logo_path)
if logo_b64:
    icon_html = f'<link rel="icon" type="image/png" href="data:image/png;base64,{logo_b64}">'
    apple_icon_html = f'<link rel="apple-touch-icon" href="data:image/png;base64,{logo_b64}">'
else:
    icon_html = "" # Fallback als logo niet bestaat
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
    // Forceer favicon update voor hardnekkige browsers
    var link = document.querySelector("link[rel~='icon']");
    if (!link) {{
        link = document.createElement('link');
        link.rel = 'icon';
        document.getElementsByTagName('head')[0].appendChild(link);
    }}
    link.href = 'data:image/png;base64,{logo_b64 if logo_b64 else ""}';
</script>
""", unsafe_allow_html=True)

# --- 1. CSS ENGINE ---
st.markdown("""
    <style>
        /* 1. BELANGRIJK: Icoontjes inladen */
        @import url("https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css");

        /* ==============================================
           2. ALGEMENE CONFIGURATIE
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
        
        /* FIX VOOR ONZICHTBARE TEKST */
        p, .stMarkdown, .stCaption, [data-testid="stCaptionContainer"], small {
            color: #0F172A !important; 
        }

        * { -webkit-tap-highlight-color: transparent !important; }

        /* ==============================================
           3. HEADER & SIDEBAR FIXES
           ============================================== */
        header[data-testid="stHeader"] {
            background-color: #F8FAFC !important;
            border-bottom: none !important;
            pointer-events: auto !important; 
            height: 60px !important;
            z-index: 999990 !important;
        }

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
        
        [data-testid="stDecoration"] { display: none !important; }
        [data-testid="stStatusWidget"] { visibility: hidden !important; }
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

        /* ==============================================
           4. UI ELEMENTEN FIXES
           ============================================== */
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
        button[data-baseweb="tab"] div p { color: #64748B !important; font-weight: 600 !important; }
        button[data-baseweb="tab"][aria-selected="true"] div p { color: #2563EB !important; }
        div[data-baseweb="tab-highlight"] { background-color: #2563EB !important; }

        /* EXPANDER FIX */
        .streamlit-expanderHeader {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 2px solid #CBD5E1 !important;
            border-radius: 8px !important;
        }
        .streamlit-expanderHeader p, .streamlit-expanderHeader span, .streamlit-expanderHeader div { color: #0F172A !important; font-weight: 600 !important; }
        .streamlit-expanderHeader:hover { background-color: #1E293B !important; border-color: #0F172A !important; }
        .streamlit-expanderHeader:hover * { color: #FFFFFF !important; fill: #FFFFFF !important; }
        div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #0F172A !important; border-color: #CBD5E1 !important; }
        ul[data-baseweb="menu"] { background-color: #FFFFFF !important; }
        li[data-baseweb="option"] { color: #0F172A !important; background-color: #FFFFFF !important; }
        input[type="checkbox"] { accent-color: #2563EB !important; background-color: #FFFFFF !important; border-color: #CBD5E1 !important; }

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

        @media (max-width: 600px) {
            .stat-grid { gap: 8px; } .stat-value { font-size: 1.1rem; } .stat-icon { font-size: 0.65rem; } .stat-sub { font-size: 0.6rem; }
            .block-container { padding-top: 1.5rem !important; }
        }

        /* BUTTONS */
        div.stButton > button[kind="primary"] { background-color: #2563EB !important; border-color: #2563EB !important; color: white !important; }
        div.stButton > button[kind="primary"]:hover { background-color: #1D4ED8 !important; border-color: #1D4ED8 !important; }
        div.stButton > button:not([kind="primary"]) { background-color: #FFFFFF !important; color: #0F172A !important; border: 1px solid #CBD5E1 !important; }
        div.stButton > button:not([kind="primary"]):hover { border-color: #2563EB !important; color: #2563EB !important; background-color: #F8FAFC !important; }

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

        /* ==============================================
           SNELHEID FIXES (Wazigheid weg)
           ============================================== */
        .stApp > header { z-index: 1 !important; }
        [data-testid="stOverlay"], [data-testid="stDecoration"] { display: none !important; }
        div.stButton > button:active { transform: scale(0.98); }
    </style>
""", unsafe_allow_html=True)

# --- 2. COOKIE MANAGER ---
cookie_manager = stx.CookieManager()
if "user" not in st.session_state:
    cookie_email = cookie_manager.get("rmecom_user_email")
    if cookie_email:
        auth.login_or_register(cookie_email)
        st.rerun()

# --- 3. LOGIN SCHERM (PIXEL PERFECT MOBILE) ---
if "user" not in st.session_state:
    if "status" in st.query_params: st.query_params.clear()
    
    # --- CSS: ULTIEME COMPACTHEID ---
    st.markdown("""
    <style>
        /* ORANJE KNOP */
        div.stButton > button[kind="primary"] { 
            background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
            border: 1px solid #B45309 !important;
            color: white !important;
            font-weight: 800 !important;
            font-size: 1rem !important;
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
            box-shadow: 0 4px 6px rgba(245, 158, 11, 0.3);
            transition: all 0.2s;
            margin-top: 0px !important; /* Geen extra marge boven knop */
        }
        div.stButton > button[kind="primary"]:hover { 
            transform: scale(1.02);
            box-shadow: 0 6px 12px rgba(245, 158, 11, 0.4);
        }

        /* DEFAULT (Desktop) */
        .compact-title {
            font-size: 1.8rem !important;
            line-height: 1.2 !important;
            margin-bottom: 5px !important;
            margin-top: 0px !important;
            font-weight: 800 !important;
        }
        .compact-sub {
            font-size: 0.95rem !important;
            color: #64748B !important;
            line-height: 1.4 !important;
            margin-bottom: 15px !important;
        }
        
        /* PADDING BINNEN HET KADER */
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 20px !important;
            padding-top: 15px !important;
            padding-bottom: 15px !important;
        }

        /* MOBIEL SPECIFIEK (AGRESSIEF COMPACT) */
        @media only screen and (max-width: 600px) {
            /* Minder ruimte bovenin de app */
            .block-container { 
                padding-top: 1rem !important; 
                padding-bottom: 1rem !important; 
            }
            
            /* Titel kleiner zodat hij op 2 regels past */
            .compact-title { 
                font-size: 1.35rem !important; 
                margin-bottom: 4px !important; 
                line-height: 1.2 !important;
            }
            
            /* Subtekst kleiner */
            .compact-sub { 
                font-size: 0.85rem !important; 
                margin-bottom: 8px !important; 
                line-height: 1.3 !important;
            }
            
            /* Logo kleiner */
            .logo-text { 
                font-size: 0.8rem !important; 
                margin-bottom: 0px !important; 
            }
            
            /* Kader padding strakker */
            div[data-testid="stVerticalBlockBorderWrapper"] > div { 
                padding: 12px !important; 
                padding-top: 10px !important;
            }
            
            /* Ruimte tussen elementen verkleinen */
            div[data-testid="stExpander"] { margin-bottom: 0px !important; }
            .stTextInput { margin-bottom: 0px !important; }
            div[class*="stGap"] { gap: 0.5rem !important; }
        }
    </style>
    """, unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1, 1.1], gap="large", vertical_alignment="center")
    
    with col_left:
        # Logo
        st.markdown("<div class='logo-text' style='font-size: 0.9rem; font-weight: 600; color: #475569; margin-bottom: 0px;'><i class='bi bi-lightning-charge-fill' style='color:#2563EB;'></i> RM Ecom Academy</div>", unsafe_allow_html=True)
        
        # Titel & Subtitel
        st.markdown("""
        <h1 class='compact-title'>
            Van 0 naar <span style='color:#166534; background: #DCFCE7; padding: 0 6px; border-radius: 6px;'>€15k/maand</span> met je eigen webshop.
        </h1>
        <p class='compact-sub'>
            De enige app die je stap-voor-stap begeleidt. Geen technische kennis nodig. Start vandaag <b>gratis</b>.
        </p>
        """, unsafe_allow_html=True)
        
        with st.container(border=True):
            tab_free, tab_pro = st.tabs(["Nieuw Account", "Inloggen"])
            
            # TAB 1: REGISTREREN
            with tab_free:
                col_name, col_email = st.columns(2)
                first_name = col_name.text_input("Voornaam", placeholder="Je naam...", label_visibility="collapsed", key="reg_name")
                email = col_email.text_input("Email", placeholder="Je email...", label_visibility="collapsed", key="reg_email")
                password = st.text_input("Wachtwoord verzinnen", placeholder="Wachtwoord...", type="password", label_visibility="collapsed", key="reg_pass")
                
                with st.expander("Heb je een vriendencode?"):
                    ref_code = st.text_input("Vriendencode", placeholder="bv. JAN-482", label_visibility="collapsed", key="ref_code_input")
                
                # Minimale witruimte boven knop
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                
                # De knop (Oranje)
                if st.button("Start direct (gratis)", type="primary", use_container_width=True):
                    if email and "@" in email and first_name and password:
                        with st.spinner("Account aanmaken..."):
                            status = db.create_user(email, password, first_name)
                            if status == "SUCCESS":
                                auth.login_or_register(email, ref_code_input=ref_code if 'ref_code' in locals() and ref_code else None, name_input=first_name)
                                cookie_manager.set("rmecom_user_email", email, expires_at=datetime.now() + timedelta(days=30))
                                st.rerun()
                            elif status == "EXISTS": st.warning("Dit emailadres bestaat al. Probeer in te loggen.")
                            else: st.error("Er ging iets mis met de database.")
                    else:
                        st.warning("Vul alle velden in.")
                
                # Footer tekstjes (Heel compact)
                st.markdown("""<div style='text-align:center; margin-top:4px; line-height:1.2;'><div style='font-size:0.7rem; color:#475569; font-weight:500;'><i class="bi bi-check-circle-fill" style="font-size:10px; color:#16A34A;"></i> Geen creditcard nodig <span style='color:#CBD5E1;'>|</span> Direct toegang</div></div>""", unsafe_allow_html=True)
                st.markdown("""<div style='display: flex; align-items: center; justify-content: center; gap: 4px; margin-top: 2px; opacity: 1.0;'><div style="color: #F59E0B; font-size: 0.75rem;"><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i></div><span style='font-size: 0.75rem; color: #475569; font-weight: 600;'>4.9/5 (550+ studenten)</span></div>""", unsafe_allow_html=True)
            
            # TAB 2: INLOGGEN
            with tab_pro:
                log_email = st.text_input("Email", placeholder="Email...", key="log_email_in")
                log_pass = st.text_input("Wachtwoord", placeholder="Wachtwoord...", type="password", key="log_pass_in")
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("Inloggen", type="primary", use_container_width=True):
                    if log_email and log_pass:
                        if db.verify_user(log_email, log_pass):
                            auth.login_or_register(log_email)
                            cookie_manager.set("rmecom_user_email", log_email, expires_at=datetime.now() + timedelta(days=30))
                            st.rerun()
                        else: st.error("Onjuiste gegevens.")
                    else: st.warning("Vul alles in.")
    
    with col_right:
        st.markdown("<br class='desktop-only'>", unsafe_allow_html=True)
        # De 'USP' box rechts
        raw_html = """
        <div style="background: white; padding: 30px; border-radius: 20px; border: 1px solid #E2E8F0; box-shadow: 0 10px 40px -10px rgba(0,0,0,0.08); color: #0F172A;">
            <h3 style="margin-top:0; color:#0F172A; font-size:1.1rem; font-weight: 700; margin-bottom: 15px;">Dit krijg je gratis:</h3>
            
            <div style="display:flex; gap:16px; margin-bottom:20px; align-items:center;">
                <div style="width:48px; height:48px; background:#EFF6FF; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:22px; flex-shrink: 0;"><i class="bi bi-map-fill" style="color:#2563EB;"></i></div>
                <div><h4 style="margin:0; font-size:0.9rem; font-weight:600; color:#1E293B;">De 'Van 0 naar sales' roadmap</h4><p style="margin:0; font-size:0.8rem; color:#64748B;">Stap-voor-stap handleiding.</p></div>
            </div>
            
            <div style="display:flex; gap:16px; margin-bottom:20px; align-items:center;">
                <div style="width:48px; height:48px; background:#F0FDF4; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:22px; flex-shrink: 0;"><i class="bi bi-robot" style="color:#16A34A;"></i></div>
                <div><h4 style="margin:0; font-size:0.9rem; font-weight:600; color:#1E293B;">Jouw eigen AI coach</h4><p style="margin:0; font-size:0.8rem; color:#64748B;">24/7 hulp bij al je vragen.</p></div>
            </div>
            
            <div style="display:flex; gap:16px; align-items:center;">
                <div style="width:48px; height:48px; background:#FFF7ED; border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:22px; flex-shrink: 0;"><i class="bi bi-trophy-fill" style="color:#EA580C;"></i></div>
                <div><h4 style="margin:0; font-size:0.9rem; font-weight:600; color:#1E293B;">Level-based groei</h4><p style="margin:0; font-size:0.8rem; color:#64748B;">Verdien tools door actie te nemen.</p></div>
            </div>
        </div>
        """
        st.markdown(raw_html.replace("\n", ""), unsafe_allow_html=True)
    st.stop()

# --- 4. INGELOGDE DATA ---
user = st.session_state.user
is_pro_license = user.get('is_pro', False)

# Haal verse status op
is_temp_pro = db.check_pro_status_db(user['email'])
pro_expiry_dt = db.get_pro_expiry_date(user['email'])

time_left_str = ""
if pro_expiry_dt:
    # Huidige tijd in UTC
    now = datetime.now(timezone.utc)
    
    # Zorg dat de database datum ook UTC is (timezone aware maken indien nodig)
    if pro_expiry_dt.tzinfo is None:
        pro_expiry_dt = pro_expiry_dt.replace(tzinfo=timezone.utc)
        
    if pro_expiry_dt > now:
        is_temp_pro = True
        diff = pro_expiry_dt - now
        total_seconds = int(diff.total_seconds())
        hours = total_seconds // 3600
        mins = (total_seconds % 3600) // 60
        time_left_str = f"nog {hours}u {mins}m"
    else:
        is_temp_pro = False # Tijd is op

# Combineer de licentie status
is_pro = is_pro_license or is_temp_pro

def calculate_level_data(current_xp):
    levels = [(0, "Starter"), (500, "Builder"), (1500, "E-com Boss"), (3000, "Legend"), (5000, "Master"), (10000, "Grandmaster")]
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

def check_credits():
    if is_pro: return True
    if st.session_state.ai_credits > 0:
        st.session_state.ai_credits -= 1
        return True
    return False

def get_greeting():
    hour = datetime.now().hour
    return "Goedemorgen" if hour < 12 else "Goedemiddag" if hour < 18 else "Goedenavond"

def get_image_base64(path):
    try:
        with open(path, "rb") as image_file: encoded = base64.b64encode(image_file.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except: return None

# --- SIDEBAR ---
with st.sidebar:
    if "nav_index" not in st.session_state: st.session_state.nav_index = 0
    display_name = user.get('first_name') or user['email'].split('@')[0].capitalize()
    st.markdown(f"""<div style="margin-bottom: 2px; padding-left: 5px;"><h3 style="margin:0; font-size:1.0rem; color:#0F172A;"><i class="bi bi-person-circle"></i> {display_name}</h3><p style="margin:0; font-size: 0.75rem; color: #64748B;"><span style="background:#EFF6FF; padding:2px 6px; border-radius:4px; border:1px solid #DBEAFE; color:#2563EB; font-weight:600;">Lvl {user['level']}</span> {rank_title}</p></div>""", unsafe_allow_html=True)
    range_span = next_xp_goal_sidebar - prev_threshold
    if range_span <= 0: range_span = 1
    xp_pct = min((user['xp'] - prev_threshold) / range_span, 1.0) * 100
    st.markdown(f"""<div style="background: transparent; border-radius: 4px; height: 6px; width: 100%; margin-top: 8px; margin-bottom: 4px; border: 1px solid #F1F5F9;"><div style="background: #2563EB; height: 100%; width: {xp_pct}%; border-radius: 4px; transition: width 0.5s;"></div></div><div style="text-align:right; font-size:0.7rem; color:#94A3B8; margin-bottom:15px;">{user['xp']} / {next_xp_goal_sidebar} XP</div>""", unsafe_allow_html=True)
    if is_temp_pro: st.markdown(f"""<div style="margin-bottom:10px; font-size:0.8rem; color:#15803D; background:#DCFCE7; padding:8px; border-radius:6px; text-align:center; border:1px solid #BBF7D0;">🌟 <b>PRO Actief:</b> {time_left_str}</div>""", unsafe_allow_html=True)
    elif not is_pro: st.markdown(f"""<div style="margin-bottom:10px; font-size:0.8rem; color:#64748B; background:#F1F5F9; padding:6px; border-radius:6px; text-align:center;">⚡ <b>{st.session_state.ai_credits}</b>/3 dagelijkse AI credits</div>""", unsafe_allow_html=True)
    
    options = ["Dashboard", "Academy", "Producten Zoeken", "Marketing & Design", "Financiën", "Instellingen"]
    icons = ["house-fill", "mortarboard-fill", "search", "palette-fill", "cash-stack", "gear-fill"]
    
    menu_display_options = []
    for opt in options:
        if not is_pro and opt in ["Producten Zoeken", "Marketing & Design"]: 
             menu_display_options.append(f"{opt} 🔒")
        else:
             menu_display_options.append(opt)

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
        key="main_sidebar_menu"
    )
    
    if selected_display:
        pg = selected_display.replace(" 🔒", "")
    else:
        pg = "Dashboard"

    if not is_pro:
        st.markdown(f"""
        <a href="{STRATEGY_CALL_URL}" target="_blank" style="text-decoration:none;">
            <div style="margin-top: 20px; background: linear-gradient(135deg, #FFD700 0%, #F59E0B 100%); padding: 15px; border-radius: 12px; box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3); text-align: center; border: 1px solid #FCD34D;">
                <div style="font-weight: 800; color: #78350F; font-size: 1.1rem; margin-bottom: 4px;">🚀 UNLOCK ALLES</div>
                <div style="font-size: 0.8rem; color: #92400E; font-weight: 600;">Word Student & Groei</div>
            </div>
        </a>
        """, unsafe_allow_html=True)

# --- AANGEPASTE RENDER PRO LOCK - MET GROTERE ACHTERGROND ZODAT HET PAST ---
def render_pro_lock(title, desc, warning_text="Deze tool geeft onze studenten een oneerlijk voordeel. Daarom is dit afgeschermd."):
    lock_html = f"""
    <div style="position: relative; overflow: hidden; border-radius: 12px; border: 1px solid #E2E8F0; margin-top: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); background: #F8FAFC; min-height: 320px;">
        
        <!-- Geblurde achtergrond inhoud (GROTER GEMAAKT: 220px hoog totaal) -->
        <div style="filter: blur(5px); opacity: 0.5; padding: 20px; pointer-events: none; user-select: none;">
            <div style="height: 20px; background: #CBD5E1; width: 60%; margin-bottom: 15px; border-radius: 4px;"></div>
            <div style="display:flex; gap:10px; margin-bottom: 10px;">
                <div style="height: 150px; background: #E2E8F0; width: 30%; border-radius: 8px;"></div>
                <div style="height: 150px; background: #E2E8F0; width: 70%; border-radius: 8px;"></div>
            </div>
            <div style="height: 15px; background: #E2E8F0; width: 90%; margin-bottom: 8px; border-radius: 4px;"></div>
            <div style="height: 15px; background: #E2E8F0; width: 80%; border-radius: 4px;"></div>
        </div>

        <!-- Witte Box (Overlay) - GEEN VASTE HOOGTE, MAAR PAST NU IN DE ACHTERGROND -->
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
                        🚀 Unlock via Shop Review Call
                    </div>
                </a>
            </div>
        </div>
    </div>
    """
    st.markdown(lock_html.replace("\n", ""), unsafe_allow_html=True)

# --- CONTENT PAGES ---

if pg == "Dashboard":
    # 1. Check Level Up (Ongewijzigd)
    if user['level'] > st.session_state.prev_level:
        st.balloons()
        st.markdown(f"""<div class="levelup-overlay" onclick="this.style.display='none'"><div class="levelup-card"><div style="font-size:60px; margin-bottom:10px;">🏆</div><h1 style="color:#F59E0B !important; margin:0;">Level Up!</h1><h3 style="color:#0F172A;">Gefeliciteerd, je bent nu Level {user['level']}!</h3><p style="color:#64748B; margin:15px 0 25px 0;">Je hebt nieuwe features vrijgespeeld. Ga zo door!</p><div style="background:#2563EB; color:white; padding:12px 30px; border-radius:50px; cursor:pointer; font-weight:bold; display:inline-block;">Doorgaan 🚀</div></div></div>""", unsafe_allow_html=True)
        st.session_state.prev_level = user['level']

    # --- DATABEREKENING VOORAF ---
    if "force_completed" not in st.session_state: st.session_state.force_completed = []
    db_progress = auth.get_progress()
    completed_steps = list(set(db_progress + st.session_state.force_completed))
    full_map = roadmap.get_roadmap()
    
    # Bereken voortgang
    total_steps_count = sum(len(f['steps']) for f in full_map.values())
    done_count = len(completed_steps)
    progress_pct = int((done_count / total_steps_count) * 100) if total_steps_count > 0 else 0
    
    # Zoek volgende stap
    next_step_title, next_step_phase_index, next_step_id, next_step_locked, next_step_desc = "Alles afgerond! 🎉", 0, None, False, "Geniet van je succes."
    for idx, (fase_key, fase) in enumerate(full_map.items()):
        phase_done = True
        for s in fase['steps']:
            if s['id'] not in completed_steps:
                next_step_title = s['title']
                next_step_desc = s.get('teaser', 'Voltooi deze stap om verder te groeien.') # Haal teaser op of standaard tekst
                next_step_phase_index = idx + 1
                next_step_id = s['id']
                next_step_locked = s.get('locked', False)
                phase_done = False
                break
        if not phase_done: break
        if phase_done and idx == len(list(full_map.keys())) - 1: next_step_phase_index = 6 

    # 2. Header: Resultaatgericht
    name = user.get('first_name') or user['email'].split('@')[0].capitalize()
    
    # Header Layout
    c_head, c_prog = st.columns([2, 1], vertical_alignment="bottom")
    with c_head:
        st.markdown(f"<h1 style='margin-bottom: 5px;'>Goedemorgen, {name} 👋</h1>", unsafe_allow_html=True)
        st.caption(f"🚀 Missie: €15k/maand | 📈 Voortgang: **{progress_pct}%**")
    with c_prog:
        # Visuele progressie balk (klein)
        st.progress(progress_pct / 100)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # 3. Intro Bonus (Alleen zichtbaar bij 0 XP)
    if user['xp'] == 0:
        with st.container(border=True):
            col_text, col_btn = st.columns([3, 1], gap="medium", vertical_alignment="center")
            with col_text:
                st.markdown("""<div style="font-weight: 600; color: #1E40AF; font-size: 1rem;">🚀 Start hier je avontuur!</div><div style="font-size: 0.85rem; color: #64748B;">Klik op de knop om je eerste punten te verdienen en de roadmap te openen.</div>""", unsafe_allow_html=True)
            with col_btn:
                if st.button("Claim 50 XP ✨", type="primary", use_container_width=True):
                    auth.mark_step_complete("intro_bonus", 50)
                    if "force_completed" not in st.session_state: st.session_state.force_completed = []
                    st.session_state.force_completed.append("intro_bonus")
                    st.balloons()
                    st.toast("Gefeliciteerd! Je eerste 50 XP zijn binnen! 🎉", icon="🚀")
                    time.sleep(0.5)
                    st.rerun()

    # 4. Progress Bar (Boven roadmap)
    html_steps = ""
    labels = ["Start", "Bouwen", "Product", "Verkoop", "Schalen", "Beheer"] 
    for i in range(1, 7):
        status_class = "completed" if i < next_step_phase_index else "active" if i == next_step_phase_index else ""
        icon_content = f'<i class="bi bi-check-lg"></i>' if status_class == "completed" else f"{i}"
        html_steps += f'<div class="progress-step {status_class}">{icon_content}<div class="progress-label">{labels[i-1]}</div></div>'
    
    st.markdown(f'<div class="progress-container"><div class="progress-line"></div>{html_steps}</div>', unsafe_allow_html=True)
    
    # 5. Next Step Card (Aanbevolen Focus - UX VERBETERD)
    is_step_pro = next_step_locked and not is_pro
    if is_step_pro:
        card_bg, accent_color, btn_text, btn_bg, btn_url, btn_target, card_icon, status_text, title_color, card_border = "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)", "#F59E0B", "🚀 Word Student", "linear-gradient(to bottom, #FBBF24, #D97706)", STRATEGY_CALL_URL, "_blank", "bi-lock-fill", "Deze stap is exclusief voor studenten.", "#FFFFFF", "1px solid #F59E0B"
    else:
        # Hier maken we de tekst en knop actiegerichter
        card_bg, accent_color, btn_text, btn_bg, btn_url, btn_target, card_icon, status_text, title_color, card_border = "linear-gradient(135deg, #2563EB 0%, #1E40AF 100%)", "#DBEAFE", "🚀 Start Opdracht", "#FBBF24", "#roadmap_start", "_self", "bi-crosshair", next_step_desc, "#FFFFFF", "1px solid rgba(255,255,255,0.1)"

    mission_html = f"""
    <div style="background: {card_bg}; padding: 24px; border-radius: 16px; color: white; margin-bottom: 20px; box-shadow: 0 10px 30px -5px rgba(0,0,0,0.4); border: {card_border}; position: relative; overflow: hidden;">
        <div style="position: relative; z-index: 2;">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.9; margin-bottom: 8px; font-weight: 700; color: {accent_color};"><i class="bi {card_icon}"></i> AANBEVOLEN FOCUS</div>
                    <div style="margin: 0; font-size: 1.6rem; color: {title_color} !important; font-weight: 800; letter-spacing: -0.5px; line-height: 1.2; text-shadow: 0 2px 4px rgba(0,0,0,0.3); margin-bottom: 8px;">{next_step_title}</div>
                    <p style="margin: 8px 0 20px 0; font-size:0.95rem; opacity:0.9; max-width: 500px; line-height: 1.5; color: #F1F5F9;">{status_text}</p>
                </div>
            </div>
            <a href="{btn_url}" target="{btn_target}" style="text-decoration:none;">
                <div style="display: inline-block; background: {btn_bg}; color: #78350F; padding: 12px 32px; border-radius: 8px; font-weight: 800; font-size: 1rem; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: transform 0.1s; border: 1px solid rgba(255,255,255,0.2);">
                    {btn_text}
                </div>
            </a>
        </div>
    </div>"""
    st.markdown(mission_html, unsafe_allow_html=True)
    
    # 6. Stats (Kleine update: 'Volgende level' inzichtelijk maken)
    needed = next_xp_goal_sidebar - user['xp']
    next_reward = "Spy tool" if user['level'] < 2 else "Video scripts"
    st.markdown(f"""<div class="stat-grid"><div class="stat-card"><div class="stat-icon"><i class="bi bi-bar-chart-fill"></i> Level</div><div class="stat-value">{user['level']}</div><div class="stat-sub">{rank_title}</div></div><div class="stat-card"><div class="stat-icon"><i class="bi bi-lightning-fill"></i> XP</div><div class="stat-value">{user['xp']}</div><div class="stat-sub">Nog <b>{needed}</b> voor Lvl {user['level']+1}</div></div><div class="stat-card"><div class="stat-icon"><i class="bi bi-gift-fill"></i> Beloning</div><div class="stat-value" style="font-size: 1.2rem; padding-top:2px;">🎁</div><div class="stat-sub" style="color:#2563EB;">{next_reward}</div></div></div>""", unsafe_allow_html=True)
    
    st.markdown("<div id='roadmap_start' style='height: 0px;'></div>", unsafe_allow_html=True)
    st.markdown("### 📍 Jouw Roadmap")
    st.caption("Klik op een fase om je taken te bekijken.")
    
    # 7. OPEN ROADMAP LOOP (Met Focus Mode 🔍 + Vrijheid 🗽)
    active_phase_idx = next_step_phase_index 
    
    for idx, (fase_key, fase) in enumerate(full_map.items()):
        phase_num = idx + 1
        
        is_current_phase = (phase_num == active_phase_idx)
        
        if phase_num < active_phase_idx:
            phase_icon = "✅" 
            phase_label = f"{fase['title']} (Voltooid)"
        elif phase_num == active_phase_idx:
            phase_icon = "📍" 
            phase_label = f"{fase['title']} (Nu Actief)" # Duidelijkere tekst
        else:
            phase_icon = "📂"
            phase_label = fase['title']
            
        with st.expander(f"{phase_icon} {phase_label}", expanded=is_current_phase):
            st.caption(fase['desc'])
            
            for step in fase['steps']:
                is_done = step['id'] in completed_steps
                
                if is_done:
                    with st.expander(f"✅ {step['title']}", expanded=False): 
                        st.info("Deze stap heb je al afgerond. Goed bezig!")
                else:
                    is_recommended = (step['id'] == next_step_id)
                    just_completed_id, xp = roadmap.render_step_card(step, is_done, is_pro, expanded=is_recommended)
                    
                    if just_completed_id:
                        with st.spinner("Opslaan..."):
                            auth.mark_step_complete(just_completed_id, xp)
                            if "force_completed" not in st.session_state: st.session_state.force_completed = []
                            st.session_state.force_completed.append(just_completed_id)
                            st.toast(f"🚀 Lekker bezig! +{xp} XP", icon="🎉") 
                            st.rerun()
    
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

elif pg == "Academy":
    st.markdown("<h1><i class='bi bi-mortarboard-fill'></i> Academy</h1>", unsafe_allow_html=True)
    st.caption("Korte training om je eerste stappen als e-commerce starter snel helder te krijgen.")
    t1, t2 = st.columns(2)
    t3, t4 = st.columns(2)
    def video_header(text): st.markdown(f"<div style='font-weight:700; font-size:0.95rem; margin-bottom:8px; color:#0F172A;'>{text}</div>", unsafe_allow_html=True)
    with t1:
        video_header("1. Mindset & realistische verwachtingen")
        with st.container(border=True): st.markdown('<iframe src="https://drive.google.com/file/d/1xyM_9q2i5FJBF__HvmhDrHTBueBoBstv/preview" width="100%" height="300" style="border-radius:8px; border:none;"></iframe>', unsafe_allow_html=True)
        st.info("Noteer na deze video in 3 bulletpoints waarom je deze webshop wilt. Dat helpt je bij tegenslag.")
    with t2:
        video_header("2. Hoe werkt een winstgevende webshop echt")
        with st.container(border=True): st.markdown('<iframe src="https://drive.google.com/file/d/1O4fa0FUA10MnCE4QqNNDe3XSLwLfkb_F/preview" width="100%" height="300" style="border-radius:8px; border:none;"></iframe>', unsafe_allow_html=True)
        st.info("Let extra op: verkeer, conversie en marge. Schrijf 1 actie op per blok.")
    with t3:
        video_header("3. Je eerste sale neerzetten")
        with st.container(border=True): st.markdown('<iframe src="https://drive.google.com/file/d/1xyM_9q2i5FJBF__HvmhDrHTBueBoBstv/preview" width="100%" height="300" style="border-radius:8px; border:none;"></iframe>', unsafe_allow_html=True)
        st.success("Na deze video kies je één product en één kanaal. Niet alles tegelijk.")
    with t4:
        video_header("4. Van 1 naar 100 sales")
        with st.container(border=True): st.markdown('<iframe src="https://drive.google.com/file/d/1O4fa0FUA10MnCE4QqNNDe3XSLwLfkb_F/preview" width="100%" height="300" style="border-radius:8px; border:none;"></iframe>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""<div style="background: #F0F9FF; padding: 25px; border-radius: 12px; border: 1px solid #BAE6FD; text-align: center;"><h4 style="color:#0369A1; margin-bottom:6px;">Klaar voor het echte werk?</h4><p style="color:#0C4A6E; margin:0;">Je hebt de basis gezien. Wil je dat we meekijken zodat dit ook echt gaat draaien?</p></div>""", unsafe_allow_html=True)
        st.link_button("Plan gratis strategie call", STRATEGY_CALL_URL, type="primary", use_container_width=True)

elif pg == "Financiën":
    st.markdown("<h1><i class='bi bi-cash-stack'></i> Financiën</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Dagelijkse Winst", "Winst Berekenen"])
    with tab1:
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
    with tab2:
        st.markdown("**ℹ️ Wat doet deze tool?**\n\nBereken of je product winstgevend is *voordat* je begint met verkopen. Zo voorkom je dat je geld verliest.")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            vp = c1.number_input("Verkoopprijs", value=29.95)
            ip = c1.number_input("Inkoop + Verzenden", value=12.00)
            cpa = c2.number_input("Ads kosten (CPA)", value=10.00)
            tr = vp * 0.03
            winst = vp - (ip + cpa + tr)
            marge = (winst / vp * 100) if vp > 0 else 0
            st.markdown("---")
            cc1, cc2, cc3 = st.columns(3)
            cc1.metric("Netto Winst", f"€{winst:.2f}")
            cc2.metric("Marge", f"{marge:.1f}%")

elif pg == "Marketing & Design": # Naam in menu en code nu gelijk
    st.markdown("<h1><i class='bi bi-palette-fill'></i> Marketing & Design</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["Logo Maker", "Video Scripts", "Teksten Schrijven", "Advertentie Check"])
    
    with tab1:
        st.markdown("**ℹ️ Wat doet deze tool?**\n\nMaak binnen 10 seconden een uniek logo voor je merk. Typ je naam in en kies een stijl.")
        if "logo_generations" not in st.session_state: st.session_state.logo_generations = 0
        has_access = is_pro or st.session_state.logo_generations < 3
        if not has_access: render_pro_lock("Credits op", "Je hebt 3 gratis logo's gemaakt. Word student om onbeperkt te genereren.", "Concurrenten betalen €200 voor een logo. Jij krijgt dit gratis.")
        else:
            if not is_pro: st.info(f"🎁 Je hebt nog **{3 - st.session_state.logo_generations}** gratis logo generaties over.")
            with st.container(border=True):
                col1, col2 = st.columns(2)
                brand_name = col1.text_input("Bedrijfsnaam", placeholder="Bijv. Lumina")
                niche = col1.text_input("Niche", placeholder="Bijv. Moderne verlichting")
                style = col2.selectbox("Stijl", ["Minimalistisch", "Modern & strak", "Vintage", "Luxe", "Speels"])
                color = col2.text_input("Voorkeurskleuren", placeholder="Bijv. Zwart en goud")
                if st.button("Genereer logo's", type="primary", use_container_width=True):
                    if not brand_name or not niche: st.warning("Vul alles in.")
                    else:
                        st.session_state.logo_generations += 1
                        with st.spinner("Ontwerpen..."):
                            images = []
                            for i in range(3):
                                img_url = ai_coach.generate_logo(brand_name, niche, style, color)
                                if img_url: images.append(img_url)
                            if images:
                                cols = st.columns(3)
                                for idx, img in enumerate(images):
                                    with cols[idx]: st.image(img, use_container_width=True)
    with tab2:
        st.markdown("**ℹ️ Wat doet deze tool?**\n\nWeet je niet wat je moet zeggen in je video? Deze tool schrijft virale scripts voor TikTok en Instagram Reels.")
        if is_pro:
            with st.container(border=True):
                prod = st.text_input("Product", key="vid_prod")
                if st.button("Genereer scripts", type="primary", key="vid_btn") and prod:
                    res = ai_coach.generate_viral_scripts(prod, "", "Viral")
                    st.markdown("### Hooks")
                    for h in res['hooks']: st.info(h)
                    with st.expander("Script"): st.text_area("Script", res['full_script'])
                    with st.expander("Briefing"): st.code(res['creator_brief'])
        else: render_pro_lock("Viral video scripts", "Laat AI scripts schrijven.", "Dit script ging vorige week 3x viraal. Alleen voor studenten.")
    with tab3:
        st.markdown("**ℹ️ Wat doet deze tool?**\n\nLaat AI een verkopende productbeschrijving schrijven of een berichtje maken om naar influencers te sturen.")
        t_desc, t_inf = st.tabs(["🛍️ Beschrijvingen", "🤳 Influencer Script"])
        with t_desc:
            with st.container(border=True):
                prod_name = st.text_input("Productnaam / URL (AliExpress)", placeholder="Bv. Galaxy Star Projector")
                if st.button("✨ Genereer Beschrijving", type="primary", use_container_width=True):
                    if not prod_name: st.warning("Vul een naam in.")
                    elif check_credits():
                        with st.spinner("AI is aan het schrijven..."):
                            res = ai_coach.generate_product_description(prod_name)
                            st.markdown(res)
                            st.success("Tekst gegenereerd!")
                    else: st.warning("Je dagelijkse credits zijn op. Word student voor onbeperkt toegang.")
        with t_inf:
            with st.container(border=True):
                inf_prod = st.text_input("Jouw Product", placeholder="Bv. Organic Face Serum")
                if st.button("📩 Genereer DM Script", type="primary", use_container_width=True):
                    if not inf_prod: st.warning("Vul een product in.")
                    elif check_credits():
                        with st.spinner("Script schrijven..."):
                            res = ai_coach.generate_influencer_dm(inf_prod)
                            st.code(res, language="text")
                            st.success("Kopieer en plak dit in Instagram DM!")
                    else: st.warning("Je dagelijkse credits zijn op.")
    with tab4:
        st.markdown("**ℹ️ Wat doet deze tool?**\n\nUpload een screenshot van je Facebook/TikTok advertentie. De AI vertelt je precies wat er beter kan.")
        if is_pro:
            with st.container(border=True):
                st.info("Upload screenshot van Ads Manager.")
                st.file_uploader("Bestand")
                st.button("Diagnose starten", type="primary")
        else: render_pro_lock("Ads check", "Laat je advertenties beoordelen.", "Gooi geen geld weg aan slechte ads. Laat AI ze checken.")

elif pg == "Producten Zoeken":
    st.markdown("<h1><i class='bi bi-search'></i> Producten Zoeken</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Winnende Producten", "Concurrenten Check"]) 
    with tab1:
        st.markdown("**ℹ️ Wat doet deze tool?**\n\nWeet je niet wat je moet verkopen? Deze tool zoekt populaire 'winnende' producten voor je uit.")
        if not is_pro:
            st.markdown("### 🎁 Gratis Voorbeeld: Huidige Bestseller")
            with st.container(border=True):
                st.markdown(f"**🔥 Galaxy Star Projector 2.0**")
                st.caption("Richtprijs verkoop: €34.95")
                st.write(f"💡 **Waarom viral:** Visueel spectaculair voor TikTok, lost het probleem op van saaie kamers, hoge marge.")
                c1, c2 = st.columns(2)
                c1.link_button("TikTok Voorbeelden", "https://www.tiktok.com/search?q=galaxy+projector", use_container_width=True)
                c2.link_button("AliExpress Inkoop", "https://www.aliexpress.com/wholesale?SearchText=galaxy+projector", use_container_width=True)
            st.write("") 
            render_pro_lock("Ontgrendel alle winnende producten", "Krijg toegang tot de volledige database met dagelijks nieuwe producten.", "Studenten vinden hier producten die €10k/maand draaien.")
        else:
            with st.container(border=True):
                col_inp, col_btn = st.columns([3, 1])
                niche = col_inp.text_input("In welke niche zoek je een product?", "Gadgets")
                if col_btn.button("Zoek ideeën", type="primary", use_container_width=True):
                    if not niche: st.warning("Vul een niche in.")
                    else:
                        results = ai_coach.find_real_winning_products(niche, "Viral")
                        if results:
                            st.markdown(f"**Resultaten voor '{niche}':**")
                            for p in results:
                                with st.container(border=True):
                                    st.markdown(f"### {p.get('title')}")
                                    st.caption(f"Richtprijs: €{p.get('price')}")
                                    st.write(f"💡 {p.get('hook')}")
                                    if p.get('search_links'):
                                        c1, c2 = st.columns(2)
                                        c1.link_button("TikTok", p['search_links']['tiktok'], use_container_width=True)
                                        c2.link_button("AliExpress", p['search_links']['ali'], use_container_width=True)
    with tab2:
        st.markdown("**ℹ️ Wat doet deze tool?**\n\nSpiek bij de buren! Vul een webshop in van een concurrent en zie direct wat hun best verkopende producten zijn.")
        if is_pro:
            with st.container(border=True):
                url = st.text_input("URL van concurrent")
                if url and st.button("Scan bestsellers", type="primary"):
                     with st.spinner("Scannen..."):
                         products = competitor_spy.scrape_shopify_store(url)
                         if products:
                             for p in products:
                                 with st.container(border=True):
                                     c1, c2 = st.columns([1, 3])
                                     if p['image_url']: c1.image(p['image_url'])
                                     c2.markdown(f"**{p['title']}**")
                                     c2.caption(f"Prijs: €{p['price']}")
                                     c2.markdown(f"[Bekijk]({p['original_url']})")
        else: render_pro_lock("Spy tool", "Zie bestsellers van andere shops.", "Zie EXACT hoeveel omzet je concurrent draait. Oneerlijk voordeel.")

elif pg == "Instellingen":
    st.markdown("<h1><i class='bi bi-gear-fill'></i> Instellingen</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Profiel", "Partner", "Koppelingen", "Hulp", "Feedback"])
    
    with tab1:
        with st.container(border=True):
            display_name = user.get('first_name') or user['email'].split('@')[0].capitalize()
            letter = display_name[0].upper()
            st.markdown(f"""<div style="display:flex; align-items:center; gap:20px; margin-bottom:20px;"><div style="width:60px; height:60px; background:#EFF6FF; border-radius:50%; display:flex; justify-content:center; align-items:center; font-size:24px; color:#2563EB; font-weight:bold; border:2px solid #2563EB;">{letter}</div><div><h3 style="margin:0;">{display_name}</h3><p style="margin:0; color:#64748B;">{user['email']}</p><p style="margin:0; font-size:0.8rem; color:#64748B;">Status: {'Student' if is_pro else 'Gast'}</p></div></div>""", unsafe_allow_html=True)
            if st.button("Uitloggen", use_container_width=True):
                cookie_manager.delete("rmecom_user_email")
                st.session_state.clear()
                st.rerun()
    with tab2:
        stats = auth.get_affiliate_stats()
        st.markdown(f"""<div class="stat-grid"><div class="stat-card"><div class="stat-icon">Totaal</div><div class="stat-value">{stats[0]}</div></div><div class="stat-card"><div class="stat-icon">Studenten</div><div class="stat-value">{stats[1]}</div></div><div class="stat-card"><div class="stat-icon">Verdiend</div><div class="stat-value">€{stats[2]}</div></div></div>""", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### Jouw vrienden code")
            st.caption("Deel deze code met mensen die willen starten.")
            st.code(user['referral_code'], language="text")
    with tab3:
        with st.container(border=True):
            st.markdown("#### Shopify koppeling")
            sh_url = st.text_input("Shop URL", value=st.session_state.get("sh_url", ""), placeholder="mijnshop.myshopify.com")
            sh_token = st.text_input("Private app token", type="password", value=st.session_state.get("sh_token", ""))
            if st.button("Opslaan", use_container_width=True):
                st.session_state["sh_url"] = sh_url.strip()
                st.session_state["sh_token"] = sh_token.strip()
                st.success("Opgeslagen.")
    with tab4:
        with st.container(border=True):
            st.markdown("#### Support")
            st.link_button("Discord community", COMMUNITY_URL, use_container_width=True)
            st.link_button("Email support", "mailto:support@rmecom.nl", use_container_width=True)
    with tab5:
        st.markdown("#### 💡 Jouw mening telt")
        st.caption("Geef goede feedback en ontvang **éénmalig 24u PRO toegang** gratis!🎁")
        fb_text = st.text_area("Feedback", placeholder="Ik mis functie X...", height=120, key="fb_settings")
        
        # HIER STAAT DE KNOP NU VEILIG BINNEN DE TAB
        if st.button("Verstuur & Claim PRO🚀", use_container_width=True):
            if len(fb_text) > 10:
                with st.spinner("Checken..."):
                    # 1. Valideer en sla op
                    is_valid = ai_coach.validate_feedback(fb_text)
                    db.save_feedback(user['email'], fb_text, is_valid)
                    
                    if is_valid:
                        # 2. Claim de reward in de database
                        status = db.claim_feedback_reward(user['email'])
                        
                        if status == "SUCCESS":
                            st.balloons()
                            st.success("🎉 PRO Geactiveerd! 24u toegang gestart.")
                            
                            # Update Sessie & Cache
                            user['is_pro'] = True 
                            st.session_state.user['is_pro'] = True
                            st.cache_data.clear()
                            
                            time.sleep(2)
                            st.rerun() 
                        elif status == "ALREADY_CLAIMED":
                            st.info("Je hebt deze beloning al eens geclaimd.")
                        else: 
                            st.error("Database fout bij activeren PRO.")
                    else: 
                        st.warning("Feedback te kort of onduidelijk.")
            else: 
                st.warning("Typ minimaal 10 letters.")