import random
import time
import pandas as pd
import datetime
import os
import streamlit as st
import re # Nodig om scores uit tekst te vissen
import base64

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

@st.cache_data(ttl=3600, show_spinner=False) # FIX: show_spinner=False toegevoegd
def generate_weekly_plan(niche):
    """Maakt een unieke contentkalender voor de niche."""
    ai_sys = f"Je bent een content strateeg voor {niche}. Maak een strategische weekplanning (Maandag t/m Zondag)."
    ai_user = "Geef me een weekplanning. Gebruik bulletpoints/emoji's. Voor elke dag: 1 Thema + 1 Concrete Hook. Zorg voor afwisseling (viral vs sales)."
    
    if not HAS_OPENAI or not client: return "AI Fout: Kon geen uniek schema maken."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": ai_sys}, {"role": "user", "content": ai_user}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except:
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
    """Geeft feedback én 3 betere alternatieven in JSON."""
    import json
    
    ai_sys = f"Je bent een virale TikTok expert voor de niche '{niche}'. Beoordeel de hook."
    ai_user = f"""
    Analyseer deze hook: '{user_hook}'.
    
    Geef antwoord in JSON formaat met de volgende velden:
    - score (getal 1-10)
    - feedback (1 pittige zin waarom het goed/slecht is)
    - alternatives (een lijst met 3 véél betere, virale variaties op deze hook)
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": ai_sys},
                {"role": "user", "content": ai_user}
            ],
            response_format={ "type": "json_object" }
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Hook Error: {e}")
        return {
            "score": 5, 
            "feedback": "Kon AI niet bereiken, maar let op dat je 'je' gebruikt.",
            "alternatives": ["Alternatief 1", "Alternatief 2", "Alternatief 3"]
        }

@st.cache_data(ttl=3600, show_spinner=False) # FIX: show_spinner=False toegevoegd
def generate_bio_options(bio, niche):
    """Herschrijft de bio."""
    ai_sys = f"Je bent een profile optimizer voor {niche}. Herschrijf deze bio om meer volgers en kliks te krijgen. Geef 3 opties."
    
    if not HAS_OPENAI or not client: return f"**Bio Optie:** 🏆 {niche} Expert | 🚀 Tips | 👇 Start hier"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": ai_sys}, {"role": "user", "content": f"Huidige bio: {bio}"}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except:
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

def analyze_analytics_screenshot(uploaded_file):
    """
    ECHTE ANALYSE: Stuurt het plaatje naar GPT-4o voor feedback.
    Versie 2.0: Met extra foutopsporing en null-checks.
    """
    # Zorg dat de imports lokaal beschikbaar zijn voor deze functie
    import base64
    import json

    if not HAS_OPENAI or not client:
        return {"advies": "AI niet verbonden (Check API Key).", "beste_video": "-", "totaal_views": 0}

    try:
        # 1. Zet plaatje om naar base64
        # We gebruiken .getvalue() voor Streamlit uploaded files
        uploaded_file.seek(0) # Reset pointer voor de zekerheid
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')

        # 2. De Prompt naar GPT-4o
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Je bent een TikTok expert. Analyseer deze screenshot. Geef JSON antwoord met keys: 'totaal_views' (getal of schatting), 'beste_video' (korte tekst), advies (2 zinnen concreet advies waarom de views stoppen). Als je het niet kan lezen, zet null."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ],
                }
            ],
            max_tokens=400,
            response_format={ "type": "json_object" } # Dwingt JSON af
        )
        
        # 3. Verwerk antwoord
        result_text = response.choices[0].message.content
        
        # CHECK: Is het antwoord leeg?
        if result_text is None:
            return {
                "totaal_views": 0, 
                "beste_video": "Geen tekst", 
                "advies": "AI gaf geen tekst terug. Probeer een duidelijkere screenshot."
            }

        # Schoonmaken (soms zet AI er ```json omheen)
        clean_text = result_text.replace("```json", "").replace("```", "").strip()
        
        return json.loads(clean_text)

    except Exception as e:
        # Print de error ook in je terminal/console voor debugging
        print(f"❌ Vision Error: {e}")
        return {
            "totaal_views": 0,
            "beste_video": "Fout",
            "advies": f"Fout bij analyse: {str(e)}"
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

def generate_viral_image(topic, style, niche):
    """
    Genereert een realistisch TikTok-shot concept.
    """
    if not HAS_OPENAI or not client:
        return None

    try:
        # Een veel slimmere prompt:
        prompt = f"""
        A high-quality, vertical (9:16 aspect ratio) photo acting as a TikTok thumbnail for the niche: '{niche}'.
        Topic of the video: '{topic}'.
        
        Visual Style: {style}.
        Camera Angle: POV (Point of View) or Close-up shot taken with an iPhone 15 Pro.
        Lighting: Bright, natural lighting or Ring light studio setup.
        Atmosphere: Authentic User Generated Content (UGC), not too cartoony.
        
        No text overlays, just the visual scene.
        """
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1792", # DALL-E 3 ondersteunt staand formaat!
            quality="standard",
            n=1,
        )
        
        return response.data[0].url
    except Exception as e:
        print(f"DALL-E Error: {e}")
        return None

def analyze_writing_style(sample_text):
    """
    CLONE MY VOICE: Analyseert tekst en maakt een persona beschrijving.
    """
    ai_sys = "Je bent een linguïstisch expert. Analyseer de schrijfstijl van deze tekst. Let op: Toon, zinslengte, gebruik van emoji's, humor, jargon en formatterig."
    ai_user = f"Beschrijf de schrijfstijl van deze tekst in 1 korte zin zodat ik het als instructie aan een AI kan geven (bv: 'Schrijf als...'). Tekst: {sample_text}"
    
    llm_out = call_llm(ai_sys, ai_user)
    if llm_out: return llm_out
    return "Een authentieke, persoonlijke schrijfstijl."

@st.cache_data(ttl=3600, show_spinner=False) # FIX: show_spinner=False toegevoegd
def get_personalized_trend(niche):
    """
    SLIMME TRENDS: Bedenkt een trend specifiek voor de niche.
    """
    import json
    
    ai_sys = f"Je bent een virale trendwatcher voor de niche '{niche}'. Bedenk 1 actueel, concreet video-format dat NU zou werken."
    ai_user = "Geef antwoord in JSON formaat met de keys: 'title', 'desc' (korte uitleg wat je moet doen) en 'sound' (suggestie voor muziek/audio)."
    
    # Init client checken, want cache heeft eigen scope
    if not HAS_OPENAI or not client:
         return {
            "title": f"De {niche} Fout", 
            "desc": "Laat zien wat iedereen fout doet en hoe jij het oplost.", 
            "sound": "Trending Audio"
        }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": ai_sys},
                {"role": "user", "content": ai_user}
            ],
            temperature=0.7,
            response_format={ "type": "json_object" }
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Trend Error: {e}")
        return {
            "title": f"De {niche} Fout", 
            "desc": "Laat zien wat iedereen fout doet en hoe jij het oplost.", 
            "sound": "Trending Audio"
        }

def check_feedback_quality(text):
    """
    Checkt of feedback nuttig is of spam.
    Geeft True terug als het goedgekeurd is, anders False.
    """
    if len(text) < 10: return False # Te kort is altijd spam
    
    import json
    ai_sys = "Je bent een moderator. Beoordeel of deze gebruikersfeedback nuttig/constructief is of onzin/spam."
    ai_user = f"""
    Feedback: "{text}"
    
    Antwoord in JSON:
    - is_valid: (true/false) - Is het een echte zin/mening? (Geen 'asdf', geen gescheld).
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": ai_sys},
                {"role": "user", "content": ai_user}
            ],
            response_format={ "type": "json_object" }
        )
        res = json.loads(response.choices[0].message.content)
        return res.get("is_valid", False)
    except:
        return True