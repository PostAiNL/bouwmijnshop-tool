import streamlit as st
from openai import OpenAI
import pandas as pd
import os  # <--- Importeer os

def get_client():
    # Vervang st.secrets door os.getenv
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: return None
    return OpenAI(api_key=api_key)

def generate_script_from_data(topic: str, top_posts: pd.DataFrame, style="Direct"):
    """Genereert een script gebaseerd op wat eerder werkte voor deze gebruiker."""
    client = get_client()
    if not client: return "⚠️ Configureer je OpenAI API key om deze functie te gebruiken."

    # Context bouwen uit eerdere successen
    context = ""
    if not top_posts.empty:
        best_post = top_posts.iloc[0]
        context = f"Mijn beste video ooit ging over '{best_post.get('Caption', 'onbekend')}' en haalde {best_post['Views']} views."

    prompt = f"""
    Je bent een expert TikTok strateeg.
    Context: {context}
    Doel: Schrijf een script voor een nieuwe video over '{topic}'.
    Stijl: {style} (Kort, punchy, geen cringe).
    
    Format:
    HOOK (0-2s): [Pakkende zin]
    BODY (15-30s): [Bullet points met wat te zeggen/doen]
    CTA: [Eén duidelijke actie]
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Snel & Goedkoop
            messages=[{"role": "system", "content": "Je bent een TikTok expert."},
                      {"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Fout: {str(e)}"

def get_quick_win_idea(niche: str):
    """Genereert 1 direct uitvoerbaar idee."""
    client = get_client()
    if not client: return "Maak een 'Behind the Scenes' van je werkplek."
    
    prompt = f"Geef mij 1 uniek, direct uitvoerbaar TikTok idee voor de niche: {niche}. Geef alleen de titel en de hook."
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content