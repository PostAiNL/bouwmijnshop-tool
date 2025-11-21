import streamlit as st
import pandas as pd
import os
import time
from pathlib import Path

from modules import analytics, ui, auth, ai_coach, data_loader

# --- CONFIG ---
st.set_page_config(page_title="PostAi – TikTok Growth", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# 1. FORCE SIDEBAR OPEN (De fix!)
ui.force_sidebar_open()

# 2. Styling
ui.inject_style_and_hacks()

# --- ROUTER (Privacy & Terms) ---
qp = st.query_params
page = qp.get("page")

if page == "privacy":
    st.markdown("<a href='/' target='_self' style='text-decoration:none;'>← Terug</a>", unsafe_allow_html=True)
    st.markdown("# Privacyverklaring")
    st.markdown("Wij geven om je data. Geen verkoop aan derden. Geen opslag van wachtwoorden.")
    st.stop()

if page == "terms":
    st.markdown("<a href='/' target='_self' style='text-decoration:none;'>← Terug</a>", unsafe_allow_html=True)
    st.markdown("# Algemene Voorwaarden")
    st.markdown("Gebruik op eigen risico. Wij garanderen geen specifieke resultaten.")
    st.stop()

# --- MOBIELE ACTIE ---
if qp.get("mobile_action") == "demo":
    st.session_state.data_source = "demo"
    st.session_state.df = data_loader.load_demo_data()
    st.query_params.clear()
    st.rerun()

# --- AUTH ---
auth.init_session()

if not auth.is_authenticated():
    auth.render_landing_page()
    st.stop()

# --- APP START ---
chat_url = auth.get_secret("CHAT_SERVER_URL", "https://chatbot-2-0-3v8l.onrender.com")
ui.inject_chat_widget(chat_url)

# Data laden
if "df" not in st.session_state: 
    st.session_state.df = data_loader.load_demo_data()
    st.session_state.data_source = "demo"

df = analytics.calculate_kpis(st.session_state.df)
is_pro = auth.is_pro()

# Mobiele onboarding (onzichtbaar op desktop)
ui.render_mobile_onboarding()

# --- SIDEBAR ---
with st.sidebar:
    # Logo checken
    logo_path = "assets/logo.png"
    if Path(logo_path).exists():
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("## 🚀 PostAi")
    
    if is_pro:
        st.success("✅ PRO Geactiveerd")
    else:
        st.info(f"🧪 DEMO Modus")

    st.markdown("---")
    st.subheader("📂 Jouw Data")
    
    uploaded_file = st.file_uploader("Upload CSV/XLSX", type=['csv', 'xlsx'])
    if uploaded_file:
        st.session_state.df = analytics.clean_data(data_loader.load_file(uploaded_file))
        st.session_state.data_source = "upload"
        st.toast("Data geladen!")
        st.rerun()
        
    if st.button("⚡ Reset naar Demo"):
        st.session_state.df = data_loader.load_demo_data()
        st.session_state.data_source = "demo"
        st.rerun()

# --- DASHBOARD ---
ui.render_trust_bar(confidence=85 if st.session_state.data_source == "demo" else 95)

tabs = st.tabs(["🧠 Start", "🤖 Coach", "📊 Analyse", "🎯 Strategie", "⚙️ Instellingen"])
t_start, t_coach, t_analyse, t_strat, t_set = tabs

# TAB 1: START
with t_start:
    avg_views = int(df['Views'].mean()) if not df.empty else 0
    avg_eng = int(df['Engagement'].mean()) if 'Engagement' in df.columns else 0
    viral = int(df['Viral Score'].mean()) if 'Viral Score' in df.columns else 0
    ui.render_kpi_row(views=avg_views, engagement=avg_eng, viral_score=viral)

    best_time = analytics.get_best_posting_time(df)
    ui.render_mission_card(
        time=best_time,
        reason="meeste volgers online",
        hook="Gebruik een 'Wist je dat...' over je niche."
    )

    col_idea, col_space = st.columns([1, 1])
    with col_idea:
        if st.button("🎲 Genereer 1 Quick Win Idee", use_container_width=True):
            idea = ai_coach.get_quick_win_idea("Algemeen")
            st.info(f"💡 **Idee:** {idea}")

# TAB 2: COACH
with t_coach:
    st.subheader("🤖 AI Coach")
    if not is_pro:
        ui.render_locked_section("Volledige AI Coach")
    else:
        st.info("Coach is actief! Chat rechtsonder of gebruik de tools hier.")
        topic = st.text_input("Onderwerp voor script:")
        if st.button("Schrijf Script"):
            script = ai_coach.generate_script_from_data(topic, df.head())
            st.text_area("Script", script, height=300)

# TAB 3: ANALYSE
with t_analyse:
    st.subheader("📊 Analyse")
    with st.expander("📋 Resultaten-overzicht (gratis)", expanded=False):
        st.dataframe(df[['Datum', 'Views', 'Likes', 'Engagement', 'Caption']], use_container_width=True)
    with st.expander("🏷️ Hashtag-prestaties (gratis)", expanded=False):
        st.bar_chart(df.head(15).set_index('Caption')['Views'])
    with st.expander("📈 Wat werkt nu? (trends, PRO)", expanded=False):
        if not is_pro: ui.render_locked_section("Trends")
        else: st.write("Trend data...")
    with st.expander("🔁 Vergelijk perioden (A vs B, PRO)", expanded=False):
        if not is_pro: ui.render_locked_section("Vergelijken")
        else: st.write("Vergelijk tool...")

# TAB 4: STRATEGIE
with t_strat:
    st.subheader("🎯 Strategie")
    with st.expander("💡 Ideeëngenerator (gratis)", expanded=False):
        t = st.text_input("Onderwerp")
        if st.button("Genereer"): st.write("- Idee 1...")
    with st.expander("🔁 A/B-test planner (PRO)"):
        if not is_pro: ui.render_locked_section("A/B Planner")
        else: st.write("A/B Tool")
    
    st.markdown("### 🤖 AI-tools (PRO)")
    tools = ["AI Coach", "Check mijn hook/caption", "Caption & Hook generator", "Chat met PostAi"]
    for tool in tools:
        with st.expander(f"✨ {tool} (PRO)"):
            if not is_pro: ui.render_locked_section(tool)
            else: st.write(f"{tool} interface...")
            
    st.markdown("### 📅 Playbook & 7-dagen plan (PRO)")
    with st.expander("📅 Playbook & exports openen (PRO)"):
        if not is_pro: ui.render_locked_section("Playbook")
        else: st.write("Download opties...")
    
    st.markdown("### ⏳ Wachtrij (PRO)")
    with st.expander("Wachtrij beheren"):
        if not is_pro: ui.render_locked_section("Wachtrij")
        else: st.write("Wachtrij items...")

# TAB 5: INSTELLINGEN
with t_set:
    st.subheader("⚙️ Instellingen")
    
    # Licentie / PRO Status
    with st.container(border=True):
        st.markdown("#### 🔑 Licentie & PRO")
        if is_pro:
            st.success("Je PRO-licentie is actief!")
            if st.button("Uitloggen / Licentie verwijderen"):
                st.session_state.license_key = None
                st.rerun()
        else:
            st.warning("PRO is niet actief. Vul je sleutel in.")
            key_in = st.text_input("Licentiesleutel")
            if st.button("Activeer PRO", type="primary"):
                auth.activate_pro(key_in)
            st.markdown("---")
            st.markdown("[Koop PRO Licentie](https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2)")

    # Branding (PRO) met OPSLAAN KNOP
    with st.container(border=True):
        st.markdown("#### 🎨 Branding (PRO)")
        if not is_pro:
            ui.render_locked_section("Branding")
        else:
            st.markdown("Upload je eigen logo en kies je merkkleur.")
            
            # Formulier voor opslaan
            with st.form("branding_form"):
                new_color = st.color_picker("Merkkleur", value="#2563eb")
                new_logo = st.file_uploader("Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
                
                save_branding = st.form_submit_button("💾 Instellingen Opslaan")
                
                if save_branding:
                    # Opslaan in sessie (kleur)
                    st.session_state['brand_color'] = new_color
                    
                    # Opslaan bestand (logo)
                    if new_logo:
                        with open("assets/logo.png", "wb") as f:
                            f.write(new_logo.getbuffer())
                    
                    st.toast("Branding opgeslagen! Herladen...", icon="✅")
                    time.sleep(1)
                    st.rerun()

    # Data Opschonen
    with st.container(border=True):
        st.markdown("#### 🧹 Data opschonen")
        if st.button("Verwijder lokale data"):
            st.session_state.clear()
            st.rerun()

ui.render_footer()