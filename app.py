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
st.set_page_config(page_title="PostAi - Jouw persoonlijke AI TikTok Coach", page_icon="assets/logo.png", layout="centered", initial_sidebar_state="collapsed")

# --- LEMONSQUEEZY AFFILIATE TRACKING ---
components.html("""
<script>
    window.lemonSqueezyAffiliateConfig = { store: "postaiapp" };
</script>
<script src="https://lmsqueezy.com/affiliate.js" defer></script>
""", height=0, width=0)

# Style laden
ui.inject_style_and_hacks(brand_color="#10b981")

# --- 2. PUBLIEKE LINKS LOGICA ---
qp = st.query_params
target_view = qp.get("view", "")

if target_view in ["privacy", "terms"]:
    st.session_state.page = target_view
    st.session_state.license_key = "public_visitor"
    for k in ["user_niche", "xp", "streak", "level", "golden_tickets"]:
        if k not in st.session_state: st.session_state[k] = 0
else:
    auth.init_session()

# --- 3. NAVIGATIE FUNCTIES ---
def go_home(): st.session_state.page = "home"
def go_studio(): st.session_state.page = "studio"
def go_tools(): st.session_state.page = "tools"
def go_stats(): st.session_state.page = "stats"
def go_settings(): st.session_state.page = "settings"

# --- 4. AUTH CHECK ---
if target_view not in ["privacy", "terms"]:
    if not auth.is_authenticated():
        auth.render_landing_page()
        st.stop()

# DATA LADEN
if target_view not in ["privacy", "terms"] and "xp" not in st.session_state:
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

# PRO STATUS
if target_view in ["privacy", "terms"]:
    is_pro = False
    niche = ""
else:
    is_pro = auth.is_pro()
    niche = st.session_state.user_niche
    ai_coach.init_ai()

# --- HELPER FUNCTIES ---
def check_feature_access(feature_key):
    if is_pro: return True
    active_feat = st.session_state.get("active_trial_feature", "")
    end_time_str = st.session_state.get("trial_end_time", "")
    if active_feat == feature_key and end_time_str:
        try:
            end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime.now() < end_time: return True
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
        else:
            st.toast(f"+{allowed} XP")
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

@st.cache_data(show_spinner=False)
def load_logo():
    if os.path.exists("assets/logo.png"):
        with open("assets/logo.png", "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return "https://via.placeholder.com/50/10b981/ffffff?text=P"

# --- 5. HEADER ---
col_head, col_set = st.columns([0.85, 0.15])
with col_head:
    logo_src = load_logo()
    badge = "PRO" if is_pro else "DEMO"
    badge_style = "background:#dcfce7; color:#166534; border:1px solid #bbf7d0;" if is_pro else "background:#eff6ff; color:#1e40af; border:1px solid #dbeafe;"
    
    st.markdown(f"""
    <div class="header-container">
        <div class="header-logo"><img src="{logo_src}"></div>
        <div class="header-text">
            <div class="header-title">PostAi <span style="font-size:0.6rem; padding:2px 6px; border-radius:4px; vertical-align:middle; margin-left:12px; {badge_style}">{badge}</span></div>
            <p class="header-subtitle">Jouw persoonlijke AI TikTok Coach</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_set:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("⚙️", key="head_set", type="secondary", help="Instellingen en abonnement"): 
        go_settings(); st.rerun()

st.markdown("---")

# --- AANGEPAST BLOK: NICHE CHECK ---
if st.session_state.page not in ["privacy", "terms"]:
    if not st.session_state.user_niche:
        st.info("Welkom! Wat is je niche?")
        n = st.text_input("Niche:", placeholder="Bijvoorbeeld: Kapper")
        if st.button("Start", type="primary"):
            if n: st.session_state.user_niche = n; auth.save_progress(niche=n, xp=50); st.rerun()
        st.stop() 

# ==========================
# 🏠 HOME DASHBOARD
# ==========================
if st.session_state.page == "home":
    display_niche = niche.title() if niche else "Creator"
    st.markdown(f"### 👋 Hi {display_niche} Creator!")
    
    # METRICS MET TOOLTIPS
    metrics_html = f"""
    <div class="metrics-strip" style="gap:5px; margin-bottom:15px;">
        <div class="metric-card" style="padding: 8px;" title="Je Streak: Aantal dagen op rij dat je actief bent. Houd dit vol!">
            <div class="metric-val" style="color:#ef4444; font-size:1.2rem;">{st.session_state.streak}</div>
            <div class="metric-lbl" style="font-size:0.7rem;">🔥 Dagen <span style="font-size:0.6rem; color:#9ca3af;">ℹ</span></div>
        </div>
        <div class="metric-card" style="padding: 8px;" title="Golden Tickets: Gebruik deze om PRO features voor 24 uur gratis te ontgrendelen.">
            <div class="metric-val" style="color:#f59e0b; font-size:1.2rem;">{st.session_state.golden_tickets}</div>
            <div class="metric-lbl" style="font-size:0.7rem;">🎫 Tickets <span style="font-size:0.6rem; color:#9ca3af;">ℹ</span></div>
        </div>
        <div class="metric-card" style="padding: 8px;" title="Experience Points: Verdien XP door acties te doen. Bij 100 XP ga je een Level omhoog en krijg je een Ticket.">
            <div class="metric-val" style="color:#3b82f6; font-size:1.2rem;">{st.session_state.xp}</div>
            <div class="metric-lbl" style="font-size:0.7rem;">🎁 XP <span style="font-size:0.6rem; color:#9ca3af;">ℹ</span></div>
        </div>
    </div>"""
    st.markdown(metrics_html, unsafe_allow_html=True)

    if st.button("🚨 PANIC BUTTON: IK HEB NU EEN IDEE NODIG!", use_container_width=True, type="primary", help="Klik hier als je GEEN inspiratie hebt en NU iets moet posten."):
        if auth.check_ai_limit():
            with st.spinner("🚀 AI scant viral kansen..."):
                script = ai_coach.generate_instant_script(niche)
                auth.track_ai_usage()
                st.session_state.last_script = script
                go_studio(); st.rerun()
        else:
             st.error(f"🛑 Daglimiet bereikt ({auth.get_ai_usage_text()}).")

    # --- SLIMME TREND LOGICA (MET WERKEND VERVERSEN) ---
    if "trend_version" not in st.session_state:
        st.session_state.trend_version = random.randint(1, 1000)

    if "niche_trend" not in st.session_state:
        if niche:
            with st.spinner(f"🔥 Trends voor {niche} zoeken..."):
                st.session_state.niche_trend = ai_coach.get_personalized_trend(niche, st.session_state.trend_version)
        else:
            st.session_state.niche_trend = ai_coach.get_weekly_trend()
            
    trend = st.session_state.niche_trend

    st.markdown(f"""
    <div class="trend-box" style="margin-top: 15px;" title="Dit is een trending video format speciaal voor jouw niche.">
        <div style="display:flex; justify-content:space-between; align-items:center;">
             <div class="trend-label">🔥 Trend voor jou</div>
        </div>
        <div class="trend-title">{trend.get('title', 'Trend')}</div>
        <div style="font-size:0.9rem; margin-top:5px; margin-bottom:10px;">{trend.get('desc', '')}</div>
        <div style="font-size:0.8rem; background:rgba(255,255,255,0.2); padding:5px 10px; border-radius:6px; margin-bottom:10px;">🎵 {trend.get('sound', '')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    c_trend1, c_trend2 = st.columns([1, 4])
    with c_trend1:
        if st.button("🔄", help="Zoek een andere trend als je deze niks vindt."):
            if auth.check_ai_limit():
                # FIX: Versie omhoog, cache legen, herladen
                st.session_state.trend_version += 1
                if "niche_trend" in st.session_state: del st.session_state.niche_trend
                auth.track_ai_usage()
                st.rerun()
            else: st.error("Op.")
    with c_trend2:
        if st.button("✍️ Gebruik deze trend", use_container_width=True, type="primary", help="Maak direct een script op basis van deze trend."):
            st.session_state.last_script = f"**Video Concept: {trend.get('title')}**\n\n**Geluid:** {trend.get('sound')}\n\n**Visueel:** {trend.get('desc')}\n\n**Script:**\n(Jouw tekst hier...)"
            st.session_state.generated_img = f"Een shot passend bij de trend: {trend.get('title')}"
            st.session_state.generated_img_url = ai_coach.generate_viral_image(trend.get('title'), "Trendy", niche)
            go_studio()
            st.rerun()

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("<div class='nav-card'><div class='nav-icon'>📅</div><div class='nav-title'>Jouw missie</div><div class='nav-desc'>Bootcamp dagtaak.</div></div>", unsafe_allow_html=True)
        if st.button("Start missie", key="btn_boot", use_container_width=True, type="primary", help="Jouw dagelijkse opdracht om te groeien op TikTok."): st.session_state.page = "bootcamp"; st.rerun()
        st.markdown("<div class='nav-card'><div class='nav-icon'>📈</div><div class='nav-title'>Check groei</div><div class='nav-desc'>Bekijk je cijfers.</div></div>", unsafe_allow_html=True)
        if st.button("Bekijk cijfers", key="btn_stats", use_container_width=True, type="primary", help="Analyseer screenshots van je TikTok statistieken."): go_stats(); st.rerun()
    with col_b:
        st.markdown("<div class='nav-card'><div class='nav-icon'>✨</div><div class='nav-title'>Nieuw script</div><div class='nav-desc'>Open de studio.</div></div>", unsafe_allow_html=True)
        if st.button("Open studio", key="btn_studio", use_container_width=True, type="primary", help="Maak een script, gebruik de teleprompter of genereer ideeën."): go_studio(); st.rerun()
        st.markdown("<div class='nav-card'><div class='nav-icon'>🚀</div><div class='nav-title'>Viral remix</div><div class='nav-desc'>Steel een format.</div></div>", unsafe_allow_html=True)
        if st.button("Open tools", key="btn_tools", use_container_width=True, type="primary", help="Extra tools: Bio generator, Remix tool, Weekplanner, etc."): go_tools(); st.rerun()

# ==========================
# 🚀 BOOTCAMP
# ==========================
if st.session_state.page == "bootcamp":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 🚀 Bootcamp")
    if st.session_state.weekly_goal == 0:
        with st.container(border=True):
            st.markdown("### 🎯 Weekdoel")
            goal = st.slider("Aantal video's:", 1, 7, 3, help="Hoeveel videos wil je deze week posten?")
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
            if st.button("✨ Schrijf script", use_container_width=True, type="primary", help="Laat de AI een script schrijven voor deze opdracht."):
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
                if st.button("🎫 Gebruik Ticket", type="primary", help="Gebruik een ticket om deze dagtaak te openen."):
                    if auth.use_ticket():
                        if auth.check_ai_limit():
                            with st.spinner("Ticket valideren..."):
                                st.session_state.chal_script = ai_coach.generate_challenge_script(current_day, task_txt, niche, "Video")
                                auth.track_ai_usage()
                                st.rerun()
                        else: st.error(f"🛑 Daglimiet bereikt.")
            elif is_pro:
                chal_format = st.radio("Format", ["🎥 Video", "📸 Foto"], horizontal=True, label_visibility="collapsed")
                if st.button("✨ Schrijf Script", use_container_width=True, type="primary", help="Laat AI het script schrijven."):
                    if auth.check_ai_limit():
                        with st.spinner("🤖 De Coach schrijft..."):
                            st.session_state.chal_script = ai_coach.generate_challenge_script(current_day, task_txt, niche, chal_format)
                            auth.track_ai_usage()
                            st.rerun()
                    else: st.error(f"🛑 Daglimiet bereikt.")
            else: ui.render_locked_section("AI Coach", "Upgrade naar PRO")

    if "chal_script" in st.session_state:
        with st.expander("📜 Jouw script", expanded=True):
            st.markdown(st.session_state.chal_script)
            st.markdown("---")
            post_link = st.text_input("Link naar TikTok video", placeholder="https://tiktok.com/...", help="Plak hier de link nadat je gepost hebt.")
            if st.button("✅ Ik heb gepost! (+50 XP)", use_container_width=True, type="primary"):
                if post_link and "http" in post_link:
                    st.balloons(); auth.handle_daily_streak(); add_xp(50)
                    st.session_state.challenge_day += 1; st.session_state.weekly_progress += 1
                    auth.save_progress(challenge_day=st.session_state.challenge_day, weekly_progress=st.session_state.weekly_progress)
                    del st.session_state.chal_script; time.sleep(2); st.rerun()
                else: st.error("Plak een geldige link!")

# ==========================
# 🎬 STUDIO
# ==========================
if st.session_state.page == "studio":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 🎬 Studio")
    
    if "last_script" in st.session_state:
        if "generated_img_url" in st.session_state and st.session_state.generated_img_url:
            c1, c2, c3 = st.columns([1, 1, 1])
            with c2: st.image(st.session_state.generated_img_url, caption="📸 Concept", width=280)

        t1, t2 = st.tabs(["Script", "Teleprompter"])
        with t1:
            st.markdown(st.session_state.last_script)
            if st.button("💾 Opslaan", type="primary", help="Bewaar dit script in je bibliotheek (Alleen PRO)."): 
                if is_pro: auth.save_script_to_library("Script", st.session_state.last_script); st.toast("Opgeslagen!")
                else: st.toast("🔒 Alleen PRO")
            if st.button("❌ Nieuw", type="secondary"): del st.session_state.last_script; st.rerun()
        
        with t2:
            st.markdown("### 🎬 Pro Teleprompter")
            c_set1, c_set2, c_set3 = st.columns([2, 2, 1])
            with c_set1: speed = st.slider("🐢 Snelheid", 0, 50, 10, help="Scroll snelheid")
            with c_set2: font_size = st.slider("🔍 Tekstgrootte", 18, 60, 32)
            with c_set3: mirror_mode = st.toggle("🪞 Spiegel", help="Spiegel de tekst voor gebruik in een fysieke prompter.")
            is_playing = st.toggle("▶️ START", value=False)
            mirror_css = "transform: scaleX(-1);" if mirror_mode else ""
            safe_script = st.session_state.last_script.replace('\n', '<br>')
            
            prompt_html = f"""
            <div id="prompter-container" style="height: 450px; overflow-y: hidden; background: #000; border-radius: 15px; position: relative; border: 4px solid #333;">
                <div id="teleprompter" style="font-size: {font_size}px; font-weight: bold; line-height: 1.5; color: #fff; padding: 50% 20px; font-family: Arial; text-align: center; {mirror_css}">
                    {safe_script}<br><br><br><br><br>
                </div>
                <div style="position: absolute; top: 45%; left: 0; right: 0; height: 10%; border-top: 2px dashed rgba(255,255,255,0.3); pointer-events: none;"></div>
            </div>
            <script>
                var container = document.getElementById("prompter-container");
                var speed = {speed}; var playing = {str(is_playing).lower()}; var currentScroll = 0;
                function scroll() {{ if (playing && speed > 0) {{ currentScroll += (speed / 5); container.scrollTop = currentScroll; }} }}
                setInterval(scroll, 50);
            </script>
            """
            components.html(prompt_html, height=500)
    else:
        tab_viral, tab_conv, tab_hook = st.tabs(["👀 Viral maker", "📈 Conversie", "🪝 Hook rater"])
        with tab_viral:
            with st.form("viral_form"):
                topic = st.text_input("Onderwerp:", help="Waar moet de video over gaan?")
                tone = st.radio("Toon:", ["⚡ Energiek", "😌 Rustig", "😂 Humor"], horizontal=True)
                fmt = st.selectbox("Format:", ["Talking head", "Vlog", "Green screen"])
                if st.form_submit_button("✨ Schrijf viral script (+10 XP)", type="primary", help="Genereer een volledig script."):
                    if auth.check_ai_limit():
                        with st.status("🚀 Bezig..."):
                            st.session_state.last_script = ai_coach.generate_script(topic if topic else "Iets leuks", fmt, tone, "verrassend", "Volg", niche)
                            st.session_state.generated_img_url = ai_coach.generate_viral_image(topic, tone, niche)
                        auth.track_ai_usage(); add_xp(10); st.rerun()
                    else: st.error(f"🛑 Daglimiet bereikt.")

        with tab_conv:
            with st.form("sales_form"):
                prod = st.text_input("Product:", help="Wat wil je verkopen?")
                pain = st.text_input("Probleem:", help="Welk probleem lost het op voor de klant?")
                if st.form_submit_button("✍️ Schrijf story", type="primary", help="Maak een script gericht op verkoop."):
                    if check_feature_access("Sales Mode"):
                        if auth.check_ai_limit():
                            with st.spinner("Bezig..."):
                                st.session_state.last_script = ai_coach.generate_sales_script(prod, pain, "Story", niche)
                                auth.track_ai_usage(); add_xp(10); st.rerun()
                        else: st.error("Daglimiet.")
                    else: st.error("Upgrade voor Sales Mode.")

        with tab_hook:
            user_hook = st.text_input("Jouw hook:", help="De eerste 3 seconden van je video (tekst of gesproken).")
            if st.button("🚀 Test & verbeter", type="primary", help="Laat AI checken of deze hook de aandacht grijpt."):
                if user_hook and auth.check_ai_limit():
                    with st.spinner("Jury overlegt..."):
                        res = ai_coach.rate_user_hook(user_hook, niche)
                        auth.track_ai_usage()
                        st.markdown(f"### Score: {res.get('score',0)}/10")
                        st.info(f"{res.get('feedback')}")
                        for alt in res.get('alternatives', []): st.write(f"🔥 {alt}")
                else: st.error("Vul iets in of daglimiet bereikt.")

# ==========================
# 🛠️ TOOLS
# ==========================
if st.session_state.page == "tools":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 🛠️ Tools")
    
    with st.expander("🧬 Bio optimalisator"):
        bio = st.text_input("Huidige bio:")
        if st.button("Verbeter bio", help="Krijg 3 betere opties voor je TikTok profieltekst."): 
            if auth.check_ai_limit():
                st.markdown(ai_coach.generate_bio_options(bio, niche))
                auth.track_ai_usage()
                
    with st.expander("🔥 Idee checker"):
        idea = st.text_input("Jouw idee:")
        if st.button("Check potentie", help="Hoe groot is de kans dat dit viraal gaat?"): 
             if auth.check_ai_limit():
                 res = ai_coach.check_viral_potential(idea, niche)
                 auth.track_ai_usage()
                 st.info(f"Score: {res['score']}/100 - {res['verdict']}")

    with st.expander("🕵️ Viral remix tool (PRO)"):
        if check_feature_access("Viral remix"):
            other = st.text_area("Plak script:", help="Plak hier de tekst van een video die je wilt namaken.")
            if st.button("🔀 Remix", help="Herschrijf dit script naar jouw niche."): 
                if auth.check_ai_limit():
                    st.markdown(ai_coach.steal_format_and_rewrite(other, "Mijn Onderwerp", niche))
                    auth.track_ai_usage()
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock Remix", key="btn_remix", help="Zet 1 Ticket in om dit 24u te gebruiken."): use_golden_ticket("Viral Remix")
            ui.render_locked_section("Viral Remix", "Steel formats.")

    with st.expander("📦 Passief inkomen (PRO)"):
        if check_feature_access("Product bedenker"):
             tgt = st.text_input("Doelgroep")
             if st.button("Genereer Plan", help="Bedenk een digitaal product om geld te verdienen."):
                 if auth.check_ai_limit():
                        plan = ai_coach.generate_digital_product_plan(niche, tgt); st.markdown(plan)
                        pdf = create_pdf(plan); auth.track_ai_usage()
                        if pdf: st.download_button("📥 PDF", data=pdf, file_name="plan.pdf", mime="application/pdf")
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock Product", key="btn_prod", help="Zet 1 Ticket in om dit 24u te gebruiken."): use_golden_ticket("Product Bedenker")
            ui.render_locked_section("Product Bedenker", "Verdien geld.")

    with st.expander("🎬 5 video's in 1 klik (PRO)"):
        if check_feature_access("Serie generator"):
            stpc = st.text_input("Onderwerp:")
            if st.button("Bouw Serie", help="Maak in één keer een 5-delige serie over dit onderwerp."): 
                if auth.check_ai_limit():
                    st.markdown(ai_coach.generate_series_ideas(stpc, niche))
                    auth.track_ai_usage()
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock Serie", key="btn_serie", help="Zet 1 Ticket in om dit 24u te gebruiken."): use_golden_ticket("Serie Generator")
            ui.render_locked_section("Serie Generator", "Binge content.")

    with st.expander("📅 Weekplanner (PRO)"):
        if check_feature_access("Weekplanner"):
            if st.button("Plan Week", help="Genereer een contentkalender voor de hele week."):
                if auth.check_ai_limit():
                    st.markdown(ai_coach.generate_weekly_plan(niche))
                    auth.track_ai_usage()
            if st.button("📥 Download ICS", help="Download voor in je agenda."):
                st.download_button("Download", ai_coach.create_ics_file(niche), "kalender.ics", "text/calendar")
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock Planner", key="btn_plan", help="Zet 1 Ticket in om dit 24u te gebruiken."): use_golden_ticket("Weekplanner")
            ui.render_locked_section("Weekplanner", "Geen stress.")

# ==========================
# 📊 STATS
# ==========================
if st.session_state.page == "stats":
    if st.button("⬅️ Terug", type="secondary"): go_home(); st.rerun()
    st.markdown("## 📊 Cijfers & analyse")
    uploaded_file = st.file_uploader("Kies je screenshot:", type=['png', 'jpg', 'jpeg'], help="Upload een screenshot van je TikTok Analytics pagina.")
    if uploaded_file and st.button("🚀 Analyseer", help="Laat AI je screenshot lezen en advies geven."):
        if auth.check_ai_limit():
            with st.spinner("🤖 Analyseren..."):
                result = ai_coach.analyze_analytics_screenshot(uploaded_file)
                auth.track_ai_usage()
                st.success("Compleet!")
                c1, c2 = st.columns(2)
                c1.metric("Views", result.get('totaal_views', '-'))
                c2.write("**Beste Video:**"); c2.caption(result.get('beste_video', '-'))
                st.info(result.get('advies', ''))
        else: st.error("Daglimiet.")

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
        voice = st.selectbox("Kies je stem:", ["De expert 🧠", "De Beste vriendin 💖", "De harde waarheid 🔥", "De grappenmaker 😂", "Custom (Gekloond) 🤖"])
        
        with st.expander("🤖 Kloon mijn stem (beta)"):
            sample = st.text_area("Plak voorbeeldtekst:", help="Plak hier een stuk tekst dat je eerder zelf geschreven hebt.")
            if st.button("🧬 Analyseer"):
                if sample and auth.check_ai_limit():
                    custom = ai_coach.analyze_writing_style(sample)
                    auth.track_ai_usage()
                    st.session_state.brand_voice = custom
                    auth.save_progress(brand_voice=custom)
                    st.success("Opgeslagen!")

        if st.button("Opslaan", type="primary"): 
            st.session_state.brand_voice = voice
            auth.save_progress(niche=new_niche, brand_voice=voice)
            st.success("Opgeslagen!")
            time.sleep(1); st.rerun()

    if is_pro:
        st.success("✅ Je bent PRO!")
    else:
        # PAYPRO LINK HIER VERVANGEN
        st.link_button("👉 Upgrade naar PRO", "https://paypro.nl/product/EN/12345", type="primary", use_container_width=True)
        
        with st.expander("Heb je al een code?"):
            c = st.text_input("Code:")
            if st.button("Activeer"): auth.activate_pro(c)