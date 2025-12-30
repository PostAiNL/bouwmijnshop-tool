import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta, timezone

# --- INIT SUPABASE ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except:
        return None

supabase = init_supabase()

# --- USER MANAGEMENT ---
def create_user(email, password, first_name):
    if not supabase: return "ERROR"
    try:
        res = supabase.table('users').select("*").eq('email', email).execute()
        if res.data: return "EXISTS"
        
        new_user = {
            "email": email,
            "password": password, 
            "first_name": first_name,
            "xp": 0,
            "level": 1,
            "is_pro": False,
            "referral_code": f"{first_name[:3].upper()}-{email[:2].upper()}"
        }
        supabase.table('users').insert(new_user).execute()
        return "SUCCESS"
    except:
        return "ERROR"

def verify_user(email, password):
    if not supabase: return False
    try:
        res = supabase.table('users').select("*").eq('email', email).eq('password', password).execute()
        return len(res.data) > 0
    except: return False

# --- WIZARD & BRAND IDENTITY ---
def update_onboarding_data(email, shop_name, income_goal, niche="Algemeen"):
    """Slaat de wizard gegevens permanent op inclusief niche voor AI Memory."""
    if not supabase: return False
    try:
        supabase.table('users').update({
            "shop_name": shop_name,
            "income_goal": income_goal,
            "niche": niche
        }).eq('email', email).execute()
        return True
    except: return False

def get_user_data(email):
    """Haalt extra data zoals shop_name en niche op."""
    if not supabase: return {}
    try:
        res = supabase.table('users').select("*").eq('email', email).execute()
        if res.data: return res.data[0]
    except: pass
    return {}

# --- PRO STATUS & REWARDS ---
def check_pro_status_db(email):
    if not supabase: return False
    try:
        res = supabase.table('users').select("is_pro, pro_expiry").eq('email', email).execute()
        if not res.data: return False
        
        user_data = res.data[0]
        if user_data.get('is_pro'): return True 
        
        if user_data.get('pro_expiry'):
            expiry = datetime.fromisoformat(user_data['pro_expiry'])
            if expiry.tzinfo is None: expiry = expiry.replace(tzinfo=timezone.utc)
            if expiry > datetime.now(timezone.utc): return True
        return False
    except: return False

def get_pro_expiry_date(email):
    """Haalt de vervaldatum van de PRO status op. (FIX VOOR CRASH)"""
    if not supabase: return None
    try:
        res = supabase.table('users').select("pro_expiry").eq('email', email).execute()
        if res.data and res.data[0]['pro_expiry']:
            return datetime.fromisoformat(res.data[0]['pro_expiry'])
    except: pass
    return None

# --- FEEDBACK ---
def save_feedback(email, message, is_valid):
    if not supabase: return False
    try:
        data = {"user_email": email, "message": message, "is_valid": is_valid, "created_at": datetime.now(timezone.utc).isoformat()}
        supabase.table('feedback').insert(data).execute()
        return True
    except: return False

def claim_feedback_reward(email):
    if not supabase: return "ERROR"
    try:
        res = supabase.table('users').select("feedback_reward_claimed").eq('email', email).execute()
        if res.data and res.data[0].get('feedback_reward_claimed'): return "ALREADY_CLAIMED"
        
        new_expiry = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        supabase.table('users').update({"pro_expiry": new_expiry, "feedback_reward_claimed": True}).eq('email', email).execute()
        return "SUCCESS"
    except: return "ERROR"

# --- FINANCIËN ---
def save_daily_stats(email, revenue, ad_spend, cogs):
    if not supabase: return False
    try:
        data = {"user_email": email, "revenue": revenue, "ad_spend": ad_spend, "cogs": cogs, "date": datetime.now().strftime("%Y-%m-%d")}
        supabase.table('daily_stats').insert(data).execute()
        return True
    except: return False

def get_daily_stats_history(email):
    if not supabase: return []
    try:
        res = supabase.table('daily_stats').select("*").eq('user_email', email).order('date', desc=True).limit(7).execute()
        return res.data
    except: return []