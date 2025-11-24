import streamlit as st
import streamlit.components.v1 as components
import base64
import os

def get_img_as_base64(file_path):
    """Hulpfunctie om afbeelding naar base64 string om te zetten"""
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def inject_style_and_hacks(brand_color="#10b981"):
    st.markdown(f"""
    <style>
        /* ALGEMENE STIJL & THEMA FORCEREN */
        .stApp {{
            background-color: #ffffff;
            color: #111827;
        }}
        .block-container {{ padding-top: 1rem; padding-bottom: 5rem; max-width: 900px; }} 
        header[data-testid="stHeader"], [data-testid="stToolbar"], footer {{ display: none !important; }}
        
        /* INPUT VELDEN (Specifiek voor Mobiel/Leesbaarheid) */
        /* Forceer witte achtergrond en zwarte tekst voor alle inputs */
        div[data-baseweb="input"] > div, 
        div[data-baseweb="base-input"] > input, 
        div[data-baseweb="textarea"] > textarea,
        div[data-baseweb="select"] > div {{
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #e5e7eb !important;
        }}
        /* Zorg dat placeholder tekst ook leesbaar is (grijs) */
        ::placeholder {{
            color: #6b7280 !important;
            opacity: 1 !important;
        }}
        /* Dropdown menu items */
        ul[data-baseweb="menu"] {{
            background-color: #ffffff !important;
            color: #000000 !important;
        }}
        
        /* KNOPPEN */
        div.stButton > button {{
            background: linear-gradient(135deg, {brand_color} 0%, #059669 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            padding: 10px 20px !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25) !important;
            transition: transform 0.1s;
        }}
        div.stButton > button:active {{ transform: scale(0.98); }}
        
        /* NICHE BAR */
        .niche-edit-bar {{
            background: #f0fdf4; border: 1px dashed #86efac; color: #166534;
            padding: 6px 12px; border-radius: 8px; font-size: 0.8rem;
            display: flex; align-items: center; gap: 8px; margin-bottom: 15px;
        }}

        /* MINI CHALLENGE MAP (COMPACT) */
        .challenge-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 6px;
            margin-top: 10px;
        }}
        .day-box {{
            aspect-ratio: 1/1;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 6px;
            font-weight: bold;
            font-size: 0.75rem;
            cursor: default;
            height: 35px;
        }}
        .day-done {{ background: #10b981; color: white; border: 1px solid #10b981; }}
        .day-active {{ background: white; color: #10b981; border: 2px solid #10b981; font-size:0.9rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .day-locked {{ background: #f3f4f6; color: #d1d5db; border: 1px solid #e5e7eb; }}

        /* LOCK OVERLAY */
        .lock-container {{
            position: relative; border-radius: 12px; overflow: hidden;
            border: 1px solid #e5e7eb; margin-bottom: 1rem; background: #f9fafb; height: 200px;
        }}
        .blurred-content {{
            filter: blur(8px); opacity: 0.5; padding: 20px; pointer-events: none;
            user-select: none; height: 100%; background: white;
        }}
        .lock-overlay {{
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            width: 90%; max-width: 320px; background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(10px); padding: 15px; border-radius: 14px;
            text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            border: 1px solid #f3f4f6; z-index: 10;
        }}
        .lock-title {{ font-size: 0.95rem; font-weight: 800; color: #111827; margin-bottom: 4px; }}
        .lock-desc {{ font-size: 0.8rem; color: #4b5563; margin-bottom: 10px; line-height: 1.3; }}
        .trust-badges {{ font-size: 0.65rem; color: #6b7280; margin-bottom: 10px; display: flex; flex-wrap: wrap; justify-content: center; gap: 4px; }}
        a.unlock-btn {{
            display: inline-block; background: #10b981; color: white !important;
            font-weight: 800; font-size: 0.85rem; text-decoration: none !important;
            padding: 8px 16px; border-radius: 8px; width: 100%;
            box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2); transition: transform 0.2s;
        }}
        a.unlock-btn:hover {{ transform: translateY(-2px); }}
    </style>
    """, unsafe_allow_html=True)

def render_header(is_pro=False, level=1):
    badge = "PRO" if is_pro else "DEMO"
    b_color = "#dcfce7" if is_pro else "#eff6ff"
    t_color = "#166534" if is_pro else "#1e40af"
    
    # Logo logica
    logo_path = "assets/logo.png"
    img_b64 = get_img_as_base64(logo_path)
    
    if img_b64:
        # Als logo bestaat: toon afbeelding (max hoogte 50px)
        logo_html = f'<img src="data:image/png;base64,{img_b64}" style="height: 50px; width: auto; object-fit: contain;">'
    else:
        # Fallback als logo niet bestaat: De groene P
        logo_html = '<div style="width:40px; height:40px; background:#10b981; border-radius:10px; display:flex; align-items:center; justify-content:center; color:white; font-weight:900; font-size:1.2rem;">P</div>'

    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:15px; margin-bottom:15px;">
        {logo_html}
        <div>
            <div style="display:flex; align-items:center; gap:8px;">
                <h1 style="margin:0; font-size:1.4rem; line-height:1.2; font-weight: 800; color: #111827;">PostAi - Dé TikTokgroeier</h1>
                <span style="background:{b_color}; color:{t_color}; padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:800; border:1px solid {b_color}; letter-spacing: 0.5px;">{badge}</span>
            </div>
            <p style="margin:0; color:#6b7280; font-size:0.85rem;">Jouw AI Social Media Manager</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_locked_section(feature_name, tease_text):
    buy_link = "https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2"
    html_content = f"""
<div class="lock-container">
<div class="lock-overlay">
<div class="lock-title">🔒 {feature_name}</div>
<div class="lock-desc">{tease_text}</div>
<div class="trust-badges">
<span>🎁 14 dgn gratis</span> • 
<span>💎 20% korting/jr</span>
</div>
<a href="{buy_link}" target="_blank" class="unlock-btn">🔓 Ontgrendel</a>
</div>
<div class="blurred-content">
<div style="margin-bottom:15px;">
<div style="height:15px; width:30%; background:#e5e7eb; border-radius:4px; margin-bottom:8px;"></div>
<div style="height:40px; width:100%; background:#f3f4f6; border:1px solid #e5e7eb; border-radius:10px;"></div>
</div>
</div>
</div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

def render_challenge_map(current_day):
    """
    Compacte grid voor in de zijbalk/kolom.
    """
    html = '<div class="challenge-grid">'
    for i in range(1, 31):
        if i < current_day:
            c = "day-done"
            icon = "✓"
        elif i == current_day:
            c = "day-active"
            icon = str(i)
        else:
            c = "day-locked"
            icon = "🔒"
        
        html += f'<div class="day-box {c}">{icon}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def inject_chat_widget(server_url): 
    # Deze versie wacht netjes tot de pagina geladen is
    js_code = f"""
    <script>
        window.BMS_CHAT_SERVER = "{server_url}";
        window.BMS_CHAT_CSS_URL = "{server_url}/chat-widget.css";
        
        function loadWidget() {{
            var script = document.createElement('script');
            script.src = "{server_url}/chat-widget.js";
            script.defer = true;
            document.body.appendChild(script);
        }}

        if (document.readyState === 'loading') {{  
            document.addEventListener('DOMContentLoaded', loadWidget);
        }} else {{  
            loadWidget();
        }}
    </script>
    """
    components.html(js_code, height=0)