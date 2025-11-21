import streamlit as st
import pandas as pd
import os
from pathlib import Path

from modules import analytics, ui, auth, ai_coach, data_loader

# --- CONFIG ---
st.set_page_config(page_title="PostAi – TikTok Growth", page_icon="📈", layout="wide")
ui.inject_style_and_hacks()

# --- ROUTER VOOR SIMPELE PAGINA'S (Privacy & Voorwaarden) ---
def route_simple_pages():
    """Checkt of we een tekstpagina moeten laten zien."""
    try:
        # Haal query param op (werkt voor nieuwe en oude streamlit versies)
        qp = st.query_params
        page = qp.get("page")
    except:
        page = None

    if page == "privacy":
        st.markdown("""
        <div style="max-width:800px; margin:0 auto; padding:40px 20px; background:#fff; border-radius:16px; border:1px solid #e5e7eb; margin-top:40px;">
            <a href="/" style="text-decoration:none; color:#2563eb; font-weight:bold;">← Terug naar Home</a>
            <h1 style="margin-top:20px;">Privacyverklaring</h1>
            <p style="color:#666; font-size:0.9rem;">Laatst bijgewerkt: 21 november 2025</p>
            <hr style="margin:20px 0; border:0; border-top:1px solid #eee;">
            
            <h3>1. Inleiding</h3>
            <p>PostAi respecteert de privacy van alle gebruikers en draagt er zorg voor dat de persoonlijke informatie die u ons verschaft vertrouwelijk wordt behandeld.</p>
            
            <h3>2. Welke gegevens verzamelen we?</h3>
            <ul>
                <li>Naam en e-mailadres (voor accounttoegang).</li>
                <li>TikTok statistieken (geüpload via CSV of gekoppeld) om de dashboards te tonen.</li>
                <li>Licentiesleutel gegevens.</li>
            </ul>

            <h3>3. Hoe gebruiken we deze gegevens?</h3>
            <p>De gegevens worden uitsluitend gebruikt om de functionaliteit van de app te bieden (analyses, advies). We verkopen uw gegevens <strong>nooit</strong> aan derden.</p>

            <h3>4. Bewaartermijn</h3>
            <p>U kunt te allen tijde uw lokale data wissen via de instellingen in de app ("Data Opschonen").</p>
            
            <br>
            <p>Vragen? Mail naar <a href="mailto:info@bouwmijnshop.nl">info@bouwmijnshop.nl</a></p>
        </div>
        """, unsafe_allow_html=True)
        st.stop() # Stop de rest van de app

    elif page == "terms":
        st.markdown("""
        <div style="max-width:800px; margin:0 auto; padding:40px 20px; background:#fff; border-radius:16px; border:1px solid #e5e7eb; margin-top:40px;">
            <a href="/" style="text-decoration:none; color:#2563eb; font-weight:bold;">← Terug naar Home</a>
            <h1 style="margin-top:20px;">Algemene Voorwaarden</h1>
            <p style="color:#666; font-size:0.9rem;">Laatst bijgewerkt: 21 november 2025</p>
            <hr style="margin:20px 0; border:0; border-top:1px solid #eee;">
            
            <h3>1. Algemeen</h3>
            <p>Deze voorwaarden zijn van toepassing op elk gebruik van de webapplicatie PostAi.</p>
            
            <h3>2. Gebruik van de dienst</h3>
            <p>PostAi is een hulpmiddel voor TikTok groei. Wij garanderen geen specifieke resultaten (zoals aantallen views of volgers), aangezien dit afhankelijk is van het algoritme van TikTok en uw eigen content.</p>

            <h3>3. Abonnementen</h3>
            <p>De PRO-versie wordt gefactureerd via Lemon Squeezy. Restitutie is mogelijk binnen 7 dagen na aankoop indien de dienst niet bevalt.</p>

            <h3>4. Aansprakelijkheid</h3>
            <p>PostAi is niet aansprakelijk voor directe of indirecte schade als gevolg van het gebruik van de applicatie.</p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

# Voer router uit
route_simple_pages()

# Chatbot url ophalen
chat_url = auth.get_secret("CHAT_SERVER_URL", "https://chatbot-2-0-3v8l.onrender.com")
ui.inject_chat_widget(chat_url)

# --- AUTH CHECK ---
auth.init_session()

# Als de gebruiker nog NIET is ingelogd (geen licentie in sessie)
if not auth.is_authenticated():
    # Toon formulier
    auth.render_landing_page()
    # STOP hier. Laad de rest van de app (en de chatbot) niet.
    st.stop()

# =========================================================
# HIERONDER KOMEN WE PAS ALS IEMAND INGELOGD IS (DEMO/PRO)
# =========================================================

# 2. NU pas de Chatbot laden (zodat hij niet op de landingspagina staat)
chat_url = auth.get_secret("CHAT_SERVER_URL", "https://chatbot-2-0-3v8l.onrender.com")
ui.inject_chat_widget(chat_url)

# --- APP LOGICA ---

# Data laden
if "df" not in st.session_state: 
    st.session_state.df = data_loader.load_demo_data()
    st.session_state.data_source = "demo"

df = analytics.calculate_kpis(st.session_state.df)
is_pro = auth.is_pro()

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