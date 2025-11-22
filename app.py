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

t_studio, t_tools, t_data, t_set = st.tabs(["🎬 Studio", "✨ Tools", "📊 Cijfers", "⚙️"])

# 1. STUDIO TAB
with t_studio:
    st.markdown(f"<h3 style='margin-bottom:10px;'>Nieuwe Video Maken</h3>", unsafe_allow_html=True)
    
    with st.container(border=True):
        # KEUZE: NORMAAL OF GELD VERDIENEN (DE GROTE SPLITSING)
        mode = st.radio(
            "Kies je doel:", 
            ["👀 Viral gaan (Views & Groei)", "💸 Geld Verdienen (Sales & UGC)"], 
            horizontal=True,
            label_visibility="collapsed"
        )

        # --- MODUS A: VIRAL GAAN (GRATIS/STANDAARD) ---
        if mode == "👀 Viral gaan (Views & Groei)":
            st.caption("Focus: Veel views, nieuwe volgers en bereik.")
            
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
                        final_hook = selected_hook.replace("{onderwerp}", topic if topic else "dit")
                        script = ai_coach.generate_script(topic, vid_format, tone, final_hook, cta_type, st.session_state.user_niche)
                        st.session_state.last_script = script
                        if "script_score" in st.session_state: del st.session_state.script_score
                        st.session_state.daily_gen_count = st.session_state.get("daily_gen_count", 0) + 1
                        st.session_state.xp += 10
                        auth.save_progress(xp=st.session_state.xp); st.rerun()

        # --- MODUS B: GELD VERDIENEN (PRO LOCK) ---
        else:
            st.markdown("""
            <div style="background:#ecfdf5; border-left:4px solid #10b981; padding:10px; border-radius:4px; font-size:0.9rem;">
            💰 <b>Cashflow Modus:</b> De AI gebruikt geavanceerde sales-psychologie (PAS/AIDA) om kijkers om te zetten in kopers.
            </div>
            """, unsafe_allow_html=True)
            
            # We tonen de velden WEL (Tease), maar de knop is gelocked
            col_p, col_pain = st.columns(2)
            with col_p: product_name = st.text_input("Wat verkoop je?", placeholder="Mijn E-book / Huidcreme...")
            with col_pain: pain_point = st.text_input("Welk probleem los je op?", placeholder="Puistjes / Geldzorgen...")
            
            sales_angle = st.selectbox("Verkoop Strategie", [
                "😱 Problem-Agitate-Solution (Klassieker)", 
                "📦 Unboxing / Demo (Visueel)", 
                "⭐ Testimonial / Resultaat (Social Proof)", 
                "🛑 Stop met X, Doe Y (Controversieel)"
            ])
            
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("💸 Schrijf Sales Script", type="primary", use_container_width=True):
                if not is_pro:
                    ui.render_locked_section(
                        feature_name="Cashflow Script", 
                        tease_text="Zet views om in Euro's. Krijg toegang tot scripts die bewezen verkopen (UGC & Sales)."
                    )
                else:
                    if not product_name or not pain_point:
                        st.error("Vul in wat je verkoopt en welk probleem het oplost.")
                    else:
                        with st.spinner("De copywriter schrijft een gelkmachine..."):
                            script = ai_coach.generate_sales_script(product_name, pain_point, sales_angle, st.session_state.user_niche)
                            st.session_state.last_script = script
                            if "script_score" in st.session_state: del st.session_state.script_score
                            st.session_state.xp += 20
                            auth.save_progress(xp=st.session_state.xp); st.rerun()

    # RESULTAAT SECTIE
    if "last_script" in st.session_state:
        st.success("💡 Script is klaar!")
        
        # Viral Audit (Alleen PRO)
        if "script_score" not in st.session_state:
            st.markdown("---")
            if not is_pro:
                st.info("🚀 **Gaat dit viraal?**")
                ui.render_locked_section("Viral Audit", "Laat het AI-algoritme je script beoordelen voordat je filmt.")
            else:
                st.info("🚀 **Pro Tip:** Check de kwaliteit.")
                if st.button("🔍 Start Audit", type="secondary", use_container_width=True):
                    with st.spinner("Analyseren..."):
                        score_data = ai_coach.audit_script(st.session_state.last_script, st.session_state.user_niche)
                        st.session_state.script_score = score_data
                        st.rerun()
        
        if "script_score" in st.session_state:
            score = st.session_state.script_score
            color = "#ef4444" if score['score'] < 60 else "#f59e0b" if score['score'] < 80 else "#10b981"
            st.markdown(f"""
            <div style="background:#f9fafb; border-radius:10px; padding:15px; border:1px solid #e5e7eb; margin-bottom:20px;">
                <div style="display:flex; justify-content:space-between;">
                    <h3 style="margin:0;">Score</h3>
                    <span style="font-size:24px; font-weight:800; color:{color};">{score['score']}/100</span>
                </div>
                <p>{score['verdict']}</p>
            </div>""", unsafe_allow_html=True)

        t1, t2 = st.tabs(["📄 Script", "🎥 Teleprompter"])
        with t1: st.markdown(st.session_state.last_script)
        with t2:
            clean = st.session_state.last_script.replace("|", "").replace("---", "")
            st.markdown(f"<div style='font-size:22px; line-height:1.6; background:#f3f4f6; padding:20px; border-radius:10px;'>{clean}</div>", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("✅ Gefilmd & Klaar!", type="secondary"):
            st.session_state.streak += 1; st.session_state.xp += 20; st.balloons()
            del st.session_state.last_script
            if "script_score" in st.session_state: del st.session_state.script_score
            st.rerun()

# 2. TOOLS TAB
with t_tools:
    st.markdown("### 🛠️ Creator Tools")
    
    # GRATIS TOOL
    with st.expander("🔥 Idee Checker (Gratis)", expanded=True):
        idea = st.text_input("Jouw ruwe idee:", placeholder="bv. Ik strik mijn veter...")
        if st.button("Check"): 
            st.session_state.idea_score = ai_coach.check_viral_potential(idea, st.session_state.user_niche)
        if "idea_score" in st.session_state:
            d = st.session_state.idea_score
            st.markdown(f"**Score: {d.get('score')}** - {d.get('label')}")
            st.info(d.get('tip'))

    # PRO TOOL: PASSIVE INCOME GENERATOR
    with st.expander("📦 Passief Inkomen Bedenker (PRO)", expanded=False):
        if not is_pro:
            ui.render_locked_section("Business Plan Generator", "Laat AI je complete digitale product bedenken (E-book, Cursus) inclusief hoofdstukken en prijs.")
        else:
            st.info("De AI analyseert je niche en bouwt een compleet product-plan.")
            target_audience = st.text_input("Voor wie is het?", placeholder="bv. Drukke moeders, beginnende sporters...")
            if st.button("Bouw mijn Business"):
                if target_audience:
                    with st.spinner("Brainstormen over jouw imperium..."):
                        st.markdown(ai_coach.generate_digital_product(st.session_state.user_niche, target_audience))

    # PRO TOOL: SERIE MAKER
    with st.expander("🎬 5 Video's in 1 klik (PRO)"):
        if not is_pro: ui.render_locked_section("Serie Generator", "Maak in 1 klik een 5-delige serie.")
        else:
            topic = st.text_input("Serie onderwerp:")
            if st.button("Bouw Serie"): st.markdown(ai_coach.generate_series_ideas(topic, st.session_state.user_niche))

    # PRO TOOL: FORMAT DIEF
    with st.expander("🕵️ Viral Video Nadoen (PRO)"):
        if not is_pro: ui.render_locked_section("Viral Kopiëren", "Steel de succes-formule.")
        else:
            other = st.text_area("Concurrent script:")
            mine = st.text_area("Mijn onderwerp:")
            if st.button("Herschrijf"): st.markdown(ai_coach.steal_format_and_rewrite(other, mine, st.session_state.user_niche))

    # PRO TOOL: WEEKPLANNER
    with st.expander("📅 Content voor de hele Week (PRO)"):
        if not is_pro: ui.render_locked_section("Weekplanner", "Content strategie voor 7 dagen.")
        else:
            if st.button("Maak Planning"): st.markdown(ai_coach.generate_weekly_plan(st.session_state.user_niche))

# 3. DATA TAB
with t_data:
    st.info("📊 Upload TikTok Data (CSV) voor inzicht.")
    up = st.file_uploader("Upload", type=['csv', 'xlsx'])
    if up: st.session_state.df = data_loader.load_file(up)
    if not st.session_state.df.empty:
        df = analytics.clean_data(st.session_state.df)
        kpis = analytics.calculate_kpis(df)
        st.metric("Views", f"{kpis['Views'].sum()/1000:.1f}k")
    else:
        if st.button("Demo Data"): st.session_state.df = data_loader.load_demo_data(); st.rerun()

# 4. SETTINGS
with t_set:
    if not is_pro:
        st.markdown("### 🔓 Word een Pro Creator")
        with st.container(border=True):
            st.markdown("#### Upgrade naar PostAi PRO 🚀")
            st.markdown("Stop met hobbyen. Start met verdienen.")
            st.markdown("""
            **Direct toegang tot:**
            *   💸 **Sales Script Modus** (Verkoop je producten)
            *   📦 **Passief Inkomen Bedenker** (Vind je goudmijn)
            *   🎬 **Serie Generator** (5x sneller groeien)
            *   ✅ **Onbeperkt Scripts**
            """)
            st.link_button("👉 Start 14 Dagen Gratis", "https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2", type="primary", use_container_width=True)
        
        with st.expander("Heb je al een code?"):
            c = st.text_input("Code")
            if st.button("Activeer"): auth.activate_pro(c)
    else:
        st.success("Je bent PRO lid! 🚀")
        if st.button("Uitloggen"): st.session_state.clear(); st.rerun()

ui.inject_chat_widget(auth.get_secret("CHAT_SERVER_URL", "https://chatbot.com"))