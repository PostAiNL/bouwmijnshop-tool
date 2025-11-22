import streamlit as st
import streamlit.components.v1 as components
import base64
from pathlib import Path

def inject_style_and_hacks(brand_color="#10b981"):
    st.markdown(f"""
    <style>
        /* ALGEMENE STIJL */
        .block-container {{ padding-top: 1rem; padding-bottom: 5rem; max-width: 800px; }}
        header[data-testid="stHeader"], [data-testid="stToolbar"], footer {{ display: none !important; }}
        
        /* KNOPPEN */
        div.stButton > button {{
            background: linear-gradient(135deg, {brand_color} 0%, #059669 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            padding: 14px 20px !important;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25) !important;
            transition: transform 0.1s;
        }}
        div.stButton > button:active {{ transform: scale(0.98); }}
        
        /* NICHE BAR */
        .niche-edit-bar {{
            background: #f0fdf4; border: 1px dashed #86efac; color: #166534;
            padding: 8px 12px; border-radius: 8px; font-size: 0.85rem;
            display: flex; align-items: center; gap: 8px; margin-bottom: 20px;
        }}

        /* LOCK OVERLAY STIJL (UPDATE: KLEINER & STRAKKER) */
        .lock-container {{
            position: relative;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #e5e7eb;
            margin-bottom: 1rem;
            background: #f9fafb;
            height: 220px; /* Vaste hoogte voor nette blur */
        }}
        
        /* De "Fake" content die geblured wordt */
        .blurred-content {{
            filter: blur(8px); /* Iets meer blur */
            opacity: 0.5;
            padding: 20px;
            pointer-events: none;
            user-select: none;
            height: 100%;
            background: white;
        }}
        
        /* Het slotje en de tekst - NU COMPACTER */
        .lock-overlay {{
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            width: 85%;
            max-width: 340px; /* Smaller gemaakt */
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(10px);
            padding: 20px 15px; /* Minder padding */
            border-radius: 14px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            border: 1px solid #f3f4f6;
            z-index: 10;
        }}
        
        .lock-title {{
            font-size: 1rem; font-weight: 800; color: #111827;
            margin-bottom: 6px; display: flex; align-items: center; justify-content: center; gap: 6px;
        }}
        
        .lock-desc {{
            font-size: 0.85rem; color: #4b5563; margin-bottom: 12px; line-height: 1.4;
        }}
        
        .trust-badges {{
            font-size: 0.7rem; color: #6b7280; margin-bottom: 12px;
            display: flex; flex-wrap: wrap; justify-content: center; gap: 6px;
        }}
        
        /* De Lemon Squeezy Knop */
        a.unlock-btn {{
            display: inline-block;
            background: #10b981;
            color: white !important;
            font-weight: 800;
            font-size: 0.9rem;
            text-decoration: none !important;
            padding: 10px 20px;
            border-radius: 8px;
            width: 100%;
            box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
            transition: transform 0.2s;
        }}
        a.unlock-btn:hover {{ transform: translateY(-2px); }}
        
    </style>
    """, unsafe_allow_html=True)

def render_header(is_pro=False, level=1):
    badge = "PRO" if is_pro else "DEMO"
    b_color = "#dcfce7" if is_pro else "#eff6ff"
    t_color = "#166534" if is_pro else "#1e40af"
    
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:15px;">
        <div style="width:48px; height:48px; background:#10b981; border-radius:12px; display:flex; align-items:center; justify-content:center; color:white; font-weight:900; font-size:1.5rem;">P</div>
        <div>
            <div style="display:flex; align-items:center; gap:8px;">
                <h1 style="margin:0; font-size:1.5rem; line-height:1.2;">PostAi</h1>
                <span style="background:{b_color}; color:{t_color}; padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:800; border:1px solid {b_color};">{badge}</span>
                <span style="background:linear-gradient(90deg, #f59e0b, #d97706); color:white; padding:2px 8px; border-radius:99px; font-size:0.75rem; font-weight:bold;">LVL {level}</span>
            </div>
            <p style="margin:0; color:#6b7280; font-size:0.85rem;">Jouw AI Social Media Manager</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_locked_section(feature_name, tease_text):
    """
    Toont een geblurde sectie. HTML is 'plat' gemaakt om weergavefouten te voorkomen.
    """
    buy_link = "https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2"
    
    # Let op: de HTML hieronder staat expres helemaal links tegen de kantlijn
    # om te voorkomen dat Streamlit het als 'code block' ziet.
    html_content = f"""
<div class="lock-container">
<div class="lock-overlay">
<div class="lock-title">🔒 {feature_name} is PRO</div>
<div class="lock-desc">{tease_text}</div>
<div class="trust-badges">
<span>🎁 14 dagen gratis</span> • 
<span>💎 20% korting bij jaar</span>
</div>
<a href="{buy_link}" target="_blank" class="unlock-btn">🔓 Ontgrendel PRO</a>
</div>
<div class="blurred-content">
<div style="margin-bottom:15px;">
<div style="height:15px; width:30%; background:#e5e7eb; border-radius:4px; margin-bottom:8px;"></div>
<div style="height:40px; width:100%; background:#f3f4f6; border:1px solid #e5e7eb; border-radius:10px;"></div>
</div>
<div style="margin-bottom:15px;">
<div style="height:15px; width:50%; background:#e5e7eb; border-radius:4px; margin-bottom:8px;"></div>
<div style="height:80px; width:100%; background:#f3f4f6; border:1px solid #e5e7eb; border-radius:10px;"></div>
</div>
</div>
</div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

def inject_chat_widget(server_url): 
    components.html(f"""<script>window.BMS_CHAT_SERVER="{server_url}";window.BMS_CHAT_CSS_URL="{server_url}/chat-widget.css";</script><script src="{server_url}/chat-widget.js"></script>""", height=0)