import streamlit as st
import pandas as pd
import random
import datetime
import json
import time
import os
import base64
import streamlit.components.v1 as components # Nodig voor de teleprompter
from modules import analytics, ui, auth, ai_coach, data_loader

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="PostAi", page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")
auth.init_session()

# Style laden
ui.inject_style_and_hacks(brand_color="#10b981")

# --- 2. NAVIGATIE ---
def go_home(): st.session_state.page = "home"
def go_studio(): st.session_state.page = "studio"
def go_tools(): st.session_state.page = "tools"
def go_stats(): st.session_state.page = "stats"
def go_settings(): st.session_state.page = "settings"
def go_privacy(): st.session_state.page = "privacy"
def go_terms(): st.session_state.page = "terms"

# --- 3. AUTH CHECK ---
if not auth.is_authenticated():
    auth.render_landing_page()
    st.stop()

# OPTIMALISATIE
if "xp" not in st.session_state:
    user_data = auth.load_progress()
    st.session_state.page = "home"
    st.session_state.streak = auth.check_daily_streak()
    st.session_state.xp = user_data.get("xp", 50)
    st.session_state.level = user_data.get("level", 1)
    st.session_state.golden_tickets = user_data.get("golden_tickets", 0)
    st.session_state.user_niche = user_data.get("niche", "")
    st.session_state.brand_voice = user_data.get("brand_voice", "De Expert 🧠")
    st.session_state.openai_key = user_data.get("openai_key", "")
    st.session_state.daily_xp_earned = user_data.get("daily_xp_earned", 0)
    st.session_state.last_xp_date = user_data.get("last_xp_date", str(datetime.datetime.now().date()))
    st.session_state.challenge_day = user_data.get("challenge_day", 1)
    st.session_state.weekly_goal = user_data.get("weekly_goal", 0)
    st.session_state.weekly_progress = user_data.get("weekly_progress", 0)

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
            if not is_pro: st.toast("🎫 +1 Golden Ticket!")
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

def create_pdf(text):
    try:
        from fpdf import FPDF
        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 15); self.cell(0, 10, 'PostAi - Masterplan', 0, 1, 'C'); self.ln(10)
        pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=11)
        safe_text = text.encode('latin-1', 'replace').decode('latin-1')
        for line in safe_text.split('\n'): pdf.multi_cell(0, 7, line)
        return pdf.output(dest='S').encode('latin-1')
    except: return None

# --- 5. HEADER ---
col_head, col_set = st.columns([0.85, 0.15])
with col_head:
    if os.path.exists("assets/logo.png"):
        with open("assets/logo.png", "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
            logo_src = f"data:image/png;base64,{img_b64}"
    else: logo_src = "https://via.placeholder.com/50/10b981/ffffff?text=P"
    badge = "PRO" if is_pro else "DEMO"
    badge_style = "background:#dcfce7; color:#166534; border:1px solid #bbf7d0;" if is_pro else "background:#eff6ff; color:#1e40af; border:1px solid #dbeafe;"
    
    st.markdown(f"""
    <div class="header-container">
        <div class="header-logo"><img src="{logo_src}"></div>
        <div class="header-text">
            <div class="header-title">PostAi <span style="font-size:0.6rem; padding:2px 6px; border-radius:4px; vertical-align:middle; margin-left:12px; {badge_style}">{badge}</span></div>
            <p class="header-subtitle">Dé Tiktokgroeier</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_set:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("⚙️", key="head_set", type="secondary"): 
        go_settings()
        st.rerun()

st.markdown("---")

# --- 6. REWARD POPUP ---
has_reward = user_data.get("unclaimed_reward", False)
if has_reward and not is_pro:
    @st.dialog("🎁 Gefeliciteerd: 5 Dagen Streak!")
    def show_reward_popup():
        st.markdown("""<div style="text-align:center;"><div style="font-size:3rem;">🔥</div><h3>Lekker bezig!</h3><p>Kies 1 PRO tool om <b>24 uur gratis</b> te gebruiken:</p></div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        end_time = (datetime.datetime.now() + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        with c1:
            if st.button("📈 Conversie Story", use_container_width=True, type="primary"): 
                auth.save_progress(unclaimed_reward=False, active_trial_feature="Sales Mode", trial_end_time=end_time)
                st.balloons(); time.sleep(1); st.rerun()
        with c2:
            if st.button("🕵️ Viral Remix", use_container_width=True, type="primary"):
                auth.save_progress(unclaimed_reward=False, active_trial_feature="Viral Remix", trial_end_time=end_time)
                st.balloons(); time.sleep(1); st.rerun()
    show_reward_popup()

if not st.session_state.user_niche:
    st.info("Welkom! Wat is je niche?")
    n = st.text_input("Niche:", placeholder="bv. Kapper")
    if st.button("Start", type="primary"):
        if n: st.session_state.user_niche = n; auth.save_progress(niche=n, xp=50); st.rerun()
    st.rerun()

# ==========================
# 🏠 HOME DASHBOARD
# ==========================
if st.session_state.page == "home":
    # Niche met hoofdletter tonen voor netheid
    display_niche = niche.title() if niche else "Creator"
    # Als er een niche is, plakken we er 'Creator' of 'Expert' achter
    greeting = f"👋 Hi {display_niche} Creator!" if niche else "👋 Hi Creator!"
    
    st.markdown(f"### {greeting}")
    
    if is_pro:
        metrics_html = f"""
        <div class="metrics-strip" style="gap:5px; margin-bottom:15px;">
            <div class="metric-card" style="padding: 8px;" title="Je streak: Houd dit vol om beloningen te krijgen!">
                <div class="metric-val" style="color:#ef4444; font-size:1.2rem;">{st.session_state.streak}</div><div class="metric-lbl" style="font-size:0.7rem;">🔥 Dagen</div>
            </div>
            <div class="metric-card" style="padding: 8px;" title="Jouw huidige niveau. Verdien 100 XP om te stijgen!">
                <div class="metric-val" style="color:#10b981; font-size:1.2rem;">{st.session_state.level}</div><div class="metric-lbl" style="font-size:0.7rem;">🏆 Level</div>
            </div>
            <div class="metric-card" style="padding: 8px;" title="Ervaringspunten. Bij 100 XP ga je een level omhoog.">
                <div class="metric-val" style="color:#3b82f6; font-size:1.2rem;">{st.session_state.xp}</div><div class="metric-lbl" style="font-size:0.7rem;">🎁 XP</div>
            </div>
        </div>"""
    else:
        metrics_html = f"""
        <div class="metrics-strip" style="gap:5px; margin-bottom:15px;">
            <div class="metric-card" style="padding: 8px;" title="Je streak: Post elke dag om deze te verhogen!">
                <div class="metric-val" style="color:#ef4444; font-size:1.2rem;">{st.session_state.streak}</div><div class="metric-lbl" style="font-size:0.7rem;">🔥 Dagen</div>
            </div>
            <div class="metric-card" style="padding: 8px;" title="Golden Tickets: Zet in om PRO functies 24 uur te unlocken.">
                <div class="metric-val" style="color:#f59e0b; font-size:1.2rem;">{st.session_state.golden_tickets}</div><div class="metric-lbl" style="font-size:0.7rem;">🎫 Tickets</div>
            </div>
            <div class="metric-card" style="padding: 8px;" title="Verdien 100 XP voor een Level Up + Gratis Ticket!">
                <div class="metric-val" style="color:#3b82f6; font-size:1.2rem;">{st.session_state.xp}</div><div class="metric-lbl" style="font-size:0.7rem;">🎁 XP</div>
            </div>
        </div>"""
    
    st.markdown(metrics_html, unsafe_allow_html=True)

    if st.button("🚨 PANIC BUTTON: IK HEB NU EEN IDEE NODIG!", use_container_width=True, type="primary"):
        if auth.check_ai_limit():
            with st.spinner("🚀 AI scant viral kansen in jouw niche..."):
                script = ai_coach.generate_instant_script(niche)
                auth.track_ai_usage()
                st.session_state.last_script = script
                go_studio(); st.rerun()
        else:
             st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}). Kom morgen terug of upgrade naar PRO!")

    # --- SLIMME TREND LOGICA ---
    if "niche_trend" not in st.session_state:
        if niche:
            with st.spinner(f"🔥 Trends voor {niche} zoeken..."):
                st.session_state.niche_trend = ai_coach.get_personalized_trend(niche)
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
    
    # Knoppen iets beter gegroepeerd
    c_trend1, c_trend2 = st.columns([1, 4])
    with c_trend1:
        if st.button("🔄", help="Nieuwe trend zoeken"):
            if auth.check_ai_limit():
                if "niche_trend" in st.session_state: del st.session_state.niche_trend
                auth.track_ai_usage()
                st.rerun()
            else:
                 st.error("Op.")
    with c_trend2:
        if st.button("✍️ Gebruik deze Trend", use_container_width=True, type="primary"):
            st.session_state.last_script = f"**Video Concept: {trend.get('title')}**\n\n**Geluid:** {trend.get('sound')}\n\n**Visueel:** {trend.get('desc')}\n\n**Script:**\n(Jouw tekst hier...)"
            st.session_state.generated_img = f"Een shot passend bij de trend: {trend.get('title')}"
            st.session_state.generated_img_url = ai_coach.generate_viral_image(trend.get('title'), "Trendy", niche)
            go_studio()
            st.rerun()
    # --------------------------------

    st.markdown("---")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("<div class='nav-card'><div class='nav-icon'>📅</div><div class='nav-title'>Jouw Missie</div><div class='nav-desc'>Bootcamp dagtaak.</div></div>", unsafe_allow_html=True)
        if st.button("Start Missie", key="btn_boot", use_container_width=True, type="primary"): st.session_state.page = "bootcamp"; st.rerun()
        
        st.markdown("<div class='nav-card'><div class='nav-icon'>📈</div><div class='nav-title'>Check Groei</div><div class='nav-desc'>Bekijk je cijfers.</div></div>", unsafe_allow_html=True)
        if st.button("Bekijk Cijfers", key="btn_stats", use_container_width=True, type="primary"): go_stats(); st.rerun()
    with col_b:
        st.markdown("<div class='nav-card'><div class='nav-icon'>✨</div><div class='nav-title'>Nieuw Script</div><div class='nav-desc'>Open de Studio.</div></div>", unsafe_allow_html=True)
        if st.button("Open Studio", key="btn_studio", use_container_width=True, type="primary"): go_studio(); st.rerun()
        
        st.markdown("<div class='nav-card'><div class='nav-icon'>🚀</div><div class='nav-title'>Viral Remix</div><div class='nav-desc'>Steel een format.</div></div>", unsafe_allow_html=True)
        if st.button("Open Tools", key="btn_tools", use_container_width=True, type="primary"): go_tools(); st.rerun()

# ==========================
# 🚀 BOOTCAMP
# ==========================
if st.session_state.page == "bootcamp":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 🚀 Bootcamp")
    if st.session_state.weekly_goal == 0:
        with st.container(border=True):
            st.markdown("### 🎯 Weekdoel")
            goal = st.slider("Aantal video's", 1, 7, 3)
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
            if st.button("✨ Schrijf Script", use_container_width=True, type="primary"):
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
                if st.button("🎫 Gebruik Ticket", type="primary"):
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
                if st.button("✨ Schrijf Script", use_container_width=True, type="primary"):
                    if auth.check_ai_limit():
                        with st.spinner("🤖 De Coach schrijft jouw bootcamp script..."):
                            st.session_state.chal_script = ai_coach.generate_challenge_script(current_day, task_txt, niche, chal_format)
                            auth.track_ai_usage()
                            st.rerun()
                    else:
                        st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")
            else: ui.render_locked_section("AI Coach", "Upgrade naar PRO")

    if "chal_script" in st.session_state:
        with st.expander("📜 Jouw Script", expanded=True):
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
# 🎬 STUDIO
# ==========================
if st.session_state.page == "studio":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 🎬 Studio")
    
    # Check of er al een script is gegenereerd
    if "last_script" in st.session_state:
        # --- FIXED: PLAATJE OP TELEFOONFORMAAT ---
        if "generated_img_url" in st.session_state and st.session_state.generated_img_url:
            # We gebruiken 3 gelijke kolommen en zetten de width vast op 280px (mobiel formaat)
            c1, c2, c3 = st.columns([1, 1, 1])
            with c2:
                st.image(st.session_state.generated_img_url, caption="📸 Visueel Concept", width=280)
        elif st.session_state.get("generated_img"): 
             st.info(f"🎥 **Visueel Shot Idee:** {st.session_state.generated_img}")
        # -------------------------------------------------

        t1, t2 = st.tabs(["Script", "Teleprompter"])
        with t1:
            st.markdown(st.session_state.last_script)
            if st.button("💾 Opslaan", type="primary"): 
                if is_pro: auth.save_script_to_library("Script", st.session_state.last_script); st.toast("Opgeslagen!")
                else: st.toast("🔒 Alleen PRO")
            if st.button("❌ Nieuw", type="secondary"): del st.session_state.last_script; st.rerun()
        
        # --- AUTO-SCROLL TELEPROMPTER ---
        with t2:
            st.markdown("### 📜 Auto-Scroll Prompter")
            c_speed, c_play = st.columns([3, 1])
            with c_speed:
                speed = st.slider("Scroll Snelheid", 0, 50, 10)
            with c_play:
                st.write("") # Spacer voor uitlijning
                is_playing = st.toggle("▶️ Play", value=False)

            # HTML/JS Injectie voor scrollen
            safe_script = st.session_state.last_script.replace('\n', '<br>')
            
            prompt_html = f"""
            <div id="teleprompter" style="
                font-size: 28px; 
                font-weight: bold;
                line-height: 1.6; 
                height: 450px; 
                overflow-y: scroll; 
                background: #000000; 
                color: #ffffff; 
                padding: 40px 20px; 
                border-radius: 15px;
                font-family: sans-serif;
                text-align: center;">
                {safe_script}
                <br><br><br><br><br><br> <!-- Extra witruimte onderaan -->
            </div>
            
            <script>
                var prompt = document.getElementById("teleprompter");
                var speed = {speed};
                var playing = {str(is_playing).lower()};
                
                function scroll() {{
                    if (playing && speed > 0) {{
                        prompt.scrollTop += (speed / 10);
                    }}
                }}
                
                // Voorkom dubbele intervals
                if (window.prompterInterval) clearInterval(window.prompterInterval);
                window.prompterInterval = setInterval(scroll, 50);
            </script>
            """
            components.html(prompt_html, height=500)
    
    else:
        # Als er nog GEEN script is, toon de tabs
        tab_viral, tab_conv, tab_hook = st.tabs(["👀 Viral Maker", "📈 Conversie", "🪝 Hook Rater"])
        
        # --- TAB 1: VIRAL MAKER ---
        with tab_viral:
            with st.form("viral_form"):
                st.markdown("### 💡 Nieuw Script")
                template = st.selectbox("Template", ["✨ Eigen idee", "🚫 Mythe Ontkrachten", "📚 How-To", "😲 Reactie"])
                topic = st.text_input("Onderwerp:", placeholder="Waar moet het over gaan?")
                tone = st.radio("Toon", ["⚡ Energiek", "😌 Rustig", "😂 Humor"], horizontal=True)
                fmt = st.selectbox("Format", ["Talking Head", "Vlog", "Green Screen"])
                
                submitted = st.form_submit_button("✨ Schrijf Viral Script (+10 XP)", type="primary")
                
                if submitted:
                    if auth.check_ai_limit():
                        status_box = st.empty()
                        
                        with status_box.status("🚀 De AI Coach is bezig...", expanded=True) as status:
                            # STAP 1: Script schrijven
                            status.write("✍️ Script schrijven...")
                            st.session_state.last_script = ai_coach.generate_script(
                                topic if topic else "Iets in mijn niche", 
                                fmt, 
                                tone, 
                                "verrassend", 
                                "Volg voor meer", 
                                niche, 
                                st.session_state.brand_voice
                            )
                            
                            # STAP 2: Plaatje genereren
                            status.write("🎨 Visueel concept tekenen (DALL-E 3)...")
                            st.session_state.generated_img_url = ai_coach.generate_viral_image(topic, tone, niche)
                            
                            status.update(label="✅ Klaar!", state="complete", expanded=False)
                            
                        auth.track_ai_usage()
                        add_xp(10)
                        st.session_state.current_topic = topic
                        st.rerun()
                    else:
                        st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")

        # --- TAB 2: CONVERSIE / SALES ---
        with tab_conv:
            with st.form("sales_form"):
                prod = st.text_input("Product/Dienst")
                pain = st.text_input("Probleem klant")
                sales_submitted = st.form_submit_button("✍️ Schrijf Story (+10 XP)", type="primary")

            if sales_submitted:
                if check_feature_access("Sales Mode"):
                    if auth.check_ai_limit():
                        with st.spinner("💰 Psychologische triggers verwerken in script..."):
                            st.session_state.last_script = ai_coach.generate_sales_script(prod, pain, "Story", niche)
                            auth.track_ai_usage()
                            add_xp(10); st.session_state.current_topic = f"Sales: {prod}"; st.rerun()
                    else:
                        st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")
                else:
                    if st.session_state.golden_tickets > 0:
                         st.error("Gebruik eerst een ticket in het Tools menu of upgrade!")
                    else:
                        st.error("Upgrade naar PRO voor Sales Mode.")

        # --- TAB 3: HOOK RATER ---
        with tab_hook:
            st.markdown("Twijfel je over je openingszin? Test hem hier.")
            user_hook = st.text_input("Jouw Hook:")
            if st.button("Test Hook", type="primary"):
                if user_hook:
                    if auth.check_ai_limit():
                        with st.spinner("🪝 Hook analyseren op viraliteit..."):
                            res = ai_coach.rate_user_hook(user_hook, niche)
                            auth.track_ai_usage()
                            st.markdown(f"### Score: {res['score']}/10")
                            st.info(res['feedback'])
                    else:
                        st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")
                else: st.error("Vul iets in!")

# ==========================
# 🛠️ TOOLS
# ==========================
if st.session_state.page == "tools":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 🛠️ Tools")
    
    with st.expander("🧬 Bio Optimalisator"):
        bio = st.text_input("Huidige bio")
        if st.button("Verbeter Bio", type="primary"): 
            if auth.check_ai_limit():
                with st.spinner("✨ Profiel optimaliseren voor conversie..."):
                    st.markdown(ai_coach.generate_bio_options(bio, niche))
                    auth.track_ai_usage()
            else:
                st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")
                
    with st.expander("🔥 Idee Checker"):
        idea = st.text_input("Jouw idee")
        if st.button("Check Potentie", type="primary"): 
             if auth.check_ai_limit():
                 with st.spinner("📊 Viral kansen berekenen..."):
                     res = ai_coach.check_viral_potential(idea, niche)
                     auth.track_ai_usage()
                     st.info(f"Score: {res['score']}/100 - {res['verdict']}")
             else:
                st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")

    with st.expander("🕵️ Viral Remix Tool (PRO)"):
        if check_feature_access("Viral Remix"):
            other = st.text_area("Plak het script dat je wilt stelen:")
            if st.button("🔀 Remix Script", type="primary"): 
                if auth.check_ai_limit():
                    with st.spinner("🕵️ Structuur stelen en herschrijven..."):
                        st.markdown(ai_coach.steal_format_and_rewrite(other, "Mijn Onderwerp", niche))
                        auth.track_ai_usage()
                else:
                    st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")
            if not is_pro: st.caption("🔓 Tijdelijk ontgrendeld")
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock Remix (24u)", key="btn_remix", type="primary"): use_golden_ticket("Viral Remix")
            ui.render_locked_section("Viral Remix", "Steel formats van virale video's.")
            
    with st.expander("📦 Passief Inkomen (PRO)"):
        if check_feature_access("Product Bedenker"):
             tgt = st.text_input("Doelgroep")
             if st.button("Genereer Plan", type="primary"):
                 if auth.check_ai_limit():
                     with st.spinner("💼 Businessplan genereren..."):
                        plan = ai_coach.generate_digital_product_plan(niche, tgt); st.markdown(plan)
                        pdf = create_pdf(plan); 
                        auth.track_ai_usage()
                        if pdf: st.download_button("📥 Download PDF", data=pdf, file_name="plan.pdf", mime="application/pdf")
                 else:
                    st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock Product (24u)", key="btn_prod", type="primary"): use_golden_ticket("Product Bedenker")
            ui.render_locked_section("Product Bedenker", "Verdien geld terwijl je slaapt.")

    with st.expander("🎬 5 Video's in 1 klik (PRO)"):
        if check_feature_access("Serie Generator"):
            series_topic = st.text_input("Onderwerp Serie:")
            if st.button("Bouw Serie", type="primary"): 
                if auth.check_ai_limit():
                    with st.spinner("🍿 Binge-waardige serie bedenken..."):
                        st.markdown(ai_coach.generate_series_ideas(series_topic, niche))
                        auth.track_ai_usage()
                else:
                    st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")
            if not is_pro: st.caption("🔓 Tijdelijk ontgrendeld")
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock Serie (24u)", key="btn_serie", type="primary"): use_golden_ticket("Serie Generator")
            ui.render_locked_section("Serie Generator", "Binge-waardige content.")

    with st.expander("📅 Weekplanner (PRO)"):
        if check_feature_access("Weekplanner"):
            if st.button("Plan Week", type="primary"):
                if auth.check_ai_limit():
                    with st.spinner("📅 Contentkalender vullen..."):
                        st.markdown(ai_coach.generate_weekly_plan(niche))
                        auth.track_ai_usage()
                else:
                    st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")
            if st.button("📥 Download voor Agenda (.ics)", type="secondary"):
                ics_data = ai_coach.create_ics_file(niche)
                st.download_button("Klik om te downloaden", ics_data, file_name="content_kalender.ics", mime="text/calendar")
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock Planner (24u)", key="btn_plan", type="primary"): use_golden_ticket("Weekplanner")
            ui.render_locked_section("Weekplanner", "Nooit meer stress over wat je moet posten.")

# ==========================
# 📊 STATS (MET VISION)
# ==========================
if st.session_state.page == "stats":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 📊 Cijfers & Analyse")
    
    # 1. Upload Sectie
    st.info("📸 Upload een screenshot van je TikTok analytics (van 1 video of je profiel).")
    uploaded_file = st.file_uploader("Kies je screenshot", type=['png', 'jpg', 'jpeg'])

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
                        st.metric("Geschatte Views", result.get('totaal_views', '-'))
                    with col2:
                        st.write("**Beste Video:**")
                        st.caption(result.get('beste_video', '-'))
                    
                    st.markdown("### 💡 Advies van de Coach")
                    st.info(result.get('advies', 'Geen advies beschikbaar.'))
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
        new_niche = st.text_input("Niche", value=niche)
        
        st.markdown("### 🗣️ Jouw Stijl (Brand Voice)")
        
        # Oude dropdown optie, maar nu slim met custom voice support
        current_voice = st.session_state.brand_voice
        voice_options = ["De Expert 🧠", "De Beste Vriendin 💖", "De Harde Waarheid 🔥", "De Grappenmaker 😂", "Custom (Gekloond) 🤖"]
        
        # Zorg dat de huidige stem in de lijst staat, anders default
        idx = 0
        if current_voice in voice_options:
            idx = voice_options.index(current_voice)
        elif current_voice not in voice_options:
            # Als we een custom voice hebben die niet in de lijst staat
            if "Custom (Gekloond) 🤖" not in voice_options: voice_options.append("Custom (Gekloond) 🤖")
            idx = voice_options.index("Custom (Gekloond) 🤖")
            
        voice = st.selectbox("Kies je stem:", voice_options, index=idx)
        
        # --- NIEUWE CLONE MY VOICE FUNCTIE ---
        with st.expander("🤖 Clone My Voice (Beta)"):
            st.info("Plak hieronder 3 van je beste captions of scripts. De AI analyseert jouw unieke stijl.")
            sample_text = st.text_area("Plak je teksten hier...", height=150)
            
            if st.button("🧬 Analyseer & Kloon Stijl"):
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
            if voice != "Custom (Gekloond) 🤖":
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
            <div class="fomo-badge">🔥Populairste Keuze</div>
            <div class="pricing-header">
                <h3>Upgrade naar PRO</h3>
                <div class="price-tag">€14,95<span class="price-period">/maand</span></div>
                <small style="color:#ef4444; font-weight:bold;">(Normaal €19,95 - Early Bird Deal)</small>
            </div>
            <div style="margin-bottom: 20px;">
                ✅ Onbeperkt Scripts (met de AI coach)<br>
                ✅ Virale Remix Tools <br>
                ✅ Passief Inkomen Generator
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Buy Button (LemonSqueezy Link)
        st.link_button("👉 Claim 25% Korting & Start Direct", "https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2", type="primary", use_container_width=True)
        st.caption("Je ontvangt direct je licentiecode per mail.")
        
        st.markdown("---")
        
        with st.expander("Heb je al een licentiecode?"):
            c = st.text_input("Vul je code in")
            if st.button("Activeer Licentie", type="primary"): auth.activate_pro(c)
            
    # --- NIEUW: HIER IS HET ACCOUNT BLOK NU ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🔑 Account & Licentie (Gegevens)", expanded=False):
        st.caption("Dit is jouw unieke sleutel. Bewaar deze om later weer in te loggen.")
        st.code(st.session_state.license_key, language=None)
        st.info("Tip: Sla deze pagina op in je favorieten ⭐")


# ==========================
# 📄 PRIVACY & VOORWAARDEN
# ==========================
if st.session_state.page == "privacy":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 🔒 Privacy Policy")
    st.markdown("Laatst bijgewerkt: 25 november 2025")
    
    st.markdown("""
    Bij **PostAi** nemen we jouw privacy serieus. Hier leggen we uit hoe we met jouw gegevens omgaan.

    ### 1. Welke gegevens verzamelen we?
    Om de app te laten werken, slaan we minimale gegevens op:
    *   **Profiel:** Jouw niche, gekozen 'brand voice' en voortgang (XP, Level, Streak).
    *   **Inputs:** De onderwerpen, teksten en bio's die jij invoert om te verbeteren.
    *   **Geüploade Media:** Screenshots van analytics worden tijdelijk verwerkt door onze AI om data uit te lezen en worden niet permanent op onze servers bewaard.

    ### 2. Hoe gebruiken we AI (OpenAI)?
    Wij gebruiken de officiële API van OpenAI (GPT-4) om scripts en analyses te genereren. 
    *   **Geen Training:** Data die via de API wordt verstuurd, wordt door OpenAI **niet** gebruikt om hun modellen te trainen (volgens hun Enterprise privacybeleid).
    *   **Verwerking:** Jouw input wordt veilig verstuurd, verwerkt en het resultaat wordt teruggestuurd naar de app.

    ### 3. Opslag van gegevens
    In deze versie van de app worden jouw voortgang en instellingen lokaal opgeslagen (in een database bestand gekoppeld aan jouw licentie) of in de browser-sessie. Wij verkopen jouw data nooit aan derden.

    ### 4. Contact
    Voor vragen over je gegevens of om je account te verwijderen, kun je contact opnemen via support@postai.nl.
    """)

if st.session_state.page == "terms":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 📜 Algemene Voorwaarden & Disclaimer")
    st.caption("Laatst gewijzigd: 25 november 2025")
    
    st.markdown("""
    ### 1. Aansprakelijkheid & Gebruik van AI
    PostAi is een hulpmiddel dat gebruikmaakt van Artificial Intelligence (OpenAI). 
    *   **Jouw verantwoordelijkheid:** De gegenereerde scripts en adviezen dienen als concept. Jij bent als gebruiker volledig eindverantwoordelijk voor de content die je publiceert. Controleer teksten altijd op feitelijke juistheden en toon.
    *   **Geen professioneel advies:** De output van de app is ter inspiratie en vervangt geen juridisch, medisch of financieel advies.
    *   **Fouten:** AI kan hallucineren (feitelijke onjuistheden produceren). PostAi is niet aansprakelijk voor enige schade die voortvloeit uit het gebruik van deze informatie.

    ### 2. Garantie op Resultaten
    *   **Geen succesgarantie:** Wij bieden tools om je kansen te vergroten, maar garanderen geen specifieke resultaten zoals het "viral gaan", groei in volgers of omzetstijging. Het succes op social media is afhankelijk van vele externe factoren en jouw eigen uitvoering.

    ### 3. Fair Use Policy (Gebruikslimiet)
    Om de service stabiel en betaalbaar te houden, geldt er een 'Fair Use Policy':
    *   **Limieten:** Er zit een dagelijkse limiet op het aantal AI-generaties per gebruiker (zowel voor PRO als gratis accounts). Deze limiet is ruim voldoende voor normaal menselijk gebruik.
    *   **Misbruik:** Het is verboden om het systeem te manipuleren, te scrapen of te gebruiken via geautomatiseerde bots. Bij misbruik wordt het account direct opgeschort zonder restitutie.

    ### 4. Intellectueel Eigendom
    *   **Jouw Content:** De scripts en ideeën die jij genereert met PostAi zijn jouw eigendom. Je mag deze vrij gebruiken, aanpassen en commercieel inzetten.
    *   **Onze App:** De broncode, het ontwerp en de werking van de PostAi applicatie blijven eigendom van PostAi.

    ### 5. Abonnement & Restitutie
    *   **Opzeggen:** Het PRO-abonnement is maandelijks opzegbaar. Na opzegging behoud je toegang tot het einde van de lopende periode.
    *   **Garantie:** Wij hanteren een 14-dagen 'niet-goed-geld-terug' garantie op de eerste betaling als de service niet aan de verwachtingen voldoet.
    """)

# --- FOOTER ---
ui.inject_chat_widget(auth.get_secret("CHAT_URL", ""))
st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    f1, f2 = st.columns(2)
    with f1: 
        if st.button("Privacy Policy", key="f_priv", use_container_width=True, type="secondary"):
            st.session_state.page = "privacy"
            st.rerun()
    with f2: 
        if st.button("Voorwaarden", key="f_terms", use_container_width=True, type="secondary"):
            st.session_state.page = "terms"
            st.rerun()

st.markdown("""<div class="footer-container"><div class="footer-text">14 dagen gratis • Gemaakt voor TikTok</div><div class="footer-sub">© 2025 PostAi. Alle rechten voorbehouden.</div></div>""", unsafe_allow_html=True)