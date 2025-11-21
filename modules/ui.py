import streamlit as st
import streamlit.components.v1 as components

# --- STYLING & CSS ---
def inject_style_and_hacks():
    """Injecteert CSS voor de PRO-overlay, mobiele weergave en algemene styling."""
    st.markdown("""
    <style>
        /* 1. VERBERG STANDAARD ELEMENTEN */
        header[data-testid="stHeader"], [data-testid="stToolbar"], footer { display: none !important; }
        .block-container { padding-top: 1rem; max-width: 1100px; }

        /* 2. DESKTOP SIDEBAR: Vastzetten (Pijltje onzichtbaar maken maar wel aanwezig laten voor script) */
        [data-testid="stSidebarCollapsedControl"] { 
            visibility: hidden !important; 
            width: 0 !important;
            margin: 0 !important;
        }
        section[data-testid="stSidebar"] { min-width: 280px !important; }

        /* 3. MOBIEL: Sidebar weg & Padding fix */
        @media (max-width: 768px) {
            section[data-testid="stSidebar"] { display: none !important; }
            .block-container { padding-left: 1rem; padding-right: 1rem; }
        }

        /* 4. MOBIELE ONBOARDING */
        .mobile-onboarding-card {
            display: none; 
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

        /* 5. PRO & UI Styling */
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
        .pro-btn {
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

def force_sidebar_open():
    """Dwingt de sidebar open op Desktop via JavaScript."""
    components.html("""
    <script>
    (function() {
        const forceOpen = () => {
            // Alleen op desktop (breder dan 768px)
            if (window.parent.innerWidth <= 768) return; 
            
            const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
            const btn = window.parent.document.querySelector('[data-testid="stSidebarCollapsedControl"] button');
            
            // Als sidebar dicht is (aria-expanded=false), klik op de knop
            if (sidebar && sidebar.getAttribute('aria-expanded') === 'false' && btn) {
                btn.click();
            }
        };
        // Check direct en daarna elke 500ms
        forceOpen();
        setInterval(forceOpen, 500);
    })();
    </script>
    """, height=0, width=0)

def inject_chat_widget(server_url):
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

def render_mission_card(time, reason, hook):
    st.markdown(f"""
    <div class="hero-card" style="border:1px solid #bbf7d0; background:#f0fdf4;">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="background:#22c55e; color:white; width:30px; height:30px; border-radius:50%; display:flex; align-items:center; justify-content:center;">✓</div>
            <div>
                <h3 style="margin:0; font-size:1.1rem; color:#14532d;">Vandaag: 1 simpele TikTok taak</h3>
                <p style="margin:0; font-size:0.9rem; color:#166534;">Doe alleen deze stappen. Dan is vandaag goed.</p>
            </div>
        </div>
        <div style="margin-top:15px; padding-left:40px; font-size:0.95rem; color:#14532d;">
            <strong>Stap 1 - Tijd:</strong> Post vandaag 1 video rond <strong>{time}:00</strong> ({reason}).<br>
            <strong>Stap 2 - Hook:</strong> {hook}<br>
            <strong>Stap 3 - Check:</strong> Check morgen pas de views.
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_kpi_row(views, engagement, viral_score):
    st.markdown(f"""
    <div style="display:flex; gap:15px; margin-bottom:20px; flex-wrap:wrap;">
        <div class="kpi-card" style="flex:1; min-width:200px;">
            <div class="kpi-label">Weergaven (7d)</div>
            <div class="kpi-value">👁️ {views:,}</div>
            <div style="color:#16a34a; font-size:0.8rem; font-weight:600;">+12.5%</div>
        </div>
        <div class="kpi-card" style="flex:1; min-width:200px;">
            <div class="kpi-label">Gem. reactiescore</div>
            <div class="kpi-value">💬 {engagement}%</div>
            <div style="color:#16a34a; font-size:0.8rem; font-weight:600;">+2.1%</div>
        </div>
        <div class="kpi-card" style="flex:1; min-width:200px;">
            <div class="kpi-label">Virale score</div>
            <div class="kpi-value">🔥 {viral_score}/100</div>
            <div style="color:#16a34a; font-size:0.8rem; font-weight:600;">+5 ptn</div>
        </div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

def render_locked_section(title="Deze functie"):
    st.markdown(f"""
    <div class="ghost-wrapper">
        <div class="pro-lock-overlay">
            <div style="font-size:1.4rem; margin-bottom:5px;">🔒 <strong>{title}</strong> is een PRO-functie</div>
            <p style="color:#4b5563; font-size:0.95rem; margin-bottom:10px;">Ontgrendel alle AI-tools, playbooks en exports.</p>
            <div style="font-size:0.85rem; color:#6b7280; margin-bottom:10px;">🎁 14 dagen gratis · 💎 20% korting bij jaar</div>
            <a href="https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2" target="_blank" class="pro-btn">🔓 Ontgrendel PRO</a>
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

def render_mobile_onboarding():
    st.markdown("""
    <div class="mobile-onboarding-card">
        <h3 style="margin-top:0;">Start hier</h3>
        <p style="color:#666; font-size:0.9rem; margin-bottom:15px;">Kies hoe je PostAi wilt gebruiken op je telefoon.</p>
        <a href="?mobile_action=demo" target="_self" class="mob-btn mob-btn-primary">⚡ Gebruik demo-data</a>
        <div style="font-size:0.8rem; color:#999; margin-top:10px;">Voor eigen data: gebruik desktop.</div>
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