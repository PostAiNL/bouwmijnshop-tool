import streamlit as st
import os
import time
import uuid
from datetime import datetime, timedelta

PRO_KEY_FIXED = "123-456-789"

def init_session():
    """Initialiseert sessie-variabelen."""
    if "license_key" not in st.session_state:
        # Check URL param (als ze via email link komen)
        params = st.query_params
        url_license = params.get("license", None)
        st.session_state.license_key = url_license if url_license else None

    if "user_email" not in st.session_state: st.session_state.user_email = None
    if "demo_start_date" not in st.session_state: st.session_state.demo_start_date = None

def is_authenticated():
    """Checkt of gebruiker binnen mag (Demo of PRO)."""
    return st.session_state.license_key is not None

def is_pro():
    """Checkt of gebruiker PRO is."""
    key = st.session_state.license_key
    # 1. Hardcoded PRO key
    if key == PRO_KEY_FIXED:
        return True
    # 2. Check environment key (als je die gebruikt)
    env_key = os.getenv("PRO_LICENSE_KEY")
    if env_key and key == env_key:
        return True
    return False

def render_landing_page():
    """Toont de eerste pagina waar mensen hun naam/email invullen."""
    st.markdown("""
    <div style="text-align:center; margin-top:40px; margin-bottom:30px;">
        <h1 style="margin-bottom:10px;">Dagelijkse TikTok ideeën voor jouw niche.</h1>
        <p style="color:#64748b;">14 dagen gratis toegang. Geen kosten. Je kunt meteen starten.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("landing_form"):
        name = st.text_input("Naam")
        email = st.text_input("E-mailadres")
        submitted = st.form_submit_button("🚀 Start mijn gratis demo", use_container_width=True)

        if submitted:
            if "@" not in email:
                st.error("Vul een geldig e-mailadres in.")
            else:
                # Simuleer licentie aanmaak
                new_license = str(uuid.uuid4())[:8] # Korte demo code
                
                # Opslaan in sessie
                st.session_state.license_key = new_license
                st.session_state.user_email = email
                st.session_state.demo_start_date = datetime.now()
                
                # Simuleer email verzending (in productie gebruik je hier SMTP)
                st.toast(f"Demo code verstuurd naar {email}!", icon="📧")
                time.sleep(1)
                st.rerun()

def activate_pro(key):
    """Activeert PRO via instellingen."""
    if key == PRO_KEY_FIXED or key == os.getenv("PRO_LICENSE_KEY"):
        st.session_state.license_key = key
        st.toast("PRO Geactiveerd! Welkom.", icon="🎉")
        time.sleep(1)
        st.rerun()
        return True
    else:
        st.error("Ongeldige licentiesleutel.")
        return False
