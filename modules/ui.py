import streamlit as st
import streamlit.components.v1 as components

# --- STYLING & CSS ---
def inject_style_and_hacks():
    """Injecteert CSS voor de PRO-overlay, mobiele weergave en algemene styling."""
    st.markdown("""
    <style>
        /* Mobiele hacks */
        @media (max-width: 768px) {
            section[data-testid="stSidebar"] {display: none;}
        }
        footer {visibility: hidden;}

        /* PRO Ghost/Blur Styling */
        .ghost-wrap {
            position: relative;
            border: 1px solid #eef2f7;
            border-radius: 16px;
            background: #ffffff;
            padding: 14px;
            margin-bottom: 12px;
            overflow: hidden;
        }
        .ghost-blur-content {
            filter: blur(3px);
            opacity: 0.6;
            pointer-events: none;
            user-select: none;
        }
        
        /* Overlay Card */
        .pro-overlay-card {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 10;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            padding: 20px;
            width: 90%;
            max-width: 420px;
            text-align: center;
        }
        .pro-title { font-weight: 700; color: #111827; margin-bottom: 5px; font-size: 1.1rem; }
        .pro-desc { font-size: 0.9rem; color: #6b7280; margin-bottom: 15px; }
        .pro-badges { font-size: 0.8rem; color: #4b5563; margin-bottom: 15px; }
        .pro-btn {
            background: #22c55e; color: white !important; 
            padding: 10px 20px; border-radius: 10px; 
            text-decoration: none; font-weight: 700; display: inline-block;
        }
        .pro-btn:hover { opacity: 0.9; }

        /* Ghost Elementen */
        .g-bar { height: 40px; background: #f1f5f9; border-radius: 8px; margin-bottom: 10px; width: 100%; }
        .g-txt { height: 14px; background: #f1f5f9; border-radius: 4px; margin-bottom: 6px; width: 70%; }
        .g-row { display: flex; gap: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

def inject_chat_widget(server_url):
    """Injecteert de Chat Widget."""
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
    with st.sidebar:
        components.html(js_code, height=0, width=0)

def render_locked_section(feature_name="Deze functie"):
    """Toont de wazige achtergrond met de PRO overlay."""
    
    # HTML voor de 'Ghost' interface (nep content op de achtergrond)
    ghost_html = """
    <div class="ghost-wrap">
        <div class="ghost-blur-content">
            <div class="g-txt" style="width: 40%"></div>
            <div class="g-bar"></div>
            <div class="g-row">
                <div class="g-bar"></div>
                <div class="g-bar"></div>
            </div>
            <div class="g-txt" style="width: 60%"></div>
            <div class="g-bar" style="height: 100px"></div>
        </div>
        
        <div class="pro-overlay-card">
            <div class="pro-title">🔒 {name} is een PRO-functie</div>
            <div class="pro-desc">Ontgrendel alle AI-tools, playbooks en exports.</div>
            <div class="pro-badges">🎁 14 dagen gratis · 💎 20% korting bij jaar</div>
            <a href="https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2" target="_blank" class="pro-btn">
              🔓 Ontgrendel PRO
            </a>
        </div>
    </div>
    """.format(name=feature_name)
    
    st.markdown(ghost_html, unsafe_allow_html=True)

def render_footer():
    st.markdown("---")
    st.markdown("<center style='color:#888; font-size: 0.8rem;'>© 2025 PostAi - Made for Creators</center>", unsafe_allow_html=True)
