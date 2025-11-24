import random
import time
import pandas as pd
import urllib.parse
import datetime

# --- CHALLENGE / BOOTCAMP FUNCTIES ---
def get_challenge_tasks():
    return {
        1: "De 'Wie ben ik' (Introductie) - Geen verkoop, alleen connectie.",
        2: "Deel één specifieke fout die je veel ziet in jouw niche.",
        3: "Geef 1 super snelle tip (binnen 15 seconden).",
        4: "Reageer op een nieuwsbericht of trend in jouw markt.",
        5: "Laat zien waar je werkt (Behind the scenes).",
        6: "Beantwoord de meest gestelde vraag die je krijgt.",
        7: "De 'Mythe': Wat denkt iedereen dat waar is, maar is fout?",
        8: "Een persoonlijk verhaal: Waarom doe je wat je doet?",
        9: "How-to: Een simpele demonstratie van je skill/product.",
        10: "Klant spotlight: Deel een succesverhaal (anoniem mag).",
        11: "De 'Rant': Waar maak jij je boos over in jouw vakgebied?",
        12: "Gebruik een trending sound met tekstballonnen.",
        13: "Stel je kijkers een vraag (Engagement post).",
        14: "De Pitch: Nodig mensen uit voor je aanbod/nieuwsbrief."
    }

def get_daily_maintenance_task():
    day_idx = datetime.datetime.today().weekday()
    schedule = {
        0: {"type": "Educatie 🎓", "task": "Ontkracht een veelvoorkomende mythe in jouw niche."},
        1: {"type": "Behind the Scenes 🎥", "task": "Laat zien waar je mee bezig bent (vlog stijl)."},
        2: {"type": "Waarde 💡", "task": "Geef 1 snelle, direct toepasbare tip."},
        3: {"type": "Connectie 🤝", "task": "Deel een fout die je zelf ooit maakte (kwetsbaarheid)."},
        4: {"type": "Conversie 💰", "task": "Pitch je product of dienst op een subtiele manier."},
        5: {"type": "Viral/Bereik 🚀", "task": "Gebruik een trending sound of meme format."},
        6: {"type": "Community 💬", "task": "Stel een vraag of doe een Q&A."}
    }
    return schedule[day_idx]

def get_daily_pro_tip(day):
    tips = [
        "Zorg voor goed licht: ga voor een raam staan, niet ertegenin.",
        "Gebruik ondertiteling (Captions), veel mensen kijken zonder geluid.",
        "De eerste 3 seconden (de Hook) zijn 80% van het succes.",
        "Kijk in de lens, niet naar jezelf op het scherm.",
        "Houd het tempo hoog. Knip stiltes eruit.",
        "Gebruik trending audio op de achtergrond (zachtjes).",
        "Eindig altijd met een Call to Action (wat moet de kijker doen?).",
        "Reageer het eerste uur direct op comments voor het algoritme.",
        "Gebruik hashtags die specifiek zijn (niet alleen #fyp).",
        "Maak een loop: Zorg dat het einde overloopt in het begin.",
        "Varieer in camerahoeken om de aandacht vast te houden.",
        "Emotie wint van feiten. Laat zien hoe je je voelt.",
        "Wees niet bang om imperfect te zijn, dat wekt vertrouwen.",
        "Gefeliciteerd met dag 14! Analyseer nu je top 3 video's."
    ]
    if day > 14: return random.choice(tips)
    return tips[day-1] if 0 < day <= len(tips) else "Blijf consistent!"

# --- SCRIPT GENERATIE FUNCTIES ---
def generate_script(topic, format_type, tone, hook, cta, niche):
    time.sleep(1.5)
    visual_suggestion = get_visual_idea(format_type)
    
    return f"""
**🎬 Video Script: {topic}**
*Format: {format_type} | Toon: {tone}*

**🎵 Audio Strategie:**
Gebruik een sound met een duidelijke 'beat drop' of overgang.
👉 [Vind hier Trending Sounds op TikTok Creative Center](https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/pad/en)

**👁️ Visueel Idee:**
{visual_suggestion}

---
**HOOK (0-3 sec) + ACTIE:**
*(Actie: {get_hook_action(hook)})*
"{hook}"

**KERN (3-45 sec):**
"{topic} is iets waar veel mensen in de {niche} mee worstelen.
Hier is de waarheid: [Leg het kernpunt uit in 3 zinnen].
Bijvoorbeeld, als je kijkt naar... [Geef een voorbeeld].
Het geheim is eigenlijk simpel: doe minder X en meer Y."

**CTA (Einde):**
"{cta} als je meer wilt leren over {niche}!"

---
**📱 KLAAR VOOR DE POST:**
**Caption:**
{topic} 👇
Wist jij dit al? Veel mensen gaan hier de mist in. 
Sla deze video op voor later! 💾

#{niche.replace(" ", "")} #{niche.replace(" ", "")}tips #leertiktok #ondernemen #viral
"""

def generate_ai_image_url(topic, format_type, niche):
    try:
        prompt = f"TikTok content creation, {format_type} style, {niche} setting, topic {topic}, professional lighting, photorealistic, 4k"
        encoded_prompt = urllib.parse.quote(prompt)
        return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
    except: return None

def generate_challenge_script(day, task, niche, format_type):
    time.sleep(1.5)
    return f"""
**📅 Bootcamp Script Dag {day}**
*Opdracht: {task}*
*Niche: {niche}*

**🎵 Audio Tip:** Akoestische gitaar of rustige piano.

**HOOK (Met Actie):**
*(Leun langzaam in de lens)*
"Ik moet jullie iets eerlijks vertellen over {niche}..."

**BODY:**
(Vertel het verhaal gerelateerd aan de opdracht: '{task}')
"Ik zie vaak dat... maar eigenlijk..."

**CTA:**
"Herkenbaar? Laat het weten in de comments 👇"

---
**📋 Caption:**
Dag {day} van mijn challenge! 🔥
Vandaag heb ik het over {task}.
#{niche} #challenge #30dagen
"""

def generate_sales_script(product, pain, angle, niche):
    time.sleep(1.5)
    return f"""
**💰 Sales Script: {product}**
*Strategie: {angle}*

**HOOK (Met Actie):**
*(Hou je hand omhoog als stopteken)*
"Stop even met scrollen als je last hebt van {pain}."

**PROBLEEM:**
"Je kent het wel: je probeert {niche} te masteren, maar het lukt niet. Frustrerend, toch?"

**OPLOSSING ({product}):**
"Daarom heb ik {product} gemaakt. Het helpt je om binnen no-time van dat probleem af te komen."

**CTA:**
"Check de link in mijn bio om het te halen!"

---
**📋 Caption:**
Eindelijk de oplossing voor {pain}! 🙌
Check de link in bio. #{niche} #{product.replace(" ", "")}
"""

# --- HULP FUNCTIES ---
def get_visual_idea(format_type):
    if "Talking Head" in format_type: return "Jij pratend in de camera, telefoon op ooghoogte. Goed licht van voren."
    if "Green Screen" in format_type: return "Gebruik een screenshot van een nieuwsartikel of foute website als achtergrond."
    if "Vlog" in format_type: return "Snelle cuts van jou terwijl je bezig bent, met voice-over."
    if "Lijstje" in format_type: return "Wijs in de lucht waar de tekstballonnen verschijnen (op de beat van de muziek)."
    return "Hou het simpel en authentiek."

def get_viral_hooks_library(niche="jouw niche"):
    triggers = ["geheim", "fout", "hack", "waarheid", "leugen"]
    t = random.choice(triggers)
    dynamic_hooks = [
        f"Stop met scrollen als je van {niche} houdt...",
        f"De nr. 1 {t} die iedereen maakt bij {niche}...",
        f"Dit is waarom je {niche}-doelen nooit lukken...",
        f"Ik ga je een {t} verklappen over {niche}...",
        f"POV: Je hebt eindelijk {niche} begrepen...",
        f"3 {niche} tips die niemand deelt...",
        f"Geloof me, dit verandert alles voor {niche}...",
        f"Niemand praat hierover in de {niche} wereld...",
        f"Wist je dat deze {niche} hack bestaat?"
    ]
    return dynamic_hooks

def get_hook_action(hook_text):
    actions = [
        "Leun plotseling naar de camera",
        "Sla met je hand op tafel",
        "Zet je bril af (of doe iets met je haar)",
        "Begin met je rug naar de camera en draai om",
        "Hou een voorwerp uit je niche vast",
        "Kom van onderuit in beeld",
        "Loop naar de camera toe"
    ]
    return random.choice(actions)

def check_viral_potential(idea, niche):
    score = random.randint(60, 98)
    tips = ["Maak de hook scherper.", "Zorg voor betere belichting.", "Kort de video in.", "Gebruik een trending sound."]
    verdict = "Viraal potentieel! 🔥" if score > 80 else "Kan beter, maar prima start."
    return {"score": score, "verdict": verdict, "tip": random.choice(tips)}

def audit_script(script_text, niche):
    score = random.randint(50, 95)
    verdict = "Sterk script!" if score > 75 else "Mist wat urgentie."
    return {"score": score, "verdict": verdict}

# --- TOOLS FUNCTIES ---
def generate_digital_product_plan(niche, target):
    time.sleep(2)
    return f"""
**🚀 Masterplan voor {niche}**
**Doelgroep:** {target}

**1. Het Product Idee:**
"De Ultimate {niche} Starterkit" - Een combinatie van een E-book en 3 video-lessen.
*Prijs:* €27 - €47 (Impuls aankoop)

**2. De Inhoud:**
- Module 1: De basis van {niche} en veelgemaakte fouten.
- Module 2: Stap-voor-stap plan voor resultaat in 7 dagen.
- Bonus: Checklist & Templates.

**3. Marketing Hoek:**
Focus op "Tijdsbesparing" en "Gemak". Jouw doelgroep ({target}) heeft weinig tijd.
"""

def generate_series_ideas(topic, niche):
    return f"""
**📺 5-Delige Serie over: {topic}**

1. **De Intro:** Wat is {topic} en waarom is het belangrijk voor {niche}?
2. **De Fout:** Wat doen de meeste mensen fout bij {topic}?
3. **De Hack:** Een simpele truc om {topic} sneller te doen.
4. **De Case:** Hoe ik (of een klant) resultaat haalde met {topic}.
5. **De Q&A:** Ik beantwoord vragen uit de comments van deel 1-4.
"""

def steal_format_and_rewrite(other_script, my_topic, niche):
    return f"""
**🕵️ Herschreven Script (The 'Steal' Method)**

**Oorspronkelijk concept:** Iemand anders succesformule.
**Jouw Niche:** {niche}
**Jouw Onderwerp:** {my_topic}

---
**HOOK:**
"Ze zeiden dat {my_topic} onmogelijk was, maar kijk dit..."

**MIDDEN:**
"Vroeger dacht ik ook dat het moeilijk was. Maar toen ontdekte ik deze simpele aanpassing..."
(Vertel hier over {my_topic})

**EINDE:**
"Wil jij dit ook? Volg voor meer {niche} hacks!"
"""

def generate_weekly_plan(niche):
    return f"""
**📅 Jouw Content Week voor {niche}**

*   **Maandag:** Mythe ontkrachten (Educatie)
*   **Dinsdag:** Behind the scenes / Vlog (Connectie)
*   **Woensdag:** Snelle Tip / How-to (Waarde)
*   **Donderdag:** Throwback of Persoonlijk verhaal (Connectie)
*   **Vrijdag:** Sales / Aanbod (Conversie)
*   **Zaterdag:** Meme / Humor over {niche} (Bereik)
*   **Zondag:** Rust of Q&A sessie (Community)
"""

# --- DATA ANALYSE ---
def analyze_data_patterns(kpi_summary, niche):
    time.sleep(1)
    return {
        "strategy_tip": f"Ik zie dat je video's over {niche}-tips het goed doen in de avonduren. Probeer vaker rond 19:00 te posten en focus op korte 'how-to' video's."
    }

# --- BIO & LEADERBOARD ---
def generate_bio_options(current_bio, niche):
    time.sleep(1.5)
    return f"""
**✨ 3 Bio Opties voor {niche}**

**Optie 1 (De Expert):**
Helping {niche}s win 🏆
Tips voor [Resultaat] 📈
👇 Haal hier je gratis gids
[Link]

**Optie 2 (De Persoonlijke):**
Jouw favo {niche} expert 👋
Ik leer je alles over [Onderwerp]
Nieuwe video elke dag! 🎬
👇 Start hier
[Link]

**Optie 3 (Kort & Krachtig):**
📍 {niche} Tips & Tricks
🚀 Van 0 naar 10k volgers
⬇️ Check dit
[Link]
"""

def get_leaderboard(user_niche, current_xp):
    data = {
        "Rank": [1, 2, 3, 4, 5],
        "Naam": [f"{user_niche}King", f"Pro{user_niche}", "Jij (Nu)", f"Start{user_niche}", "MisterX"],
        "Week Views": ["150.2k", "89.5k", "---", "12.1k", "4.3k"],
        "XP": [5400, 3200, current_xp, 800, 450]
    }
    return pd.DataFrame(data)