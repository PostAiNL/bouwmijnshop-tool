import streamlit as st
import streamlit.components.v1 as components

def inject_style_and_hacks():
    """Injecteert CSS voor de PRO-overlay, mobiele weergave en sidebar fixes."""
    st.markdown("""
    <style>
        /* 1. VERBERG STANDAARD ELEMENTEN */
        header[data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none !important; }
        .block-container { padding-top: 1rem; max-width: 1100px; }

        /* 2. DESKTOP SIDEBAR: Vastzetten (Pijltje weg) */
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        section[data-testid="stSidebar"] { min-width: 280px !important; }

        /* 3. MOBIEL: Sidebar weg & Padding fix */
        @media (max-width: 768px) {
            section[data-testid="stSidebar"] { display: none !important; }
            .block-container { padding-left: 1rem; padding-right: 1rem; }
        }

        /* 4. MOBIELE ONBOARDING (Alleen zichtbaar op klein scherm) */
        .mobile-onboarding-card {
            display: none; /* Standaard weg op desktop */
            background: #ffffff; border: 1px solid #e5e7eb; border-radius: 16px;
            padding: 20px; margin-bottom: 20px; text-align: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        }
        
        @media (max-width: 768px) {
            .mobile-onboarding-card { display: block !important; }
        }

        .mob-btn {
            display: block; width: 100%; padding: 12px; margin-bottom: 10px;
            border-radius: 10px; text-decoration: none; font-weight: 600; text-align: center;
            cursor: pointer; border: none;
        }
        .mob-btn-primary { background: #2563eb; color: white !important; }
        .mob-btn-secondary { background: #f1f5f9; color: #111827 !important; border: 1px solid #e5e7eb; }

        /* 5. PRO Gating & Cards (Oude Stijl) */
        .hero-card, .kpi-card {
            border: 1px solid #e5e7eb; border-radius: 16px; padding: 16px;
            background: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 15px;
        }
        .kpi-label { color: #6b7280; font-size: 0.85rem; margin-bottom: 4px; }
        .kpi-value { font-size: 1.5rem; font-weight: 700; color: #111827; }
        
        .ghost-wrapper { position: relative; margin-bottom: 20px; overflow: hidden; border-radius: 16px; border:1px solid #f3f4f6; }
        .ghost-content { filter: blur(6px); opacity: 0.6; pointer-events: none; user-select: none; padding: 20px; background: #fff;}
        .pro-lock-overlay {
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: #ffffff; padding: 20px 25px; border-radius: 16px;
            box-shadow: 0 20px 40px -5px rgba(0,0,0,0.15); text-align: center; width: 90%; max-width: 450px; border: 1px solid #e5e7eb; z-index: 10;
        }
        .pro-btn-lock {
            background: linear-gradient(135deg, #22c55e, #16a34a); color: white !important; font-weight: 700; padding: 10px 24px;
            border-radius: 10px; text-decoration: none; display: inline-block; margin-top: 12px;
        }

        /* Trust Bar */
        .trust-row { display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; font-size: 0.8rem; color: #6b7280; }
        .trust-pill { background: #f9fafb; border: 1px solid #e5e7eb; padding: 2px 10px; border-radius: 99px; display: flex; align-items: center; gap: 6px; }
        .trust-green { background: #ecfdf5; color: #166534; border-color: #bbf7d0; }
        .dot { width: 8px; height: 8px; background: #22c55e; border-radius: 50%; }
    </style>
    """, unsafe_allow_html=True)

def inject_chat_widget(server_url):
    html = f"""
    <script>
        window.BMS_CHAT_SERVER = "{server_url}";
        window.BMS_CHAT_CSS_URL = "{server_url}/chat-widget.css";
    </script>
    <script src="{server_url}/chat-widget.js"></script>
    """
    components.html(html, height=0)

def render_mobile_onboarding():
    """Toont speciale knoppen die ALLEEN op mobiel zichtbaar zijn (via CSS)."""
    
    # We gebruiken HTML buttons die de pagina herladen met een query param
    # Dit is de enige manier om het design 100% custom te krijgen buiten de Streamlit grid om.
    st.markdown("""
    <div class="mobile-onboarding-card">
        <h3 style="margin-top:0;">Start hier</h3>
        <p style="color:#666; font-size:0.9rem; margin-bottom:15px;">Kies hoe je PostAi wilt gebruiken op je telefoon.</p>
        
        <a href="?mobile_action=demo" target="_self" class="mob-btn mob-btn-primary">⚡ Gebruik demo-data</a>
        <!-- Upload kan helaas niet via simpele HTML link, dus we verwijzen naar de instellingen tab of tonen tekst -->
        <div style="font-size:0.8rem; color:#999; margin-top:10px;">
            Voor eigen data uploaden: gebruik een desktop of ga naar Instellingen.
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_locked_section(title="Deze functie"):
    st.markdown(f"""
    <div class="ghost-wrapper">
        <div class="pro-lock-overlay">
            <div style="font-size:1.4rem; margin-bottom:5px;">🔒 <strong>{title}</strong> is een PRO-functie</div>
            <p style="color:#4b5563; font-size:0.95rem; margin-bottom:10px;">Ontgrendel alle AI-tools, playbooks en exports.</p>
            <a href="https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2" target="_blank" class="pro-btn-lock">🔓 Ontgrendel PRO</a>
        </div>
        <div class="ghost-content">
            <h3>Voorbeeld</h3><div style="height:100px; background:#f3f4f6; width:100%; border-radius:12px;"></div>
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
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; color:#94a3b8; font-size:0.8rem;">
        <a href="?page=privacy" target="_self" style="color:#94a3b8; text-decoration:none;">Privacy</a> &nbsp; · &nbsp; 
        <a href="?page=terms" target="_self" style="color:#94a3b8; text-decoration:none;">Voorwaarden</a> &nbsp; · &nbsp; 
        🎁 14 dagen gratis
        <br><br>
        © 2025 PostAi
    </div>
    """, unsafe_allow_html=True)