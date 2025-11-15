# app.py — PostAi (TikTok Growth Agent) • PRO-ready + AI Coach/Generator/Chat
from __future__ import annotations

import os, re, io, json, uuid, base64, time, logging, urllib.parse
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Tuple
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import streamlit as st

# Nieuwe OpenAI SDK (>=1.0)
try:
    from openai import OpenAI
except ImportError:
    raise RuntimeError("Voeg 'openai>=1.0.0' toe aan requirements.txt")

# Key ophalen: eerst uit Streamlit secrets (lokaal), anders uit env (Render)
try:
    OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_KEY:
    st.warning("Voeg je OPENAI_API_KEY toe in Streamlit secrets of als Render environment variable.")
    client = None
else:
    client = OpenAI(api_key=OPENAI_KEY)


def ai_coach_reply(prompt: str) -> str:
    """Eenvoudige helper: stuur prompt naar OpenAI en krijg coach-antwoord terug."""
    if client is None:
        return "⚠️ Geen OPENAI_API_KEY gevonden."
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Je bent een nuchtere TikTok growth coach."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


# --------------------------------- Optioneel ---------------------------------
try:
    import altair as alt
    HAS_ALTAIR = True
except Exception:
    HAS_ALTAIR = False


# =============================== Basis / Config ===============================
APP_NAME = "PostAi — TikTok Growth Agent"
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "auto"
BRAND_DIR = APP_DIR / "branding"
DATA_DIR.mkdir(exist_ok=True)
BRAND_DIR.mkdir(exist_ok=True)

LATEST_FILE = DATA_DIR / "analytics_latest.csv"
SETTINGS_FILE = APP_DIR / "settings.json"
LICENSE_FILE = APP_DIR / "license.key"
ALERT_STATE_FILE = APP_DIR / "last_alert.txt"
SYNC_STATE_FILE = APP_DIR / "last_sync.txt"
POST_QUEUE_FILE = DATA_DIR / "post_queue.json"
COACH_STATE_FILE = DATA_DIR / "coach_state.json"

LEMON_CHECKOUT_URL = (
    "https://postai.lemonsqueezy.com/buy/fb9b229e-ff4a-4d3e-b3d3-a706ea6921a2"  # vervang
)

TZ = "Europe/Amsterdam"
REVIEW_MODE = os.getenv("REVIEW_MODE", "0").strip() == "1"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
log = logging.getLogger("postai")


def getconf(key: str, default: str = "") -> str:
    """Config ophalen uit Streamlit secrets of env var."""
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)


# ------------------------------- Dev helpers ---------------------------------
DEV_ALLOW_HTTP_LOCAL = True


def _is_local_url(url: str) -> bool:
    try:
        u = urlparse(url)
        return u.hostname in ("localhost", "127.0.0.1")
    except Exception:
        return False


def _get_public_base_url() -> str:
    url = getconf("APP_PUBLIC_URL", "").strip().rstrip("/")
    if not url:
        return ""
    if url.startswith("https://"):
        return url
    if DEV_ALLOW_HTTP_LOCAL and _is_local_url(url) and url.startswith("http://"):
        return url
    st.error(
        "Misconfiguratie: **APP_PUBLIC_URL** moet https zijn "
        "(of http://localhost bij lokaal testen)."
    )
    return ""


def has_oauth_config() -> bool:
    base = getconf("APP_PUBLIC_URL", "").strip()
    key = getconf("TIKTOK_CLIENT_KEY", "").strip()
    if not base or not key:
        return False
    if base.startswith("https://"):
        return True
    return DEV_ALLOW_HTTP_LOCAL and _is_local_url(base) and base.startswith("http://")


def build_tiktok_auth_url() -> str:
    client_key = getconf("TIKTOK_CLIENT_KEY", "").strip()
    scopes = getconf("TIKTOK_SCOPES", "user.info.basic").strip()
    base_url = _get_public_base_url()
    if not client_key or not base_url:
        return ""
    redirect_uri = f"{base_url}/"
    state = st.session_state.get("_tiktok_state") or uuid.uuid4().hex
    st.session_state["_tiktok_state"] = state
    params = {
        "client_key": client_key,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes,
        "state": state,
    }
    return (
        "https://www.tiktok.com/v2/auth/authorize/?"
        + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    )


# --------------------------- Licentie / PRO status ----------------------------
def _read_license() -> Tuple[str, bool]:
    """Lees licentie uit bestand. Geeft (key, is_pro). 'DEMO' is expliciet geen PRO."""
    try:
        if LICENSE_FILE.exists():
            key = LICENSE_FILE.read_text(encoding="utf-8").strip()
            if key:
                # 'DEMO' telt expliciet als géén PRO
                return key, key.upper() != "DEMO"
    except Exception:
        pass
    return "", False


def _write_license(key: str) -> bool:
    try:
        LICENSE_FILE.write_text(key.strip(), encoding="utf-8")
        st.session_state["LICENSE_KEY"] = key.strip()
        st.session_state["IS_PRO"] = (key.strip().upper() != "DEMO")
        return True
    except Exception:
        return False


def _remove_license() -> bool:
    try:
        if LICENSE_FILE.exists():
            LICENSE_FILE.unlink()
        st.session_state["LICENSE_KEY"] = ""
        st.session_state["IS_PRO"] = False
        return True
    except Exception:
        return False


def _init_license_state() -> None:
    """Init PRO/DEMO status één keer per sessie."""
    if "IS_PRO" in st.session_state and "LICENSE_KEY" in st.session_state:
        return  # al gedaan

    env_key = getconf("LICENSE_KEY", "").strip()
    if env_key:
        # Licentie via secrets/env → altijd PRO
        st.session_state["LICENSE_KEY"] = env_key
        st.session_state["IS_PRO"] = True
    else:
        file_key, is_pro_flag = _read_license()
        st.session_state["LICENSE_KEY"] = file_key
        st.session_state["IS_PRO"] = is_pro_flag


# ---- aanroepen bij start van de app + helpers ----
_init_license_state()

def is_pro() -> bool:
    return bool(st.session_state.get("IS_PRO", False))

def license_key() -> str:
    return st.session_state.get("LICENSE_KEY", "")

# ============================== Streamlit Setup ===============================
st.set_page_config(
    page_title=f"{APP_NAME} — {'PRO' if is_pro() else 'DEMO'}",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================== Simple routes (GEUPDATE) ======================
def _render_privacy():
    st.markdown(
        """
# Privacyverklaring — PostAi

PostAi gebruikt **alleen** TikTok-login om jouw **profielstatistieken** te bekijken.
We **slaan geen wachtwoorden** of privédata op en **posten niets namens jou**.

**Wat verzamelen we?**
- Basisprofiel (naam, avatar) via TikTok OAuth
- Geüploade CSV/XLSX die jij zelf aanlevert (blijft lokaal op de server van de app)

**Waarvoor gebruiken we dit?**
- Om je analytics te tonen en je best-tijden te berekenen
- Voor anonieme, geaggregeerde analyse ter verbetering van advies

**Wat bewaren we niet**
- Geen wachtwoorden of directe berichten
- Geen automatische posts zonder expliciete actie

**Bewaartermijn**
- Gegevens die je uploadt worden lokaal bewaard tot je ze wist via
  _Instellingen → Data opschonen (privacy)_.

**Je rechten**
- Je kunt op elk moment je data verwijderen via de knop “🧹 Verwijder lokale data”
  in **Instellingen**.

**Contact**
info@bouwmijnshop.nl
"""
    )


def _render_terms():
    st.markdown(
        """
# Algemene Voorwaarden — PostAi (TikTok Growth Agent)

**Versie:** 1.0 · **Laatst bijgewerkt:** 12-11-2025

## 1. Definities
- **PostAi**: de software waarin je analytics bekijkt en advies krijgt.
- **Gebruiker**: iedere natuurlijke of rechtspersoon die PostAi gebruikt.
- **PRO**: betaalde versie van PostAi.

## 2. Toepasselijkheid
Deze voorwaarden zijn van toepassing op elk gebruik van PostAi en op alle offertes, abonnementen en leveringen van diensten door ons.

## 3. Dienst & beperkingen
- PostAi toont analytics en geeft advies. **Geen automatische plaatsing** op TikTok zonder jouw actie.
- PostAi is **niet gelieerd** aan TikTok. Gebruik is onderworpen aan TikTok’s eigen voorwaarden.
- Demo-data en schattingen zijn indicatief; resultaten kunnen variëren.

## 4. Accounts & toegang
- Inloggen gebeurt via **TikTok OAuth**. Wij ontvangen basisprofielgegevens (zoals naam en avatar).
- Jij bent verantwoordelijk voor je account en voor bestanden die je uploadt.

## 5. Abonnementen & betalingen (PRO)
- Afhandeling via **Lemon Squeezy**. Prijs zoals in de app getoond.
- **Proefperiode**: 14 dagen gratis (indien van toepassing).
- **Opzegging**: kan op elk moment; stopt aan het einde van de lopende termijn.
- **Terugbetalingen**: geen restitutie voor reeds lopende termijnen, behalve waar wettelijk verplicht. We bieden een **7-dagen geld-terug** garantie op de **eerste** aankoop.

## 6. Gebruik/licentie
- Je krijgt een **niet-exclusieve, niet-overdraagbare** licentie om PostAi te gebruiken.
- Het is niet toegestaan de software te kopiëren, reverse-engineeren of door te verkopen.

## 7. Data & privacy
- We verwerken alleen de data die nodig is voor de dienst. Zie onze **[Privacyverklaring](?page=privacy)**.
- Je kunt via **Instellingen → Data opschonen** geüploade data verwijderen.

## 8. Fair use & limieten
- We hanteren redelijke limieten voor verzoeken/exports om misbruik te voorkomen.
- Bij misbruik kunnen we toegang beperken of beëindigen.

## 9. Aansprakelijkheid
- De dienst wordt geleverd “zoals hij is”. We garanderen geen specifiek bereik of resultaat.
- Onze totale aansprakelijkheid is beperkt tot het bedrag dat in de laatste 3 maanden aan abonnementskosten is betaald, voor zover wettelijk toegestaan.

## 10. Beëindiging
- We kunnen accounts (tijdelijk) blokkeren of beëindigen bij schending van deze voorwaarden of bij veiligheidsrisico’s.

## 11. Wijzigingen
- We mogen deze voorwaarden wijzigen. Bij materiële wijzigingen informeren we je via de app of per e-mail.

## 12. Toepasselijk recht
- Nederlands recht is van toepassing. Geschillen worden voorgelegd aan de bevoegde rechter te **Amsterdam**, tenzij dwingend recht anders bepaalt.

## 13. Contact
Vragen? **support@bouwmijnshop.nl**
"""
    )


def _render_404(slug: str):
    st.markdown(
        f"""
# Pagina niet gevonden
De pagina `?page={slug}` bestaat niet.

- Ga naar de **[startpagina](/)**  
- Of bekijk: **[Privacy](?page=privacy)** · **[Voorwaarden](?page=terms)**
"""
    )


def _route_simple_pages():
    # Werkt in nieuwe én oude Streamlit-versies
    try:
        page = st.query_params.get("page", "")
    except Exception:
        qp = st.experimental_get_query_params()
        page = (qp.get("page", [""]) or [""])[0]

    p = (page or "").lower().strip()
    if p == "privacy":
        _render_privacy()
        st.stop()
    if p in ("terms", "voorwaarden", "tos"):
        _render_terms()
        st.stop()
    if p not in ("", None):
        _render_404(p)
        st.stop()


# Roep de router aan vóór andere logica (zoals OAuth)
_route_simple_pages()

# ============================== Cookie/Consent ===============================
def _cookie_banner():
    # Toon de banner alleen als er nog geen keuze is gemaakt
    if st.session_state.get("consent") in ("accepted", "declined"):
        return

    with st.container(border=True):
        c1, c2 = st.columns([4, 2])
        with c1:
            st.markdown(
                "We gebruiken alleen functionele data (login/analytics). "
                "[Privacy](?page=privacy) · [Voorwaarden](?page=terms)"
            )
        with c2:
            a, b = st.columns(2)
            with a:
                if st.button("Accepteer", use_container_width=True, type="primary"):
                    st.session_state["consent"] = "accepted"
                    st.toast("Cookies/functional tracking geaccepteerd.")
                    st.rerun()
            with b:
                if st.button("Weiger", use_container_width=True):
                    st.session_state["consent"] = "declined"
                    st.toast("Functionele tracking geweigerd.")
                    st.rerun()


# Banner direct tonen
_cookie_banner()

# ============================== OAuth callback ===============================
qp = st.query_params
if "error" in qp:
    st.error(f"❌ TikTok OAuth error: {qp.get('error_description', qp.get('error'))}")
elif "code" in qp:
    state_ok = qp.get("state", "") == st.session_state.get("_tiktok_state")
    if REVIEW_MODE:
        st.success(f"✅ TikTok OAuth code ontvangen (state ok: {state_ok}).")
        st.session_state["tik_code"] = qp.get("code")
    else:
        st.success("✅ Ingelogd via TikTok.")
    st.session_state["tik_state_ok"] = state_ok

# ================================ Branding ===================================
def _load_branding():
    color = st.session_state.get("brand_color", "#2563eb")
    p = BRAND_DIR / "color.txt"
    if p.exists():
        try:
            color = p.read_text(encoding="utf-8").strip() or color
        except Exception:
            pass
    logo_path = BRAND_DIR / "logo.png"
    logo_bytes = logo_path.read_bytes() if logo_path.exists() else None
    return color, logo_bytes


def _save_brand_color(color_hex: str) -> bool:
    try:
        (BRAND_DIR / "color.txt").write_text(color_hex.strip(), encoding="utf-8")
        st.session_state["brand_color"] = color_hex.strip()
        return True
    except Exception:
        return False


def _save_brand_logo(file) -> bool:
    try:
        (BRAND_DIR / "logo.png").write_bytes(file.read())
        return True
    except Exception:
        return False


def _remove_brand_logo() -> bool:
    try:
        p = BRAND_DIR / "logo.png"
        if p.exists():
            p.unlink()
            return True
    except Exception:
        return False


THEME_COLOR, LOGO_BYTES = _load_branding()

# ================================== CSS ======================================
def _inject_css(theme_color: str, pro: bool):
    vars_block = f"""
:root {{
  --brand:{theme_color};
  --ring:#e8edf3; --muted:#4b5563; --head:#f8fafc;
  --card:#ffffff; --card-border:#eef2f7; --text:#111827; --bg:#ffffff;
  --hover:#f4f8ff; --track:#e5e7eb; --skeleton:#f1f5f9;
}}
"""

    base_css = """
html { color-scheme: light; -webkit-text-size-adjust: 100%; }
body, [data-testid="stAppViewContainer"] { background: var(--bg) !important; color: var(--text) !important; }
section[data-testid="stSidebar"] > div:first-child { background: var(--head); border-right:1px solid var(--card-border); }
.block-container { max-width:1200px; padding-top:14px; }
section[data-testid="stSidebar"] { width:260px !important; }

/* Sidebar altijd open: knop zichtbaar maar NIET klikbaar */
[data-testid="collapsedControl"] {
  pointer-events: none !important;
  opacity: 0.4;
}

/* Sidebar content iets omhoog zodat het gelijk valt met het logo */
section[data-testid="stSidebar"] .block-container { padding-top:1.5rem; }
.accent { color:var(--brand); }
h1,h2,h3 { letter-spacing:-.01em; color: var(--text); }

/* Header */
.app-header { margin-bottom:10px; }
.app-title-row {
  display:flex;
  align-items:center;
  gap:10px;
}
.app-title-row h1 {
  margin:0;
  font-size:1.6rem;
}
.app-pill {
  font-size:.8rem;
  padding:4px 10px;
  border-radius:999px;
  background:#dcfce7;
  border:1px solid #bbf7d0;
  color:#166534;
  font-weight:600;
}
.app-subtitle {
  margin:2px 0 0;
  font-size:.9rem;
  color:#6b7280;
}

/* Cards */
.hero-card, .kpi-card {
  border:1px solid var(--card-border);
  border-radius:16px;
  padding:14px 16px;
  background: var(--card);
  box-shadow:0 6px 18px rgba(0,0,0,.06);
  color: var(--text);
}
.kpi-label { color:var(--muted); font-size:.85rem; margin-bottom:4px; }
.kpi-value { font-size:1.35rem; font-weight:700; color: var(--text); }
.chip {
  display:inline-block;
  padding:4px 10px;
  border:1px solid var(--ring);
  border-radius:999px;
  margin-right:6px;
  margin-bottom:6px;
  font-size:.8rem;
  background: var(--card);
  color: var(--text);
}
.kpi-gap { margin-top:10px; margin-bottom:14px; }

/* Home mini-KPI's bovenin */
.home-mini-row{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin:10px 0 14px;
}
.home-mini{
  flex:1 1 0;
  border-radius:16px;
  border:1px solid var(--card-border);
  background:var(--head);
  padding:10px 12px;
  font-size:.85rem;
}
.home-mini-label{
  color:#6b7280;
  font-size:.75rem;
  margin-bottom:4px;
}
.home-mini-value{
  font-weight:700;
  font-size:1rem;
}

/* Today card rechts */
.today-card{
  border-radius:16px;
  border:1px solid var(--card-border);
  padding:14px 16px;
  background:#ecfdf5;
}
.today-title{
  font-weight:700;
  margin-bottom:4px;
}
.today-sub{
  color:#4b5563;
  font-size:.9rem;
}

/* Buttons – BASE (desktop & mobile) */
.stButton>button,
.stLinkButton>a {
  border-radius:12px !important;
  font-weight:700 !important;
  transition:transform .12s ease, box-shadow .12s ease, opacity .2s ease !important;
  -webkit-appearance:none !important; appearance:none !important;
  text-decoration:none !important; outline:none !important;
}
.stButton>button:hover,
.stLinkButton>a:hover { transform:translateY(-1px); box-shadow:0 6px 16px rgba(0,0,0,.06); }

/* Defaults (neutraal) wanneer geen custom class is gebruikt */
.stButton>button {
  background:var(--card) !important;
  color:var(--text) !important;
  border:1px solid var(--card-border) !important;
}
.stLinkButton>a {
  background:var(--brand) !important;
  color:#fff !important;
  border:1px solid var(--brand) !important;
}

/* Optionele varianten (als je ze gebruikt) */
.primary-btn>button {
  background:var(--brand) !important;
  color:#fff !important;
  border:1px solid var(--brand) !important;
}
.soft-btn>button {
  background:var(--card) !important;
  border:1px solid var(--ring) !important;
  color: var(--text) !important;
}

/* Inputs */
.stSelectbox div[role="combobox"],
.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stTextArea textarea {
  background: var(--card) !important;
  color: var(--text) !important;
  border:1px solid var(--card-border) !important;
  border-radius:12px !important;
}
label, .stCheckbox, .stRadio, .stMetric, .stMarkdown p {
  color: var(--text) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  position:sticky;
  top:0;
  z-index:5;
  background: var(--head);
  padding-top:6px;
  border-bottom:1px solid var(--card-border);
}

/* Progress / bars */
.stProgress > div > div { background: #ffffff !important; }
.stProgress > div {
  background: var(--track) !important;
  border-radius:8px;
}

/* Dataframes */
.stDataFrame, .stTable {
  background: var(--card) !important;
  color: var(--text) !important;
}
.dataframe td, .dataframe th { border-color: var(--card-border) !important; }

/* Confidence bar */
.nbabarshell {
  margin:8px 0;
  height:8px;
  background:var(--track);
  border-radius:8px;
  position:relative;
}
.nbabar {
  height:100%;
  background:#22c55e;
  border-radius:8px;
}
.nbalabel {
  position:absolute;
  right:8px;
  top:-18px;
  font-size:.8rem;
  color:#6b7280;
}

/* Skeleton */
.skeleton {
  position:relative;
  overflow:hidden;
  background:var(--skeleton);
  border-radius:14px;
  min-height:64px;
  border:1px solid var(--ring);
}
.skeleton::after {
  content:"";
  position:absolute;
  inset:0;
  background:linear-gradient(
    90deg,
    rgba(255,255,255,0) 0%,
    rgba(255,255,255,.25) 50%,
    rgba(255,255,255,0) 100%
  );
  transform:translateX(-100%);
  animation:shimmer 1.15s infinite;
}
@keyframes shimmer { 100% { transform:translateX(100%); } }

/* ===== Mobile ONLY (≤760px) ===== */
@media (max-width:760px){
  .block-container{ padding-left:12px; padding-right:12px; }
  .stButton>button, .stLinkButton>a{ width:100% !important; }
  .stButton>button, .stLinkButton>a{
      background:var(--brand) !important;
      color:#fff !important;
      border:1px solid var(--brand) !important;
  }
  .soft-btn>button{
      background:var(--card) !important;
      color:var(--text) !important;
      border:1px solid var(--ring) !important;
  }
  .stSelectbox div[role="combobox"],
  .stTextInput input,
  .stNumberInput input,
  .stDateInput input,
  .stTextArea textarea{
      font-size:14px !important;
  }
  .kpi-card{ padding:12px; border-radius:14px; }
  .kpi-value{ font-size:1.05rem; }
  .stTabs [data-baseweb="tab-list"]{ padding-top:4px; }
  .stTabs [data-baseweb="tab"]{ padding:8px 10px; font-size:13px; }
}
"""

    st.markdown("<style>" + vars_block + base_css + "</style>", unsafe_allow_html=True)

    # ❌ PRO-badge = VERWIJDERD
    # st.markdown(f"<div class='pro-badge'>{'PRO' if pro else 'DEMO'}</div>", unsafe_allow_html=True)


_inject_css(THEME_COLOR, is_pro())
import streamlit.components.v1 as components  # als dit al ergens staat, hoef je 'm niet nog eens te zetten

# Zorgt dat de sidebar bij laden altijd open staat
components.html(
    """
<script>
(function() {
  function ensureSidebarOpen() {
    try {
      const root = window.parent.document;
      const ctrl = root.querySelector('[data-testid="collapsedControl"]');
      if (!ctrl) return;
      const expanded = ctrl.getAttribute("aria-expanded");
      // Als hij dicht is, klik 'm open
      if (expanded === "false") {
        ctrl.click();
      }
    } catch (e) {}
  }
  // kleine delay zodat Streamlit klaar is
  setTimeout(ensureSidebarOpen, 300);
})();
</script>
""",
    height=0,
    width=0,
)

# ============================== Date helpers (FIX) ===========================
def _to_naive(series_like) -> pd.Series:
    """
    Forceer ALLE waarden naar tz-naive pandas datetime64[ns].
    Werkt ook bij gemixte inputs (strings, date, aware/naive).
    """
    s = pd.to_datetime(series_like, errors="coerce", utc=False)

    # Case A: hele Series heeft een tz (eenduidig tz-aware dtype)
    try:
        if getattr(s.dtype, "tz", None) is not None:
            return s.dt.tz_convert(None).astype("datetime64[ns]")
    except Exception:
        pass

    # Case B: gemixte objecten -> elementair strippen
    def _strip(v):
        if pd.isna(v):
            return pd.NaT
        try:
            t = pd.Timestamp(v)
            if t.tzinfo is not None:
                # harde strip
                return t.tz_convert(None).to_pydatetime().replace(tzinfo=None)
            return t.to_pydatetime().replace(tzinfo=None)
        except Exception:
            return pd.NaT

    return s.apply(_strip).astype("datetime64[ns]")

# ============================== Data Helpers ==============================
def _looks_like_xlsx(p: Path) -> bool:
    try:
        with open(p, "rb") as f:
            return f.read(4) == b"PK\x03\x04"
    except Exception:
        return False

@st.cache_data(show_spinner=False, ttl=600, hash_funcs={Path: lambda p: (p.stat().st_mtime, p.stat().st_size)})
def _smart_read_any(path_or_file) -> pd.DataFrame:
    try:
        if isinstance(path_or_file, (str, Path)):
            p = Path(path_or_file)
            if not p.exists() or p.stat().st_size == 0:
                return pd.DataFrame()
            if _looks_like_xlsx(p) or p.suffix.lower() == ".xlsx":
                return pd.read_excel(p)
            for args in (dict(sep=None, engine="python"), dict(sep=";"), dict()):
                try:
                    return pd.read_csv(p, **args)
                except Exception:
                    pass
            return pd.read_csv(p)
        else:
            name = getattr(path_or_file, "name", "").lower()
            if name.endswith(".xlsx"):
                return pd.read_excel(path_or_file)
            try:
                return pd.read_csv(path_or_file, sep=None, engine="python")
            except Exception:
                path_or_file.seek(0)
                return pd.read_csv(path_or_file)
    except Exception:
        return pd.DataFrame()

def _nk(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[^a-z0-9]", "", s)
    return s

def _pick(lower: dict, *keys):
    for k in keys:
        if k in lower:
            return lower[k]
    return None

def _to_int_safe(x):
    if pd.isna(x):
        return np.nan
    s = str(x).strip().lower()
    if s.endswith(("k", "m")):
        mul = 1000 if s.endswith("k") else 1_000_000
        s = s[:-1].replace(",", ".")
        try:
            return int(float(s) * mul)
        except Exception:
            return np.nan
    s = s.replace(".", "").replace(",", "")
    try:
        return int(float(s))
    except Exception:
        return np.nan

def _parse_nl_date(s):
    if pd.isna(s):
        return None
    txt = str(s).strip().lower().strip(" '\"\t\r\n,.;")
    months = {
        "januari": 1, "februari": 2, "maart": 3, "april": 4, "mei": 5, "juni": 6,
        "juli": 7, "augustus": 8, "september": 9, "oktober": 10, "november": 11, "december": 12
    }
    m = re.search(rf"(\d{{1,2}})\s*({'|'.join(months.keys())})", txt)
    if m:
        d, mon = int(m.group(1)), m.group(2)
        try:
            return date(datetime.now().year, months[mon], d)
        except Exception:
            pass
    try:
        return pd.to_datetime(txt, dayfirst=True, errors="coerce").date()
    except Exception:
        return None

def _is_tiktok_url(u: str) -> bool:
    u = str(u).strip().lower()
    return u.startswith("http") and "tiktok.com" in u

def _to_local(series_or_str):
    ts = pd.to_datetime(series_or_str, errors="coerce", utc=True)
    try:
        return ts.tz_convert(TZ)
    except Exception:
        return ts

def normalize_per_post(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    # kolommen herkennen
    lower = {_nk(c): c for c in df.columns}
    col = {
        "caption": _pick(lower, "videotitle", "videotitel", "caption", "tekst", "title", "titel", "omschrijving", "beschrijving"),
        "views":   _pick(lower, "totalviews", "views", "plays", "weergaven", "videoweergaven", "videoviews"),
        "likes":   _pick(lower, "totallikes", "likes", "hearts", "hartjes", "vindikleuks"),
        "comments":_pick(lower, "totalcomments", "comments", "reacties", "opmerkingen"),
        "shares":  _pick(lower, "totalshares", "shares", "gedeeld", "keergedeeld", "delen"),
        "date":    _pick(lower, "posttime", "time", "date", "datum", "createdat", "publicatiedatum", "gepubliceerddatum"),
        "link":    _pick(lower, "videolink", "videourl", "video link", "link", "url"),
        "videoid": _pick(lower, "videoid", "awemeid", "id"),
        "author":  _pick(lower, "author", "username", "account"),
    }

    d = df.copy()

    # Hashtags uit caption
    if col["caption"]:
        raw = d[col["caption"]].astype(str)
        d["Hashtags"] = raw.apply(lambda s: " ".join(re.findall(r"#\w+", s))).replace("", np.nan)
    else:
        d["Hashtags"] = np.nan

    # metrics naar int
    d["Views"]    = d[col["views"]].apply(_to_int_safe)    if col["views"]    else np.nan
    d["Likes"]    = d[col["likes"]].apply(_to_int_safe)    if col["likes"]    else np.nan
    d["Comments"] = d[col["comments"]].apply(_to_int_safe) if col["comments"] else np.nan
    d["Shares"]   = d[col["shares"]].apply(_to_int_safe)   if col["shares"]   else np.nan

    # DATUM — altijd tz-naive maken
    if col["date"]:
        raw_dates = d[col["date"]].astype(str).str.strip(" '\"\t\r\n,.;")

        # 1) grof parsen
        parsed = pd.to_datetime(raw_dates, dayfirst=True, errors="coerce")

        # 2) fallback NL-tekst
        parsed = parsed.where(
            parsed.notna(),
            pd.to_datetime(raw_dates.apply(_parse_nl_date), errors="coerce")
        )

        # 3) uniform: tz-naive
        parsed = _to_naive(parsed).astype("datetime64[ns]")

        # 4) posts zonder tijd → 12:00
        parsed = parsed.apply(
            lambda x: x.replace(hour=12) if pd.notna(x) and getattr(x, "hour", 0) == 0 else x
        )

        d["Datum"] = parsed
    else:
        d["Datum"] = pd.NaT

    # Video link
    d["Video link"] = ""
    if col["link"]:
        urls = d[col["link"]].astype(str)
        d["Video link"] = urls.where(urls.map(_is_tiktok_url), "")
    elif col["videoid"] and col["author"]:
        base = d[col["author"]].fillna("").astype(str).str.lstrip("@").str.strip()
        vid  = d[col["videoid"]].fillna("").astype(str).str.strip()
        d["Video link"] = "https://www.tiktok.com/@" + base + "/video/" + vid

    keep = ["Hashtags", "Video link", "Views", "Likes", "Comments", "Shares", "Datum"]
    return d[keep].copy()


def add_kpis(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    d = df.copy()
    for c in ["Views", "Likes", "Comments", "Shares"]:
        if c not in d.columns:
            d[c] = np.nan

    views    = pd.to_numeric(d["Views"], errors="coerce")
    likes    = pd.to_numeric(d["Likes"], errors="coerce")
    comments = pd.to_numeric(d["Comments"], errors="coerce")
    shares   = pd.to_numeric(d["Shares"], errors="coerce")

    denom = views.replace(0, np.nan)
    d["Like rate"]    = (likes    / denom).fillna(0.0)
    d["Comment rate"] = (comments / denom).fillna(0.0)
    d["Share rate"]   = (shares   / denom).fillna(0.0)
    d["Engagement %"] = d["Like rate"] + d["Comment rate"] + d["Share rate"]

    # --- TZ FIX: maak 'Datum' uniform tz-aware (UTC) en strip daarna tz => tz-naive
    ds = pd.to_datetime(d.get("Datum"), errors="coerce", utc=True)
    try:
        ds = ds.dt.tz_convert(None)      # strip timezone -> tz-naive
    except Exception:
        try:
            ds = ds.dt.tz_localize(None) # fallback
        except Exception:
            pass

    ds = pd.to_datetime(ds, errors="coerce")  # garandeer datetime64[ns]
    today = pd.Timestamp.now(tz="UTC").tz_convert(None).normalize()

    days = (today - ds).dt.days
    days = days.clip(lower=0).fillna(7).replace(0, 1)

    d["Velocity"] = (likes / days).fillna(0.0)
    d["Recency"]  = np.exp(-days / 90.0)

    def _mm(x: pd.Series) -> pd.Series:
        x = x.astype(float)
        mn, mx = np.nanmin(x), np.nanmax(x)
        if not np.isfinite(mn) or not np.isfinite(mx) or mx <= mn:
            return pd.Series(0.0, index=x.index)
        return (x - mn) / (mx - mn)

    score = (
        0.35 * _mm(views)
        + 0.25 * _mm(d["Engagement %"])
        + 0.15 * _mm(d["Share rate"])
        + 0.10 * _mm(d["Like rate"])
        + 0.10 * _mm(d["Velocity"])
        + 0.05 * d["Recency"]
    ).astype(float)

    d["Score"]    = score.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    d["Virality"] = (d["Score"] * 100).round(0)
    return d


@st.cache_data(show_spinner=False, ttl=600)
def trending_hashtags(d: pd.DataFrame, days_window: int = 14) -> pd.DataFrame:
    if d is None or d.empty:
        return pd.DataFrame()

    df = d.copy()
    df["Datum"] = _to_naive(df["Datum"])
    df = df.dropna(subset=["Datum"])
    if df.empty: return pd.DataFrame()

    last_date = df["Datum"].max().normalize()
    p2_start = last_date - pd.Timedelta(days=days_window - 1)
    p1_end   = p2_start - pd.Timedelta(days=1)
    p1_start = p1_end - pd.Timedelta(days=days_window - 1)

    tmp = df.assign(tag=df["Hashtags"].fillna("").str.split()).explode("tag")
    tmp = tmp[tmp["tag"].astype(str).str.startswith("#", na=False)]
    if tmp.empty: return pd.DataFrame()

    p1 = tmp[(tmp["Datum"]>=p1_start) & (tmp["Datum"]<=p1_end)]
    p2 = tmp[(tmp["Datum"]>=p2_start) & (tmp["Datum"]<=last_date)]

    g1 = p1.groupby("tag").agg(avg_views=("Views","mean"), cnt=("Views","count"))
    g2 = p2.groupby("tag").agg(avg_views=("Views","mean"), cnt=("Views","count"))

    out = g1.join(g2, how="outer", lsuffix="_prev", rsuffix="_curr").fillna(0)
    prev = pd.to_numeric(out["avg_views_prev"], errors="coerce").fillna(0.0)
    curr = pd.to_numeric(out["avg_views_curr"], errors="coerce").fillna(0.0)
    out["growth_%"] = np.where(prev>0, (curr-prev)/prev*100.0, 0.0)
    out = out[out["cnt_curr"] >= 3].sort_values(["growth_%","avg_views_curr","cnt_curr"], ascending=[False,False,False])
    return out

def _sparkline(series: pd.Series, width=120, height=28):
    if not HAS_ALTAIR: return None
    df_s = pd.DataFrame({"x": np.arange(len(series)), "y": pd.to_numeric(series, errors="coerce").fillna(method="ffill").fillna(0.0)})
    return alt.Chart(df_s).mark_line().encode(x="x:Q", y="y:Q").properties(width=width, height=height).configure_axis(disable=True)

def _best_hours(d: pd.DataFrame, n: int = 3) -> List[int]:
    if d is None or d.empty:
        return [19, 20, 18][:n]

    # Datum naar tz-naive
    dt = pd.to_datetime(d.get("Datum"), errors="coerce")
    try:
        dt = dt.dt.tz_convert(None)
    except Exception:
        try:
            dt = dt.dt.tz_localize(None)
        except Exception:
            pass
    dt = dt.astype("datetime64[ns]")

    v = pd.to_numeric(d.get("Views"), errors="coerce")
    v_cap = v.clip(upper=v.quantile(0.95))

    # 'today' als tz-naive middernacht
    try:
        today = pd.Timestamp.now("UTC").tz_convert(None).normalize()
    except Exception:
        today = pd.Timestamp.utcnow().tz_localize("UTC").tz_convert(None).normalize()

    base = dt.dt.normalize()
    days_ago = (today - base).dt.days.clip(lower=0).fillna(30)

    recent_w = np.exp(-(days_ago / 30.0))
    hrs = dt.dt.hour.fillna(12).astype(int)

    score = (v_cap * recent_w).groupby(hrs).median().sort_values(ascending=False)
    best = score.head(max(1, n)).index.tolist()
    return best or [19, 20, 18][:n]

def _should_sync_hourly() -> bool:
    try:
        if not SYNC_STATE_FILE.exists(): return True
        ts = float(SYNC_STATE_FILE.read_text().strip() or "0")
        return (datetime.utcnow().timestamp() - ts) > 3600
    except Exception: return True

def _mark_synced():
    try: SYNC_STATE_FILE.write_text(str(datetime.utcnow().timestamp()))
    except Exception: pass

def run_manual_fetch() -> dict:
    _mark_synced()
    if LATEST_FILE.exists(): return {"ok": True, "msg": "Gegevens ververst."}
    else: return {"ok": True, "msg": "Klaar. (Laad demo of upload CSV om data te zien.)"}

def _read_queue() -> List[dict]:
    try:
        if POST_QUEUE_FILE.exists(): return json.loads(POST_QUEUE_FILE.read_text(encoding="utf-8"))
    except Exception: pass
    return []

def _write_queue(items: List[dict]): POST_QUEUE_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")

def queue_post(caption: str, hashtags: str, hour: int):
    items = _read_queue()
    items.append({"id": uuid.uuid4().hex[:8], "caption": caption, "hashtags": hashtags, "hour": int(hour), "status": "pending"})
    _write_queue(items)

def approve_and_post(item_id: str) -> bool:
    items = _read_queue()
    for it in items:
        if it["id"] == item_id:
            it["status"] = "posted"; _write_queue(items); return True
    return False

def undo_post(item_id: str) -> bool:
    items = _read_queue()
    for it in items:
        if it["id"] == item_id and it["status"] == "posted":
            it["status"] = "pending"; _write_queue(items); return True
    return False

# =============================== I18N / Tekst ================================
def tr(k: str) -> str:
    I18N = dict(
        no_data="Nog geen data.",
        next_best="Vandaag: beste stap",
        review_queue="Wachtrij om te plaatsen",
        add_queue="Zet in wachtrij",
        trust1="Privacy-vriendelijk", trust2="CSV/XLSX", trust3="14 dagen gratis", trust4="Gemaakt voor TikTok",
    )
    return I18N.get(k, k)

# =============================== Header =======================================
c1, c2 = st.columns([1, 6])

with c1:
    if LOGO_BYTES:
        b64 = base64.b64encode(LOGO_BYTES).decode("ascii")
        st.markdown(
            f"<img src='data:image/png;base64,{b64}' style='height:64px;border-radius:16px;' />",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='height:64px;width:64px;border-radius:16px;"
            "background:linear-gradient(135deg,#22c55e,#16a34a);"
            "display:flex;align-items:center;justify-content:center;"
            "color:white;font-weight:700;font-size:20px;'>PA</div>",
            unsafe_allow_html=True,
        )

with c2:
    st.markdown(
        f"""
<div class="app-header">
  <div class="app-title-row">
    <h1><span class="accent">PostAi</span> — TikTok Growth Agent</h1>
        <span class="app-pill">{'PRO' if is_pro() else 'DEMO'}</span>
  </div>
  <p class="app-subtitle">Slimmer groeien met TikTok-data. Dare to know.</p>
</div>
""",
        unsafe_allow_html=True,
    )

# ============================ Demo-data helper ================================
def _activate_demo_data() -> None:
    """Genereer voorbeelddata en zet deze actief in de sessie."""
    rng = pd.date_range(end=pd.Timestamp.today().normalize(), periods=35, freq="D")
    np.random.seed(42)
    rows = []
    tags_pool = [
        "#darkfacts #psychology #fyp",
        "#love #lovestory #bf #bestie",
        "#viral #mindblown #creepy #tiktoknl",
        "#redthoughts #besties #bff #lovehim",
        "#deepthought #foryou #real #reels",
    ]
    for d_ in rng:
        views = np.random.randint(20_000, 500_000)
        likes = int(views * np.random.uniform(0.04, 0.18))
        comments = int(views * np.random.uniform(0.003, 0.02))
        shares = int(views * np.random.uniform(0.002, 0.015))
        d_ = d_ + pd.Timedelta(
            hours=int(
                np.random.choice(
                    [12, 14, 16, 18, 20, 0],
                    p=[0.25, 0.2, 0.18, 0.15, 0.12, 0.1],
                )
            )
        )
        rows.append(
            dict(
                caption=np.random.choice(tags_pool),
                views=views,
                likes=likes,
                comments=comments,
                shares=shares,
                date=d_,
                videolink="",
            )
        )
    df_demo = pd.DataFrame(rows)
    df_demo.to_csv(LATEST_FILE, index=False)
    st.session_state["df"] = df_demo
    st.session_state["demo_active"] = True
    st.toast("✅ Demo-data geactiveerd")

# ------------------------------ Sidebar -------------------------------
SHOW_SETUP_WARNINGS = st.session_state.get("show_setup_warnings", False)

# ============================= Sidebar styling =============================
st.markdown(
    """
    <style>
    /* =================== SIDEBAR LAYOUT =================== */

    /* Minder witruimte bovenin de sidebar */
    [data-testid="stSidebar"] {
        background: #f9fafb;
        border-right: 1px solid #e5e7eb;
        /* <<< HIER regel je hoe hoog alles begint */
        padding: 0.0rem 1.75rem 2.25rem !important;
    }

    /* Geen extra top-padding meer op inner containers */
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebar"] .block-container {
        padding-top: 0 !important;
    }

    /* --- PRO / DEMO pill --- */
    .sidebar-pro-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.2rem 0.75rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        background: #ecfdf5;
        color: #047857;
        border: 1px solid #a7f3d0;
        margin-bottom: 0.35rem;
    }

    .sidebar-pro-sub {
        font-size: 0.78rem;
        color: #6b7280;
        margin-bottom: 0.5rem;
    }

    /* --- Section titles & subtitels --- */
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text",
                     "Segoe UI", sans-serif;
        font-weight: 600;
        color: #111827;
        margin-bottom: 0.25rem;
    }

    [data-testid="stSidebar"] h3 {
        font-size: 0.9rem;
        margin-top: 0.4rem;
    }

    .sidebar-subtitle {
        font-size: 0.8rem;
        color: #6b7280;
        margin-bottom: 0.9rem;
    }

    .sidebar-section {
        margin-bottom: 1.8rem;
    }

    .sidebar-mini {
        font-size: 0.78rem;
        color: #6b7280;
        margin-top: 0.35rem;
    }

    /* --- Buttons (TikTok / data / upload) --- */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stLinkButton > button {
        width: 100%;
        border-radius: 999px;
        border: 1px solid #e5e7eb;
        background: #ffffff;
        color: #111827;
        font-weight: 500;
        font-size: 0.86rem;
        padding: 0.55rem 0.9rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        transition: all 0.15s ease-out;
    }

    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] .stLinkButton > button:hover {
        background: #f8fafc;
        border-color: #d1d5db;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.10);
    }

    [data-testid="stSidebar"] .stButton > button:active,
    [data-testid="stSidebar"] .stLinkButton > button:active {
        transform: translateY(0);
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08);
    }

    /* Icoon + tekst in button netjes gecentreerd */
    [data-testid="stSidebar"] .stButton > button div,
    [data-testid="stSidebar"] .stLinkButton > button div {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }

    /* File uploader titel kleiner & subtieler */
    [data-testid="stSidebar"] .uploadedFile {
        font-size: 0.8rem;
    }
    [data-testid="stSidebar"] label {
        font-size: 0.8rem;
        color: #6b7280;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    # PRO / DEMO-status
    if is_pro():
        st.markdown(
            "<div class='sidebar-pro-pill'>✅ PRO geactiveerd</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='sidebar-pro-sub'>Alle functies beschikbaar.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='sidebar-pro-pill'>🧪 DEMO-modus</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='sidebar-pro-sub'>Je draait nu in demo. Upgrade voor alle PRO-functies.</div>",
            unsafe_allow_html=True,
        )

    # Koppel TikTok
    st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    st.markdown("### Koppel TikTok")
    st.markdown(
        "<div class='sidebar-subtitle'>Verbind je account één keer.</div>",
        unsafe_allow_html=True,
    )

    login_url = build_tiktok_auth_url()
    if login_url:
        st.link_button("Log in met TikTok", login_url, use_container_width=True)
        st.markdown(
            "<div class='sidebar-mini'>Beschikbaar zodra TikTok onze app heeft goedgekeurd.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.button("Log in met TikTok", disabled=True, use_container_width=True)
        st.markdown(
            "<div class='sidebar-mini'>TikTok beoordeelt onze app, binnenkort kun je inloggen!</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Data
    st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    st.markdown("### Data")
    st.markdown(
        "<div class='sidebar-subtitle'>Kies een bron voor je advies.</div>",
        unsafe_allow_html=True,
    )

    if st.button("📊 Analytics ophalen"):
        res = run_manual_fetch()
        st.toast(res["msg"] if res["ok"] else f"❌ {res['msg']}")

    if st.button("⚡ Demo-data gebruiken"):
        _activate_demo_data()

    if st.session_state.get("df") is not None:
        st.markdown(
            "<div class='sidebar-mini'>Data: ✓ klaar voor advies.</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Upload
    st.markdown("<div class='sidebar-section'>", unsafe_allow_html=True)
    st.markdown("### Upload (optioneel)")
    st.markdown(
        "<div class='sidebar-subtitle'>TikTok-export in CSV/XLSX.</div>",
        unsafe_allow_html=True,
    )

    up = st.file_uploader("Drag and drop hier", type=["csv", "xlsx"])
    # (je upload-logica hier…)
    st.markdown("</div>", unsafe_allow_html=True)

# ============================= Onboarding bar ================================
def _onboarding_bar(step: int):
    """Eenvoudige, rustige voortgangsbalk voor starters (stap 0–5)."""
    labels = ["Data", "Check", "A/B-test", "Plan", "Resultaat"]
    filled = min(step, len(labels))
    frac = filled / len(labels)

    step_labels = [
        ("✅ " + label) if i < filled else label
        for i, label in enumerate(labels)
    ]

    st.progress(frac, text=" ➜ ".join(step_labels))

# =============================== Data load ===================================
if "df" not in st.session_state:
    st.session_state["df"] = _smart_read_any(LATEST_FILE)
df_raw = st.session_state.get("df", pd.DataFrame())

if _should_sync_hourly():
    _ = run_manual_fetch()
    if "df" not in st.session_state or st.session_state["df"].empty:
        st.session_state["df"] = _smart_read_any(LATEST_FILE); df_raw = st.session_state["df"]

# ================================ KPI helpers ================================
def _fmt_delta(curr, prev):
    try:
        if prev is None or not np.isfinite(prev) or prev == 0:
            return "—", None
        diff = ((curr - prev) / prev) * 100
        return f"{diff:+.1f}%", ("↑" if diff >= 0 else "↓")
    except Exception:
        return "—", None


def _kpi_row(d: pd.DataFrame, key_ns: str = "top"):
    """Compacte KPI-rij in dezelfde premium stijl als de rest van de app."""
    # Klein beetje verticale ruimte boven de rij
    st.markdown("<div class='kpi-gap'></div>", unsafe_allow_html=True)

    if d is None or d.empty:
        # Skeleton-state: drie placeholders zodat de layout gelijk blijft
        c1, c2, c3 = st.columns(3)
        for col in (c1, c2, c3):
            col.markdown("<div class='skeleton'></div>", unsafe_allow_html=True)
        return

    # -------- Periode-selector (compact aan rechterkant) --------
    period_options = [7, 14, 28]
    kpi_left, kpi_right = st.columns([4, 1])

    with kpi_right:
        st.caption("Periode")
        sel = st.selectbox(
            "Periode",
            period_options,
            index=0,
            key=f"kpi_range_{key_ns}",
            label_visibility="collapsed",
            help="Hoeveel dagen wil je vergelijken?",
        )

    with kpi_left:
        # 1) Datum uniform tz-naive datetime64[ns]
        dt = _to_naive(d["Datum"]).astype("datetime64[ns]")

        # 2) Grenzen ook als np.datetime64 — gebaseerd op lokale tijdzone
        now_ts = pd.Timestamp.now(tz=TZ).tz_convert(None).normalize()
        cur_start = np.datetime64(now_ts - pd.Timedelta(days=sel))
        cur_end = np.datetime64(now_ts + pd.Timedelta(days=1))  # half-open

        prev_end = np.datetime64(now_ts - pd.Timedelta(days=sel))
        prev_start = np.datetime64(now_ts - pd.Timedelta(days=2 * sel))

        # 3) Masks
        cur_mask = (dt >= cur_start) & (dt < cur_end)
        prev_mask = (dt >= prev_start) & (dt < prev_end)

        def _sum(df, col):
            return int(pd.to_numeric(df[col], errors="coerce").sum(skipna=True))

        def _mean(df, col):
            return float(pd.to_numeric(df[col], errors="coerce").mean(skipna=True))

        cur = d.loc[cur_mask]
        prev = d.loc[prev_mask]

        total_views_cur = _sum(cur, "Views") if not cur.empty else 0
        total_views_prev = _sum(prev, "Views") if not prev.empty else 0

        avg_eng_cur = (_mean(cur, "Engagement %") * 100) if not cur.empty else 0.0
        avg_eng_prev = (_mean(prev, "Engagement %") * 100) if not prev.empty else 0.0

        vir_cur = _mean(cur, "Virality") if not cur.empty else 0.0
        vir_prev = _mean(prev, "Virality") if not prev.empty else 0.0

        d1, a1 = _fmt_delta(total_views_cur, total_views_prev)
        d2, a2 = _fmt_delta(avg_eng_cur, avg_eng_prev)
        d3, a3 = _fmt_delta(vir_cur, vir_prev)

        c1, c2, c3 = st.columns(3)

        def _card(title: str, value: str, delta_str: str, arrow: str | None, icon: str) -> str:
            color = "#16a34a" if arrow == "↑" else ("#dc2626" if arrow == "↓" else "#6b7280")
            delta_txt = delta_str if delta_str != "—" else "—"
            html = (
                "<div class='kpi-card'>"
                f"<div class='kpi-label'>{title}</div>"
                "<div class='kpi-value'>"
                f"{icon} {value} "
                f"<span style='color:{color}'>({delta_txt})</span>"
                "</div>"
                "</div>"
            )
            return html

        # Kaarten in dezelfde stijl als de rest
        c1.markdown(
            _card(
                f"Weergaven ({sel}d)",
                f"{total_views_cur:,}".replace(",", "."),
                d1,
                a1,
                "👁️",
            ),
            unsafe_allow_html=True,
        )
        c2.markdown(
            _card(
                f"Gem. reactiescore ({sel}d)",
                f"{avg_eng_cur:.2f}%",
                d2,
                a2,
                "💬",
            ),
            unsafe_allow_html=True,
        )
        c3.markdown(
            _card(
                f"Virale score ({sel}d)",
                f"{vir_cur:.0f}/100",
                d3,
                a3,
                "🔥",
            ),
            unsafe_allow_html=True,
        )

        # Kleine sparklines onderin de kaarten (optioneel)
        if HAS_ALTAIR and not cur.empty:
            s1 = _sparkline(pd.to_numeric(cur["Views"], errors="coerce"))
            s2 = _sparkline(pd.to_numeric(cur["Engagement %"], errors="coerce") * 100)
            s3 = _sparkline(pd.to_numeric(cur["Virality"], errors="coerce"))

            if s1 is not None:
                c1.altair_chart(s1, use_container_width=False)
            if s2 is not None:
                c2.altair_chart(s2, use_container_width=False)
            if s3 is not None:
                c3.altair_chart(s3, use_container_width=False)

# ========================== Hero + Aanbeveling ===============================
def _confidence_from_data(d: pd.DataFrame) -> int:
    if d is None or d.empty:
        return 0

    dc = d.copy()
    dc["Datum"] = _to_naive(dc.get("Datum"))

    v = pd.to_numeric(dc.get("Views"), errors="coerce")

    n = int(v.notna().sum())
    size_score = float(np.clip(n / 30.0, 0, 1))

    now_naive = pd.Timestamp.now(tz=TZ).tz_convert(None).normalize()
    cutoff = np.datetime64(now_naive - pd.Timedelta(days=30))

    n_recent = int((dc["Datum"] >= cutoff).sum())
    recency_score = float(np.clip(n_recent / 15.0, 0, 1))

    have = sum(c in dc.columns for c in ["Views", "Likes", "Comments", "Shares", "Datum"])
    coverage = have / 5.0

    v_clean = v.dropna()
    if len(v_clean) >= 5 and v_clean.mean() > 0:
        stability = 1.0 - float(np.clip(v_clean.std() / (v_clean.mean() + 1e-9), 0, 1))
    else:
        stability = 0.5

    conf = 100 * (0.4 * size_score + 0.3 * recency_score + 0.2 * coverage + 0.1 * stability)
    return int(np.clip(conf, 0, 100))


def _hero_and_nba(d: pd.DataFrame, last_sync: str, bron: str):
    """Hoofdblok op het startscherm: 'Vandaag: 1 simpele groeistap'."""
    has_data = d is not None and not d.empty

    # ---------------- Stats voorbereiden ----------------
    views_7d_str = "—"
    posts_7d_str = "—"
    best_hour_label = "—"
    trend_tag = "#tiktoknl"

    if has_data:
        dfm = d.copy()
        dfm["Datum"] = _to_naive(dfm.get("Datum"))
        dfm = dfm.dropna(subset=["Datum"])

        if not dfm.empty:
            today = pd.Timestamp.now(tz=TZ).tz_convert(None).normalize()
            start7 = today - pd.Timedelta(days=6)
            mask7 = (dfm["Datum"] >= start7) & (dfm["Datum"] < today + pd.Timedelta(days=1))
            last7 = dfm.loc[mask7]

            if not last7.empty:
                views_7d = int(
                    pd.to_numeric(last7.get("Views", pd.Series(dtype=float)), errors="coerce").sum(skipna=True)
                )
                posts_7d = int(len(last7))
                views_7d_str = f"{views_7d:,}".replace(",", ".")
                posts_7d_str = str(posts_7d)

            # Beste uur
            try:
                best_hour = _best_hours(dfm, n=1)[0]
                best_hour_label = f"{best_hour:02d}:00"
            except Exception:
                best_hour = 20
                best_hour_label = "20:00"

            # Trending hashtag
            try:
                tr_df = trending_hashtags(dfm, days_window=14)
                if tr_df is not None and not tr_df.empty:
                    trend_tag = str(tr_df.head(1).index[0])
            except Exception:
                pass
        else:
            best_hour = 20
    else:
        best_hour = 20

    confidence = _confidence_from_data(d) if has_data else 0

    # ---------------- Info-regel boven hero ----------------
    st.markdown(
        f"""
        <div style="
            display:flex;
            flex-wrap:wrap;
            gap:0.5rem 0.75rem;
            align-items:center;
            font-size:0.78rem;
            color:#6b7280;
            margin-bottom:0.4rem;
        ">
          <div style="
              padding:0.15rem 0.7rem;
              border-radius:999px;
              background:#f9fafb;
              border:1px solid #e5e7eb;
              display:inline-flex;
              align-items:center;
              gap:0.4rem;
          ">
            🕒 <span>Laatste update: <strong>{last_sync or '—'}</strong></span>
          </div>
          <div style="
              padding:0.15rem 0.7rem;
              border-radius:999px;
              background:#f9fafb;
              border:1px solid #e5e7eb;
              display:inline-flex;
              align-items:center;
              gap:0.4rem;
          ">
            📂 <span>Bron: <strong>{bron or 'Onbekend'}</strong></span>
          </div>
          <div style="
              padding:0.15rem 0.7rem;
              border-radius:999px;
              background:#ecfdf5;
              border:1px solid #bbf7d0;
              display:inline-flex;
              align-items:center;
              gap:0.35rem;
              color:#047857;
          ">
            <span style="
                width:7px;
                height:7px;
                border-radius:999px;
                background:#22c55e;
                display:inline-block;
            "></span>
            <span>Vertrouwen in dit advies: <strong>{confidence}%</strong></span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------- Hero card: 1 simpele groeistap ----------------
    with st.container(border=True):
        # Titel + korte uitleg
        c1, c2 = st.columns([3, 2])

        with c1:
            st.markdown(
                """
                <div style="display:flex;align-items:center;gap:0.65rem;margin-bottom:0.15rem;">
                  <div style="
                      width:38px;height:38px;border-radius:999px;
                      background:#ecfdf5;color:#047857;
                      display:flex;align-items:center;justify-content:center;
                      font-size:1.2rem;
                  ">🚀</div>
                  <div>
                    <div style="font-size:1.05rem;font-weight:600;color:#111827;">
                      Vandaag: 1 simpele groeistap
                    </div>
                    <div style="font-size:0.86rem;color:#6b7280;margin-top:2px;">
                      Perfect voor starters: één duidelijke actie, geen ruis.
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Concrete “vandaag doen” in bullets
            if has_data:
                st.markdown(
                    f"""
                    - Post **1 video** rond **{best_hour_label}**  
                    - Gebruik een hook + hashtag in de richting van **{trend_tag}**  
                    - Kijk morgen alleen naar: *views in de eerste 2 uur*  
                    """,
                )
            else:
                st.markdown(
                    """
                    - Activeer **demo-data** of upload een CSV in de sidebar  
                    - Post 1 korte video (6–12 sec) vandaag  
                    - Schrijf 1 duidelijke hook + 2–3 woorden als hashtag  
                    """,
                )

        # Rechts: mini KPI’s heel clean
        with c2:
            st.markdown(
                f"""
                <div style="display:flex;flex-direction:column;align-items:flex-end;gap:0.35rem;">
                  <div style="
                      font-size:0.78rem;
                      font-weight:500;
                      padding:0.15rem 0.65rem;
                      border-radius:999px;
                      background:#eff6ff;
                      border:1px solid #bfdbfe;
                      color:#1d4ed8;
                  ">
                    Vandaag focus
                  </div>
                  <div style="text-align:right;">
                    <div style="font-size:0.8rem;color:#6b7280;">Beste tijd nu</div>
                    <div style="font-size:1.12rem;font-weight:600;color:#111827;">
                      {best_hour_label}
                    </div>
                  </div>
                  <div style="display:flex;flex-direction:column;align-items:flex-end;font-size:0.8rem;color:#6b7280;">
                    <span>Views (7 dagen): <strong>{views_7d_str}</strong></span>
                    <span>Posts (7 dagen): <strong>{posts_7d_str}</strong></span>
                    <span>Trending: <strong>{trend_tag}</strong></span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Kleine voetnoot onderin de card
        st.markdown(
            """
            <div style="font-size:0.8rem;color:#6b7280;margin-top:0.4rem;">
              Volg eerst deze stap. Daarna kun je in <strong>Analyse</strong> en 
              <strong>Strategie</strong> verder testen en tweaken.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------------- Onboarding-balk er direct onder ----------------
    _onboarding_bar(2 if has_data else 1)

# ============================== Build & Hero ================================
# Basis-dataset uit session of laatste bestand
if "df" not in st.session_state:
    st.session_state["df"] = _smart_read_any(LATEST_FILE)

# Zorg dat demo-flag altijd bestaat
st.session_state.setdefault("demo_active", False)

df_raw = st.session_state.get("df", pd.DataFrame())

base_for_hero = normalize_per_post(df_raw)
d_for_hero = add_kpis(base_for_hero) if not base_for_hero.empty else pd.DataFrame()

# Laatste sync-tijd mooi tonen
try:
    ts = float(SYNC_STATE_FILE.read_text().strip()) if SYNC_STATE_FILE.exists() else 0
    last_sync = datetime.fromtimestamp(ts).strftime("%d-%m %H:%M") if ts else "—"
except Exception:
    last_sync = "—"

# Bron-label duidelijker maken
if st.session_state.get("demo_active"):
    bron = "DEMO-data"
elif LATEST_FILE.exists():
    bron = "Eigen CSV/XLSX"
else:
    bron = "—"

_hero_and_nba(d_for_hero, last_sync, bron)
_kpi_row(d_for_hero, key_ns="top")
st.divider()

# ===== Mini-script voor vandaag ===========================================
# Bepaal beste uur voor mini-script (gebruik dezelfde data als hero)
source = d_for_hero

if source is None or source.empty:
    best_hour = 20
else:
    best_hour = _best_hours(source, n=1)[0]

with st.container(border=True):
    st.markdown("### 🎬 Mini-script voor vandaag")
    st.caption(
        "Gebruik dit als startpunt voor je video. Pas de tekst aan naar jouw onderwerp en stijl."
    )

    st.code(
        f"Hook: Wist je dit? Rond {best_hour:02d}:00 doen jouw video’s het vaak net iets beter.\n"
        "Body: Deel een korte tip, feit of persoonlijk inzicht in 2–3 zinnen. "
        "Houd het persoonlijk en duidelijk.\n"
        "CTA: Volg voor meer dagelijkse TikTok-inspiratie.",
        language="markdown",
    )

# ================================ LLM / AI Core ==============================
def _has_openai() -> bool:
    return bool(getconf("OPENAI_API_KEY", ""))

def _default_model() -> str:
    return getconf("OPENAI_MODEL", "gpt-4o-mini")

def _ask_llm(system: str, user: str, temperature: float = 0.4, max_tokens: int = 900) -> str:
    api_key = getconf("OPENAI_API_KEY", "")
    if not api_key:
        return "⚠️ Geen OPENAI_API_KEY gevonden. Voeg je key toe in st.secrets."
    model = _default_model()
    try:
        from openai import OpenAI
        client_ = OpenAI(api_key=api_key)
        resp = client_.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        import requests
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        if r.status_code != 200:
            return f"⚠️ OpenAI API fout ({r.status_code}): {r.text[:200]}"
        data = r.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            return "⚠️ Kon geen geldig antwoord ophalen van het model."

def _summarize_dataset_for_context(d: pd.DataFrame, top_n: int = 30) -> str:
    if d is None or d.empty:
        return "GEEN_DATA"
    df = d.copy()
    df["Datum"] = _to_naive(df["Datum"])
    df = df.sort_values("Datum", ascending=False).head(top_n)

    views = pd.to_numeric(df["Views"], errors="coerce").fillna(0)
    likes = pd.to_numeric(df["Likes"], errors="coerce").fillna(0)
    shares = pd.to_numeric(df["Shares"], errors="coerce").fillna(0)

    like_rate = (likes / views.replace(0, np.nan)).fillna(0).mean()
    share_rate = (shares / views.replace(0, np.nan)).fillna(0).mean()

    best_hours = _best_hours(d, n=3)
    top_tags = (
        df["Hashtags"]
        .dropna()
        .astype(str)
        .str.split()
        .explode()
        .pipe(lambda s: s[s.str.startswith("#")])
        .value_counts()
        .head(5)
        .index
        .tolist()
    )

    return (
        f"posts_analyzed={len(df)}; mean_views={int(views.mean())}; "
        f"like_rate_avg={like_rate:.3f}; share_rate_avg={share_rate:.3f}; "
        f"best_hours={best_hours}; top_hashtags={top_tags}"
    )

# ---------------------------- Coach Memory (nieuw) ----------------------------
def _load_coach_state() -> dict:
    if COACH_STATE_FILE.exists():
        try:
            return json.loads(COACH_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"kb": [], "feedback": [], "accepted_tips": []}

def _save_coach_state(state: dict) -> bool:
    try:
        COACH_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception:
        return False

def add_kb_note(text: str, tags: List[str] | None = None):
    stt = _load_coach_state()
    stt["kb"].append({"id": uuid.uuid4().hex[:8], "text": text.strip(), "tags": tags or []})
    _save_coach_state(stt)

def add_feedback(prompt: str, tips_text: str, rating: int):
    stt = _load_coach_state()
    stt["feedback"].append({"ts": time.time(), "prompt": prompt, "tips": tips_text, "rating": int(rating)})
    _save_coach_state(stt)

def mark_tip_accepted(tip_text: str):
    stt = _load_coach_state()
    stt["accepted_tips"].append(tip_text.strip())
    _save_coach_state(stt)

def _rank_notes_simple(query: str, notes: List[dict], top_k: int = 5) -> List[dict]:
    if not query or not query.strip() or not notes: return []
    q = set(re.findall(r"[a-z0-9#]+", _nk(query)))
    scored = []
    for n in notes:
        t = _nk(n.get("text",""))
        toks = set(re.findall(r"[a-z0-9#]+", t))
        overlap = len(q & toks)
        if overlap > 0:
            scored.append((overlap, n))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [n for _, n in scored[:top_k]]

# ---------------------------- AI Coach (Feature 1) ---------------------------
def ai_coach_suggestions(d: pd.DataFrame, niche_hint: str = "", user_prompt: str = "") -> str:
    ctx = _summarize_dataset_for_context(d, top_n=30)
    stt = _load_coach_state()
    kb_hits = _rank_notes_simple(user_prompt or niche_hint or "coach", stt.get("kb", []), top_k=6)
    kb_context = "\n".join(f"- {n['text']}" for n in kb_hits) if kb_hits else "(geen)"
    accepted = stt.get("accepted_tips", [])[-3:]
    fewshot = "\n".join(f"- {t}" for t in accepted) if accepted else "(geen)"
    last5 = stt.get("feedback", [])[-5:]
    neg_rate = (sum(1 for f in last5 if f.get("rating") == 0) / max(1, len(last5)))
    temp = 0.35 if neg_rate >= 0.4 else 0.4

    sys = (
        "Je bent een vriendelijke, concrete TikTok coach voor beginners. "
        "Gebruik simpele taal en geef ALTIJD precies 3 bullets en een korte afsluitende actie. "
        "Focus op timing (uren/dagen), hooks (8–12 woorden), max 3 hashtags, lengte/structuur, en hergebruik van topcontent. "
        "Weeg de kennisbank en eerder geaccepteerde tips mee waar relevant."
    )
    usr = (
        f"Dataset samenvatting: {ctx}\n"
        f"Niche/onderwerp: {niche_hint or 'onbekend'}\n"
        f"Vraag: {user_prompt or '—'}\n\n"
        f"Kennisbank (relevant):\n{kb_context}\n\n"
        f"Eerder geaccepteerde tips:\n{fewshot}\n\n"
        "Geef 3 direct uitvoerbare tips met cijfers/uren waar logisch. "
        "Sluit af met één duidelijke actiestap."
    )
    return _ask_llm(sys, usr, temperature=temp, max_tokens=600)

# ------------------ AI Caption & Hook generator (Feature 2) ------------------
def ai_generate_captions(d: pd.DataFrame, topic: str, n_variants: int = 3, style: str = "hooky") -> List[str]:
    ctx = _summarize_dataset_for_context(d, top_n=50)
    if d is not None and not d.empty:
        hash_df = (d.assign(_tag=d["Hashtags"].fillna("").str.split()).explode("_tag"))
        hash_df = hash_df[hash_df["_tag"].astype(str).str.startswith("#", na=False)]
    else:
        hash_df = pd.DataFrame(columns=["_tag"])
    top_hashtags = []
    if not hash_df.empty:
        top_hashtags = (hash_df["_tag"].value_counts().head(6).index.tolist())[:3]
    sys = (
        "Je bent een TikTok caption & hook generator. "
        "Geef korte, pakkende hooks (8–12 woorden), en 1–2 zinnen caption. "
        "Gebruik max 3 relevante hashtags. Geen emoji-spam."
    )
    usr = (
        f"Topic: {topic}\n"
        f"Dataset context: {ctx}\n"
        f"Stijl: {style}\n"
        f"Voorkeur-hashtags (op basis van data): {', '.join(top_hashtags) if top_hashtags else '(geen)'}\n"
        f"Geef {n_variants} varianten. Formaat per variant: HOOK — Caption — Hashtags"
    )
    raw = _ask_llm(sys, usr, temperature=0.8, max_tokens=600)
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    variants = []
    buff = []
    for ln in lines:
        if re.match(r"^\d+[\).\-]\s*", ln) and buff:
            variants.append(" ".join(buff).strip()); buff = [ln]
        else:
            buff.append(ln)
    if buff: variants.append(" ".join(buff).strip())
    if not variants:
        variants = [raw]
    return variants[:n_variants]
# -------------------------- Chat met PostAi (Feature 3) ----------------------
def ai_chat_answer(d: pd.DataFrame, question: str) -> str:
    ctx = _summarize_dataset_for_context(d, top_n=60)
    if d is None or d.empty:
        facts = "GEEN_DATA"
    else:
        df = d.copy()
        df["Datum"] = _to_naive(df["Datum"])
        df = df.sort_values("Datum", ascending=False).head(60)
        views = pd.to_numeric(df["Views"], errors="coerce").fillna(0)
        top_view = int(views.max()) if len(views) else 0
        med_view = int(views.median()) if len(views) else 0
        best_hours = _best_hours(d, n=3)
        facts = f"top_views={top_view}; median_views={med_view}; best_hours={best_hours}"
    sys = (
        "Je bent een data-assistent die kort antwoord geeft op basis van de meegegeven dataset. "
        "Als iets niet exact te zeggen is, geef een simpele vuistregel."
    )
    usr = (
        f"Vraag: {question}\n"
        f"Dataset_context: {ctx}\n"
        f"Kerncijfers: {facts}\n"
        "Geef een kort antwoord (2–5 zinnen) en sluit af met één praktische vervolgstap."
    )
    return _ask_llm(sys, usr, temperature=0.4, max_tokens=450)

# ================= Paywall helper v3 — ghost-UI + OVERLAY CTA ================
def locked_section(feature_name: str, pattern: str = "generic", height: int | None = None):
    """
    Toont ghost-UI achter blur met daarboven een vaste overlay-CTA kaart.
    Gebruik voor PRO-only onderdelen.
    """

    # Kleine helpers voor ghost-blokken
    def bar(h=44, w="100%", cls="ghost-bar", mt=0):
        return f"<div class='{cls}' style='height:{h}px;width:{w};margin-top:{mt}px;'></div>"

    def text(lbl, cls="ghost-txt", mt=6):
        return f"<div class='{cls}' style='margin-top:{mt}px;'>{lbl}</div>"

    css = """
<style>
  .ghost-wrap {
      position: relative;
      border: 1px solid var(--card-border);
      border-radius: 16px;
      background: var(--card);
      padding: 14px 14px 18px 14px;
      margin: 8px 0 12px 0;
  }
  .ghost-txt {
      font-size: 13px;
      color: #475569;
      opacity: .65;
  }
  .ghost-cap {
      font-size: 14px;
      font-weight: 600;
      color: #334155;
      opacity: .6;
  }
  .ghost-row {
      display: flex;
      gap: 10px;
      align-items: center;
      margin-top: 6px;
  }
  .ghost-pill {
      height: 28px;
      border-radius: 999px;
      background: #eef2f7;
  }
  .ghost-bar {
      height: 44px;
      border-radius: 12px;
      background: #eef2f7;
  }
  .ghost-block {
      border-radius: 12px;
      background: #f1f5f9;
  }

  /* PRO overlay card */
  .pro-overlay {
      position: absolute;
      left: 50%;
      transform: translateX(-50%);
      bottom: 14px;
      z-index: 30;
      pointer-events: auto;
      background: #ffffff;
      border: 1px solid var(--card-border);
      border-radius: 18px;
      box-shadow: 0 18px 40px rgba(15, 23, 42, .18);
      padding: 16px 20px;
      width: min(540px, 92%);
      text-align: center;
  }
  .pro-cta-title {
      font-weight: 700;
      font-size: 16px;
      color: #111827;
      margin-bottom: 4px;
  }
  .pro-cta-sub {
      color: #374151;
      margin-bottom: 6px;
      font-size: 13px;
  }
  .pro-cta-badges {
      color: #4b5563;
      margin-bottom: 10px;
      font-size: 12px;
  }
  .pro-cta-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 10px 18px;
      font-weight: 700;
      font-size: 14px;
      border-radius: 12px;
      background: #22c55e;
      color: #ffffff;
      border: 1px solid #16a34a;
      text-decoration: none;
      outline: none;
      cursor: pointer;
      -webkit-tap-highlight-color: transparent;
  }
  .pro-cta-btn:link,
  .pro-cta-btn:visited,
  .pro-cta-btn:hover,
  .pro-cta-btn:active,
  .pro-cta-btn:focus {
      text-decoration: none !important;
      border-bottom: 0 !important;
      color: #ffffff;
  }
  .pro-cta-btn:hover {
      filter: brightness(0.98);
  }
  .pro-cta-btn:active {
      transform: translateY(1px);
  }
  .pro-cta-btn:focus {
      box-shadow: 0 0 0 3px rgba(34, 197, 94, .25);
  }

  /* Extra ruimte zodat overlay niet over de container-rand valt */
  .ghost-pad {
      padding-bottom: 130px;
  }
</style>
"""

    def card(title: str) -> str:
        return f"""
  <div class="pro-overlay">
    <div class="pro-cta-title">🔒 {title} is een PRO-functie</div>
    <div class="pro-cta-sub">Ontgrendel alle AI-tools, playbooks en exports.</div>
    <div class="pro-cta-badges">🎁 14 dagen gratis · 💎 20% korting bij jaar · 🪙 7 dagen geld terug</div>
    <a class="pro-cta-btn" href="{LEMON_CHECKOUT_URL}" target="_blank" rel="noopener">
      ✨ Ontgrendel PRO
    </a>
  </div>
"""

    # ---------- Ghost content per pattern ----------
    if pattern == "generator":
        ghost_ui = f"""{text("Onderwerp/video-idee")}
{bar(44)}
<div class="ghost-row" style="margin-top:10px;">
  <div style="flex:1">{text("Stijl")}{bar(44)}</div>
  <div style="width:220px">{text("Aantal varianten")}{bar(44)}</div>
  <div style="width:220px">{text(" ")}{bar(44)}</div>
</div>
{bar(40, w='200px', cls='ghost-pill', mt=12)}
{text("Voorbeeld output")}
<div class="ghost-block" style="height:220px; margin-top:8px;"></div>"""

    elif pattern == "coach":
        ghost_ui = f"""{text("Waar heb je nu hulp bij?", 'ghost-cap', 0)}
<div class="ghost-block" style="height:90px; margin-top:8px;"></div>
<div class="ghost-row">
  <div style="flex:1">{text("Niche (optioneel)")}{bar(44)}</div>
  <div style="flex:1">{text("Regels/notities")}{bar(44)}</div>
</div>
{bar(40, w='220px', cls='ghost-pill', mt=10)}"""

    elif pattern == "chat":
        ghost_ui = f"""{text("Stel je vraag", 'ghost-cap', 0)}
{bar(44)}
{bar(40, w='200px', cls='ghost-pill', mt=10)}
<div class="ghost-block" style="height:160px; margin-top:12px;"></div>"""

    elif pattern == "trends":
        ghost_ui = f"""{text("Hashtag-filter")}
{bar(40, w='260px')}
{text("Top trending hashtags (14d vs 14d ervoor)", 'ghost-cap', 10)}
<div class="ghost-block" style="height:260px; margin-top:6px;"></div>"""

    elif pattern == "compare":
        ghost_ui = f"""<div class="ghost-row" style="margin-top:0;">
  <div style="flex:1">{text("Periode A")}{bar(44)}</div>
  <div style="flex:1">{text("Periode B")}{bar(44)}</div>
</div>
{text("Kern-KPI's", 'ghost-cap', 10)}
<div class="ghost-row">
  <div class="ghost-block" style="height:70px; flex:1;"></div>
  <div class="ghost-block" style="height:70px; flex:1;"></div>
  <div class="ghost-block" style="height:70px; flex:1;"></div>
</div>
<div class="ghost-block" style="height:220px; margin-top:12px;"></div>"""

    elif pattern == "exports":
        ghost_ui = f"""{text("Playbook & 7-dagen plan", 'ghost-cap', 0)}
<div class="ghost-block" style="height:190px; margin-top:8px;"></div>
<div class="ghost-row" style="margin-top:10px;">
  <div style="flex:1">{bar(40, cls='ghost-pill')}</div>
  <div style="flex:1">{bar(40, cls='ghost-pill')}</div>
</div>"""

    elif pattern == "branding":
        ghost_ui = f"""<div class="ghost-row" style="margin-top:0;">
  <div style="flex:1">{text("Merkkleur")}{bar(44)}</div>
  <div style="flex:1">{text("Logo (png) upload")}{bar(120, cls='ghost-block')}</div>
</div>"""

    elif pattern == "queue":
        ghost_ui = f"""{text("Wachtrij (voorbeeld items)", 'ghost-cap', 0)}
<div class="ghost-block" style="height:60px; margin-top:8px;"></div>
<div class="ghost-row">
  <div style="flex:1">{bar(40, cls='ghost-pill')}</div>
  <div style="flex:1">{bar(40, cls='ghost-pill')}</div>
</div>"""

    else:
        ghost_ui = f"""{text("Voorbeeld sectie", 'ghost-cap', 0)}
<div class="ghost-block" style="height:160px; margin-top:8px;"></div>
{bar(40, w='200px', cls='ghost-pill', mt=10)}"""

    html = f"""
{css}
<div class="ghost-wrap ghost-pad">
  <div style="filter:blur(1.6px) saturate(.95); opacity:.96; pointer-events:none;">
    {ghost_ui}
  </div>
  {card(feature_name)}
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# ================================ Tabs ======================================
tabs = st.tabs(["🧠 Start", "🤖 Coach", "📊 Analyse", "🎯 Strategie", "⚙️ Instellingen"])
tab_assist, tab_coach, tab_analyse, tab_strategy, tab_settings = tabs

# ----------------------------- Slimme assistent (Onboarding) ----------------
with tab_assist:
    st.subheader("🧠 Start — eerste stappen")

    # Data-status bepalen
    base = normalize_per_post(df_raw)
    d = add_kpis(base) if not base.empty else pd.DataFrame()
    has_data = not d.empty
    has_ai   = _has_openai()

    # Onboarding-progress (1 = data nog niet, 2 = data ok, 3 = data + AI)
    if not has_data:
        step = 1
    elif has_data and not has_ai:
        step = 2
    else:
        step = 3

    _onboarding_bar(step)

    # Korte uitleg bovenaan
    st.markdown(
        """
        <div style="font-size:0.88rem;color:#4b5563;margin-top:0.35rem;margin-bottom:0.75rem;">
          Begin hier als je net start met TikTok of met PostAi. 
          Doorloop de drie blokken van boven naar beneden – meer hoef je niet te doen.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =================== STAP 1 – Data aansluiten ===================
    with st.container(border=True):
        st.markdown("#### 1️⃣ Data aansluiten")

        if has_data:
            bron = "DEMO-data" if st.session_state.get("demo_active") else "Eigen CSV/XLSX"
            st.markdown(
                f"<span style='font-size:0.85rem;color:#16a34a;'>✅ {bron} is actief. Je kunt direct verder.</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div style="font-size:0.85rem;color:#6b7280;margin-bottom:0.45rem;">
                  Kies één optie om PostAi iets met je cijfers te laten doen.
                </div>
                """,
                unsafe_allow_html=True,
            )

        c1, c2 = st.columns(2)

        with c1:
            if st.button("🎯 Activeer demo-data", use_container_width=True):
                _activate_demo_data()
                st.experimental_rerun()

            st.caption(
                "Handig om de app te testen als je nog geen export hebt."
            )

        with c2:
            tpl = pd.DataFrame(
                [
                    dict(
                        caption="Voorbeeld caption #hashtag",
                        views=12345,
                        likes=678,
                        comments=12,
                        shares=34,
                        date=pd.Timestamp.today().normalize(),
                        videolink="",
                        author="@account",
                        videoid="1234567890",
                    )
                ]
            )
            st.download_button(
                "⬇️ Download CSV-sjabloon",
                data=tpl.to_csv(index=False).encode("utf-8"),
                file_name="postai_template.csv",
                mime="text/csv",
                use_container_width=True,
            )
            st.caption("Vul dit sjabloon met je eigen TikTok-statistieken.")

        st.caption(
            "Als je CSV is geladen, kun je onder **📊 Analyse** checken of views/likes/datum goed staan."
        )

    # =================== STAP 2 – Wat zie je op het startscherm? ===================
    with st.container(border=True):
        st.markdown("#### 2️⃣ Wat zie je bovenaan je scherm?")

        st.markdown(
            """
            <div style="font-size:0.85rem;color:#6b7280;margin-bottom:0.35rem;">
              Boven de tabs zie je één hoofdblok met:
            </div>
            <ul style="font-size:0.84rem;color:#4b5563;margin-top:0;margin-bottom:0.25rem;padding-left:1.1rem;">
              <li>een voorgesteld tijdstip <strong>“Vandaag posten”</strong></li>
              <li>mini-statistieken van de laatste dagen</li>
              <li>een simpel mini-script voor je video</li>
            </ul>
            <div style="font-size:0.83rem;color:#6b7280;margin-top:0.25rem;">
              Focus als beginner vooral op: <strong>tijdstip volgen</strong> en 
              <strong>het script gebruiken als kapstok</strong>. Niet op alle details.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if has_data:
            best_hour = _best_hours(d, n=1)[0]
            st.info(
                f"Op basis van je data is een veilig tijdstip voor vandaag rond **{best_hour:02d}:00**. "
                "Dit zie je terug in het groene blokje ‘Vandaag posten’ bovenaan."
            )
        else:
            st.info(
                "Zodra je data hebt (demo of eigen CSV), laat de hero bovenaan een concreet tijdstip zien om vandaag te posten."
            )

    # =================== STAP 3 – Naar de Coach ===================
    with st.container(border=True):
        st.markdown("#### 3️⃣ Persoonlijk advies via de Coach")

        if not has_ai:
            st.warning(
                "De Coach gebruikt OpenAI voor persoonlijk advies. "
                "Voeg een `OPENAI_API_KEY` toe in `st.secrets` of als environment variable om de Coach te activeren."
            )
        else:
            if not is_pro():
                st.markdown(
                    """
                    <div style="font-size:0.85rem;color:#6b7280;margin-bottom:0.35rem;">
                      De volledige 🧠 Coach staat klaar in de tab <strong>‘🤖 Coach’</strong>,
                      maar is onderdeel van PRO. In deze DEMO kun je al zien wat de app met je data doet.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.success(
                    "Je hebt PRO én een AI-key. Gebruik de tab **‘🤖 Coach’** als jouw dagelijkse TikTok-trainer."
                )

        st.markdown(
            """
            <div style="font-size:0.83rem;color:#6b7280;margin-top:0.35rem;">
              • Gebruik deze <strong>Start</strong>-tab als korte uitleg<br>
              • Gebruik <strong>🤖 Coach</strong> voor wat-je-nu-moet-doen advies<br>
              • Gebruik <strong>📊 Analyse</strong> en <strong>🎯 Strategie</strong> om later te gaan testen
            </div>
            """,
            unsafe_allow_html=True,
        )

    # =================== Wachtrij overzicht (PRO) ===================
    with st.container(border=True):
        st.markdown("#### ⏳ Wachtrij (PRO)")

        if not is_pro():
            locked_section("Wachtrij", pattern="queue")
        else:
            q = _read_queue()
            if not q:
                st.caption(
                    "Niets in de wachtrij. Voeg varianten toe via de A/B-test planner in de tab **🎯 Strategie**."
                )
            else:
                for it in q[:5]:
                    l, r = st.columns([6, 3])
                    l.markdown(
                        f"**{it['caption'][:64]}**  \n"
                        f"`{it['hashtags']}` · 🕒 {int(it['hour']):02d}:00"
                    )
                    if it["status"] == "pending":
                        if r.button(
                            "✅ Markeer als geplaatst",
                            key=f"ap_{it['id']}",
                            help="Simuleert dat deze post geplaatst is.",
                        ):
                            if approve_and_post(it["id"]):
                                st.toast("Gemarkeerd als geplaatst (demo).")
                    else:
                        r.markdown("✅ Geplaatst")

# ----------------------------- Volledige Coach -----------------------------
with tab_coach:
    st.subheader("🤖 TikTok Coach")

    # Data voorbereiden
    base = normalize_per_post(df_raw)
    d = add_kpis(base) if not base.empty else pd.DataFrame()
    has_data = not d.empty

    # Als er nog geen data is
    if not has_data:
        st.markdown(
            """
            <div style="font-size:0.88rem;color:#4b5563;margin-top:0.25rem;margin-bottom:0.75rem;">
              De coach werkt het beste met échte cijfers. Activeer eerst demo-data of upload een CSV in de sidebar.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info(
            "Nog geen data beschikbaar. "
            "Upload een CSV/XLSX of activeer de demo-data in de sidebar, "
            "dan kan de coach gericht advies geven."
        )
    else:
        # Boven: compacte contextkaart op basis van data
        with st.container(border=True):
            st.markdown("#### 📌 Coach voor vandaag")

            best_hours = _best_hours(d, n=3)
            try:
                tr_df = trending_hashtags(d, days_window=14)
                top_tag = tr_df.head(1).index[0] if tr_df is not None and not tr_df.empty else "#tiktoknl"
            except Exception:
                top_tag = "#tiktoknl"

            views = pd.to_numeric(d.get("Views"), errors="coerce").fillna(0)
            mean_views = int(views.mean()) if len(views) else 0
            max_views = int(views.max()) if len(views) else 0

            c1, c2, c3 = st.columns(3)
            c1.markdown(
                "<div class='kpi-card'><div class='kpi-label'>Beste uren nu</div>"
                f"<div class='kpi-value'>{', '.join(f'{h:02d}:00' for h in best_hours)}</div></div>",
                unsafe_allow_html=True,
            )
            c2.markdown(
                "<div class='kpi-card'><div class='kpi-label'>Gem. views per post</div>"
                f"<div class='kpi-value'>{mean_views:,}</div></div>".replace(",", "."),
                unsafe_allow_html=True,
            )
            c3.markdown(
                "<div class='kpi-card'><div class='kpi-label'>Top-hashtag</div>"
                f"<div class='kpi-value'>{top_tag}</div></div>",
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div style="font-size:0.83rem;color:#6b7280;margin-top:0.25rem;">
                  De coach gebruikt deze cijfers plus jouw vraag om 1–3 concrete stappen te geven.
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Zonder OpenAI-key: uitleg tonen en stoppen
    if not _has_openai():
        st.markdown("---")
        st.info(
            "Om de coach te gebruiken heb je een **OPENAI_API_KEY** nodig in `st.secrets` "
            "of als environment variable. Voeg die toe en herlaad de app."
        )
    else:
        # PRO-gate: volledige coach alleen voor PRO
        if not is_pro():
            st.markdown("---")
            locked_section("Volledige coach", pattern="coach")
        else:
            # ================== Coach UI ==================
            st.markdown("---")

            # Optioneel: coach leren (kennisbank)
            with st.expander("📚 Coach leren (eigen regels)", expanded=False):
                kb_txt = st.text_area(
                    "Regels/notities (do’s/don’ts, merkstem, CTA’s)…",
                    height=120,
                    placeholder=(
                        "Voorbeeld:\n"
                        "- Gebruik max 3 hashtags, nooit #foryou.\n"
                        "- Merkstem: direct, geen emoji-spam.\n"
                        "- Hook-sjabloon: 'Dit gaat je X besparen in Y seconden'."
                    ),
                    help="Schrijf dingen op die de Coach moet onthouden."
                )
                kb_tags = st.text_input(
                    "Tags (optioneel, komma-gescheiden)",
                    value="brand, captions, hooks",
                )
                if st.button("➕ Voeg toe aan kennisbank"):
                    if kb_txt.strip():
                        add_kb_note(
                            kb_txt.strip(),
                            [t.strip() for t in kb_tags.split(",") if t.strip()],
                        )
                        st.success("Toegevoegd aan kennisbank.")
                st.caption("Laatste items in kennisbank:")
                kb_items = _load_coach_state().get("kb", [])
                st.write("\n".join(f"• {n['text']}" for n in kb_items[-5:]) or "—")

            # Hoofd-layout: links vraag, rechts context/tips
            col_left, col_right = st.columns([2.1, 1])

            # ---------------- LINKERKANT: vraag & modus ----------------
            with col_left:
                st.markdown("#### 🎯 Waar heb je nu hulp bij?")

                growth_mode = st.radio(
                    "Kies je groeistand:",
                    ["🔵 Standje Views", "🟣 Standje Volgers", "🟠 Standje Comments"],
                    horizontal=True,
                    key="coach_full_growth_mode",
                )

                mode_context = {
                    "🔵 Standje Views": (
                        "Focus op snelle hooks, korte video’s, sterke eerste 2 seconden "
                        "en logisch gebruik van trending hashtags."
                    ),
                    "🟣 Standje Volgers": (
                        "Focus op series (deel 1/2/3), cliffhangers, verhaalopbouw en duidelijke follow-CTA’s."
                    ),
                    "🟠 Standje Comments": (
                        "Focus op stellingen, vragen in caption, A/B-keuzes en reacties uitlokken."
                    ),
                }[growth_mode]

                doel = st.selectbox(
                    "Hoofddoel van je account",
                    ["Meer views", "Meer volgers", "Meer comments", "Meer profielbezoeken"],
                    help="De coach stemt zijn advies hierop af.",
                    key="coach_main_goa",
                )

                niche = st.text_input(
                    "Niche / onderwerp",
                    placeholder="Bijv. dark psychology, liefde, fashion, fitness…",
                    help="Optioneel, maar helpt voor betere hooks & voorbeelden.",
                    key="coach_nich",
                )

                vraag = st.text_area(
                    "Beschrijf je grootste struggle van nu",
                    placeholder=(
                        "Voorbeelden:\n"
                        "- Mijn dark facts-video’s zakken na 2 seconden weg\n"
                        "- Ik krijg bijna geen comments\n"
                        "- Ik weet niet wat ik deze week moet posten\n"
                    ),
                    height=120,
                    key="coach_questio",
                )

                modus = st.radio(
                    "Wat wil je nu krijgen?",
                    [
                        "Advies (coach legt uit wat je moet doen)",
                        "Hooks & captions (directe tekstvoorstellen)",
                        "Data-vraag (kort antwoord op basis van mijn cijfers)",
                    ],
                    index=0,
                    help="Je kunt dit per vraag wisselen.",
                    key="coach_reply_mod",
                )

                uitvoeren = st.button(
                    "🧠 Vraag de coach",
                    type="primary",
                    use_container_width=True,
                    key="coach_submit_butto",
                )

            # ---------------- RECHTERKANT: tips & context ----------------
            with col_right:
                st.markdown("#### ℹ️ Zo haal je het meeste eruit")
                st.markdown(
                    """
                    <ul style="font-size:0.83rem;color:#4b5563;margin-top:0;margin-bottom:0.4rem;padding-left:1.1rem;">
                      <li>Noem één probleem tegelijk</li>
                      <li>Zeg wat je al hebt geprobeerd</li>
                      <li>Noem een richting: dark facts, love stories, POV, etc.</li>
                    </ul>
                    """,
                    unsafe_allow_html=True,
                )

                if has_data:
                    ctx = _summarize_dataset_for_context(d, top_n=40)
                    st.caption("Samenvatting die de coach ziet:")
                    st.code(ctx, language="text")
                else:
                    st.caption("Zodra er data is, ziet de coach hier jouw samenvatting.")

            # ================== Coach-aanroepen ==================
            if uitvoeren:
                if not vraag.strip() and not modus.startswith("Hooks & captions"):
                    st.warning("Beschrijf eerst kort je vraag of probleem.")
                else:
                    with st.spinner("Coach denkt met je mee…"):

                        if modus.startswith("Advies"):
                            # Advies-modus
                            enriched_prompt = (
                                vraag or f"Help mij met {doel.lower()} in niche {niche or 'algemeen'}"
                            ) + (
                                f"\nGROEI-STAND: {growth_mode}. "
                                f"Richt je advies volledig volgens deze modus: {mode_context}"
                            )

                            tips = ai_coach_suggestions(
                                d if has_data else pd.DataFrame(),
                                niche_hint=f"{niche} · doel: {doel}",
                                user_prompt=enriched_prompt,
                            )

                            st.markdown("### 🧠 Coach-advies")
                            st.markdown(tips)

                            # Vandaag-doen actie
                            try:
                                best_hour = _best_hours(d, n=1)[0]
                            except Exception:
                                best_hour = 19

                            gm_clean = growth_mode.replace("🔵 ", "").replace("🟣 ", "").replace("🟠 ", "")
                            action_text = (
                                f"**Vandaag doen:** Post 1 video om **{best_hour:02d}:00** "
                                f"in **{gm_clean}**-stijl, afgestemd op '{doel.lower()}'."
                            )

                            st.markdown("---")
                            st.markdown(action_text)

                            done_key = f"done_{uuid.uuid4().hex[:6]}"
                            if st.checkbox("Ik heb dit gedaan ✔️", key=done_key):
                                st.success("Nice! Je ligt op schema. Morgen pakken we de volgende stap 💪")

                            # Feedback-knoppen
                            colA, colB, colC = st.columns(3)
                            with colA:
                                if st.button("👍 Helpt mij", key="coach_helpful"):
                                    add_feedback(vraag, tips, rating=1)
                                    st.success("Top! De coach leert hiervan.")
                            with colB:
                                if st.button("👎 Niet helpend", key="coach_not_helpful"):
                                    add_feedback(vraag, tips, rating=0)
                                    st.info("Feedback opgeslagen, dank je.")
                            with colC:
                                if st.button("➕ Zet eerste tip in wachtrij (19:00)", key="coach_queue_tip"):
                                    first_line = tips.splitlines()[0] if tips else "Nieuwe tip"
                                    queue_post(first_line, "#tiktoknl", 19)
                                    mark_tip_accepted(first_line)
                                    st.success("Eerste tip toegevoegd aan wachtrij.")

                        elif modus.startswith("Hooks & captions"):
                            # Hooks & captions-modus
                            topic = (vraag or niche).strip()
                            if not topic:
                                st.warning(
                                    "Vul bij ‘Niche / onderwerp’ of in het tekstveld iets in "
                                    "waar de hooks/captions over moeten gaan."
                                )
                            else:
                                out = ai_generate_captions(
                                    d if has_data else pd.DataFrame(),
                                    topic=topic,
                                    n_variants=3,
                                    style="hooky",
                                )
                                st.markdown("### 🪄 Hooks & captions")
                                for i, var in enumerate(out, 1):
                                    st.markdown(f"**Variant {i}**")
                                    st.code(var, language="text")
                                st.caption(
                                    "Tip: kies 2 varianten en zet ze in de A/B-test planner voor een simpele test."
                                )

                        else:
                            # Data-vraag-modus
                            ans = ai_chat_answer(d if has_data else pd.DataFrame(), vraag)
                            st.markdown("### 📊 Antwoord op je datavraag")
                            st.markdown(ans)

# ---- Analyse ---------------------------------------------------------------
with tab_analyse:
    st.subheader("📊 Analyse — duidelijk voor iedereen")

    base = normalize_per_post(df_raw)
    d = add_kpis(base) if not base.empty else pd.DataFrame()

    # ================== Blok 1: Resultaten-overzicht ==================
    with st.expander("📋 Resultaten-overzicht", expanded=False):
        st.caption(
            "Bekijk al je posts in één tabel. Filter op een hashtag om snel te zien wat werkt."
        )

        if d.empty:
            st.info(tr("no_data"))
        else:
            qtxt = (
                st.text_input(
                    "Filter op hashtag (optioneel)",
                    placeholder="#love, #psychology…",
                    help="Typ een hashtag om te filteren. Laat leeg om alles te tonen.",
                )
                .strip()
                .lower()
            )

            if qtxt:
                filt = d[
                    d["Hashtags"]
                    .fillna("")
                    .str.lower()
                    .str.contains(qtxt, regex=False)
                ]
            else:
                filt = d

            cols = [
                c
                for c in [
                    "Hashtags",
                    "Views",
                    "Likes",
                    "Comments",
                    "Shares",
                    "Datum",
                    "Like rate",
                    "Share rate",
                    "Velocity",
                    "Score",
                    "Virality",
                    "Video link",
                ]
                if c in filt.columns
            ]

            st.dataframe(filt[cols], use_container_width=True, hide_index=True)

    # ================== Blok 2: Hashtag-prestaties ====================
    with st.expander("🏷 Hashtag-prestaties", expanded=False):
        st.caption(
            "Zie welke hashtags je het vaakst gebruikt en welke het beste scoren op basis van jouw data."
        )

        if d.empty:
            st.info(tr("no_data"))
        else:
            tags = d.assign(_tag=d["Hashtags"].fillna("").str.split()).explode("_tag")
            tags = tags[tags["_tag"].astype(str).str.startswith("#", na=False)]

            if tags.empty:
                st.info("Geen hashtags gevonden in je data.")
            else:
                agg = (
                    tags.groupby("_tag", dropna=True)
                    .agg(
                        freq=("Views", "count"),
                        views=("Views", "sum"),
                        avg_like_rate=("Like rate", "mean"),
                        avg_share_rate=("Share rate", "mean"),
                        avg_score=("Score", "mean"),
                        avg_virality=("Virality", "mean"),
                    )
                    .sort_values(["freq", "avg_score"], ascending=[False, False])
                )

                st.dataframe(agg.head(30), use_container_width=True)
                st.caption("Gesorteerd op combinatie van gebruiksfrequentie en gemiddelde score.")

    # ================== Blok 3: Wat werkt nu? (trends) =================
    with st.expander("📈 Wat werkt nu? (trends, PRO)", expanded=False):
        if not is_pro():
            locked_section("Trends", pattern="trends")
        else:
            st.caption(
                "We vergelijken de laatste 14 dagen met de 14 dagen daarvoor en tonen welke hashtags nu in de lift zitten."
            )

            if d.empty:
                st.info(tr("no_data"))
            else:
                tr_df = trending_hashtags(d, days_window=14)

                if tr_df is None or tr_df.empty:
                    st.info("Niet genoeg data om betrouwbare trends te berekenen.")
                else:
                    st.dataframe(tr_df.head(25), use_container_width=True)
                    st.caption(
                        "Tip: kies 1–2 hashtags uit de top en verwerk die in je volgende 5 posts."
                    )

    # ================== Blok 4: Vergelijk perioden (PRO) ==============
    with st.expander("🔁 Vergelijk perioden (A vs. B, PRO)", expanded=False):
        if not is_pro():
            locked_section("Vergelijk perioden", pattern="compare")
        else:
            st.caption(
                "Vergelijk twee zelfgekozen periodes. Handig om te zien of je nieuwe aanpak beter werkt."
            )

            if d.empty:
                st.info(tr("no_data"))
            else:
                colA, colB = st.columns(2)

                with colA:
                    a = st.date_input(
                        "Periode A",
                        value=(),
                        format="YYYY-MM-DD",
                        key="pa",
                        help="Kies begin- en einddatum voor je eerste periode.",
                    )

                with colB:
                    b = st.date_input(
                        "Periode B",
                        value=(),
                        format="YYYY-MM-DD",
                        key="pb",
                        help="Kies begin- en einddatum voor je tweede periode.",
                    )

                def slice_period(rng: tuple) -> pd.DataFrame:
                    if not isinstance(rng, (list, tuple)) or len(rng) != 2:
                        return pd.DataFrame()
                    start = pd.to_datetime(rng[0])
                    end = pd.to_datetime(rng[1]) + pd.Timedelta(days=1)
                    dt = _to_naive(d["Datum"])
                    mask = (dt >= start) & (dt < end)
                    return d.loc[mask].copy()

                A = slice_period(a)
                B = slice_period(b)

                def kpis(df: pd.DataFrame) -> tuple[int, float, float]:
                    if df is None or df.empty:
                        return 0, 0.0, 0.0

                    tv = int(
                        pd.to_numeric(
                            df.get("Views", pd.Series(dtype=float)),
                            errors="coerce",
                        ).sum(skipna=True)
                    )
                    eng = float(
                        pd.to_numeric(
                            df.get("Engagement %", pd.Series(dtype=float)),
                            errors="coerce",
                        )
                        .mean(skipna=True)
                        * 100
                    )
                    sc = float(
                        pd.to_numeric(
                            df.get("Score", pd.Series(dtype=float)),
                            errors="coerce",
                        ).mean(skipna=True)
                    )
                    return tv, eng, sc

                tvA, engA, scA = kpis(A)
                tvB, engB, scB = kpis(B)

                k1, k2, k3 = st.columns(3)

                k1.markdown(
                    "<div class='kpi-card'><div class='kpi-label'>Views A / B</div>"
                    f"<div class='kpi-value'>👁️ {tvA:,} / {tvB:,}</div></div>".replace(",", "."),
                    unsafe_allow_html=True,
                )
                k2.markdown(
                    "<div class='kpi-card'><div class='kpi-label'>Gem. engagement (%)</div>"
                    f"<div class='kpi-value'>📈 {engA:.2f}% / {engB:.2f}%</div></div>",
                    unsafe_allow_html=True,
                )
                k3.markdown(
                    "<div class='kpi-card'><div class='kpi-label'>Δ Virale score (B − A)</div>"
                    f"<div class='kpi-value'>{(scB - scA):+,.3f}</div></div>".replace(",", "."),
                    unsafe_allow_html=True,
                )

                st.caption(
                    "Praktisch: kies een periode vóór je nieuwe aanpak als A, en een periode daarna als B. "
                    "Zo zie je snel of je strategie echt beter werkt."
                )

# -------------------------------- Archief -----------------------------------


# -------------------------------- STRATEGIE -----------------------------------
with tab_strategy:
    st.subheader("🎯 Strategie — makkelijk testen")

    base = normalize_per_post(df_raw)
    d = add_kpis(base) if not base.empty else pd.DataFrame()

    # ===================== Blok 1: Ideeën & testen ============================
    st.markdown("### 🧪 Ideeën & testen")

    # Ideeën (gratis teaser)
    with st.expander("💡 Ideeëngenerator (gratis)", expanded=False):
        topic = st.text_input(
            "Onderwerp of thema",
            placeholder="Bijv. manipulatie, angst, liefde…",
            help="Waar gaat je video over?",
            key="strat_topic_ideas",  # 👈 unieke key
        )

        if topic:
            st.caption(
                "We geven 3 simpele video-ideeën die je direct kunt opnemen. "
                "Pas ze aan naar jouw niche."
            )
            for i in range(1, 4):
                st.markdown(f"**Idee {i}** — #{topic}")
                cap = f"{topic}. Volg @Darkestpsycho voor meer dark psych facts."
                tags = "#darkfacts #psychology #creepy #mindblown #tiktoknl"
                prompt = (
                    f"Korte 9:16 video over **{topic}**; donkere stijl; 5–8s; "
                    "1) hook shockfact 2) 2–3 beats 3) CTA 'Volg @Darkestpsycho'."
                )
                st.code(cap, language="text")
                st.code(tags, language="text")
                st.code(prompt, language="text")
                st.divider()

    # ===================== Blok 2: A/B-test planner (PRO) =====================
    with st.expander("🔁 A/B-test planner (PRO)", expanded=False):
        if not is_pro():
            locked_section("A/B-test planner", pattern="generator")
        else:
            if d.empty:
                st.info("Upload een CSV/XLSX of gebruik de demo-data om te plannen.")
            else:
                col1, col2 = st.columns(2)

                with col1:
                    hook_a = st.text_input(
                        "Hook A (eerste zin)",
                        value="Wat bijna niemand weet…",
                        help="De allereerste zin. Kort en prikkelend (8–12 woorden).",
                        key="strat_ab_hook_a",   # 👈 unieke key
                    )
                    tags_a = st.text_input(
                        "Hashtags A",
                        value="#darkfacts #psychology #tiktoknl",
                        help="Gebruik max. 3 hashtags. Houd ze relevant.",
                        key="strat_ab_tags_a",   # 👈 unieke key
                    )
                    hour_a = st.number_input(
                        "Uur A",
                        min_value=0,
                        max_value=23,
                        value=19,
                        key="strat_ab_hour_a",   # 👈 unieke key
                        help="Het uur waarop je wilt posten (0–23).",
                    )

                with col2:
                    hook_b = st.text_input(
                        "Hook B",
                        value="Dit klinkt raar, maar…",
                        help="Alternatieve eerste zin.",
                        key="strat_ab_hook_b",   # 👈 unieke key
                    )
                    tags_b = st.text_input(
                        "Hashtags B",
                        value="#viral #mindblown #fyp",
                        help="Alternatieve hashtagset.",
                        key="strat_ab_tags_b",   # 👈 unieke key
                    )
                    hour_b = st.number_input(
                        "Uur B",
                        min_value=0,
                        max_value=23,
                        value=21,
                        key="strat_ab_hour_b",   # 👈 unieke key
                        help="Alternatief uur.",
                    )

                # ---- Simpele “PVS” (Performance Voorspel Score) ----
                def pvs(hook, tags, hr):
                    base_vir = float(
                        d["Virality"].tail(50).mean(skipna=True)
                    ) if "Virality" in d and not d["Virality"].empty else 50

                    hook_len = len(hook.split())
                    n_tags = len([t for t in tags.split() if t.startswith("#")])

                    hook_bonus = np.clip(hook_len * 2.2, 0, 22)
                    tags_bonus = np.clip(n_tags * 3.0, 0, 18)
                    hr_bonus = 22 if hr in _best_hours(d, n=3) else 8

                    return int(
                        np.clip(
                            base_vir * 0.3 + hook_bonus + tags_bonus + hr_bonus,
                            0,
                            100,
                        )
                    )

                rows = []
                for label, hook, tags, hr in [
                    ("A", hook_a, tags_a, int(hour_a)),
                    ("B", hook_b, tags_b, int(hour_b)),
                ]:
                    rows.append([label, hook, tags, hr, pvs(hook, tags, hr)])

                combo = pd.DataFrame(
                    rows,
                    columns=["Variant", "Hook (tekst)", "Hashtag-mix", "Uur", "PVS"],
                )

                st.dataframe(combo, use_container_width=True, hide_index=True)

                st.markdown("### In wachtrij zetten")
                pick = st.selectbox(
                    "Welke variant toevoegen?",
                    ["A", "B"],
                    help="Kies de versie die je wilt inplannen.",
                    key="strat_ab_pick",        # 👈 unieke key
                )

                if st.button(tr("add_queue"), key="strat_ab_add_btn"):
                    row = combo.loc[0 if pick == "A" else 1]
                    queue_post(row["Hook (tekst)"], row["Hashtag-mix"], int(row["Uur"]))
                    st.success("Toegevoegd aan wachtrij.")

    st.markdown("---")

    # ===================== Blok 2: AI-tools (PRO) =============================
    st.markdown("### 🤖 AI-tools (PRO)")

    # AI Coach — PRO
    with st.expander("🧠 AI Coach — persoonlijk advies", expanded=False):
        if not _has_openai():
            st.info("Voeg je **OPENAI_API_KEY** toe in `st.secrets` om de AI Coach te gebruiken.")
        else:
            if not is_pro():
                locked_section("AI Coach — persoonlijk advies", pattern="coach")
            else:
                has_data = not d.empty

                if d.empty:
                    st.info("Nog geen data. Upload of gebruik demo-data voor persoonlijk advies.")
                else:
                    # hier begint de layout
                    col_left, col_right = st.columns([2, 1])

                    # ------------- LINKERKANT: vraag & context -------------
                    with col_left:
                        st.markdown("##### 🎯 Waar heb je nu hulp bij?")

                        growth_mode = st.radio(
                            "Kies je groeistand:",
                            ["🔵 Standje Views", "🟣 Standje Volgers", "🟠 Standje Comments"],
                            horizontal=True,
                            key="coach_growth_mode",
                        )

                        main_goal = st.selectbox(
                            "Hoofddoel van je account",
                            [
                                "Meer views",
                                "Meer volgers",
                                "Meer comments / gesprekken",
                                "Meer profielbezoeken / kliks",
                            ],
                            index=0,
                            key="coach_main_goal",
                        )

                        niche = st.text_input(
                            "Niche / onderwerp",
                            placeholder="Bijv. dark psychology, liefde, fashion, fitness…",
                            key="coach_niche",
                        )

                        user_text_check = st.text_area(
                            "Beschrijf kort waar je nu mee vastloopt",
                            height=160,
                            placeholder=(
                                "Voorbeelden:\n"
                                "- Mijn dark facts-video’s zakken na 2 seconden weg\n"
                                "- Ik krijg bijna geen comments\n"
                                "- Ik weet niet welke hook ik moet pakken…"
                            ),
                            key="coach_issue_text",
                        )

                        modus = st.radio(
                            "Kies wat je nu wilt krijgen:",
                            [
                                "Advies: wat moet ik nu doen?",
                                "Hooks & captions: kant-en-klare tekst",
                                "Data-vraag: kort antwoord op basis van mijn cijfers",
                            ],
                            index=0,
                            help="Je kunt dit per vraag wisselen.",
                            key="coach_reply_mode",
                        )

                        # interne variabelen voor de coach-logica
                        vraag = user_text_check
                        doel = main_goal

                        if growth_mode.startswith("🔵"):
                            mode_context = "focus op zoveel mogelijk views"
                        elif growth_mode.startswith("🟣"):
                            mode_context = "focus op volgersgroei en herkenbare series"
                        else:
                            mode_context = "focus op gesprekken en comments"

                        uitvoeren = st.button(
                            "🧠 Vraag de coach",
                            type="primary",
                            use_container_width=True,
                            key="coach_submit_button",
                        )

                    # ------------- RECHTERKANT: tips / uitleg -------------
                    with col_right:
                        st.markdown("##### ℹ️ Tip voor de beste antwoorden")
                        st.markdown(
                            "- Wees concreet: noem één probleem tegelijk\n"
                            "- Vertel wat je al geprobeerd hebt\n"
                            "- Noem een richting: dark facts, love stories, POV, etc."
                        )
                        ctx = _summarize_dataset_for_context(d, top_n=25)
                        st.caption("Samenvatting die de coach ziet:")
                        st.code(ctx, language="text")

                    # ---------------- Coach-aanroep ----------------
                    if uitvoeren:
                        if not vraag.strip() and not modus.startswith("Hooks & captions"):
                            st.warning("Beschrijf eerst kort je grootste struggle.")
                        else:
                            with st.spinner("Coach denkt even met je mee…"):

                                if modus.startswith("Advies"):
                                    # Advies-modus
                                    enriched_prompt = (
                                        vraag
                                        or f"Help mij met {doel.lower()} in niche {niche or 'algemeen'}"
                                    ) + (
                                        f"\nGROEI-STAND: {growth_mode}. "
                                        f"Richt je advies volledig volgens deze modus: {mode_context}"
                                    )

                                    tips = ai_coach_suggestions(
                                        d if has_data else pd.DataFrame(),
                                        niche_hint=f"{niche} · doel: {doel}",
                                        user_prompt=enriched_prompt,
                                    )

                                    st.markdown("### 🧠 Coach-advies")
                                    st.markdown(tips)

                                    # Vandaag-doen actie
                                    try:
                                        best_hour = _best_hours(d, n=1)[0]
                                    except Exception:
                                        best_hour = 19

                                    gm_clean = (
                                        growth_mode.replace("🔵 ", "")
                                        .replace("🟣 ", "")
                                        .replace("🟠 ", "")
                                    )
                                    action_text = (
                                        f"**Vandaag doen:** Post **1 video** om **{best_hour:02d}:00** "
                                        f"in **{gm_clean}**-stijl, afgestemd op '{doel.lower()}'."
                                    )

                                    st.markdown("---")
                                    st.markdown(action_text)

                                    done_key = f"done_{uuid.uuid4().hex[:6]}"
                                    if st.checkbox("Ik heb dit gedaan ✔️", key=done_key):
                                        st.success(
                                            "Nice! Je ligt op schema. Morgen pakken we de volgende stap 💪"
                                        )

                                    # Feedback-knoppen
                                    colA, colB, colC = st.columns(3)
                                    with colA:
                                        if st.button("👍 Helpt mij", key="coach_helpful"):
                                            add_feedback(vraag, tips, rating=1)
                                            st.success("Top! De coach ‘leert’ van je feedback.")
                                    with colB:
                                        if st.button("👎 Niet helpend", key="coach_not_helpful"):
                                            add_feedback(vraag, tips, rating=0)
                                            st.info("Feedback opgeslagen, dank je.")
                                    with colC:
                                        if st.button(
                                            "➕ Zet eerste tip in wachtrij (19:00)",
                                            key="coach_queue_tip",
                                        ):
                                            first_line = (
                                                tips.splitlines()[0] if tips else "Nieuwe tip"
                                            )
                                            queue_post(first_line, "#tiktoknl", 19)
                                            mark_tip_accepted(first_line)
                                            st.success("Eerste tip toegevoegd aan wachtrij.")

                                elif modus.startswith("Hooks & captions"):
                                    # Hooks & captions-modus
                                    topic = (vraag or niche).strip()
                                    if not topic:
                                        st.warning(
                                            "Vul bij ‘Niche / onderwerp’ of in het tekstveld iets in "
                                            "waar de hooks/captions over moeten gaan."
                                        )
                                    else:
                                        out = ai_generate_captions(
                                            d if has_data else pd.DataFrame(),
                                            topic=topic,
                                            n_variants=3,
                                            style="hooky",
                                        )
                                        st.markdown("### 🪄 Hooks & captions")
                                        for i, var in enumerate(out, 1):
                                            st.markdown(f"**Variant {i}**")
                                            st.code(var, language="text")
                                        st.caption(
                                            "Tip: kies 2 varianten en zet ze in de A/B-test planner voor een simpele test."
                                        )

                                else:
                                    # Data-vraag-modus
                                    ans = ai_chat_answer(d if has_data else pd.DataFrame(), vraag)
                                    st.markdown("### 📊 Antwoord op je datavraag")
                                    st.markdown(ans)

                    st.markdown("---")

    # ------------- Hook/Caption checker -------------
    with st.expander("✍️ Check mijn hook/caption", expanded=False):
        st.caption(
                        "Plak een hook of caption en krijg 3 concrete verbeterpunten. "
                        "Handig als snelle check voordat je post."
                    )
        user_text_check_2 = st.text_area(
            "Je hook/caption",
            height=160,
            placeholder=(
                "Voorbeelden:\n"
                "- Mijn dark facts-video’s zakken na 2 seconden weg\n"
                "- Ik krijg bijna geen comments\n"
                "- Ik weet niet welke hook ik moet pakken…"
            ),
            key="coach_issue_text_v2",  # 👈 unieke key
        )

        analyse_btn = st.button(
            "🔍 Analyseer mijn tekst",
            use_container_width=True,
            key="coach_analyse_btn",  # 👈 ook unieke key
        )

        if analyse_btn:
            if not user_text_check_2.strip():
                st.warning("Plak eerst een hook of caption.")
            else:
                with st.spinner("Analyseren..."):
                    # Beste hashtag uit data
                    if has_data:
                        try:
                            tr = trending_hashtags(d, days_window=14)
                            top_hash = (
                                tr.head(1).index[0]
                                if tr is not None and not tr.empty
                                else "#tiktoknl"
                            )
                        except Exception:
                            top_hash = "#tiktoknl"
                    else:
                        top_hash = "#tiktoknl"

                    system_msg = (
                        "Je bent een ervaren TikTok script-editor. "
                        "Geef altijd precies 3 bullets met concrete verbeterpunten voor de gegeven tekst. "
                        "Focus op hook-kracht, lengte, spanning/kijkersretentie en duidelijkheid. "
                        "Maak het kort, direct en toepasbaar voor beginners."
                    )

                    check_prompt = (
                        f"Growth mode: {growth_mode} ({mode_context}).\n"
                        f"Beste hashtag volgens mijn data: {top_hash}.\n\n"
                        "Analyseer deze tekst alsof het hook + caption is voor TikTok "
                        "en geef precies 3 bullets met verbeterpunten:\n\n"
                        f"\"{user_text_check_2.strip()}\""
                    )

                    result = _ask_llm(
                        system_msg,
                        check_prompt,
                        temperature=0.5,
                        max_tokens=400,
                    )

                    st.markdown("### 📌 Analyse")
                    st.markdown(result)
                    st.caption(
                        "Deze feedback is gebaseerd op je eigen data + TikTok best practices."
                    )

        # Onder: beste uren nog één keer als opdracht
        if has_data:
            best = _best_hours(d, n=3)
            st.markdown("---")
            st.caption(
                "📌 Volgens je data zijn dit nu je beste uren: "
                + ", ".join(f"**{h:02d}:00**" for h in best)
                + ". Plan minimaal 3 video’s op deze momenten in voor komende week."
            )

    # ================= Caption & Hook generator — PRO ==================
    with st.expander("🪄 Caption & Hook generator (PRO)", expanded=False):
        if not _has_openai():
            st.info("Voeg je **OPENAI_API_KEY** toe in `st.secrets` om de generator te gebruiken.")
        else:
            if not is_pro():
                locked_section("Caption & Hook generator", pattern="generator")
            else:
                if d.empty:
                    st.info("Nog geen data. Je kunt wel genereren, maar met data wordt het slimmer afgestemd.")
                st.caption(
                    "Geef een onderwerp en stijl. PostAi bedenkt meerdere varianten zodat jij alleen nog hoeft te kiezen."
                )

                topic = st.text_input(
                    "Onderwerp / video-idee",
                    placeholder="Bijv. Waarom 90% dit fout doet…",
                )
                style = st.selectbox(
                    "Stijl",
                    ["hooky (kort & punchy)", "informatief", "conversational"],
                    index=0,
                )
                n_var = st.slider("Aantal varianten", 1, 5, 3)

                if st.button("✨ Genereer captions", use_container_width=True):
                    if not topic.strip():
                        st.warning("Vul eerst een onderwerp in.")
                    else:
                        with st.spinner("Aan het bedenken…"):
                            out = ai_generate_captions(
                                d if not d.empty else pd.DataFrame(),
                                topic=topic,
                                n_variants=int(n_var),
                                style=style.split()[0],
                            )
                        for i, var in enumerate(out, 1):
                            st.markdown(f"**Variant {i}**")
                            st.code(var)
                        st.caption("Tip: zet je favoriete variant in de A/B-test planner.")

    # ================= Chat — PRO ==================
    with st.expander("💬 Chat met PostAi (PRO)", expanded=False):
        if not _has_openai():
            st.info("Voeg je **OPENAI_API_KEY** toe in `st.secrets` om te chatten.")
        else:
            if not is_pro():
                locked_section("Chat", pattern="chat")
            else:
                if d.empty:
                    st.info(
                        "Nog geen data. Upload of gebruik demo-data voor antwoorden die echt bij jouw account passen."
                    )

                st.caption(
                    "Stel hier losse vragen over je account, timing, content of groei. "
                    "Handig als snelle ‘second opinion’."
                )

                question = st.text_input(
                    "Stel je vraag",
                    placeholder="Bijv. ‘Wat is mijn beste posttijd?’ of ‘Wat verbeteren aan mijn captions?’",
                )

                if st.button("Vraag het PostAi", use_container_width=True):
                    if not question.strip():
                        st.warning("Typ eerst een vraag.")
                    else:
                        with st.spinner("Kijken wat je data zegt…"):
                            ans = ai_chat_answer(d if not d.empty else pd.DataFrame(), question)
                        st.markdown(ans)

    st.markdown("---")

    # ===================== Blok 3: Playbook & Plan (PRO) ======================
    st.markdown("### 📅 Playbook & 7-dagen plan (PRO)")

    with st.expander("📅 Playbook & exports openen", expanded=False):
        if not is_pro():
            locked_section("Playbook & Exports", pattern="exports")
        else:
            if d.empty:
                st.info(tr("no_data"))
            else:
                # ---------- Kleine helpers om playbook & weekplan te bouwen ----------
                def generate_playbook(d: pd.DataFrame) -> Dict[str, str]:
                    hours = _best_hours(d, n=3)
                    htxt = ", ".join([f"{h:02d}:00" for h in hours])

                    tr_df = trending_hashtags(d, days_window=14)
                    top_tag = (
                        tr_df.head(1).index[0]
                        if tr_df is not None and not tr_df.empty
                        else "#viral"
                    )

                    return dict(
                        beste_tijden=htxt,
                        top_hashtag=top_tag,
                        hook_stijl="shock",
                        actie="Repost je best scorende video en maak een vervolg.",
                    )

                def generate_week_plan(d: pd.DataFrame) -> pd.DataFrame:
                    hours = _best_hours(d, n=3)
                    h1, h2, h3 = (hours + [19, 20, 18])[:3]

                    tr_df = trending_hashtags(d, days_window=14)
                    trend_tag = (
                        tr_df.head(1).index[0]
                        if tr_df is not None and not tr_df.empty
                        else "#darkfacts"
                    )

                    rows = [
                        ["Ma", "Repost topvideo",       f"{h1:02d}:00", "Wat bijna niemand weet…",      f"{trend_tag} #tiktoknl #fyp", "Herbruik"],
                        ["Di", "Nieuw idee (trending)", f"{h2:02d}:00", "Dit klinkt gek, maar…",        f"{trend_tag} #psychology",    "Test"],
                        ["Wo", "Reacties beantwoorden", "—",           "—",                             "—",                          "Engage"],
                        ["Do", "A/B-test A",            f"{h1:02d}:00", "Niemand vertelt je dit…",      "#viral #nl",                 "Test"],
                        ["Vr", "A/B-test B",            f"{h2:02d}:00", "De meeste mensen weten niet…",  "#facts #dark",               "Test"],
                        ["Za", "Behind the scenes",     f"{h3:02d}:00", "Zo maak ik m’n video’s…",       "#creator #real",             "Connect"],
                        ["Zo", "Weekoverzicht",         f"{h1:02d}:00", "Deze video ging viral!",        "#recap #weekend",            "Reflectie"],
                    ]

                    return pd.DataFrame(
                        rows,
                        columns=[
                            "Dag",
                            "Type",
                            "Tijd",
                            "Hook/Caption",
                            "Hashtags",
                            "Doel",
                        ],
                    )

                # ---------- Playbook data op basis van jouw account ----------
                pb = generate_playbook(d)

                with st.container(border=True):
                    st.markdown("#### 📘 Playbook op basis van je data")
                    st.caption(
                        "Dit is je compacte groei-playbook voor deze week. "
                        "Gebruik het als kapstok voor je contentplanning."
                    )

                    c1, c2, c3, c4 = st.columns(4)
                    c1.markdown(
                        "<div class='kpi-card'><div class='kpi-label'>Beste tijden</div>"
                        f"<div class='kpi-value'>{pb['beste_tijden']}</div></div>",
                        unsafe_allow_html=True,
                    )
                    c2.markdown(
                        "<div class='kpi-card'><div class='kpi-label'>Top-hashtag</div>"
                        f"<div class='kpi-value'>{pb['top_hashtag']}</div></div>",
                        unsafe_allow_html=True,
                    )
                    c3.markdown(
                        "<div class='kpi-card'><div class='kpi-label'>Hook-stijl</div>"
                        f"<div class='kpi-value'>{pb['hook_stijl']}</div></div>",
                        unsafe_allow_html=True,
                    )
                    c4.markdown(
                        "<div class='kpi-card'><div class='kpi-label'>Actie</div>"
                        "<div class='kpi-value'>Nu doen</div></div>",
                        unsafe_allow_html=True,
                    )

                    st.info(pb["actie"])

                st.markdown("")  # kleine ruimte

                # ---------- 7-dagen postplan ----------
                with st.container(border=True):
                    st.markdown("#### 🗓 7-dagen postplan")
                    st.caption(
                        "Een simpel schema voor de komende 7 dagen. "
                        "Zie het als suggestie: je kunt de hooks/uren altijd nog tweaken."
                    )

                    plan = generate_week_plan(d)
                    st.dataframe(plan, use_container_width=True, hide_index=True)

                    colx1, colx2 = st.columns(2)

                    with colx1:
                        dt_str = pd.Timestamp.today().strftime("%Y-%m-%d")
                        st.download_button(
                            "⬇️ Exporteer plan (CSV)",
                            data=plan.to_csv(index=False).encode("utf-8"),
                            file_name=f"postplan_7_dagen_{dt_str}.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )

                    with colx2:
                        txt = io.StringIO()
                        txt.write("PLAYBOOK\n")
                        for k, v in pb.items():
                            txt.write(f"{k}: {v}\n")
                        st.download_button(
                            "⬇️ Exporteer playbook (TXT)",
                            data=txt.getvalue().encode("utf-8"),
                            file_name="playbook.txt",
                            mime="text/plain",
                            use_container_width=True,
                        )

                    st.caption(
                        "Tip: print dit schema desnoods uit of zet het in je notities, "
                        "zodat je elke dag één duidelijke TikTok-actie hebt."
                    )

# ------------------------------ Instellingen -------------------------------
with tab_settings:
    st.subheader("⚙️ Instellingen")
    st.caption(
        "Hou het simpel: stel hier in hoe PostAi test, post en je op de hoogte houdt. "
        "Alles is later weer aan te passen."
    )

    # Kleine helpers voor laden / bewaren
    def _load_settings() -> dict:
        if SETTINGS_FILE.exists():
            try:
                return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        # Default waardes
        return {
            "auto_experiments": True,
            "auto_post_mode": "review",
            "alert_channel": "email",
            "lang": "nl",
            "data_retention_days": 180,
        }

    def _save_settings(cfg: dict) -> bool:
        try:
            SETTINGS_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            return True
        except Exception:
            return False

    cfg = _load_settings()

    # ====================== Card: Algemene instellingen ======================
    with st.container(border=True):
        st.markdown("#### ⚙️ Basis van je account")
        st.caption("Kies hoe PostAi test, post en meldingen verstuurt.")

        col1, col2 = st.columns(2)

        # -------- Linkerkolom: gedrag & taal --------
        with col1:
            cfg["auto_experiments"] = st.toggle(
                "Slim testen (A/B → slimste wint)",
                value=cfg.get("auto_experiments", True),
                help="Automatisch varianten testen en vaker posten wat het beste werkt.",
            )

            cfg["auto_post_mode"] = st.selectbox(
                "Automatisch posten",
                ["review", "off"],
                index=["review", "off"].index(cfg.get("auto_post_mode", "review")),
                help=(
                    "‘review’: jij keurt alles eerst goed. "
                    "‘off’: er wordt nooit automatisch gepost."
                ),
            )

            cfg["lang"] = st.selectbox(
                "Taal van de interface",
                ["nl", "en"],
                index=["nl", "en"].index(cfg.get("lang", "nl")),
            )

        # -------- Rechterkolom: alerts & data --------
        with col2:
            cfg["alert_channel"] = st.selectbox(
                "Alerts kanaal",
                ["email"],
                index=0,
                help="Kanaal voor meldingen over tests en adviezen.",
            )

            cfg["data_retention_days"] = st.number_input(
                "Data bewaren (dagen)",
                min_value=30,
                max_value=365,
                value=int(cfg.get("data_retention_days", 180)),
                help="Na deze periode mogen we oude data opschonen.",
            )

        # E-mailveld over de volle breedte eronder
        st.session_state["alert_email"] = st.text_input(
            "E-mail voor alerts",
            value=st.session_state.get("alert_email", ""),
            placeholder="bijv. creator@jouwdomein.nl",
            help="Alleen gebruikt als jij alerts inschakelt.",
        )

        # Opslaan-knop onderaan de card
        if st.button("💾 Bewaar instellingen", use_container_width=True, type="primary"):
            if _save_settings(cfg):
                st.success("Instellingen opgeslagen.")
            else:
                st.error("Kon instellingen niet opslaan. Probeer het later opnieuw.")

    st.markdown("---")

        # ====================== Card: Branding (PRO) ======================
    with st.container(border=True):
        st.markdown("#### 🎨 Branding")
        st.caption(
            "Maak PostAi herkenbaar voor jouw merk. We gebruiken deze stijl in exports en de interface."
        )

        if not is_pro():
            locked_section("Branding", pattern="branding")
        else:
            b1, b2 = st.columns(2)

            # Merkkleur
            with b1:
                color = st.color_picker(
                    "Merkkleur",
                    value=THEME_COLOR,
                    help="Kies de hoofdkleur van je merk of kanaal.",
                )
                if st.button("💾 Bewaar merkkleur", key="save_brand_color", use_container_width=True):
                    if _save_brand_color(color):
                        st.success("Kleur opgeslagen. Herlaad de pagina om alles te updaten.")
                    else:
                        st.error("Kon kleur niet opslaan. Probeer het later opnieuw.")

            # Logo
            with b2:
                st.markdown("Logo")
                if LOGO_BYTES:
                    st.image(LOGO_BYTES, caption="Huidig logo", width=90)
                    if st.button(
                        "🗑 Verwijder logo",
                        key="remove_brand_logo",
                        use_container_width=True,
                    ):
                        if _remove_brand_logo():
                            st.success("Logo verwijderd. Herlaad de pagina.")
                        else:
                            st.error("Kon logo niet verwijderen.")
                else:
                    lf = st.file_uploader(
                        "Upload logo (PNG)",
                        type=["png"],
                        help="Vierkant of horizontaal logo werkt het best.",
                    )
                    if lf is not None:
                        if _save_brand_logo(lf):
                            st.success("Logo opgeslagen. Herlaad de pagina om het te zien.")
                        else:
                            st.error("Kon logo niet opslaan. Controleer het bestand.")

    st.markdown("---")

    # =========================== Card: Licentie ==============================
with st.container(border=True):
    st.markdown("#### 🔑 Licentie & PRO")
    st.caption("Bekijk of je PRO draait en beheer hier je licentiesleutel.")

    if is_pro():
        st.success("Je draait momenteel **PRO**. Bedankt voor je vertrouwen! 🎉")

        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.caption("Je hebt toegang tot alle PRO-functies (coach, playbook, exports, branding).")
        with col_r:
            if st.button(
                "Deactiveer PRO",
                key="deactivate_license",
                use_container_width=True,
                help="Verwijdert de huidige licentie van dit apparaat.",
            ):
                ok = _remove_license()
                if ok:
                    st.toast("Licentie verwijderd. PRO is gedeactiveerd.")
                else:
                    st.toast("Kon licentie niet verwijderen, maar instellingen worden opnieuw geladen…")
                st.experimental_rerun()
    else:
        key = st.text_input(
            "Licentiesleutel",
            value=license_key(),
            placeholder="Voer hier je PRO-sleutel in",
            help="Je ontvangt deze sleutel na aankoop van PRO.",
        )

        col_l, col_r = st.columns([2, 1])
        with col_l:
            if st.button(
                "🔓 Activeer PRO",
                use_container_width=True,
                key="activate_license",
            ):
                k = key.strip()
                if not k:
                    st.warning("Vul eerst een geldige sleutel in.")
                else:
                    ok = _write_license(k)
                    if ok:
                        st.toast("Licentie opgeslagen. PRO wordt nu geactiveerd…")
                        st.experimental_rerun()
                    else:
                        st.error("Kon licentie niet opslaan. Controleer je sleutel.")
        with col_r:
            st.link_button(
                "✨ Koop PRO",
                LEMON_CHECKOUT_URL,
                use_container_width=True,
            )

        st.caption(
            "Nog geen licentie? Met PRO krijg je o.a. toegang tot de volledige coach, playbook en branding."
        )

    st.markdown("---")

    # ====================== Card: Data opschonen =============================
    with st.container(border=True):
        st.markdown("#### 🧹 Data opschonen (privacy)")
        st.caption(
            "Verwijder alle lokale CSV’s en app-state van deze installatie. "
            "Handig als je schoon wilt beginnen of je apparaat deelt."
        )

        if st.button(
            "🧹 Verwijder lokale data (CSV / archief / state)",
            use_container_width=True,
            key="wipe_local_data",
        ):
            try:
                # Alle CSV’s in de data-map verwijderen
                for p in DATA_DIR.glob("*.csv"):
                    p.unlink(missing_ok=True)

                # Kernbestanden verwijderen
                for p in [
                    LATEST_FILE,
                    ALERT_STATE_FILE,
                    SYNC_STATE_FILE,
                    POST_QUEUE_FILE,
                    COACH_STATE_FILE,
                ]:
                    if p.exists():
                        p.unlink()

                st.success("Alle lokale data en states zijn verwijderd. Je draait nu een schone installatie.")
            except Exception as e:
                st.error(f"Kon data niet verwijderen: {e}")

# ------------------------------ Legal blok -------------------------------
if REVIEW_MODE:
    with st.expander("📜 Legal & TikTok review info", expanded=False):
        base = _get_public_base_url() or "https://postai.bouwmijnshop.nl"
        requested_scopes = getconf("TIKTOK_SCOPES", "user.info.basic").strip()

        st.markdown(
            f"""
**Basisgegevens**

- **Website (deze app):** {base}  
- **Redirect URI:** `{base}/`  
- **Aangevraagde scopes:** `{requested_scopes}`  

**Wat doet de app?**

- Inloggen via TikTok (OAuth)  
- Eigen analytics in een dashboard tonen  
- Geen automatische plaatsingen zonder expliciete toestemming  

**Juridisch & support**

- Terms (in-app): [`?page=terms`](?page=terms)  
- Privacy (in-app): [`?page=privacy`](?page=privacy)  
- Officiële site: [Voorwaarden](https://www.bouwmijnshop.nl/pages/onze-voorwaarden) · [Privacy](https://www.bouwmijnshop.nl/pages/privacy)  
- Support: [support@bouwmijnshop.nl](mailto:support@bouwmijnshop.nl)
""",
            unsafe_allow_html=True,
        )

# ----------------------------- Footer badges -------------------------------
st.markdown(
    f"""
<style>
.footer-trust {{
    margin: 1.5rem 0 0.5rem;
    text-align: center;
    font-size: 0.8rem;
    color: #6b7280;
}}
.footer-trust span {{
    margin: 0 0.45rem;
    white-space: nowrap;
}}
</style>
<div class="footer-trust">
  <span>🛡️ {tr('trust1')}</span>
  <span>📄 {tr('trust2')}</span>
  <span>🎁 {tr('trust3')}</span>
  <span>🎯 {tr('trust4')}</span>
</div>
""",
    unsafe_allow_html=True,
)

# ============================== Mini-footer ===============================
def _mini_footer():
    year = datetime.now().year
    st.markdown(
        f"""
<style>
.mini-footer {{
    margin: 0.25rem 0 1.25rem;
    text-align: center;
    font-size: 0.78rem;
    color: #9ca3af;
}}
.mini-footer a {{
    color: #4b5563;
    text-decoration: none;
    border-bottom: 1px dotted #cbd5e1;
}}
.mini-footer a:hover {{
    border-bottom-style: solid;
    color: #111827;
}}
.mini-footer .sep {{
    margin: 0 .35rem;
    color: #d1d5db;
}}
</style>
<div class="mini-footer">
  © {year} PostAi
  <span class="sep">·</span><a href="?page=privacy">Privacy</a>
  <span class="sep">·</span><a href="?page=terms">Voorwaarden</a>
  <span class="sep">·</span><a href="mailto:support@bouwmijnshop.nl">Support</a>
</div>
""",
        unsafe_allow_html=True,
    )

_mini_footer()

# ----------------------------- Chat widget (schoon / minimaal) -----------------------------
import streamlit.components.v1 as components

CHAT_SERVER = "https://chatbot-2-0-3v8l.onrender.com"

components.html(
    f"""
<link rel="stylesheet" href="{CHAT_SERVER}/chat-widget.css">
<script src="{CHAT_SERVER}/chat-boot.js"
        data-server="{CHAT_SERVER}"
        data-css="{CHAT_SERVER}/chat-widget.css"></script>
""",
    height=0,
    scrolling=False,
)
st.markdown(
    """
<style>
/* Streamlit chrome verbergen */
#MainMenu { visibility:hidden; }
footer { visibility:hidden; }

header[data-testid="stHeader"] { height:0; visibility:hidden; }
div[data-testid="stToolbar"] { display:none; }
div.block-container { padding-top:14px !important; }

/* Belangrijk: CSS-inspector overlay mag geen kliks blokkeren */
#css-inspector-overlay {
    pointer-events: none !important;
}

/* NIETS anders blokkeren of overriden – chat en cookies met rust laten */
</style>
""",
    unsafe_allow_html=True,
)
