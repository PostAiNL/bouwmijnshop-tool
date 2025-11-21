import streamlit as st
import pandas as pd
import time
from pathlib import Path
import os

# Modules importeren
from modules import analytics, ui, auth, ai_coach, data_loader

# --- CONFIG ---
st.set_page_config(page_title="PostAi – TikTok Growth", page_icon="📈", layout="wide")

# CSS laden
with open("assets/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# JS Injecties (voor mobiele optimalisatie & widget)
ui.inject_mobile_hacks()
chat_url = os.getenv("CHAT_SERVER_URL", "https://chatbot-2-0-3v8l.onrender.com")
ui.inject_chat_widget(server_url=chat_url)

# --- SESSION STATE SETUP ---
if "data_source" not in st.session_state: st.session_state.data_source = "demo"
if "df" not in st.session_state: 
    st.session_state.df = data_loader.load_demo_data() # Start altijd met data

# --- SIDEBAR ---
with st.sidebar:
    st.image("assets/logo.png" if Path("assets/logo.png").exists() else "https://placehold.co/200x60/png?text=PostAi", use_column_width=True)
    
    # Auth Status
    is_pro = auth.check_license()
    if is_pro:
        st.success("✅ PRO Actief")
    else:
        st.info("🧪 DEMO Modus")
        
    st.markdown("---")
    
    # Data Selectie
    st.subheader("📂 Jouw Data")
    
    # Stap 1: TikTok Login (Mockup voor OAuth flow)
    auth_url = auth.get_tiktok_auth_url()
    st.link_button("🔗 Koppel TikTok", auth_url, use_container_width=True, type="primary" if st.session_state.data_source == "demo" else "secondary")
    
    st.markdown("**OF**")
    
    # Stap 2: Upload
    uploaded_file = st.file_uploader("Upload CSV/XLSX", type=['csv', 'xlsx'])
    if uploaded_file:
        raw_df = data_loader.load_file(uploaded_file)
        st.session_state.df = analytics.clean_data(raw_df)
        st.session_state.data_source = "upload"
        st.success("Data geladen!")
        
    if st.button("🔄 Reset naar Demo Data"):
        st.session_state.df = data_loader.load_demo_data()
        st.session_state.data_source = "demo"
        st.rerun()

# --- MAIN LOGIC ---
df = analytics.calculate_kpis(st.session_state.df)
streak = analytics.get_consistency_streak(df)
best_time = analytics.get_best_posting_time(df)

# --- HEADER SECTIE ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Goedemorgen, Creator! 🚀")
    st.caption(f"Vandaag is een perfecte dag om te groeien. ({st.session_state.data_source} data actief)")
with col2:
    # Gamification element
    st.metric("🔥 Consistentie Streak", f"{streak} Dagen", delta=1 if streak > 0 else 0)

# --- TABS ---
tab_start, tab_coach, tab_analyse, tab_settings = st.tabs(["🧠 Start", "🤖 AI Coach", "📊 Analyse", "⚙️ Instellingen"])

# TAB 1: START (Actionable Dashboard)
with tab_start:
    # Hero Card: Wat moet ik NU doen?
    st.markdown(f"""
    <div class="hero-card">
        <h3>📅 Jouw Plan voor Vandaag</h3>
        <p>Op basis van je data is <strong>{best_time}:00</strong> het beste moment om te posten.</p>
        <div style="display:flex; gap:10px; margin-top:10px;">
            <div style="background:#eef2f7; padding:5px 10px; border-radius:5px;">✅ Stap 1: Film 15s video</div>
            <div style="background:#eef2f7; padding:5px 10px; border-radius:5px;">✅ Stap 2: Gebruik hook type 'vraag'</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Win Generator
    col_idea, col_kpi = st.columns([1, 1])
    
    with col_idea:
        with st.container(border=True):
            st.subheader("💡 Inspiratie nodig?")
            if st.button("🎲 Genereer 1 Quick Win Idee"):
                idea = ai_coach.get_quick_win_idea("Algemeen") # Niche kan uit settings komen
                st.info(f"**Idee:** {idea}")
    
    with col_kpi:
        # Simpele KPI overview
        avg_views = int(df['Views'].mean()) if not df.empty else 0
        st.metric("Gemiddelde Views", f"{avg_views:,}", "+12% vs vorige week")

# TAB 2: AI COACH (PRO Feature)
with tab_coach:
    st.header("Jouw Persoonlijke AI Scriptschrijver")
    
    col_input, col_output = st.columns(2)
    
    with col_input:
        topic = st.text_input("Waar wil je een video over maken?")
        style = st.select_slider("Toon", options=["Grappig", "Direct", "Educatief", "Controversieel"], value="Direct")
        
        if st.button("✨ Schrijf Script", type="primary"):
            if not is_pro and st.session_state.data_source == "demo":
                ui.show_pro_gate() # Toont upgrade popup
            else:
                with st.spinner("AI analyseert je beste video's..."):
                    # Gebruik top 5 posts voor context
                    top_posts = df.head(5)
                    script = ai_coach.generate_script_from_data(topic, top_posts, style)
                    st.session_state['last_script'] = script
    
    with col_output:
        if 'last_script' in st.session_state:
            st.text_area("Jouw Script", st.session_state['last_script'], height=300)
            st.button("Kopieer naar Klembord")
        else:
            st.info("👈 Vul een onderwerp in en laat AI het werk doen.")

# TAB 3: ANALYSE
with tab_analyse:
    st.subheader("Diepte Analyse")
    
    if df.empty:
        st.warning("Geen data beschikbaar.")
    else:
        # Interactieve grafiek (Altair is native in Streamlit)
        import altair as alt
        
        chart = alt.Chart(df.head(30)).mark_line(point=True).encode(
            x='Datum',
            y='Views',
            tooltip=['Datum', 'Views', 'Likes']
        ).interactive()
        
        st.altair_chart(chart, use_container_width=True)
        
        st.dataframe(df[['Datum', 'Views', 'Likes', 'Viral Score', 'Caption']], use_container_width=True)

# TAB 4: INSTELLINGEN
with tab_settings:
    st.text_input("Licentiesleutel", type="password", help="Vul je PRO key in")
    if st.button("Activeer Licentie"):
        st.success("Licentie geactiveerd! (Demo)")

# --- FOOTER ---
ui.render_footer()