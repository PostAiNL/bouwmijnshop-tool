import streamlit as st
import json
import requests
import base64
import warnings
from openai import OpenAI

warnings.simplefilter("ignore")


def init_ai():
    """Initialiseert de OpenAI client met de key uit secrets."""
    if "OPENAI_API_KEY" in st.secrets:
        return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    return None

def call_llm(system_prompt, user_prompt, model="gpt-4o-mini", json_mode=False):
    """Generieke helper om de LLM aan te roepen."""
    client = init_ai()
    if not client: return None
    try:
        kwargs = {
            "model": model, 
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], 
            "temperature": 0.7
        }
        if json_mode: kwargs["response_format"] = { "type": "json_object" }
        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except: return None

# --- NIEUWE UPGRADES: VISION & CFO ---

def get_cfo_advice(revenue, spend, cogs):
    """De CFO Bot: Analyseert winstgevendheid en geeft direct actie-advies."""
    profit = revenue - spend - cogs
    roas = revenue / spend if spend > 0 else 0
    
    prompt = f"Omzet: €{revenue}, Ads: €{spend}, Inkoop: €{cogs}, Winst: €{profit}, ROAS: {roas}. Geef 1 kort advies (max 25 woorden) voor groei of besparing."
    return call_llm("Je bent een agressieve E-com CFO die focust op netto winst.", prompt) or "Blijf je marges bewaken."

def analyze_ad_screenshot(image_file):
    """AI Vision: Analyseert advertentie screenshots op conversie-punten."""
    client = init_ai()
    if not client: return "Vision AI niet beschikbaar (Check API Key)."
    
    # Encode image naar base64
    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyseer deze advertentie voor een webshop. Geef 3 kritische punten voor betere conversie (visuals/copy). Hou het kort en direct."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ],
                }
            ],
            max_tokens=300,
        )
        return response.choices[0].message.content
    except Exception as e: 
        return f"Analyse mislukt: {e}"

# --- LOGO GENERATIE (CLEAN VECTOR STYLE) ---

def generate_logo(brand_name, niche, style, colors):
    """Genereert een logo met Ideogram (Beter met tekst)."""
    # Check of de key is ingevuld
    if "PLAK_HIER" in IDEOGRAM_API_KEY:
        return f"https://placehold.co/1024x1024/2563EB/FFFFFF/png?text={brand_name}"

    url = "https://api.ideogram.ai/generate"

    # 1. Bepaal de 'Vibe'
    style_prompt = ""
    if style == "Minimalistisch":
        style_prompt = "minimalist, flat line art, apple style, less is more"
    elif style == "Modern & strak":
        style_prompt = "modern, tech, geometric, bold sans-serif"
    elif style == "Vintage":
        style_prompt = "retro badge, 2d stamp style, classic serif"
    elif style == "Luxe":
        style_prompt = "luxury fashion, elegant thin lines, high-end serif"
    elif style == "Speels":
        style_prompt = "playful, bold shapes, mascot, vibrant"
    else:
        style_prompt = "professional corporate, clean vector"

    # 2. De 'Anti-Mockup' Prompt
    # We gebruiken termen als 'sticker', 'vector file' en 'white background' om 3D effecten te doden.
    prompt = (
        f"A single, isolated, flat vector logo for the brand '{brand_name}'. "
        f"Strict design requirements: "
        f"1. NO MOCKUPS. Do not show the logo on a wall, paper, or screen. "
        f"2. NO 3D EFFECTS. No shadows, no gradients, no realism. Completely flat 2D design. "
        f"3. LAYOUT: An abstract {niche} icon on top, with the text '{brand_name}' directly below it. "
        f"4. TYPOGRAPHY: {style_prompt}. Correct spelling is mandatory. "
        f"5. COLORS: {colors}. Use a solid, pure white background (#FFFFFF). "
        f"The result must look like an SVG file ready for print."
    )

    payload = {
        "image_request": {
            "prompt": prompt,
            "aspect_ratio": "ASPECT_1_1",
            "model": "V_2",
            "magic_prompt": "AUTO" 
        }
    }
    
    headers = {
        "Api-Key": IDEOGRAM_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                return data['data'][0]['url']
        else:
            print(f"Ideogram Error: {response.text}")
            
    except Exception as e:
        print(f"Fout bij verbinden met Ideogram: {e}")

    # Fallback
    return f"https://placehold.co/1024x1024/2563EB/FFFFFF/png?text={brand_name}"

# --- TEXT & PRODUCT TOOLS ---

def generate_product_description(product_name):
    """Schrijft een verkopende AIDA-beschrijving."""
    return call_llm("Je bent een expert copywriter.", f"Schrijf een conversie-gerichte productbeschrijving (NL) voor: {product_name}. Gebruik bullets.")

def generate_influencer_dm(product_name):
    """Schrijft een DM script voor influencer outreach."""
    return call_llm("Marketeer", f"Schrijf een korte, informele DM (NL) voor een influencer samenwerking voor: {product_name}.")

def find_real_winning_products(niche, filter_type="Viral"):
    """Zoekt viral productideeën met links naar onderzoek."""
    tiktok_url = f"https://www.tiktok.com/search?q={niche.replace(' ', '+')}+must+have"
    aliexpress_url = f"https://www.aliexpress.com/wholesale?SearchText={niche.replace(' ', '+')}"
    
    prompt = f"Geef 3 viral dropshipping producten voor de niche: {niche}. Output JSON: {{'suggestions': [{{'title': '...', 'hook': '...', 'price': '...'}}]}}"
    res = call_llm("Product Researcher", prompt, json_mode=True)
    
    results = []
    try:
        data = json.loads(res).get('suggestions', [])
        for item in data:
            item["search_links"] = {"tiktok": tiktok_url, "ali": aliexpress_url}
            results.append(item)
    except:
        results = [{"title": f"{niche} Concept", "hook": "Check de links hieronder.", "price": "29.95", "search_links": {"tiktok": tiktok_url, "ali": aliexpress_url}}]
    return results

def generate_viral_scripts(product, benefits, platform="TikTok"):
    """Maakt virale video scripts."""
    prompt = f"Maak een viral {platform} script voor {product}. Voordelen: {benefits}. Output JSON: {{'hooks': [], 'full_script': '', 'creator_brief': ''}}"
    res = call_llm("Viral Video Expert", prompt, json_mode=True)
    try: return json.loads(res)
    except: return {"hooks": ["Hook 1"], "full_script": "Script...", "creator_brief": "Brief..."}

def validate_feedback(text):
    """Checkt of feedback serieus is voor beloningen."""
    res = call_llm("Spam Filter. Antwoord alleen TRUE of FALSE.", f"Is dit serieuze feedback (meer dan 2 woorden): '{text}'?")
    return "TRUE" in str(res).upper()

def analyze_store_audit(store_data):
    """
    Geeft een conversie-audit op basis van gescrapte tekst.
    """
    prompt = f"""
    Je bent een E-commerce Conversion Rate Expert. Beoordeel deze webshop op basis van de tekst.
    
    Titel: {store_data['title']}
    Beschrijving: {store_data['description']}
    Homepage Tekst: {store_data['content']}
    
    Geef een kritisch rapport (Nederlands):
    1. Geef een cijfer (1-10) voor vertrouwen en duidelijkheid.
    2. Noem 3 sterke punten.
    3. Noem 3 kritische fouten of gemiste kansen (bijv. ontbrekende waardepropositie, vage teksten).
    4. Geef 1 "Golden Tip" om direct meer sales te krijgen.
    
    Houd het kort, krachtig en direct. Gebruik emojis.
    """
    return call_llm("Senior E-com Audit Specialist", prompt) or "AI Audit mislukt."