import streamlit as st
import random
import string
import time
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client

# --- CONFIGURATIE ---
APP_URL = "https://rmacademy.onrender.com" 

RANKS = {
    0: "🐣 Starter",
    200: "🔨 Bouwer",
    500: "🚀 Expert",       
    1000: "👑 E-com Boss",
    3000: "💎 Legend",
    5000: "🔥 Master",
    10000: "🦄 Grandmaster"
}

# CONNECTIE MET SUPABASE
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except: return None

supabase = init_supabase()

# --- HULPFUNCTIE: BEPAAL RANG ---
def get_rank_info(xp):
    current_title = "🐣 Starter"
    next_xp = 200
    
    # Sorteer levels om de juiste huidige en volgende te vinden
    sorted_ranks = sorted(RANKS.items())
    
    for i, (threshold, title) in enumerate(sorted_ranks):
        if xp >= threshold:
            current_title = title
            # Volgende doel bepalen
            if i + 1 < len(sorted_ranks):
                next_xp = sorted_ranks[i+1][0]
            else:
                next_xp = threshold * 2 # Fallback als max level bereikt is
        else:
            break
            
    return current_title, next_xp

# --- DATA OPHALEN VOOR LEADERBOARD & TICKER ---
def get_leaderboard_data():
    """Haalt de top 10 users op uit Supabase."""
    if not supabase: return []
    try:
        response = supabase.table('users').select('email, first_name, xp, level, is_pro').order('xp', desc=True).limit(10).execute()
        data = response.data
        
        leaderboard = []
        for i, u in enumerate(data):
            if u.get('first_name'):
                display_name = u['first_name']
            else:
                email_parts = u['email'].split('@')
                name_part = email_parts[0].capitalize()
                domain_char = email_parts[1][0].upper() if len(email_parts) > 1 else "X"
                display_name = f"{name_part} {domain_char}."
            
            title, _ = get_rank_info(u['xp'])
            
            leaderboard.append({
                "rank": i + 1,
                "name": display_name,
                "xp": u['xp'],
                "title": title,
                "is_pro": u['is_pro']
            })
        return leaderboard
    except Exception as e:
        print(f"Leaderboard error: {e}")
        return []

# --- MAIL FUNCTIE 1: WELKOM ---
def send_welcome_email(to_email, referral_code, first_name="Ondernemer"):
    try:
        # Check of mail secrets bestaan
        if "email" not in st.secrets: return False
        
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
        smtp_user = st.secrets["email"]["smtp_user"]
        smtp_password = st.secrets["email"]["smtp_password"]
        sender_email = st.secrets["email"]["sender_email"]

        referral_link = f"{APP_URL}?ref_code={referral_code}"

        subject = "🚀 Welkom bij RM Ecom Academy - Start & Verdien"
        
        body = f"""
        <html>
          <body style="font-family: 'Helvetica', 'Arial', sans-serif; background-color: #f3f4f6; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <div style="background-color: #2563EB; padding: 30px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px;">RM Ecom Academy</h1>
                </div>
                <div style="padding: 40px 30px; color: #334155; line-height: 1.6;">
                    <h2 style="color: #0F172A; margin-top: 0;">Hi {first_name}! 🚀</h2>
                    <p>Je account is succesvol aangemaakt. Je kunt nu direct starten met de roadmap.</p>
                    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                    <h3 style="color: #0F172A;">💰 Verdien €250 per Student</h3>
                    <p>Jouw Vrienden Code:</p>
                    <div style="background: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px dashed #cbd5e1; text-align: center; margin-bottom: 20px;">
                        <span style="font-size: 24px; color: #2563EB; font-weight: 800; letter-spacing: 1px;">{referral_code}</span>
                    </div>
                    <a href="{referral_link}" style="display: block; background-color: #2563EB; color: #ffffff; text-decoration: none; text-align: center; padding: 12px; border-radius: 8px; font-weight: bold; margin-top: 10px;">
                        🔗 Kopieer Jouw Link
                    </a>
                </div>
                <div style="background-color: #f8fafc; padding: 20px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                    <p>&copy; 2024 RM Ecom Academy.</p>
                </div>
            </div>
          </body>
        </html>
        """

        msg = MIMEMultipart()
        msg['From'] = f"RM Ecom Academy <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Mail Fout: {e}")
        return False

# --- MAIL FUNCTIE 2: LEVEL UP ---
def send_levelup_email(to_email, first_name, new_rank):
    try:
        if "email" not in st.secrets: return False
        
        smtp_server = st.secrets["email"]["smtp_server"]
        smtp_port = st.secrets["email"]["smtp_port"]
        smtp_user = st.secrets["email"]["smtp_user"]
        smtp_password = st.secrets["email"]["smtp_password"]
        sender_email = st.secrets["email"]["sender_email"]

        subject = f"🏆 Gefeliciteerd {first_name}! Je bent nu een {new_rank}"
        
        body = f"""
        <html>
          <body style="font-family: 'Helvetica', 'Arial', sans-serif; background-color: #f3f4f6; margin: 0; padding: 0;">
            <div style="max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <div style="background-color: #10B981; padding: 30px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 24px;">LEVEL UP! 🚀</h1>
                </div>
                <div style="padding: 40px 30px; color: #334155; line-height: 1.6;">
                    <h2 style="color: #0F172A; margin-top: 0;">Lekker bezig, {first_name}!</h2>
                    <p>Je hebt hard gewerkt aan je webshop. Je bent zojuist gepromoveerd naar de rang:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <span style="font-size: 28px; font-weight: 800; color: #10B981; background: #ECFDF5; padding: 10px 20px; border-radius: 50px; border: 2px solid #10B981;">
                            {new_rank}
                        </span>
                    </div>

                    <p>Met deze rang heb je mogelijk nieuwe tools of functies ontgrendeld. Ga snel naar de app om te kijken.</p>
                    
                    <a href="{APP_URL}" style="display: block; background-color: #10B981; color: #ffffff; text-decoration: none; text-align: center; padding: 14px; border-radius: 8px; font-weight: bold; margin-top: 25px;">
                        👉 Ga naar Dashboard
                    </a>
                </div>
            </div>
          </body>
        </html>
        """

        msg = MIMEMultipart()
        msg['From'] = f"RM Ecom Academy <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"LevelMail Fout: {e}")
        return False

def generate_referral_code(name):
    prefix = name[:3].upper() if len(name) >=3 else "USER"
    suffix = ''.join(random.choices(string.digits, k=3))
    return f"{prefix}-{suffix}"

def login_or_register(email, license_input=None, ref_code_input=None, name_input=None):
    """Haalt gebruiker op uit sessie state, of haalt uit DB."""
    email = email.lower().strip()
    
    # Probeer gebruiker uit DB te halen
    user = None
    if supabase:
        try:
            res = supabase.table('users').select("*").eq('email', email).execute()
            if res.data: user = res.data[0]
        except: pass

    # Als gebruiker nog niet bestaat (zou via db.create_user moeten gaan, dit is fallback)
    if not user:
         st.session_state.user = {
            "id": "temp",
            "email": email,
            "first_name": name_input or "Gast",
            "xp": 0,
            "level": 1,
            "is_pro": False,
            "referral_code": "TEMP"
         }
         return

    # Sla op in sessie
    st.session_state.user = user
    st.session_state.is_pro = user.get('is_pro', False)
    
    # License activatie logica
    if license_input and not user.get('is_pro'):
        if license_input.startswith("PRO-"):
            if supabase:
                supabase.table('users').update({"is_pro": True, "license_key": license_input}).eq('id', user['id']).execute()
            st.session_state.user['is_pro'] = True
            st.session_state.is_pro = True
            st.balloons()

    st.toast("Succesvol ingelogd!", icon="🚀")

def get_progress():
    if "user" not in st.session_state or not supabase: return []
    try:
        # Als user ID 'temp' is (geen DB), return leeg
        if st.session_state.user['id'] == 'temp': return []
        
        res = supabase.table('progress').select("step_id").eq('user_id', st.session_state.user['id']).execute()
        return [r['step_id'] for r in res.data]
    except: return []

# --- PROGRESSIE MET AUTOMATISCHE LEVEL-UP MAIL ---
def mark_step_complete(step_id, xp_reward):
    # Als offline/temp user
    if "user" not in st.session_state: return
    if st.session_state.user['id'] == 'temp':
        st.session_state.user['xp'] += xp_reward
        st.toast(f"✅ Voltooid! +{xp_reward} XP (Demo Mode)", icon="🔥")
        return

    uid = st.session_state.user['id']
    if not supabase: return

    try:
        # Check of al gedaan
        check = supabase.table('progress').select('*').eq('user_id', uid).eq('step_id', step_id).execute()
        if check.data: return

        # Voeg toe aan progress
        supabase.table('progress').insert({"user_id": uid, "step_id": step_id}).execute()
        
        current_xp = st.session_state.user['xp']
        new_xp = current_xp + xp_reward
        update_data = {"xp": new_xp}
        
        old_title, _ = get_rank_info(current_xp)
        new_title, _ = get_rank_info(new_xp)
        
        # Check speciale unlocks
        if current_xp < 500 and new_xp >= 500:
            st.balloons()
            st.success("🔓 GEFELICITEERD! Je bent nu een Builder!")
            time.sleep(2)
        
        # Stuur mail bij promotie
        if new_title != old_title:
            st.toast(f"🆙 PROMOTIE! Je bent nu: {new_title}", icon="⭐")
            st.balloons()
            
            user_email = st.session_state.user.get('email')
            user_name = st.session_state.user.get('first_name') or "Topper"
            
            if user_email:
                send_levelup_email(user_email, user_name, new_title)
            
        supabase.table('users').update(update_data).eq('id', uid).execute()
        st.session_state.user['xp'] = new_xp
        #st.toast(f"✅ Voltooid! +{xp_reward} XP", icon="🔥")
             
    except Exception as e:
        print(f"Error marking complete: {e}")

def get_affiliate_stats():
    if "user" not in st.session_state or st.session_state.user['id'] == 'temp' or not supabase: 
        return 0, 0, 0
    
    uid = st.session_state.user['id']
    try:
        res = supabase.table('users').select("is_pro").eq('referred_by', uid).execute()
        total = len(res.data)
        pro = sum(1 for u in res.data if u['is_pro'])
        return total, pro, pro * 250
    except: return 0, 0, 0