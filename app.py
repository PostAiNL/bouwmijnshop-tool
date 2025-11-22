import streamlit as st
import pandas as pd
import random
import datetime
import json
from modules import analytics, ui, auth, ai_coach, data_loader

# --- CONFIG ---
st.set_page_config(page_title="PostAi", page_icon="🚀", layout="centered", initial_sidebar_state="collapsed")
auth.init_session()
ui.inject_style_and_hacks(brand_color="#10b981")

# --- ROUTING & AUTH ---
if not auth.is_authenticated():
    auth.render_landing_page()
    st.stop()

# --- STATE & DATA ---
user_data = auth.load_progress()
if "df" not in st.session_state: st.session_state.df = pd.DataFrame() 
if "streak" not in st.session_state: st.session_state.streak = user_data.get("streak", 0)
if "level" not in st.session_state: st.session_state.level = user_data.get("level", 1)
if "xp" not in st.session_state: st.session_state.xp = user_data.get("xp", 10)
if "user_niche" not in st.session_state: st.session_state.user_niche = user_data.get("niche", "")

is_pro = auth.is_pro()

# --- HEADER ---
ui.render_header(is_pro, st.session_state.level)

# --- ONBOARDING ---
if not st.session_state.user_niche:
    st.markdown("---")
    with st.container(border=True):
        st.markdown("### 👋 Welkom! Even voorstellen...")
        st.info("Ik ben je nieuwe AI Strateeg. Om te beginnen moet ik weten waar je account over gaat.")
        niche_in = st.text_input("Waar ben je expert in?", placeholder="bv. Koken, Boekhouding, Honden training...")
        if st.button("🚀 Start mijn reis", type="primary"):
            if niche_in:
                st.session_state.user_niche = niche_in
                auth.save_progress(niche=niche_in)
                st.rerun()
    st.stop()

# --- DASHBOARD ---
c1, c2 = st.columns([0.85, 0.15])
with c1: st.markdown(f"<div class='niche-edit-bar'><span>🎯 Je focus: <b>{st.session_state.user_niche}</b></span></div>", unsafe_allow_html=True)
with c2:
    if st.button("✏️", key="edit_niche", help="Verander je onderwerp"): 
        st.session_state.user_niche = ""; auth.save_progress(niche=""); st.rerun()

# NIEUWE TAB STRUKTUUR: WORKFLOW TOEGEVOEGD
t_studio, t_workflow, t_tools, t_data, t_set = st.tabs(["🎬 Studio", "🗂️ Workflow", "✨ Tools", "📊 Cijfers", "⚙️"])

# 1. STUDIO TAB
with t_studio:
    st.markdown(f"<h3 style='margin-bottom:10px;'>Nieuwe Video Maken</h3>", unsafe_allow_html=True)
    
    with st.container(border=True):
        mode = st.radio("Kies je doel:", ["👀 Viral gaan (Views & Groei)", "💸 Geld Verdienen (Sales & UGC)"], horizontal=True, label_visibility="collapsed")

        if mode == "👀 Viral gaan (Views & Groei)":
            col_in, col_dice = st.columns([0.85, 0.15], vertical_alignment="bottom")
            with col_in:
                default_val = st.session_state.get("idea_input", "")
                topic = st.text_input("1. Onderwerp", value=default_val, placeholder="Bv. 3 fouten die starters maken...")
            with col_dice:
                if st.button("🎲"):
                    ideas = [f"De grootste fout in {st.session_state.user_niche}", "Handige tool", "Snelle tip", "Mijn mening"]
                    st.session_state.idea_input = random.choice(ideas); st.rerun()

            c_fmt, c_tone = st.columns(2)
            with c_fmt: vid_format = st.selectbox("2. Format", ["🗣️ Ik vertel iets", "🟩 Green Screen", "📸 Vlog", "📝 Lijstje"])
            with c_tone: tone = st.selectbox("3. Toon", ["⚡ Energiek", "😌 Rustig", "😂 Humor", "🎓 Serieus"])

            hooks = ai_coach.get_viral_hooks_library()
            selected_hook = st.selectbox("4. Opening (Hook)", hooks)
            cta_type = st.selectbox("5. Doel", ["➕ Volgers", "💬 Reacties", "↗️ Delen"])
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("✨ Schrijf Viral Script", type="primary", use_container_width=True):
                if not is_pro and st.session_state.get("daily_gen_count", 0) >= 1:
                    st.error("⚠️ Daglimiet bereikt. Upgrade naar PRO.")
                else:
                    with st.spinner("De regisseur schrijft..."):
                        style_prompt = user_data.get("my_style", "")
                        final_hook = selected_hook.replace("{onderwerp}", topic if topic else "dit")
                        script = ai_coach.generate_script(topic, vid_format, tone, final_hook, cta_type, st.session_state.user_niche, style_prompt)
                        st.session_state.last_script = script
                        st.session_state.current_topic = topic if topic else "Viral Video"
                        st.session_state.daily_gen_count = st.session_state.get("daily_gen_count", 0) + 1
                        st.session_state.xp += 10
                        auth.save_progress(xp=st.session_state.xp); st.rerun()

        else:
            st.markdown("<div style='background:#ecfdf5; border-left:4px solid #10b981; padding:10px; font-size:0.9rem;'>💰 <b>Cashflow Modus</b></div>", unsafe_allow_html=True)
            col_p, col_pain = st.columns(2)
            with col_p: product_name = st.text_input("Wat verkoop je?", placeholder="Mijn E-book...")
            with col_pain: pain_point = st.text_input("Welk probleem los je op?", placeholder="Geldzorgen...")
            sales_angle = st.selectbox("Strategie", ["😱 PAS (Problem-Agitate-Solution)", "📦 Demo", "⭐ Testimonial"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💸 Schrijf Sales Script", type="primary", use_container_width=True):
                if not is_pro: ui.render_locked_section("Cashflow Script", "Zet views om in Euro's.")
                else:
                    if not product_name or not pain_point: st.error("Vul alle velden in.")
                    else:
                        with st.spinner("De copywriter schrijft..."):
                            script = ai_coach.generate_sales_script(product_name, pain_point, sales_angle, st.session_state.user_niche)
                            st.session_state.last_script = script
                            st.session_state.current_topic = f"Sales: {product_name}"
                            st.session_state.xp += 20
                            auth.save_progress(xp=st.session_state.xp); st.rerun()

    # RESULTAAT MET OPSLAAN KNOP
    if "last_script" in st.session_state:
        st.success("💡 Script is klaar!")
        
        # NIEUW: OPSLAAN NAAR LIBRARY
        c_save, c_audit = st.columns(2)
        with c_save:
            if st.button("💾 Opslaan in Workflow", type="secondary", use_container_width=True):
                if not is_pro:
                    st.toast("🔒 Alleen voor PRO leden")
                else:
                    auth.save_script_to_library(st.session_state.get("current_topic", "Script"), st.session_state.last_script, "Viral" if mode.startswith("👀") else "Sales")
                    st.toast("✅ Opgeslagen in Workflow Tab!")
        
        with c_audit:
            if st.button("🔍 Audit (Score)", type="secondary", use_container_width=True):
                if not is_pro: st.toast("🔒 Alleen voor PRO")
                else:
                    with st.spinner("Checken..."):
                        st.session_state.script_score = ai_coach.audit_script(st.session_state.last_script, st.session_state.user_niche)
                        st.rerun()

        if "script_score" in st.session_state:
            s = st.session_state.script_score
            st.info(f"**Score: {s.get('score')}/100** - {s.get('verdict')}")

        st.markdown(st.session_state.last_script)
        st.markdown("---")
        if st.button("✅ Gefilmd & Klaar!", type="secondary"):
            st.session_state.streak += 1; st.session_state.xp += 20; st.balloons()
            del st.session_state.last_script
            if "script_score" in st.session_state: del st.session_state.script_score
            st.rerun()

# 2. WORKFLOW TAB (NIEUWE FEATURE)
with t_workflow:
    st.markdown("### 🗂️ Content Management")
    if not is_pro:
        ui.render_locked_section("Content Workflow", "Beheer al je scripts op één plek. Van idee tot gepost.")
    else:
        library = auth.get_user_library()
        if not library:
            st.info("Je bibliotheek is leeg. Sla scripts op in de Studio!")
        else:
            # Weergave als lijst met statussen
            for s in library:
                with st.expander(f"{s.get('status', 'Script')} | {s.get('topic', 'Naamloos')} ({s.get('date')})"):
                    st.markdown(s.get("content"))
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("🎥 Gefilmd", key=f"f_{s['id']}"):
                            auth.update_script_status(s['id'], "✅ Gefilmd")
                            st.rerun()
                    with c2:
                        if st.button("🚀 Gepost", key=f"p_{s['id']}"):
                            auth.update_script_status(s['id'], "🚀 Gepost")
                            st.rerun()
                    with c3:
                        if st.button("🗑️ Verwijder", key=f"d_{s['id']}"):
                            auth.delete_script(s['id'])
                            st.rerun()

# 3. TOOLS TAB
with t_tools:
    st.markdown("### 🛠️ Creator Tools")
    with st.expander("🔥 Idee Checker (Gratis)", expanded=True):
        idea = st.text_input("Jouw ruwe idee:", placeholder="bv. Ik strik mijn veter...")
        if st.button("Check"): 
            st.session_state.idea_score = ai_coach.check_viral_potential(idea, st.session_state.user_niche)
        if "idea_score" in st.session_state:
            d = st.session_state.idea_score
            st.info(f"Score: {d.get('score')} - {d.get('label')}\nTip: {d.get('tip')}")

    with st.expander("📦 Passief Inkomen Bedenker (PRO)"):
        if not is_pro: ui.render_locked_section("Business Plan", "Laat AI je product bedenken.")
        else:
            target = st.text_input("Doelgroep:")
            if st.button("Bedenk"): st.markdown(ai_coach.generate_digital_product(st.session_state.user_niche, target))

    with st.expander("🎬 Serie Generator (PRO)"):
        if not is_pro: ui.render_locked_section("Serie Generator", "Maak 5 video's in 1 klik.")
        else:
            topic = st.text_input("Serie onderwerp:")
            if st.button("Bouw Serie"): st.markdown(ai_coach.generate_series_ideas(topic, st.session_state.user_niche))

    with st.expander("🕵️ Format Dief (PRO)"):
        if not is_pro: ui.render_locked_section("Format Dief", "Kopieer succesformules.")
        else:
            other = st.text_area("Script concurrent:")
            mine = st.text_area("Mijn onderwerp:")
            if st.button("Herschrijf"): st.markdown(ai_coach.steal_format_and_rewrite(other, mine, st.session_state.user_niche))

    with st.expander("📅 Weekplanner (PRO)"):
        if not is_pro: ui.render_locked_section("Weekplanner", "7 dagen content.")
        else:
            if st.button("Maak Planning"): st.markdown(ai_coach.generate_weekly_plan(st.session_state.user_niche))

# 4. DATA TAB (MET AI DETECTIVE)
with t_data:
    st.info("📊 Upload TikTok Data (CSV) voor inzicht.")
    up = st.file_uploader("Upload", type=['csv', 'xlsx'])
    if up: st.session_state.df = data_loader.load_file(up)
    
    if not st.session_state.df.empty:
        df = analytics.clean_data(st.session_state.df)
        kpis = analytics.calculate_kpis(df)
        
        # DE AI DATA DETECTIVE
        st.markdown("### 🕵️ AI Data Detective (PRO)")
        if not is_pro:
            ui.render_locked_section("Data Analyse", "Laat AI patronen vinden in je data. Waarom ga je viraal? Wat is je beste tijd?")
        else:
            if st.button("🔍 Analyseer mijn Data"):
                with st.spinner("De AI zoekt patronen in je cijfers..."):
                    # Maak een tekstuele samenvatting voor de AI
                    best_video = kpis.iloc[0]
                    summary = f"""
                    Totaal views: {kpis['Views'].sum()}. Gem. Engagement: {kpis['Engagement'].mean():.2f}%.
                    Beste video: '{best_video['Caption']}' met {best_video['Views']} views.
                    Slechtste video had {kpis['Views'].min()} views.
                    Gemiddelde lengte caption: {kpis['Caption'].str.len().mean():.0f} tekens.
                    """
                    insights = ai_coach.analyze_data_patterns(summary, st.session_state.user_niche)
                    
                    st.success("Analyse Voltooid!")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**💡 {insights.get('insight_1', 'Inzicht 1')}**")
                        st.markdown(f"**💡 {insights.get('insight_2', 'Inzicht 2')}**")
                    with c2:
                        st.markdown(f"**💡 {insights.get('insight_3', 'Inzicht 3')}**")
                        st.info(f"🚀 **Actie:** {insights.get('strategy_tip')}")
        
        st.markdown("---")
        st.metric("Totaal Views", f"{kpis['Views'].sum()/1000:.1f}k")
        st.bar_chart(analytics.get_best_posting_time(df), x="Uur", y="Views", color="#10b981")

    else:
        if st.button("Laad Demo Data"): st.session_state.df = data_loader.load_demo_data(); st.rerun()

# 5. SETTINGS
with t_set:
    if not is_pro:
        st.markdown("### 🔓 Word een Pro Creator")
        with st.container(border=True):
            st.markdown("#### Upgrade naar PostAi PRO 🚀")
            st.markdown("De tool voor serieuze creators.")
            st.markdown("""
            *   🗂️ **Workflow Systeem** (Beheer je scripts)
            *   🕵️ **AI Data Detective** (Vind de goudmijnen in je data)
            *   💸 **Cashflow Modus** (Sales Scripts)
            *   📦 **Product Bedenker**
            """)
            st.link_button("👉 Start 14 Dagen Gratis", "https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2", type="primary", use_container_width=True)
        
        with st.expander("Heb je al een code?"):
            c = st.text_input("Code")
            if st.button("Activeer"): auth.activate_pro(c)
    else:
        st.success("Je bent PRO lid! 🚀")
        with st.expander("🧬 Train je AI Tweeling"):
            curr = user_data.get("my_style", "")
            s = st.text_area("Jouw stijl:", value=curr)
            if st.button("Sla op"): 
                auth.save_progress(my_style=s); st.success("Opgeslagen!")
        if st.button("Uitloggen"): st.session_state.clear(); st.rerun()

ui.inject_chat_widget(auth.get_secret("CHAT_SERVER_URL", "https://chatbot.com"))