import streamlit as st
import pandas as pd
import random
import datetime
import json
import time
import os
import base64
from modules import analytics, ui, auth, ai_coach, data_loader

# --- 1. CONFIGURATIE ---
st.set_page_config(page_title="PostAi", page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")
auth.init_session()
ui.inject_style_and_hacks(brand_color="#10b981")

# --- 2. NAVIGATIE FUNCTIES ---
def go_home(): st.session_state.page = "home"
def go_studio(): st.session_state.page = "studio"
def go_tools(): st.session_state.page = "tools"
def go_stats(): st.session_state.page = "stats"
def go_settings(): st.session_state.page = "settings"
def go_privacy(): st.session_state.page = "privacy"
def go_terms(): st.session_state.page = "terms"

# --- 3. AUTH & DATA LADEN ---
if not auth.is_authenticated():
    auth.render_landing_page()
    st.stop()

user_data = auth.load_progress()

# State Variabelen
if "page" not in st.session_state: st.session_state.page = "home"
if "streak" not in st.session_state: st.session_state.streak = auth.check_daily_streak()
if "xp" not in st.session_state: st.session_state.xp = user_data.get("xp", 50)
if "level" not in st.session_state: st.session_state.level = user_data.get("level", 1)
if "golden_tickets" not in st.session_state: st.session_state.golden_tickets = user_data.get("golden_tickets", 0)
if "user_niche" not in st.session_state: st.session_state.user_niche = user_data.get("niche", "")
if "brand_voice" not in st.session_state: st.session_state.brand_voice = user_data.get("brand_voice", "De Expert 🧠")
if "daily_xp_earned" not in st.session_state: st.session_state.daily_xp_earned = user_data.get("daily_xp_earned", 0)
if "last_xp_date" not in st.session_state: st.session_state.last_xp_date = user_data.get("last_xp_date", str(datetime.datetime.now().date()))
if "challenge_day" not in st.session_state: st.session_state.challenge_day = user_data.get("challenge_day", 1)
if "weekly_goal" not in st.session_state: st.session_state.weekly_goal = user_data.get("weekly_goal", 0)
if "weekly_progress" not in st.session_state: st.session_state.weekly_progress = user_data.get("weekly_progress", 0)

is_pro = auth.is_pro()
niche = st.session_state.user_niche

# --- 4. HELPER LOGICA ---

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
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("⚙️", key="head_set"): go_settings(); st.rerun()

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
            if st.button("📈 Conversie Story", use_container_width=True): 
                auth.save_progress(unclaimed_reward=False, active_trial_feature="Sales Mode", trial_end_time=end_time)
                st.balloons(); time.sleep(1); st.rerun()
        with c2:
            if st.button("🕵️ Viral Remix", use_container_width=True):
                auth.save_progress(unclaimed_reward=False, active_trial_feature="Viral Remix", trial_end_time=end_time)
                st.balloons(); time.sleep(1); st.rerun()
    show_reward_popup()

if not st.session_state.user_niche:
    st.info("Welkom! Wat is je niche?")
    n = st.text_input("Niche:", placeholder="bv. Kapper")
    if st.button("Start"):
        if n: st.session_state.user_niche = n; auth.save_progress(niche=n, xp=50); st.rerun()
    st.stop()

# ==========================
# 🏠 HOME DASHBOARD
# ==========================
if st.session_state.page == "home":
    st.markdown(f"**👋 Hi {niche}-creator!**")
    
    # METRICS LOGICA: PRO vs DEMO
    if is_pro:
        # PRO VERSIE: Geen Tickets, maar LEVEL (Status)
        # XP blijft wel staan voor Leaderboard competitie
        metrics_html = f"""
        <div class="metrics-strip">
            <div class="metric-card" title="Streak: Houd dit vol!">
                <div class="metric-val" style="color:#ef4444;">{st.session_state.streak}</div><div class="metric-lbl">🔥 Streakdagen</div>
            </div>
            <div class="metric-card" title="Jouw status. Stijg op het leaderboard!">
                <div class="metric-val" style="color:#10b981;">{st.session_state.level}</div><div class="metric-lbl">🏆 Jouw Level</div>
            </div>
            <div class="metric-card" title="XP Punten: Blijf klimmen!">
                <div class="metric-val" style="color:#3b82f6;">{st.session_state.xp}</div><div class="metric-lbl">🎁 XP Punten</div>
            </div>
        </div>"""
    else:
        # DEMO VERSIE: Tickets tonen
        metrics_html = f"""
        <div class="metrics-strip">
            <div class="metric-card" title="Streak: Houd dit vol voor beloningen!">
                <div class="metric-val" style="color:#ef4444;">{st.session_state.streak}</div><div class="metric-lbl">🔥 Streakdagen</div>
            </div>
            <div class="metric-card" title="Tickets: Zet in om functies te unlocken.">
                <div class="metric-val" style="color:#f59e0b;">{st.session_state.golden_tickets}</div><div class="metric-lbl">🎫 Tickets</div>
            </div>
            <div class="metric-card" title="XP: 100 XP = Level Up + Ticket.">
                <div class="metric-val" style="color:#3b82f6;">{st.session_state.xp}</div><div class="metric-lbl">🎁 XP (Lvl {st.session_state.level})</div>
            </div>
        </div>"""
    
    st.markdown(metrics_html, unsafe_allow_html=True)

    # TREND BOX
    trend = ai_coach.get_weekly_trend()
    st.markdown(f"""
    <div class="trend-box">
        <div class="trend-label">🔥 Trend van de Week</div>
        <div class="trend-title">{trend['title']}</div>
        <div style="font-size:0.9rem; margin-top:5px;">{trend['desc']}</div>
        <div style="margin-top:10px; font-size:0.8rem; background:rgba(255,255,255,0.2); padding:5px 10px; border-radius:6px;">🎵 {trend['sound']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='panic-btn-red'>", unsafe_allow_html=True)
    if st.button("🚨 PANIC BUTTON: IK HEB NU EEN IDEE NODIG!", use_container_width=True):
        with st.spinner("AI zoekt viral kans..."):
            script = ai_coach.generate_instant_script(niche)
            st.session_state.last_script = script
            go_studio(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("<div class='nav-card'><div class='nav-icon'>🚀</div><div class='nav-title'>Bootcamp</div><div class='nav-desc'>Jouw missie.</div></div>", unsafe_allow_html=True)
        if st.button("Ga naar Bootcamp", key="btn_boot", use_container_width=True): st.session_state.page = "bootcamp"; st.rerun()
        st.markdown("<div class='nav-card'><div class='nav-icon'>📊</div><div class='nav-title'>Cijfers</div><div class='nav-desc'>Check je groei.</div></div>", unsafe_allow_html=True)
        if st.button("Bekijk Cijfers", key="btn_stats", use_container_width=True): go_stats(); st.rerun()
    with col_b:
        st.markdown("<div class='nav-card'><div class='nav-icon'>🎬</div><div class='nav-title'>Studio</div><div class='nav-desc'>Maak scripts.</div></div>", unsafe_allow_html=True)
        if st.button("Open Studio", key="btn_studio", use_container_width=True): go_studio(); st.rerun()
        st.markdown("<div class='nav-card'><div class='nav-icon'>🛠️</div><div class='nav-title'>Tools</div><div class='nav-desc'>Remix & Bio.</div></div>", unsafe_allow_html=True)
        if st.button("Open Tools", key="btn_tools", use_container_width=True): go_tools(); st.rerun()

# ==========================
# 🚀 BOOTCAMP
# ==========================
if st.session_state.page == "bootcamp":
    if st.button("⬅️ Terug"): go_home(); st.rerun()
    st.markdown("## 🚀 Bootcamp")
    if st.session_state.weekly_goal == 0:
        with st.container(border=True):
            st.markdown("### 🎯 Weekdoel")
            goal = st.slider("Aantal video's", 1, 7, 3)
            if st.button("Ik beloof het! 🤝", use_container_width=True): 
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
            if st.button("✨ Schrijf Script", use_container_width=True):
                st.session_state.chal_script = ai_coach.generate_challenge_script(current_day, task_txt, niche, chal_format); st.rerun()
        else:
            if st.session_state.golden_tickets > 0 and not is_pro:
                st.markdown(f"<div class='ticket-box'>🔒 <b>PRO Dag.</b><br>Inzetten: 1 Ticket?</div>", unsafe_allow_html=True)
                if st.button("🎫 Gebruik Ticket"):
                    if auth.use_ticket(): st.session_state.chal_script = ai_coach.generate_challenge_script(current_day, task_txt, niche, "Video"); st.rerun()
            elif is_pro:
                # PRO Directe Toegang
                chal_format = st.radio("Format", ["🎥 Video", "📸 Foto"], horizontal=True, label_visibility="collapsed")
                if st.button("✨ Schrijf Script", use_container_width=True):
                    st.session_state.chal_script = ai_coach.generate_challenge_script(current_day, task_txt, niche, chal_format); st.rerun()
            else: ui.render_locked_section("AI Coach", "Upgrade naar PRO")

    if "chal_script" in st.session_state:
        with st.expander("📜 Jouw Script", expanded=True):
            st.markdown(st.session_state.chal_script)
            if st.button("✅ Gedaan! (+50 XP)", use_container_width=True):
                st.balloons(); auth.handle_daily_streak(); add_xp(50)
                st.session_state.challenge_day += 1; st.session_state.weekly_progress += 1
                auth.save_progress(challenge_day=st.session_state.challenge_day, weekly_progress=st.session_state.weekly_progress)
                del st.session_state.chal_script; time.sleep(2); st.rerun()

# ==========================
# 🎬 STUDIO
# ==========================
if st.session_state.page == "studio":
    if st.button("⬅️ Terug"): go_home(); st.rerun()
    st.markdown("## 🎬 Studio")
    if "last_script" in st.session_state:
        if st.session_state.get("generated_img"): st.image(st.session_state.generated_img, caption="AI Sfeerbeeld", use_container_width=True)
        t1, t2 = st.tabs(["Script", "Teleprompter"])
        with t1:
            st.markdown(st.session_state.last_script)
            if st.button("💾 Opslaan"): 
                if is_pro: auth.save_script_to_library("Script", st.session_state.last_script); st.toast("Opgeslagen!")
                else: st.toast("🔒 Alleen PRO")
            if st.button("❌ Nieuw"): del st.session_state.last_script; st.rerun()
        with t2:
            font = st.slider("Grootte", 16, 50, 24)
            st.markdown(f"<div class='teleprompter-box' style='font-size:{font}px;'>{st.session_state.last_script}</div>", unsafe_allow_html=True)
    else:
        tab_viral, tab_conv, tab_hook = st.tabs(["👀 Viral Maker", "📈 Conversie", "🪝 Hook Rater"])
        with tab_viral:
            if st.button("🔥 Gebruik Viral Format (Bewezen)", type="secondary"):
                st.session_state.last_script = ai_coach.generate_script("Trending", "Vlog", "Energiek", "Wait", "Volg", niche, st.session_state.brand_voice)
                st.session_state.generated_img = ai_coach.generate_ai_image_url("Trending", "Vlog", niche)
                st.rerun()
            st.markdown("---")
            template = st.selectbox("💡 Template", ["✨ Eigen idee", "🚫 Mythe Ontkrachten", "📚 How-To", "😲 Reactie"])
            topic = st.text_input("Onderwerp:", placeholder="Waar gaat het over?")
            if st.button("🎲 Idee"): st.session_state.idea_input = random.choice(["Veelgemaakte fout", "Geheim trucje", "Mijn mening"]); st.rerun()
            st.caption("Toon:"); tone = st.radio("Tone", ["⚡ Energiek", "😌 Rustig", "😂 Humor"], horizontal=True, label_visibility="collapsed")
            c1, c2 = st.columns(2)
            with c1: fmt = st.selectbox("Format", ["Talking Head", "Vlog", "Green Screen"])
            with c2: hook = st.selectbox("Hook", ai_coach.get_viral_hooks_library(niche))
            if st.button("✨ Schrijf Viral Script (+10 XP)", type="primary", use_container_width=True):
                st.session_state.last_script = ai_coach.generate_script(topic if topic else "Algemeen", fmt, tone.split()[1], hook, "Volg", niche, st.session_state.brand_voice)
                st.session_state.generated_img = ai_coach.generate_ai_image_url(topic, fmt, niche)
                add_xp(10); st.session_state.current_topic = topic; st.rerun()
        with tab_conv:
            prod = st.text_input("Product/Dienst"); pain = st.text_input("Probleem klant")
            if check_feature_access("Sales Mode"):
                if st.button("✍️ Schrijf Story (+10 XP)", type="primary", use_container_width=True):
                    st.session_state.last_script = ai_coach.generate_sales_script(prod, pain, "Story", niche)
                    add_xp(10); st.session_state.current_topic = f"Sales: {prod}"; st.rerun()
                if not is_pro: st.caption("🔓 Tijdelijk ontgrendeld")
            else:
                if st.session_state.golden_tickets > 0:
                    if st.button("🎫 Unlock Story (24u)"): use_golden_ticket("Sales Mode")
                else: ui.render_locked_section("Conversie Storytelling", "Zet conversie op nummer 1.")
        with tab_hook:
            st.markdown("Twijfel je over je openingszin? Test hem hier.")
            user_hook = st.text_input("Jouw Hook:")
            if st.button("Test Hook"):
                if user_hook:
                    res = ai_coach.rate_user_hook(user_hook, niche)
                    st.markdown(f"### Score: {res['score']}/10")
                    st.info(res['feedback'])
                else: st.error("Vul iets in!")

# ==========================
# 🛠️ TOOLS
# ==========================
if st.session_state.page == "tools":
    if st.button("⬅️ Terug"): go_home(); st.rerun()
    st.markdown("## 🛠️ Tools")
    with st.expander("🧬 Bio Optimalisator"):
        bio = st.text_input("Huidige bio")
        if st.button("Verbeter"): st.markdown(ai_coach.generate_bio_options(bio, niche))
    with st.expander("🔥 Idee Checker"):
        idea = st.text_input("Jouw idee")
        if st.button("Check"): st.info(ai_coach.check_viral_potential(idea, niche)['verdict'])
    with st.expander("🕵️ Viral Remix Tool (PRO)"):
        if check_feature_access("Viral Remix"):
            other = st.text_area("Script om te stelen:")
            if st.button("🔀 Remix Script"): st.markdown(ai_coach.steal_format_and_rewrite(other, "Mijn Onderwerp", niche))
            if not is_pro: st.caption("🔓 Tijdelijk ontgrendeld")
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock Remix (24u)", key="btn_remix"): use_golden_ticket("Viral Remix")
            ui.render_locked_section("Viral Remix", "Steel formats van virale video's.")
    with st.expander("📦 Passief Inkomen (PRO)"):
        if check_feature_access("Product Bedenker"):
             tgt = st.text_input("Doelgroep")
             if st.button("Genereer Plan"):
                 plan = ai_coach.generate_digital_product_plan(niche, tgt); st.markdown(plan)
                 pdf = create_pdf(plan); 
                 if pdf: st.download_button("📥 Download PDF", data=pdf, file_name="plan.pdf", mime="application/pdf")
             if not is_pro: st.caption("🔓 Tijdelijk ontgrendeld")
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock Product (24u)", key="btn_prod"): use_golden_ticket("Product Bedenker")
            ui.render_locked_section("Product Bedenker", "Verdien geld terwijl je slaapt.")
    with st.expander("🎬 5 Video's in 1 klik (PRO)"):
        if check_feature_access("Serie Generator"):
            series_topic = st.text_input("Onderwerp Serie:")
            if st.button("Bouw Serie"): st.markdown(ai_coach.generate_series_ideas(series_topic, niche))
            if not is_pro: st.caption("🔓 Tijdelijk ontgrendeld")
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock Serie (24u)", key="btn_serie"): use_golden_ticket("Serie Generator")
            ui.render_locked_section("Serie Generator", "Binge-waardige content.")
    with st.expander("📅 Weekplanner (PRO)"):
        if check_feature_access("Weekplanner"):
            if st.button("Plan Week"): st.markdown(ai_coach.generate_weekly_plan(niche))
            if st.button("📥 Download voor Agenda (.ics)"):
                ics_data = ai_coach.create_ics_file(niche)
                st.download_button("Klik om te downloaden", ics_data, file_name="content_kalender.ics", mime="text/calendar")
            if not is_pro: st.caption("🔓 Tijdelijk ontgrendeld")
        else:
            if st.session_state.golden_tickets > 0:
                if st.button("🎫 Unlock Planner (24u)", key="btn_plan"): use_golden_ticket("Weekplanner")
            ui.render_locked_section("Weekplanner", "Nooit meer stress over wat je moet posten.")

# ==========================
# 📊 STATS
# ==========================
if st.session_state.page == "stats":
    if st.button("⬅️ Terug"): go_home(); st.rerun()
    st.markdown("## 📊 Cijfers")
    if auth.is_tiktok_connected():
        st.success("✅ Data wordt automatisch opgehaald.")
        st.bar_chart({"Views": [100, 450, 300, 900, 1200]})
    else:
        st.warning("⚠️ Koppel TikTok op het dashboard.")
        v = st.number_input("Views laatste video", step=100)
        if st.button("Claim XP (+20)"): auth.handle_daily_streak(); add_xp(20); st.rerun()
    st.markdown("#### 🏆 Leaderboard")
    st.dataframe(ai_coach.get_leaderboard(niche, st.session_state.xp), use_container_width=True, hide_index=True)

# ==========================
# ⚙️ SETTINGS
# ==========================
if st.session_state.page == "settings":
    if st.button("⬅️ Terug"): go_home(); st.rerun()
    st.markdown("## ⚙️ Instellingen")
    
    with st.container(border=True):
        new_niche = st.text_input("Niche", value=niche)
        st.markdown("### 🗣️ Jouw Stijl (Brand Voice)")
        voice = st.selectbox("Hoe wil je klinken?", ["De Expert 🧠", "De Beste Vriendin 💖", "De Harde Waarheid 🔥", "De Grappenmaker 😂"], index=0)
        
        if st.button("Opslaan"): 
            st.session_state.brand_voice = voice
            auth.save_progress(niche=new_niche, brand_voice=voice)
            st.success("Opgeslagen!")
            time.sleep(1)
            st.rerun()

    if is_pro:
        st.success("✅ Je bent een PRO lid. Geniet van alle functies!")
        st.info(f"Level: {st.session_state.level} | XP: {st.session_state.xp}/100")
        # Misschien een progress bar hier voor XP tot volgend level?
        st.progress(st.session_state.xp / 100)
        st.caption("XP tot volgend level")
    else:
        st.markdown("""
        <div class="pricing-box">
            <div class="fomo-badge">🔥 Populairste Keuze</div>
            <div class="pricing-header">
                <h3>🚀 Upgrade naar PRO</h3>
                <div class="price-tag">€9,95<span class="price-period">/maand</span></div>
                <small style="color:#ef4444; font-weight:bold;">(Normaal €19,95 - Early Bird Deal)</small>
            </div>
            <div style="display:flex; gap:10px;">
                <div style="flex:1;">
                    <ul class="feature-list">
                        <li class="feature-item"><span class="check-icon">✅</span> Onbeperkt Scripts</li>
                        <li class="feature-item"><span class="check-icon">✅</span> Viral Remix Tool</li>
                        <li class="feature-item"><span class="check-icon">✅</span> Passief Inkomen Generator</li>
                        <li class="feature-item"><span class="check-icon">✅</span> Wekelijkse Trends</li>
                    </ul>
                </div>
                <div style="flex:1;">
                    <ul class="feature-list">
                        <li class="feature-item"><span class="cross-icon">❌</span> <span class="strike-text">Max 1 script/dag</span></li>
                        <li class="feature-item"><span class="cross-icon">❌</span> <span class="strike-text">Geen Sales Modus</span></li>
                        <li class="feature-item"><span class="cross-icon">❌</span> <span class="strike-text">Geen Kalender Export</span></li>
                    </ul>
                </div>
            </div>
            <div style="text-align:center; margin-top:20px;">
                <a href="https://postai.lemonsqueezy.com/buy/..." target="_blank" style="text-decoration:none;">
                    <button style="background:#10b981; color:white; border:none; padding:12px 25px; border-radius:10px; font-weight:800; font-size:1.1rem; cursor:pointer; width:100%; box-shadow:0 4px 10px rgba(16,185,129,0.3);">
                        👉 Claim 50% Korting & Start Direct
                    </button>
                </a>
                <p style="font-size:0.7rem; color:#9ca3af; margin-top:10px;">14 dagen niet-goed-geld-terug garantie.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("Heb je al een licentiecode?"):
            c = st.text_input("Vul je code in")
            if st.button("Activeer Licentie"): auth.activate_pro(c)

    st.markdown("---")
    if st.button("🧪 DEV: Zet Streak op 5 (Popup Test)"): st.session_state.streak = 5; auth.save_progress(streak=5, unclaimed_reward=True); st.rerun()

# ==========================
# 📄 PRIVACY & VOORWAARDEN
# ==========================
if st.session_state.page == "privacy":
    if st.button("⬅️ Terug"): go_home(); st.rerun()
    st.markdown("## 🔒 Privacy Policy")
    st.markdown("""**Laatst bijgewerkt: 2025**\n\nBij PostAi nemen we jouw privacy serieus.\n1. **Gegevensverzameling:** We slaan alleen je voortgang (XP, streak) en niche op. Scripts worden lokaal verwerkt.\n2. **Derden:** We delen geen data met derden, behalve voor betalingsverwerking (LemonSqueezy).\n3. **AI Gebruik:** Je inputs worden verwerkt door AI om content te genereren, maar niet gebruikt om modellen te trainen.\n\nVoor vragen: support@postai.nl""")

if st.session_state.page == "terms":
    if st.button("⬅️ Terug"): go_home(); st.rerun()
    st.markdown("## 📜 Algemene Voorwaarden")
    st.markdown("""**1. Gebruik:** PostAi is een hulpmiddel. Jij blijft verantwoordelijk voor de content die je plaatst.\n**2. Abonnement:** Het PRO abonnement is maandelijks opzegbaar. \n**3. Aansprakelijkheid:** Wij garanderen geen specifieke resultaten (zoals viral gaan).\n**4. Refund:** Niet tevreden? 14 dagen geld terug garantie.""")

# --- FOOTER ---
ui.inject_chat_widget(auth.get_secret("CHAT_URL", ""))
st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    f1, f2 = st.columns(2)
    with f1: 
        if st.button("Privacy Policy", key="f_priv", use_container_width=True):
            st.session_state.page = "privacy"
            st.rerun()
    with f2: 
        if st.button("Voorwaarden", key="f_terms", use_container_width=True):
            st.session_state.page = "terms"
            st.rerun()

st.markdown("""<div class="footer-container"><div class="footer-text">14 dagen gratis • Gemaakt voor TikTok</div><div class="footer-sub">© 2025 PostAi. Alle rechten voorbehouden.</div></div>""", unsafe_allow_html=True)