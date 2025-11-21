import streamlit as st
import streamlit.components.v1 as components

def inject_style_and_hacks():
    """Laadt de styling die 100% matcht met de oude app."""
    st.markdown("""
    <style>
        /* Verberg standaard elementen */
        header[data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none !important; }
        .block-container { padding-top: 1rem; max-width: 1100px; }
        
        /* Sidebar fix */
        @media (max-width: 768px) { section[data-testid="stSidebar"] { display: none; } }

        /* KAART STIJLEN (Uit oude app) */
        .hero-card, .kpi-card {
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 16px;
            background: #ffffff;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            margin-bottom: 15px;
        }
        .kpi-label { color: #6b7280; font-size: 0.85rem; margin-bottom: 4px; }
        .kpi-value { font-size: 1.5rem; font-weight: 700; color: #111827; }
        
        /* PRO OVERLAY (Blur & Lock) */
        .ghost-wrapper { position: relative; margin-bottom: 20px; overflow: hidden; border-radius: 16px; border:1px solid #f3f4f6; }
        .ghost-content { filter: blur(6px); opacity: 0.6; pointer-events: none; user-select: none; padding: 20px; background: #fff;}
        .pro-lock-overlay {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: #ffffff; padding: 20px 25px; border-radius: 16px;
            box-shadow: 0 20px 40px -5px rgba(0,0,0,0.15);
            text-align: center; width: 90%; max-width: 450px; border: 1px solid #e5e7eb; z-index: 10;
        }
        .pro-btn {
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white !important; font-weight: 700; padding: 10px 24px;
            border-radius: 10px; text-decoration: none; display: inline-block; margin-top: 12px;
            box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3); border:0;
        }
        .pro-btn:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(34, 197, 94, 0.4); }

        /* TRUST BADGES */
        .trust-row { display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; font-size: 0.8rem; color: #6b7280; }
        .trust-pill { background: #f9fafb; border: 1px solid #e5e7eb; padding: 2px 10px; border-radius: 99px; display: flex; align-items: center; gap: 6px; }
        .trust-green { background: #ecfdf5; color: #166534; border-color: #bbf7d0; }
        .dot { width: 8px; height: 8px; background: #22c55e; border-radius: 50%; }
    </style>
    """, unsafe_allow_html=True)

def inject_chat_widget(server_url):
    """Injecteert de chatbot zodat hij altijd zichtbaar is."""
    html = f"""
    <script>
        window.BMS_CHAT_SERVER = "{server_url}";
        window.BMS_CHAT_CSS_URL = "{server_url}/chat-widget.css";
    </script>
    <script src="{server_url}/chat-widget.js"></script>
    """
    components.html(html, height=0)

def render_locked_section(title="Deze functie"):
    """Toont de PRO blokkade precies zoals in de screenshots."""
    st.markdown(f"""
    <div class="ghost-wrapper">
        <div class="pro-lock-overlay">
            <div style="font-size:1.4rem; margin-bottom:5px;">🔒 <strong>{title}</strong> is een PRO-functie</div>
            <p style="color:#4b5563; font-size:0.95rem; margin-bottom:10px;">
                Ontgrendel alle AI-tools, playbooks en exports.
            </p>
            <div style="font-size:0.85rem; color:#6b7280; margin-bottom:10px;">
                🎁 14 dagen gratis · 💎 20% korting bij jaar · 🪙 7 dagen geld terug
            </div>
            <a href="https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2" target="_blank" class="pro-btn">
                🔓 Ontgrendel PRO
            </a>
        </div>
        <div class="ghost-content">
            <h3>Voorbeeld weergave</h3>
            <div style="height:12px; background:#f3f4f6; width:40%; margin-bottom:10px; border-radius:4px;"></div>
            <div style="height:12px; background:#f3f4f6; width:80%; margin-bottom:10px; border-radius:4px;"></div>
            <div style="height:120px; background:#f3f4f6; width:100%; border-radius:12px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_trust_bar(confidence=95):
    import datetime
    nu = datetime.datetime.now().strftime("%d-%m %H:%M")
    st.markdown(f"""
    <div class="trust-row">
        <div class="trust-pill">🕒 Laatste update: {nu}</div>
        <div class="trust-pill">📂 Bron: Eigen Data</div>
        <div class="trust-pill trust-green"><div class="dot"></div> Vertrouwen in dit advies: {confidence}%</div>
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    st.markdown("<br><br><center style='color:#ccc; font-size:0.8rem'>© 2025 PostAi</center>", unsafe_allow_html=True)