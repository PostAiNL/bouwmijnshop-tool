# app.py — PostAi (TikTok Growth Agent) • PRO-ready + AI Coach/Generator/Chat
from __future__ import annotations

import os, re, io, json, uuid, base64, time, logging, urllib.parse
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import streamlit as st

# --------------------------------- Optioneel ---------------------------------
try:
    import altair as alt
    HAS_ALTAIR = True
except Exception:
    HAS_ALTAIR = False

# =============================== Basis / Config ===============================
APP_NAME  = "PostAi — TikTok Growth Agent"
APP_DIR   = Path(__file__).resolve().parent
DATA_DIR  = APP_DIR / "auto"
BRAND_DIR = APP_DIR / "branding"
DATA_DIR.mkdir(exist_ok=True); BRAND_DIR.mkdir(exist_ok=True)

LATEST_FILE      = DATA_DIR / "analytics_latest.csv"
SETTINGS_FILE    = APP_DIR / "settings.json"
LICENSE_FILE     = APP_DIR / "license.key"
ALERT_STATE_FILE = APP_DIR / "last_alert.txt"
SYNC_STATE_FILE  = APP_DIR / "last_sync.txt"
POST_QUEUE_FILE  = DATA_DIR / "post_queue.json"
COACH_STATE_FILE = DATA_DIR / "coach_state.json"  # ⬅️ nieuw

LEMON_CHECKOUT_URL = "https://your-lemon-squeezy-checkout.link/PRODUCT"  # vervang

TZ = "Europe/Amsterdam"
REVIEW_MODE = os.getenv("REVIEW_MODE", "0").strip() == "1"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("postai")

def getconf(key: str, default: str = "") -> str:
    """Eerst uit st.secrets, dan uit env, anders default."""
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)

# ------------------------------- Dev helpers ---------------------------------
from urllib.parse import urlparse
DEV_ALLOW_HTTP_LOCAL = True

def _is_local_url(url: str) -> bool:
    try:
        u = urlparse(url)
        return u.hostname in ("localhost", "127.0.0.1")
    except Exception:
        return False

def _get_public_base_url() -> str:
    url = getconf("APP_PUBLIC_URL", "").strip().rstrip("/")
    if not url: return ""
    if url.startswith("https://"): return url
    if DEV_ALLOW_HTTP_LOCAL and _is_local_url(url) and url.startswith("http://"):
        return url
    st.error("Misconfiguratie: **APP_PUBLIC_URL** moet https zijn (of http://localhost bij lokaal testen).")
    return ""

def has_oauth_config() -> bool:
    base = getconf("APP_PUBLIC_URL", "").strip()
    key  = getconf("TIKTOK_CLIENT_KEY", "").strip()
    if not base or not key: return False
    if base.startswith("https://"): return True
    return DEV_ALLOW_HTTP_LOCAL and _is_local_url(base) and base.startswith("http://")

def build_tiktok_auth_url() -> str:
    client_key = getconf("TIKTOK_CLIENT_KEY", "").strip()
    scopes     = getconf("TIKTOK_SCOPES", "user.info.basic").strip()
    base_url   = _get_public_base_url()
    if not client_key or not base_url: return ""
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
    return "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

# --------------------------- Licentie / PRO status ----------------------------
def _read_license() -> Tuple[str, bool]:
    try:
        if LICENSE_FILE.exists():
            key = LICENSE_FILE.read_text(encoding="utf-8").strip()
            if key and key.upper() != "DEMO": return key, True
    except Exception:
        pass
    return "", False

def _write_license(key: str) -> bool:
    try:
        LICENSE_FILE.write_text(key.strip(), encoding="utf-8"); return True
    except Exception:
        return False

def _remove_license() -> bool:
    try:
        if LICENSE_FILE.exists(): LICENSE_FILE.unlink(); return True
    except Exception:
        return False

ENV_LICENSE = getconf("LICENSE_KEY", "").strip()
if ENV_LICENSE:
    LICENSE_KEY = ENV_LICENSE; IS_PRO = True
else:
    LICENSE_KEY, IS_PRO = _read_license()

# ============================== Streamlit Setup ===============================
st.set_page_config(
    page_title=f"{APP_NAME} — {'PRO' if IS_PRO else 'DEMO'}",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# OAuth callback (minimal)
qp = st.query_params
if "error" in qp:
    st.error(f"❌ TikTok OAuth error: {qp.get('error_description', qp.get('error'))}")
elif "code" in qp:
    state_ok = (qp.get("state", "") == st.session_state.get("_tiktok_state"))
    if REVIEW_MODE:
        st.success(f"✅ TikTok OAuth code ontvangen (state ok: {state_ok}).")
        st.session_state["tik_code"] = qp.get("code")
    else:
        st.success("✅ Ingelogd via TikTok.")
    st.session_state["tik_state_ok"] = state_ok

# ================================ Branding ====================================
def _load_branding():
    color = st.session_state.get("brand_color", "#2563eb")
    p = BRAND_DIR / "color.txt"
    if p.exists():
        try: color = p.read_text(encoding="utf-8").strip() or color
        except Exception: pass
    logo_path = BRAND_DIR / "logo.png"
    logo_bytes = logo_path.read_bytes() if logo_path.exists() else None
    return color, logo_bytes

def _save_brand_color(color_hex: str) -> bool:
    try:
        (BRAND_DIR / "color.txt").write_text(color_hex.strip(), encoding="utf-8")
        st.session_state["brand_color"] = color_hex.strip(); return True
    except Exception:
        return False

def _save_brand_logo(file) -> bool:
    try: (BRAND_DIR / "logo.png").write_bytes(file.read()); return True
    except Exception: return False

def _remove_brand_logo() -> bool:
    try:
        p = BRAND_DIR / "logo.png"
        if p.exists(): p.unlink(); return True
    except Exception:
        return False

THEME_COLOR, LOGO_BYTES = _load_branding()

# ================================== CSS =======================================
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
html { color-scheme: light; }
body, [data-testid="stAppViewContainer"] { background: var(--bg) !important; color: var(--text) !important; }
section[data-testid="stSidebar"] > div:first-child { background: var(--head); border-right:1px solid var(--card-border); }
.block-container { max-width:1200px; padding-top:14px; }
section[data-testid="stSidebar"] { width:260px !important; }
.accent { color:var(--brand); }
h1,h2,h3 { letter-spacing:-.01em; color: var(--text); }

/* Cards */
.hero-card, .kpi-card { border:1px solid var(--card-border); border-radius:16px; padding:14px 16px; background: var(--card); box-shadow:0 6px 18px rgba(0,0,0,.06); color: var(--text); }
.kpi-label { color:var(--muted); font-size:.85rem; margin-bottom:4px; }
.kpi-value { font-size:1.35rem; font-weight:700; color: var(--text); }
.chip { display:inline-block; padding:4px 10px; border:1px solid var(--ring); border-radius:999px; margin-right:6px; margin-bottom:6px; font-size:.8rem; background: var(--card); color: var(--text); }
.kpi-gap { margin-top:10px; margin-bottom:14px; }

/* Buttons */
.stButton>button { transition:transform .12s ease, box-shadow .12s ease, opacity .2s ease; border-radius:12px; font-weight:700; }
.stButton>button:hover { transform:translateY(-1px); box-shadow:0 6px 16px rgba(0,0,0,.06); }
.primary-btn>button { background:var(--brand); color:#fff; border:1px solid var(--brand); height:50px; font-size:1.05rem; }
.soft-btn>button { background:var(--card); border:1px solid var(--ring); color: var(--text); }

/* Inputs */
.stSelectbox div[role="combobox"], .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea { background: var(--card) !important; color: var(--text) !important; border:1px solid var(--card-border) !important; border-radius:12px !important; }
label, .stCheckbox, .stRadio, .stMetric, .stMarkdown p { color: var(--text) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { position:sticky; top:0; z-index:5; background: var(--head); padding-top:6px; border-bottom:1px solid var(--card-border); }

/* Progress / bars */
.stProgress > div > div { background: var(--brand) !important; }
.stProgress > div { background: var(--track) !important; border-radius:8px; }

/* Dataframes */
.stDataFrame, .stTable { background: var(--card) !important; color: var(--text) !important; }
.dataframe td, .dataframe th { border-color: var(--card-border) !important; }

/* Confidence bar */
.nbabarshell { margin:8px 0;height:8px;background:var(--track);border-radius:8px; position:relative; }
.nbabar { height:100%;background:#22c55e;border-radius:8px; }
.nbalabel { position:absolute; right:8px; top:-18px; font-size:.8rem; color:var(--muted); }

/* Skeleton */
.skeleton { position:relative; overflow:hidden; background:var(--skeleton); border-radius:14px; min-height:64px; border:1px solid var(--ring); }
.skeleton::after { content:""; position:absolute; inset:0; background:linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,.25) 50%, rgba(255,255,255,0) 100%); transform:translateX(-100%); animation:shimmer 1.15s infinite; }
@keyframes shimmer { 100% { transform:translateX(100%); } }

/* Pro badge & lock preview */
.pro-badge { position:fixed; top:8px; right:12px; z-index:9999; color:#fff; padding:6px 12px; border-radius:999px; font-weight:700; background:#10b981; }
.locked { position:relative; filter:blur(1.2px) saturate(.8); }
.locked::after { content:"🔒 PRO — Ontgrendel om dit te gebruiken"; position:absolute; inset:0; display:flex; align-items:center; justify-content:center; color:#111827; background:rgba(255,255,255,.65); border:1px dashed var(--card-border); border-radius:16px; font-weight:700; }
"""
    st.markdown("<style>" + vars_block + base_css + "</style>", unsafe_allow_html=True)
    st.markdown(f"<div class='pro-badge'>{'PRO' if pro else 'DEMO'}</div>", unsafe_allow_html=True)

THEME_COLOR, LOGO_BYTES = _load_branding()
_inject_css(THEME_COLOR, IS_PRO)

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
        "juli": 7, "augustus": 8, "september": 9, "oktober": 10, "november": 12 if False else 11, "december": 12
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

    lower = {_nk(c): c for c in df.columns}
    col = {
        "caption": _pick(lower, "videotitle", "videotitel", "caption", "tekst", "title", "titel", "omschrijving", "beschrijving"),
        "views": _pick(lower, "totalviews", "views", "plays", "weergaven", "videoweergaven", "videoviews"),
        "likes": _pick(lower, "totallikes", "likes", "hearts", "hartjes", "vindikleuks"),
        "comments": _pick(lower, "totalcomments", "comments", "reacties", "opmerkingen"),
        "shares": _pick(lower, "totalshares", "shares", "gedeeld", "keergedeeld", "delen"),
        "date": _pick(lower, "posttime", "time", "date", "datum", "createdat", "publicatiedatum", "gepubliceerddatum"),
        "link": _pick(lower, "videolink", "videourl", "video link", "link", "url"),
        "videoid": _pick(lower, "videoid", "awemeid", "id"),
        "author": _pick(lower, "author", "username", "account"),
    }

    d = df.copy()

    if col["caption"]:
        raw = d[col["caption"]].astype(str)
        d["Hashtags"] = raw.apply(lambda s: " ".join(re.findall(r"#\w+", s))).replace("", np.nan)
    else:
        d["Hashtags"] = np.nan

    d["Views"] = d[col["views"]].apply(_to_int_safe) if col["views"] else np.nan
    d["Likes"] = d[col["likes"]].apply(_to_int_safe) if col["likes"] else np.nan
    d["Comments"] = d[col["comments"]].apply(_to_int_safe) if col["comments"] else np.nan
    d["Shares"] = d[col["shares"]].apply(_to_int_safe) if col["shares"] else np.nan

    if col["date"]:
        raw_dates = d[col["date"]].astype(str).str.strip(" '\"\t\r\n,.;")
        parsed = pd.to_datetime(raw_dates, dayfirst=True, errors="coerce", utc=True)
        parsed = parsed.where(parsed.notna(), pd.to_datetime(raw_dates.apply(_parse_nl_date), errors="coerce", utc=True))
        try:
            parsed = parsed.dt.tz_convert(TZ)
        except Exception:
            pass
        parsed = parsed.apply(lambda x: x.replace(hour=12) if pd.notna(x) and getattr(x, "hour", 0) == 0 else x)
        d["Datum"] = parsed
    else:
        d["Datum"] = pd.NaT

    d["Video link"] = ""
    if col["link"]:
        urls = d[col["link"]].astype(str)
        d["Video link"] = urls.where(urls.map(_is_tiktok_url), "")
    elif col["videoid"] and col["author"]:
        base = d[col["author"]].fillna("").astype(str).str.lstrip("@").str.strip()
        vid = d[col["videoid"]].fillna("").astype(str).str.strip()
        d["Video link"] = "https://www.tiktok.com/@" + base + "/video/" + vid

    keep = ["Hashtags", "Video link", "Views", "Likes", "Comments", "Shares", "Datum"]
    return d[keep].copy()

def add_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Voegt Like/Comment/Share rates, Engagement %, Velocity, Recency, Score en Virality toe."""
    if df is None or df.empty:
        return pd.DataFrame()

    d = df.copy()
    for c in ["Views", "Likes", "Comments", "Shares"]:
        if c not in d.columns: d[c] = np.nan

    views = pd.to_numeric(d["Views"], errors="coerce")
    likes = pd.to_numeric(d["Likes"], errors="coerce")
    comments = pd.to_numeric(d["Comments"], errors="coerce")
    shares = pd.to_numeric(d["Shares"], errors="coerce")

    denom = views.replace(0, np.nan)
    d["Like rate"]    = (likes    / denom).fillna(0.0)
    d["Comment rate"] = (comments / denom).fillna(0.0)
    d["Share rate"]   = (shares   / denom).fillna(0.0)
    d["Engagement %"] = d["Like rate"] + d["Comment rate"] + d["Share rate"]

    ds = pd.to_datetime(d.get("Datum"), errors="coerce")
    try: ds = ds.dt.tz_localize(None)
    except Exception: pass

    today = pd.Timestamp.today().normalize()
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

    d["Score"] = score.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    d["Virality"] = (d["Score"] * 100).round(0)
    return d

@st.cache_data(show_spinner=False, ttl=600)
def trending_hashtags(d: pd.DataFrame, days_window: int = 14) -> pd.DataFrame:
    if d is None or d.empty:
        return pd.DataFrame()

    df = d.copy()
    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
    try: df["Datum"] = df["Datum"].dt.tz_localize(None)
    except Exception: pass
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
    if d is None or d.empty: return [19, 20, 18][:n]
    dt = pd.to_datetime(d["Datum"], errors="coerce")
    try: dt = dt.dt.tz_localize(None)
    except Exception: pass
    v = pd.to_numeric(d["Views"], errors="coerce")
    v_cap = v.clip(upper=v.quantile(0.95))
    days_ago = (pd.Timestamp.today().normalize() - dt.dt.normalize()).dt.days.clip(lower=0).fillna(30)
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
        next_best="Jouw groeiaanbeveling",
        review_queue="Review-wachtrij",
        add_queue="Zet in review-wachtrij",
        trust1="GDPR-proof", trust2="CSV/XLSX", trust3="7 dagen gratis", trust4="Gemaakt voor TikTok",
    )
    return I18N.get(k, k)

# =============================== Sidebar =====================================
with st.sidebar:
    # PRO/DEMO badge
    if IS_PRO:
        st.markdown("<div class='chip' style='background:#ecfdf5;border-color:#a7f3d0;'>✅ Je draait <b>PRO</b>. Bedankt! 🎉</div>", unsafe_allow_html=True)
    else:
        st.info("🔓 Je draait **DEMO** (7 dagen). Sommige functies zijn vergrendeld.")
        st.link_button("✨ Ontgrendel PRO", LEMON_CHECKOUT_URL, use_container_width=True)

    # TikTok koppeling
    st.markdown("### 🔗 TikTok koppelen")
    _login_url = build_tiktok_auth_url()
    if _login_url:
        st.link_button("Log in met TikTok", _login_url, use_container_width=True)
        with st.popover("Welke data gebruiken we?"):
            st.caption("Alleen **inloggen** en je profielfoto/naam. We posten **niets** en lezen geen vriendenlijst. Privacy-first.")
    else:
        base = getconf("APP_PUBLIC_URL", "").strip() or "(leeg)"
        key  = getconf("TIKTOK_CLIENT_KEY", "").strip()
        if not base: st.warning("APP_PUBLIC_URL ontbreekt. Lokaal mag `http://localhost:8501`.")
        elif not (base.startswith("https://") or (DEV_ALLOW_HTTP_LOCAL and _is_local_url(base) and base.startswith("http://"))):
            st.warning("APP_PUBLIC_URL moet https (of http://localhost bij lokaal testen).")
        if not key: st.warning("TIKTOK_CLIENT_KEY ontbreekt.")
        st.caption("Zet **APP_PUBLIC_URL** en **TIKTOK_CLIENT_KEY** als env vars of in `.streamlit/secrets.toml`.")
    if st.session_state.get("tik_code"):
        st.caption("Status: OAuth code ontvangen ✅ (alleen login & display).")
    st.markdown("---")

    # Data
    st.markdown("### 📊 Data")
    if st.button("📥 Haal analytics op", use_container_width=True):
        res = run_manual_fetch(); st.toast(res["msg"] if res["ok"] else f"❌ {res['msg']}")
    if st.button("🎯 Probeer met voorbeelddata", use_container_width=True):
        rng = pd.date_range(end=pd.Timestamp.today().normalize(), periods=35, freq="D")
        np.random.seed(42); rows = []
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
            d_ = d_ + pd.Timedelta(hours=int(np.random.choice([12, 14, 16, 18, 20, 0], p=[.25, .2, .18, .15, .12, .1])))
            rows.append(dict(caption=np.random.choice(tags_pool), views=views, likes=likes, comments=comments, shares=shares, date=d_, videolink=""))
        df_demo = pd.DataFrame(rows)
        df_demo.to_csv(LATEST_FILE, index=False)
        st.session_state["df"] = df_demo
        st.session_state["demo_active"] = True
        st.toast("✅ Demo-data geladen")

    st.markdown("### 📁 Upload bestand")
    up = st.file_uploader("Upload je TikTok CSV/XLSX (of gebruik demo)", type=["csv", "xlsx"])
    if up is not None:
        try:
            df_up = _smart_read_any(up)
            try: up.seek(0)
            except Exception: pass
            df_up.to_csv(LATEST_FILE, index=False)
            st.session_state["df"] = df_up; st.session_state["demo_active"] = False
            st.success(f"✅ Bestand opgeslagen ({up.name}) — {len(df_up):,} rijen")
            base_chk = normalize_per_post(df_up)
            need = [c for c in ["Views","Likes","Comments","Shares","Datum"] if c not in base_chk.columns]
            if need: st.warning("We missen kolommen: " + ", ".join(need) + ". Gebruik ons sjabloon (zie hoofdscherm).")
        except Exception as e:
            st.error(f"Kon bestand niet verwerken: {e}")

# =============================== Header =======================================
c1, c2 = st.columns([1, 8])
with c1:
    if LOGO_BYTES:
        b64 = base64.b64encode(LOGO_BYTES).decode("ascii")
        st.markdown(f"<img src='data:image/png;base64,{b64}' style='height:60px;border-radius:12px;' />", unsafe_allow_html=True)
with c2:
    st.markdown(f"<h1 style='margin:0;font-size:1.6rem;'><span class='accent'>PostAi</span> — TikTok Growth Agent — {'PRO' if IS_PRO else 'DEMO'}</h1>", unsafe_allow_html=True)
    st.caption("Slimmer groeien met data. **Dare to know.**")

# ============================= Onboarding bar ================================
def _onboarding_bar(step: int):
    labels = ["Upload", "Analyse", "A/B test", "Playbook", "Resultaat"]
    filled = min(step, len(labels))
    frac = filled / len(labels)
    st.progress(frac, text=" ➜ ".join([("✅ "+l) if i < filled else l for i,l in enumerate(labels)]))

# ============================== Uitleg =======================================
with st.expander("Uitleg in het kort (altijd zichtbaar)", expanded=False):
    st.markdown("""
**Zo werkt het in 1 minuut (zonder vakjargon):**  
1) **Upload** je CSV/XLSX of kies **Voorbeelddata**.  
2) Klik **Start analyse** — wij kijken: *wat werkt? wanneer posten?*  
3) **A/B-planner**: test 2 hooks, 2 hashtag-mixen en 2 tijden.  
4) **Playbook & Plan**: simpel weekplan met beste tijden.  
5) *(PRO)* **AI Coach**, **Caption generator**, **Chat-assistent**, **PDF/e-mail**.
""")

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
        if prev is None or not np.isfinite(prev) or prev == 0: return "—", None
        diff = ((curr - prev) / prev) * 100
        return f"{diff:+.1f}%", ("↑" if diff >= 0 else "↓")
    except Exception: return "—", None

def _kpi_row(d: pd.DataFrame, key_ns: str = "top"):
    st.markdown("<div class='kpi-gap'></div>", unsafe_allow_html=True)
    if d is None or d.empty:
        a,b,c = st.columns(3)
        for col in (a,b,c): col.markdown("<div class='skeleton'></div>", unsafe_allow_html=True)
        return
    period_options = [7,14,28]
    kpi_left, kpi_right = st.columns([4,1])
    with kpi_right:
        sel = st.selectbox("Periode", period_options, index=0, key=f"kpi_range_{key_ns}")
    with kpi_left:
        dt = pd.to_datetime(d["Datum"], errors="coerce")
        try: dt = dt.dt.tz_localize(None)
        except Exception: pass
        now = pd.Timestamp.today().normalize()
        cur_mask = (dt >= (now - pd.Timedelta(days=sel))) & (dt <= now + pd.Timedelta(days=1))
        prev_mask = (dt >= (now - pd.Timedelta(days=2*sel))) & (dt < (now - pd.Timedelta(days=sel)))
        def _sum(df, col): return int(pd.to_numeric(df[col], errors="coerce").sum(skipna=True))
        def _mean(df, col): return float(pd.to_numeric(df[col], errors="coerce").mean(skipna=True))
        cur  = d.loc[cur_mask]
        prev = d.loc[prev_mask]
        total_views_cur  = _sum(cur, "Views") if not cur.empty else 0
        total_views_prev = _sum(prev, "Views") if not prev.empty else 0
        avg_eng_cur  = (_mean(cur, "Engagement %") * 100) if not cur.empty else 0.0
        avg_eng_prev = (_mean(prev, "Engagement %") * 100) if not prev.empty else 0.0
        vir_cur  = _mean(cur, "Virality") if not cur.empty else 0.0
        vir_prev = _mean(prev, "Virality") if not prev.empty else 0.0
        d1, a1 = _fmt_delta(total_views_cur, total_views_prev)
        d2, a2 = _fmt_delta(avg_eng_cur, avg_eng_prev)
        d3, a3 = _fmt_delta(vir_cur, vir_prev)
        c1, c2, c3 = st.columns(3)
        def _card(title, value, delta_str, arrow, icon):
            color = "#16a34a" if arrow == "↑" else ("#dc2626" if arrow == "↓" else "#6b7280")
            html = f"<div class='kpi-card'><div class='kpi-label'>{title}</div><div class='kpi-value'>{icon} {value} <span style='color:{color}'>({delta_str if delta_str!='—' else '—'})</span></div></div>"
            return html
        c1.markdown(_card(f"Totaal views ({sel}d)", f"{total_views_cur:,}".replace(",", "."), d1, a1, "👁️"), unsafe_allow_html=True)
        c2.markdown(_card(f"Gem. reactie-score ({sel}d)", f"{avg_eng_cur:.2f}%", d2, a2, "💬"), unsafe_allow_html=True)
        c3.markdown(_card(f"Virale kans ({sel}d)", f"{vir_cur:.0f}/100", d3, a3, "🔥"), unsafe_allow_html=True)
        if HAS_ALTAIR and not cur.empty:
            s1 = _sparkline(pd.to_numeric(cur["Views"], errors="coerce"))
            s2 = _sparkline(pd.to_numeric(cur["Engagement %"], errors="coerce") * 100)
            s3 = _sparkline(pd.to_numeric(cur["Virality"], errors="coerce"))
            if s1: c1.altair_chart(s1, use_container_width=False)
            if s2: c2.altair_chart(s2, use_container_width=False)
            if s3: c3.altair_chart(s3, use_container_width=False)

# ========================== Hero + Aanbeveling ===============================
def _confidence_from_data(d: pd.DataFrame) -> int:
    if d is None or d.empty: return 0
    dc = d.copy()
    dc["Datum"] = pd.to_datetime(dc.get("Datum"), errors="coerce")
    try: dc["Datum"] = dc["Datum"].dt.tz_localize(None)
    except Exception: pass
    v = pd.to_numeric(dc.get("Views"), errors="coerce")
    n = int(v.notna().sum()); size_score = float(np.clip(n/30.0, 0, 1))
    now = pd.Timestamp.today().normalize()
    n_recent = int((dc["Datum"] >= (now - pd.Timedelta(days=30))).sum())
    recency_score = float(np.clip(n_recent/15.0, 0, 1))
    have = sum(c in dc.columns for c in ["Views","Likes","Comments","Shares","Datum"])
    coverage = have/5.0
    v_clean = v.dropna()
    if len(v_clean)>=5 and v_clean.mean()>0:
        stability = 1.0 - float(np.clip(v_clean.std()/(v_clean.mean()+1e-9), 0, 1))
    else: stability = 0.5
    conf = 100*(0.4*size_score + 0.3*recency_score + 0.2*coverage + 0.1*stability)
    return int(np.clip(conf, 0, 100))

def _hero_and_nba(d: pd.DataFrame, last_sync: str, bron: str):
    with st.container(border=True):
        st.markdown(
            f"<h2 style='margin:0 0 4px 0;'>PostAi — TikTok Growth Agent</h2>"
            f"<p style='margin:0;color:#4b5563;'>Slimmer groeien met data. <i>Dare to know.</i></p>"
            f"<p style='margin:6px 0 0 0;color:#6b5563;'>⏱️ Laatste sync: <b>{last_sync}</b> · 📁 Bron: <b>{bron}</b></p>",
            unsafe_allow_html=True
        )
        left, right = st.columns([3,2])

        with left:
            _onboarding_bar(1 if (df_raw is None or df_raw.empty) else 2)
            _login_url_top = build_tiktok_auth_url()
            if _login_url_top:
                st.link_button("Log in met TikTok", _login_url_top, use_container_width=True)
            if st.button("🚀 Start analyse", key="hero_analyse_btn", use_container_width=True, type="primary"):
                with st.spinner("We kijken wat werkt…"):
                    time.sleep(0.7); st.toast("✅ Analyse voltooid — aanbeveling geüpdatet.")
            st.caption("Duurt ± 3–5 sec. We checken *wat* en *wanneer* je het beste post.")
            # Quick actions
            cc1, cc2 = st.columns(2)
            with cc1:
                tpl = pd.DataFrame([dict(
                    caption="Voorbeeld caption #hashtag",
                    views=12345, likes=678, comments=12, shares=34,
                    date=pd.Timestamp.today().normalize(), videolink="", author="@account", videoid="1234567890"
                )])
                st.download_button("⬇️ Voorbeeld-CSV", data=tpl.to_csv(index=False).encode("utf-8"), file_name="postai_template.csv", mime="text/csv", use_container_width=True)
            with cc2:
                if st.button("🎯 Laad demo-set", use_container_width=True, key="demo_btn_hero"):
                    rng = pd.date_range(end=pd.Timestamp.today().normalize(), periods=35, freq="D")
                    np.random.seed(42); rows=[]
                    tags_pool = ["#darkfacts #psychology #fyp","#love #lovestory #bf #bestie","#viral #mindblown #creepy #tiktoknl","#redthoughts #besties #bff #lovehim","#deepthought #foryou #real #reels"]
                    for d_ in rng:
                        v = np.random.randint(20_000, 500_000)
                        rows.append(dict(caption=np.random.choice(tags_pool), views=v, likes=int(v*np.random.uniform(0.04,0.18)), comments=int(v*np.random.uniform(0.003,0.02)), shares=int(v*np.random.uniform(0.002,0.015)), date=d_+pd.Timedelta(hours=int(np.random.choice([12,14,16,18,20,0], p=[.25,.2,.18,.15,.12,.1]))), videolink=""))
                    pd.DataFrame(rows).to_csv(LATEST_FILE, index=False)
                    st.session_state["df"] = pd.read_csv(LATEST_FILE); st.session_state["demo_active"] = True
                    st.toast("✅ Demo-data geladen")
            st.markdown(f"<div class='trust-row'><span class='chip badge'>🛡️ {tr('trust1')}</span><span class='chip badge'>📄 {tr('trust2')}</span><span class='chip badge'>🎁 {tr('trust3')}</span><span class='chip badge'>🎯 {tr('trust4')}</span></div>", unsafe_allow_html=True)

        with right:
            st.markdown(f"**{tr('next_best')}**")
            if d is None or d.empty:
                st.write("Upload data of laad demo om advies te krijgen.")
            else:
                best_time = _best_hours(d, n=1)[0]
                conf = _confidence_from_data(d)
                st.markdown(f"<div class='nbabarshell'><div class='nbabar' style='width:{conf}%;'></div><div class='nbalabel'>{conf}%</div></div>", unsafe_allow_html=True)
                st.markdown(f"🔥 **Post om {best_time:02d}:00.** Herpost je best scorende video. Test variant A.")
                with st.expander("Waarom?"):
                    st.write("Op basis van mediane views, deel-ratio en je topuren van de afgelopen 14 dagen.")
                st.button("🔥 Voer aanbeveling uit", use_container_width=True)

# ============================== Build & Hero ================================
base_for_hero = normalize_per_post(df_raw)
d_for_hero = add_kpis(base_for_hero) if not base_for_hero.empty else pd.DataFrame()
try:
    ts = float(SYNC_STATE_FILE.read_text().strip()) if SYNC_STATE_FILE.exists() else 0
    last_sync = datetime.fromtimestamp(ts).strftime("%d-%m %H:%M") if ts else "—"
except Exception: last_sync = "—"
bron = "DEMO" if st.session_state.get("demo_active") else ("CSV/XLSX" if LATEST_FILE.exists() else "—")

_hero_and_nba(d_for_hero, last_sync, bron)
_kpi_row(d_for_hero, key_ns="top")
st.divider()

# ================================ LLM / AI Core ==============================
# We ondersteunen OpenAI via openai-py of HTTP fallback.
def _has_openai() -> bool:
    return bool(getconf("OPENAI_API_KEY", ""))

def _default_model() -> str:
    return getconf("OPENAI_MODEL", "gpt-4o-mini")

def _ask_llm(system: str, user: str, temperature: float = 0.4, max_tokens: int = 900) -> str:
    api_key = getconf("OPENAI_API_KEY", "")
    if not api_key:
        return "⚠️ Geen OPENAI_API_KEY gevonden. Voeg je key toe in st.secrets."
    model = _default_model()
    # Probeer de moderne SDK
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role":"system","content":system},
                {"role":"user","content":user}
            ]
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        # Fallback via requests (unofficial minimal)
        import requests
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type":"application/json"}
        payload = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages":[
                {"role":"system","content":system},
                {"role":"user","content":user}
            ]
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
    """Kleine contextstring met high-level cijfers voor de AI (beperkt tokens)."""
    if d is None or d.empty:
        return "GEEN_DATA"
    df = d.copy()
    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
    df = df.sort_values("Datum", ascending=False).head(top_n)
    views = pd.to_numeric(df["Views"], errors="coerce").fillna(0)
    likes = pd.to_numeric(df["Likes"], errors="coerce").fillna(0)
    comments = pd.to_numeric(df["Comments"], errors="coerce").fillna(0)
    shares = pd.to_numeric(df["Shares"], errors="coerce").fillna(0)
    like_rate = (likes / views.replace(0, np.nan)).fillna(0).mean()
    share_rate = (shares / views.replace(0, np.nan)).fillna(0).mean()
    best_hours = _best_hours(d, n=3)
    top_tags = (df["Hashtags"].dropna().astype(str).str.split().explode()
                .pipe(lambda s: s[s.str.startswith("#")])
                .value_counts().head(5).index.tolist())
    return (
        f"posts_analyzed={len(df)}; mean_views={int(views.mean())}; "
        f"like_rate_avg={like_rate:.3f}; share_rate_avg={share_rate:.3f}; "
        f"best_hours={best_hours}; top_hashtags={top_tags}"
    )

# ---------------------------- Coach Memory (nieuw) ----------------------------
def _load_coach_state() -> dict:
    """Kennisbank + feedback + meta."""
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
    """Eenvoudige overlap-ranking (later eventueel embeddings)."""
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

    # RAG: relevante notities ophalen
    kb_hits = _rank_notes_simple(user_prompt or niche_hint or "coach", stt.get("kb", []), top_k=6)
    kb_context = "\n".join(f"- {n['text']}" for n in kb_hits) if kb_hits else "(geen)"

    # Few-shot uit geaccepteerde tips
    accepted = stt.get("accepted_tips", [])[-3:]
    fewshot = "\n".join(f"- {t}" for t in accepted) if accepted else "(geen)"

    # adaptieve temperatuur o.b.v. recente feedback
    last5 = stt.get("feedback", [])[-5:]
    neg_rate = (sum(1 for f in last5 if f.get("rating") == 0) / max(1, len(last5)))
    temp = 0.35 if neg_rate >= 0.4 else 0.4  # iets conservatiever bij veel 👎

    sys = (
        "Je bent een vriendelijke, concrete TikTok coach voor beginners. "
        "Gebruik Jip-en-Janneke taal en geef ALTIJD precies 3 bullets en een korte afsluitende actie. "
        "Focus op timing (uren/dagen), hooks/captions (hooks max 8–12 woorden), max 3 hashtags, lengte/structuur, en hergebruik van topcontent. "
        "Weeg de kennisbank en eerder geaccepteerde tips mee waar relevant."
    )
    usr = (
        f"Dataset samenvatting: {ctx}\n"
        f"Niche/onderwerp: {niche_hint or 'onbekend'}\n"
        f"Gebruikersvraag: {user_prompt or '—'}\n\n"
        f"Kennisbank (relevant):\n{kb_context}\n\n"
        f"Eerder geaccepteerde tips (few-shot):\n{fewshot}\n\n"
        "Geef 3 direct uitvoerbare tips met cijfers/uren waar logisch. "
        "Sluit af met één duidelijke actiestap."
    )
    return _ask_llm(sys, usr, temperature=temp, max_tokens=600)

# ------------------ AI Caption & Hook generator (Feature 2) ------------------
def ai_generate_captions(d: pd.DataFrame, topic: str, n_variants: int = 3, style: str = "hooky") -> List[str]:
    ctx = _summarize_dataset_for_context(d, top_n=50)
    # haal top hashtags uit dataset (max 3)
    hash_df = (d.assign(_tag=d["Hashtags"].fillna("").str.split())
                 .explode("_tag"))
    hash_df = hash_df[hash_df["_tag"].astype(str).str.startswith("#", na=False)]
    top_hashtags = []
    if not hash_df.empty:
        top_hashtags = (hash_df["_tag"].value_counts()
                        .head(6).index.tolist())[:3]
    sys = (
        "Je bent een TikTok caption & hook generator. "
        "Geef korte, pakkende hooks (max 8–12 woorden), en 1–2 zinnen caption. "
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
    # Probeer simpele parsing naar lijst
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    # groepeer regels die eruitzien als varianten
    variants = []
    buff = []
    for ln in lines:
        if re.match(r"^\d+[\).\-]\s*", ln) and buff:
            variants.append(" ".join(buff).strip()); buff = [ln]
        else:
            buff.append(ln)
    if buff: variants.append(" ".join(buff).strip())
    # fallback: als niets geparsed, geef raw terug als 1 item
    if not variants:
        variants = [raw]
    # beperk tot n_variants
    return variants[:n_variants]

# -------------------------- Chat met PostAi (Feature 3) ----------------------
def ai_chat_answer(d: pd.DataFrame, question: str) -> str:
    ctx = _summarize_dataset_for_context(d, top_n=60)
    # Mini “facts” die helpen bruikbare, concrete antwoorden te geven
    if d is None or d.empty:
        facts = "GEEN_DATA"
    else:
        df = d.copy()
        df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
        df = df.sort_values("Datum", ascending=False).head(60)
        views = pd.to_numeric(df["Views"], errors="coerce").fillna(0)
        top_view = int(views.max()) if len(views) else 0
        med_view = int(views.median()) if len(views) else 0
        best_hours = _best_hours(d, n=3)
        facts = f"top_views={top_view}; median_views={med_view}; best_hours={best_hours}"
    sys = (
        "Je bent een data-assistent die antwoorden geeft op basis van de meegegeven dataset. "
        "Antwoord kort en duidelijk. Als iets niet exact te zeggen is, geef een eenvoudige vuistregel."
    )
    usr = (
        f"Vraag: {question}\n"
        f"Dataset_context: {ctx}\n"
        f"Kerncijfers: {facts}\n"
        "Geef een kort antwoord (2–5 zinnen), en sluit af met één praktische vervolgstap."
    )
    return _ask_llm(sys, usr, temperature=0.4, max_tokens=450)

# ================================ Tabs ======================================
tabs = st.tabs([
    "🧠 Slimme assistent","📊 Resultaten","🏷️ Hashtags","🔥 Wat werkt nu?","⚖️ Vergelijk",
    "🗃️ Archief","🎯 A/B-planner","💡 Ideeën","🤖 AI Coach","🪄 Captions & Hooks","💬 Chat met PostAi","📅 Playbook & Plan","⚙️ Instellingen"
])
(tab_assist, tab_results, tab_tags, tab_trend, tab_compare, tab_arch,
 tab_ab, tab_ideas, tab_coach, tab_caps, tab_chat, tab_play, tab_settings) = tabs

# ---------------------------- Slimme assistent ------------------------------
with tab_assist:
    st.subheader("🧠 Slimme assistent — jouw contentcoach")
    base = normalize_per_post(df_raw)
    if base.empty:
        st.info("Nog geen data. Upload je CSV/XLSX of laad de demo-set.")
        with st.container(border=True):
            st.markdown("#### Onboarding-checklist")
            st.checkbox("CSV/XLSX geüpload", value=LATEST_FILE.exists(), disabled=True)
            st.checkbox("Beste tijden berekend", value=False, disabled=True)
            st.checkbox("Eerste A/B test gepland", value=False, disabled=True)
            st.checkbox("Alerts ingesteld (e-mail)", value=False, disabled=True)
    else:
        st.markdown("Deze assistent vertelt je **wat** en **wanneer** je vandaag het best post. Simpel 😊")
        st.divider()
        q = _read_queue()
        with st.container(border=True):
            st.markdown(f"### ⏳ {tr('review_queue')}")
            if not q: st.caption("Nog niets in de wachtrij. Voeg iets toe vanuit A/B of Ideeën.")
            else:
                for it in q[:4]:
                    l, r = st.columns([6,3])
                    l.markdown(f"**{it['caption'][:54]}…**  \n`{it['hashtags']}` · 🕒 {int(it['hour']):02d}:00")
                    if it["status"] == "pending":
                        if r.button("✅ Goedkeuren & posten", key=f"ap_{it['id']}"):
                            if approve_and_post(it["id"]):
                                st.session_state["undo_id"] = it["id"]; st.toast("Geplaatst (demo).")
                    else:
                        undo_id = st.session_state.get("undo_id")
                        if undo_id == it["id"]:
                            if r.button("↩️ Ongedaan maken (5s)", key=f"undo_{it['id']}"):
                                if undo_post(it["id"]): st.toast("Ongedaan gemaakt."); st.session_state["undo_id"] = None
                        else:
                            r.markdown("✅ Geplaatst")

# ------------------------------- Resultaten --------------------------------
with tab_results:
    st.subheader("📊 Resultaten")
    base = normalize_per_post(df_raw)
    if base.empty: st.info(tr("no_data"))
    else:
        d = add_kpis(base); st.caption("Tip: filter op een hashtag om te zien wat wérkt.")
        qtxt = st.text_input("Filter op hashtag (bijv. #love, #psychology)…").strip().lower()
        filt = d if not qtxt else d[d["Hashtags"].fillna("").str.lower().str.contains(qtxt, regex=False)]
        cols = [c for c in ["Hashtags","Views","Likes","Comments","Shares","Datum","Like rate","Share rate","Velocity","Score","Virality","Video link"] if c in filt.columns]
        st.dataframe(filt[cols], use_container_width=True, hide_index=True)
        st.markdown("#### Export")
        dt_str = pd.Timestamp.today().strftime("%Y-%m-%d")
        st.download_button("⬇️ Download data (HTML)", data=filt.to_html(index=False), file_name=f"tiktok_data_{dt_str}.html", mime="text/html")
        if not IS_PRO:
            st.caption("🔒 PDF-rapport is onderdeel van PRO.")
            with st.container(border=True):
                st.markdown("<div class='locked' style='border-radius:16px; padding:10px;'></div>", unsafe_allow_html=True)
        else:
            st.caption("PDF-rapport (placeholder) — integratie hier toevoegen.")

# -------------------------------- Hashtags ----------------------------------
with tab_tags:
    st.subheader("🏷️ Hashtags")
    base = normalize_per_post(df_raw)
    if base.empty: st.info(tr("no_data"))
    else:
        d = add_kpis(base)
        tags = (d.assign(_tag=d["Hashtags"].fillna("").str.split()).explode("_tag"))
        tags = tags[tags["_tag"].str.startswith("#", na=False)]
        if tags.empty: st.info("Geen hashtags gevonden.")
        else:
            agg = (tags.groupby("_tag", dropna=True)
                      .agg(freq=("Views","count"), views=("Views","sum"),
                           avg_like_rate=("Like rate","mean"), avg_share_rate=("Share rate","mean"),
                           avg_score=("Score","mean"), avg_virality=("Virality","mean"))
                      .sort_values(["freq","avg_score"], ascending=[False, False]))
            st.dataframe(agg.head(30), use_container_width=True)

# ---------------------------- Wat werkt nu? ---------------------------------
with tab_trend:
    st.subheader("🔥 Wat werkt nu goed? (14d vs 14d)")
    base = normalize_per_post(df_raw)
    if base.empty: st.info(tr("no_data"))
    else:
        d = add_kpis(base); tr_df = trending_hashtags(d, days_window=14)
        if tr_df is None or tr_df.empty: st.info("Niet genoeg datapunten om trends te berekenen.")
        else:
            st.dataframe(tr_df.head(25), use_container_width=True)
            st.caption("We vergelijken de laatste 14 dagen met de 14 dagen daarvoor.")

# ---------------------------- Vergelijk perioden ----------------------------
with tab_compare:
    st.subheader("⚖️ Vergelijk twee perioden")
    base = normalize_per_post(df_raw)
    if base.empty: st.info(tr("no_data"))
    else:
        d = add_kpis(base)
        colA, colB = st.columns(2)
        with colA: a = st.date_input("Periode A", value=(), format="YYYY-MM-DD", key="pa")
        with colB: b = st.date_input("Periode B", value=(), format="YYYY-MM-DD", key="pb")
        def slice_period(rng: tuple) -> pd.DataFrame:
            if not isinstance(rng, (list, tuple)) or len(rng) != 2: return pd.DataFrame()
            start = pd.to_datetime(rng[0]); end = pd.to_datetime(rng[1]) + pd.Timedelta(days=1)
            dt = pd.to_datetime(d["Datum"], errors="coerce"); mask = (dt >= start) & (dt < end)
            return d.loc[mask].copy()
        A = slice_period(a); B = slice_period(b)
        def kpis(df: pd.DataFrame) -> tuple[int, float, float]:
            if df is None or df.empty: return 0, 0.0, 0.0
            tv = int(pd.to_numeric(df.get("Views", pd.Series(dtype=float)), errors="coerce").sum(skipna=True))
            eng = float(pd.to_numeric(df.get("Engagement %", pd.Series(dtype=float)), errors="coerce").mean(skipna=True) * 100)
            sc  = float(pd.to_numeric(df.get("Score", pd.Series(dtype=float)), errors="coerce").mean(skipna=True))
            return tv, eng, sc
        tvA, engA, scA = kpis(A); tvB, engB, scB = kpis(B)
        k1, k2, k3 = st.columns(3)
        k1.markdown(f"<div class='kpi-card'><div class='kpi-label'>Views A / B</div><div class='kpi-value'>👁️ {tvA:,} / {tvB:,}</div></div>".replace(",", "."), unsafe_allow_html=True)
        k2.markdown(f"<div class='kpi-card'><div class='kpi-label'>Gem. reactie-score</div><div class='kpi-value'>📈 {engA:.2f}% / {engB:.2f}%</div></div>", unsafe_allow_html=True)
        k3.markdown(f"<div class='kpi-card'><div class='kpi-label'>Δ Virale score (B − A)</div><div class='kpi-value'>{(scB - scA):+,.3f}</div></div>".replace(",", "."), unsafe_allow_html=True)

# -------------------------------- Archief -----------------------------------
with tab_arch:
    st.subheader("🗃️ Archief")
    files = sorted(DATA_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    rows = []
    for p in files:
        try:
            df = _smart_read_any(p)
            rows.append({"Bestand": p.name, "Grootte (KB)": round(p.stat().st_size/1024, 1), "Rijen": len(df), "Laatste wijziging": datetime.fromtimestamp(p.stat().st_mtime)})
        except Exception: pass
    table = pd.DataFrame(rows)
    if table.empty: st.info("Nog geen bestanden in het archief.")
    else: st.dataframe(table, use_container_width=True, hide_index=True)

# ------------------------------ A/B-planner ---------------------------------
with tab_ab:
    st.subheader("🎯 A/B-planner")
    base = normalize_per_post(df_raw); d = add_kpis(base) if not base.empty else pd.DataFrame()
    if d.empty: st.info("Upload of laad demo-data om te plannen.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            hook_a = st.text_input("Hook A (de eerste zin)", value="Wat bijna niemand weet…")
            tags_a = st.text_input("Hashtags A", value="#darkfacts #psychology #tiktoknl")
            hour_a = st.number_input("Uur A", min_value=0, max_value=23, value=19)
        with col2:
            hook_b = st.text_input("Hook B", value="Dit klinkt raar, maar…")
            tags_b = st.text_input("Hashtags B", value="#viral #mindblown #fyp")
            hour_b = st.number_input("Uur B", min_value=0, max_value=23, value=21)
        def pvs(hook, tags, hr):
            base_vir = float(d["Virality"].tail(50).mean(skipna=True)) if "Virality" in d and not d["Virality"].empty else 50
            hook_len = len(hook.split()); n_tags = len([t for t in tags.split() if t.startswith("#")])
            hook_bonus = np.clip(hook_len*2.2, 0, 22); tags_bonus = np.clip(n_tags*3.0, 0, 18); hr_bonus = 22 if hr in _best_hours(d, n=3) else 8
            return int(np.clip(base_vir*0.3 + hook_bonus + tags_bonus + hr_bonus, 0, 100))
        rows = []
        for label, hook, tags, hr in [("A", hook_a, tags_a, int(hour_a)), ("B", hook_b, tags_b, int(hour_b))]:
            rows.append([label, hook, tags, hr, pvs(hook, tags, hr)])
        combo = pd.DataFrame(rows, columns=["Variant","Hook (tekst)","Hashtag-mix","Uur","PVS"])
        st.dataframe(combo, use_container_width=True, hide_index=True)
        if IS_PRO:
            st.markdown("### In review-wachtrij zetten")
            pick = st.selectbox("Welke variant toevoegen?", ["A","B"])
            if st.button(tr("add_queue")):
                row = combo.loc[0 if pick=="A" else 1]
                queue_post(row["Hook (tekst)"], row["Hashtag-mix"], int(row["Uur"]))
                st.success("Toegevoegd aan wachtrij.")
        else:
            with st.container(border=True):
                st.markdown("<div class='locked' style='border-radius:16px; padding:10px;'></div>", unsafe_allow_html=True)

# ---------------------------- Ideeëngenerator -------------------------------
with tab_ideas:
    st.subheader("💡 Ideeën")
    topic = st.text_input("Onderwerp of thema? (bijv. manipulatie, angst, liefde, brein…)", placeholder="Typ hier je onderwerp…")
    if topic:
        st.caption("We geven je 3 kant-en-klare ideeën. Kort, duidelijk en meteen te filmen.")
        for i in range(1,4):
            st.markdown(f"**Idee {i}** — #{topic}")
            cap = f"{topic}. Volg @Darkestpsycho voor meer dark psych facts."
            tags = "#darkfacts #psychology #creepy #mindblown #tiktoknl"
            prompt = (f"Korte 9:16 video over **{topic}**; donkere stijl; 5–8s; 1) hook shockfact 2) 2–3 beats 3) CTA 'Volg @Darkestpsycho'.")
            st.code(cap); st.code(tags); st.code(prompt)
            if IS_PRO:
                if st.button(tr("add_queue"), key=f"addq_{i}"):
                    queue_post(cap, tags, 19); st.success("Toegevoegd aan wachtrij.")
            else:
                st.markdown("<div class='locked' style='border-radius:12px; height:44px;'></div>", unsafe_allow_html=True)
            st.divider()

# ---------------------------- 🤖 AI Coach (UPGRADED) ------------------------
# helper: rerun werkt in nieuwe én oude Streamlit
def _rerun():
    try:
        st.rerun()
    except AttributeError:
        try:
            st.experimental_rerun()  # fallback voor oudere versies
        except Exception:
            pass

# ---------------------------- 🤖 AI Coach (UPGRADED) ------------------------
with tab_coach:
    st.subheader("🤖 AI Coach — persoonlijk advies")
    if not _has_openai():
        st.info("Voeg je **OPENAI_API_KEY** toe in `st.secrets` om de AI Coach te gebruiken.")
    else:
        base = normalize_per_post(df_raw)
        d = add_kpis(base) if not base.empty else pd.DataFrame()
        if d.empty:
            st.info("Nog geen data. Upload of laad de demo-set.")
        else:
            # 📚 Kennisbank invoer
            with st.expander("📚 Coach leren (kennisbank)"):
                kb_txt = st.text_area(
                    "Voeg regels/notities toe voor de coach (do’s/don’ts, merkstem, formules, CTA’s)…",
                    height=120,
                    placeholder="Voorbeeld:\n- Gebruik max 3 hashtags, nooit #foryou.\n- Merkstem: direct, geen emoji-spam.\n- Hook-sjabloon: 'Dit gaat je X besparen in Y seconden'."
                )
                kb_tags = st.text_input("Tags (optioneel, komma-gescheiden)", value="brand, captions, hooks")
                if st.button("➕ Voeg toe aan kennisbank"):
                    if kb_txt.strip():
                        add_kb_note(kb_txt.strip(), [t.strip() for t in kb_tags.split(",") if t.strip()])
                        st.success("Toegevoegd aan kennisbank.")

                st.caption("Laatste 5 kennisitems:")
                kb_items = _load_coach_state().get("kb", [])
                st.write("\n".join(f"• {n['text']}" for n in kb_items[-5:]) or "—")

            # 🔎 Vraag & advies
            niche = st.text_input("Niche (optioneel)", placeholder="psychologie, fashion, fitness…")
            prefill = st.session_state.get("coach_q_prefill", "")
            q_user = st.text_input(
                "Waar heb je nu advies voor nodig?",
                value=prefill,
                placeholder="Bijv. betere hooks voor mijn dark psychology video’s"
            )

            if st.button("🧠 Vraag advies aan Coach", type="primary"):
                with st.spinner("Coach denkt met je mee…"):
                    tips = ai_coach_suggestions(d, niche_hint=niche, user_prompt=q_user)
                st.markdown(tips)

                colA, colB, colC = st.columns(3)
                with colA:
                    if st.button("👍 Helpt mij"):
                        add_feedback(q_user, tips, rating=1)
                        st.success("Top! Coach onthoudt dat dit werkte.")
                with colB:
                    if st.button("👎 Niet helpend"):
                        add_feedback(q_user, tips, rating=0)
                        st.info("Feedback opgeslagen. Volgende keer sturen we bij.")
                with colC:
                    if st.button("➕ Zet tip in wachtrij (19:00)"):
                        first_line = tips.splitlines()[0] if tips else "Nieuwe tip"
                        queue_post(first_line, "#tiktoknl", 19)
                        mark_tip_accepted(first_line)
                        st.success("Toegevoegd aan review-wachtrij.")

            # ---- 🔧 Snelle prompts ----
            st.markdown("#### 🔧 Snelle prompts")
            c1, c2, c3 = st.columns(3)

            if c1.button("Hooks verbeteren"):
                st.session_state["coach_q_prefill"] = (
                    "Geef 3 hook-verbeteringen voor mijn best presterende onderwerp."
                )
                _rerun()

            if c2.button("Hashtag-mix"):
                st.session_state["coach_q_prefill"] = (
                    "Welke 3 hashtags werken nu het best en waarom?"
                )
                _rerun()

            if c3.button("Posttijden"):
                st.session_state["coach_q_prefill"] = (
                    "Welke 3 posttijden bevelen we aan komende week?"
                )
                _rerun()

            # 📌 Snelle info uit je data  ← LET OP: zelfde indent als 'Snelle prompts'
            best = _best_hours(d, n=3)
            st.caption(f"📌 Beste uren volgens je data: **{', '.join([f'{h:02d}:00' for h in best])}**")
# ----------------------- 🪄 Captions & Hooks (NEW) -----------------------
with tab_caps:
    st.subheader("🪄 Caption & Hook generator")
    if not _has_openai():
        st.info("Voeg je **OPENAI_API_KEY** toe in `st.secrets` om de generator te gebruiken.")
    else:
        base = normalize_per_post(df_raw); d = add_kpis(base) if not base.empty else pd.DataFrame()
        if d.empty:
            st.info("Nog geen data. Upload of laad demo (we kunnen desnoods zonder, maar mét data zijn de captions beter).")
        topic = st.text_input("Onderwerp/video-idee", placeholder="Bijv. Waarom 90% dit fout doet…")
        style = st.selectbox("Stijl", ["hooky (kort & punchy)","informatief","conversational"], index=0)
        n_var = st.slider("Aantal varianten", 1, 5, 3)
        if st.button("✨ Genereer captions"):
            if not topic.strip():
                st.warning("Vul eerst een onderwerp in.")
            else:
                with st.spinner("Aan het bedenken…"):
                    out = ai_generate_captions(d if not d.empty else pd.DataFrame(), topic=topic, n_variants=int(n_var), style=style.split()[0])
                for i, var in enumerate(out, 1):
                    st.markdown(f"**Variant {i}**")
                    st.code(var)
                st.caption("Tip: voeg je favoriete variant direct toe in de A/B-planner.")

# -------------------------- 💬 Chat met PostAi (NEW) -----------------------
with tab_chat:
    st.subheader("💬 Chat met PostAi")
    if not _has_openai():
        st.info("Voeg je **OPENAI_API_KEY** toe in `st.secrets` om te chatten.")
    else:
        base = normalize_per_post(df_raw); d = add_kpis(base) if not base.empty else pd.DataFrame()
        if d.empty:
            st.info("Nog geen data. Upload of laad demo om gerichte antwoorden te krijgen.")
        question = st.text_input("Stel je vraag (bijv. 'Wat is mijn beste posttijd?' of 'Wat verbeteren aan mijn captions?')")
        if st.button("Vraag het PostAi"):
            if not question.strip():
                st.warning("Typ eerst een vraag.")
            else:
                with st.spinner("Kijken wat je data zegt…"):
                    ans = ai_chat_answer(d if not d.empty else pd.DataFrame(), question)
                st.markdown(ans)

# --------------------------- Playbook & Plan -------------------------------
with tab_play:
    st.subheader("📅 Playbook & 7-dagen Plan")
    base = normalize_per_post(df_raw); d = add_kpis(base) if not base.empty else pd.DataFrame()
    if not IS_PRO:
        st.warning("🔒 Alleen in PRO. Ontgrendel om je weekplan te zien.")
        st.markdown("<div class='locked' style='height:220px;'></div>", unsafe_allow_html=True)
    else:
        if d.empty: st.info(tr("no_data"))
        else:
            def generate_playbook(d: pd.DataFrame) -> Dict[str, str]:
                hours = _best_hours(d, n=3); htxt = ", ".join([f"{h:02d}:00" for h in hours])
                tr_df = trending_hashtags(d, days_window=14); top_tag = tr_df.head(1).index[0] if tr_df is not None and not tr_df.empty else "#viral"
                return dict(beste_tijden=htxt, top_hashtag=top_tag, hook_stijl="shock", actie="Herpost je best scorende video en maak een vervolg.")
            def generate_week_plan(d: pd.DataFrame) -> pd.DataFrame:
                hours = _best_hours(d, n=3); h1,h2,h3=(hours+[19,20,18])[:3]
                tr_df = trending_hashtags(d, days_window=14); trend_tag = tr_df.head(1).index[0] if tr_df is not None and not tr_df.empty else "#darkfacts"
                rows=[["Ma","Herpost topvideo",f"{h1:02d}:00","Wat bijna niemand weet…",f"{trend_tag} #tiktoknl #fyp","Herbruik"],
                      ["Di","Nieuw idee (trending)",f"{h2:02d}:00","Dit klinkt gek, maar…",f"{trend_tag} #psychology","Test"],
                      ["Wo","Reacties / community","—","—","—","Engage"],
                      ["Do","A/B-test variant A",f"{h1:02d}:00","Niemand vertelt je dit…","#viral #nl","Test"],
                      ["Vr","A/B-test variant B",f"{h2:02d}:00","De meeste mensen weten niet…","#facts #dark","Test"],
                      ["Za","Behind the scenes",f"{h3:02d}:00","Zo maak ik m’n video’s…","#creator #real","Connect"],
                      ["Zo","Weekoverzicht / highlight",f"{h1:02d}:00","Deze video ging viral!","#recap #weekend","Reflectie"]]
                return pd.DataFrame(rows, columns=["Dag","Type","Tijd","Hook/Caption","Hashtags","Doel"])
            pb = generate_playbook(d)
            c1,c2,c3,c4 = st.columns(4)
            c1.markdown(f"<div class='kpi-card'><div class='kpi-label'>Beste tijden</div><div class='kpi-value'>{pb['beste_tijden']}</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='kpi-card'><div class='kpi-label'>Top-hashtag</div><div class='kpi-value'>{pb['top_hashtag']}</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='kpi-card'><div class='kpi-label'>Hook-stijl</div><div class='kpi-value'>{pb['hook_stijl']}</div></div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='kpi-card'><div class='kpi-label'>Actie</div><div class='kpi-value'>Nu doen</div></div>", unsafe_allow_html=True)
            st.info(pb["actie"])
            st.markdown("### 📅 7-dagen Postplan")
            plan = generate_week_plan(d); st.dataframe(plan, use_container_width=True, hide_index=True)
            colx1, colx2 = st.columns(2)
            with colx1:
                dt_str = pd.Timestamp.today().strftime("%Y-%m-%d")
                st.download_button("⬇️ Exporteer plan (CSV)", data=plan.to_csv(index=False).encode("utf-8"), file_name=f"postplan_7_dagen_{dt_str}.csv", mime="text/csv")
            with colx2:
                txt = io.StringIO(); txt.write("PLAYBOOK\n"); [txt.write(f"{k}: {v}\n") for k,v in pb.items()]
                st.download_button("⬇️ Exporteer playbook (TXT)", data=txt.getvalue().encode("utf-8"), file_name="playbook.txt", mime="text/plain")

# ------------------------------ Instellingen -------------------------------
with tab_settings:
    st.subheader("⚙️ Instellingen")
    def _load_settings() -> dict:
        if SETTINGS_FILE.exists():
            try: return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            except Exception: pass
        return {"auto_experiments": True,"auto_post_mode":"review","alert_channel":"email","lang":"nl","data_retention_days":180}
    def _save_settings(cfg: dict) -> bool:
        try: SETTINGS_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8"); return True
        except Exception: return False
    cfg = _load_settings()
    col1, col2 = st.columns(2)
    with col1:
        cfg["auto_experiments"] = st.toggle("Slimme testen (A/B → bandit)", value=cfg.get("auto_experiments", True))
        cfg["auto_post_mode"] = st.selectbox("Automatisch posten", ["review","off"], index=["review","off"].index(cfg.get("auto_post_mode","review")))
        cfg["lang"] = st.selectbox("Taal", ["nl","en"], index=["nl","en"].index(cfg.get("lang","nl")))
    with col2:
        cfg["alert_channel"] = st.selectbox("Alerts kanaal", ["email"], index=0)
        cfg["data_retention_days"] = st.number_input("Data-retentie (dagen)", min_value=30, max_value=365, value=int(cfg.get("data_retention_days",180)))
        st.session_state["alert_email"] = st.text_input("Alert e-mail ontvanger", value=st.session_state.get("alert_email",""))
    if st.button("Bewaar instellingen"):
        if _save_settings(cfg): st.success("Instellingen opgeslagen.")
        else: st.error("Kon instellingen niet opslaan.")
    st.markdown("---"); st.markdown("### Branding")
    b1, b2 = st.columns([1,1])
    with b1:
        color = st.color_picker("Merkkleur", value=THEME_COLOR)
        if st.button("Bewaar kleur"):
            if _save_brand_color(color): st.success("Kleur opgeslagen. Herlaad de pagina.")
    with b2:
        if LOGO_BYTES:
            st.image(LOGO_BYTES, caption="Logo", width=90)
            if st.button("Logo verwijderen"):
                if _remove_brand_logo(): st.success("Logo verwijderd. Herladen…")
        else:
            lf = st.file_uploader("Upload logo (png)", type=["png"])
            if lf is not None and _save_brand_logo(lf): st.success("Logo opgeslagen. Herladen…")
    st.markdown("---"); st.markdown("### Licentie")
    if IS_PRO:
        st.success("Je draait **PRO**. Bedankt! 🎉")
        if st.button("Deactiveer (verwijder licentie)"):
            if _remove_license(): st.success("Licentie verwijderd. Herladen…")
    else:
        key = st.text_input("Licentie sleutel")
        if st.button("Activeer PRO"):
            if key.strip():
                if _write_license(key.strip()): st.success("Licentie opgeslagen. Herladen…")
            else: st.warning("Voer een geldige key in.")
        st.caption("Nog geen licentie? Koop ‘m hieronder.")
        st.link_button("✨ Koop PRO", LEMON_CHECKOUT_URL, use_container_width=True)
    st.markdown("---"); st.markdown("### Data opschonen (GDPR)")
    if st.button("🧹 Verwijder lokale data (CSV/archief/state)"):
        try:
            for p in DATA_DIR.glob("*.csv"): p.unlink(missing_ok=True)
            for p in [LATEST_FILE, ALERT_STATE_FILE, SYNC_STATE_FILE, POST_QUEUE_FILE, COACH_STATE_FILE]:
                if p.exists(): p.unlink()
            st.success("Alle lokale data/states zijn verwijderd.")
        except Exception as e:
            st.error(f"Kon data niet verwijderen: {e}")

# ------------------------------ Legal blok -------------------------------
with st.expander("Legal & TikTok Review Info", expanded=False):
    base = _get_public_base_url() or "https://postai.bouwmijnshop.nl"
    requested_scopes = getconf("TIKTOK_SCOPES", "user.info.basic").strip()
    st.markdown(f"""
- **Website (this app):** {base}  
- **Redirect URI:** {base}/  
- **Requested scopes:** `{requested_scopes}`  
- **Wat we doen:** inloggen + analytics tonen. **Geen auto-posting.**  
- **Terms:** <https://www.bouwmijnshop.nl/pages/onze-voorwaarden>  
- **Privacy:** <https://www.bouwmijnshop.nl/pages/privacy>  
- **Support:** support@bouwmijnshop.nl
""")

# ----------------------------- Footer badges -------------------------------
st.markdown(f"<div class='footer-trust'>🛡️ {tr('trust1')} · 📄 {tr('trust2')} · 🎁 {tr('trust3')} · 🎯 {tr('trust4')}</div>", unsafe_allow_html=True)
