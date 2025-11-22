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
    # Hooks zijn de openingzinnen die zorgen dat mensen blijven kijken
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
    if not client: return "⚠️ Geen API Key. Check je instellingen."
    
    prompt = f"""
    Je bent een expert TikTok Scripter.
    DOEL: Een script schrijven dat de kijker vasthoudt tot het einde.
    
    INFO:
    - Niche: {niche}
    - Onderwerp: {topic}
    - Manier van filmen: {video_format}
    - Sfeer/Toon: {tone}
    - Opening (Hook): {hook}
    - Einde (Actie): {cta}
    
    FORMAT (Markdown Tabel):
    | Tijd | Wat te zien (Visueel) | Wat te zeggen (Audio) |
    
    EISEN:
    - Schrijf in spreektaal (Kort, krachtig, menselijk).
    - Geef duidelijke visuele instructies (Bv. "Wijs naar boven", "Tekst in beeld: ...").
    - Geef onder de tabel een suggestie voor "Tekst op Cover/Thumbnail".
    """
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"Fout bij genereren: {str(e)}"

def audit_script(script_text, niche):
    client = get_client()
    if not client: return {"score": 0, "verdict": "Geen verbinding", "pros": "-", "cons": "-", "tip": "-"}
    
    prompt = f"""
    Jij bent het TikTok Algoritme. Beoordeel dit script ({niche}) streng.
    Script: {script_text}
    
    Geef JSON terug:
    {{
        "score": (0-100),
        "verdict": (Zeer korte mening),
        "pros": (Sterke punten, max 5 woorden),
        "cons": (Zwakke punten, max 5 woorden),
        "tip": (1 actiegerichte tip)
    }}
    """
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(res.choices[0].message.content)
    except:
        return {"score": 70, "verdict": "Prima, maar kan spannender.", "pros": "Duidelijk", "cons": "Beetje saai", "tip": "Voeg meer energie toe."}

def check_viral_potential(idea, niche):
    client = get_client()
    prompt = f"""
    Beoordeel dit video-idee voor de niche '{niche}'.
    Idee: '{idea}'
    
    Geef antwoord als JSON:
    {{
        "score": (getal 0-100),
        "label": (Kort label: "Viral Hit", "Prima", "Saai", of "Flop"),
        "explanation": (Korte uitleg waarom),
        "tip": (Eén concrete tip om de score te verhogen)
    }}
    """
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(res.choices[0].message.content)
    except: 
        return {"score": 50, "label": "Foutje", "explanation": "Kon niet verbinden.", "tip": "Probeer opnieuw."}

def generate_series_ideas(topic, niche):
    """
    Genereert een 5-delige serie structuur.
    """
    client = get_client()
    if not client: return "⚠️ Geen API Key."
    
    prompt = f"""
    Ik wil een 'TikTok Serie' maken om volgers te binden (Deel 1 t/m 5).
    Niche: {niche}
    Onderwerp van de serie: {topic}
    
    Bedenk 5 video's die op elkaar aansluiten.
    Zorg voor een "Cliffhanger" effect tussen de delen.
    
    Format: Markdown.
    Gebruik emojis.
    Voor elk deel: 
    1. Titel (Tekst op Cover)
    2. De Hook (Eerste zin)
    3. Korte inhoud (Wat gebeurt er?)
    """
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Kon serie niet maken."

def steal_format_and_rewrite(other_script, my_topic, niche):
    client = get_client()
    prompt = f"Analyseer de structuur van dit script: '{other_script}'. Schrijf een NIEUW script over '{my_topic}' ({niche}) dat exact die structuur volgt."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Fout."

def generate_weekly_plan(niche):
    client = get_client()
    prompt = f"7 Dagen content kalender voor '{niche}'. Tabelvorm: Dag|Format|Idee|Waarom dit werkt."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Fout."