import streamlit as st
from openai import OpenAI
import os
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

# --- GENERATORS ---
def generate_script(topic, video_format, tone, hook, cta, niche, user_style=""):
    client = get_client()
    if not client: return "⚠️ Geen API Key."
    style_ins = f"Stijl: {user_style}" if user_style else ""
    prompt = f"""
    Expert TikTok Script. Niche: {niche} | Topic: {topic} | Format: {video_format} | Tone: {tone}.
    Hook: {hook} | CTA: {cta}. {style_ins}. Output: Markdown Tabel (Tijd|Visueel|Audio).
    """
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"Error: {str(e)}"

def generate_sales_script(product, pain, strategy, niche):
    client = get_client()
    if not client: return "⚠️ Geen API Key."
    prompt = f"""
    Direct Response Copywriting TikTok Script.
    Product: {product}. Pain: {pain}. Strategy: {strategy}. Niche: {niche}.
    Gebruik AIDA. Output: Markdown Tabel (Tijd|Visueel|Audio).
    """
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except Exception as e: return f"Error: {str(e)}"

# --- ANALYTICS (DE DATA DETECTIVE) ---
def analyze_data_patterns(df_summary, niche):
    """
    Dit is de PRO functie die ruwe data omzet in goud.
    """
    client = get_client()
    if not client: return "Geen API Key."
    
    prompt = f"""
    Jij bent een Data Analist voor TikTok Creators.
    Hier is een samenvatting van de account statistieken van een creator in de niche '{niche}':
    
    DATA SAMENVATTING:
    {df_summary}
    
    OPDRACHT:
    Zoek naar verborgen patronen. Waarom scoort de top video goed? Waarom faalt de rest?
    Geef 3 CONCRETE inzichten.
    
    Output format (JSON):
    {{
        "insight_1": "Titel + Uitleg",
        "insight_2": "Titel + Uitleg",
        "insight_3": "Titel + Uitleg",
        "strategy_tip": "Eén concrete actie voor de volgende video."
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
        return {
            "insight_1": "Focus op Hooks", 
            "insight_2": "Korte video's werken beter", 
            "insight_3": "Gebruik meer tekst", 
            "strategy_tip": "Probeer de eerste 3 seconden sneller te maken."
        }

# --- OVERIGE FUNCTIES ---
def generate_digital_product(niche, audience):
    client = get_client()
    prompt = f"Bedenk digitaal product voor {niche} doelgroep {audience}. Markdown: Titel, Format, Prijs, Hoofdstukken."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Error."

def audit_script(script_text, niche):
    client = get_client()
    prompt = f"Audit script ({niche}). JSON: score(0-100), verdict, pros, cons, tip. Script: {script_text}"
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
        return json.loads(res.choices[0].message.content)
    except: return {"score": 70, "verdict": "Prima", "pros": "-", "cons": "-", "tip": "-"}

def check_viral_potential(idea, niche):
    client = get_client()
    prompt = f"Rate idea '{idea}' ({niche}). JSON: score(0-100), label, explanation, tip."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
        return json.loads(res.choices[0].message.content)
    except: return {"score": 50, "label": "Error", "explanation": "-", "tip": "-"}

def generate_series_ideas(topic, niche):
    client = get_client()
    prompt = f"5-delige TikTok serie '{topic}' ({niche}). Markdown."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Error."

def steal_format_and_rewrite(other, mine, niche):
    client = get_client()
    prompt = f"Steel structuur van '{other}', schrijf over '{mine}' ({niche}). Markdown."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Error."

def generate_weekly_plan(niche):
    client = get_client()
    prompt = f"7 Dagen content kalender '{niche}'. Tabel."
    try:
        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
        return res.choices[0].message.content
    except: return "Error."