import streamlit as st
import pandas as pd
import time
import os
from pathlib import Path

# Modules importeren
from modules import analytics, ui, auth, ai_coach, data_loader

# --- CONFIG ---
st.set_page_config(page_title="PostAi – TikTok Growth", page_icon="📈", layout="wide")

# CSS laden
try:
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    # Fallback als de 's' nog niet goed staat
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# JS Injecties
ui.inject_mobile_hacks()
chat_url = os.getenv("CHAT_SERVER_URL", "https://chatbot-2-0-3v8l.onrender.com")
ui.inject_chat_widget(server_url=chat_url)

# --- SESSION STATE SETUP ---
if "data_source" not in st.session_state: st.session_state.data_source = "demo"
if "df" not in st.session_state: 
    st.session_state.df = data_loader.load_demo_data()

# --- SIDEBAR ---
with st.sidebar:
    logo_path = "assets/logo.png"
    if Path(logo_path).exists():
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("## PostAi 🚀")
    
    is_pro = auth.check_license()
    if is_pro:
        st.success("✅ PRO Actief")
    else:
        st.info("🧪 DEMO Modus")
        
    st.markdown("---")
    st.subheader("📂 Jouw Data")
    
    # Upload
    uploaded_file = st.file_uploader("Upload CSV/XLSX", type=['csv', 'xlsx'])
    if uploaded_file:
        raw_df = data_loader.load_file(uploaded_file)
        st.session_state.df = analytics.clean_data(raw_df)
        st.session_state.data_source = "upload"
        st.toast("Data succesvol geladen!", icon="📊")
        
    if st.button("🔄 Reset naar Demo Data"):
        st.session_state.df = data_loader.load_demo_data()
        st.session_state.data_source = "demo"
        st.rerun()

# --- MAIN LOGIC ---
df = analytics.calculate_kpis(st.session_state.df)
streak = analytics.get_consistency_streak(df)
best_time = analytics.get_best_posting_time(df)

# --- HEADER ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Goedemorgen, Creator! 🚀")
    st.caption(f"Vandaag is een perfecte dag om te groeien. ({st.session_state.data_source} data actief)")
with col2:
    st.metric("🔥 Consistentie Streak", f"{streak} Dagen", delta=1 if streak > 0 else 0)

# --- TABS ---
tab_start, tab_coach, tab_analyse, tab_strategy, tab_settings = st.tabs([
    "🧠 Start", "🤖 AI Coach", "📊 Analyse", "🎯 Strategie", "⚙️ Instellingen"
])

# === TAB 1: START ===
with tab_start:
    st.markdown(f"""
    <div class="hero-card">
        <h3>📅 Jouw Plan voor Vandaag</h3>
        <p>Op basis van je data is <strong>{best_time}:00</strong> het beste moment om te posten.</p>
        <div style="display:flex; gap:10px; margin-top:10px; flex-wrap:wrap;">
            <div style="background:#eef2f7; padding:5px 10px; border-radius:5px;">✅ Stap 1: Film 15s video</div>
            <div style="background:#eef2f7; padding:5px 10px; border-radius:5px;">✅ Stap 2: Gebruik hook type 'vraag'</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_idea, col_kpi = st.columns([1, 1])
    with col_idea:
        with st.container(border=True):
            st.subheader("💡 Inspiratie nodig?")
            if st.button("🎲 Genereer 1 Quick Win Idee", use_container_width=True):
                idea = ai_coach.get_quick_win_idea("Algemeen")
                st.info(f"**Idee:** {idea}")
    
    with col_kpi:
        avg_views = int(df['Views'].mean()) if not df.empty else 0
        st.metric("Gemiddelde Views", f"{avg_views:,}", "+12% vs vorige week")

# === TAB 2: AI COACH ===
with tab_coach:
    st.header("Jouw Persoonlijke AI Scriptschrijver")
    col_input, col_output = st.columns(2)
    
    with col_input:
        topic = st.text_input("Waar wil je een video over maken?")
        style = st.select_slider("Toon", options=["Grappig", "Direct", "Educatief", "Controversieel"], value="Direct")
        
        if st.button("✨ Schrijf Script", type="primary", use_container_width=True):
            if not is_pro and st.session_state.data_source == "demo":
                ui.show_pro_gate()
            else:
                with st.spinner("AI analyseert je beste video's..."):
                    top_posts = df.head(5)
                    script = ai_coach.generate_script_from_data(topic, top_posts, style)
                    st.session_state['last_script'] = script
    
    with col_output:
        if 'last_script' in st.session_state:
            st.text_area("Jouw Script", st.session_state['last_script'], height=350)
        else:
            st.info("👈 Vul een onderwerp in en laat AI het werk doen.")

# === TAB 3: ANALYSE ===
with tab_analyse:
    st.subheader("Diepte Analyse")
    if df.empty:
        st.warning("Geen data beschikbaar.")
    else:
        import altair as alt
        chart = alt.Chart(df.head(30)).mark_line(point=True).encode(
            x='Datum', y='Views', tooltip=['Datum', 'Views', 'Likes']
        ).interactive()
        st.altair_chart(chart, use_container_width=True)
        
        st.markdown("### 📋 Recente Posts")
        st.dataframe(
            df[['Datum', 'Views', 'Likes', 'Engagement', 'Viral Score', 'Caption']], 
            use_container_width=True,
            hide_index=True
        )

# === TAB 4: STRATEGIE (De ontbrekende functies) ===
with tab_strategy:
    st.subheader("🎯 Content Strategie & A/B Testen")
    
    with st.expander("🔁 A/B Test Planner", expanded=True):
        if not is_pro and st.session_state.data_source == "demo":
            ui.show_pro_gate()
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Variant A**")
                hook_a = st.text_input("Hook A", "Wat niemand je vertelt over...")
            with c2:
                st.markdown("**Variant B**")
                hook_b = st.text_input("Hook B", "De grootste fout bij...")
            
            if st.button("🚀 Bereken Winnaar Kans"):
                import random
                score_a = random.randint(70, 95)
                score_b = random.randint(60, 90)
                winner = "A" if score_a > score_b else "B"
                st.success(f"De AI voorspelt dat **Variant {winner}** {abs(score_a - score_b)}% beter zal scoren.")

    with st.expander("📅 Wachtrij & Planning"):
        st.write("Hier kun je je geplande video's beheren.")
        if 'queue' not in st.session_state: st.session_state.queue = []
        
        new_item = st.text_input("Nieuw idee voor wachtrij")
        if st.button("Toevoegen"):
            st.session_state.queue.append(new_item)
            st.rerun()
            
        for i, item in enumerate(st.session_state.queue):
            st.text(f"{i+1}. {item}")

# === TAB 5: INSTELLINGEN ===
with tab_settings:
    st.markdown("### ⚙️ Account")
    key_input = st.text_input("Licentiesleutel", type="password", help="Vul je PRO key in")
    
    if st.button("Activeer Licentie"):
        # In het echt sla je dit op in cookies of db
        if key_input:
            st.session_state.license_key = key_input
            st.success("Licentie gecheckt! Herlaad de pagina.")
            time.sleep(1)
            st.rerun()

# --- FOOTER ---
ui.render_footer()