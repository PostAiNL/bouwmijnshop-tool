import streamlit as st
import streamlit.components.v1 as components

def inject_style_and_hacks():
    """Laadt CSS."""
    try:
        with open("assets/styles.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        pass # Fallback als bestand mist

def inject_chat_widget(server_url):
    """Injecteert Chatbot."""
    # We gebruiken een iframe truc om hem over de app te leggen
    js_code = f"""
        <script>
            window.BMS_CHAT_SERVER = "{server_url}";
            window.BMS_CHAT_CSS_URL = "{server_url}/chat-widget.css";
        </script>
        <script src="{server_url}/chat-widget.js"></script>
    """
    # Injectie onderaan de body
    components.html(js_code, height=0)

def render_trust_bar(confidence=95):
    """Toont de balk met laatste update en vertrouwen."""
    import datetime
    nu = datetime.datetime.now().strftime("%d-%m %H:%M")
    
    st.markdown(f"""
    <div class="trust-bar">
        <div class="trust-badge">🕒 Laatste update: {nu}</div>
        <div class="trust-badge">📂 Bron: Eigen Data</div>
        <div class="trust-badge" style="background:#ecfdf5; color:#166534; border-color:#bbf7d0;">
            <div class="trust-dot"></div> Vertrouwen in dit advies: {confidence}%
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_kpi_row(views, engagement, viral_score):
    """Toont de 3 grote kaarten bovenaan."""
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">Weergaven (7d)</div>
            <div class="kpi-value">👁️ {views:,}</div>
            <div class="kpi-delta delta-pos">+12.5%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Gem. reactiescore</div>
            <div class="kpi-value">💬 {engagement}%</div>
            <div class="kpi-delta delta-pos">+2.1%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Virale score</div>
            <div class="kpi-value">🔥 {viral_score}/100</div>
            <div class="kpi-delta delta-pos">+5 ptn</div>
        </div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

def render_mission_card(time, reason, hook):
    """Toont de 'Vandaag' missie kaart."""
    st.markdown(f"""
    <div class="mission-card">
        <div class="mission-time-badge">Vandaag posten</div>
        <div class="mission-header">
            <div class="mission-icon">✅</div>
            <div>
                <h3 style="margin:0; font-size:1.1rem; color:#1e3a8a;">Vandaag: 1 simpele TikTok taak</h3>
                <p style="margin:0; color:#64748b; font-size:0.9rem;">Doe alleen deze stappen. Dan is vandaag goed.</p>
            </div>
        </div>
        <div style="margin-top:15px; padding-left:52px; color:#334155; line-height:1.6;">
            <strong>Stap 1 - Tijd:</strong><br>
            Post vandaag 1 video rond <strong>{time}:00</strong> ({reason}).<br><br>
            <strong>Stap 2 - Hook:</strong><br>
            "{hook}"
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_locked_section(title="Deze functie"):
    """Toont de wazige PRO blokkade."""
    st.markdown(f"""
    <div class="ghost-wrapper">
        <div class="pro-lock-overlay">
            <div style="font-size:1.5rem; margin-bottom:10px;">🔒</div>
            <h3 style="margin:0 0 5px 0; font-size:1.1rem;">{title} is een PRO-functie</h3>
            <p style="color:#666; font-size:0.9rem; margin-bottom:15px;">
                Ontgrendel alle AI-tools, playbooks en exports.
            </p>
            <div style="font-size:0.8rem; color:#888; margin-bottom:10px;">
                🎁 14 dagen gratis · 💎 20% korting bij jaar
            </div>
            <a href="https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2" target="_blank" class="pro-btn">
                ✨ Ontgrendel PRO
            </a>
        </div>
        <div class="ghost-content">
            <!-- Nep content voor de blur -->
            <h3>Analyse overzicht</h3>
            <p>Hier zouden gedetailleerde grafieken staan...</p>
            <div style="height:150px; background:#f1f5f9; border-radius:10px; margin-top:10px;"></div>
            <div style="height:40px; background:#f1f5f9; border-radius:5px; margin-top:10px; width:60%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; color:#94a3b8; font-size:0.8rem;">
        🛡️ Privacy-vriendelijk &nbsp; · &nbsp; 📄 CSV/XLSX &nbsp; · &nbsp; 🎁 14 dagen gratis
        <br><br>
        © 2025 PostAi - Made for Creators
    </div>
    """, unsafe_allow_html=True)
