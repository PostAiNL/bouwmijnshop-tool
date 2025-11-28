import streamlit as st
import streamlit.components.v1 as components
import base64
import os

def get_img_as_base64(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def inject_style_and_hacks(brand_color="#10b981"):
    # 1. CSS STYLING
    css = f"""
    <style>
        /* --- MOBIELE FIXES & ALGEMENE RESET --- */
        * {{ -webkit-tap-highlight-color: transparent !important; }}
        
        .stApp {{ background-color: #f3f4f6 !important; color: #111827; }}
        .block-container {{ padding-top: 1rem; padding-bottom: 5rem; max-width: 900px; }} 
        header[data-testid="stHeader"], [data-testid="stToolbar"], footer {{ display: none !important; }}
        
        /* --- TEKST & LABELS --- */
        .stMarkdown, .stMarkdown p, label, .stRadio label, .stSelectbox label, .stTextInput label {{
            color: #374151 !important;
        }}
        div[data-baseweb="radio"] label {{
            color: #111827 !important;
        }}

        /* --- INPUTS & FORMULIEREN --- */
        div[data-baseweb="input"] > div, div[data-baseweb="base-input"] > input, 
        div[data-baseweb="textarea"] > textarea, div[data-baseweb="select"] > div {{
            background-color: #ffffff !important; 
            color: #000000 !important; 
            border: 1px solid #e5e7eb !important;
        }}
        
        /* --- NIEUWE MINIMALISTISCHE TABS --- */
        div[data-baseweb="tab-list"] {{
            background-color: transparent !important;
            border-bottom: 1px solid #e5e7eb !important;
            gap: 20px !important;
            padding-bottom: 0px !important;
        }}
        button[data-baseweb="tab"] {{
            background-color: transparent !important;
            border: none !important;
            padding-top: 0px !important;
            padding-bottom: 10px !important;
            margin: 0 !important;
        }}
        button[data-baseweb="tab"][aria-selected="false"] {{
            color: #9ca3af !important; 
        }}
        button[data-baseweb="tab"][aria-selected="false"]:hover {{
            color: {brand_color} !important; 
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {brand_color} !important;
            border-bottom: 3px solid {brand_color} !important;
            font-weight: 800 !important;
        }}

        /* --- EXPANDERS --- */
        div[data-testid="stExpander"] details > summary {{
            background-color: #ffffff !important;
            color: #111827 !important;
            border-radius: 8px !important;
            border: 1px solid #e5e7eb !important;
        }}
        div[data-testid="stExpander"] details > summary:hover {{
            color: {brand_color} !important;
        }}
        div[data-testid="stExpander"] details[open] > summary {{
            color: {brand_color} !important;
            border-bottom-left-radius: 0 !important;
            border-bottom-right-radius: 0 !important;
        }}
        div[data-testid="stExpander"] details > div {{
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            border-top: none !important;
            border-bottom-left-radius: 8px !important;
            border-bottom-right-radius: 8px !important;
            color: #374151 !important; 
        }}

        /* --- KNOPPEN STYLING --- */
        button[kind="primary"] {{
            background: linear-gradient(135deg, {brand_color} 0%, #059669 100%) !important;
            color: white !important; 
            border: none !important; 
            border-radius: 12px !important;
            font-weight: 700 !important; 
            padding: 12px 20px !important;
            box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2) !important;
            transition: all 0.2s ease;
        }}
        button[kind="primary"]:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(16, 185, 129, 0.3) !important;
        }}
        button[kind="primary"]:focus, button[kind="primary"]:active {{
            background: linear-gradient(135deg, {brand_color} 0%, #059669 100%) !important;
            color: white !important;
            border-color: transparent !important;
        }}

        button[kind="secondary"] {{
            background-color: #ffffff !important;
            color: #4b5563 !important;
            border: 1px solid #e5e7eb !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        }}
        button[kind="secondary"]:hover {{
            background-color: #f9fafb !important;
            color: #111827 !important;
            border-color: #d1d5db !important;
        }}
        
        div.stButton > button {{
            width: 100%; 
        }}

        /* --- HEADER --- */
        .header-container {{
            display: flex; align-items: center; gap: 20px; width: 100%; margin-bottom: 15px;
        }}
        .header-logo img {{ height: 50px; width: auto; border-radius: 12px; }}
        .header-text {{ flex-grow: 1; line-height: 1.2; }}
        .header-title {{ font-size: 1.4rem; font-weight: 800; color: #111827 !important; margin: 0; display: flex; align-items: center; }}
        .header-subtitle {{ font-size: 0.85rem; color: #6b7280 !important; margin: 0; margin-top: 4px; }}
        
        /* --- METRICS --- */
        .metrics-strip {{ display: flex; flex-direction: row; justify-content: space-between; gap: 10px; width: 100%; margin-bottom: 25px; margin-top: 15px; }}
        .metric-card {{
            flex: 1; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 12px 5px;
            text-align: center; display: flex; flex-direction: column; justify-content: center; align-items: center;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); min-width: 0; cursor: help; transition: transform 0.2s;
        }}
        .metric-card:hover {{ transform: translateY(-2px); border-color: {brand_color}; }}
        .metric-val {{ font-size: 1.6rem; font-weight: 900; line-height: 1.1; margin-bottom: 4px; white-space: nowrap; color: #111827; }}
        .metric-lbl {{ font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #6b7280 !important; white-space: nowrap; width: 100%; overflow: hidden; text-overflow: ellipsis; }}

        /* --- LOCK OVERLAY --- */
        .lock-wrapper {{
            position: relative; border-radius: 12px; overflow: hidden; border: 1px solid #e5e7eb; margin-bottom: 1rem; background: #ffffff; min-height: 300px; 
        }}
        .lock-content-blur {{
            filter: blur(6px); opacity: 0.5; padding: 20px; pointer-events: none; user-select: none; background: #f9fafb; height: 100%; min-height: 300px;
            display: flex; flex-direction: column; gap: 20px; justify-content: flex-start; 
        }}
        .fake-bar {{ height: 12px; background: #d1d5db; border-radius: 4px; width: 80%; }}
        .fake-box {{ height: 120px; background: #e5e7eb; border-radius: 8px; width: 100%; }}

        .lock-overlay {{
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: auto; min-width: 280px; max-width: 85%;
            background: rgba(255, 255, 255, 0.98); padding: 25px 20px; border-radius: 16px; text-align: center;
            border: 1px solid #e5e7eb; box-shadow: 0 15px 35px rgba(0,0,0,0.12); z-index: 10;
        }}
        .unlock-btn {{
            display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white !important;
            font-weight: 800; padding: 10px 20px; border-radius: 10px; text-decoration: none !important;
            margin-top: 10px; box-shadow: 0 4px 10px rgba(16, 185, 129, 0.3); transition: transform 0.2s;
        }}
        .unlock-btn:hover {{ transform: scale(1.02); }}

        /* TREND BOX */
        .trend-box {{
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: white !important; padding: 15px;
            border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3); position: relative; overflow: hidden;
        }}
        .trend-label {{ font-size: 0.7rem; text-transform: uppercase; font-weight: 800; opacity: 0.8; letter-spacing: 1px; }}
        .trend-title {{ font-size: 1.1rem; font-weight: 800; margin-top: 2px; }}

        /* FOOTER & NAV */
        .footer-container {{ text-align: center; margin-top: 10px; padding-top: 10px; width: 100%; }}
        .footer-text {{ font-size: 0.85rem; color: #6b7280; margin-bottom: 5px; }}
        .footer-sub {{ font-size: 0.75rem; color: #9ca3af; }}
        .nav-card {{ background: #ffffff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 15px; cursor: pointer; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); transition: 0.2s; }}
        .nav-card:hover {{ transform: translateY(-3px); border-color: {brand_color}; }}
        .nav-icon {{ font-size: 2.5rem; margin-bottom: 8px; }}
        .nav-title {{ font-weight: 800; color: #111827 !important; font-size: 1.1rem; }}
        .nav-desc {{ color: #6b7280 !important; font-size: 0.85rem; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

    # 2. JS HACK (AGRESSIEVE STYLING)
    # Hier zorgen we dat de Panic button ROOD wordt en de Trend button PAARS
    components.html("""
    <script>
        function styleButtons() {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(btn => {
                // RODE PANIC BUTTON
                if (btn.innerText.includes("Panic button")) {
                    btn.style.setProperty('background', 'linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)', 'important');
                    btn.style.setProperty('color', 'white', 'important');
                    btn.style.setProperty('border', '2px solid #fee2e2', 'important');
                    btn.style.setProperty('box-shadow', '0 4px 15px rgba(239, 68, 68, 0.4)', 'important');
                    btn.onmouseenter = function() { this.style.setProperty('transform', 'scale(1.02)', 'important'); };
                    btn.onmouseleave = function() { this.style.setProperty('transform', 'scale(1)', 'important'); };
                }
                // PAARSE TREND BUTTON
                if (btn.innerText.includes("Gebruik deze trend")) {
                    btn.style.setProperty('background', 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)', 'important');
                    btn.style.setProperty('color', 'white', 'important');
                    btn.style.setProperty('border', 'none', 'important');
                    btn.onmouseenter = function() { this.style.setProperty('opacity', '0.9', 'important'); this.style.setProperty('transform', 'translateY(-2px)', 'important'); };
                    btn.onmouseleave = function() { this.style.setProperty('opacity', '1', 'important'); this.style.setProperty('transform', 'translateY(0)', 'important'); };
                }
            });
        }
        styleButtons();
        setInterval(styleButtons, 500);
    </script>
    """, height=0, width=0)

def render_locked_section(feature_name, tease_text):
    buy_link = "https://www.paypro.nl/product/PostAi_PRO_-_Maandelijks/125181"
    st.markdown(f"""
    <div class="lock-wrapper">
        <div class="lock-overlay">
            <div style="font-size:1.5rem; margin-bottom:5px;">🔒</div>
            <div style="font-weight:800; font-size:1rem; color:#111827; margin-bottom:5px;">{feature_name}</div>
            <div style="font-size:0.8rem; color:#6b7280; margin-bottom:15px; line-height:1.4;">{tease_text}</div>
            <a href="{buy_link}" target="_blank" class="unlock-btn">🔓 Upgrade naar PRO</a>
            <div style="margin-top:12px; font-size:0.65rem; color:#9ca3af;">14 dagen gratis • Direct opzegbaar</div>
        </div>
        <div class="lock-content-blur">
            <div class="fake-bar"></div>
            <div class="fake-bar" style="width:60%"></div>
            <div class="fake-box"></div>
            <div class="fake-bar" style="width:90%"></div>
            <div class="fake-bar" style="width:40%"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def inject_chat_widget(server_url): pass