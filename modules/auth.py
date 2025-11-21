import streamlit as st
import os  # <--- Importeer os

def check_license():
    """Checkt of de gebruiker een PRO licentie heeft ingevuld."""
    license_key = st.session_state.get("license_key", "")
    # Hier gebruiken we os.getenv in plaats van st.secrets
    secret_key = os.getenv("PRO_LICENSE_KEY", "DEMO123")
    
    if license_key == secret_key:
        return True
    return False

def get_tiktok_auth_url():
    """Genereert de TikTok OAuth URL."""
    # Ook hier os.getenv gebruiken
    client_key = os.getenv("TIKTOK_CLIENT_KEY", "test_key")
    # APP_PUBLIC_URL is de naam die we in Render zagen staan
    base_url = os.getenv("APP_PUBLIC_URL", "http://localhost:8501")
    
    # Zorg dat er geen slash achter de URL blijft hangen
    redirect_uri = base_url.rstrip("/")
    
    return f"https://www.tiktok.com/v2/auth/authorize/?client_key={client_key}&response_type=code&scope=user.info.basic,video.list&redirect_uri={redirect_uri}&state=12345"