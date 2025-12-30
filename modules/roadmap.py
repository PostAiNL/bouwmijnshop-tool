import streamlit as st
import time
import pandas as pd
from io import BytesIO
from modules import ai_coach

STRATEGY_CALL_URL = "https://calendly.com/rmecomacademy/30min"
COMMUNITY_URL = "https://discord.com"

def get_roadmap():
    return {
        "fase_1": {
            "title": "Fase 1: De Fundering", 
            "desc": "Zonder fundering stort je huis in. We beginnen met het leuke werk: je idee en je naam.", 
            "steps": [
                {
                    "id": "onboarding_done", # Deze matcht met de wizard in app.py
                    "title": "Startschot & Doel", 
                    "icon": "", "locked": False,
                    "content": "TEXT_ONLY", "xp_reward": 10,
                    "text": "✅ Gefeliciteerd! Je hebt je eerste doel gesteld en de knoop doorgehakt om te starten. Dit is vaak de lastigste stap."
                },
                {
                    "id": "step_niche", "title": "Wat ga je verkopen?", "icon": "", "locked": False,
                    "content": "TOOL_NICHE_FINDER", "xp_reward": 100,
                    "teaser": "Weet je niet wat je moet verkopen? Vraag de AI om hulp."
                },
                {
                    "id": "step_avatar", "title": "Wie is je Droomklant?", "icon": "", "locked": False, 
                    "content": "TEXT_ONLY", "xp_reward": 125,
                    "text": "Stop! Voordat je bouwt: Wie gaat dit kopen? Bedenk een naam (bv. 'Linda'), leeftijd en hobby's. Zonder dit wordt adverteren onmogelijk duur."
                },
                {
                    "id": "step_domain", "title": "Domeinnaam Kiezen", "icon": "", "locked": False,
                    "content": "TOOL_DOMAIN_CHECK", "xp_reward": 50,
                },
                {
                    "id": "step_bank", "title": "Zakelijke Rekening", "icon": "", "locked": False,
                    "content": "TOOL_BANK_WIZARD", "xp_reward": 75,
                },
                {
                    "id": "step_kvk", "title": "KVK Nummer Regelen", "icon": "", "locked": False,
                    "content": "TOOL_KVK_GUIDE", "xp_reward": 100, 
                    "video_url": "https://rmacademy.huddlecommunity.com/module/kvk-inschrijven",
                    "teaser": "Klaar voor het echie? Tijd om het officieel te maken."
                }
            ]
        },
        "fase_2": {
            "title": "Fase 2: Winkel Bouwen", 
            "desc": "Zet de techniek en het design klaar voor je eerste bezoekers.",
            "steps": [
                {
                    "id": "step_shopify_setup", "title": "Shopify Account Maken", "icon": "", "locked": False,
                    "content": "TOOL_SHOPIFY_GUIDE", "xp_reward": 150,
                },
                {
                    "id": "step_theme", "title": "Logo & Huisstijl", "icon": "", "locked": False,
                    "content": "TOOL_THEME_GUIDE", "xp_reward": 100,
                },
                {
                    "id": "step_payments", "title": "Betalingen Instellen", "icon": "", "locked": False,
                    "content": "TOOL_PAYMENTS", "xp_reward": 125,
                },
                {
                    "id": "step_legal_safe", "title": "Juridisch & Regels", "icon": "", "locked": False,
                    "content": "TOOL_LEGAL_SAFE_NEW", "xp_reward": 150,
                }
            ]
        },
        "fase_3": {
            "title": "Fase 3: Het Aanbod",
            "desc": "Een product is nog geen business. Hier maak je er een onweerstaanbare deal van.",
            "steps": [
                {
                    "id": "step_supplier", "title": "Leverancier Koppelen", "icon": "", "locked": False,
                    "content": "TOOL_SUPPLIER_HUB", "xp_reward": 100,
                },
                {
                    "id": "step_sample", "title": "Sample Bestellen (Verplicht)", "icon": "", "locked": False, 
                    "content": "TEXT_ONLY", "xp_reward": 150,
                    "text": "Bestel het product ZELF naar je eigen huis. Waarom? 1. Kwaliteitscheck (voorkom refunds). 2. Zelf video's maken met je telefoon. Zonder eigen content ben je kansloos op TikTok."
                },
                {
                    "id": "step_offer", "title": "Onweerstaanbaar Aanbod", "icon": "", "locked": False, 
                    "content": "TOOL_PROFIT_CALC", "xp_reward": 100,
                    "text": "Verkoop je alleen een lamp? Saai. Maak een bundel: 'Lamp + Batterijen + E-book'. Bereken hier je marge."
                }
            ]
        },
        "fase_4": {
            "title": "Fase 4: Vertrouwen & Content",
            "desc": "Zorg dat je shop er betrouwbaar uitziet en dat alles werkt.",
            "steps": [
                {
                    "id": "step_about_us", "title": "'Over ons' Pagina", "icon": "", "locked": False, 
                    "content": "TOOL_ABOUT_US", "xp_reward": 100,
                },
                {
                    "id": "step_reviews", "title": "Reviews Instellen", "icon": "", "locked": False,
                    "content": "TOOL_REVIEWS", "xp_reward": 100,
                },
                {
                    "id": "step_support", "title": "Klantenservice Setup", "icon": "", "locked": False,
                    "content": "TEXT_ONLY", "xp_reward": 100,
                    "text": "Zorg voor een professioneel e-mailadres (support@jouwdomein.nl) en stel een automatische bevestiging in. Dit voorkomt bans bij PayPal en advertentieplatforms."
                },
                {
                    "id": "step_pixels", "title": "Bezoekers Meten (Pixels)", "icon": "", "locked": False,
                    "content": "TOOL_PIXELS", "xp_reward": 125,
                },
                {
                    "id": "step_email", "title": "Automatische E-mails", "icon": "", "locked": False,
                    "content": "TOOL_EMAIL_GEN", "xp_reward": 150,
                }
            ]
        },
        "fase_5": {
            "title": "Fase 5: Go Live & Traffic",
            "desc": "De sluizen gaan open. We gaan bezoekers naar je winkel sturen.",
            "steps": [
                {
                    "id": "step_24h_live", "title": "Launch Checklist", "icon": "", "locked": False,
                    "content": "TOOL_24H_CHECK", "xp_reward": 150,
                },
                {
                    "id": "step_content_creation", "title": "Je Eerste Video Maken", "icon": "", "locked": False, 
                    "content": "TEXT_ONLY", "xp_reward": 150,
                    "text": "Pak je sample. Film 3 hoeken: 1. Het probleem (donkere kamer). 2. De oplossing (jouw lamp). 3. Het resultaat (sfeer). Dit is je advertentie."
                },
                {
                    "id": "step_winning_prod", "title": "Spy: Wat werkt er nu?", "icon": "", "locked": True,
                    "content": "TOOL_PRODUCT_SPY", "xp_reward": 200,
                },
                {
                    "id": "step_fulfillment", "title": "Je Eerste Order Verwerken", "icon": "", "locked": False,
                    "content": "TEXT_ONLY", "xp_reward": 100,
                    "text": "PANIEK? Neehoor! 🎉 Je hebt een sale. Wat nu?\n1. Ga naar je leverancier (AliExpress/Agent).\n2. Bestel het product en vul het adres van JOUW KLANT in.\n3. De leverancier stuurt het direct naar de klant.\n4. Jij houdt het verschil (winst)!"
                },
                {
                    "id": "step_influencer", "title": "Influencers (Gratis bereik)", "icon": "", "locked": False,
                    "content": "TOOL_INFLUENCER_OUTREACH", "xp_reward": 100,
                }
            ]
        },
        "fase_6": {
            "title": "Fase 6: Opschalen & Ads",
            "desc": "De shop staat. Nu begint het echte werk: Data lezen, testen en winst pakken.",
            "steps": [
                {
                    "id": "step_testing_ads", "title": "Dag 1: Advertenties Starten", "icon": "", "locked": False,
                    "content": "TEXT_ONLY", "text": "Start met €20-€50 per dag. Gebruik de video die je in Fase 5 hebt gemaakt.",
                    "xp_reward": 150
                },
                {
                    "id": "step_analysis", "title": "Dag 3: Winst of Verlies?", "icon": "", "locked": False,
                    "content": "TEXT_ONLY", "text": "Kijk naar je CPC (onder €0.50?) en ROAS. Geen sales? 90% kans dat je video (Fase 5) niet boeiend genoeg is. Maak een nieuwe.",
                    "xp_reward": 150
                },
                {
                    "id": "step_kill_scale", "title": "Dag 7: Doorgaan of Stoppen?", "icon": "", "locked": False,
                    "content": "TEXT_ONLY", "text": "Heb je winst? Schaal op (20% budget erbij per dag). Geen winst? Stop met dit product. Ga terug naar Fase 3 (Sample bestellen van nieuw product).",
                    "xp_reward": 200
                }
            ]
        }
    }

def render_step_card(step, is_completed, is_pro, expanded=False):
    # --- 1. STATUS & KLEUREN BEPALEN ---
    
    # Standaard waardes (voor toekomstige stappen - Rustig grijs)
    bg_color = "#F8FAFC"      # Off-white / Lichtgrijs
    border_color = "#E2E8F0"  # Standaard rand
    title_color = "#0F172A"   # Donkerblauw/zwart
    badge = ""
    shadow = "none"
    opacity = "0.9"

    # SITUATIE A: STAP IS AFGEROND ✅ (Groen)
    if is_completed:
        bg_color = "#F0FDF4"      # Zachtgroen
        border_color = "#BBF7D0"  # Groen randje
        title_color = "#166534"   # Donkergroene tekst
        badge = "<span style='color:#16A34A; font-weight:bold; font-size:1.1rem;'><i class='bi bi-check-circle-fill'></i></span>"
        opacity = "1"

    # SITUATIE B: DIT IS DE VOLGENDE STAP 🚀 (Wit + Blauw + Schaduw)
    elif expanded: 
        bg_color = "#FFFFFF"      # Helder wit
        border_color = "#2563EB"  # Fel blauwe rand
        title_color = "#1E293B"   # Zwart/Donkerblauw
        badge = "<span style='background:#EFF6FF; color:#2563EB; padding:2px 8px; border-radius:10px; font-size:0.7rem; font-weight:700; border:1px solid #BFDBFE;'>NU DOEN</span>"
        shadow = "0 4px 6px -1px rgba(37, 99, 235, 0.1), 0 2px 4px -1px rgba(37, 99, 235, 0.06)"
        opacity = "1"

    # SITUATIE C: OP SLOT (NIET PRO) 🔒
    elif step.get('locked', False) and not is_pro:
        bg_color = "#F1F5F9"      # Iets donkerder grijs
        border_color = "#E2E8F0"
        title_color = "#94A3B8"   # Lichtgrijs
        badge = "<i class='bi bi-lock-fill'></i>"
        opacity = "0.6"

    usage_key = f"tool_used_{step['id']}"
    is_locked = step.get('locked', False) and not is_pro

    # --- 2. RENDER DE KAART (HEADER) ---
    # CSS variabele voor styling om HTML bugs te voorkomen
    card_style = f"border: 1px solid {border_color}; background-color: {bg_color}; border-radius: 12px; padding: 16px; margin-bottom: 0px; box-shadow: {shadow}; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s; opacity: {opacity};"
    
    st.markdown(f"""
    <div style="{card_style}">
        <div style="font-weight:600; font-size:1rem; display:flex; align-items:center; gap:12px; color:{title_color};">
            <span>{step['title']}</span>
        </div>
        <div>{badge}</div>
    </div>
    """, unsafe_allow_html=True)

    # --- 3. INHOUD (ALTIJD BESCHIKBAAR VIA EXPANDER) ---
    if is_locked:
        teaser_text = step.get('teaser', 'Upgrade voor toegang.')
        lock_html = f"""<div style="background:#F8FAFC; padding:15px; border:1px solid #E2E8F0; border-top:none; border-radius: 0 0 12px 12px; text-align:center; color:#64748B; margin-bottom:12px; font-size:0.9rem;"><i class="bi bi-lock"></i> {teaser_text} <a href="{STRATEGY_CALL_URL}" target="_blank" style="font-weight:bold; color:#2563EB; text-decoration:none; margin-left:5px;">Unlock 🔓</a></div>"""
        st.markdown(lock_html, unsafe_allow_html=True)
        return None, 0
    else:
        expander_label = "🔽 Opdracht & Tools bekijken"
        
        with st.expander(expander_label, expanded=expanded):
            with st.container():
                st.markdown(f"<div style='border-left: 2px solid {border_color}; padding-left: 15px; margin-left: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)
                
                # --- TOOLS & CONTENT ---
                if step.get('video_url'):
                    if is_pro:
                        st.markdown(f"""<a href="{step['video_url']}" target="_blank" style="text-decoration:none;"><div style="margin-bottom: 20px; padding: 12px; background: #EFF6FF; border-radius: 10px; border: 1px solid #DBEAFE; display: flex; align-items: center; gap: 10px;"><span style="color: #1E40AF; font-weight: 600;">🎥 Bekijk de video instructie</span><span style="margin-left:auto; color:#2563EB;">&rarr;</span></div></a>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""<div style="margin-bottom: 20px; padding: 12px; background: #F8FAFC; border-radius: 10px; border: 1px dashed #CBD5E1; display: flex; align-items: center; gap: 10px; opacity: 0.7;"><span style="color: #64748B; font-weight: 600;">🎥 Video instructie (Student only)</span><span style="margin-left:auto;">🔒</span></div>""", unsafe_allow_html=True)

                if step.get('content') == "TEXT_ONLY":
                    st.info(step['text'])
                    st.session_state[usage_key] = True

                elif step['content'] == "TOOL_KVK_GUIDE":
                    st.info("💡 Tip: Maak eerst een afspraak, het is vaak druk bij de KVK!")
                    st.link_button("📅 Ga naar KVK.nl", "https://www.kvk.nl/inschrijven", use_container_width=True)
                    # FIX: Unieke key
                    if st.checkbox("✅ Ik heb mijn afspraak/inschrijving geregeld", key=f"kvk_check_{step['id']}"): 
                        st.session_state[usage_key] = True

                elif step['content'] == "TOOL_NICHE_FINDER":
                    st.write("Weet je niet wat je moet verkopen?")
                    # FIX: Unieke keys
                    interest = st.text_input("Jouw interesses (bv. fitness, honden, gadgets)", key=f"niche_in_{step['id']}")
                    if st.button("🔍 Vraag AI om suggesties", key=f"niche_btn_{step['id']}"):
                        st.session_state[usage_key] = True
                        if not interest: st.warning("Vul iets in!")
                        else:
                            st.info(f"💡 Suggesties voor '{interest}':")
                            st.markdown("1. **Probleem-oplosser:** Iets dat irritatie wegneemt.\n2. **Passie:** Iets waar mensen trots op zijn.\n3. **Viral:** Iets dat er cool uitziet.")
                            st.success("Kies één richting en ga door!")

                elif step['content'] == "TOOL_BANK_WIZARD":
                    c1, c2 = st.columns(2)
                    c1.link_button("Knab (Bank)", "https://knab.nl", use_container_width=True)
                    c2.link_button("N26 (Creditcard)", "https://n26.com", use_container_width=True)
                    # FIX: Unieke key
                    if st.checkbox("✅ Ik heb dit geregeld", key=f"bank_check_{step['id']}"): 
                        st.session_state[usage_key] = True

                elif step['content'] == "TOOL_DOMAIN_CHECK":
                    st.link_button("🔎 Check TransIP", "https://www.transip.nl", use_container_width=True)
                    # FIX: Unieke key
                    if st.checkbox("✅ Domeinnaam vastgelegd", key=f"domain_check_{step['id']}"): 
                        st.session_state[usage_key] = True

                elif step['content'] == "TOOL_SHOPIFY_GUIDE":
                    st.info("💰 **Actie:** Eerste 3 maanden voor €1/maand.")
                    st.link_button("🚀 Claim €1 Shopify deal", "https://shopify.com", type="primary", use_container_width=True)
                    # FIX: Unieke key
                    if st.checkbox("✅ Account aangemaakt", key=f"shopify_check_{step['id']}"): 
                        st.session_state[usage_key] = True

                elif step['content'] == "TOOL_THEME_GUIDE":
                    st.info("💡 Advies: Gebruik 'Dawn' of 'Sense' (Gratis).")
                    st.link_button("Shopify Themes", "https://themes.shopify.com", use_container_width=True)
                    # FIX: Unieke key
                    if st.checkbox("✅ Thema ingesteld", key=f"theme_check_{step['id']}"): 
                        st.session_state[usage_key] = True

                elif step['content'] == "TOOL_PAYMENTS":
                    st.link_button("Maak Mollie account", "https://www.mollie.com", use_container_width=True)
                    # FIX: Unieke key
                    if st.checkbox("✅ Betaalmethode actief", key=f"pay_check_{step['id']}"): 
                        st.session_state[usage_key] = True

                elif step['content'] == "TOOL_LEGAL_SAFE_NEW":
                    # FIX: Unieke keys
                    c_name = st.text_input("Bedrijfsnaam", key=f"legal_name_{step['id']}")
                    c_mail = st.text_input("Contact Email", key=f"legal_mail_{step['id']}")
                    if st.button("📝 Genereer Teksten", key=f"legal_btn_{step['id']}"):
                        if c_name and c_mail:
                            res = ai_coach.generate_legal_text(c_name)
                            st.text_area("Privacy Policy", res, height=150, key=f"legal_area_{step['id']}")
                            st.session_state[usage_key] = True
                        else: st.warning("Vul beide velden in.")

                elif step['content'] == "TOOL_SUPPLIER_HUB":
                    st.info("💎 Student Only: Private Agent toegang.")
                    # FIX: Unieke key
                    if st.checkbox("✅ Leverancier geregeld", key=f"supplier_check_{step['id']}"): 
                        st.session_state[usage_key] = True

                elif step['content'] == "TOOL_PROFIT_CALC":
                    # FIX: Unieke keys
                    p = st.number_input("Verkoopprijs", 30.0, key=f"prof_p_{step['id']}")
                    c = st.number_input("Inkoop", 10.0, key=f"prof_c_{step['id']}")
                    if st.button("Bereken Marge", key=f"prof_btn_{step['id']}"):
                        st.session_state[usage_key] = True
                        st.metric("Winst", f"€{p-c}")

                elif step['content'] == "TOOL_ABOUT_US":
                    # FIX: Unieke keys
                    nm = st.text_input("Jouw Naam", key=f"about_name_{step['id']}")
                    if st.button("Schrijf Over Ons", key=f"about_btn_{step['id']}"):
                        st.session_state[usage_key] = True
                        st.text_area("Tekst", ai_coach.generate_about_us(nm, "General"), key=f"about_res_{step['id']}")

                elif step['content'] == "TOOL_REVIEWS":
                    st.link_button("Installeer Judge.me", "https://apps.shopify.com/judgeme", use_container_width=True)
                    # FIX: Unieke key
                    if st.checkbox("✅ Reviews ingesteld", key=f"rev_check_{step['id']}"): 
                        st.session_state[usage_key] = True

                elif step['content'] == "TOOL_PIXELS":
                    st.info("Installeer TikTok & Facebook apps in Shopify.")
                    # FIX: Unieke key
                    if st.checkbox("✅ Pixels gekoppeld", key=f"pixel_check_{step['id']}"): 
                        st.session_state[usage_key] = True

                elif step['content'] == "TOOL_EMAIL_GEN":
                    st.write("Verlaten winkelwagen mail:")
                    st.code("Onderwerp: Je bent iets vergeten!\nHier is 10% korting: WELKOM10", language="text")
                    # FIX: Unieke key
                    if st.button("✅ Gedaan", key=f"email_btn_{step['id']}"): 
                        st.session_state[usage_key] = True

                elif step['content'] == "TOOL_24H_CHECK":
                    # FIX: Unieke keys
                    c1 = st.checkbox("✅ Testbestelling gedaan", key=f"check24_1_{step['id']}")
                    c2 = st.checkbox("✅ Mobiel gecheckt", key=f"check24_2_{step['id']}")
                    if c1 and c2:
                        st.session_state[usage_key] = True

                elif step['content'] == "TOOL_INFLUENCER_OUTREACH":
                    st.write("Ga naar 'Marketing' in het menu.")
                    # FIX: Unieke key
                    if st.checkbox("✅ Gedaan", key=f"inf_check_{step['id']}"): 
                        st.session_state[usage_key] = True

                elif step['content'] == "TOOL_PRODUCT_SPY":
                    st.write("Ga naar 'Producten Zoeken'.")
                    # FIX: Unieke key
                    if st.checkbox("✅ Gedaan", key=f"spy_check_{step['id']}"): 
                        st.session_state[usage_key] = True

                st.markdown("</div>", unsafe_allow_html=True)

                # ACTIE KNOPPEN (Unieke keys ook hier!)
                if not is_completed:
                    if st.session_state.get(usage_key, False):
                        if st.button(f"🎉 Taak Afronden (+{step['xp_reward']} XP)", key=f"btn_finish_{step['id']}", type="primary", use_container_width=True):
                            return step['id'], step['xp_reward']
                    else:
                        st.button("Voltooi eerst de stappen hierboven ☝️", disabled=True, key=f"dis_finish_{step['id']}", use_container_width=True)
        
        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    return None, 0