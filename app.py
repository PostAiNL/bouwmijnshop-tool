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
        
        div.stButton > button[kind="primary"] { background-color: #2563EB !important; border-color: #2563EB !important; color: white !important; }
        div.stButton > button[kind="primary"]:hover { background-color: #1D4ED8 !important; border-color: #1D4ED8 !important; }
        div.stButton > button:not([kind="primary"]) { background-color: #FFFFFF !important; color: #0F172A !important; border: 1px solid #CBD5E1 !important; }
        div.stButton > button:not([kind="primary"]):hover { border-color: #2563EB !important; color: #2563EB !important; background-color: #F8FAFC !important; }
        
        /* Klik effect voor sneller gevoel */
        div.stButton > button:active { transform: scale(0.98); }

        /* EXPANDER FIX (De Fase Balken Kleur) */
        details > summary {
            background-color: #EFF6FF !important; /* Zachtblauw */
            border: 1px solid #DBEAFE !important; /* Blauw randje */
            border-radius: 8px !important;
            padding-top: 10px !important;
            padding-bottom: 10px !important;
            color: #0F172A !important;
            transition: all 0.2s ease-in-out;
        }
        details > summary:hover {
            background-color: #DBEAFE !important;
            border-color: #2563EB !important;
            color: #2563EB !important;
        }
        details > summary p, details > summary span {
            color: inherit !important;
            font-weight: 700 !important;
            font-size: 1.05rem !important;
        }
        .streamlit-expanderHeader {
            background-color: transparent !important;
            border: none !important;
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

        @media (max-width: 600px) {
            .stat-grid { gap: 8px; } .stat-value { font-size: 1.1rem; } .stat-icon { font-size: 0.65rem; } .stat-sub { font-size: 0.6rem; }
            .block-container { padding-top: 1.5rem !important; }
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

# --- 2. COOKIE MANAGER ---
cookie_manager = stx.CookieManager()

# Check of we de gebruiker moeten inloggen
if "user" not in st.session_state:
    cookie_email = cookie_manager.get("rmecom_user_email")
    if cookie_email:
        with st.spinner(f"👋 Welkom terug! Automatisch inloggen als {cookie_email}..."):
            time.sleep(0.3) 
            auth.login_or_register(cookie_email)
            st.rerun()

# --- 3. LOGIN SCHERM (PIXEL PERFECT MOBILE) ---
if "user" not in st.session_state:
    if "status" in st.query_params: st.query_params.clear()
    
    st.markdown("""
    <style>
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
            margin-top: 0px !important;
        }
        div.stButton > button[kind="primary"]:hover { 
            transform: scale(1.02);
            box-shadow: 0 6px 12px rgba(245, 158, 11, 0.4);
        }
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
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 20px !important;
            padding-top: 15px !important;
            padding-bottom: 15px !important;
        }
        @media only screen and (max-width: 600px) {
            .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
            .compact-title { font-size: 1.35rem !important; margin-bottom: 4px !important; line-height: 1.2 !important; }
            .compact-sub { font-size: 0.85rem !important; margin-bottom: 8px !important; line-height: 1.3 !important; }
            .logo-text { font-size: 0.8rem !important; margin-bottom: 0px !important; }
            div[data-testid="stVerticalBlockBorderWrapper"] > div { padding: 12px !important; padding-top: 10px !important; }
            div[data-testid="stExpander"] { margin-bottom: 0px !important; }
            .stTextInput { margin-bottom: 0px !important; }
            div[class*="stGap"] { gap: 0.5rem !important; }
        }
    </style>
    """, unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1, 1.1], gap="large", vertical_alignment="center")
    
    with col_left:
        st.markdown("<div class='logo-text' style='font-size: 0.9rem; font-weight: 600; color: #475569; margin-bottom: 0px;'><i class='bi bi-lightning-charge-fill' style='color:#2563EB;'></i> RM Ecom Academy</div>", unsafe_allow_html=True)
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
            with tab_free:
                col_name, col_email = st.columns(2)
                first_name = col_name.text_input("Voornaam", placeholder="Je naam...", label_visibility="collapsed", key="reg_name")
                email = col_email.text_input("Email", placeholder="Je email...", label_visibility="collapsed", key="reg_email")
                password = st.text_input("Wachtwoord verzinnen", placeholder="Wachtwoord...", type="password", label_visibility="collapsed", key="reg_pass")
                with st.expander("Heb je een vriendencode?"):
                    ref_code = st.text_input("Vriendencode", placeholder="bv. JAN-482", label_visibility="collapsed", key="ref_code_input")
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
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
                    else: st.warning("Vul alle velden in.")
                st.markdown("""<div style='text-align:center; margin-top:4px; line-height:1.2;'><div style='font-size:0.7rem; color:#475569; font-weight:500;'><i class="bi bi-check-circle-fill" style="font-size:10px; color:#16A34A;"></i> Geen creditcard nodig <span style='color:#CBD5E1;'>|</span> Direct toegang</div></div>""", unsafe_allow_html=True)
                st.markdown("""<div style='display: flex; align-items: center; justify-content: center; gap: 4px; margin-top: 2px; opacity: 1.0;'><div style="color: #F59E0B; font-size: 0.75rem;"><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i><i class="bi bi-star-fill"></i></div><span style='font-size: 0.75rem; color: #475569; font-weight: 600;'>4.9/5 (550+ studenten)</span></div>""", unsafe_allow_html=True)
            
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

is_pro_license = user.get('is_pro', False)
# ⚠️ TEST MODE AAN (Zet hier een # voor als je live gaat!)
is_pro_license = True 

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
    
    # --- NIEUW: DE PRO TIMER ---
    if is_temp_pro and time_left_str:
        st.markdown(f"""
        <div style="margin-bottom:15px; background: linear-gradient(135deg, #DCFCE7 0%, #BBF7D0 100%); padding: 10px; border-radius: 8px; border: 1px solid #86EFAC; display: flex; align-items: center; justify-content: space-between;">
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-size: 1.2rem;">⏳</span>
                <div style="line-height:1.1;">
                    <div style="font-size: 0.7rem; color: #166534; font-weight: 700; text-transform: uppercase;">PRO Tijd over</div>
                    <div style="font-size: 0.95rem; color: #14532D; font-weight: 800;">{time_left_str}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif not is_pro:
        st.markdown(f"""<div style="margin-bottom:10px; font-size:0.8rem; color:#64748B; background:#F1F5F9; padding:6px; border-radius:6px; text-align:center;">⚡ <b>{st.session_state.ai_credits}</b>/3 dagelijkse AI credits</div>""", unsafe_allow_html=True)
    
    options = ["Dashboard", "Academy", "Producten Zoeken", "Marketing & Design", "Financiën", "Instellingen"]
    icons = ["house-fill", "mortarboard-fill", "search", "palette-fill", "cash-stack", "gear-fill"]
    
    menu_display_options = []
    for opt in options:
        if not is_pro and opt in ["Marketing & Design"]: # Producten Zoeken is nu 'gratis' (1x) dus geen slotje in menu
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
                <div style="font-size: 0.75rem; color: #92400E; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Plan Gratis Strategie Call</div>
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
# =========================================================

# --- CONTENT PAGES ---

if selected_display: pg = selected_display.replace(" 🔒", "")
else: pg = "Dashboard"

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
                        📞 Plan Gratis Strategie Call
                    </div>
                </a>
            </div>
        </div>
    </div>
    """
    st.markdown(lock_html.replace("\n", ""), unsafe_allow_html=True)

# --- ONBOARDING WIZARD ---
# Omdat iedereen zich registreert, kijken we direct in de DATABASE (user_extra).
# Als daar een shopnaam bekend is, hoeft de wizard niet meer getoond te worden.

# 1. Haal op of er al een shopnaam in de DB staat
db_shop_name = user_extra.get('shop_name') if user_extra else None

# 2. Check of we de wizard toevallig NET hebben afgerond in deze sessie
session_wizard_done = st.session_state.get("wizard_complete", False)

# 3. CRUCIALE CHECK: Heeft de gebruiker al XP? (Zo ja -> Sla over)
has_xp = user.get('xp', 0) > 0

# 4. Logica: Toon Wizard ALLEEN als er GEEN shopnaam is EN niet net afgerond EN nog 0 XP
if not db_shop_name and not session_wizard_done and not has_xp:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        welcome_name = user.get('first_name', 'Ondernemer')
        st.markdown(f"""<div style="text-align: center; padding: 20px;"><h1 style="color: #2563EB; margin-bottom: 10px;">👋 Welkom bij de Academy, {welcome_name}!</h1><p style="font-size: 1.1rem; color: #64748B;">Laten we je profiel instellen voor maximaal succes.</p></div>""", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            shop_name = st.text_input("Hoe gaat je webshop heten?", placeholder="Bijv. Nova Gadgets")
            goal = st.selectbox("Wat is je eerste maandelijkse doel?", ["€1.000 /maand (Sidehustle)", "€5.000 /maand (Serieus)", "€10.000+ /maand (Fulltime)"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 Start Mijn Avontuur (+10 XP)", type="primary", use_container_width=True):
                if shop_name:
                    # 1. OPSLAAN IN DATABASE
                    # Tip: Zorg dat in Supabase de kolommen 'shop_name' (text) en 'income_goal' (text) bestaan in de 'users' tabel!
                    db.update_onboarding_data(user['email'], shop_name, goal)
                    
                    # 2. Update XP in Database
                    new_xp = user['xp'] + 10
                    if auth.supabase:
                        auth.supabase.table('users').update({"xp": new_xp}).eq('email', user['email']).execute()
                    
                    # 3. Markeer stap als voltooid
                    auth.mark_step_complete("onboarding_done", 0) 
                    
                    # 4. Update Sessie Status
                    st.session_state.shop_name = shop_name 
                    st.session_state.income_goal = goal
                    st.session_state.wizard_complete = True
                    st.session_state.user['xp'] = new_xp
                    
                    # 5. Feest & Reload
                    st.balloons()
                    st.cache_data.clear() 
                    time.sleep(1)
                    st.rerun()
                else: 
                    st.warning("Vul een naam in!")
    
    # Stop de rest van de app zolang de wizard er is
    st.stop()

if pg == "Dashboard":
    if user['level'] > st.session_state.prev_level:
        st.balloons()
        st.markdown(f"""<div class="levelup-overlay" onclick="this.style.display='none'"><div class="levelup-card"><div style="font-size:60px; margin-bottom:10px;">🏆</div><h1 style="color:#F59E0B !important; margin:0;">Level Up!</h1><h3 style="color:#0F172A;">Gefeliciteerd, je bent nu Level {user['level']}!</h3><p style="color:#64748B; margin:15px 0 25px 0;">Je hebt nieuwe features vrijgespeeld. Ga zo door!</p><div style="background:#2563EB; color:white; padding:12px 30px; border-radius:50px; cursor:pointer; font-weight:bold; display:inline-block;">Doorgaan 🚀</div></div></div>""", unsafe_allow_html=True)
        st.session_state.prev_level = user['level']

    # GHOST DATA (STABIEL)
    def get_community_stats():
        # We gebruiken de datum + het uur als 'zaadje'. 
        # Hierdoor veranderen de cijfers pas als het uur voorbij is.
        # Dit zorgt voor totale rust bij de gebruiker (geen flikkerende cijfers bij refresh).
        now = datetime.now()
        seed = int(now.strftime("%Y%m%d%H")) # Bv: 2023121914 (14u)
        
        # Gebruik een geisoleerde random generator
        rng = random.Random(seed)
        
        u_online = rng.randint(120, 185)
        u_sales = rng.randint(15, 42)
        return u_online, u_sales

    live_users, sales_today = get_community_stats()
    
    st.markdown(f"""<div style="display: flex; gap: 15px; margin-bottom: 10px; flex-wrap: wrap;"><div style="background: #F0FDF4; border: 1px solid #BBF7D0; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; color: #15803D; font-weight: 600; display: flex; align-items: center; gap: 6px;"><span style="height: 8px; width: 8px; background-color: #22C55E; border-radius: 50%; display: inline-block;"></span>{live_users} studenten online</div><div style="background: #FFF7ED; border: 1px solid #FED7AA; padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; color: #9A3412; font-weight: 600; display: flex; align-items: center; gap: 6px;">🔥 {sales_today} studenten haalden vandaag hun eerste sale</div></div>""", unsafe_allow_html=True)

    if "force_completed" not in st.session_state: st.session_state.force_completed = []
    @st.cache_data(ttl=60, show_spinner=False)
    def get_cached_progress_db(uid): return auth.get_progress()
    db_progress = get_cached_progress_db(user['id'])
    completed_steps = list(set(db_progress + st.session_state.force_completed))
    full_map = roadmap.get_roadmap()
    total_steps_count = sum(len(f['steps']) for f in full_map.values())
    done_count = len(completed_steps)
    progress_pct = int((done_count / total_steps_count) * 100) if total_steps_count > 0 else 0
    next_step_title, next_step_phase_index, next_step_id, next_step_locked, next_step_desc = "Alles afgerond! 🎉", 0, None, False, "Geniet van je succes."
    for idx, (fase_key, fase) in enumerate(full_map.items()):
        phase_done = True
        for s in fase['steps']:
            if s['id'] not in completed_steps:
                next_step_title, next_step_desc, next_step_phase_index, next_step_id, next_step_locked = s['title'], s.get('teaser', 'Voltooi deze stap.'), idx + 1, s['id'], s.get('locked', False)
                phase_done = False
                break
        if not phase_done: break
        if phase_done and idx == len(list(full_map.keys())) - 1: next_step_phase_index = 6 

    name = user.get('first_name') or user['email'].split('@')[0].capitalize()
    
    ug = user_extra.get('income_goal') if user_extra else st.session_state.get('income_goal', '€15k/maand')
    us = user_extra.get('shop_name') if user_extra else st.session_state.get('shop_name', None)
    
    c_head, c_prog = st.columns([2, 1], vertical_alignment="bottom")
    with c_head:
        st.markdown(f"<h1 style='margin-bottom: 5px;'>Goedemorgen, {name} 👋</h1>", unsafe_allow_html=True)
        if is_temp_pro and time_left_str:
            st.markdown(f"<span style='background:#DCFCE7; color:#166534; padding:2px 8px; border-radius:4px; font-size:0.8rem; font-weight:600; border:1px solid #BBF7D0;'>⚡ PRO ACTIEF: Nog {time_left_str}</span>", unsafe_allow_html=True)
        else:
            if us: st.caption(f"🚀 {us.title()}: **{ug}** | 📈 Voortgang: **{progress_pct}%**")
            else: st.caption(f"🚀 Jouw Doel: **{ug}** | 📈 Voortgang: **{progress_pct}%**")
    with c_prog: st.progress(progress_pct / 100)
    
    # --- NIEUW: DAILY HABIT / FOCUS ---
    daily_id = f"daily_habit_{datetime.now().strftime('%Y%m%d')}"
    is_daily_done = daily_id in completed_steps

    st.markdown("### 📅 Jouw Daily Focus")
    with st.container(border=True):
        if not is_daily_done:
            c1, c2 = st.columns([3, 1], vertical_alignment="center")
            c1.markdown("**Heb je vandaag minstens 15 minuten aan je shop gewerkt?**\n\nConsistentie is de sleutel tot succes.")
            if c2.button("✅ Ja, Claim XP", type="primary", use_container_width=True):
                auth.mark_step_complete(daily_id, 10)
                if "force_completed" not in st.session_state: st.session_state.force_completed = []
                st.session_state.force_completed.append(daily_id)
                st.balloons()
                st.rerun()
        else:
            st.success("Lekker bezig! Je hebt je daily habit voor vandaag gehaald. 🔥")

    html_steps = ""
    labels = ["Start", "Bouwen", "Product", "Verkoop", "Schalen", "Beheer"] 
    for i in range(1, 7):
        status_class = "completed" if i < next_step_phase_index else "active" if i == next_step_phase_index else ""
        icon_content = f'<i class="bi bi-check-lg"></i>' if status_class == "completed" else f"{i}"
        html_steps += f'<div class="progress-step {status_class}">{icon_content}<div class="progress-label">{labels[i-1]}</div></div>'
    st.markdown(f'<div class="progress-container"><div class="progress-line"></div>{html_steps}</div>', unsafe_allow_html=True)
    
    is_step_pro = next_step_locked and not is_pro
    if is_step_pro: card_bg, accent_color, btn_text, btn_bg, btn_url, btn_target, card_icon, status_text, title_color, card_border = "linear-gradient(135deg, #0F172A 0%, #1E293B 100%)", "#F59E0B", "🚀 Word Student", "linear-gradient(to bottom, #FBBF24, #D97706)", STRATEGY_CALL_URL, "_blank", "bi-lock-fill", "Deze stap is exclusief voor studenten.", "#FFFFFF", "1px solid #F59E0B"
    else: card_bg, accent_color, btn_text, btn_bg, btn_url, btn_target, card_icon, status_text, title_color, card_border = "linear-gradient(135deg, #2563EB 0%, #1E40AF 100%)", "#DBEAFE", "🚀 Start Opdracht", "#FBBF24", "#roadmap_start", "_self", "bi-crosshair", next_step_desc, "#FFFFFF", "1px solid rgba(255,255,255,0.1)"
    st.markdown(f"""<div style="background: {card_bg}; padding: 24px; border-radius: 16px; color: white; margin-bottom: 20px; box-shadow: 0 10px 30px -5px rgba(0,0,0,0.4); border: {card_border}; position: relative; overflow: hidden;"><div style="position: relative; z-index: 2;"><div style="display:flex; justify-content:space-between; align-items:start;"><div><div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.9; margin-bottom: 8px; font-weight: 700; color: {accent_color};"><i class="bi {card_icon}"></i> AANBEVOLEN FOCUS</div><div style="margin: 0; font-size: 1.6rem; color: {title_color} !important; font-weight: 800; letter-spacing: -0.5px; line-height: 1.2; text-shadow: 0 2px 4px rgba(0,0,0,0.3); margin-bottom: 8px;">{next_step_title}</div><p style="margin: 8px 0 20px 0; font-size:0.95rem; opacity:0.9; max-width: 500px; line-height: 1.5; color: #F1F5F9;">{status_text}</p></div></div><a href="{btn_url}" target="{btn_target}" style="text-decoration:none;"><div style="display: inline-block; background: {btn_bg}; color: #78350F; padding: 12px 32px; border-radius: 8px; font-weight: 800; font-size: 1rem; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: transform 0.1s; border: 1px solid rgba(255,255,255,0.2);">{btn_text}</div></a></div></div>""", unsafe_allow_html=True)
    
    needed = next_xp_goal_sidebar - user['xp']
    next_reward = "Spy tool" if user['level'] < 2 else "Video scripts"
    st.markdown(f"""<div class="stat-grid"><div class="stat-card"><div class="stat-icon"><i class="bi bi-bar-chart-fill"></i> Level</div><div class="stat-value">{user['level']}</div><div class="stat-sub">{rank_title}</div></div><div class="stat-card"><div class="stat-icon"><i class="bi bi-lightning-fill"></i> XP</div><div class="stat-value">{user['xp']}</div><div class="stat-sub">Nog <b>{needed}</b> voor Lvl {user['level']+1}</div></div><div class="stat-card"><div class="stat-icon"><i class="bi bi-gift-fill"></i> Beloning</div><div class="stat-value" style="font-size: 1.2rem; padding-top:2px;">🎁</div><div class="stat-sub" style="color:#2563EB;">{next_reward}</div></div></div>""", unsafe_allow_html=True)
    
    st.markdown("<div id='roadmap_start' style='height: 0px;'></div>", unsafe_allow_html=True)
    st.markdown("### 📍 Jouw Roadmap")
    st.caption("Klik op een fase om je taken te bekijken.")
    
    active_phase_idx = next_step_phase_index 
    for idx, (fase_key, fase) in enumerate(full_map.items()):
        phase_num = idx + 1
        is_current_phase = (phase_num == active_phase_idx)
        if phase_num < active_phase_idx: phase_icon, phase_label = "✅", f"{fase['title']} (Voltooid)"
        elif phase_num == active_phase_idx: phase_icon, phase_label = "📍", f"{fase['title']} (Nu Actief)" 
        else: phase_icon, phase_label = "📂", fase['title']
            
        with st.expander(f"{phase_icon} {phase_label}", expanded=is_current_phase):
            st.caption(fase['desc'])
            for step in fase['steps']:
                is_done = step['id'] in completed_steps
                if is_done:
                    with st.expander(f"✅ {step['title']}", expanded=False): st.info("Deze stap heb je al afgerond. Goed bezig!")
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
    # --- CSS VOOR PREMIUM LOOK ---
    st.markdown("""
    <style>
        /* Premium Card Styling */
        .premium-card {
            background: white;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s;
        }
        .premium-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        
        /* Locked Module Styling */
        .locked-module {
            background: #F8FAFC;
            border: 1px dashed #CBD5E1;
            border-radius: 8px;
            padding: 12px 15px;
            margin-bottom: 8px;
            color: #94A3B8;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.9rem;
        }
        
        /* Navigatie Knoppen Links (Premium) */
        div.stButton > button[kind="secondary"] {
            border: 1px solid #E2E8F0 !important;
            background: white !important;
            color: #475569 !important;
            justify-content: flex-start !important;
            padding-left: 15px !important;
            text-align: left !important;
        }
        div.stButton > button[kind="secondary"]:hover {
            border-color: #2563EB !important;
            color: #2563EB !important;
            background: #EFF6FF !important;
        }
        div.stButton > button[kind="primary"] {
            background: #2563EB !important;
            border: 1px solid #2563EB !important;
            justify-content: flex-start !important;
            padding-left: 15px !important;
            font-weight: 600 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1><i class='bi bi-mortarboard-fill'></i> Academy</h1>", unsafe_allow_html=True)
    
    # We maken twee tabs: eentje voor de gratis content, eentje voor de betaalde
    tab_free, tab_pro_course = st.tabs(["🎁 Gratis Mini Training", "🎓 Volledige Cursus (70+ Video's)"])

    # =========================================================
    # --- TAB 1: GRATIS MINI TRAINING (HIGH FOMO EDITIE) ---
    # =========================================================
    with tab_free:
        # 1. Status Balk
        st.markdown("""
        <div style="background: #EFF6FF; border: 1px solid #DBEAFE; border-radius: 8px; padding: 10px 15px; display: flex; align-items: center; gap: 10px; margin-bottom: 20px; color: #1E3A8A; font-size: 0.9rem;">
            <i class="bi bi-info-circle-fill"></i>
            <span>Je hebt <b>Preview Toegang</b>: 4 van de 74 lessen zijn beschikbaar.</span>
            <span style="margin-left: auto; background: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.75rem; border: 1px solid #BFDBFE;">GAST ACCOUNT</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 👋 Start hier met je gratis lessen")
        
        # 2. De 4 Gratis Video's (In een strak grid)
        c1, c2 = st.columns(2)
        
        with c1:
            with st.container(border=True):
                st.markdown("**1. Van Chaos naar Actie 🚀**")
                st.video("https://www.youtube.com/embed/nYN7EyMb7uQ")
                st.caption("Start Jouw Ondernemersreis Vandaag!")
            
            with st.container(border=True):
                st.markdown("**3. Kies het juiste product 📦**")
                st.video("https://www.youtube.com/embed/CM5CtnXrvEU")
                st.caption("Hoe vind je een winner?")

        with c2:
            with st.container(border=True):
                st.markdown("**2. Jouw volgende stap 📈**")
                st.video("https://www.youtube.com/embed/yIJJbwIZL6k")
                st.caption("Ontdek hoe e-commerce echt werkt.")
            
            with st.container(border=True):
                st.markdown("**4. Je eerste advertentie 🔥**")
                st.video("https://www.youtube.com/embed/cA8Gvhfic-s")
                st.caption("Breng je product tot leven.")

        # 3. HET IJSBERG EFFECT (De locked content laten zien)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🔒 Wat je mist in de volledige cursus:")
        st.caption("Studenten hebben toegang tot al deze modules, templates en scripts.")

        # Een lijst van "Locked" modules om FOMO te kweken
        locked_modules = [
            "Module 2: Het Begin (KvK, Bank, Mindset)",
            "Module 3: Dropshipping & Branding Strategie",
            "Module 4: De Fundering & Niche Keuze",
            "Module 5: Shopify Masterclass (15 lessen)",
            "Module 6: Conversie Apps & Hacks",
            "Module 7: Facebook Ads Setup (Van A tot Z)",
            "Module 8: Facebook Live Gaan & Testen",
            "Module 9: Opschalen (Geavanceerd)",
            "Module 10: Branding & Logo Design",
            "Module 11: Private Agents & Snelle Levering",
            "Module 12: Viral Content Creatie (TikTok)",
            "Module 13: Klantenservice Automatisering",
            "Module 14: Must Have Tools & AI"
        ]

        # Toon de lijst in 2 kolommen
        lc1, lc2 = st.columns(2)
        for i, mod in enumerate(locked_modules):
            # HTML voor een 'locked' kaartje
            html = f"""
            <div class="locked-module">
                <span><i class="bi bi-collection-play" style="margin-right:8px;"></i> {mod}</span>
                <i class="bi bi-lock-fill" style="color:#CBD5E1;"></i>
            </div>
            """
            if i % 2 == 0:
                lc1.markdown(html, unsafe_allow_html=True)
            else:
                lc2.markdown(html, unsafe_allow_html=True)
        
        # 4. De FOMO Knal Actie
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%); padding: 30px; border-radius: 16px; border: 2px solid #F97316; text-align: center; box-shadow: 0 10px 30px -10px rgba(249, 115, 22, 0.3);">
            <div style="font-size: 2rem; margin-bottom: 10px;">🚀</div>
            <h3 style="color:#9A3412; margin:0 0 10px 0; font-weight: 800; font-size: 1.3rem;">Klaar met de basis? Tijd voor het echte werk.</h3>
            <p style="color:#7C2D12; font-size:0.95rem; line-height: 1.6; margin-bottom: 25px; max-width: 600px; margin-left: auto; margin-right: auto;">
                Je hebt nu <b>5%</b> gezien. Wil je toegang tot de overige <b>95%</b>, inclusief de copy-paste templates, de winnende product strategieën en de 1-op-1 community?<br><br>
                <b>Claim je plek in de Academy en start vandaag nog.</b>
            </p>
            <a href="https://calendly.com/rmecomacademy/30min" target="_blank" style="text-decoration:none;">
                <div style="background: #EA580C; color: white; padding: 12px 30px; border-radius: 50px; font-weight: bold; display: inline-block; box-shadow: 0 4px 15px rgba(234, 88, 12, 0.4);">
                    📞 Plan Gratis Strategie Call & Unlock Alles
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)


    # =========================================================
    # --- TAB 2: DE ECHTE CURSUS (Premium Dashboard) ---
    # =========================================================
    with tab_pro_course:
        
        # CONFIGURATIE VAN JE CURSUS
        course_content = {
            "Module 1: Welkom": [
                {"title": "Introductie - Welkom bij RM Ecom Academy", "url": "https://youtu.be/N7sftaU3T_E", "duration": "5 min"},
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

        if not is_pro:
            st.write("")
            render_pro_lock("Unlock de Volledige Cursus", "Krijg direct toegang tot 70+ video's.", "Stop met zelf prutsen.")
        else:
            # --- LAYOUT: 1/3 Navigatie, 2/3 Video ---
            col_nav, col_content = st.columns([1, 2.2], gap="large")
            
            with col_nav:
                st.markdown("#### 📂 Modules")
                
                # MODULE KIEZER (Strak)
                module_names = list(course_content.keys())
                if "curr_module" not in st.session_state: st.session_state.curr_module = module_names[0]
                
                try: idx = module_names.index(st.session_state.curr_module)
                except: idx = 0
                
                selected_module = st.selectbox("Kies module:", module_names, index=idx, label_visibility="collapsed")
                st.session_state.curr_module = selected_module

                st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:0.75rem; color:#94A3B8; margin-bottom:8px; text-transform:uppercase; font-weight:700; letter-spacing:1px;'>Lessen in deze module</div>", unsafe_allow_html=True)
                
                # VIDEO LIJST (MET PREMIUM KNOPPEN)
                videos_in_module = course_content[selected_module]
                
                # Initialize selected video if needed
                if "curr_video" not in st.session_state: 
                    st.session_state.curr_video = videos_in_module[0]['title']
                
                # Zorg dat de geselecteerde video ook in deze module bestaat (anders reset naar 1e)
                vid_titles = [v['title'] for v in videos_in_module]
                if st.session_state.curr_video not in vid_titles:
                    st.session_state.curr_video = vid_titles[0]

                # Render de lijst als knoppen
                for v in videos_in_module:
                    title = v['title']
                    is_active = (title == st.session_state.curr_video)
                    
                    # Check status (Vinkje)
                    vid_hash = f"vid_{abs(hash(title))}"
                    is_done = vid_hash in completed_steps
                    
                    # Icon logica
                    if is_done: icon = "✅" 
                    elif is_active: icon = "▶️"
                    else: icon = "📺"
                    
                    # Style: Primary = Blauw (Actief), Secondary = Wit/Grijs (Inactief)
                    btn_type = "primary" if is_active else "secondary"
                    
                    # De knop zelf (Full Width)
                    if st.button(f"{icon}  {title}", key=f"nav_btn_{vid_hash}", type=btn_type, use_container_width=True):
                        st.session_state.curr_video = title
                        st.rerun()

            # Zoek data van de geselecteerde video
            current_video = next((v for v in videos_in_module if v['title'] == st.session_state.curr_video), None)

            with col_content:
                if current_video:
                    # --- DE VIDEO KAART (WIT & STRAK) ---
                    
                    # 1. Titel Header (Premium HTML)
                    st.markdown(f"""
                    <div style="border-bottom: 1px solid #E2E8F0; padding-bottom: 10px; margin-bottom: 15px;">
                        <h2 style="margin:0; font-size:1.6rem; color:#0F172A; letter-spacing:-0.5px; line-height:1.2;">{current_video['title']}</h2>
                        <div style="color:#64748B; font-size:0.85rem; margin-top:6px; font-weight:500;">
                            <span style="background:#F1F5F9; padding:2px 8px; border-radius:4px;">{selected_module}</span> 
                            &nbsp;•&nbsp; <i class="bi bi-clock"></i> {current_video['duration']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 2. Content (Video of Tekst)
                    if current_video['title'] == "Opzetten van je agency advertentieaccount":
                        st.info("ℹ️ Voor deze stap is geen video nodig. Volg de instructies hieronder.")
                        with st.container(border=True):
                            st.markdown("""
                            ### Hoe maak ik een agency advertentieaccount aan?

                            Wanneer je via je eigen privé Facebook-account advertenties draait, loop je sneller risico dat je account wordt beperkt of zelfs geblokkeerd. Daarom raden wij altijd aan om te werken via een **agency advertentieaccount**.

                            Bij NOVA Agency regelen wij dit eenvoudig voor je:

                            **1. Stuur NOVA Agency een bericht**
                            Stuur een bericht via WhatsApp: **06-27210591** (NOVA Agency / NL).
                            Laat weten dat je een agency account wilt aanvragen, geef hun RM Ecom Academy door als ze hiernaar zouden vragen.

                            **2. Vul het aanvraagformulier in**
                            [Klik hier voor het formulier](https://docs.google.com/forms/d/10VwwoOXOQqhAaFUvFFwwohGxofmzpPxk7YsXasJLSs/viewform?edit_requested=true)
                            Dit is een kort formulier waarin we de benodigde gegevens verzamelen (zoals je bedrijfsnaam, e-mailadres en website).

                            **3. Betaal de setup fee**
                            Eenmalig €250. Na betaling gaan wij direct voor je aan de slag.

                            **4. Wij maken jouw account aan**
                            Dit account is gekoppeld via ons agency-netwerk. Hierdoor profiteer je van:
                            *   ✅ Minder kans op blokkades of beperkingen
                            *   ✅ Sneller opschalen en campagnes live zetten
                            *   ✅ Betere stabiliteit voor je advertenties

                            **5. Je krijgt toegang**
                            Je behoudt volledige inzage en wij zorgen dat alles technisch juist staat ingesteld.

                            👉 *Met een agency account ben je dus altijd verzekerd van meer stabiliteit, minder risico en sneller resultaat.*
                            """)
                    elif current_video['title'] == "Klantenservice templates":
                         st.info("ℹ️ Handige standaardteksten om te kopiëren en plakken.")
                         with st.container(border=True):
                             st.markdown("""
                             In deze les richten we ons op klantenservice templates voor een webshop. Templates zijn standaardteksten die je snel kunt gebruiken of aanpassen bij verschillende klantvragen. Het doel is om consistentie, snelheid en professionaliteit te waarborgen in alle klantcommunicatie.

                             ### Wat is een template?
                             *   Een template is een voorgeschreven bericht met vaste onderdelen en invulvelden.
                             *   **Voordelen:**
                                 *   Snelheid: reageer sneller op veelvoorkomende vragen.
                                 *   Consistentie: dezelfde toon en informatie bij elke interactie.
                                 *   Foutreductie: minimaal kans op missende informatie.
                                 *   Eenvoudige personalisatie: ruimte voor klantnaam en specifieke gegevens.

                             ### Kernonderwerpen waarvoor templates handig zijn
                             *   Orderbevestiging: bevestiging van aankoop, samenvatting van bestelling, betalingsstatus en contactinformatie.
                             *   Buiten levertermijn: duidelijke uitleg waarom de levering niet op tijd is, verwachte nieuwe leverdatum, compensatie of opties.
                             *   Verzendkosten: transparante kosten, free shipping drempels, waar nodig kostenverdeling.
                             *   Track en trace: link naar zending, statusupdates, verwachte levertijd.
                             *   Productvragen: specificaties, compatibiliteit, gebruiksaanwijzingen, garantie en retourbeleid.

                             ### Structuur van een goede klantenservice template
                             1.  **Openingsgroet:** Personaliseer waar mogelijk: "Beste [Naam]," Bedank voor de aankoop: "Bedankt voor je bestelling bij [Winkelnaam]."
                             2.  **Kerninformatie:** Duidelijke samenvatting van de vraag of situatie. Relevante feiten: bestelnummer, orderdatum, productnaam, gewenste datum, etc. Concrete oplossing of antwoord.
                             3.  **Actiepunten en vervolgstappen:** Wat de klant moet doen (indien van toepassing). Volgende stappen vanuit de klantenservice. Verwachte reactie tijd: bijvoorbeeld "Wij reageren binnen 24 uur."
                             4.  **Afsluiting:** Uitnodiging tot verdere vragen. Alternatieve contactkanalen. Vriendelijke afsluiting met naam van de klantenadviseur.

                             ### Voorbeelden per onderwerp

                             **1) Orderbevestiging**
                             *   **Onderwerp:** Bevestiging van je bestelling bij [Winkelnaam]
                             *   **Tekst:**
                                 *   Bedankt voor je aankoop! Je bestelling [ordernummer] is ontvangen en wordt verwerkt.
                                 *   Samenvatting: [aantal] x [productnaam], totaalbedrag [bedrag], verwachte verzenddatum [datum].
                                 *   Betalingsstatus: [betaald/onder voorbehoud].
                                 *   Contactgegevens: [klantenservice-mail/telefoon].
                                 *   Sluiting: Wij houden je op de hoogte via e-mail van elke statusupdate.

                             **2) Buiten levertermijn**
                             *   **Onderwerp:** Update levering - [Bestelnummer]
                             *   **Tekst:**
                                 *   Onze excuses, levering verloopt niet volgens planning wegens [reden].
                                 *   Nieuwe verwachte leverdatum: [datum].
                                 *   Mogelijke opties: vervanging, retour of terugbetaling.
                                 *   Neem gerust contact op bij vragen.

                             **3) Verzendkosten**
                             *   **Onderwerp:** Verzendkosten voor je bestelling bij [Winkelnaam]
                             *   **Tekst:**
                                 *   Bestaande verzendkosten: [kosten].
                                 *   Gratis verzenden bij besteding vanaf [bedrag].
                                 *   Interessante tip: combineer producten voor verzending zonder extra kosten.

                             **4) Track en trace**
                             *   **Onderwerp:** Track en trace voor bestelling [ordernummer]
                             *   **Tekst:**
                                 *   Je zending is meegestuurd. Volg de status via deze link: [track link].
                                 *   Geschatte bezorgtijd: [tijd].
                                 *   Contact bij vragen: [klantenservice].

                             **5) Productvragen**
                             *   **Onderwerp:** Vraag over [productnaam] - informatie en gebruik
                             *   **Tekst:**
                                 *   Specificaties: [belangrijkste specs].
                                 *   Compatibiliteit/gebruik: [toelichting].
                                 *   Garantie en retourbeleid: [voorwaarden].
                                 *   Vragen? Antwoord zo nodig met aanvullende details.

                             ### Tonaliteit en stijladvies
                             *   Gebruik een vriendelijke, professionele en helpende toon.
                             *   Wees duidelijk en beknopt; vermijd vakjargon of onduidelijke termen.
                             *   Pas de template aan op de klant en situatie (persoonlijk: naam, ordernummer).
                             *   Houd consistentie in terminologie en structuur.

                             ### Praktische oefeningen
                             *   **Oefening A:** Pas een generieke template aan voor een klant die buiten levertermijn contact opneemt. Voeg relevante details toe.
                             *   **Oefening B:** Schrijf een track & trace bericht voor een zending met vertraging, inclusief proposeer een oplossing.
                             *   **Oefening C:** Maak een korte productvragen-template voor een veel verkocht item met drie belangrijkste specificaties.

                             ### Real-world toepassingen
                             *   Gebruik templates in reply-functies van je klantenservice-systeem, chat en e-mail.
                             *   Integreer met orderbeheersystemen zodat gegevens automatisch kunnen invullen (ordernummer, naam, product).
                             *   Raadpleeg een kennisbank of FAQ en link naar relevante artikelen in de template.

                             ### Open invulvelden voor jouw lesmateriaal
                             *   [Bedrijfsnaam]
                             *   [Klantnaam]
                             *   [Ordernummer]
                             *   [Datum]
                             *   [Productnaam]
                             *   [Bedrag]
                             *   [Track link]
                             *   [Reden uitlooptijd]
                             *   [Nieuwe leverdatum]

                             ### Samenvattend
                             Templates helpen je webshop-klanten snel, consistent en professioneel te antwoorden. Gebruik de bovenstaande sjablonen als basis en pas ze aan per situatie en klant. Pas het lesmateriaal verder aan met jouw eigen bedrijfsinformatie en veelgestelde vragen.

                             *Download hierboven kant en klare templates voor de klantenservice EN het retourproces.*
                             """)
                    else:
                        st.video(current_video['url'])
                    
                    # 3. Actie Balk (Strak & Compact)
                    vid_id = f"vid_{abs(hash(current_video['title']))}"
                    is_done = vid_id in completed_steps
                    curr_idx = vid_titles.index(current_video['title'])
                    has_next = curr_idx < len(vid_titles) - 1
                    
                    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
                    
                    # Kolommen voor knoppen
                    c_done, c_next = st.columns([1, 1.3])
                    
                    with c_done:
                        if not is_done:
                            # Knop: Afronden
                            if st.button("✅ Les Afronden (+15 XP)", key=f"btn_finish_{vid_id}", type="primary", use_container_width=True):
                                auth.mark_step_complete(vid_id, 15)
                                if "force_completed" not in st.session_state: st.session_state.force_completed = []
                                st.session_state.force_completed.append(vid_id)
                                st.balloons()
                                time.sleep(0.5)
                                st.rerun()
                        else:
                            # Statische tekst als het al klaar is
                            st.markdown("""
                            <div style="background:#F0FDF4; border:1px solid #BBF7D0; color:#166534; padding:8px; border-radius:8px; text-align:center; font-weight:600; font-size:0.9rem;">
                                <i class="bi bi-check-circle-fill"></i> Voltooid
                            </div>
                            """, unsafe_allow_html=True)

                    with c_next:
                        if has_next:
                            next_vid_name = vid_titles[curr_idx+1]
                            # Visuele hint voor volgende
                            st.markdown(f"""
                            <div style="text-align:right; font-size:0.8rem; color:#64748B; line-height:1.2; padding-top:5px;">
                                Volgende: <b style="color:#0F172A;">{next_vid_name[:25]}...</b> 👉
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("<div style='text-align:right; color:#94A3B8; font-size:0.8rem; padding-top:5px;'>🏁 Module compleet</div>", unsafe_allow_html=True)

                else:
                    st.error("Selecteer een video.")

elif pg == "Financiën":
    st.markdown("<h1><i class='bi bi-cash-stack'></i> Financiën</h1>", unsafe_allow_html=True)
    # TABS: Winst Berekenen EERST (Tab 1), want dat is de 'Tool' voor TikTok
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
            vp = c1.number_input("Verkoopprijs (€)", value=29.95, step=1.0)
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

elif pg == "Marketing & Design": 
    st.markdown("<h1><i class='bi bi-palette-fill'></i> Marketing & Design</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["Logo Maker", "Video Scripts", "Teksten Schrijven", "Advertentie Check"])
    
    with tab1:
        st.markdown("**ℹ️ Wat doet deze tool?**\n\nMaak binnen 10 seconden een uniek logo voor je merk. Typ je naam in en kies een stijl.")
        
        # --- INIT SESSION STATE VOOR LOGOS ---
        if "logo_generations" not in st.session_state: st.session_state.logo_generations = 0
        if "generated_logos" not in st.session_state: st.session_state.generated_logos = [] # Hier slaan we ze op
        
        # Check toegang
        has_access = is_pro or st.session_state.logo_generations < 3
        
        if not has_access: 
            render_pro_lock("Credits op", "Je hebt 3 gratis logo's gemaakt. Word student om onbeperkt te genereren.", "Concurrenten betalen €200 voor een logo. Jij krijgt dit gratis.")
        else:
            if not is_pro: 
                st.info(f"🎁 Je hebt nog **{3 - st.session_state.logo_generations}** gratis logo generaties over.")
            
            with st.container(border=True):
                col1, col2 = st.columns(2)
                brand_name = col1.text_input("Bedrijfsnaam", placeholder="Bijv. Lumina")
                niche = col1.text_input("Niche", placeholder="Bijv. Online growth, speed")
                style = col2.selectbox("Stijl", ["Minimalistisch", "Modern & strak", "Vintage", "Luxe", "Speels"])
                color = col2.text_input("Voorkeurskleuren", placeholder="Bijv. Zwart en goud")
                
                # GENEREER KNOP
                if st.button("Genereer logo's", type="primary", use_container_width=True):
                    if not brand_name or not niche: 
                        st.warning("Vul alles in.")
                    else:
                        st.session_state.logo_generations += 1
                        with st.spinner("Onze designers zijn bezig... (Dit duurt ca. 10 sec)"):
                            import requests
                            
                            # Tijdelijke lijst om resultaten op te vangen
                            new_logos = []
                            
                            for i in range(3):
                                img_url = ai_coach.generate_logo(brand_name, niche, style, color)
                                if img_url and "placehold" not in img_url:
                                    # We downloaden de data NU al, zodat de downloadknop direct werkt en blijft werken
                                    try:
                                        resp = requests.get(img_url)
                                        if resp.status_code == 200:
                                            new_logos.append({
                                                "url": img_url,
                                                "data": resp.content,
                                                "name": f"logo_{brand_name}_{i+1}.png"
                                            })
                                    except: pass
                            
                            # Sla op in sessie state (Het Geheugen)
                            if new_logos:
                                st.session_state.generated_logos = new_logos
                            else:
                                st.error("Er ging iets mis bij het genereren. Probeer het opnieuw.")

            # --- WEERGAVE (Buiten de knop, zodat het blijft staan) ---
            if st.session_state.generated_logos:
                st.markdown("---")
                st.markdown("### 🎉 Jouw resultaten:")
                st.success("Tip: Klik op de knop onder het logo om hem in hoge kwaliteit op te slaan.")
                
                cols = st.columns(3)
                for idx, logo in enumerate(st.session_state.generated_logos):
                    with cols[idx]:
                        # 1. Toon plaatje
                        st.image(logo["url"], use_container_width=True)
                        
                        # 2. Download knop (gebruikt opgeslagen data)
                        st.download_button(
                            label="📥 Download Logo",
                            data=logo["data"],
                            file_name=logo["name"],
                            mime="image/png",
                            key=f"dl_btn_persistent_{idx}",
                            use_container_width=True
                        )
                
                # Knop om te wissen
                if st.button("Opnieuw beginnen (Wist huidige logo's)", type="secondary"):
                    st.session_state.generated_logos = []
                    st.rerun()

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
                uploaded_file = st.file_uploader("Bestand", type=['png', 'jpg', 'jpeg'])
                if uploaded_file and st.button("Diagnose starten", type="primary"):
                    with st.spinner("AI analyseert je advertentie..."):
                         # We roepen de nieuwe Vision functie aan
                         advies = ai_coach.analyze_ad_screenshot(uploaded_file)
                         st.markdown("### 🔍 Analyse Resultaat")
                         st.write(advies)
                         st.success("Pas deze tips toe om je ROAS te verhogen!")

        else: render_pro_lock("Ads check", "Laat je advertenties beoordelen.", "Gooi geen geld weg aan slechte ads. Laat AI ze checken.")

elif pg == "Producten Zoeken":
    # --- HEADER ---
    st.markdown("<h1><i class='bi bi-search'></i> Winning Product Hunter</h1>", unsafe_allow_html=True)
    st.caption("De ultieme toolkit om winstgevende producten te vinden via TikTok en Facebook.")

    tab1, tab2, tab3 = st.tabs(["🔥 Viral TikTok Hunter", "🧿 Meta Ad Spy (Facebook)", "🕵️ Concurrenten Spy"]) 
    
# =========================================================
    # --- TAB 1: VIRAL TIKTOK HUNTER (PRO UPGRADE) ---
    # =========================================================
    with tab1:
        st.markdown("""
        <div style="background:#F8FAFC; border-left: 4px solid #2563EB; padding: 15px; border-radius: 4px; margin-bottom: 20px;">
            <h4 style="margin:0; color:#1E293B;">🌪️ The Viral Hunter</h4>
            <p style="margin:0; color:#64748B; font-size:0.9rem;">
                Vind producten die <b>nu</b> viraal gaan. Klik op een niche of typ zelf.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if not is_pro:
             render_pro_lock("Viral Hunter 🔒", "Vind producten die NU viraal gaan.", "Krijg toegang tot de real-time scanner.")
        else:
            with st.container(border=True):
                # --- UPGRADE 1: NICHE SNELKNOPPEN ---
                st.write("**Kies een winnende niche:**")
                # We gebruiken kolommen als 'knoppenbalk'
                b1, b2, b3, b4, b5, b6 = st.columns(6)
                
                # State management voor de knoppen
                if "search_query" not in st.session_state: st.session_state.search_query = "tiktokmademebuyit"
                
                if b1.button("🏠 Home", use_container_width=True): st.session_state.search_query = "kitchenhacks"
                if b2.button("🐶 Pets", use_container_width=True): st.session_state.search_query = "dogmusthaves"
                if b3.button("💄 Beauty", use_container_width=True): st.session_state.search_query = "beautytips"
                if b4.button("🚗 Auto", use_container_width=True): st.session_state.search_query = "caraccessories"
                if b5.button("🏋️ Sport", use_container_width=True): st.session_state.search_query = "gymgadgets"
                if b6.button("👶 Baby", use_container_width=True): st.session_state.search_query = "babymusthaves"

                st.markdown("---")

                c_filter1, c_filter2, c_filter3 = st.columns([2, 1, 1])
                
                with c_filter1:
                    # Input veld luistert naar de knoppen hierboven
                    search_query = st.text_input("Of typ zelf een zoekwoord/hashtag:", value=st.session_state.search_query)
                
                with c_filter2:
                    min_views = st.selectbox("Min. Views", [10000, 100000, 500000, 1000000], index=1)
                
                with c_filter3:
                    sort_option = st.selectbox("Sorteer", ["Omzet (Geschat)", "Viral Score", "Views"])
            
            # Grote Actieknop
            if st.button(f"🚀 Zoek Winners in '{search_query}'", type="primary", use_container_width=True):
                if not search_query:
                    st.warning("Vul iets in.")
                else:
                    with st.spinner(f"🕵️‍♂️ De markt afstruinen naar '{search_query}' trends..."):
                        from modules import viral_finder
                        sort_map = {"Omzet (Geschat)": "revenue", "Viral Score": "score", "Views": "views"}
                        
                        # We halen nu iets meer op (6) voor een voller scherm
                        results = viral_finder.search_tiktok_winning_products(search_query, min_views, sort_map[sort_option])
                        st.session_state.tiktok_results = results # Opslaan in sessie

            # --- RESULTATEN WEERGAVE ---
            if st.session_state.get("tiktok_results"):
                results = st.session_state.tiktok_results
                st.success(f"🔥 {len(results)} Potentiële winners gevonden!")
                
                # Grid weergave
                for i in range(0, len(results), 2):
                    col_a, col_b = st.columns(2)
                    
                    # Hulpfunctie om kaart te tekenen
                    def render_tiktok_card(col, item):
                        with col:
                            with st.container(border=True):
                                # Video/Cover
                                if item['cover']: 
                                    st.image(item['cover'], use_container_width=True)
                                
                                # Titel & Metrics
                                st.markdown(f"**{item['desc'][:60]}...**")
                                
                                # Viral Score Badge
                                score = item.get('viral_score', 50)
                                score_color = "#16A34A" if score > 80 else "#CA8A04"
                                st.markdown(f"<span style='color:{score_color}; font-weight:bold; font-size:0.8rem;'>🔥 Viral Score: {score}/100</span>", unsafe_allow_html=True)

                                m1, m2 = st.columns(2)
                                m1.metric("Views", f"{item['views']//1000}k")
                                m2.metric("Est. Omzet", f"€{item['est_revenue']:,}")
                                
                                # --- UPGRADE 2: ACTION BUTTONS ---
                                c1, c2 = st.columns(2)
                                # Link naar TikTok
                                c1.link_button("🎵 Bekijk", item['url'], use_container_width=True)
                                
                                # Link direct naar AliExpress Search
                                # We halen hashtags weg uit de beschrijving voor een schonere zoekopdracht
                                clean_query = item['desc'].split('#')[0][:30] 
                                ali_link = f"https://www.aliexpress.com/wholesale?SearchText={urllib.parse.quote(clean_query)}"
                                c2.link_button("📦 Source", ali_link, use_container_width=True)

                                # --- UPGRADE 3: AI ANALYSE (Expander) ---
                                with st.expander("🤖 Vraag de AI Coach"):
                                    if st.button("Analyseer dit product", key=f"ai_{item['id']}"):
                                        with st.spinner("Analyseren..."):
                                            # We faken hier even een AI call voor snelheid, 
                                            # in het echt zou je 'ai_coach.analyze_product' aanroepen
                                            st.markdown(f"""
                                            **🎯 Oordeel:** 8/10
                                            **💡 Waarom:** Dit product heeft een duidelijk 'wow-effect'.
                                            **🛒 Doelgroep:** Mensen die houden van {search_query}.
                                            """)

                    if i < len(results):
                        render_tiktok_card(col_a, results[i])
                    if i + 1 < len(results):
                        render_tiktok_card(col_b, results[i+1])
            
            elif "tiktok_results" not in st.session_state:
                # Lege staat: Laat zien wat ze kunnen verwachten
                st.info("👆 Klik op een niche hierboven om te beginnen!")

# =========================================================
    # --- TAB 2: META AD SPY (MET FILTERS) ---
    # =========================================================
    with tab2:
        # CSS voor perfecte vierkante plaatjes
        st.markdown("""
        <style>
            div[data-testid="stImage"] > img {
                aspect-ratio: 1 / 1;
                width: 100% !important;
                object-fit: cover !important;
                border-radius: 12px !important;
            }
            .metric-container {
                display: flex; justify-content: space-between; 
                background: #F8FAFC; border-radius: 8px; padding: 10px; margin: 10px 0;
                border: 1px solid #E2E8F0;
            }
            .metric-item { text-align: center; width: 33%; }
            .metric-val { font-weight: 800; font-size: 1rem; color: #0F172A; }
            .metric-lbl { font-size: 0.65rem; color: #64748B; text-transform: uppercase; font-weight: 600; }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("### 🧿 Meta (Facebook) Ad Spy")
        st.write("Zie precies welke video-advertenties er **NU** draaien op Facebook & Instagram.")
        
        if is_pro:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 1, 1], vertical_alignment="bottom")
                
                with c1:
                    fb_niche = st.text_input("Zoekwoord:", placeholder="Bijv. Smart Watch", value="dames mode")
                with c2:
                    fb_country = st.selectbox("Land:", ["NL", "US", "DE", "BE", "ALL"], index=0)
                
                with c3:
                    if st.button("🕵️‍♂️ Scan Facebook", type="primary", use_container_width=True):
                        if not fb_niche:
                            st.warning("Vul een zoekwoord in.")
                        else:
                            st.session_state.fb_search_active = True
                            st.session_state.fb_query = fb_niche
                            
                            # We halen nu MAX 30 ads op (Sneller)
                            with st.spinner("30 Advertenties ophalen uit de bibliotheek..."):
                                from modules import facebook_spy
                                country_code = "ALL" if fb_country == "ALL" else fb_country
                                results = facebook_spy.search_facebook_ads(fb_niche, country=country_code, max_results=30)
                                st.session_state.fb_results = results

            # --- FILTER DASHBOARD (VERSCHIJNT NA ZOEKEN) ---
            if st.session_state.get("fb_results"):
                raw_ads = st.session_state.fb_results
                
                with st.container(border=True):
                    st.markdown("#### 🌪️ Filter & Sorteer")
                    
                    f1, f2, f3 = st.columns(3)
                    with f1:
                        sort_order = st.selectbox("Sorteer op:", ["Langst Actief (Winners)", "Nieuwste Eerst", "Willekeurig"])
                    with f2:
                        media_filter = st.selectbox("Media Type:", ["Alles", "Alleen Video's"])
                    with f3:
                        min_days = st.slider("Minimaal dagen actief:", 0, 30, 0, help="Filter op ads die al langer draaien en dus winstgevend zijn.")
                
                # 1. Pas Filters toe
                filtered_ads = raw_ads
                
                if media_filter == "Alleen Video's":
                    filtered_ads = [ad for ad in filtered_ads if ad['is_video']]
                
                filtered_ads = [ad for ad in filtered_ads if ad['days_active'] >= min_days]
                
                # 2. Pas Sortering toe
                if sort_order == "Langst Actief (Winners)":
                    filtered_ads.sort(key=lambda x: x['days_active'], reverse=True)
                elif sort_order == "Nieuwste Eerst":
                    filtered_ads.sort(key=lambda x: x['days_active'], reverse=False)
                # Willekeurig doet niks (is standaard volgorde van Facebook)

                st.success(f"✅ {len(filtered_ads)} Advertenties over (van de {len(raw_ads)} totaal)")
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Grid weergave (3 kolommen)
                for i in range(0, len(filtered_ads), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(filtered_ads):
                            ad = filtered_ads[i+j]
                            with cols[j]:
                                with st.container(border=True):
                                    # Header
                                    st.markdown(f"""
                                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
                                        <img src="{ad['page_profile_picture_url']}" style="width:28px; height:28px; border-radius:50%; border:1px solid #E2E8F0;">
                                        <div style="font-weight:700; font-size:0.85rem; color:#1E293B; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{ad['page_name']}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Media
                                    if ad['media']:
                                        st.image(ad['media'], use_container_width=True)
                                    else:
                                        st.markdown("<div style='height:200px; background:#F1F5F9; display:flex; align-items:center; justify-content:center; color:#94A3B8;'>Geen preview</div>", unsafe_allow_html=True)
                                    
                                    # Metrics
                                    days = ad['days_active']
                                    if days < 1: days = 1
                                    
                                    # Realistische schattingen
                                    base_spend = days * 25
                                    est_spend = base_spend + random.randint(0, 50)
                                    
                                    if days > 14: 
                                        status_col = "#16A34A" 
                                        status_txt = "🔥 WINNER"
                                    elif days > 3:
                                        status_col = "#CA8A04" 
                                        status_txt = "⚡ SCALING"
                                    else:
                                        status_col = "#2563EB" 
                                        status_txt = "🧪 TESTING"

                                    st.markdown(f"""
                                    <div class="metric-container">
                                        <div class="metric-item">
                                            <div class="metric-val">{days}d</div>
                                            <div class="metric-lbl">Actief</div>
                                        </div>
                                        <div class="metric-item">
                                            <div class="metric-val">€{int(est_spend)}</div>
                                            <div class="metric-lbl">Spend</div>
                                        </div>
                                        <div class="metric-item">
                                            <div class="metric-val" style="color:{status_col}; font-size:0.9rem;">{status_txt}</div>
                                            <div class="metric-lbl">Status</div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)

                                    # Knoppen
                                    st.link_button(f"🛒 Bekijk Product in Shop", ad['shop_link'], type="primary", use_container_width=True)
                                    
                                    with st.expander("📄 Lees Ad Tekst"):
                                        st.code(ad['caption'], language="text")

            elif st.session_state.get("fb_search_active") and not st.session_state.get("fb_results"):
                st.warning("Geen ads gevonden. Probeer het over een minuutje nog eens.")

        else:
            render_pro_lock("Meta Spy", "Direct toegang tot winnende Facebook Ads.", "Zie precies welke ads en teksten je concurrenten gebruiken.")



    # =========================================================
    # --- TAB 3: CONCURRENTEN SPY (SHOPIFY) ---
    # =========================================================
    with tab3:
        st.markdown("### 🕵️ Spiek bij de buren")
        st.markdown("Heb je een dropshipping store gevonden? Vul de URL in en zie hun bestsellers.")
        
        if is_pro:
            with st.container(border=True):
                url_input = st.text_input("URL van concurrent", placeholder="bijv. www.loavies.com")
                
                if url_input and st.button("🚀 Scan Webshop", type="primary"):
                     if "." not in url_input:
                         st.warning("Vul een geldige URL in.")
                     else:
                         with st.spinner(f"Bezig met scannen van {url_input}..."):
                             products = competitor_spy.scrape_shopify_store(url_input)
                             
                             if products:
                                 st.success(f"✅ {len(products)} producten gevonden!")
                                 for i in range(0, len(products), 3):
                                     cols = st.columns(3)
                                     for j in range(3):
                                         if i + j < len(products):
                                             p = products[i + j]
                                             with cols[j]:
                                                 with st.container(border=True):
                                                     if p['image_url']: st.image(p['image_url'], use_container_width=True)
                                                     st.markdown(f"**{p['title']}**")
                                                     price_display = f"€{p['price']}" if p['price'] != "???" else "?"
                                                     st.caption(f"{price_display}")
                                                     st.link_button("Bekijk in shop", p['url'], use_container_width=True)
                             else:
                                 st.error("Kon geen producten vinden. Is dit wel een Shopify store?")
        else: 
            render_pro_lock("Spy Tool", "Zie de nieuwste producten van élke concurrent.", "Exclusief voor studenten.")

elif pg == "Instellingen":
    st.markdown("<h1><i class='bi bi-gear-fill'></i> Instellingen</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Profiel", "Partner", "Koppelingen", "Hulp", "Feedback"])
    
    with tab1:
        # --- PROFIEL PAGINA (PLAYER CARD STYLE) ---
        st.markdown("### 👤 Jouw Profiel")
        
        with st.container(border=True):
            col_p1, col_p2 = st.columns([1, 3], vertical_alignment="center")
            
            with col_p1:
                # Grote Avatar Letter
                display_name = user.get('first_name') or "Gast"
                letter = display_name[0].upper()
                st.markdown(f"""
                <div style="width:80px; height:80px; background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); 
                border-radius:50%; display:flex; justify-content:center; align-items:center; 
                font-size:35px; color:#2563EB; font-weight:800; border:3px solid #BFDBFE; margin: 0 auto;">
                    {letter}
                </div>
                """, unsafe_allow_html=True)
            
            with col_p2:
                # Naam & Status Badge
                user_status = "Student 🎓" if is_pro else "Gast 👤"
                status_color = "#DCFCE7" if is_pro else "#F1F5F9"
                status_text_color = "#166534" if is_pro else "#64748B"
                
                st.markdown(f"""
                <h3 style="margin:0; padding:0;">{display_name}</h3>
                <div style="margin-top:5px; margin-bottom:10px;">
                    <span style="background:{status_color}; color:{status_text_color}; padding: 4px 10px; border-radius:15px; font-size:0.8rem; font-weight:700; border: 1px solid rgba(0,0,0,0.05);">
                        {user_status}
                    </span>
                    <span style="color:#94A3B8; font-size:0.9rem; margin-left:10px;">{user['email']}</span>
                </div>
                """, unsafe_allow_html=True)

            # Voortgangsbalkje in profiel
            st.markdown("---")
            c_lvl, c_xp = st.columns([1, 4], vertical_alignment="bottom")
            c_lvl.markdown(f"**Lvl {user['level']}**")
            # Herbereken percentage voor visualisatie
            range_span = next_xp_goal_sidebar - prev_threshold
            xp_pct = min((user['xp'] - prev_threshold) / range_span, 1.0)
            c_xp.progress(xp_pct)
            c_xp.caption(f"Nog {next_xp_goal_sidebar - user['xp']} XP tot volgende level")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚪 Uitloggen", use_container_width=True):
                cookie_manager.delete("rmecom_user_email")
                st.session_state.clear()
                st.rerun()

    with tab2:
        # --- PARTNER / VRIENDEN PAGINA ---
        
        # 1. De Header
        st.markdown("""
        <div style="text-align:center; margin-bottom: 20px;">
            <h2 style="color:#166534; margin-bottom:5px;">💸 Verdien €250,- per vriend</h2>
            <p style="color:#64748B;">Help anderen starten met e-commerce en wordt zelf beloond.</p>
        </div>
        """, unsafe_allow_html=True)

        # 2. De Stats
        stats = auth.get_affiliate_stats()
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 25px;">
            <div style="background:#F8FAFC; padding:15px; border-radius:12px; text-align:center; border:1px solid #E2E8F0;">
                <div style="font-size:0.8rem; font-weight:700; color:#64748B; text-transform:uppercase;">Kliks</div>
                <div style="font-size:1.4rem; font-weight:800; color:#0F172A;">{stats[0] * 5}</div> 
            </div>
            <div style="background:#F0FDF4; padding:15px; border-radius:12px; text-align:center; border:1px solid #BBF7D0;">
                <div style="font-size:0.8rem; font-weight:700; color:#166534; text-transform:uppercase;">Studenten</div>
                <div style="font-size:1.4rem; font-weight:800; color:#15803D;">{stats[1]}</div>
            </div>
            <div style="background:#FFF7ED; padding:15px; border-radius:12px; text-align:center; border:1px solid #FED7AA;">
                <div style="font-size:0.8rem; font-weight:700; color:#9A3412; text-transform:uppercase;">Verdiend</div>
                <div style="font-size:1.4rem; font-weight:800; color:#C2410C;">€{stats[2]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 3. Hoe werkt het
        with st.container(border=True):
            st.markdown("#### 🚀 Hoe werkt het?")
            c1, c2, c3 = st.columns(3)
            c1.markdown("**1. Deel je link**\nStuur je unieke link naar vrienden die ook willen ondernemen.")
            c2.markdown("**2. Zij starten**\nZij maken een account aan via jouw link.")
            c3.markdown("**3. Jij casht**\nWorden ze student? Dan krijg jij direct **€250** gestort.")

        # --- LOGICA VOOR CODE GENERATIE (TEMP FIX) ---
        # Als de user 'TEMP' heeft, maken we een mooie code op basis van de naam
        current_ref = user.get('referral_code', 'TEMP')
        if current_ref == 'TEMP':
            # Pak eerste 3 letters van naam (of email) + random getal
            safe_name = user.get('first_name') or user.get('email', 'USER')
            safe_name = safe_name[:3].upper()
            # We gebruiken een hash van de email zodat het getal altijd hetzelfde is voor deze user, maar wel 'random' lijkt
            fake_num = sum(ord(c) for c in user['email']) % 900 + 100
            current_ref = f"{safe_name}-{fake_num}"

        # 4. Deel Acties
        st.markdown("### 🔗 Deel direct & Claim XP")
        
        # Deel Link maken
        share_link = f"https://rmacademy.onrender.com/?ref={current_ref}"
        share_text = f"Hee! Ik ben begonnen met mijn eigen webshop via RM Ecom. Gebruik mijn code {current_ref} voor een vliegende start: {share_link}"
        whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(share_text)}"
        
        # Duidelijke beloning tekst
        st.info("🎁 **Bonus:** Klik op een knop hieronder en ontvang direct **+50 XP**!")

        col_share_1, col_share_2 = st.columns(2)
        
        with col_share_1:
            st.link_button(f"💚 Deel via WhatsApp", whatsapp_url, use_container_width=True)
            
        with col_share_2:
            if st.button("📋 Link Kopiëren", use_container_width=True):
                st.toast(f"Link gekopieerd: {share_link}", icon="✅")
                # XP Beloning toekennen
                if "share_xp_claimed" not in st.session_state:
                    auth.mark_step_complete("share_bonus_action", 50)
                    st.session_state.share_xp_claimed = True
                    st.balloons()
                    time.sleep(1)
                    st.rerun()

        # 5. Handmatige code tonen
        with st.expander("Toon mijn handmatige code"):
            st.write("Jouw unieke vriendencode:")
            st.code(current_ref, language="text")
            st.caption("Vrienden kunnen deze code invullen bij het aanmaken van een account.")
            
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
        # --- HULP PAGINA (DUIDELIJKE KEUZE) ---
        st.markdown("### 🆘 Waar heb je hulp bij nodig?")
        st.markdown("Kies de juiste weg voor het snelste antwoord.")

        col_h1, col_h2 = st.columns(2)

        with col_h1:
            with st.container(border=True):
                st.markdown("""
                <div style="text-align:center;">
                    <div style="font-size:40px; margin-bottom:10px;">💬</div>
                    <h4 style="margin:0;">Vragen over E-com?</h4>
                    <p style="font-size:0.85rem; color:#64748B; min-height:40px;">
                        "Hoe werkt Shopify?", "Is dit product goed?".<br>Vraag het aan 500+ andere studenten.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                st.link_button("Naar Discord Community", COMMUNITY_URL, type="primary", use_container_width=True)

        with col_h2:
            with st.container(border=True):
                st.markdown("""
                <div style="text-align:center;">
                    <div style="font-size:40px; margin-bottom:10px;">⚙️</div>
                    <h4 style="margin:0;">Account Problemen?</h4>
                    <p style="font-size:0.85rem; color:#64748B; min-height:40px;">
                        Inloggen lukt niet, wachtwoord vergeten of betalingsvragen.<br>Wij helpen je persoonlijk.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                st.link_button("Stuur Email", "mailto:support@rmecom.nl", use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("❓ Veelgestelde vragen"):
            st.markdown("""
            **Is de app gratis?**
            Ja, de basis is gratis. Voor geavanceerde tools (Spy Tool, AI content) heb je de cursus nodig.
            
            **Hoe krijg ik meer XP?**
            Voltooi stappen in de Roadmap of gebruik de tools in het dashboard.
            
            **Mijn vriendencode werkt niet?**
            Neem even contact op via de mail, dan lossen we het op!
            """)
    
    with tab5:
        st.markdown("#### 💡 Jouw mening telt")
        
        # Check of we in deze sessie al succesvol feedback hebben gegeven
        if st.session_state.get("feedback_done", False):
            # --- DE 'LOCKED' / SUCCES STATUS ---
            st.markdown("""
            <div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 12px; padding: 20px; text-align: center;">
                <div style="font-size: 40px; margin-bottom: 10px;">✅</div>
                <h3 style="color: #166534; margin: 0;">Bedankt voor je feedback!</h3>
                <p style="color: #15803D; margin-top: 5px;">We hebben je bericht ontvangen en je beloning geactiveerd.</p>
                <div style="margin-top: 15px; font-size: 0.9rem; color: #16A34A; font-weight: 600;">
                    Geniet van je 24u PRO toegang! 🚀
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            # --- WINACTIE BANNER (NIEUW) ---
            st.markdown("""
            <div style="background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); border: 1px solid #FCD34D; padding: 15px; border-radius: 12px; margin-bottom: 20px; display: flex; gap: 15px; align-items: center;">
                <div style="font-size: 30px; background: white; width: 50px; height: 50px; display: flex; align-items: center; justify-content: center; border-radius: 50%; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">🏆</div>
                <div>
                    <h4 style="margin: 0; color: #92400E; font-size: 1rem;">Win Lifetime PRO Toegang!</h4>
                    <p style="margin: 2px 0 0 0; font-size: 0.85rem; color: #B45309;">
                        Elke maand geven we <b>1x Volledige Cursus + PRO</b> weg aan de beste feedback.
                        Help ons verbeteren en win!
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- HET FORMULIER ---
            st.caption("Je krijgt sowieso **direct 24u PRO toegang** als dank voor je bericht! 🎁")
            
            fb_text = st.text_area("Feedback", placeholder="Ik mis functie X... / Ik vind dit lastig...", height=120, key="fb_settings")
            
            if st.button("Verstuur & Claim PRO🚀", use_container_width=True):
                if len(fb_text) > 10:
                    with st.spinner("Checken..."):
                        # 1. Valideer en sla op
                        is_valid = ai_coach.validate_feedback(fb_text)
                        db.save_feedback(user['email'], fb_text, is_valid)
                        
                        if is_valid:
                            # 2. Claim de reward
                            status = db.claim_feedback_reward(user['email'])
                            
                            if status == "SUCCESS":
                                st.balloons()
                                st.success("🎉 PRO Geactiveerd! 24u toegang gestart.")
                                
                                # Update Sessie, Cache EN zet de Feedback Vlag op True
                                user['is_pro'] = True 
                                st.session_state.user['is_pro'] = True
                                st.session_state.feedback_done = True # <--- DIT ZORGT VOOR DE LOCK
                                st.cache_data.clear()
                                
                                time.sleep(2)
                                st.rerun() 
                                
                            elif status == "ALREADY_CLAIMED":
                                st.session_state.feedback_done = True 
                                st.warning("Je hebt deze beloning al eens geclaimd.")
                                time.sleep(2)
                                st.rerun()
                                
                            else: 
                                st.error("Database fout bij activeren PRO.")
                        else: 
                            st.warning("Feedback te kort of onduidelijk.")
                else: 
                    st.warning("Typ minimaal 10 letters.")