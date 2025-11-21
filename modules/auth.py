import streamlit as st
import os
import time

def check_license():
    """Checkt of de gebruiker PRO is."""
    # 1. Check sessie (gebruiker heeft net ingelogd)
    if st.session_state.get("is_pro_session", False):
        return True
        
    # 2. Check opgeslagen key (als we cookies zouden gebruiken)
    # Voor nu houden we het simpel bij de sessie
    return False

def activate_license(key_input):
    """Probeert een licentie te activeren."""
    real_key = os.getenv("PRO_LICENSE_KEY", "DEMO123")
    
    if key_input and key_input.strip() == real_key:
        st.session_state.is_pro_session = True
        st.success("✅ Licentie geactiveerd! Welkom bij PRO.")
        time.sleep(1)
        st.rerun() # <--- DIT zorgt voor de directe herlaadactie
        return True
    else:
        st.error("❌ Ongeldige licentiesleutel.")
        return False

def get_tiktok_auth_url():
    client_key = os.getenv("TIKTOK_CLIENT_KEY", "test")
    base_url = os.getenv("APP_PUBLIC_URL", "http://localhost:8501")
    return f"https://www.tiktok.com/v2/auth/authorize/?client_key={client_key}&response_type=code&scope=user.info.basic,video.list&redirect_uri={base_url}&state=123"
