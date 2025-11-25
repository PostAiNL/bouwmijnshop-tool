import random
import time
import pandas as pd
import urllib.parse
import datetime

# --- TRENDS (Actueel/Pulse) ---
def get_weekly_trend():
    """Hardcoded 'Pulse' trend, elke week handmatig updaten voor 'Sticky-ness'"""
    return {
        "title": "De 'Wes Anderson' Stijl",
        "desc": "Symmetrische shots, statisch beeld, vrolijke muziek.",
        "sound": "Obituary - Alexandre Desplat",
        "action": "Film je dagelijkse routine alsof het een film is."
    }

# --- BRAND VOICE & DIRECTOR'S CUT ---
def generate_script(topic, format_type, tone, hook, cta, niche, brand_voice="Expert"):
    time.sleep(2) 
    
    sound = get_trending_sound_recommendation(tone)
    
    # Brand Voice aanpassingen
    voice_style = ""
    if brand_voice == "De Beste Vriendin 💖":
        voice_style = "Gebruik woorden als 'Lieve schat', 'Eerlijk', 'Girl/Boy math'."
    elif brand_voice == "De Harde Waarheid 🔥":
        voice_style = "Wees direct. Geen sugarcoating. 'Stop met dit te doen'."
    elif brand_voice == "De Grappenmaker 😂":
        voice_style = "Gebruik ironie en sarcasme."
    else:
        voice_style = "Professioneel maar toegankelijk."

    return f"""
**🎬 Video Script: {topic}**
*Format: {format_type} | Stijl: {brand_voice}*

**🎵 SOUND ADVIES:** [{sound['name']}]({sound['url']})

**🎥 DIRECTOR'S CUT (Regie):**
1.  **[0-3s]:** {get_hook_action(hook)} (Zoom in op gezicht).
2.  **[3-15s]:** Laat B-Roll zien van je werk/product terwijl je praat.
3.  **[Einde]:** Wijs fysiek naar de volg-knop of link in bio.

---
**HOOK:**
"{hook}"

**KERN ({voice_style}):**
"Ik zie zoveel {niche}-mensen de fout in gaan hiermee.
Het zit zo: [Leg uit in 2 zinnen].
Stop met moeilijk doen en probeer gewoon X."

**CTA:**
"{cta} als je klaar bent voor verandering!"
"""

# --- HOOK RATER ---
def rate_user_hook(user_hook, niche):
    time.sleep(1.5)
    length = len(user_hook.split())
    score = 0
    feedback = ""
    
    if length < 3: 
        score = 4
        feedback = "Te kort. Wees iets specifieker."
    elif length > 15:
        score = 5
        feedback = "Te lang. Mensen scrollen door. Kort het in."
    elif "je" in user_hook.lower() or "jouw" in user_hook.lower():
        score = 8
        feedback = "Goed! Je spreekt de kijker direct aan ('Je/Jouw')."
    elif "?" in user_hook:
        score = 7
        feedback = "Vragen werken goed, maar zorg dat het antwoord niet 'nee' is."
    else:
        score = 6
        feedback = "Prima start. Probeer er een 'Pattern Interrupt' in te doen (iets geks)."
        
    return {"score": score, "feedback": feedback}

# --- ICS EXPORT (Kalender) ---
def create_ics_file(niche):
    """Genereert een simpele ICS file content voor agenda import"""
    now = datetime.datetime.now()
    ics_content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//PostAi//NONSGML v1.0//EN\n"
    
    # Maak 5 events voor de week
    days = ["Maandag: Mythe", "Dinsdag: Vlog", "Woensdag: Tip", "Donderdag: Story", "Vrijdag: Sales"]
    for i, task in enumerate(days):
        dt_start = (now + datetime.timedelta(days=i+1)).strftime('%Y%m%dT090000')
        dt_end = (now + datetime.timedelta(days=i+1)).strftime('%Y%m%dT093000')
        ics_content += f"BEGIN:VEVENT\nDTSTART:{dt_start}\nDTEND:{dt_end}\nSUMMARY:PostAi - {task} ({niche})\nDESCRIPTION:Tijd om te filmen! Opdracht: {task}\nEND:VEVENT\n"
    
    ics_content += "END:VCALENDAR"
    return ics_content

# --- BESTAANDE FUNCTIES (Ongewijzigd) ---
def get_trending_sound_recommendation(tone):
    sounds = {
        "Energiek": [{"name": "Phonk Beat", "url": "#"}, {"name": "Speed Up", "url": "#"}],
        "Rustig": [{"name": "Acoustic", "url": "#"}, {"name": "LoFi", "url": "#"}],
        "Humor": [{"name": "Funny Fail", "url": "#"}, {"name": "Capybara", "url": "#"}],
        "Sales": [{"name": "Business BGM", "url": "#"}, {"name": "Success", "url": "#"}]
    }
    cat = sounds.get(tone, sounds["Energiek"])
    return random.choice(cat)

def get_challenge_tasks():
    return {1: "Introductie", 2: "Fout in niche", 3: "Snelle Tip", 4: "Trend reactie", 5: "Behind Scenes", 6: "Q&A", 7: "Mythe", 8: "Story", 9: "How-to", 10: "Klant", 11: "Rant", 12: "Sound", 13: "Vraag", 14: "Pitch"}

def generate_instant_script(niche):
    time.sleep(1)
    topic = random.choice(["Een misvatting", "Mijn tool", "Routine", "Hack"])
    return f"**🚨 NOOD SCRIPT: {topic}**\n\n**HOOK:** 'Ik moet dit kwijt...'\n**KERN:** 'Iedereen doet moeilijk over {topic}, maar het is simpel.'\n**CTA:** 'Wat vind jij?'"

def generate_ai_image_url(topic, format_type, niche):
    try:
        prompt = urllib.parse.quote(f"{niche} {topic} {format_type}")
        return f"https://image.pollinations.ai/prompt/{prompt}?width=1024&height=1024&nologo=true"
    except: return None

def generate_challenge_script(day, task, niche, format_type):
    time.sleep(1.5)
    return f"**📅 Bootcamp Dag {day}**\n*Opdracht: {task}*\n\n**HOOK:** 'Eerlijk verhaal...'\n**BODY:** (Vertel over {task})\n**CTA:** 'Herkenbaar?'"

def generate_sales_script(product, pain, angle, niche):
    time.sleep(1.5)
    return f"**🚀 Sales: {product}**\n\n**HOOK:** 'Stop met scrollen als je last hebt van {pain}.'\n**STORY:** 'Ik ken het gevoel...'\n**OPLOSSING:** '{product} helpt hiermee.'\n**CTA:** 'Link in bio!'"

def get_visual_idea(format_type):
    return "Jij pratend in camera, goed licht."

def get_viral_hooks_library(niche):
    return [f"Stop met scrollen voor {niche}...", f"De nr. 1 fout in {niche}...", f"3 {niche} tips..."]

def get_hook_action(hook_text):
    return random.choice(["Leun naar camera", "Sla op tafel", "Zet bril af"])

def check_viral_potential(idea, niche):
    score = random.randint(60, 98)
    return {"score": score, "verdict": "Viraal potentieel! 🔥" if score > 80 else "Kan beter."}

def generate_digital_product_plan(niche, target):
    time.sleep(2)
    return f"**Masterplan {niche}:** E-book voor {target}."

def generate_series_ideas(topic, niche):
    return f"**Serie {topic}:** 1. Intro, 2. Fout, 3. Hack, 4. Case, 5. Q&A"

def steal_format_and_rewrite(other, my_topic, niche):
    time.sleep(2)
    return f"**🕵️ REMIX:**\n**HOOK:** 'Ze liegen over {my_topic}...'\n**KERN:** 'Doe X ipv Y.'\n**CTA:** 'Volg voor meer!'"

def generate_weekly_plan(niche):
    return "**Weekplan:** Ma: Mythe, Di: Vlog, Wo: Tip, Do: Story, Vr: Sales, Za: Meme, Zo: Rust."

def generate_bio_options(bio, niche):
    return f"**Bio Optie:** 🏆 {niche} Expert | 🚀 Tips | 👇 Start hier"

def get_leaderboard(niche, xp):
    return pd.DataFrame({"Rank": [1,2,3], "Naam": ["Pro", "Jij", "Starter"], "XP": [5000, xp, 200]})