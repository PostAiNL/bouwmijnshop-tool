import random
import time
import pandas as pd
import datetime
import os
import streamlit as st
import re # Nodig om scores uit tekst te vissen

# Probeer OpenAI te importeren
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

client = None

def init_ai():
    """Initialiseert OpenAI direct vanuit de server secrets."""
    global client
    # Check of de secret bestaat in .streamlit/secrets.toml
    if HAS_OPENAI and "OPENAI_API_KEY" in st.secrets:
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        except Exception as e:
            print(f"AI Connectie Fout: {e}")
            client = None
    else:
        # print("Geen OpenAI Key gevonden in secrets.toml")
        client = None

def call_llm(system_prompt, user_prompt):
    """Centrale functie voor AI calls. Valt terug op None als het mislukt."""
    if not HAS_OPENAI or not client:
        return None
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Snel, slim en goedkoop
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# ==========================================
# 1. CORE SCRIPTS (Studio & Panic)
# ==========================================

def generate_script(topic, format_type, tone, hook, cta, niche, brand_voice="Expert"):
    # 1. AI Modus
    ai_system = f"""
    Je bent een wereldklasse TikTok scriptwriter voor de niche '{niche}'. 
    Jouw tone-of-voice is '{tone}' en je persona is '{brand_voice}'.
    Je schrijft scripts die viraal gaan door hoge retentie.
    """
    ai_user = f"""
    Schrijf een TikTok script over: '{topic}'.
    Format: {format_type}.
    De Hook moet inspelen op: {hook}.
    Eindig met deze CTA: {cta}.
    
    Output formaat:
    - **TITEL**
    - **VISUELE HOOK (0-3s)**: Wat zien we?
    - **AUDIO HOOK**: De eerste zin.
    - **BODY**: De kernboodschap (kort en krachtig).
    - **CTA**: De afsluiter.
    """
    
    llm_out = call_llm(ai_system, ai_user)
    if llm_out: return llm_out
    
    # 2. Fallback
    time.sleep(1)
    return f"**⚠️ AI Offline:** Kan script over {topic} niet genereren. Check je internet of API key."

def generate_instant_script(niche):
    ai_sys = f"Je bent een 'Panic Button' script generator. De gebruiker heeft NU inspiratie nodig voor niche: {niche}. Geef 1 briljant, makkelijk uit te voeren idee."
    llm_out = call_llm(ai_sys, "Geef me een script. Kort. Krachtig. Nu.")
    if llm_out: return llm_out
    
    return f"**🚨 NOOD SCRIPT**\n\n**HOOK:** 'Ik moet dit kwijt...'\n**KERN:** 'Iedereen doet moeilijk over {niche}, maar het is simpel.'\n**CTA:** 'Wat vind jij?'"

def generate_challenge_script(day, task, niche, format_type):
    ai_sys = f"Je bent een strenge maar rechtvaardige TikTok coach. Het is bootcamp dag {day}. De taak is: {task}. Niche: {niche}. Format: {format_type}."
    llm_out = call_llm(ai_sys, "Schrijf het script voor vandaag.")
    if llm_out: return llm_out
    
    return f"**📅 Bootcamp Dag {day}**\n*Opdracht: {task}*\n\nProbeer de AI opnieuw te activeren."

def generate_sales_script(product, pain, angle, niche):
    ai_sys = f"Je bent een conversie-expert en copywriter voor {niche}. Je gebruikt psychologische triggers (PAS: Pain, Agitation, Solution)."
    ai_user = f"Verkoop het product '{product}'. De pijn van de klant is '{pain}'. Format: TikTok Story."
    llm_out = call_llm(ai_sys, ai_user)
    if llm_out: return llm_out
    
    return f"**🚀 Sales: {product}**\n\nAI is even niet beschikbaar."

# ==========================================
# 2. INTELLIGENTE TOOLS (100% AI)
# ==========================================

def check_viral_potential(idea, niche):
    """Beoordeelt een idee met een score 0-100 en feedback."""
    ai_sys = f"Je bent een kritisch TikTok algoritme. Je beoordeelt video-ideeën voor de niche '{niche}'."
    ai_user = f"Beoordeel dit idee: '{idea}'. Geef een score van 0 tot 100 en 1 zin keiharde, eerlijke feedback. Begin je antwoord met 'Score: [getal]'. "
    
    llm_out = call_llm(ai_sys, ai_user)
    
    if llm_out:
        # Probeer het getal uit de tekst te vissen met Regex
        score_match = re.search(r'Score:\s*(\d+)', llm_out)
        if score_match:
            score = int(score_match.group(1))
            verdict = llm_out.replace(score_match.group(0), "").strip()
        else:
            # Als AI geen "Score:" format volgt, gokken we op het eerste getal of een default
            first_num = re.search(r'\d+', llm_out)
            score = int(first_num.group(0)) if first_num else 50
            verdict = llm_out

        return {"score": score, "verdict": verdict}
    
    return {"score": 0, "verdict": "Kon AI niet bereiken."}

def generate_weekly_plan(niche):
    """Maakt een unieke contentkalender voor de niche."""
    ai_sys = f"Je bent een content strateeg voor {niche}. Maak een strategische weekplanning (Maandag t/m Zondag)."
    ai_user = "Geef me een weekplanning. Gebruik bulletpoints/emoji's. Voor elke dag: 1 Thema + 1 Concrete Hook. Zorg voor afwisseling (viral vs sales)."
    
    llm_out = call_llm(ai_sys, ai_user)
    if llm_out: return llm_out
    
    return "AI Fout: Kon geen uniek schema maken."

def generate_digital_product_plan(niche, target):
    """Bedenkt een digitaal product + mini business plan."""
    ai_sys = f"Je bent een business coach voor creators in {niche}. Bedenk een winstgevend digitaal product voor doelgroep: {target}."
    ai_user = """
    Schrijf een mini-businessplan:
    1. **Titel van het product** (Catchy & Sellable)
    2. **Het Concept** (E-book, Cursus, Template?)
    3. **Prijsstrategie** (Wat vraag je en waarom?)
    4. **Inhoudsopgave**: 3 Hoofdstukken/Modules die erin moeten.
    """
    
    llm_out = call_llm(ai_sys, ai_user)
    if llm_out: return llm_out
    
    return f"**Masterplan {niche}:** Kon geen plan genereren."

def generate_series_ideas(topic, niche):
    """Bedenkt een 5-delige serie."""
    ai_sys = f"Je bent een content strateeg voor {niche}. Bedenk een 5-delige TikTok serie over '{topic}' die mensen dwingt om te blijven kijken (binge-waardig)."
    llm_out = call_llm(ai_sys, "Geef de titels en korte inhoud voor deel 1 t/m 5. Maak de titels clickbait-waardig.")
    if llm_out: return llm_out

    return f"**Serie {topic}:** AI niet beschikbaar."

def rate_user_hook(user_hook, niche):
    """Geeft feedback op een hook."""
    ai_sys = f"Je bent een kritische TikTok hook expert voor {niche}. Beoordeel de hook op schaal 1-10 en geef harde feedback."
    llm_out = call_llm(ai_sys, f"Beoordeel deze hook: '{user_hook}'")
    
    if llm_out:
        return {"score": "AI", "feedback": llm_out}
        
    return {"score": "?", "feedback": "AI offline."}

def generate_bio_options(bio, niche):
    """Herschrijft de bio."""
    ai_sys = f"Je bent een profile optimizer voor {niche}. Herschrijf deze bio om meer volgers en kliks te krijgen. Geef 3 opties."
    llm_out = call_llm(ai_sys, f"Huidige bio: {bio}")
    if llm_out: return llm_out
    return f"**Bio Optie:** 🏆 {niche} Expert | 🚀 Tips | 👇 Start hier"

def steal_format_and_rewrite(other_script, my_topic, niche):
    """Remixed een script."""
    ai_sys = f"Je bent een remix expert. Analyseer de *structuur* (niet de inhoud) van het gegeven script. Schrijf een NIEUW script over '{my_topic}' voor de niche '{niche}' dat exact die succesvolle structuur volgt."
    llm_out = call_llm(ai_sys, f"Script om te analyseren: {other_script}")
    if llm_out: return llm_out
    return "**Remix:** AI offline."

# ==========================================
# 3. HELPERS & DATA (Statisch / Simulatie)
# ==========================================

def get_weekly_trend():
    """
    Geeft een hardcoded 'Viral Pick' terug. 
    (We doen dit niet via AI om de homepage snel te houden).
    """
    trends = [
        {"title": "De 'Wes Anderson' Stijl", "desc": "Symmetrisch, stilstaand beeld, vrolijke muziek.", "sound": "Obituary - Alexandre Desplat"},
        {"title": "Photo Swipe Challenge", "desc": "Snel achter elkaar foto's op de beat.", "sound": "Any fast Phonk beat"},
        {"title": "Silent Review", "desc": "Producten reviewen door alleen gezichtsuitdrukkingen.", "sound": "ASMR sounds"},
        {"title": "POV: You found...", "desc": "Camera standpunt vanuit de ogen van de kijker.", "sound": "Trending Pop Song"}
    ]
    return random.choice(trends)

def get_challenge_tasks():
    return {
        1: "De 'Wie ben ik' video (maar dan niet saai)", 
        2: "De grootste fout in jouw niche", 
        3: "Een snelle, waardevolle tip (Green Screen)", 
        4: "Reageer op een nieuwsbericht in je markt", 
        5: "Behind the Scenes (zonder woorden)", 
        6: "Beantwoord de meest gestelde vraag", 
        7: "Ontkracht een hardnekkige mythe", 
        8: "Persoonlijk verhaal (Storytelling)", 
        9: "How-to tutorial (stap voor stap)", 
        10: "Klantresultaat / Case Study"
    }

def analyze_analytics_screenshot(img_file):
    """
    Simuleert Vision API. 
    Om dit ECHT te maken, moet je de image base64 encoden en naar GPT-4o sturen.
    Voor nu simuleren we een slimme analyse om de UX te testen.
    """
    time.sleep(3) # "AI is thinking..."
    return {
        "totaal_views": 12500,
        "beste_video": "Die over tips (3.2k views)",
        "advies": "Je video's op dinsdag doen het goed. Je retentie zakt na 3 seconden: werk aan je hooks!",
        "views_history": {"Ma": 1200, "Di": 3400, "Wo": 800, "Do": 2100, "Vr": 5000}
    }

def create_ics_file(niche):
    now = datetime.datetime.now()
    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//PostAi//NONSGML v1.0//EN\n"
    days = ["Maandag: Mythe", "Dinsdag: Vlog", "Woensdag: Tip", "Donderdag: Story", "Vrijdag: Sales"]
    for i, task in enumerate(days):
        dt_start = (now + datetime.timedelta(days=i+1)).strftime('%Y%m%dT090000')
        dt_end = (now + datetime.timedelta(days=i+1)).strftime('%Y%m%dT093000')
        ics_content += f"BEGIN:VEVENT\nDTSTART:{dt_start}\nDTEND:{dt_end}\nSUMMARY:PostAi Content - {task} ({niche})\nDESCRIPTION:Tijd om te filmen! Opdracht: {task}\nEND:VEVENT\n"
    ics_content += "END:VCALENDAR"
    return ics_content

def get_leaderboard(niche, xp):
    return pd.DataFrame({
        "Rank": [1, 2, 3, 4], 
        "Naam": ["Pro Creator", "Jij", "Starter", "Newbie"], 
        "XP": [5000, xp, 200, 50]
    })