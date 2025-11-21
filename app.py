import streamlit as st
import pandas as pd
import os
from pathlib import Path

from modules import analytics, ui, auth, ai_coach, data_loader

# --- CONFIG ---
st.set_page_config(page_title="PostAi – TikTok Growth", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
ui.inject_style_and_hacks()

# --- ROUTER (Privacy & Terms) ---
# We gebruiken query params. Als page=privacy, toon ALLEEN dat en stop.
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

# --- MOBIELE ACTIE CHECK ---
# Als iemand op de mobiele knop 'Demo' klikt
if qp.get("mobile_action") == "demo":
    st.session_state.data_source = "demo"
    st.session_state.df = data_loader.load_demo_data()
    # Reset de URL (zodat je niet in een loop komt)
    st.query_params.clear()
    st.rerun()

# --- AUTH CHECK ---
auth.init_session()

if not auth.is_authenticated():
    auth.render_landing_page()
    st.stop()

# --- APP START ---

# Chatbot laden (alleen als ingelogd)
chat_url = auth.get_secret("CHAT_SERVER_URL", "https://chatbot-2-0-3v8l.onrender.com")
ui.inject_chat_widget(chat_url)

# Data laden
if "df" not in st.session_state: 
    st.session_state.df = data_loader.load_demo_data()
    st.session_state.data_source = "demo"

df = analytics.calculate_kpis(st.session_state.df)
is_pro = auth.is_pro()

# --- MOBIELE ONBOARDING (Boven alles) ---
# Dit wordt getoond, maar door CSS in ui.py is het onzichtbaar op desktop!
ui.render_mobile_onboarding()

# Sidebar
with st.sidebar:
    if Path("assets/logo.png").exists():
        st.image("assets/logo.png", use_container_width=True)
    else:
        st.markdown("### PostAi 🚀")

    if is_pro:
        st.success("✅ PRO Geactiveerd")
    else:
        st.info("🧪 DEMO Modus")

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

# --- HOOFD SCHERM ---

# Trust Bar
ui.render_trust_bar(confidence=85 if st.session_state.data_source == "demo" else 95)

tabs = st.tabs(["🧠 Start", "🤖 Coach", "📊 Analyse", "🎯 Strategie", "⚙️ Instellingen"])
t_start, t_coach, t_analyse, t_strat, t_set = tabs

# TAB 1: START
with t_start:
    # KPI Cards
    avg_views = int(df['Views'].mean()) if not df.empty else 0
    avg_eng = int(df['Engagement'].mean()) if 'Engagement' in df.columns else 0
    viral = int(df['Viral Score'].mean()) if 'Viral Score' in df.columns else 0
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='kpi-card'><div class='kpi-label'>Weergaven (7d)</div><div class='kpi-value'>👁️ {avg_views:,}</div><div style='color:#16a34a; font-size:0.8rem'>+12.5%</div></div>".replace(",", "."), unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi-card'><div class='kpi-label'>Gem. reactiescore</div><div class='kpi-value'>💬 {avg_eng}%</div><div style='color:#16a34a; font-size:0.8rem'>+2.1%</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi-card'><div class='kpi-label'>Virale score</div><div class='kpi-value'>🔥 {viral}/100</div><div style='color:#16a34a; font-size:0.8rem'>+5 ptn</div></div>", unsafe_allow_html=True)

    # Missie Kaart
    best_time = analytics.get_best_posting_time(df)
    st.markdown(f"""
    <div class="hero-card" style="border:1px solid #bbf7d0; background:#f0fdf4;">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="background:#22c55e; color:white; width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center;">✓</div>
            <div>
                <h3 style="margin:0; font-size:1.1rem; color:#14532d;">Vandaag: 1 simpele TikTok taak</h3>
                <p style="margin:0; font-size:0.9rem; color:#166534;">Doe alleen deze stappen. Dan is vandaag goed.</p>
            </div>
        </div>
        <div style="margin-top:15px; padding-left:40px; font-size:0.95rem; color:#14532d;">
            <strong>Stap 1 - Tijd:</strong> Post vandaag 1 video rond <strong>{best_time}:00</strong>.<br>
            <strong>Stap 2 - Hook:</strong> Gebruik 'Wist je dat...' over je niche.<br>
            <strong>Stap 3 - Check:</strong> Check morgen pas de views.
        </div>
    </div>
    """, unsafe_allow_html=True)

# TAB 2: COACH
with t_coach:
    st.subheader("🤖 AI Coach")
    if not is_pro:
        ui.render_locked_section("Volledige AI Coach")
    else:
        st.info("Coach is actief! Chat rechtsonder of gebruik de tools hier.")
        topic = st.text_input("Waar moet het over gaan?")
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
    # De PRO tools
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
    
    if is_pro:
        st.success("Je bent PRO lid!")
        if st.button("Uitloggen / Licentie verwijderen"):
            st.session_state.license_key = None
            st.rerun()
    else:
        with st.container(border=True):
            st.markdown("#### 🔑 Licentie & PRO")
            key_in = st.text_input("Licentiesleutel")
            if st.button("Activeer PRO", type="primary"):
                if auth.activate_pro(key_in):
                    pass # Refresh handled in activate_pro
            
            st.markdown("---")
            st.markdown("[Koop PRO Licentie](https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2)")

    # Branding (PRO)
    with st.container(border=True):
        st.markdown("#### 🎨 Branding (PRO)")
        if not is_pro:
            ui.render_locked_section("Branding")
        else:
            st.color_picker("Merkkleur")
            st.file_uploader("Logo")

    # Data
    with st.container(border=True):
        st.markdown("#### 🧹 Data opschonen")
        if st.button("Verwijder lokale data"):
            st.session_state.clear()
            st.rerun()

ui.render_footer()