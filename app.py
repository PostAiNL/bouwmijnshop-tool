import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Modules
from modules import analytics, ui, auth, ai_coach, data_loader

# --- CONFIG ---
st.set_page_config(page_title="PostAi – TikTok Growth", page_icon="📈", layout="wide")
ui.inject_style_and_hacks()

# Chatbot (altijd laden, hij regelt zelf of hij zichtbaar is)
chat_url = os.getenv("CHAT_SERVER_URL", "https://chatbot-2-0-3v8l.onrender.com")
ui.inject_chat_widget(server_url=chat_url)

# --- AUTH & ROUTING ---
auth.init_session()

# Router: Als niet ingelogd -> Landing Page
if not auth.is_authenticated():
    auth.render_landing_page()
    st.stop() # Stop hier, laat de rest van de app niet zien

# --- APP LOGICA (Alleen zichtbaar na login) ---

# Data laden
if "df" not in st.session_state: st.session_state.df = data_loader.load_demo_data()
df = analytics.calculate_kpis(st.session_state.df) # Zorg dat deze functie in analytics.py bestaat!
if 'Viral Score' not in df.columns: df['Viral Score'] = 50 # Fallback

# Check PRO status
is_pro = auth.is_pro()

# --- SIDEBAR ---
with st.sidebar:
    if Path("assets/logo.png").exists():
        st.image("assets/logo.png", use_container_width=True)
    else:
        st.markdown("## 🚀 PostAi")
    
    if is_pro:
        st.success("✅ PRO Geactiveerd")
    else:
        st.info(f"🧪 DEMO Modus (Verloopt over 14 dgn)")

    st.markdown("---")
    st.subheader("📂 Jouw Data")
    uploaded_file = st.file_uploader("Upload CSV/XLSX", type=['csv', 'xlsx'])
    if uploaded_file:
        raw_df = data_loader.load_file(uploaded_file)
        # Let op: analytics.clean_data moet bestaan!
        st.session_state.df = raw_df 
        st.toast("Data geladen!")
        st.rerun()
        
    if st.button("⚡ Reset Data"):
        st.session_state.df = data_loader.load_demo_data()
        st.rerun()

# --- DASHBOARD ---

# 1. Vertrouwen balk
conf = analytics.calculate_confidence(df) if hasattr(analytics, 'calculate_confidence') else 85
ui.render_trust_bar(confidence=conf)

# 2. Tabs
tabs = st.tabs(["🧠 Start", "🤖 Coach", "📊 Analyse", "🎯 Strategie", "⚙️ Instellingen"])
t_start, t_coach, t_analyse, t_strat, t_set = tabs

with t_start:
    # KPI Rij (Bovenaan!)
    avg_views = int(df['Views'].mean()) if not df.empty else 0
    avg_eng = int(df['Engagement'].mean()) if 'Engagement' in df.columns else 0
    avg_viral = int(df['Viral Score'].mean()) if 'Viral Score' in df.columns else 0
    ui.render_kpi_row(views=avg_views, engagement=avg_eng, viral_score=avg_viral)

    # Missie Kaart
    best_time = analytics.get_best_posting_time(df) if hasattr(analytics, 'get_best_posting_time') else 19
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

with t_coach:
    st.subheader("🤖 AI Coach")
    if not is_pro:
        ui.render_locked_section("Persoonlijke AI Coach")
    else:
        st.write("De coach staat klaar! Gebruik de chat rechtsonder.")
        topic = st.text_input("Onderwerp voor script:")
        if st.button("Schrijf Script"):
            s = ai_coach.generate_script_from_data(topic, df.head())
            st.text_area("Script", s, height=300)

with t_analyse:
    st.subheader("📊 Analyse")
    st.dataframe(df.head(10), use_container_width=True)
    
    if not is_pro:
        ui.render_locked_section("Trend Analyse & Vergelijken")
    else:
        st.write("PRO Grafieken hier...")

with t_strat:
    st.subheader("🎯 Strategie")
    with st.expander("Ideeëngenerator (Gratis)"):
        st.write("Ideeën...")
        
    if not is_pro:
        ui.render_locked_section("A/B Test Planner")
    else:
        st.write("A/B Tester hier...")

with t_set:
    st.subheader("⚙️ Instellingen")
    
    # Branding (PRO)
    if not is_pro:
        ui.render_locked_section("Branding & Logo")
    else:
        st.file_uploader("Upload je logo")
        st.color_picker("Merkkleur")

    st.markdown("---")
    
    # Licentie activatie
    with st.container(border=True):
        st.markdown("#### 🔑 Licentie")
        if is_pro:
            st.success("Je licentie is actief.")
        else:
            key_in = st.text_input("Heb je een sleutel? Vul hem hier in:")
            if st.button("Activeer PRO"):
                auth.activate_pro(key_in)
            
            st.markdown("---")
            st.markdown("[Koop PRO Licentie (Lemon Squeezy)](https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2)")

    # Data wipe
    if st.button("🧹 Data Opschonen (Privacy)"):
        st.session_state.clear()
        st.rerun()

ui.render_footer()