import streamlit as st
from openai import OpenAI
import os
import datetime
import json

def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try: api_key = st.secrets["OPENAI_API_KEY"]
        except: return None
    return OpenAI(api_key=api_key)

# --- 30 DAGEN CHALLENGE LOGICA ---
def get_challenge_tasks():
    return {
        1: "De 'Wie ben ik' (Introductie)",
        2: "Deel een persoonlijke fout",
        3: "De snelle tip (Quick Win)",
        4: "Reageer op een vraag",
        5: "Behind the scenes (Werkplek)",
        6: "Mythe ontkrachten",
        7: "Favoriete tool of app",
        8: "Klant succesverhaal",
        9: "Dit vs. Dat",
        10: "Kleine overwinning vieren",
    }

def get_daily_pro_tip(day):
    tips = {
        1: "Film dit niet zittend! Sta op en beweeg. Energie = Retentie.",
        2: "Begin niet met 'Hoi ik ben..'. Begin direct met de fout die je maakte.",
        3: "Houd de tip onder de 15 seconden. Korte video's worden vaker herbekeken.",
        4: "Gebruik de 'Green Screen' functie met de vraag in beeld voor visuele context.",
        5: "Het hoeft niet netjes te zijn! Rommel op je bureau creëert juist authenticiteit.",
    }
    return tips.get(day, "Zorg voor goed licht (raam) en heldere audio. Dat is 50% van je succes.")

def generate_challenge_script(day_number, task_description, niche, format_type="Video"):
    client = get_client()
    if not client: return "⚠️ Geen API Key."
    
    if "Foto" in format_type:
        prompt = f"""
        Je bent een Nederlandse TikTok Expert.
        Opdracht: Schrijf een script voor de '30 Dagen Viral Challenge' (Dag {day_number}).
        Taak: {task_description}.
        Niche: {niche}.
        Format: FOTO CARROUSEL (TikTok Slide).
        
        EISEN:
        1. Taal: NEDERLANDS.
        2. Geef ALLEEN de tabel terug. Geen introductie of tekst eromheen.
        3. Schrijf tekst voor 3-5 slides.
        
        Output formaat (Markdown Tabel):
        | Slide | Afbeelding (Wat staat er op de foto?) | Tekst Overlay (Wat staat er in beeld?) | Caption (Onderschrift) |
        """
    else:
        prompt = f"""
        Je bent een Nederlandse TikTok Expert.
        Opdracht: Schrijf een script voor de '30 Dagen Viral Challenge' (Dag {day_number}).
        Taak: {task_description}.
        Niche: {niche}.
        Format: KORTE VIDEO.
        
        EISEN:
        1. Taal: NEDERLANDS.
        2. Geef ALLEEN de tabel terug. Geen introductie of tekst eromheen.
        3. Gebruik spreektaal.
        
        Output formaat (Markdown Tabel): | Tijd | Visueel (Wat zien we?) | Audio (Wat zeg ik?) |
        """
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"Error: {str(e)}"

# --- GENERATORS ---
def get_viral_hooks_library():
    return [
        "Stop met {onderwerp} op deze manier...",
        "Waarom niemand praat over {onderwerp}...",
        "Ik testte {onderwerp} voor 7 dagen...",
        "3 signalen dat je {onderwerp} verkeerd doet...",
        "De #1 hack voor {onderwerp}...",
        "POV: Je snapt eindelijk {onderwerp}...",
        "Dit verandert alles aan {onderwerp}..."
    ]

def generate_script(topic, video_format, tone, hook, cta, niche, user_style=""):
    client = get_client()
    if not client: return "⚠️ Geen API Key."
    style_ins = f"Hanteer deze schrijfstijl: {user_style}" if user_style else ""
    
    prompt = f"""
    Je bent een Nederlandse TikTok Scripter.
    Niche: {niche} | Topic: {topic} | Format: {video_format} | Toon: {tone}.
    Hook: {hook} | CTA: {cta}. 
    {style_ins}
    
    EISEN:
    1. Taal: NEDERLANDS.
    2. Geef ALLEEN de Markdown Tabel terug. Geen inleiding ("Hier is je script").
    3. Kolommen: | Tijd | Visueel | Audio |
    """
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"Error: {str(e)}"

def generate_sales_script(product, pain, strategy, niche):
    client = get_client()
    if not client: return "⚠️ Geen API Key."
    
    prompt = f"""
    Je bent een Nederlandse Copywriter voor TikTok.
    DOEL: VERKOOP. Product: '{product}'. Pijn: '{pain}'. Strategie: {strategy}. Niche: '{niche}'.
    
    EISEN:
    1. Taal: NEDERLANDS.
    2. Geef ALLEEN de Markdown Tabel terug. Geen chat eromheen.
    3. Gebruik het AIDA model.
    4. Kolommen: | Tijd | Visueel | Audio |
    """
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"Error: {str(e)}"

def generate_digital_product_plan(niche, audience):
    client = get_client()
    if not client: return "⚠️ Geen API Key."
    
    prompt = f"""
    Jij bent een Nederlandse Business Coach.
    Niche: {niche}. Doelgroep: {audience}.
    
    Ontwikkel ÉÉN compleet digitaal product (Cursus/E-book).
    Taal: NEDERLANDS.
    
    Structuur (Markdown):
    # 🚀 MASTERPLAN: [Product Naam]
    ## 1. Belofte
    ## 2. Inhoud (Modules)
    ## 3. Bonussen
    ## 4. Prijs & Omzet
    ## 5. Lancering Script (Video)
    ## 6. Email Funnel (3 mails)
    """
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return res.choices[0].message.content
    except: return "Kon business plan niet genereren."

# --- ANALYTICS ---
def analyze_data_patterns(df_summary, niche):
    client = get_client()
    prompt = f"""
    Data Analist (Nederlands). Niche: {niche}. Data: {df_summary}.
    Geef 3 inzichten + 1 strategie tip. 
    Output JSON: insight_1, insight_2, insight_3, strategy_tip.
    Taal: Nederlands.
    """
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
        return json.loads(res.choices[0].message.content)
    except: return {"strategy_tip": "Post consistenter."}

def audit_script(script_text, niche):
    client = get_client()
    prompt = f"""
    Beoordeel dit TikTok script ({niche}). Taal: Nederlands.
    Output JSON: score (0-100), verdict (oordeel), pros (pluspunten), cons (minpunten), tip.
    Script: {script_text}
    """
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
        return json.loads(res.choices[0].message.content)
    except: return {"score": 75, "verdict": "Prima basis.", "pros": "Helder", "cons": "Kan scherper", "tip": "Meer energie."}

def check_viral_potential(idea, niche):
    client = get_client()
    prompt = f"Beoordeel video idee '{idea}' ({niche}). Taal: Nederlands. Output JSON: score (0-100), label (Kort), explanation, tip."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
        return json.loads(res.choices[0].message.content)
    except: return {"score": 50, "label": "Error", "explanation": "-", "tip": "-"}

def generate_series_ideas(topic, niche):
    client = get_client()
    prompt = f"Bedenk een 5-delige TikTok serie over '{topic}' ({niche}). Taal: Nederlands. Markdown format."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Error."

def steal_format_and_rewrite(other, mine, niche):
    client = get_client()
    prompt = f"Analyseer de structuur van '{other}'. Schrijf een NIEUW script over '{mine}' ({niche}) met diezelfde structuur. Taal: Nederlands. Alleen script."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Error."

def generate_weekly_plan(niche):
    client = get_client()
    prompt = f"7 Dagen content kalender '{niche}'. Taal: Nederlands. Markdown Tabel."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Error."