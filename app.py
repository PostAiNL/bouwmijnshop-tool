import streamlit as st
import pandas as pd
import random
import datetime
import json
import time
import os
import base64
from modules import analytics, ui, auth, ai_coach, data_loader

# --- CONFIG ---
st.set_page_config(page_title="PostAi", page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")
auth.init_session()
ui.inject_style_and_hacks(brand_color="#10b981")

# --- CSS ---
st.markdown("""
<style>
    .stButton button { border-radius: 12px !important; }
    div[data-testid="stExpander"] { border-radius: 16px !important; overflow: hidden; border: 1px solid #e4e4e7; }
    div[data-testid="stImage"] { border-radius: 15px !important; overflow: hidden !important; }
    div[data-testid="stImage"] > div { border-radius: 15px !important; }
    div[data-testid="stImage"] img { border-radius: 15px !important; object-fit: cover !important; }
    img { border-radius: 15px !important; }

    /* Custom Metrics */
    .metrics-container { display: flex; flex-direction: row; justify-content: space-between; gap: 10px; width: 100%; margin-bottom: -5px; }
    .metric-box { 
        flex: 1; border-radius: 12px; padding: 10px 5px; text-align: center; 
        display: flex; flex-direction: column; align-items: center; justify-content: center; min-width: 80px; 
        transition: transform 0.2s; cursor: help;
    }
    .metric-box:hover { transform: scale(1.02); }
    
    .mbox-orange { background: #fff7ed; border: 1px solid orange; }
    .mbox-yellow { background: #fefce8; border: 1px solid #facc15; }
    .mbox-green  { background: #f0fdf4; border: 1px solid #10b981; }
    
    .metric-val { margin: 0; font-size: 1.6rem; font-weight: 800; line-height: 1.2; }
    .metric-lbl { margin: 0; font-size: 0.75rem; text-transform: uppercase; font-weight: 600; opacity: 0.8; white-space: nowrap; }
    
    /* Footer */
    .footer-text { text-align: center; font-size: 0.85rem; color: #6b7280; margin-top: 15px; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    .footer-sub { text-align: center; font-size: 0.75rem; color: #9ca3af; margin-top: 5px; }
    .legal-title { font-size: 1.8rem; font-weight: 800; color: #111827; margin-bottom: 10px; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }

    /* Teleprompter */
    .teleprompter-box {
        background-color: #000; color: #fff; padding: 40px 20px; border-radius: 15px;
        min-height: 300px; overflow-y: auto; text-align: center; margin-top: 10px;
    }

    /* Ticket Box */
    .ticket-box {
        background-color: #fffbeb; border: 1px solid #fcd34d; color: #92400e; padding: 10px; border-radius: 8px; margin-bottom: 10px; font-size: 0.9rem; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- NAVIGATIE ---
if "current_page" not in st.session_state: st.session_state.current_page = "app"
if not auth.is_authenticated():
    auth.render_landing_page()
    st.stop()

# --- LEGAL PAGES ---
def render_legal_header(title):
    col_l, col_r = st.columns([0.2, 0.8])
    with col_l:
        if st.button("⬅️ Terug", use_container_width=True, type="secondary"):
            st.session_state.current_page = "app"
            st.rerun()
    st.markdown(f"<div class='legal-title'>{title}</div>", unsafe_allow_html=True)

if st.session_state.current_page == "privacy":
    render_legal_header("Privacybeleid")
    with st.container(border=True): st.markdown("""**Laatst bijgewerkt:** 24 november 2025...""")
    st.stop()

if st.session_state.current_page == "terms":
    render_legal_header("Algemene Voorwaarden")
    with st.container(border=True): st.markdown("""Welkom bij PostAi...""")
    st.stop()

# --- STATE ---
user_data = auth.load_progress()
current_streak = auth.check_daily_streak()
if "df" not in st.session_state: st.session_state.df = pd.DataFrame() 
if "streak" not in st.session_state: st.session_state.streak = current_streak
if "level" not in st.session_state: st.session_state.level = user_data.get("level", 1)
if "xp" not in st.session_state: st.session_state.xp = user_data.get("xp", 50)
if "user_niche" not in st.session_state: st.session_state.user_niche = user_data.get("niche", "")
if "challenge_day" not in st.session_state: st.session_state.challenge_day = user_data.get("challenge_day", 1)
if "golden_tickets" not in st.session_state: st.session_state.golden_tickets = user_data.get("golden_tickets", 0)

if "weekly_goal" not in st.session_state: 
    st.session_state.weekly_goal = user_data.get("weekly_goal", 0)
if "weekly_progress" not in st.session_state: 
    st.session_state.weekly_progress = user_data.get("weekly_progress", 0)

is_pro = auth.is_pro()
niche = st.session_state.user_niche

# --- HELPER FUNCTIES ---
def handle_daily_streak():
    """Verwerkt streak, datum en beloningen in één keer."""
    today_str = str(datetime.date.today())
    last_active = user_data.get("last_active_date", "")
    
    if today_str != last_active:
        st.session_state.streak += 1
        
        # Check voor beloning elke 5 dagen (ALLEEN ALS JE GEEN PRO BENT)
        give_reward = False
        if not auth.is_pro() and st.session_state.streak > 0 and st.session_state.streak % 5 == 0:
            give_reward = True
        
        if give_reward:
            auth.save_progress(last_active_date=today_str, streak=st.session_state.streak, unclaimed_reward=True)
        else:
            auth.save_progress(last_active_date=today_str, streak=st.session_state.streak)
            
        st.toast("🔥 Streak verhoogd! Goed bezig!")
        return True
    else:
        st.toast("Je hebt je streak voor vandaag al binnen! 🔥")
        return False

def add_xp(amount):
    """Voegt XP toe en checkt voor Level Up + Golden Ticket."""
    st.session_state.xp += amount
    
    calculated_level = 1 + (st.session_state.xp // 100)
    if calculated_level > st.session_state.level:
        levels_gained = calculated_level - st.session_state.level
        st.session_state.level = calculated_level
        st.session_state.golden_tickets += levels_gained
        st.balloons()
        st.toast(f"🎉 LEVEL UP! +{levels_gained} Golden Ticket(s) gekregen!", icon="🎟️")
        time.sleep(2)
    else:
        st.toast(f"💪 +{amount} XP erbij!")
    
    auth.save_progress(xp=st.session_state.xp, level=st.session_state.level, golden_tickets=st.session_state.golden_tickets)

def use_ticket():
    """Verbruikt 1 ticket."""
    if st.session_state.golden_tickets > 0:
        st.session_state.golden_tickets -= 1
        auth.save_progress(golden_tickets=st.session_state.golden_tickets)
        st.toast("🎟️ Ticket ingezet! Functie ontgrendeld.")
        return True
    else:
        st.error("Geen tickets meer! Level up om nieuwe te verdienen.")
        return False

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

# --- HEADER & ONBOARDING ---
ui.render_header(is_pro, st.session_state.level)

# --- POPUP BELONING ---
has_reward = user_data.get("unclaimed_reward", False)
if has_reward and not is_pro:
    @st.dialog("🎁 Cadeautje voor jou")
    def show_reward_popup():
        st.markdown(f"<h2 style='text-align:center'>🎉 {st.session_state.streak} Dagen Streak!</h2>", unsafe_allow_html=True)
        st.write("Wat goed bezig! Als beloning mag je **24 uur lang** één PRO-functie gratis gebruiken.")
        c1, c2, c3 = st.columns(3)
        future = (datetime.datetime.now() + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        with c1: 
            if st.button("Sales Mode 💸", help="Maak scripts die écht verkopen"): 
                auth.save_progress(unclaimed_reward=False, active_trial_feature="Sales Mode", trial_end_time=future)
                st.toast("Geactiveerd! Veel plezier.")
                time.sleep(1); st.rerun()
        with c2:
            if st.button("Product 📦", help="Laat AI een digitaal product bedenken"): 
                auth.save_progress(unclaimed_reward=False, active_trial_feature="Product Bedenker", trial_end_time=future)
                st.toast("Geactiveerd! Veel plezier.")
                time.sleep(1); st.rerun()
        with c3:
            if st.button("Data 📊", help="Diepe analyse van je cijfers"): 
                auth.save_progress(unclaimed_reward=False, active_trial_feature="Data Detective", trial_end_time=future)
                st.toast("Geactiveerd! Veel plezier.")
                time.sleep(1); st.rerun()
    show_reward_popup()

if not st.session_state.user_niche:
    st.markdown("---")
    with st.container(border=True):
        st.info("Ik ben PostAi, jouw persoonlijke social media coach.")
        niche_in = st.text_input("Jouw Niche / Onderwerp:", placeholder="bv. Kapper, Boekhouder...", help="Waarover ga je content maken?")
        if st.button("🚀 Start mijn reis", type="primary"):
            if niche_in: st.session_state.user_niche = niche_in; auth.save_progress(niche=niche_in, xp=50); st.rerun()
    st.stop()

c1, c2 = st.columns([0.85, 0.15])
with c1: st.markdown(f"<div class='niche-edit-bar'><span>🎯 Je focus: <b>{niche}</b></span></div>", unsafe_allow_html=True)
with c2:
    if st.button("✏️", key="edit_niche", help="Verander je onderwerp"): st.session_state.user_niche = ""; auth.save_progress(niche=""); st.rerun()

# --- UITLEG BLOK ---
with st.expander("ℹ️ Hoe werkt PostAi? (Klik hier voor uitleg)", expanded=False):
    st.markdown("""
    **Welkom! Zo gebruik je deze app om te groeien op TikTok:**
    
    🔥 **Streakdagen:**  
    Consistentie is het geheim. Kom elke dag terug en maak (of plaats) een video om je vlammetje aan te houden.
    *   **Beloning:** Bij elke **5 dagen streak** krijg je als gratis gebruiker 24 uur toegang tot een PRO-functie!
    
    🎫 **Golden Tickets:**  
    Dit zijn jouw 'jokers'. Heb je geen inspiratie of wil je een gesloten PRO-functie gebruiken? Zet een ticket in om er éénmalig gebruik van te maken. 
    *   **Hoe verdien je ze?** Door XP te halen! Elke 100 XP ga je een Level omhoog en krijg je 1 Ticket.
    
    🚀 **De Bootcamp:**  
    Weet je niet waar je moet beginnen? Volg simpelweg de Bootcamp. Elke dag krijg je 1 duidelijke opdracht. Na 14 dagen ben je klaar voor het echte werk.
    """)

t_chal, t_studio, t_workflow, t_tools, t_data, t_set = st.tabs(["🥾 Bootcamp", "🎬 Studio", "🗂️ Workflow", "✨ Tools", "📊 Cijfers", "⚙️"])

# 1. BOOTCAMP
with t_chal:
    # METRICS MET HOVER TITLES (HERSTELD)
    html_metrics = f"""
    <div class="metrics-container">
        <div class="metric-box mbox-orange" title="Houd dit elke dag vol! Bij elke 5 dagen krijg je een cadeau.">
            <h2 class="metric-val" style="color:orange;">🔥 {st.session_state.streak}</h2>
            <small class="metric-lbl">Streakdagen</small>
        </div>
        <div class="metric-box mbox-yellow" title="Jokers om PRO functies te gebruiken. Verdien ze door te levelen (elke 100 XP).">
            <h2 class="metric-val" style="color:#ca8a04;">🎫 {st.session_state.golden_tickets}</h2>
            <small class="metric-lbl">Golden Tickets</small>
        </div>
        <div class="metric-box mbox-green" title="Verdien 100 XP om te levelen. Elk nieuw level = +1 Ticket!">
            <h2 class="metric-val" style="color:#10b981;">{st.session_state.xp}</h2>
            <small class="metric-lbl">XP Punten (Lvl {st.session_state.level})</small>
        </div>
    </div>
    """
    st.markdown(html_metrics, unsafe_allow_html=True)
    st.markdown("---")
    st.caption("Volg dit programma om consistentie op te bouwen. Elke dag 1 taak.")

    if st.session_state.weekly_goal == 0:
        with st.container(border=True):
            st.markdown("### 🎯 Weekdoel Stellen")
            st.write("Commitment is alles. Hoeveel video's ga je deze week maken?")
            goal = st.slider("Aantal video's", 1, 7, 3, help="Wees realistisch. 3 is een mooi begin.")
            if st.button("Ik beloof het! 🤝", help="Start je week"): 
                st.session_state.weekly_goal = goal
                auth.save_progress(weekly_goal=goal)
                st.toast("Doel opgeslagen! Zet 'm op!")
                time.sleep(4)
                st.rerun()
    else:
        st.markdown(f"**Weekdoel: {st.session_state.weekly_progress} / {st.session_state.weekly_goal} Video's**")
        prog = min(st.session_state.weekly_progress / st.session_state.weekly_goal, 1.0)
        st.progress(prog)
        if st.session_state.weekly_progress >= st.session_state.weekly_goal: st.success("🎉 Doel bereikt!")

    col_main, col_sidebar = st.columns([0.65, 0.35], gap="medium")
    current_day = st.session_state.challenge_day
    
    if current_day > 14:
        daily_info = ai_coach.get_daily_maintenance_task()
        task_today = daily_info['task']
        header_text = f"### 📅 Vandaag: {daily_info['type']}"
    else:
        tasks = ai_coach.get_challenge_tasks()
        task_today = tasks.get(current_day, "Gefeliciteerd! Bootcamp volbracht.")
        header_text = f"#### 🥾 Dag {current_day}: Bootcamp Opdracht"

    with col_main:
        with st.container(border=True):
            st.markdown(header_text)
            
            if current_day > 14:
                 st.info(f"**Focus:** {task_today}")
                 st.markdown("**Hoe wil je dit maken?**")
                 chal_format = st.radio("Format", ["🎥 Video (Filmen)", "📸 Foto Slider (Carrousel)"], horizontal=True, label_visibility="collapsed", help="Kies de vorm van je content")
                 if st.button("✨ Schrijf Dagelijks Script", type="primary", use_container_width=True):
                        with st.spinner("De coach schrijft je script..."):
                            st.session_state.chal_script = ai_coach.generate_challenge_script(current_day, task_today, niche, chal_format)
                            st.rerun()
            else:
                st.info(f"**Missie:** {task_today}")
                
                is_locked = current_day > 3 and not is_pro
                if not is_locked:
                    st.markdown("**Hoe wil je dit maken?**")
                    chal_format = st.radio("Format", ["🎥 Video (Filmen)", "📸 Foto Slider (Carrousel)"], horizontal=True, label_visibility="collapsed", help="Kies video voor bereik, foto's voor educatie.")
                    if st.button("✨ Schrijf Bootcamp Script", type="primary", use_container_width=True, help="Laat AI het werk doen"):
                        with st.spinner("De coach schrijft je script..."):
                            st.session_state.chal_script = ai_coach.generate_challenge_script(current_day, task_today, niche, chal_format)
                            st.rerun()
                else:
                    if st.session_state.golden_tickets > 0:
                        st.markdown(f"<div class='ticket-box'>🔒 <b>Deze dag is voor PRO's.</b><br>Je hebt <b>{st.session_state.golden_tickets}</b> Ticket(s). Inzetten?</div>", unsafe_allow_html=True)
                        if st.button("🎫 Gebruik Ticket & Open", use_container_width=True):
                            if use_ticket():
                                with st.spinner("Ticket geaccepteerd! Schrijven..."):
                                    st.session_state.chal_script = ai_coach.generate_challenge_script(current_day, task_today, niche, "Video")
                                    st.rerun()
                    else:
                        ui.render_locked_section("AI Coach", "Upgrade naar PRO voor de rest van de bootcamp.")

        if "chal_script" in st.session_state:
            st.success("Script gereed!")
            with st.expander("Bekijk Script", expanded=True):
                st.markdown(st.session_state.chal_script)
                if st.button("✅ Gefilmd & Geplaatst (+50 XP)", type="secondary", use_container_width=True, help="Klik hier als je de video op TikTok hebt gezet"):
                    st.balloons()
                    handle_daily_streak()
                    add_xp(50)
                    st.session_state.challenge_day += 1
                    st.session_state.weekly_progress += 1
                    auth.save_progress(challenge_day=st.session_state.challenge_day, weekly_progress=st.session_state.weekly_progress)
                    del st.session_state.chal_script
                    time.sleep(4) 
                    st.rerun()

    with col_sidebar:
        ui.render_challenge_map(current_day)
        st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        st.info(f"💡 **Tip:** {ai_coach.get_daily_pro_tip(current_day)}")

# 2. STUDIO
with t_studio:
    st.markdown("### 🎬 Studio")
    st.caption("Hier maak je scripts voor je eigen ideeën, los van de bootcamp.")
    
    with st.container(border=True):
        st.markdown("#### 1. Wat is je doel?")
        mode = st.radio("Doel", ["👀 Viral gaan (Meer views)", "💸 Geld Verdienen (Verkoop)"], horizontal=True, label_visibility="collapsed", help="Wil je groeien of verkopen?")
        
        if mode == "👀 Viral gaan (Meer views)":
            if st.button("🔥 Gebruik 'Viral Formats' (Bewezen)", use_container_width=True, type="secondary", help="Gebruik een structuur die vaak viraal gaat"):
                with st.spinner("Trend zoeken..."):
                    st.session_state.last_script = ai_coach.generate_script("Trending", "Vlog", "Humor", f"{niche} life", "Volg", niche)
                    st.session_state.generated_img = ai_coach.generate_ai_image_url("Trending", "Vlog", niche)
                    st.rerun()
            st.markdown("---")
            st.markdown("#### 2. Waar gaat het over?")
            template = st.selectbox("💡 Template (Optioneel):", ["✨ Eigen idee", "🚫 Mythe Ontkrachten", "📚 How-To", "😲 Reactie"], help="Een template helpt je verhaal structuur te geven.")
            col_in, col_dice = st.columns([0.85, 0.15], vertical_alignment="bottom")
            with col_in:
                ph = "Welke mythe?" if "Mythe" in template else "Onderwerp..."
                topic = st.text_input("Onderwerp:", value=st.session_state.get("idea_input", ""), placeholder=ph, help="Waarover wil je het hebben?")
            with col_dice:
                if st.button("🎲", help="Geef mij een willekeurig idee"): st.session_state.idea_input = random.choice([f"Fout in {niche}", "Snelle tip"]); st.rerun()
            
            st.markdown("#### 3. Details")
            c_f, c_t = st.columns(2)
            with c_f: vid_format = st.selectbox("Format", ["🗣️ Talking Head", "📸 Vlog", "🟩 Green Screen"], help="Wat ziet de kijker?")
            with c_t: tone = st.selectbox("Toon", ["⚡ Energiek", "😌 Rustig", "😂 Humor"], help="Welke sfeer heeft de video?")
            
            hooks = ai_coach.get_viral_hooks_library(niche)
            hook = st.selectbox("Hook", hooks, help="De eerste zin die de aandacht grijpt.")
            cta = st.selectbox("CTA", ["➕ Volgen", "💬 Reageren"], help="Wat moet de kijker doen na het kijken?")
            
            if st.button("✨ Schrijf Viral Script (+10 XP)", type="primary", use_container_width=True):
                if not is_pro and st.session_state.get("daily_gen_count", 0) >= 1: st.error("⚠️ Daglimiet bereikt. Upgrade voor meer.")
                else:
                    with st.spinner("Magie toepassen..."):
                        final_hook = hook.replace("{onderwerp}", topic if topic else "dit")
                        st.session_state.last_script = ai_coach.generate_script(topic, vid_format, tone, final_hook, cta, niche)
                        st.session_state.generated_img = ai_coach.generate_ai_image_url(topic, vid_format, niche)
                        st.session_state.daily_gen_count = st.session_state.get("daily_gen_count", 0) + 1
                        add_xp(10)
                        st.session_state.current_topic = topic
                        st.rerun()
        
        else:
            st.markdown("<div style='background:#ecfdf5; border-left:4px solid #10b981; padding:10px; font-size:0.9rem;'>💰 <b>Cashflow Modus</b></div>", unsafe_allow_html=True)
            col_p, col_pain = st.columns(2)
            with col_p: product_name = st.text_input("Product", placeholder="E-book...", help="Wat verkoop je?")
            with col_pain: pain_point = st.text_input("Probleem", placeholder="Tijdgebrek...", help="Welk probleem lost het op?")
            sales_angle = st.selectbox("Strategie", ["😱 Pijn & Oplossing", "📦 Demo", "⭐ Testimonial"], help="Hoe wil je het presenteren?")
            
            if auth.has_access("Sales Mode"):
                if st.button("💸 Schrijf Sales Script (+10 XP)", type="primary", use_container_width=True):
                    if not product_name: st.error("Vul product in.")
                    else:
                        with st.spinner("Schrijven..."):
                            st.session_state.last_script = ai_coach.generate_sales_script(product_name, pain_point, sales_angle, niche)
                            st.session_state.generated_img = None
                            add_xp(10)
                            st.session_state.current_topic = f"Sales: {product_name}"; st.rerun()
            else:
                if st.session_state.golden_tickets > 0:
                    st.markdown(f"<div class='ticket-box'>🔒 <b>Sales Modus is PRO.</b><br>Je hebt {st.session_state.golden_tickets} Ticket(s). Inzetten?</div>", unsafe_allow_html=True)
                    if st.button("🎫 Gebruik 1 Ticket & Schrijf", use_container_width=True):
                        if use_ticket():
                            with st.spinner("Schrijven..."):
                                st.session_state.last_script = ai_coach.generate_sales_script(product_name, pain_point, sales_angle, niche)
                                st.session_state.generated_img = None
                                add_xp(10)
                                st.session_state.current_topic = f"Sales: {product_name}"; st.rerun()
                else:
                    ui.render_locked_section("Cashflow Script", "Upgrade naar PRO.")

    if "last_script" in st.session_state:
        st.markdown("---")
        tab_scr, tab_tel, tab_seo = st.tabs(["📄 Script", "🎥 Teleprompter", "#️⃣ Caption"])
        with tab_scr:
            st.success("Klaar!")
            if st.session_state.get("generated_img"):
                st.image(st.session_state.generated_img, caption="AI Visuele Suggestie", use_container_width=True)
            
            st.markdown(st.session_state.last_script)
            c_sv, c_aud = st.columns(2)
            with c_sv: 
                if st.button("💾 Opslaan", use_container_width=True):
                    if is_pro: auth.save_script_to_library(st.session_state.get("current_topic", "Script"), st.session_state.last_script, "Script"); st.toast("Opgeslagen!"); time.sleep(4); st.rerun()
                    else: st.toast("🔒 Alleen PRO"); time.sleep(2)
            with c_aud:
                if st.button("🔍 Audit", use_container_width=True, help="Check hoe goed dit script is"): st.info(ai_coach.audit_script(st.session_state.last_script, niche)['verdict'])
        with tab_tel:
            font_size = st.slider("Lettergrootte", 16, 50, 24)
            st.markdown(f"<div class='teleprompter-box' style='font-size:{font_size}px; line-height:1.5;'>{st.session_state.last_script.replace('**','').replace('---','')}</div>", unsafe_allow_html=True)
        with tab_seo:
            st.code(f"{st.session_state.get('current_topic','Video')} 👇\n\n#{niche.replace(' ','')} #fyp", language="text")

# 3. WORKFLOW
with t_workflow:
    st.caption("Hier vind je al je opgeslagen werk terug.")
    if is_pro:
        st.markdown("### 🗂️ Script Archief")
        library = auth.get_user_library()
        if not library: st.info("Leeg.")
        for s in library:
            with st.expander(f"{s.get('status')} | {s.get('topic')}"):
                st.markdown(s.get('content'))
                if st.button("🗑️", key=s['id']): auth.delete_script(s['id']); st.rerun()
    else: ui.render_locked_section("Workflow", "Bewaar scripts.")

# 4. TOOLS
with t_tools:
    st.markdown("### 🛠️ Creator Tools")
    st.caption("Handige hulpmiddelen om je leven makkelijker te maken.")
    
    with st.expander("🧬 Bio Optimalisator (Nieuw)", expanded=True):
        curr_bio = st.text_input("Huidige bio:", help="Plak hier je huidige TikTok bio")
        if st.button("Optimaliseer"): st.markdown(ai_coach.generate_bio_options(curr_bio, niche))

    with st.expander("🔥 Idee Checker (Gratis)"):
        idea = st.text_input("Jouw idee:", key="chk_free", help="Heb je een video idee? Check het hier.")
        if st.button("Check"): st.info(ai_coach.check_viral_potential(idea, niche)['verdict'])

    with st.expander("📦 Passief Inkomen Bedenker (PRO)"):
        if not auth.has_access("Product Bedenker"):
            if st.session_state.golden_tickets > 0:
                st.markdown(f"<div class='ticket-box'>🔒 <b>Dit is een PRO tool.</b><br>Wil je 1 Ticket inzetten?</div>", unsafe_allow_html=True)
                target = st.text_input("Doelgroep:", help="Voor wie is het?")
                if st.button("🎫 Gebruik Ticket & Genereer"):
                    if use_ticket():
                        with st.spinner("Genereren..."):
                            st.session_state.biz_plan = ai_coach.generate_digital_product_plan(niche, target)
            else:
                ui.render_locked_section("Business Plan", "Laat AI je product bedenken.")
        else:
            target = st.text_input("Doelgroep:", help="Voor wie is het product?")
            if st.button("Genereer Masterplan"):
                if not target: st.error("Vul een doelgroep in.")
                else:
                    with st.spinner("Schrijven..."):
                        st.session_state.biz_plan = ai_coach.generate_digital_product_plan(niche, target)
        
        if "biz_plan" in st.session_state:
            st.markdown(st.session_state.biz_plan)
            pdf_data = create_pdf(st.session_state.biz_plan)
            if pdf_data: st.download_button("📥 Download PDF", data=pdf_data, file_name="plan.pdf", mime="application/pdf")

    with st.expander("🎬 5 Video's in 1 klik (PRO)"):
        if not is_pro:
             ui.render_locked_section("Serie Generator", "Maak 5 video's in 1 klik.")
        else:
            topic = st.text_input("Serie onderwerp:", help="Waar moet de serie over gaan?")
            if st.button("Bouw Serie"): st.markdown(ai_coach.generate_series_ideas(topic, niche))

    with st.expander("🕵️ Viral Video Nadoen (PRO)"):
        if not is_pro:
            ui.render_locked_section("Format Dief", "Kopieer succesformules.")
        else:
            other = st.text_area("Script concurrent:", help="Plak hier de tekst van een video die je goed vindt.")
            mine = st.text_area("Mijn onderwerp:", help="Waar wil jij het over hebben?")
            if st.button("Herschrijf"): st.markdown(ai_coach.steal_format_and_rewrite(other, mine, niche))

    with st.expander("📅 Weekplanner (PRO)"):
        if not is_pro:
            ui.render_locked_section("Weekplanner", "7 dagen content in 1 klik.")
        else:
            if st.button("Maak Planning"): 
                with st.spinner("Plannen..."):
                    st.markdown(ai_coach.generate_weekly_plan(niche))

# 5. DATA
with t_data:
    st.markdown("### 📊 Jouw Cijfers")
    st.caption("Houd bij hoe je video's presteren.")
    
    with st.container(border=True):
        st.markdown("#### 🚀 Snelle Check-in")
        st.write("Vul je resultaten in voor punten (XP).")
        col_i, col_t, col_b = st.columns([0.4, 0.4, 0.2], vertical_alignment="bottom")
        with col_i: v = st.number_input("Views laatste video", min_value=0, step=100, help="Aantal weergaven")
        with col_t: r = st.number_input("Kijktijd (sec) [Optioneel]", min_value=0, step=1, help="Hoe lang keken mensen gemiddeld?")
        with col_b: 
            if st.button("Claim XP", type="primary", use_container_width=True): 
                if v>0: 
                    st.balloons()
                    handle_daily_streak() # Streak check
                    add_xp(20)
                    msg = "+20 XP! "
                    if r > 0 and r < 3: msg += "Tip: Werk aan je hook, mensen haken snel af."
                    elif r > 3: msg += "Lekker bezig! Retentie is koning."
                    st.toast(msg)
                    time.sleep(4)
                    st.rerun()

    st.markdown("#### 🏆 Leaderboard: " + niche)
    # Leaderboard update met huidige XP
    lb = ai_coach.get_leaderboard(niche, st.session_state.xp)
    st.dataframe(lb, use_container_width=True, hide_index=True)

    with st.expander("📂 Geavanceerd: TikTok CSV Upload"):
        up = st.file_uploader("Upload CSV", type=['csv','xlsx'])
        if up: st.session_state.df = data_loader.load_file(up)
        if not st.session_state.df.empty:
            df = analytics.clean_data(st.session_state.df)
            kpis = analytics.calculate_kpis(df)
            if auth.has_access("Data Detective"):
                if st.button("🔍 AI Analyse"): st.info(ai_coach.analyze_data_patterns(f"Views: {kpis['Views'].sum()}", niche)['strategy_tip'])
            st.metric("Totaal Views", f"{kpis['Views'].sum()/1000:.1f}k")
            st.bar_chart(analytics.get_best_posting_time(df), x="Uur", y="Views")

# 6. SETTINGS
with t_set:
    st.markdown("### ⚙️ Instellingen")
    st.caption("Beheer je account en voorkeuren.")
    
    with st.container(border=True):
        st.markdown("#### 👤 Jouw Profiel")
        new_niche = st.text_input("Jouw Niche:", value=niche, help="Dit past alle AI suggesties aan.")
        if new_niche != niche:
            if st.button("💾 Niche Opslaan"):
                auth.save_progress(niche=new_niche)
                st.session_state.user_niche = new_niche
                st.toast("Niche aangepast! Pagina herlaadt...")
                time.sleep(2)
                st.rerun()

    with st.container(border=True):
        st.markdown("#### 📅 Weekdoel")
        st.write(f"Huidig doel: {st.session_state.weekly_goal} video's")
        if st.button("🔄 Reset Weekdoel"):
            st.session_state.weekly_goal = 0
            st.session_state.weekly_progress = 0
            auth.save_progress(weekly_goal=0, weekly_progress=0)
            st.toast("Weekdoel gereset!")
            time.sleep(2)
            st.rerun()

    st.markdown("---")
    
    if not is_pro:
        st.markdown("### 🔓 Upgrade naar PostAi PRO 🚀")
        st.markdown("Voorkom dat je je Streak en Scripts verliest! Upgrade voor onbeperkte toegang.")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("❌ **Max 1 script** per dag")
                st.markdown("❌ **Geen** Sales Modus")
                st.markdown("❌ **Geen** Product Bedenker")
            with c2:
                st.markdown("✅ **Onbeperkt** Scripts")
                st.markdown("✅ **Geld Verdienen** Tools")
                st.markdown("✅ **Volledige** Roadmap")
            
            st.markdown("""
            <div style='text-align:center; margin-top:10px; margin-bottom:10px;'>
                <span class='pricing-strike'>€29,95</span> <span class='pricing-deal'>Nu €19,95 / maand</span>
            </div>
            """, unsafe_allow_html=True)
            st.link_button("👉 Start 14 Dagen Gratis", "https://postai.lemonsqueezy.com/buy/...", type="primary", use_container_width=True)
        
        with st.expander("Heb je al een code?"):
            c = st.text_input("Code")
            if st.button("Activeer"): auth.activate_pro(c)
    else:
        st.success("Je bent PRO lid! 🚀")
        if st.button("Uitloggen"): st.session_state.clear(); st.rerun()
    
    # TEST KNOP
    st.markdown("---")
    if st.button("🧪 Test Beloning (Zet Streak op 5)"):
        st.session_state.streak = 5
        auth.save_progress(streak=5, unclaimed_reward=True)
        st.toast("Streak op 5 gezet! Ververs de pagina.")
        time.sleep(2)
        st.rerun()

ui.inject_chat_widget(auth.get_secret("CHAT_SERVER_URL", "https://chatbot.com"))

# --- FOOTER ---
st.markdown("<div style='margin-top:50px; border-top:1px solid #f3f4f6; margin-bottom:20px;'></div>", unsafe_allow_html=True)
c_space_left, c_btn1, c_btn2, c_space_right = st.columns([3, 2, 2, 3])
with c_btn1:
    if st.button("Privacy Policy", key="foot_priv", use_container_width=True, type="secondary"): st.session_state.current_page = "privacy"; st.rerun()
with c_btn2:
    if st.button("Voorwaarden", key="foot_terms", use_container_width=True, type="secondary"): st.session_state.current_page = "terms"; st.rerun()

st.markdown("""<div class="footer-text">14 dagen gratis • Gemaakt voor TikTok</div><div class="footer-sub">© 2025 PostAi. Alle rechten voorbehouden.</div>""", unsafe_allow_html=True)