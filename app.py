import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Modules importeren
from modules import analytics, ui, auth, ai_coach, data_loader

# --- CONFIG ---
st.set_page_config(page_title="PostAi – TikTok Growth", page_icon="📈", layout="wide")

# Styling laden
ui.inject_style_and_hacks()

# Chatbot laden
chat_url = os.getenv("CHAT_SERVER_URL", "https://chatbot-2-0-3v8l.onrender.com")
ui.inject_chat_widget(server_url=chat_url)

# --- STATE SETUP ---
if "data_source" not in st.session_state: st.session_state.data_source = "demo"
if "df" not in st.session_state: st.session_state.df = data_loader.load_demo_data()

# --- SIDEBAR ---
with st.sidebar:
    if Path("assets/logo.png").exists():
        st.image("assets/logo.png", use_container_width=True)
    else:
        st.markdown("## 🚀 PostAi")
    
    # PRO STATUS CHECK
    is_pro = auth.check_license()
    
    if is_pro:
        st.markdown("""
        <div style="background:#dcfce7; padding:8px; border-radius:8px; color:#166534; font-weight:bold; text-align:center; border:1px solid #bbf7d0; margin-bottom:20px;">
           ✅ PRO Geactiveerd
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#e0f2fe; padding:8px; border-radius:8px; color:#0369a1; font-weight:bold; text-align:center; border:1px solid #bae6fd; margin-bottom:20px;">
           🧪 DEMO Modus
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📂 Jouw Data")
    
    # Koppel TikTok
    st.link_button("🔗 Koppel TikTok", auth.get_tiktok_auth_url(), use_container_width=True, type="primary")
    st.caption("Of gebruik een bestand:")
    
    # Upload
    uploaded_file = st.file_uploader("Upload CSV/XLSX", type=['csv', 'xlsx'])
    if uploaded_file:
        raw_df = data_loader.load_file(uploaded_file)
        st.session_state.df = analytics.clean_data(raw_df)
        st.session_state.data_source = "upload"
        st.toast("Data geladen!")
        st.rerun() # Direct verversen
        
    if st.button("⚡ Reset naar Demo Data", use_container_width=True):
        st.session_state.df = data_loader.load_demo_data()
        st.session_state.data_source = "demo"
        st.rerun()

# --- HOOFD SCHERM ---
df = analytics.calculate_kpis(st.session_state.df)
streak = analytics.get_consistency_streak(df)
best_time = analytics.get_best_posting_time(df)

# Header
c1, c2 = st.columns([3, 1])
with c1:
    st.title("Goedemorgen, Creator! 🚀")
    st.caption(f"Vandaag is een perfecte dag om te groeien. (Bron: {st.session_state.data_source})")
with c2:
    st.metric("🔥 Consistentie Streak", f"{streak} Dagen")

# Tabs
tabs = st.tabs(["🧠 Start", "🤖 Coach", "📊 Analyse", "🎯 Strategie", "⚙️ Instellingen"])
t_start, t_coach, t_analyse, t_strat, t_set = tabs

# === TAB 1: START ===
with t_start:
    st.subheader("Start - eerste stappen")
    
    st.info(f"📅 **Jouw plan voor vandaag:** Post om **{best_time}:00** uur.")
    
    # Mini script
    with st.container(border=True):
        st.markdown("### 🎬 Mini-script voor vandaag")
        st.text("Hook: 'Ik wou dat ik dit eerder wist over [jouw niche]...'")
        st.text("Body: Vertel 1 veelgemaakte fout en hoe het wél moet.")
        st.text("CTA: 'Volg voor meer tips.'")

    col_idea, col_kpi = st.columns(2)
    with col_idea:
        if st.button("🎲 Genereer 1 Quick Win Idee", use_container_width=True):
            idea = ai_coach.get_quick_win_idea("Algemeen")
            st.success(f"**Idee:** {idea}")
    with col_kpi:
        st.metric("Gemiddelde Views", f"{int(df['Views'].mean()):,}")

# === TAB 2: COACH (PRO ONLY) ===
with t_coach:
    st.subheader("🤖 AI Coach (PRO)")
    
    if not is_pro:
        ui.render_locked_section("Volledige AI Coach")
    else:
        st.write("De coach staat klaar. Stel je vraag in de chat rechtsonder of gebruik de tools hier.")
        topic = st.text_input("Waar gaat je video over?")
        if st.button("✨ Schrijf Script"):
            with st.spinner("Bezig..."):
                script = ai_coach.generate_script_from_data(topic, df.head(5))
                st.text_area("Script", script, height=300)

# === TAB 3: ANALYSE (Zoals screenshot) ===
with t_analyse:
    st.subheader("📊 Analyse - duidelijk voor iedereen")
    
    # 1. Resultaten overzicht (Gratis)
    with st.expander("📋 Resultaten-overzicht (gratis)", expanded=False):
        st.dataframe(df[['Datum', 'Views', 'Likes', 'Engagement', 'Caption']], use_container_width=True)

    # 2. Hashtags (Gratis)
    with st.expander("🏷️ Hashtag-prestaties (gratis)", expanded=False):
        st.write("Hier zie je welke hashtags het beste werken.")
        # Dummy logica voor nu, kan later uitgebreid
        st.bar_chart(df.head(10).set_index('Caption')['Views'])

    # 3. Trends (PRO)
    with st.expander("📈 Wat werkt nu? (trends, PRO)", expanded=False):
        if not is_pro:
            ui.render_locked_section("Trend Analyse")
        else:
            st.success("Je populairste onderwerpen van de laatste 14 dagen:")
            st.write("1. #Tutorials")
            st.write("2. #BehindTheScenes")

    # 4. Vergelijk (PRO)
    with st.expander("🔁 Vergelijk perioden (A vs. B, PRO)", expanded=False):
        if not is_pro:
            ui.render_locked_section("Periode Vergelijker")
        else:
            c1, c2 = st.columns(2)
            c1.date_input("Periode A")
            c2.date_input("Periode B")
            st.info("Selecteer data om te vergelijken.")

# === TAB 4: STRATEGIE (Zoals screenshot) ===
with t_strat:
    st.subheader("🎯 Strategie - makkelijk testen")
    
    st.markdown("### 🧪 Ideeën & testen")
    
    # Ideeëngenerator (Gratis)
    with st.expander("💡 Ideeëngenerator (gratis)", expanded=False):
        topic_idea = st.text_input("Onderwerp", key="idea_gen")
        if st.button("Geef ideeën"):
            st.write(f"1. 3 Fouten bij {topic_idea}")
            st.write(f"2. Hoe ik begon met {topic_idea}")
            
    # A/B Planner (PRO)
    with st.expander("🔁 A/B-test planner (PRO)", expanded=False):
        if not is_pro:
            ui.render_locked_section("A/B Test Planner")
        else:
            st.text_input("Hook A")
            st.text_input("Hook B")
            st.button("Sla test op")

    st.markdown("### 🤖 AI-tools (PRO)")
    
    # AI Coach
    with st.expander("🧠 AI Coach - persoonlijk advies (PRO)"):
        if not is_pro: ui.render_locked_section("AI Coach")
        else: st.write("Gebruik de chat rechtsonder voor direct advies!")

    # Hook Check
    with st.expander("✍️ Check mijn hook/caption (PRO)"):
        if not is_pro: ui.render_locked_section("Hook/caption check")
        else: 
            hook = st.text_input("Plak je hook")
            if st.button("Check"): st.success("Sterke hook! 8/10")

    # Generator
    with st.expander("🪄 Caption & Hook generator (PRO)"):
        if not is_pro: ui.render_locked_section("Caption & Hook generator")
        else: st.write("Generator tools hier...")

    # Chat
    with st.expander("💬 Chat met PostAi (PRO)"):
        if not is_pro: ui.render_locked_section("Chat functie")
        else: st.write("De chat widget staat rechtsonder.")

    st.markdown("### 📅 Playbook & 7-dagen plan (PRO)")
    
    with st.expander("📅 Playbook & exports openen (PRO)"):
        if not is_pro: ui.render_locked_section("Playbook & Exports")
        else: st.button("Download PDF Plan")

# === TAB 5: INSTELLINGEN ===
with t_set:
    st.subheader("⚙️ Instellingen")
    
    with st.container(border=True):
        st.markdown("#### 🔑 Licentie & PRO")
        
        if is_pro:
            st.success("Je PRO-licentie is actief! Alle functies zijn ontgrendeld.")
            if st.button("Licentie deactiveren (Log uit)"):
                st.session_state.is_pro_session = False
                st.rerun()
        else:
            st.warning("PRO is niet actief. Vul je sleutel in.")
            key = st.text_input("Licentiesleutel", type="password")
            if st.button("🔓 Activeer PRO", type="primary"):
                auth.activate_license(key)

# Footer
ui.render_footer()