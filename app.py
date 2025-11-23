import streamlit as st
import pandas as pd
import random
import datetime
import json
import os
import base64
from modules import analytics, ui, auth, ai_coach, data_loader

# --- CONFIG ---
st.set_page_config(page_title="PostAi", page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")
auth.init_session()
ui.inject_style_and_hacks(brand_color="#10b981")

# --- ROUTING & AUTH ---
if not auth.is_authenticated():
    auth.render_landing_page()
    st.stop()

# --- STATE & DATA ---
current_streak = auth.check_daily_streak()
user_data = auth.load_progress()

if "df" not in st.session_state: st.session_state.df = pd.DataFrame() 
if "streak" not in st.session_state: st.session_state.streak = current_streak
if "level" not in st.session_state: st.session_state.level = user_data.get("level", 1)
if "xp" not in st.session_state: st.session_state.xp = user_data.get("xp", 50)
if "user_niche" not in st.session_state: st.session_state.user_niche = user_data.get("niche", "")
if "challenge_day" not in st.session_state: st.session_state.challenge_day = user_data.get("challenge_day", 1)
if "golden_tickets" not in st.session_state: st.session_state.golden_tickets = user_data.get("golden_tickets", 0)
if "free_audit_credits" not in st.session_state: st.session_state.free_audit_credits = user_data.get("free_audit_credits", 0)

is_pro = auth.is_pro()
niche = st.session_state.user_niche

# --- HULP FUNCTIES (PDF & LOGO) ---
def create_pdf(text):
    try:
        from fpdf import FPDF
        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 15)
                self.cell(0, 10, 'PostAi - Masterplan', 0, 1, 'C')
                self.ln(10)
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        safe_text = text.encode('latin-1', 'replace').decode('latin-1')
        for line in safe_text.split('\n'): pdf.multi_cell(0, 7, line)
        return pdf.output(dest='S').encode('latin-1')
    except: return None

def get_img_as_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- HEADER MET LOGO ONDERSTEUNING ---
def render_custom_header():
    badge = "PRO" if is_pro else "DEMO"
    b_color = "#dcfce7" if is_pro else "#eff6ff"
    t_color = "#166534" if is_pro else "#1e40af"
    
    # Check of logo bestaat
    logo_html = ""
    if os.path.exists("assets/logo.png"):
        img_b64 = get_img_as_base64("assets/logo.png")
        logo_html = f'<img src="data:image/png;base64,{img_b64}" style="width:48px; height:48px; border-radius:12px; object-fit:cover;">'
    else:
        logo_html = '<div style="width:48px; height:48px; background:#10b981; border-radius:12px; display:flex; align-items:center; justify-content:center; color:white; font-weight:900; font-size:1.5rem;">P</div>'

    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:15px;">
        {logo_html}
        <div>
            <div style="display:flex; align-items:center; gap:8px;">
                <h1 style="margin:0; font-size:1.5rem; line-height:1.2;">PostAi</h1>
                <span style="background:{b_color}; color:{t_color}; padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:800; border:1px solid {b_color};">{badge}</span>
                <span style="background:linear-gradient(90deg, #f59e0b, #d97706); color:white; padding:2px 8px; border-radius:99px; font-size:0.75rem; font-weight:bold;">LVL {st.session_state.level}</span>
            </div>
            <p style="margin:0; color:#6b7280; font-size:0.85rem;">Jouw AI Social Media Manager</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- BELONINGS LOGICA (MET LIVE TIMER) ---
has_reward = user_data.get("unclaimed_reward", False)
trial_end_str = user_data.get("trial_end", "")
active_feature = user_data.get("trial_feature", "")

seconds_left = 0
if trial_end_str and not is_pro:
    try:
        end_dt = datetime.datetime.strptime(trial_end_str, "%Y-%m-%d %H:%M:%S")
        seconds_left = (end_dt - datetime.datetime.now()).total_seconds()
    except: seconds_left = 0

# 1. DE LIVE TIMER BALK
if seconds_left > 0 and not is_pro:
    # Bepaal de locatie instructie
    loc_text = "in de app"
    if active_feature == "Sales Mode": loc_text = "in de <b>🎬 Studio</b> (tab Sales)"
    elif active_feature == "Product Bedenker": loc_text = "in de <b>✨ Tools</b> tab"
    elif active_feature == "Data Detective": loc_text = "in de <b>📊 Cijfers</b> tab"

    # JavaScript timer injectie
    timer_html = f"""
    <div id="fomo-bar" style="
        background: linear-gradient(90deg, #10b981 0%, #064e3b 100%); 
        color: white; 
        padding: 12px; 
        text-align: center; 
        font-weight: bold; 
        border-radius: 0 0 12px 12px; 
        margin-top: -1rem; 
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
        font-family: sans-serif; font-size: 0.9rem;
    ">
        ⚡ <b>SUPERPASS ACTIEF:</b> {active_feature} &nbsp;|&nbsp; 👉 Vind het {loc_text} &nbsp;|&nbsp; ⏳ <span id="timer">Laden...</span>
    </div>

    <script>
    var timeLeft = {int(seconds_left)};
    var timerElement = document.getElementById("timer");
    
    var countdown = setInterval(function() {{
        if (timeLeft <= 0) {{
            clearInterval(countdown);
            document.getElementById("fomo-bar").style.display = "none";
        }} else {{
            var hours = Math.floor(timeLeft / 3600);
            var minutes = Math.floor((timeLeft % 3600) / 60);
            var seconds = Math.floor(timeLeft % 60);
            
            var h = hours < 10 ? "0" + hours : hours;
            var m = minutes < 10 ? "0" + minutes : minutes;
            var s = seconds < 10 ? "0" + seconds : seconds;
            
            if (timerElement) {{ timerElement.innerHTML = h + ":" + m + ":" + s; }}
            timeLeft -= 1;
        }}
    }}, 1000);
    </script>
    """
    st.markdown(timer_html, unsafe_allow_html=True)

# 2. DE BELONINGS POPUP (CLEAN & PRO)
@st.dialog("🎁 Cadeautje voor jou")
def show_reward_popup():
    streak = st.session_state.streak
    st.markdown(f"""
    <div style="text-align:center; padding-bottom:20px;">
        <h2 style="margin:0; font-size:1.8rem;">🎉 {streak} Dagen Streak!</h2>
        <p style="color:#555; font-size:1rem; margin-top:10px; line-height:1.5;">
            Wat goed bezig! Als beloning mag je <b>24 uur lang</b> een PRO-functie gratis gebruiken.
            <br>Welke kies je?
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""<style>.reward-card-container { background-color: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; text-align: center; height: 200px; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); } .reward-icon { font-size: 2.5rem; margin-bottom: 10px; } .reward-title { font-weight: 800; font-size: 1.1rem; color: #111827; margin-bottom: 5px; } .reward-desc { font-size: 0.85rem; color: #6b7280; line-height: 1.4; } .pop-tag { background-color: #ecfdf5; color: #047857; font-size: 0.7rem; font-weight: 700; padding: 4px 8px; border-radius: 99px; margin-bottom: 10px; }</style>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3, gap="small")
    
    with c1:
        st.markdown("""
        <div class="reward-card-container" style="border-color: #10b981; background-color: #fafffd;">
            <div class="pop-tag">🔥 Populair</div>
            <div class="reward-icon">💸</div>
            <div class="reward-title">Sales Mode</div>
            <div class="reward-desc">Zet kijkers om in betalende klanten.</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Activeer Sales", type="primary", use_container_width=True):
            end = (datetime.datetime.now() + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            auth.save_progress(unclaimed_reward=False, active_trial_feature="Sales Mode", trial_end_time=end)
            st.balloons(); st.rerun()

    with c2:
        st.markdown("""
        <div class="reward-card-container">
            <div style="height:24px"></div>
            <div class="reward-icon">📦</div>
            <div class="reward-title">Product Idee</div>
            <div class="reward-desc">Laat AI een digitaal product bedenken.</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Kies Product", use_container_width=True):
            end = (datetime.datetime.now() + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            auth.save_progress(unclaimed_reward=False, active_trial_feature="Product Bedenker", trial_end_time=end)
            st.balloons(); st.rerun()

    with c3:
        st.markdown("""
        <div class="reward-card-container">
            <div style="height:24px"></div>
            <div class="reward-icon">📈</div>
            <div class="reward-title">Cijfers</div>
            <div class="reward-desc">Analyseer je data en ontdek patronen.</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Kies Data", use_container_width=True):
            end = (datetime.datetime.now() + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            auth.save_progress(unclaimed_reward=False, active_trial_feature="Data Detective", trial_end_time=end)
            st.balloons(); st.rerun()
    
    st.markdown("<div style='text-align:center; margin-top:20px; font-size:0.8rem; color:#9ca3af;'>⏳ Je toegang start direct na het klikken.</div>", unsafe_allow_html=True)

if has_reward and not is_pro: show_reward_popup()

# --- RENDER CUSTOM HEADER ---
render_custom_header()

# --- ONBOARDING ---
if not st.session_state.user_niche:
    st.markdown("---")
    with st.container(border=True):
        st.markdown("### 👋 Welkom! Even voorstellen...")
        st.info("Ik ben PostAi, jouw persoonlijke social media strateeg. Ik help je groeien, stap voor stap.")
        
        st.markdown("**Waar wil je bekend om worden?**")
        niche_in = st.text_input("Jouw Niche / Onderwerp:", placeholder="bv. Kapper, Boekhouder, Fitness Coach...", label_visibility="collapsed")
        st.caption("Tip: Kies iets specifieks. Dit helpt de AI om betere teksten te schrijven.")
        
        if st.button("🚀 Start mijn reis", type="primary", use_container_width=True):
            if niche_in:
                st.session_state.user_niche = niche_in
                auth.save_progress(niche=niche_in, xp=50)
                st.rerun()
    st.stop()

# --- DASHBOARD ---
c1, c2 = st.columns([0.85, 0.15])
with c1: st.markdown(f"<div class='niche-edit-bar'><span>🎯 Je focus: <b>{niche}</b></span></div>", unsafe_allow_html=True)
with c2:
    if st.button("✏️", key="edit_niche", help="Pas je onderwerp aan"): 
        st.session_state.user_niche = ""; auth.save_progress(niche=""); st.rerun()

t_chal, t_studio, t_workflow, t_tools, t_data, t_set = st.tabs(["🚀 Challenge", "🎬 Studio", "🗂️ Workflow", "✨ Tools", "📊 Cijfers", "⚙️"])

# 1. CHALLENGE TAB
with t_chal:
    streak = st.session_state.streak
    tickets = st.session_state.golden_tickets
    col_s, col_t, col_p = st.columns(3)
    with col_s: st.markdown(f"<div style='text-align:center; padding:10px; background:#fff7ed; border-radius:10px; border:1px solid orange;'><h2 style='margin:0; color:orange;'>🔥 {streak}</h2><small>Streak Dagen</small></div>", unsafe_allow_html=True)
    with col_t: st.markdown(f"<div style='text-align:center; padding:10px; background:#fefce8; border-radius:10px; border:1px solid #facc15;'><h2 style='margin:0; color:#ca8a04;'>🎫 {tickets}</h2><small>Tickets</small></div>", unsafe_allow_html=True)
    with col_p: st.markdown(f"<div style='text-align:center; padding:10px; background:#f0fdf4; border-radius:10px; border:1px solid #10b981;'><h2 style='margin:0; color:#10b981;'>{st.session_state.xp}</h2><small>XP Punten</small></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.9rem; color:#1e40af; background:#eff6ff; padding:15px; border-radius:8px; border-left: 4px solid #3b82f6; margin-bottom:20px;">
    👋 <b>Hoe werkt de Challenge?</b><br>
    Geen inspiratie? Geen zorgen. Volg gewoon dit stappenplan. Elke dag krijg je <b>1 concrete opdracht</b>. 
    De AI schrijft het script voor je. Jij hoeft het alleen maar te filmen.
    </div>""", unsafe_allow_html=True)

    col_main, col_sidebar = st.columns([0.65, 0.35], gap="medium")
    current_day = st.session_state.challenge_day
    tasks = ai_coach.get_challenge_tasks()
    task_today = tasks.get(current_day, f"Dag {current_day}: Verrassing!")
    pro_tip = ai_coach.get_daily_pro_tip(current_day)

    with col_main:
        with st.container(border=True):
            st.markdown(f"#### 📅 Vandaag: Dag {current_day}")
            st.markdown(f"**Opdracht:** {task_today}")
            
            is_locked_day = current_day > 3 and not is_pro
            if not is_locked_day:
                st.markdown("**Hoe wil je dit maken?**")
                chal_format = st.radio("Format", ["🎥 Video (Filmen)", "📸 Foto Slider (Carrousel)"], horizontal=True, label_visibility="collapsed")
                btn_label = "✨ Schrijf Video Script" if "Video" in chal_format else "✨ Schrijf Foto Teksten"
                if st.button(f"{btn_label}", type="primary", use_container_width=True):
                    with st.spinner(f"De AI maakt je {chal_format}..."):
                        script = ai_coach.generate_challenge_script(current_day, task_today, niche, chal_format)
                        st.session_state.chal_script = script
                        st.rerun()
            else:
                st.info("🚀 **Level 1-3 voltooid!** De AI-hulp is nu beperkt tot PRO leden.")
                if tickets > 0:
                    st.markdown(f"<div style='background:#fefce8; padding:10px; border:1px solid #facc15; border-radius:5px; margin-bottom:10px;'>🎫 <b>Je hebt {tickets} Golden Ticket(s)!</b><br>Wil je er eentje gebruiken voor dit level?</div>", unsafe_allow_html=True)
                    if st.button("🎫 Gebruik Ticket & Schrijf", type="primary", use_container_width=True):
                        st.session_state.golden_tickets -= 1
                        auth.save_progress(golden_tickets=st.session_state.golden_tickets)
                        with st.spinner("Ticket geaccepteerd! Schrijven..."):
                            script = ai_coach.generate_challenge_script(current_day, task_today, niche, "Video")
                            st.session_state.chal_script = script
                            st.rerun()
                else:
                    ui.render_locked_section("AI Script Generator", "Upgrade naar PRO of gebruik een Golden Ticket.")
                
                st.markdown("---")
                st.caption("Geen geld/tickets? Doe het zelf om je streak te behouden.")
                if st.button("😓 Ik heb het zelf bedacht & gefilmd", type="secondary", use_container_width=True):
                    st.balloons()
                    today_str = str(datetime.datetime.now().date())
                    last_active = user_data.get("last_active", "")
                    if today_str != last_active:
                        st.session_state.streak += 1
                        if st.session_state.streak % 5 == 0: auth.save_progress(unclaimed_reward=True)
                    st.session_state.challenge_day += 1
                    st.session_state.xp += 25
                    auth.save_progress(xp=st.session_state.xp, challenge_day=st.session_state.challenge_day, streak=st.session_state.streak, last_active=today_str)
                    st.rerun()

        if not is_pro:
            st.markdown(f"""
            <div style="position:relative; margin-top:15px; padding:15px; background:#f3f4f6; border-radius:10px; border:1px dashed #9ca3af; overflow:hidden;">
                <div style="filter:blur(5px); opacity:0.6; user-select:none;">
                    <b>💡 Geheime Pro Tip:</b><br>
                    Zorg dat je bij deze video altijd de camera op ooghoogte houdt en gebruik de regel van derden voor 30% meer retentie.
                </div>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); font-weight:bold; color:#ef4444; background:rgba(255,255,255,0.9); padding:5px 10px; border-radius:5px; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
                    🔒 Upgrade voor de Tip
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.info(f"💡 **Pro Tip:** {pro_tip}")

        if "chal_script" in st.session_state:
            st.success("💡 Je script staat klaar!")
            st.markdown(f"""
            <div style="font-size:0.9rem; background:#f0fdf4; color:#166534; padding:10px; border-radius:8px; margin-bottom:10px;">
            🧠 <b>AI Analyse:</b><br>
            Dit script is geoptimaliseerd voor de {niche}-doelgroep en gebruikt psychologische triggers om aandacht te houden.
            </div>""", unsafe_allow_html=True)
            with st.expander("Bekijk Script", expanded=True):
                st.markdown(st.session_state.chal_script)
                if st.button("✅ Gefilmd! (+50 XP)", type="secondary", use_container_width=True):
                    st.balloons()
                    today_str = str(datetime.datetime.now().date())
                    last_active = user_data.get("last_active", "")
                    if today_str != last_active:
                        st.session_state.streak += 1
                        if st.session_state.streak % 5 == 0: auth.save_progress(unclaimed_reward=True)
                    st.session_state.challenge_day += 1
                    st.session_state.xp += 50
                    auth.save_progress(xp=st.session_state.xp, challenge_day=st.session_state.challenge_day, streak=st.session_state.streak, last_active=today_str, golden_tickets=st.session_state.golden_tickets)
                    del st.session_state.chal_script
                    st.rerun()

    with col_sidebar:
        st.markdown("**Jouw Roadmap**")
        ui.render_challenge_map(current_day)
        st.markdown("---")
        st.markdown("""
        <div style="font-size:0.8rem; color:#6b7280; background:#f9fafb; padding:10px; border-radius:8px;">
        🔥 <b>Streak Regel:</b><br>
        Je streak telt <b>dagen</b>. Batchen mag, maar je streak groeit 1x per dag.
        </div>""", unsafe_allow_html=True)

# 2. STUDIO TAB
with t_studio:
    st.markdown(f"<h3 style='margin-bottom:10px;'>Vrij Video Maken</h3>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown("#### 1. Wat is je doel?")
        mode = st.radio(
            "Doel", 
            ["👀 Viral gaan (Meer views)", "💸 Geld Verdienen (Verkoop)"], 
            horizontal=True, 
            label_visibility="collapsed",
            help="Kies 'Viral' voor bereik of 'Geld' als je iets wilt verkopen."
        )

        if mode == "👀 Viral gaan (Meer views)":
            if st.button("🔥 Gebruik 'Trend van Vandaag' (Snel & Makkelijk)", use_container_width=True, type="secondary", help="De AI bedenkt een script op basis van een huidige TikTok trend."):
                with st.spinner("Trend zoeken..."):
                    script = ai_coach.generate_script("Trending: 'Of Course' Challenge", "Vlog", "Humor", f"Wij zijn {niche}-experts, natuurlijk...", "Volg voor meer", niche)
                    st.session_state.last_script = script
                    st.rerun()
            
            st.markdown("---")
            st.markdown("#### 2. Waar gaat het over?")
            template = st.selectbox(
                "💡 Kies een succes-formule (Optioneel):", 
                ["✨ Ik heb zelf een idee...", "🚫 Mythe Ontkrachten", "📚 How-To / Uitleg", "😲 Reactie / Green Screen", "🗣️ Rant / Mening"],
                help="Templates zijn bewezen video-structuren die goed werken."
            )

            col_in, col_dice = st.columns([0.85, 0.15], vertical_alignment="bottom")
            with col_in:
                ph = "Waar gaat je video over?"
                if "Mythe" in template: ph = f"Welke onzin over {niche} geloven mensen?"
                elif "How-To" in template: ph = f"Wat wil je uitleggen over {niche}?"
                default_val = st.session_state.get("idea_input", "")
                topic = st.text_input("Onderwerp:", value=default_val, placeholder=ph)
            with col_dice:
                if st.button("🎲", help="Geef mij een willekeurig idee"): 
                    st.session_state.idea_input = random.choice([f"Grootste fout in {niche}", f"Handige tool voor {niche}", "Snelle tip", "Eerlijke mening"]); st.rerun()

            st.markdown("#### 3. De details")
            c_fmt, c_tone = st.columns(2)
            with c_fmt: 
                vid_format = st.selectbox(
                    "🎥 Hoe ga je filmen?", 
                    ["🗣️ Ik vertel (Talking Head)", "🟩 Ik laat iets zien (Green Screen)", "📸 Vlog (Sfeerbeelden)", "📝 Lijstje (Opsomming)"],
                    help="Kies wat de kijker ziet."
                )
            with c_tone: 
                tone = st.selectbox(
                    "🎭 Wat is de sfeer?", 
                    ["⚡ Energiek & Snel", "😌 Rustig & Uitleggend", "😂 Grappig", "🎓 Serieus & Zakelijk"],
                    help="Hoe wil je overkomen?"
                )

            hooks = ai_coach.get_viral_hooks_library()
            selected_hook = st.selectbox(
                "🪝 Kies je openingszin (Hook)", 
                hooks,
                help="De eerste 3 seconden zijn het belangrijkst."
            )
            cta_type = st.selectbox(
                "🎯 Wat moet de kijker doen?", 
                ["➕ Mij gaan volgen", "💬 Een reactie plaatsen", "↗️ De video delen"],
                help="De actie aan het einde van de video."
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✨ Schrijf Viral Script", type="primary", use_container_width=True):
                if not is_pro and st.session_state.get("daily_gen_count", 0) >= 1:
                    st.error("⚠️ Je hebt je gratis script voor vandaag gehad. Upgrade naar PRO.")
                else:
                    with st.spinner("De regisseur schrijft..."):
                        final_hook = selected_hook.replace("{onderwerp}", topic if topic else "dit")
                        script = ai_coach.generate_script(topic, vid_format, tone, final_hook, cta_type, niche)
                        st.session_state.last_script = script
                        st.session_state.current_topic = topic if topic else "Viral Video"
                        st.session_state.daily_gen_count = st.session_state.get("daily_gen_count", 0) + 1
                        st.session_state.xp += 10
                        auth.save_progress(xp=st.session_state.xp); st.rerun()

        else: # Sales Mode
            st.markdown("<div style='background:#ecfdf5; border-left:4px solid #10b981; padding:10px; font-size:0.9rem;'>💰 <b>Cashflow Modus</b>: Zet kijkers om in betalende klanten.</div>", unsafe_allow_html=True)
            col_p, col_pain = st.columns(2)
            with col_p: 
                product_name = st.text_input("Wat verkoop je?", placeholder=f"bv. Mijn {niche} E-book...")
            with col_pain: 
                pain_point = st.text_input("Welk probleem los je op?", placeholder=f"bv. Problemen met {niche}...")
            
            sales_angle = st.selectbox(
                "🧠 Verkoop Strategie", 
                ["😱 Pijn & Oplossing (PAS)", "📦 Demo (Laat het zien)", "⭐ Testimonial (Klantverhaal)"],
                help="Kies hoe je het product wilt presenteren."
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            has_ticket = st.session_state.golden_tickets > 0
            # CHECK FOR ACCESS (PRO or TRIAL)
            if auth.has_access("Sales Mode"):
                if st.button("💸 Schrijf Sales Script", type="primary", use_container_width=True):
                    if not product_name: st.error("Vul in wat je verkoopt.")
                    else:
                        with st.spinner("De copywriter schrijft..."):
                            script = ai_coach.generate_sales_script(product_name, pain_point, sales_angle, niche)
                            st.session_state.last_script = script
                            st.session_state.current_topic = f"Sales: {product_name}"
                            st.session_state.xp += 20
                            auth.save_progress(xp=st.session_state.xp); st.rerun()
            else:
                if has_ticket:
                    st.info(f"🎫 Je hebt {st.session_state.golden_tickets} Golden Ticket(s). Wil je er één inzetten?")
                    if st.button("🎫 Gebruik Ticket & Schrijf", type="primary", use_container_width=True):
                        st.session_state.golden_tickets -= 1
                        auth.save_progress(golden_tickets=st.session_state.golden_tickets)
                        with st.spinner("Ticket geaccepteerd! Schrijven..."):
                            script = ai_coach.generate_sales_script(product_name, pain_point, sales_angle, niche)
                            st.session_state.last_script = script
                            st.rerun()
                else:
                    ui.render_locked_section("Cashflow Script", "Verdien 5 dagen streak om een Superpass te krijgen.")

    if "last_script" in st.session_state:
        st.success("💡 Script is klaar!")
        
        st.markdown(f"""
        <div style="font-size:0.9rem; background:#f0fdf4; color:#166534; padding:10px; border-radius:8px; margin-bottom:10px;">
        🧠 <b>AI Analyse:</b><br>
        Dit script is geoptimaliseerd voor de {niche}-doelgroep en gebruikt psychologische triggers om aandacht te houden.
        </div>""", unsafe_allow_html=True)

        c_save, c_audit = st.columns(2)
        with c_save:
            if st.button("💾 Opslaan in Archief", type="secondary", use_container_width=True):
                if not is_pro: st.toast("🔒 Alleen PRO")
                else:
                    auth.save_script_to_library(st.session_state.get("current_topic", "Script"), st.session_state.last_script, "Viral" if mode.startswith("👀") else "Sales")
                    st.toast("✅ Opgeslagen!")
        with c_audit:
            # CHECK FOR ACCESS (PRO or TRIAL)
            if auth.has_access("Viral Audit"):
                if st.button("🔍 Check Viraliteit (Audit)", type="secondary", use_container_width=True):
                    with st.spinner("Checken..."):
                        st.session_state.script_score = ai_coach.audit_script(st.session_state.last_script, niche)
                        st.rerun()
            else:
                if st.button("🔍 Check Viraliteit (Locked)", disabled=True, use_container_width=True): pass

        if "script_score" in st.session_state:
            s = st.session_state.script_score
            st.info(f"**Score: {s.get('score')}/100** - {s.get('verdict')}")

        t1, t2 = st.tabs(["📄 Script", "🎥 Teleprompter"])
        with t1: st.markdown(st.session_state.last_script)
        with t2:
            clean = st.session_state.last_script.replace("|", "").replace("---", "")
            st.markdown(f"<div style='font-size:22px; line-height:1.6; background:#f3f4f6; padding:20px; border-radius:10px;'>{clean}</div>", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("✅ Gefilmd (+10 XP)", type="secondary"):
            st.session_state.streak += 1; st.session_state.xp += 10;
            auth.save_progress(streak=st.session_state.streak, xp=st.session_state.xp, last_active=str(datetime.datetime.now().date()))
            st.balloons()
            del st.session_state.last_script
            if "script_score" in st.session_state: del st.session_state.script_score
            st.rerun()

# 3. WORKFLOW TAB
with t_workflow:
    st.markdown("### 🗂️ Script Archief")
    st.caption("Hier vind je al je opgeslagen scripts terug. Handig voor batchen!")
    if not is_pro: ui.render_locked_section("Content Workflow", "Beheer al je scripts op één plek.")
    else:
        library = auth.get_user_library()
        if not library: st.info("Je bibliotheek is leeg. Ga naar de Studio om iets te maken.")
        for s in library:
            with st.expander(f"{s.get('status')} | {s.get('topic')}"):
                st.markdown(s.get('content'))
                if st.button("🗑️ Verwijder", key=s['id']): auth.delete_script(s['id']); st.rerun()

# 4. TOOLS TAB
with t_tools:
    st.markdown("### 🛠️ Creator Tools")
    
    with st.expander("🔥 Idee Checker (Gratis)", expanded=True):
        st.info("Twijfel je over een video idee? De AI voorspelt of het gaat werken.")
        idea = st.text_input("Jouw idee:", placeholder=f"bv. Iets met {niche}...")
        if st.button("Check"): 
            st.session_state.idea_score = ai_coach.check_viral_potential(idea, niche)
        if "idea_score" in st.session_state:
            d = st.session_state.idea_score
            st.info(f"Score: {d.get('score')}\nTip: {d.get('tip')}")

    # HIER IS DE GEUPDATE PASSIEF INKOMEN TOOL (MET PDF & SPINNER)
    with st.expander("📦 Passief Inkomen Bedenker (PRO)"):
        # CHECK FOR ACCESS (PRO or TRIAL)
        if not auth.has_access("Product Bedenker"):
            ui.render_locked_section("Business Plan", "Laat AI je product bedenken. Verdien 5 dagen streak voor een Superpass.")
        else:
            st.markdown("### 🧠 Laat de AI je Masterplan schrijven")
            st.write(f"De AI bedenkt een compleet **High-End Business Plan** voor de {niche} markt.")
            
            target = st.text_input("Voor wie is het?", placeholder="bv. Beginners, Drukke moeders...")
            
            if st.button("🚀 Genereer Masterplan"):
                if not target: st.error("Vul een doelgroep in.")
                else:
                    # DEZE SPINNER IS TOEGEVOEGD VOOR DUIDELIJKHEID
                    with st.spinner("De business coach schrijft je plan (dit duurt +/- 15 sec)..."):
                        st.session_state.biz_plan = ai_coach.generate_digital_product_plan(niche, target)
            
            if "biz_plan" in st.session_state:
                st.success("✅ Je Business Plan is klaar!")
                st.markdown(st.session_state.biz_plan)
                
                pdf_data = create_pdf(st.session_state.biz_plan)
                if pdf_data:
                    st.download_button("📥 Download als PDF", data=pdf_data, file_name="masterplan.pdf", mime="application/pdf", type="primary")
                else:
                    st.download_button("📥 Download als Tekst", data=st.session_state.biz_plan, file_name="masterplan.txt")

    with st.expander("🎬 5 Video's in 1 klik (PRO)"):
        if not is_pro: ui.render_locked_section("Serie Generator", "Maak 5 video's in 1 klik.")
        else:
            st.write("Maak een reeks die op elkaar aansluit (blijven kijken!).")
            topic = st.text_input("Serie onderwerp:")
            if st.button("Bouw Serie"): st.markdown(ai_coach.generate_series_ideas(topic, niche))

    with st.expander("🕵️ Viral Video Nadoen (PRO)"):
        if not is_pro: ui.render_locked_section("Format Dief", "Kopieer succesformules.")
        else:
            st.write("Plak een tekst van een ander, de AI maakt er iets nieuws van voor JOU.")
            other = st.text_area("Script concurrent:")
            mine = st.text_area("Mijn onderwerp:")
            if st.button("Herschrijf"): st.markdown(ai_coach.steal_format_and_rewrite(other, mine, niche))

    with st.expander("📅 Weekplanner (PRO)"):
        if not is_pro: ui.render_locked_section("Weekplanner", "7 dagen content in 1 klik.")
        else:
            st.write("Krijg een planning voor de hele week.")
            # DEZE SPINNER IS TOEGEVOEGD
            if st.button("Maak Planning"): 
                with st.spinner("De AI plant je week in..."):
                    st.markdown(ai_coach.generate_weekly_plan(niche))

# 5. DATA TAB
with t_data:
    st.markdown("### 📊 Jouw Cijfers")
    
    with st.expander("❓ Hoe kom ik aan data?"):
        st.write("Ga naar TikTok op je computer -> Instellingen -> Data Downloaden (CSV).")

    up = st.file_uploader("Upload TikTok Data (CSV)", type=['csv', 'xlsx'])
    if up: st.session_state.df = data_loader.load_file(up)
    if not st.session_state.df.empty:
        df = analytics.clean_data(st.session_state.df)
        kpis = analytics.calculate_kpis(df)
        st.markdown("#### 🕵️ AI Data Detective (PRO)")
        # CHECK FOR ACCESS (PRO or TRIAL)
        if not auth.has_access("Data Detective"):
            ui.render_locked_section("Data Analyse", "Laat AI patronen vinden. Verdien 5 dagen streak voor een Superpass.")
        else:
            if st.button("🔍 Analyseer mijn data"):
                with st.spinner("Analyseren..."):
                    insights = ai_coach.analyze_data_patterns(f"Views: {kpis['Views'].sum()}", niche)
                    st.success("Klaar!"); st.info(insights.get('strategy_tip'))
        st.metric("Totaal Views", f"{kpis['Views'].sum()/1000:.1f}k")
        st.bar_chart(analytics.get_best_posting_time(df), x="Uur", y="Views", color="#10b981")
    else:
        if st.button("Laad Voorbeeld Data"): st.session_state.df = data_loader.load_demo_data(); st.rerun()

# 6. SETTINGS
with t_set:
    if not is_pro:
        st.markdown("### 🔓 Word een Pro Creator")
        with st.container(border=True):
            st.markdown("#### Upgrade naar PostAi PRO 🚀")
            st.markdown("De tool voor serieuze creators.")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("❌ **Max 1 script** per dag")
                st.markdown("❌ **Geen** Sales Modus")
                st.markdown("❌ **Geen** Product Bedenker")
            with c2:
                st.markdown("✅ **Onbeperkt** Scripts")
                st.markdown("✅ **Geld Verdienen** Tools")
                st.markdown("✅ **Volledige** Roadmap")
            
            st.info("💡 Verkoop 1 E-book en je hebt je abonnement eruit.")
            st.link_button("👉 Start 14 Dagen Gratis", "https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2", type="primary", use_container_width=True)
        
        with st.expander("Heb je al een code?"):
            c = st.text_input("Code")
            if st.button("Activeer"): auth.activate_pro(c)
    else:
        st.success("Je bent PRO lid! 🚀")
        if st.button("Uitloggen"): st.session_state.clear(); st.rerun()

    # --- TIJDELIJKE TEST TOOLS ---
    st.markdown("---")
    st.markdown("### 🛠️ Developer Test Zone")
    col_test1, col_test2, col_test3 = st.columns(3)
    with col_test1:
        if st.button("🧪 Zet Streak op 4"):
            st.session_state.license_key = "TEST_USER_123"
            auth.save_progress(streak=4, challenge_day=4, unclaimed_reward=False, golden_tickets=0)
            st.rerun()
    with col_test2:
        if st.button("🎁 Forceer Popup NU"):
            st.session_state.license_key = "TEST_USER_123"
            auth.save_progress(streak=5, unclaimed_reward=True, active_trial_feature=None)
            st.rerun()
    with col_test3:
        if st.button("🔄 Hard Reset"): st.session_state.clear(); st.rerun()

ui.inject_chat_widget(auth.get_secret("CHAT_SERVER_URL", "https://chatbot.com"))