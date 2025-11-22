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
        # STAP 1
        col_in, col_dice = st.columns([0.85, 0.15], vertical_alignment="bottom")
        with col_in:
            default_val = st.session_state.get("idea_input", "")
            topic = st.text_input(
                "1. Waar gaat de video over?", 
                value=default_val, 
                placeholder="Bv. 3 fouten die starters maken...", 
                help="Typ hier kort het onderwerp. De AI bedenkt de rest."
            )
        with col_dice:
            if st.button("🎲", help="Geef mij een willekeurig idee"):
                ideas = [f"De grootste fout in {st.session_state.user_niche}", "Handige tool die ik gebruik", "Snelle tip voor beginners", "Mijn eerlijke mening"]
                st.session_state.idea_input = random.choice(ideas); st.rerun()

        # STAP 2 & 3
        c_fmt, c_tone = st.columns(2)
        with c_fmt: 
            vid_format = st.selectbox(
                "2. Format (Hoe film je?)", 
                ["🗣️ Ik vertel iets", "🟩 Green Screen", "📸 Vlog / Sfeer", "📝 Lijstje (Tekst)"], 
                help="Kies hoe de video eruit ziet. 'Ik vertel iets' is jij pratend in de camera."
            )
        with c_tone: 
            tone = st.selectbox(
                "3. Toon (Sfeer)", 
                ["⚡ Energiek & Snel", "😌 Rustig & Uitleggend", "😂 Grappig", "🎓 Serieus"],
                help="Hoe wil je overkomen op de kijker?"
            )

        # STAP 4 & 5
        hooks = ai_coach.get_viral_hooks_library()
        selected_hook = st.selectbox(
            "4. Kies de Opening (Hook)", 
            hooks,
            help="De eerste 3 seconden zijn cruciaal. Kies een zin die nieuwsgierig maakt."
        )
        cta_type = st.selectbox(
            "5. Doel van de video", 
            ["➕ Volgers erbij", "💬 Reacties krijgen", "💰 Klikken op link", "↗️ Viraal gaan (Delen)"],
            help="Wat moet de kijker doen na het kijken?"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("✨ Schrijf Script", type="primary", use_container_width=True):
            if not is_pro and st.session_state.get("daily_gen_count", 0) >= 1:
                # GRATIS GEBRUIKERS KRIJGEN HIER EEN LIMIET MELDING
                st.error("⚠️ Je hebt je gratis script voor vandaag gehad. Upgrade naar PRO voor onbeperkt.")
            else:
                with st.spinner("De regisseur schrijft je script..."):
                    final_hook = selected_hook.replace("{onderwerp}", topic if topic else "dit")
                    script = ai_coach.generate_script(topic, vid_format, tone, final_hook, cta_type, st.session_state.user_niche)
                    st.session_state.last_script = script
                    if "script_score" in st.session_state: del st.session_state.script_score
                    st.session_state.daily_gen_count = st.session_state.get("daily_gen_count", 0) + 1
                    st.session_state.xp += 10
                    auth.save_progress(xp=st.session_state.xp); st.rerun()

    # RESULTAAT
    if "last_script" in st.session_state:
        st.success("💡 Script is klaar!")
        
        # --- HIER IS DE AANPASSING: VIRAL AUDIT NU ACHTER SLOT ---
        if "script_score" not in st.session_state:
            st.markdown("---")
            if not is_pro:
                # Voor GRATIS gebruikers: Toon de lock
                st.info("🚀 **Wil je weten of dit script viraal gaat?**")
                ui.render_locked_section(
                    feature_name="Viral Audit", 
                    tease_text="Laat het AI-algoritme je script vooraf beoordelen met een score van 0-100. Voorkom dat je slechte video's filmt."
                )
            else:
                # Voor PRO gebruikers: Toon de knop
                st.info("🚀 **Pro Tip:** Laat de AI je script controleren voordat je gaat filmen.")
                if st.button("🔍 Start Viral Audit (Score 0-100)", type="secondary", use_container_width=True):
                    with st.spinner("Het algoritme kijkt mee..."):
                        score_data = ai_coach.audit_script(st.session_state.last_script, st.session_state.user_niche)
                        st.session_state.script_score = score_data
                        st.rerun()
        
        # SCORECARD (Alleen zichtbaar als pro erop geklikt heeft)
        if "script_score" in st.session_state:
            score = st.session_state.script_score
            color = "#ef4444" if score['score'] < 60 else "#f59e0b" if score['score'] < 80 else "#10b981"
            
            st.markdown(f"""
            <div style="background:#f9fafb; border-radius:10px; padding:15px; border:1px solid #e5e7eb; margin-bottom:20px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0; color:#374151;">Viral Score</h3>
                    <span style="font-size:24px; font-weight:800; color:{color};">{score['score']}/100</span>
                </div>
                <p style="font-weight:bold; margin-top:5px;">{score['verdict']}</p>
                <div style="font-size:0.9rem; color:#4b5563;">
                    <p>✅ <b>Goed:</b> {score['pros']}</p>
                    <p>⚠️ <b>Pas op:</b> {score['cons']}</p>
                    <p>💡 <b>Verbetering:</b> {score['tip']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # TABS
        t1, t2 = st.tabs(["📄 Script Lezen", "🎥 Teleprompter"])
        with t1: 
            st.markdown(st.session_state.last_script)
        with t2:
            st.info("Zet je telefoon neer en lees de tekst van het scherm.")
            clean = st.session_state.last_script.replace("|", "").replace("---", "")
            st.markdown(f"<div style='font-size:22px; line-height:1.6; background:#f3f4f6; padding:20px; border-radius:10px; border-left: 5px solid #10b981;'>{clean}</div>", unsafe_allow_html=True)

        st.markdown("---")
        if st.button("✅ Gefilmd & Klaar!", type="secondary"):
            st.session_state.streak += 1; st.session_state.xp += 20; st.balloons()
            del st.session_state.last_script
            if "script_score" in st.session_state: del st.session_state.script_score
            st.rerun()

# 2. TOOLS TAB
with t_tools:
    st.markdown("### 🛠️ Creator Tools")
    
    # --- GRATIS TOOL ---
    with st.expander("🔥 Idee Checker (Gratis)", expanded=True):
        st.info("🤷‍♂️ **Wat doet dit?** Twijfel je over een onderwerp? De AI voorspelt of het viral gaat.")
        c_in, c_btn = st.columns([0.75, 0.25], vertical_alignment="bottom")
        with c_in:
            idea = st.text_input("Jouw ruwe idee:", placeholder="bv. Ik strik mijn veter...", label_visibility="collapsed")
        with c_btn:
            check_btn = st.button("Check", type="primary", use_container_width=True)

        if check_btn and idea:
            with st.spinner("Analyseren..."):
                st.session_state.idea_score = ai_coach.check_viral_potential(idea, st.session_state.user_niche)

        if "idea_score" in st.session_state:
            data = st.session_state.idea_score
            score = data.get('score', 0)
            color = "green" if score >= 80 else "orange" if score >= 60 else "red"
            icon = "🚀" if score >= 80 else "👌" if score >= 60 else "💤"

            st.markdown("---")
            c_s, c_t = st.columns([0.3, 0.7])
            with c_s:
                st.markdown(f"""
                <div style="text-align:center; border: 2px solid {color}; border-radius: 15px; padding: 10px; background: #f9fafb;">
                    <div style="font-size: 2.5rem; font-weight: 800; color: {color}; line-height: 1;">{score}</div>
                    <div style="font-size: 0.7rem; font-weight: bold; color: #6b7280; text-transform: uppercase;">SCORE</div>
                </div>
                """, unsafe_allow_html=True)
            with c_t:
                st.progress(score)
                st.markdown(f"**{icon} {data.get('label', 'Analyse')}**")
                st.caption(data.get('explanation'))
                st.info(f"💡 **Tip:** {data.get('tip')}")
        else:
             st.markdown("<div style='opacity:0.5; margin-top:10px; font-size:0.8rem;'>Typ iets om de meter te starten...</div>", unsafe_allow_html=True)

    # --- PRO TOOL 1: SERIE MAKEN ---
    with st.expander("🎬 5 Video's in 1 klik (PRO)", expanded=False):
        if not is_pro:
            ui.render_locked_section(
                feature_name="Serie Generator", 
                tease_text="Maak in 1 klik een verslavende 5-delige serie. Groei 5x sneller door kijkers te binden."
            )
        else:
            st.info("💎 **Waarde:** De snelste manier om te groeien is een serie. Maak hier 5 video-ideeën in 1 klik.")
            serie_topic = st.text_input("Waar moet de serie over gaan?", placeholder="bv. Budget koken, Fit worden...")
            if st.button("Bouw mijn 5-delige Serie"):
                if serie_topic:
                    with st.spinner("De AI bedenkt 5 virale delen..."):
                        st.markdown(ai_coach.generate_series_ideas(serie_topic, st.session_state.user_niche))

    # --- PRO TOOL 2: FORMAT NADOEN ---
    with st.expander("🕵️ Viral Video Nadoen (PRO)"):
        if not is_pro:
            ui.render_locked_section(
                feature_name="Viral Kopiëren", 
                tease_text="Steel de geheime succes-formule van je concurrenten zonder te plagieëren."
            )
        else:
            st.info("🧠 **Wat doet dit?** Plak tekst van een concurrent. De AI steelt de *formule* (niet de tekst) en past die toe op jouw onderwerp.")
            other = st.text_area("Plak script van concurrent:", height=100)
            mine = st.text_area("Waar wil jij het over hebben?", height=100)
            if st.button("Herschrijf met Formule"): 
                with st.spinner("Kraken..."):
                    st.markdown(ai_coach.steal_format_and_rewrite(other, mine, st.session_state.user_niche))

    # --- PRO TOOL 3: WEEKPLANNER ---
    with st.expander("📅 Content voor de hele Week (PRO)"):
        if not is_pro:
             ui.render_locked_section(
                 feature_name="Weekplanner", 
                 tease_text="Nooit meer stress. Je complete content strategie voor 7 dagen in 10 seconden geregeld."
             )
        else:
            st.info("📅 **Wat doet dit?** Een schema voor 7 dagen, zodat je precies weet wat je moet maken.")
            if st.button("Maak Planning"): 
                with st.spinner("Plannen..."):
                    st.markdown(ai_coach.generate_weekly_plan(st.session_state.user_niche))

# 3. DATA TAB
with t_data:
    st.info("📊 **Waarom dit gebruiken?** Upload je TikTok data (CSV) om te zien wat werkt.")
    uploaded_file = st.file_uploader("Upload TikTok Data", type=['csv', 'xlsx'])
    
    if uploaded_file: st.session_state.df = data_loader.load_file(uploaded_file)
    
    if not st.session_state.df.empty:
        df = analytics.clean_data(st.session_state.df)
        kpis = analytics.calculate_kpis(df)
        c1,c2,c3 = st.columns(3)
        c1.metric("Views", f"{kpis['Views'].sum()/1000:.1f}k")
        c2.metric("Engagement", f"{kpis['Engagement'].mean():.1f}%", help="Hoger dan 5% is super!")
        st.bar_chart(analytics.get_best_posting_time(df), x="Uur", y="Views", color="#10b981")
    else:
        if st.button("Laad Demo Data (Voorbeeld)"): st.session_state.df = data_loader.load_demo_data(); st.rerun()

# 4. SETTINGS (DEZE IS GE-UPDATE MET FOMO)
with t_set:
    if not is_pro:
        # HIER BEGINT DE NIEUWE FOMO KAART
        st.markdown("### 🔓 Word een Pro Creator")
        
        with st.container(border=True):
            st.markdown("<h4 style='margin-top:0'>Upgrade naar PostAi PRO 🚀</h4>", unsafe_allow_html=True)
            st.markdown("Stop met gokken. Start met groeien met de tools die pro's gebruiken.")
            
            st.markdown("""
            **Wat je direct krijgt:**
            *   ✅ **Onbeperkt Scripts** (Geen dagelijkse limiet meer)
            *   🎬 **Serie Generator** (5 video's in 1 klik)
            *   🕵️ **Concurrentie Spy** (Steel succesformules)
            *   📅 **Weekplanner** (Je week gevuld in 10 seconden)
            *   🔍 **Viral Audit** (Laat AI je video keuren)
            """)
            
            st.markdown("---")
            st.caption("🎁 **Eerste 14 dagen gratis** • 💎 20% korting bij jaar • 🔓 Altijd opzegbaar")
            
            st.link_button(
                "👉 Start 14 Dagen Gratis", 
                "https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2", 
                type="primary", 
                use_container_width=True
            )

        # Licentie invoer verborgen in een expander
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("Heb je al een licentie code?"):
            code = st.text_input("Vul je code in", label_visibility="collapsed", placeholder="Plak je code hier...")
            if st.button("Activeer Licentie"): auth.activate_pro(code)
            
    else:
        st.success("Je bent PRO lid! 🚀")
        st.caption("Bedankt voor je support.")
        if st.button("Uitloggen"): st.session_state.clear(); st.rerun()

ui.inject_chat_widget(auth.get_secret("CHAT_SERVER_URL", "https://chatbot.com"))