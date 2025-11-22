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

def generate_script(topic, video_format, tone, hook, cta, niche):
    client = get_client()
    if not client: return "⚠️ Geen API Key."
    
    prompt = f"""
    Expert TikTok Script.
    Niche: {niche} | Topic: {topic} | Format: {video_format} | Toon: {tone}.
    Hook: {hook} | CTA: {cta}.
    Format: Markdown Tabel (Tijd | Visueel | Audio).
    """
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"Error: {str(e)}"

def generate_sales_script(product, pain, strategy, niche):
    """
    De 'Money Maker'. Genereert scripts puur voor conversie.
    """
    client = get_client()
    if not client: return "⚠️ Geen API Key."
    
    prompt = f"""
    Je bent een Direct Response Copywriter voor TikTok.
    DOEL: VERKOOP. Product: '{product}'. Niche: '{niche}'.
    Strategie: {strategy}.
    Pijn die het oplost: {pain}.
    
    Schrijf een script dat de kijker direct grijpt en niet loslaat tot ze kopen.
    
    Structuur:
    1. HOOK: Raak de pijn.
    2. STORY/DEMO: Laat zien hoe het leven is MET product.
    3. OFFER: Wat krijgen ze?
    4. CTA: Dwingende reden om NU te klikken.
    
    Output: Markdown Tabel (Tijd | Visueel | Audio).
    """
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"Error: {str(e)}"

def generate_digital_product(niche, audience):
    """
    De Passief Inkomen Bedenker.
    """
    client = get_client()
    if not client: return "⚠️ Geen API Key."
    
    prompt = f"""
    Ik ben een creator in de niche '{niche}' en mijn doelgroep is '{audience}'.
    Bedenk HET perfecte digitale product om te verkopen (E-book, Cursus, Template).
    
    Geef me een compleet Business Plan:
    1. **De Titel** (Pakkend)
    2. **Het Format** (Wat is het?)
    3. **De Prijs** (Adviesprijs)
    4. **De Hoofdstukindeling** (5-7 modules/hoofdstukken)
    5. **De Marketing Hook** (Eén zin om het te verkopen)
    
    Gebruik Markdown. Maak het aantrekkelijk.
    """
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Fout bij genereren."

def audit_script(script_text, niche):
    client = get_client()
    prompt = f"Beoordeel script ({niche}) op JSON: score (0-100), verdict, pros, cons, tip. Script: {script_text}"
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
        return json.loads(res.choices[0].message.content)
    except: return {"score": 75, "verdict": "Prima basis.", "pros": "Helder", "cons": "Kan scherper", "tip": "Meer energie."}

def check_viral_potential(idea, niche):
    client = get_client()
    prompt = f"Beoordeel idee '{idea}' ({niche}) JSON: score (0-100), label, explanation, tip."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
        return json.loads(res.choices[0].message.content)
    except: return {"score": 50, "label": "Error", "explanation": "-", "tip": "-"}

def generate_series_ideas(topic, niche):
    client = get_client()
    prompt = f"5-delige TikTok serie over '{topic}' ({niche}). Markdown. Titel, Hook, Inhoud per deel."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Error."

def steal_format_and_rewrite(other_script, my_topic, niche):
    client = get_client()
    prompt = f"Analyseer structuur van '{other_script}'. Schrijf nieuw script over '{my_topic}' ({niche}) met die structuur."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Error."

def generate_weekly_plan(niche):
    client = get_client()
    prompt = f"7 Dagen content kalender '{niche}'. Tabel: Dag|Idee|Waarom."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Error."