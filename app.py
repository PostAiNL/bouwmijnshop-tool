import streamlit as st
import pandas as pd
import random
import datetime
import json
import time
import os
import base64
import streamlit.components.v1 as components 
from modules import analytics, ui, auth, ai_coach, data_loader

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="PostAi - Jouw persoonlijke Ai TikTok coach", page_icon="assets/logo.png", layout="centered", initial_sidebar_state="collapsed")

# Style laden
ui.inject_style_and_hacks(brand_color="#10b981")

# --- 2. PUBLIEKE LINKS LOGICA (VOOR PADDLE) ---
qp = st.query_params
target_view = qp.get("view", "")

# Als de URL ?view=privacy of ?view=terms bevat
if target_view in ["privacy", "terms", "contact"]:
    st.session_state.page = target_view
    st.session_state.license_key = "public_visitor"
    
    # --- FIX: DUMMY VARIABELEN AANMAKEN OM CRASH TE VOORKOMEN ---
    if "user_niche" not in st.session_state: st.session_state.user_niche = ""
    if "xp" not in st.session_state: st.session_state.xp = 0
    if "streak" not in st.session_state: st.session_state.streak = 0
    if "level" not in st.session_state: st.session_state.level = 1
    if "golden_tickets" not in st.session_state: st.session_state.golden_tickets = 0
    # -------------------------------------------------------------
else:
    # Normale initialisatie voor echte gebruikers
    auth.init_session()

# --- 3. NAVIGATIE FUNCTIES ---
def go_home(): st.session_state.page = "home"
def go_studio(): st.session_state.page = "studio"
def go_tools(): st.session_state.page = "tools"
def go_stats(): st.session_state.page = "stats"
def go_settings(): st.session_state.page = "settings"
def go_privacy(): st.session_state.page = "privacy"
def go_terms(): st.session_state.page = "terms"
def go_contact(): st.session_state.page = "contact"

# --- 4. AUTH CHECK ---
if target_view not in ["privacy", "terms", "contact"]:
    if not auth.is_authenticated():
        auth.render_landing_page()
        st.stop()

# OPTIMALISATIE & DATA LADEN (Alleen als we echt ingelogd zijn)
if target_view not in ["privacy", "terms", "contact"] and "xp" not in st.session_state:
    user_data = auth.load_progress()
    st.session_state.page = "home"
    st.session_state.streak = auth.check_daily_streak()
    st.session_state.xp = user_data.get("xp", 50)
    st.session_state.level = user_data.get("level", 1)
    st.session_state.golden_tickets = user_data.get("golden_tickets", 0)
    st.session_state.user_niche = user_data.get("niche", "")
    st.session_state.brand_voice = user_data.get("brand_voice", "De expert 🧠")
    st.session_state.openai_key = user_data.get("openai_key", "")
    st.session_state.daily_xp_earned = user_data.get("daily_xp_earned", 0)
    st.session_state.last_xp_date = user_data.get("last_xp_date", str(datetime.datetime.now().date()))
    st.session_state.challenge_day = user_data.get("challenge_day", 1)
    st.session_state.weekly_goal = user_data.get("weekly_goal", 0)
    st.session_state.weekly_progress = user_data.get("weekly_progress", 0)

# Variabelen instellen (Ook voor public view, anders crasht de rest van de code)
if target_view in ["privacy", "terms", "contact"]:
    is_pro = False
    niche = ""
    user_data = {}
else:
    is_pro = auth.is_pro()
    niche = st.session_state.user_niche
    user_data = st.session_state.get("local_user_data", {}) 
    ai_coach.init_ai()

# --- 4. HELPER FUNCTIES ---
def check_feature_access(feature_key):
    if is_pro: return True
    active_feat = user_data.get("active_trial_feature", "")
    end_time_str = user_data.get("trial_end_time", "")
    if active_feat == feature_key and end_time_str:
        try:
            end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() < end_time: return True
            else: auth.save_progress(active_trial_feature=None, trial_end_time=None); return False
        except: return False
    return False

def add_xp(amount):
    today = str(datetime.datetime.now().date())
    if st.session_state.last_xp_date != today:
        st.session_state.daily_xp_earned = 0
        st.session_state.last_xp_date = today
        auth.save_progress(daily_xp_earned=0, last_xp_date=today)
    if st.session_state.daily_xp_earned >= 80:
        st.toast("⚠️ Daglimiet XP bereikt (80/80)")
        return
    allowed = min(amount, 80 - st.session_state.daily_xp_earned)
    if allowed > 0:
        st.session_state.xp += allowed
        st.session_state.daily_xp_earned += allowed
        if st.session_state.xp >= 100:
            st.session_state.xp -= 100
            st.session_state.level += 1
            st.session_state.golden_tickets += 1
            st.balloons()
            st.toast(f"🎉 LEVEL UP! Lvl {st.session_state.level}")
            if not is_pro: st.toast("🎫 +1 Golden ticket!")
        else:
            st.toast(f"+{allowed} XP ({st.session_state.xp}/100)")
        auth.save_progress(xp=st.session_state.xp, level=st.session_state.level, golden_tickets=st.session_state.golden_tickets, daily_xp_earned=st.session_state.daily_xp_earned, last_xp_date=today)

def use_golden_ticket(feature_name):
    if st.session_state.golden_tickets > 0:
        st.session_state.golden_tickets -= 1
        end_time = (datetime.datetime.now() + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        auth.save_progress(golden_tickets=st.session_state.golden_tickets, active_trial_feature=feature_name, trial_end_time=end_time)
        st.balloons()
        st.success(f"🔓 {feature_name} is 24 uur geactiveerd!")
        time.sleep(2); st.rerun()
    else: st.error("Geen tickets genoeg!")

# OPTIMALISATIE: Logo Cachen (Nu met show_spinner=False)
@st.cache_data(show_spinner=False)
def load_logo():
    if os.path.exists("assets/logo.png"):
        with open("assets/logo.png", "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{img_b64}"
    return "https://via.placeholder.com/50/10b981/ffffff?text=P"

# --- GAME EXPLANATION DIALOG (AANGEPAST: KORT & SIMPEL) ---
@st.dialog("🎓 Hoe werkt PostAi?")
def show_help_dialog():
    st.markdown("""
    Zo gebruik je hem als beste:

    🔥 **Streakdagen:**
    Log elke dag in om je vlammetje te houden. Mis je een dag? Dan begin je opnieuw.
    
    🎁 **XP punten:**
    Maak scripts en verdien punten. Bij 100 XP ga je een **level omhoog**!
    
    🎫 **Golden tickets:**
    Level omhoog? Dan krijg je een ticket. Daarmee mag je **PRO tools** 24 uur lang gratis gebruiken.
    """)
    if st.button("Begrepen! 🚀", type="primary"):
        st.rerun()

# --- 5. HEADER ---
col_head, col_set = st.columns([0.85, 0.15])
with col_head:
    logo_src = load_logo() # Gebruik de gecachte versie
    badge = "PRO" if is_pro else "DEMO"
    badge_style = "background:#dcfce7; color:#166534; border:1px solid #bbf7d0;" if is_pro else "background:#eff6ff; color:#1e40af; border:1px solid #dbeafe;"
    
    st.markdown(f"""
    <div class="header-container">
        <div class="header-logo"><img src="{logo_src}"></div>
        <div class="header-text">
            <div class="header-title">PostAi <span style="font-size:0.6rem; padding:2px 6px; border-radius:4px; vertical-align:middle; margin-left:12px; {badge_style}">{badge}</span></div>
            <p class="header-subtitle">Jouw persoonlijke AI TikTok coach</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_set:
    # AANGEPAST: Instellingen knop is weg, nu een 'Help' knop voor uitleg
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("❓", help="Uitleg over de app", type="secondary"): 
        show_help_dialog()

st.markdown("---")

# --- 6. REWARD POPUP ---
has_reward = user_data.get("unclaimed_reward", False)
if has_reward and not is_pro:
    @st.dialog("🎁 Gefeliciteerd: 5 dagen streak!")
    def show_reward_popup():
        st.markdown("""<div style="text-align:center;"><div style="font-size:3rem;">🔥</div><h3>Lekker bezig!</h3><p>Kies 1 PRO tool om <b>24 uur gratis</b> te gebruiken:</p></div>""", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        end_time = (datetime.datetime.now() + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        with c1:
            if st.button("📈 Conversie story", use_container_width=True, type="primary"): 
                auth.save_progress(unclaimed_reward=False, active_trial_feature="Sales mode", trial_end_time=end_time)
                st.balloons(); time.sleep(1); st.rerun()
        with c2:
            if st.button("🕵️ Viral remix", use_container_width=True, type="primary"):
                auth.save_progress(unclaimed_reward=False, active_trial_feature="Viral remix", trial_end_time=end_time)
                st.balloons(); time.sleep(1); st.rerun()
        with c3:
            if st.button("🎬 Serie bedenker", use_container_width=True, type="primary"):
                auth.save_progress(unclaimed_reward=False, active_trial_feature="Serie generator", trial_end_time=end_time)
                st.balloons(); time.sleep(1); st.rerun()
    show_reward_popup()

# --- AANGEPAST BLOK: NICHE CHECK OVERSLAAN BIJ PUBLIC PAGES ---
if st.session_state.page not in ["privacy", "terms", "contact"]:
    if not st.session_state.user_niche:
        st.info("Welkom! Wat is je niche?")
        n = st.text_input("Niche:", placeholder="bv. Kapper")
        if st.button("Start", type="primary"):
            if n: st.session_state.user_niche = n; auth.save_progress(niche=n, xp=50); st.rerun()
        st.stop() # Stop hier zodat de rest van de app niet laadt zonder niche
# --------------------------------------------------------------

# ==========================
# 🏠 HOME DASHBOARD
# ==========================
if st.session_state.page == "home":
    # Niche met hoofdletter tonen voor netheid
    display_niche = niche.title() if niche else "Creator"
    greeting = f"👋 Hi {display_niche} creator!" if niche else "👋 Hi creator!"
    
    st.markdown(f"<h3 style='margin:0; padding:0; margin-bottom: 10px;'>{greeting}</h3>", unsafe_allow_html=True)
    
    if is_pro:
        metrics_html = f"""
        <div class="metrics-strip" style="gap:5px; margin-bottom:15px;">
            <div class="metric-card" style="padding: 8px;" title="Je streak: Houd dit vol om beloningen te krijgen!">
                <div class="metric-val" style="color:#ef4444; font-size:1.2rem;">{st.session_state.streak}</div><div class="metric-lbl" style="font-size:0.7rem;">🔥 Streakdagen</div>
            </div>
            <div class="metric-card" style="padding: 8px;" title="Jouw huidige niveau. Verdien 100 XP om te stijgen!">
                <div class="metric-val" style="color:#10b981; font-size:1.2rem;">{st.session_state.level}</div><div class="metric-lbl" style="font-size:0.7rem;">🏆 Level</div>
            </div>
            <div class="metric-card" style="padding: 8px;" title="Ervaringspunten. Bij 100 XP ga je een level omhoog.">
                <div class="metric-val" style="color:#3b82f6; font-size:1.2rem;">{st.session_state.xp}</div><div class="metric-lbl" style="font-size:0.7rem;">🎁 XP punten</div>
            </div>
        </div>"""
    else:
        metrics_html = f"""
        <div class="metrics-strip" style="gap:5px; margin-bottom:15px;">
            <div class="metric-card" style="padding: 8px;" title="Je streak: Post elke dag om deze te verhogen!">
                <div class="metric-val" style="color:#ef4444; font-size:1.2rem;">{st.session_state.streak}</div><div class="metric-lbl" style="font-size:0.7rem;">🔥 Streakdagen</div>
            </div>
            <div class="metric-card" style="padding: 8px;" title="Golden tickets: Zet in om PRO functies 24 uur te unlocken.">
                <div class="metric-val" style="color:#f59e0b; font-size:1.2rem;">{st.session_state.golden_tickets}</div><div class="metric-lbl" style="font-size:0.7rem;">🎫 Tickets</div>
            </div>
            <div class="metric-card" style="padding: 8px;" title="Verdien 100 XP voor een Level up + Gratis ticket!">
                <div class="metric-val" style="color:#3b82f6; font-size:1.2rem;">{st.session_state.xp}</div><div class="metric-lbl" style="font-size:0.7rem;">🎁 XP punten</div>
            </div>
        </div>"""
    
    st.markdown(metrics_html, unsafe_allow_html=True)

# ... (na de metrics html) ...

    if st.button("🚨 Panic button: ik heb nu een idee nodig!", use_container_width=True, type="primary"):
        if auth.check_ai_limit():
            with st.spinner("🚀 AI scant viral kansen in jouw niche..."):
                script = ai_coach.generate_instant_script(niche)
                auth.track_ai_usage()
                
                # --- FIX: Oude afbeeldingen verwijderen ---
                # Dit voorkomt dat je een plaatje van de 'Viral Maker' ziet bij je Panic script
                if "generated_img_url" in st.session_state:
                    del st.session_state.generated_img_url
                if "generated_img" in st.session_state:
                    del st.session_state.generated_img
                # ------------------------------------------
                    
                st.session_state.last_script = script
                go_studio(); st.rerun()
        else:
             st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}). Kom morgen terug of upgrade naar PRO!")

    # --- SLIMME TREND LOGICA (FIX: MET SEED) ---
    if "trend_version" not in st.session_state:
        st.session_state.trend_version = random.randint(1, 1000)

    if "niche_trend" not in st.session_state:
        if niche:
            with st.spinner(f"🔥 Trends voor {niche} zoeken..."):
                st.session_state.niche_trend = ai_coach.get_personalized_trend(niche, st.session_state.trend_version)
        else:
            st.session_state.niche_trend = ai_coach.get_weekly_trend()
            
    trend = st.session_state.niche_trend

    # Strakkere Trend Box
    st.markdown(f"""
    <div class="trend-box" style="margin-top: 15px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
             <div class="trend-label">🔥 Trend voor jou</div>
        </div>
        <div class="trend-title">{trend.get('title', 'Trend')}</div>
        <div style="font-size:0.9rem; margin-top:5px; margin-bottom:10px;">{trend.get('desc', '')}</div>
        <div style="font-size:0.8rem; background:rgba(255,255,255,0.2); padding:5px 10px; border-radius:6px; margin-bottom:10px;">🎵 {trend.get('sound', '')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Knoppen
    c_trend1, c_trend2 = st.columns([1, 4])
    with c_trend1:
        if st.button("🔄", help="Nieuwe trend zoeken"):
            if auth.check_ai_limit():
                # FIX: Cache breken door versie te verhogen
                st.session_state.trend_version += 1
                if "niche_trend" in st.session_state: del st.session_state.niche_trend
                auth.track_ai_usage()
                st.rerun()
            else:
                 st.error("🛑 Daglimiet bereikt (10/10). Kom morgen terug of upgrade naar PRO!")
    with c_trend2:
        if st.button("✍️ Gebruik deze trend", use_container_width=True, type="primary"):
            st.session_state.last_script = f"**Video Concept: {trend.get('title')}**\n\n**Geluid:** {trend.get('sound')}\n\n**Visueel:** {trend.get('desc')}\n\n**Script:**\n(Jouw tekst hier...)"
            st.session_state.generated_img = f"Een shot passend bij de trend: {trend.get('title')}"
            st.session_state.generated_img_url = ai_coach.generate_viral_image(trend.get('title'), "Trendy", niche)
            go_studio()
            st.rerun()
    # --------------------------------

    st.markdown("---")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("<div class='nav-card'><div class='nav-icon'>📅</div><div class='nav-title'>Bootcamp</div><div class='nav-desc'>Jouw opdracht van vandaag.</div></div>", unsafe_allow_html=True)
        if st.button("Start missie", key="btn_boot", use_container_width=True, type="primary"): st.session_state.page = "bootcamp"; st.rerun()
        
        st.markdown("<div class='nav-card'><div class='nav-icon'>📈</div><div class='nav-title'>Cijfers & advies</div><div class='nav-desc'>Upload stats en krijg tips.</div></div>", unsafe_allow_html=True)
        if st.button("Bekijk stats", key="btn_stats", use_container_width=True, type="primary"): go_stats(); st.rerun()
    with col_b:
        st.markdown("<div class='nav-card'><div class='nav-icon'>✨</div><div class='nav-title'>Maak content</div><div class='nav-desc'>Laat AI je script schrijven.</div></div>", unsafe_allow_html=True)
        if st.button("Open studio", key="btn_studio", use_container_width=True, type="primary"): go_studio(); st.rerun()
        
        st.markdown("<div class='nav-card'><div class='nav-icon'>🚀</div><div class='nav-title'>Slimme tools</div><div class='nav-desc'>Bio-fixer, remixer & meer.</div></div>", unsafe_allow_html=True)
        if st.button("Open tools", key="btn_tools", use_container_width=True, type="primary"): go_tools(); st.rerun()

# ==========================
# 🚀 BOOTCAMP
# ==========================
if st.session_state.page == "bootcamp":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 🚀 Bootcamp")
    if st.session_state.weekly_goal == 0:
        with st.container(border=True):
            st.markdown("### 🎯 Weekdoel")
            goal = st.slider("Aantal video's:", 1, 7, 3)
            if st.button("Ik beloof het! 🤝", use_container_width=True, type="primary"): 
                st.session_state.weekly_goal = goal; auth.save_progress(weekly_goal=goal); st.rerun()
    else:
        st.progress(min(st.session_state.weekly_progress / st.session_state.weekly_goal, 1.0))
        st.caption(f"Doel: {st.session_state.weekly_progress}/{st.session_state.weekly_goal} Video's")

    current_day = st.session_state.challenge_day
    tasks = ai_coach.get_challenge_tasks()
    task_txt = tasks.get(current_day, "Klaar!")

    with st.container(border=True):
        st.markdown(f"#### 🥾 Dag {current_day}: Opdracht")
        st.info(f"**Missie:** {task_txt}")
        if not (current_day > 3 and not is_pro):
            chal_format = st.radio("Format", ["🎥 Video", "📸 Foto"], horizontal=True, label_visibility="collapsed")
            if st.button("✨ Schrijf script", use_container_width=True, type="primary"):
                if auth.check_ai_limit():
                    with st.spinner("🤖 De Coach schrijft jouw bootcamp script..."):
                        st.session_state.chal_script = ai_coach.generate_challenge_script(current_day, task_txt, niche, chal_format)
                        auth.track_ai_usage()
                        st.rerun()
                else:
                    st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")
        else:
            if st.session_state.golden_tickets > 0 and not is_pro:
                st.markdown(f"<div class='ticket-box'>🔒 <b>PRO Dag.</b><br>Inzetten: 1 Ticket?</div>", unsafe_allow_html=True)
                if st.button("🎫 Gebruik ticket", type="primary"):
                    if auth.use_ticket():
                        if auth.check_ai_limit():
                            with st.spinner("Ticket valideren en script schrijven..."):
                                st.session_state.chal_script = ai_coach.generate_challenge_script(current_day, task_txt, niche, "Video")
                                auth.track_ai_usage()
                                st.rerun()
                        else:
                            st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")
            elif is_pro:
                chal_format = st.radio("Format", ["🎥 Video", "📸 Foto"], horizontal=True, label_visibility="collapsed")
                if st.button("✨ Schrijf script", use_container_width=True, type="primary"):
                    if auth.check_ai_limit():
                        with st.spinner("🤖 De Coach schrijft jouw bootcamp script..."):
                            st.session_state.chal_script = ai_coach.generate_challenge_script(current_day, task_txt, niche, chal_format)
                            auth.track_ai_usage()
                            st.rerun()
                    else:
                        st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")
            else: ui.render_locked_section("AI Coach", "Upgrade naar PRO")

    if "chal_script" in st.session_state:
        with st.expander("📜 Jouw script", expanded=True):
            st.markdown(st.session_state.chal_script)
            st.markdown("---")
            st.caption("Heb je de video gepost? Plak de link om je XP te claimen!")
            post_link = st.text_input("Link naar TikTok video", placeholder="https://tiktok.com/...")
            
            if st.button("✅ Ik heb gepost! (+50 XP)", use_container_width=True, type="primary"):
                if post_link and "http" in post_link:
                    with st.spinner("Link controleren & XP toekennen..."):
                        st.balloons(); auth.handle_daily_streak(); add_xp(50)
                        st.session_state.challenge_day += 1; st.session_state.weekly_progress += 1
                        auth.save_progress(challenge_day=st.session_state.challenge_day, weekly_progress=st.session_state.weekly_progress)
                        del st.session_state.chal_script; time.sleep(2); st.rerun()
                else:
                    st.error("Plak eerst een geldige link naar je video!")

# ==========================
# 🎬 STUDIO (VERBETERD MET BIBLIOTHEEK)
# ==========================
# ==========================
# 🎬 STUDIO (MET LOSSE VISUALS & BIBLIOTHEEK FIX)
# ==========================
if st.session_state.page == "studio":
    # Header
    c_back, c_title, c_clear = st.columns([1, 3, 1])
    with c_back:
        if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    with c_title:
        st.markdown("## 🎬 Studio")
    with c_clear:
        # Knop om het huidige werkblad leeg te maken
        if "last_script" in st.session_state or "studio_mode" in st.session_state:
            if st.button("🗑️ Wis", help="Leeg het werkblad"):
                keys_to_clear = ["last_script", "generated_img_url", "studio_mode", "current_visual"]
                for k in keys_to_clear:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()

    # Data ophalen
    saved_library = user_data.get("library", [])
    
    # Check wat we aan het doen zijn (Script modus of Visual modus)
    has_active_script = "last_script" in st.session_state
    has_active_visual = "current_visual" in st.session_state and not has_active_script

    # --- BEPAAL TAB INDELING ---
    if has_active_script:
        tab_editor, tab_prompter, tab_lib = st.tabs(["📝 Huidig Script", "🎬 Teleprompter", "📚 Bibliotheek"])
    elif has_active_visual:
        tab_vis_view, tab_lib = st.tabs(["🖼️ Jouw Creatie", "📚 Bibliotheek"])
    else:
        tab_gen, tab_lib = st.tabs(["✨ Nieuw Maken", "📚 Bibliotheek"])

    # ==========================================
    # 1. EDITOR (ALS ER EEN SCRIPT IS)
    # ==========================================
    if has_active_script:
        with tab_editor:
            # Toon bijbehorend plaatje (indien aanwezig)
            if "generated_img_url" in st.session_state and st.session_state.generated_img_url:
                st.image(st.session_state.generated_img_url, caption="📸 Visueel concept", width=300)
            
            st.info("👇 Dit is je huidige werkversie.")
            
            # Script weergave
            st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:10px; border:1px solid #e5e7eb; color:black;">
                {st.session_state.last_script.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
            
            st.write("") # Spacer

            # Actie knoppen
            c_save, c_copy = st.columns(2)
            with c_save:
                if st.button("💾 Opslaan in bieb", type="primary", use_container_width=True):
                    if is_pro:
                        topic_name = st.session_state.get("current_topic", f"Script {datetime.datetime.now().strftime('%d-%m')}")
                        # We slaan het op als type 'script'
                        script_data = {
                            "id": str(uuid.uuid4()), 
                            "date": str(datetime.datetime.now().date()), 
                            "topic": topic_name, 
                            "content": st.session_state.last_script,
                            "type": "script",
                            "img": st.session_state.get("generated_img_url", "")
                        }
                        
                        # Toevoegen aan library lijst
                        new_lib = [script_data] + saved_library
                        auth.save_progress(library=new_lib)
                        
                        st.balloons()
                        st.toast("✅ Script opgeslagen!")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("🔒 Opslaan is een PRO functie.")
            
            with c_copy:
                # FIX: Hier ging het fout. Nu gebruiken we st.code wat een ingebouwde copy knop heeft
                # Of we gebruiken een verborgen tekstblokje. De makkelijkste fix is st.code (als tekst):
                st.code(st.session_state.last_script, language=None)
                st.caption("👆 Klik op het icoontje rechtsboven in het vak om te kopiëren.")

        with tab_prompter:
            # (Teleprompter code blijft hetzelfde als je al had, ingekort voor overzicht)
            st.markdown("### 🎬 Pro teleprompter")
            st.info("Plak je telefoon tegen de spiegel of lees direct van het scherm.")
            safe_script = st.session_state.last_script.replace('\n', '<br>')
            components.html(f"""
            <div style="font-family:Arial; font-weight:bold; font-size:40px; text-align:center; color:white; background:black; padding:50px;">
            <marquee direction="up" scrollamount="3" height="400px">{safe_script}</marquee></div>
            """, height=450)

    # ==========================================
    # 2. VISUAL VIEWER (ALS ER ALLEEN EEN PLAATJE IS)
    # ==========================================
    elif has_active_visual:
        with tab_vis_view:
            st.markdown("### 🖼️ Jouw AI Creatie")
            st.image(st.session_state.current_visual, use_column_width=True)
            
            if st.button("💾 Opslaan in bieb", key="save_vis_btn", type="primary"):
                 if is_pro:
                        topic_name = f"Visual {datetime.datetime.now().strftime('%d-%m %H:%M')}"
                        vis_data = {
                            "id": str(uuid.uuid4()), 
                            "date": str(datetime.datetime.now().date()), 
                            "topic": topic_name, 
                            "content": st.session_state.current_visual, # Hier zit de URL in
                            "type": "image"
                        }
                        new_lib = [vis_data] + saved_library
                        auth.save_progress(library=new_lib)
                        st.balloons(); st.toast("✅ Opgeslagen!"); time.sleep(1); st.rerun()
                 else: st.error("🔒 Alleen PRO")
            
            if st.button("🔄 Maak er nog een", type="secondary"):
                del st.session_state.current_visual
                st.rerun()

# ==========================================
    # 3. GENERATORS (NIEUW MAKEN)
    # ==========================================
    else:
        with tab_gen:
            # Tabbladen
            sub_viral, sub_conv, sub_vis, sub_hook = st.tabs(["👀 Viral Script", "📈 Sales Script (PRO)", "🎨 Visuals (PRO)", "🪝 Hook Tester"])
            
            # --- A. VIRAL SCRIPT (GRATIS) ---
            with sub_viral:
                with st.form("viral_form"):
                    st.markdown("### 🎬 Script Generator")
                    topic = st.text_input("Onderwerp:", placeholder="Waar gaat de video over?")
                    tone = st.radio("Toon", ["Energiek ⚡", "Rustig 😌", "Grappig 😂"], horizontal=True)
                    
                    # AANGEPAST: Formats met uitleg
                    format_options = [
                        "Talking Head 🗣️ (Jij praat direct in de camera)",
                        "Vlog 🤳 (Dag uit het leven / op pad)",
                        "Green Screen 🖼️ (Jij voor een nieuwsbericht/plaatje)"
                    ]
                    fmt_selection = st.selectbox("Format:", format_options)
                    
                    # We moeten de selectie weer 'schoonmaken' voor de AI (alleen het eerste deel)
                    fmt_clean = fmt_selection.split(" (")[0].strip()
                    
                    if st.form_submit_button("Schrijf Script (+10 XP)", type="primary"):
                        if auth.check_ai_limit():
                            with st.spinner("✍️ Script schrijven & Visual bedenken..."):
                                # 1. Script
                                st.session_state.last_script = ai_coach.generate_script(topic, fmt_clean, tone, "verrassend", "Volg voor meer", niche, st.session_state.brand_voice)
                                # 2. Afbeelding (Gratis gebruikers krijgen hier ook een plaatje bij, dat hoort bij de core functie)
                                st.session_state.generated_img_url = ai_coach.generate_viral_image(topic, tone, niche)
                                
                                auth.track_ai_usage()
                                add_xp(10)
                                st.session_state.current_topic = topic
                                st.rerun()
                        else: st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")

            # --- B. SALES SCRIPT (PRO LOCKED) ---
            with sub_conv:
                # Check of gebruiker PRO is of een trial heeft
                if check_feature_access("Sales Mode"):
                    with st.form("sales_form"):
                        st.markdown("### 📈 Sales Script")
                        st.caption("Gebruik psychologische triggers om te verkopen.")
                        
                        prod = st.text_input("Product of Dienst:", placeholder="bv. Mijn E-book over afvallen")
                        pain = st.text_input("Pijnpunt van klant:", placeholder="bv. Geen tijd om te sporten")
                        
                        sales_submitted = st.form_submit_button("✍️ Schrijf Sales Script (+10 XP)", type="primary")

                    if sales_submitted:
                        if auth.check_ai_limit():
                            with st.spinner("💰 Psychologische triggers verwerken..."):
                                st.session_state.last_script = ai_coach.generate_sales_script(prod, pain, "Story", niche)
                                st.session_state.generated_img_url = ai_coach.generate_viral_image(f"Product shot: {prod}", "Clean & Aesthetic", niche)
                                auth.track_ai_usage(); add_xp(10); st.session_state.current_topic = f"Sales: {prod}"; st.rerun()
                        else: st.error(f"🛑 Daglimiet bereikt.")
                else:
                    # PRO LOCK WEERGAVE
                    # Laat de gebruiker eventueel een ticket inzetten als ze die hebben
                    if st.session_state.golden_tickets > 0:
                        st.info(f"Je hebt {st.session_state.golden_tickets} Golden Tickets. Wil je er eentje inzetten?")
                        if st.button("🎫 Zet Golden Ticket in (24u toegang)", key="ticket_sales"):
                            use_golden_ticket("Sales Mode")
                    
                    # Toon het slotje
                    ui.render_locked_section("Sales Mode", "Verander kijkers in kopers met psychologische scripts.")

# --- C. VISUALS (PRO LOCKED + TICKET OPTIE) ---
            with sub_vis:
                # 1. Check toegang (Pro OF tijdelijk via Ticket)
                if check_feature_access("Creative Visuals"):
                    st.markdown("### 🎨 Creative Generator")
                    st.caption("Maak thumbnails, achtergronden of moodboards zonder script.")
                    
                    vis_prompt = st.text_input("Wat wil je zien?", placeholder="Bv. Een luxe kantoor met neon verlichting...")
                    vis_style = st.selectbox("Stijl", ["Fotorealistisch 📸", "Cinematic 🎬", "3D Render 🧊", "Anime 🌸", "Minimalistisch ⚪"])
                    
                    if st.button("✨ Genereer Visual (+5 XP)", type="primary"):
                        if auth.check_ai_limit():
                            with st.spinner("🎨 Aan het schilderen..."):
                                img_url = ai_coach.generate_viral_image(vis_prompt, vis_style, niche)
                                auth.track_ai_usage()
                                add_xp(5)
                                st.session_state.current_visual = img_url
                                st.rerun()
                        else: st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")
                
                # 2. Geen toegang? Toon Ticket knop + Slotje
                else:
                    # Als ze tickets hebben, toon de knop om te unlocken
                    if st.session_state.golden_tickets > 0:
                        st.info(f"Je hebt {st.session_state.golden_tickets} Golden Tickets. Wil je er eentje inzetten?")
                        if st.button("🎫 Zet Golden Ticket in (24u toegang)", key="ticket_visuals"):
                            use_golden_ticket("Creative Visuals")
                    
                    # Het slotje (verwijst naar upgrade pagina)
                    ui.render_locked_section("Creative Visuals", "Genereer onbeperkt unieke AI afbeeldingen voor je video's.")

            # --- D. HOOK TESTER (GRATIS) ---
            with sub_hook:
                st.markdown("### 🪝 Viral Hook Tester")
                st.caption("Een goede hook is 80% van je succes.")
                
                user_hook = st.text_input("Jouw openingszin:", placeholder="Bijvoorbeeld: Stop met scrollen als je...")
                
                if st.button("🚀 Test & Verbeter", type="primary"):
                    if user_hook:
                        if auth.check_ai_limit():
                            with st.spinner("⚖️ De jury overlegt..."):
                                res = ai_coach.rate_user_hook(user_hook, niche)
                                auth.track_ai_usage()
                                score = res.get('score', 0)
                                color = "red" if score < 6 else "orange" if score < 8 else "green"
                                st.markdown(f"""
                                <div style="text-align:center; padding:15px; border-radius:10px; border:2px solid {color}; background:rgba(255,255,255,0.8); margin-bottom:15px; color:black;">
                                    <div style="font-size:2.5rem; font-weight:bold; color:{color};">{score}/10</div>
                                    <div style="font-style:italic;">"{res.get('feedback')}"</div>
                                </div>""", unsafe_allow_html=True)
                                if 'alternatives' in res:
                                    st.markdown("#### ✨ Probeer deze eens:")
                                    for alt in res['alternatives']: st.info(f"🔥 {alt}")
                        else: st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")
                    else: st.warning("Vul eerst een zin in!")

    # ==========================================
    # 4. BIBLIOTHEEK (SLIM GEMAAKT)
    # ==========================================
    with tab_lib:
        st.markdown("### 📂 Bibliotheek")
        if not saved_library:
            st.info("Nog niks opgeslagen.")
        else:
            for item in saved_library:
                # Check type (script of image)
                item_type = item.get("type", "script") # Backwards compatibility
                icon = "🖼️" if item_type == "image" else "📝"
                
                with st.expander(f"{icon} {item.get('date', '?')} | {item.get('topic', 'Naamloos')}"):
                    
                    # WEERGAVE LOGICA
                    if item_type == "script":
                        st.caption("📝 Script")
                        st.text(item.get('content')[:100] + "...") # Preview
                        if st.button("Openen", key=f"open_{item['id']}"):
                            st.session_state.last_script = item.get('content')
                            st.session_state.generated_img_url = item.get('img', None)
                            st.rerun()
                            
                    elif item_type == "image":
                        st.caption("🖼️ Afbeelding")
                        st.image(item.get('content'), width=200)
                        if st.button("Vergroot / Bewerk", key=f"view_{item['id']}"):
                            st.session_state.current_visual = item.get('content')
                            # Zorg dat we niet in script modus zitten
                            if "last_script" in st.session_state: del st.session_state.last_script
                            st.rerun()

                    # VERWIJDER KNOP (Gedeeld)
                    if st.button("🗑️ Verwijderen", key=f"del_{item['id']}", type="secondary"):
                        auth.delete_script_from_library(item['id'])
                        st.rerun()

# ==========================
# 🛠️ TOOLS
# ==========================
if st.session_state.page == "tools":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 🛠️ Tools")
    st.caption("Gebruik deze slimme tools om sneller te groeien.")
    
    # 1. BIO
    with st.expander("🧬 Bio optimalisator"):
        st.info("💡 **Doel:** Maak van jouw bezoekers, echte volgers door een perfecte bio.")
        bio = st.text_input("Huidige bio:")
        if st.button("Verbeter bio", type="primary"): 
            if auth.check_ai_limit():
                with st.spinner("Analyseren..."):
                    st.markdown(ai_coach.generate_bio_options(bio, niche))
                    auth.track_ai_usage()
            else: st.error("Daglimiet.")

    # 2. IDEE CHECKER
    with st.expander("🔥 Idee checker"):
        st.info("💡 **Doel:** Voorspel of je video gaat scoren vóórdat je filmt.")
        idea = st.text_input("Jouw video-idee:")
        if st.button("Check potentie", type="primary"): 
             if auth.check_ai_limit():
                 with st.spinner("Scannen..."):
                     res = ai_coach.check_viral_potential(idea, niche)
                     auth.track_ai_usage()
                     st.success(f"Score: {res['score']}/100")
                     st.write(res['verdict'])
             else: st.error("Daglimiet.")

    # 3. REMIX
    with st.expander("🕵️ Viral remix tool (PRO)"):
        st.info("💡 **Doel:** Maak een eigen versie van een virale video")
        if check_feature_access("Viral remix"):
            other = st.text_area("Plak hier het script/tekst van de concurrent:")
            if st.button("🔀 Remix dit script", type="primary"): 
                if auth.check_ai_limit():
                    with st.spinner("Herschrijven..."):
                        st.markdown(ai_coach.steal_format_and_rewrite(other, "Mijn Onderwerp", niche))
                        auth.track_ai_usage()
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock de remix tool (24u)", key="btn_remix"): use_golden_ticket("Viral remix")
            ui.render_locked_section("Viral remix", "Maak eigen versie succescontent.")

    # 4. PASSIEF INKOMEN
    with st.expander("📦 Passief inkomen bedenker (PRO)"):
        st.info("💡 **Doel:** Bedenk een digitaal product om geld te verdienen.")
        if check_feature_access("Product bedenker"):
             tgt = st.text_input("Wie is de doelgroep?:")
             if st.button("Genereer businessplan:", type="primary"):
                 if auth.check_ai_limit():
                     with st.spinner("Brainstormen..."):
                        plan = ai_coach.generate_digital_product_plan(niche, tgt); st.markdown(plan)
                        auth.track_ai_usage()
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock de product tool (24u)", key="btn_prod"): use_golden_ticket("Product bedenker")
            ui.render_locked_section("Product bedenker", "Verdien geld terwijl je slaapt.")

    # 5. SERIE
    with st.expander("🎬 5 video's in 1 klik (PRO)"):
        st.info("💡 **Doel:** Maak in één keer een hele serie scripts om kijkers vast te houden.")
        if check_feature_access("Serie generator"):
            stpc = st.text_input("Onderwerp van de serie:")
            if st.button("Bouw serie", type="primary"): 
                if auth.check_ai_limit():
                    with st.spinner("Schrijven..."):
                        st.markdown(ai_coach.generate_series_ideas(stpc, niche))
                        auth.track_ai_usage()
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock de serie tool (24u)", key="btn_serie"): use_golden_ticket("Serie generator")
            ui.render_locked_section("Serie generator", "Binge-waardige content.")

    # 6. WEEKPLANNER
    with st.expander("📅 Weekplanner (PRO)"):
        st.info("💡 **Doel:** Een kant-en-klaar schema voor de hele week, zodat je consistent blijft.")
        if check_feature_access("Weekplanner"):
            if st.button("Plan mijn week", type="primary"):
                if auth.check_ai_limit():
                    with st.spinner("Plannen..."):
                        st.markdown(ai_coach.generate_weekly_plan(niche))
                        auth.track_ai_usage()
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock de weekplanner (24u)", key="btn_plan"): use_golden_ticket("Weekplanner")
            ui.render_locked_section("Weekplanner", "Nooit meer stress.")

# ==========================
# 📊 STATS (MET VISION)
# ==========================
if st.session_state.page == "stats":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 📊 Cijfers & analyse")
    
    # 1. Upload Sectie
    st.info("📸 Upload een screenshot van je TikTok analytics (van 1 video of je profiel).")
    uploaded_file = st.file_uploader("Kies je screenshot:", type=['png', 'jpg', 'jpeg'])

    if uploaded_file is not None:
        # Toon het plaatje klein
        st.image(uploaded_file, caption="Jouw screenshot", width=200)
        
        if st.button("🚀 Analyseer met AI", type="primary"):
            if auth.check_ai_limit():
                with st.spinner("🤖 AI kijkt naar je cijfers..."):
                    # Hier roepen we de functie in ai_coach.py aan
                    result = ai_coach.analyze_analytics_screenshot(uploaded_file)
                    auth.track_ai_usage()
                    
                    # Toon resultaat
                    st.success("Analyse compleet!")
                    
                    # Mooie weergave van de data
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Geschatte views:", result.get('totaal_views', '-'))
                    with col2:
                        st.write("**Beste video:**")
                        st.caption(result.get('beste_video', '-'))
                    
                    st.markdown("### 💡 Advies van de coach")
                    st.info(result.get('advies:', 'Geen advies beschikbaar.'))
            else:
                 st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")

    st.markdown("---")
    st.markdown("#### 🏆 Leaderboard")
    st.dataframe(ai_coach.get_leaderboard(niche, st.session_state.xp), use_container_width=True, hide_index=True)

# ==========================
# ⚙️ SETTINGS
# ==========================
if st.session_state.page == "settings":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## ⚙️ Instellingen")
    
    with st.container(border=True):
        new_niche = st.text_input("Niche:", value=niche)
        
        st.markdown("### 🗣️ Jouw stijl (brand voice)")
        
        # Oude dropdown optie, maar nu slim met custom voice support
        current_voice = st.session_state.brand_voice
        voice_options = ["De expert 🧠", "De beste vriendin 💖", "De harde waarheid 🔥", "De grappenmaker 😂", "Custom (gekloond) 🤖"]
        
        # Zorg dat de huidige stem in de lijst staat, anders default
        idx = 0
        if current_voice in voice_options:
            idx = voice_options.index(current_voice)
        elif current_voice not in voice_options:
            # Als we een custom voice hebben die niet in de lijst staat
            if "Custom (gekloond) 🤖" not in voice_options: voice_options.append("Custom (gekloond) 🤖")
            idx = voice_options.index("Custom (gekloond) 🤖")
            
        voice = st.selectbox("Kies je stem:", voice_options, index=idx)
        
        # --- NIEUWE CLONE MY VOICE FUNCTIE ---
        with st.expander("🤖 Kloon mijn stem (beta)"):
            st.info("Plak hieronder 3 van je beste captions of scripts. De AI analyseert jouw unieke stijl.")
            sample_text = st.text_area("Plak je teksten hier:", height=150)
            
            if st.button("🧬 Analyseer & kloon Stijl"):
                if sample_text and len(sample_text) > 50:
                    if auth.check_ai_limit():
                        with st.spinner("Jouw DNA analyseren..."):
                            custom_style = ai_coach.analyze_writing_style(sample_text)
                            auth.track_ai_usage()
                            
                            # Opslaan
                            st.session_state.brand_voice = custom_style
                            auth.save_progress(brand_voice=custom_style)
                            st.success(f"Gelukt! Jouw nieuwe stijl: '{custom_style}'")
                            time.sleep(2)
                            st.rerun()
                    else:
                        st.error("Daglimiet bereikt.")
                else:
                    st.warning("Plak iets meer tekst voor een goede analyse.")
        # -------------------------------------

        if st.button("Opslaan", type="primary"): 
            # Alleen opslaan als we niet net de clone knop hebben gebruikt (die slaat al op)
            if voice != "Custom (gekloond) 🤖":
                st.session_state.brand_voice = voice
            
            auth.save_progress(niche=new_niche, brand_voice=st.session_state.brand_voice)
            st.success("Instellingen opgeslagen!")
            time.sleep(1)
            st.rerun()

    if is_pro:
        st.success("✅ Je bent een PRO lid. Geniet van alle functies!")
        st.info(f"Level: {st.session_state.level} | XP: {st.session_state.xp}/100")
    else:
        st.markdown("###")
        
        # Pricing Box
        st.markdown("""
        <div class="pricing-box">
            <div class="fomo-badge">🔥Populairste keuze</div>
            <div class="pricing-header">
                <h3>Upgrade naar PRO</h3>
                <div class="price-tag">€14,95<span class="price-period">/maand</span></div>
                <small style="color:#ef4444; font-weight:bold;">(Normaal €19,95 - Early bird deal)</small>
            </div>
            <div style="margin-bottom: 20px;">
                ✅ Onbeperkt scripts (met de AI coach)<br>
                ✅ Virale remix tools <br>
                ✅ Passief inkomen generator
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Buy Button (PayPro Link Updated)
        st.link_button("👉 Claim 25% korting & start direct", "https://www.paypro.nl/product/PostAi_PRO_-_Maandelijks/125181", type="primary", use_container_width=True)
        st.caption("Je ontvangt direct je licentiecode per mail.")
        
        st.markdown("---")
        
        with st.expander("Heb je al een licentiecode?"):
            c = st.text_input("Vul je licentiecode in:")
            if st.button("Activeer Licentiecode", type="primary"): auth.activate_pro(c)
            
    # --- NIEUW: HIER IS HET ACCOUNT BLOK NU ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🔑 Account & licentiecode (gegevens)", expanded=False):
        st.caption("Dit is jouw unieke sleutel. Bewaar deze om later weer in te loggen.")
        st.code(st.session_state.license_key, language=None)
        st.info("Tip: Sla deze pagina op in je favorieten ⭐")

# --- IN app.py (Settings sectie) ---
    
    st.markdown("---")
    st.markdown("### 🎁 Help ons & krijg een cadeau")
    
    # We kijken in de data of ze het al gedaan hebben
    already_done = user_data.get("has_given_feedback", False)
    
    # Pas de titel aan op basis van status
    expander_title = "✅ Feedback gegeven (Ticket geclaimd)" if already_done else "📢 Geef je mening (+1 Golden Ticket)"
    
    with st.expander(expander_title, expanded=False):
        if already_done:
            st.info("Bedankt voor je hulp! Je hebt je golden ticket al ontvangen. Je kunt dit maar 1x doen.")
            st.caption("Heb je meer feedback? Mail gerust naar support@postaiapp.nl")
        else:
            st.write("Heb je tips en/of tops? Geef je feedback en krijg een gratis **Golden Ticket** !")
            
            fb_text = st.text_area("Jouw feedback:", placeholder="Ik zou graag willen dat...")
            
            if st.button("Verstuur & claim ticket", type="primary"):
                if fb_text and len(fb_text) > 5:
                    with st.spinner("🤖 AI beoordeelt je feedback..."):
                        # 1. Check kwaliteit
                        is_good = ai_coach.check_feedback_quality(fb_text)
                        
                        # 2. Opslaan & Belonen (Met de nieuwe check)
                        # save_feedback geeft nu True of False terug
                        success = auth.save_feedback(fb_text, is_good)
                        
                        if is_good and success:
                            st.balloons()
                            st.success("✅ Goedgekeurd! +1 Golden Ticket toegevoegd aan je account.")
                            time.sleep(2)
                            st.rerun()
                        elif not is_good:
                            st.error("❌ De AI vond je feedback te kort of niet specifiek genoeg. Probeer het opnieuw.")
                        else:
                            # Dit gebeurt als ze via een omweg toch proberen te dubbelen
                            st.error("⚠️ Je hebt deze beloning al geclaimd.")
                else:
                    st.warning("Vul minimaal 1 korte zin in.")

# ==========================
# 📄 PRIVACY, VOORWAARDEN & CONTACT
# ==========================
if st.session_state.page == "privacy":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 🔒 Privacybeleid")
    st.markdown("Laatst bijgewerkt: 25 november 2025")
    
    st.markdown("""
    Bij **PostAi** nemen we jouw privacy serieus. Hier leggen we uit hoe we met jouw gegevens omgaan.

    ### 1. Welke gegevens verzamelen we?
    Om de app te laten werken, slaan we minimale gegevens op:
    *   **Profiel:** Jouw niche, gekozen 'brand voice' en voortgang (XP, Level, Streak).
    *   **Inputs:** De onderwerpen, teksten en bio's die jij invoert om te verbeteren.
    *   **Geüploade media:** Screenshots van analytics worden tijdelijk verwerkt door onze AI om data uit te lezen en worden niet permanent op onze servers bewaard.

    ### 2. Hoe gebruiken we AI (OpenAI)?
    Wij gebruiken de officiële API van OpenAI (GPT-4) om scripts en analyses te genereren. 
    *   **Geen training:** Data die via de API wordt verstuurd, wordt door OpenAI **niet** gebruikt om hun modellen te trainen (volgens hun Enterprise privacybeleid).
    *   **Verwerking:** Jouw input wordt veilig verstuurd, verwerkt en het resultaat wordt teruggestuurd naar de app.

    ### 3. Opslag van gegevens
    In deze versie van de app worden jouw voortgang en instellingen lokaal opgeslagen (in een database bestand gekoppeld aan jouw licentiecode) of in de browser-sessie. Wij verkopen jouw data nooit aan derden.

    ### 4. Contact
    Voor vragen over je gegevens of om je account te verwijderen, kun je contact opnemen via support@postaiapp.nl.
    """)

if st.session_state.page == "terms":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 📜 Algemene voorwaarden & disclaimer")
    st.caption("Laatst gewijzigd: 25 november 2025")
    
    st.markdown("""
    ### 1. Aansprakelijkheid & gebruik van AI
    PostAi is een hulpmiddel dat gebruikmaakt van Artificial Intelligence (OpenAI). 
    *   **Jouw verantwoordelijkheid:** De gegenereerde scripts en adviezen dienen als concept. Jij bent als gebruiker volledig eindverantwoordelijk voor de content die je publiceert. Controleer teksten altijd op feitelijke juistheden en toon.
    *   **Geen professioneel advies:** De output van de app is ter inspiratie en vervangt geen juridisch, medisch of financieel advies.
    *   **Fouten:** AI kan hallucineren (feitelijke onjuistheden produceren). PostAi is niet aansprakelijk voor enige schade die voortvloeit uit het gebruik van deze informatie.

    ### 2. Garantie op resultaten
    *   **Geen succesgarantie:** Wij bieden tools om je kansen te vergroten, maar garanderen geen specifieke resultaten zoals het "viral gaan", groei in volgers of omzetstijging. Het succes op social media is afhankelijk van vele externe factoren en jouw eigen uitvoering.

    ### 3. Fair Use Policy (gebruikslimiet)
    Om de service stabiel en betaalbaar te houden, geldt er een 'Fair Use Policy':
    *   **Limieten:** Er zit een dagelijkse limiet op het aantal AI-generaties per gebruiker (zowel voor PRO als gratis accounts). Deze limiet is ruim voldoende voor normaal menselijk gebruik.
    *   **Misbruik:** Het is verboden om het systeem te manipuleren, te scrapen of te gebruiken via geautomatiseerde bots. Bij misbruik wordt het account direct opgeschort zonder restitutie.

    ### 4. Intellectueel eigendom
    *   **Jouw content:** De scripts en ideeën die jij genereert met PostAi zijn jouw eigendom. Je mag deze vrij gebruiken, aanpassen en commercieel inzetten.
    *   **Onze App:** De broncode, het ontwerp en de werking van de PostAi applicatie blijven eigendom van PostAi.

    ### 5. Abonnement & restitutie
    *   **Opzeggen:** Het PRO-abonnement is maandelijks opzegbaar. Na opzegging behoud je toegang tot het einde van de lopende periode.
    *   **Garantie:** Wij hanteren een 14-dagen 'niet-goed-geld-terug' garantie op de eerste betaling als de service niet aan de verwachtingen voldoet.
    """)

if st.session_state.page == "contact":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 📬 Contact & support")
    
    st.markdown("""
    Heb je vragen, hulp nodig bij je abonnement of een technische storing? 
    Neem contact met ons op, we helpen je graag verder!
    """)
    
    with st.container(border=True):
        st.markdown("### ✍️ Stuur een bericht")
        subject = st.text_input("Onderwerp:", placeholder="Waar gaat het over?")
        msg_body = st.text_area("Bericht:", placeholder="Typ hier je vraag...")
        
        # Omdat we geen backend mailserver hebben in de frontend, gebruiken we mailto
        mail_link = f"mailto:support@postaiapp.nl?subject={subject}&body={msg_body}"
        
        st.link_button("📤 Verstuur via mail", mail_link, type="primary", use_container_width=True)
        st.caption("Dit opent je standaard mailprogramma.")

    st.markdown("---")
    
    st.markdown("### 🏢 Bedrijfsgegevens")
    st.info("""
    **Bouwmijnshop.nl (PostAi)**  
    Stephanusstraat 21  
    6363BM Wijnandsrade  
    
    **KVK:** 95665293
    **BTW:** NL005168650B28  
    **Email:** support@postaiapp.nl
    """)

# --- FOOTER ---
ui.inject_chat_widget(auth.get_secret("CHAT_URL", ""))
st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

# Footer aangepast: Instellingen naar beneden + Contact toegevoegd
c_foot1, c_foot2, c_foot3 = st.columns([1, 4, 1]) # Breder middenstuk

with c_foot2:
    if st.button("⚙️ Instellingen", use_container_width=True, type="secondary"):
        go_settings()
        st.rerun()
        
    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
    
    f1, f2, f3 = st.columns(3)
    with f1: 
        if st.button("Ons privacybeleid", key="f_priv", use_container_width=True, type="secondary"):
            go_privacy(); st.rerun()
    with f2: 
        if st.button("Onze voorwaarden", key="f_terms", use_container_width=True, type="secondary"):
            go_terms(); st.rerun()
    with f3:
        if st.button("Onze contactgegevens", key="f_contact", use_container_width=True, type="secondary"):
            go_contact(); st.rerun()

st.markdown("""<div class="footer-container"><div class="footer-text">14 dagen gratis • Gemaakt voor TikTok</div><div class="footer-sub">© 2025 PostAi. Alle rechten voorbehouden.</div></div>""", unsafe_allow_html=True)