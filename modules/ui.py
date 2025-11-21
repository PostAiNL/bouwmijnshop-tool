import streamlit as st
import streamlit.components.v1 as components

def inject_mobile_hacks():
    """Verbergt sidebar op mobiel en past padding aan."""
    st.markdown("""
        <style>
        @media (max-width: 768px) {
            section[data-testid="stSidebar"] {display: none;}
        }
        </style>
    """, unsafe_allow_html=True)

def inject_chat_widget(server_url):
    """Injecteert de Chat Widget (Sanne)."""
    # Let op: we gebruiken de bestanden die je hebt aangeleverd, 
    # maar laden ze via de externe server URL om CORS problemen te voorkomen.
    js_code = f"""
    <script>
        window.BMS_CHAT_SERVER = "{server_url}";
        window.BMS_CHAT_CSS_URL = "{server_url}/chat-widget.css";
        
        var script = document.createElement('script');
        script.src = "{server_url}/chat-widget.js";
        script.defer = true;
        document.head.appendChild(script);
        
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = "{server_url}/chat-widget.css";
        document.head.appendChild(link);
    </script>
    """
    components.html(js_code, height=0, width=0)

def show_pro_gate():
    """Toont een overlay wanneer iemand op een PRO feature klikt."""
    st.markdown("""
    <div class="pro-overlay">
        <h3>🔒 PRO Feature</h3>
        <p>Krijg onbeperkt AI scripts gebaseerd op jouw eigen data.</p>
        <a href="#" class="pro-cta-btn">Upgrade nu voor €19,95</a>
    </div>
    """, unsafe_allow_html=True)
    st.toast("Deze functie is alleen voor PRO leden.", icon="🔒")

def render_footer():
    st.markdown("---")
    st.markdown("<center style='color:#888;'>© 2025 PostAi - Made for Creators</center>", unsafe_allow_html=True)