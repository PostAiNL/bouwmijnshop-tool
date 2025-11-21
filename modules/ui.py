import streamlit as st
import streamlit.components.v1 as components

def inject_mobile_hacks():
    """Verbergt sidebar op mobiel en past padding aan."""
    st.markdown("""
        <style>
        @media (max-width: 768px) {
            section[data-testid="stSidebar"] {display: none;}
        }
        /* Zorgt dat de footer niet in de weg zit */
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

def inject_chat_widget(server_url):
    """Injecteert de Chat Widget (Sanne) via een iframe hack."""
    
    # We gebruiken height=700 zodat het chatvenster ruimte heeft om open te klappen
    # scrolling=False zorgt dat je geen lelijke scrollbalken in de app krijgt
    js_code = f"""
    <html>
    <head>
        <script>
            window.BMS_CHAT_SERVER = "{server_url}";
            window.BMS_CHAT_CSS_URL = "{server_url}/chat-widget.css";
        </script>
        <link rel="stylesheet" href="{server_url}/chat-widget.css">
    </head>
    <body style="background:transparent;">
        <script src="{server_url}/chat-widget.js"></script>
    </body>
    </html>
    """
    
    # We plaatsen dit in een container die over de content zweeft
    # Let op: in Streamlit is dit lastig perfect te krijgen, 
    # maar we zetten de height hoog genoeg zodat de chat open kan.
    with st.sidebar:
        # We verbergen dit component onderaan de sidebar, maar de fixed position css 
        # in de widget zelf zorgt dat hij rechtsonder komt.
        components.html(js_code, height=0, width=0)

def show_pro_gate():
    """Toont een overlay wanneer iemand op een PRO feature klikt."""
    st.markdown("""
    <div class="pro-overlay">
        <h3>🔒 PRO Feature</h3>
        <p>Krijg onbeperkt AI scripts gebaseerd op jouw eigen data.</p>
        <a href="https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2" target="_blank" class="pro-cta-btn">Upgrade nu voor €19,95</a>
    </div>
    """, unsafe_allow_html=True)
    st.toast("Deze functie is alleen voor PRO leden.", icon="🔒")

def render_footer():
    st.markdown("---")
    st.markdown("<center style='color:#888; font-size: 0.8rem;'>© 2025 PostAi - Made for Creators</center>", unsafe_allow_html=True)
