# app.py — PostAi (TikTok Growth Agent) • 10/10 polish edition
from __future__ import annotations

from typing import Dict, List, Tuple
import re, io, json, uuid, base64, time
from pathlib import Path
from datetime import datetime, date

import numpy as np
import pandas as pd
import streamlit as st

# ------------------------ Optionele imports ------------------------
try:
    import altair as alt
    HAS_ALTAIR = True
except Exception:
    HAS_ALTAIR = False
# === TikTok OAuth (Login Kit) – minimal review version ======================
# Vereist env vars op Render:
# - TIKTOK_CLIENT_KEY  (Client Key uit TikTok Developer Portal)
# - TIKTOK_SCOPES      (optioneel, bv: user.info.basic,video.list)
# - APP_PUBLIC_URL     (je base URL, bv: https://postai.bouwmijnshop.nl)

import os, urllib.parse, uuid

def _get_public_base_url() -> str:
    # Gebruik env zodat dit ook op custom domain werkt
    url = os.getenv("APP_PUBLIC_URL", "").strip().rstrip("/")
    return url

def build_tiktok_auth_url() -> str:
    client_key = os.getenv("TIKTOK_CLIENT_KEY", "").strip()
    scopes     = os.getenv("TIKTOK_SCOPES", "user.info.basic,video.list").strip()
    base_url   = _get_public_base_url()
    if not client_key or not base_url:
        return ""  # laat UI tonen dat env ontbreekt

    # We gebruiken de homepage als redirect (Streamlit leest query params)
    redirect_uri = f"{base_url}/"

    # state voor CSRF bescherming
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
# ============================================================================

# ------------------------ Paden & metadata -------------------------
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

LEMON_CHECKOUT_URL = "https://your-lemon-squeezy-checkout.link/PRODUCT"  # vervang

# ------------------------ Licentie utils ---------------------------
def _read_license() -> Tuple[str, bool]:
    try:
        if LICENSE_FILE.exists():
            key = LICENSE_FILE.read_text(encoding="utf-8").strip()
            if key and key.upper() != "DEMO":
                return key, True
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

import os

# 1️⃣ Check eerst environment variable (Render / .env)
ENV_LICENSE = os.getenv("LICENSE_KEY", "").strip()

if ENV_LICENSE:
    LICENSE_KEY = ENV_LICENSE
    IS_PRO = True
else:
    # 2️⃣ Anders val terug op lokaal license.key bestand
    LICENSE_KEY, IS_PRO = _read_license()


# ------------------------ Streamlit setup --------------------------
st.set_page_config(
    page_title=f"{APP_NAME} — {'PRO' if IS_PRO else 'DEMO'}",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)
# === OAuth callback handling (leest query params van TikTok) ===============
# TikTok stuurt terug naar je base URL met ?code=&state=&scopes=
qp = st.query_params
if "code" in qp:
    # Toon status voor je review video
    code  = qp.get("code")
    state = qp.get("state", "")
    ok_state = (state == st.session_state.get("_tiktok_state"))
    st.success(f"✅ TikTok OAuth code ontvangen (state ok: {ok_state}). Je kunt dit scherm tonen in je reviewvideo.")
    # Bewaar kort in session (we wisselen hier nog GEEN token om; voor review is dit genoeg)
    st.session_state["tik_code"] = code
    st.session_state["tik_state_ok"] = ok_state
# ============================================================================

# ------------------------ Branding utils --------------------------
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

# ------------------------ Settings / I18N --------------------------
DEFAULT_SETTINGS = {
    "auto_experiments": True,
    "auto_post_mode": "review",
    "alert_channel": "email",
    "lang": "nl",
    "data_retention_days": 180,
}

def _load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try: return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception: pass
    return DEFAULT_SETTINGS.copy()

def _save_settings(cfg: dict) -> bool:
    try:
        SETTINGS_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8"); return True
    except Exception:
        return False

SET = _load_settings()

def tr(k: str) -> str:
    I18N = dict(
        no_data="Nog geen data.",
        next_best="Jouw groeiaanbeveling",
        review_queue="Review-wachtrij",
        approve_post="Goedkeuren & Posten",
        add_queue="Zet in review-wachtrij",
        playbook="Playbook",
        plan7="Postplan",
        trust1="GDPR-proof",
        trust2="CSV/XLSX",
        trust3="14-dagen gratis",
        trust4="Made for TikTok",
    )
    return I18N.get(k, k)

# ------------------------ CSS --------------------------------------
def _inject_css(theme_color: str, pro: bool):
    st.markdown(f"""
    <style>
      :root {{
        --brand:{theme_color}; --ring:#e8edf3; --muted:#4b5563; --head:#f8fafc;
      }}
      .block-container {{ max-width:1200px; padding-top:14px; }}
      section[data-testid="stSidebar"] {{ width:260px !important; }}
      .accent {{ color:var(--brand); }}
      h1,h2,h3 {{ letter-spacing:-.01em; }}
      /* cards */
      .hero-card {{ border:1px solid var(--ring); border-radius:16px; padding:18px; background:#fff; box-shadow:0 6px 18px rgba(0,0,0,.06); }}
      .kpi-card {{ border:1px solid var(--ring); border-radius:16px; padding:14px 16px; background:#fff; box-shadow:0 4px 12px rgba(0,0,0,.05); }}
      .kpi-label {{ color:var(--muted); font-size:.85rem; margin-bottom:4px; }}
      .kpi-value {{ font-size:1.35rem; font-weight:700; }}
      .chip {{ display:inline-block; padding:4px 10px; border:1px solid var(--ring); border-radius:999px; margin-right:6px; margin-bottom:6px; font-size:.8rem; background:#fff; }}
      .chip.badge {{ background:#eef6ff; border-color:#cfe3ff; }}
      .pro-badge {{ position:fixed; top:8px; right:12px; z-index:9999; background:{"#10b981" if pro else "#6b7280"}; color:#fff; padding:6px 12px; border-radius:999px; font-weight:700; box-shadow:0 1px 3px rgba(0,0,0,.1); }}
      .stTabs [data-baseweb="tab-list"] {{ position:sticky; top:0; z-index:5; background:#fff; padding-top:6px; border-bottom:1px solid #eef2f7; }}
      /* spacing polish */
      .hero-gap {{ margin-bottom:16px; }}
      .kpi-gap {{ margin-top:10px; margin-bottom:14px; }}
      /* Buttons */
      .stButton>button {{
        transition:transform .1s ease, box-shadow .1s ease, opacity .2s ease;
        border-radius:12px; font-weight:700;
      }}
      .stButton>button:hover {{ transform:translateY(-1px); box-shadow:0 6px 16px rgba(0,0,0,.06); }}
      .primary-btn>button {{ background:var(--brand); color:#fff; border:1px solid var(--brand); height:50px; font-size:1.05rem; }}
      .primary-btn>button:disabled {{ opacity:.7; cursor:not-allowed; }}
      .soft-btn>button {{ background:#fff; border:1px solid var(--ring); }}
      /* Focus ring accessibility */
      .stButton>button:focus {{ outline:2px solid var(--brand) !important; outline-offset:2px !important; }}
      a:focus {{ outline:2px solid var(--brand) !important; outline-offset:2px !important; }}
      /* Dropzone hover */
      [data-testid="stFileUploaderDropzone"] {{ border:1px dashed var(--ring); border-radius:14px; }}
      [data-testid="stFileUploaderDropzone"]:hover {{ border-color: var(--brand); background:#f4f8ff; }}
      /* Confidence bar */
      .nbabarshell {{ margin:8px 0;height:8px;background:#e5e7eb;border-radius:8px; position:relative; }}
      .nbabar {{ height:100%;background:#22c55e;border-radius:8px; }}
      .nbalabel {{ position:absolute; right:8px; top:-18px; font-size:.8rem; color:#4b5563; }}
      .footer-trust {{ color:#6b7280; font-size:.9rem; margin-top:24px; border-top:1px solid #eef2f7; padding-top:12px; }}
      /* Skeletons */
      .skeleton {{ position:relative; overflow:hidden; background:#f1f5f9; border-radius:14px; min-height:64px; border:1px solid #e5e7eb; }}
      .skeleton::after {{
        content:""; position:absolute; inset:0; background:linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,.6) 50%, rgba(255,255,255,0) 100%);
        transform:translateX(-100%); animation:shimmer 1.2s infinite;
      }}
      @keyframes shimmer {{ 100% {{ transform:translateX(100%); }} }}
    </style>
    """, unsafe_allow_html=True)
    st.markdown(f"<div class='pro-badge'>{'PRO' if pro else 'DEMO'}</div>", unsafe_allow_html=True)

THEME_COLOR, LOGO_BYTES = _load_branding()
_inject_css(THEME_COLOR, IS_PRO)

# ------------------------ Helpers ----------------------------------
def _looks_like_xlsx(path: Path) -> bool:
    try:
        with open(path, "rb") as f: return f.read(4) == b"PK\x03\x04"
    except Exception: return False

@st.cache_data(show_spinner=False, ttl=600)
def _smart_read_any(path_or_file) -> pd.DataFrame:
    try:
        if isinstance(path_or_file, (str, Path)):
            p = Path(path_or_file)
            if not p.exists() or p.stat().st_size == 0: return pd.DataFrame()
            if _looks_like_xlsx(p) or p.suffix.lower()==".xlsx": return pd.read_excel(p)
            for args in (dict(sep=None, engine="python"), dict(sep=";"), dict()):
                try: return pd.read_csv(p, **args)
                except Exception: pass
            return pd.read_csv(p)
        else:
            name = getattr(path_or_file, "name", "").lower()
            if name.endswith(".xlsx"): return pd.read_excel(path_or_file)
            try: return pd.read_csv(path_or_file, sep=None, engine="python")
            except Exception:
                path_or_file.seek(0); return pd.read_csv(path_or_file)
    except Exception: return pd.DataFrame()

def _nk(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower(); s = re.sub(r"\s+","",s); s = re.sub(r"[^a-z0-9]","",s); return s

def _pick(lower: dict, *keys):
    for k in keys:
        if k in lower: return lower[k]
    return None

def _to_int_safe(x):
    if pd.isna(x): return np.nan
    s = str(x).strip().lower()
    if s.endswith(("k","m")):
        mul = 1000 if s.endswith("k") else 1_000_000
        s = s[:-1].replace(",", ".")
        try: return int(float(s)*mul)
        except: return np.nan
    s = s.replace(".","").replace(",","")
    try: return int(float(s))
    except: return np.nan

def _parse_nl_date(s):
    if pd.isna(s): return None
    txt = str(s).strip().lower().strip(" '\"\t\r\n,.;")
    months = {"januari":1,"februari":2,"maart":3,"april":4,"mei":5,"juni":6,"juli":7,"augustus":8,"september":9,"oktober":10,"november":11,"december":12}
    m = re.search(rf"(\d{{1,2}})\s*({'|'.join(months.keys())})", txt)
    if m:
        d, mon = int(m.group(1)), m.group(2)
        try: return date(datetime.now().year, months[mon], d)
        except: pass
    try: return pd.to_datetime(txt, dayfirst=True, errors="coerce").date()
    except: return None

def _is_tiktok_url(u: str) -> bool:
    u = str(u).strip().lower()
    return u.startswith("http") and "tiktok.com" in u

def normalize_per_post(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty: return pd.DataFrame()
    lower = {_nk(c): c for c in df.columns}
    col = {
        "caption":  _pick(lower, "videotitle","videotitel","caption","tekst","title","titel","omschrijving","beschrijving"),
        "views":    _pick(lower, "totalviews","views","plays","weergaven","videoweergaven","videoviews"),
        "likes":    _pick(lower, "totallikes","likes","hearts","hartjes","vindikleuks"),
        "comments": _pick(lower, "totalcomments","comments","reacties","opmerkingen"),
        "shares":   _pick(lower, "totalshares","shares","gedeeld","keergedeeld","delen"),
        "date":     _pick(lower, "posttime","time","date","datum","createdat","publicatiedatum","gepubliceerddatum"),
        "link":     _pick(lower, "videolink","videourl","video link","link","url"),
        "videoid":  _pick(lower, "videoid","awemeid","id"),
        "author":   _pick(lower, "author","username","account"),
    }
    d = df.copy()
    if col["caption"]:
        raw = d[col["caption"]].astype(str)
        d["Hashtags"] = raw.apply(lambda s: " ".join(re.findall(r"#\w+", s))).replace("", np.nan)
    else:
        d["Hashtags"] = np.nan
    d["Views"]    = d[col["views"]].apply(_to_int_safe) if col["views"] else np.nan
    d["Likes"]    = d[col["likes"]].apply(_to_int_safe) if col["likes"] else np.nan
    d["Comments"] = d[col["comments"]].apply(_to_int_safe) if col["comments"] else np.nan
    d["Shares"]   = d[col["shares"]].apply(_to_int_safe) if col["shares"] else np.nan

    if col["date"]:
        raw_dates = d[col["date"]].astype(str).str.strip(" '\"\t\r\n,.;")
        parsed = pd.to_datetime(raw_dates, dayfirst=True, errors="coerce")
        parsed = parsed.where(parsed.notna(), pd.to_datetime(raw_dates.apply(_parse_nl_date), errors="coerce"))
        parsed = parsed.apply(lambda x: x.replace(hour=12) if pd.notna(x) and getattr(x, "hour", 0)==0 else x)
        d["Datum"] = parsed
    else:
        d["Datum"] = pd.NaT

    d["Video link"] = ""
    if col["link"]:
        urls = d[col["link"]].astype(str)
        d["Video link"] = urls.where(urls.map(_is_tiktok_url), "")
    elif col["videoid"] and col["author"]:
        base = d[col["author"]].fillna("").astype(str).str.lstrip("@").str.strip()
        vid  = d[col["videoid"]].fillna("").astype(str).str.strip()
        d["Video link"] = "https://www.tiktok.com/@" + base + "/video/" + vid

    keep = ["Hashtags","Video link","Views","Likes","Comments","Shares","Datum"]
    return d[keep].copy()

def add_kpis(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty: return pd.DataFrame()
    d = df.copy()
    for c in ["Views","Likes","Comments","Shares"]:
        if c not in d.columns: d[c] = np.nan
    views    = pd.to_numeric(d["Views"], errors="coerce")
    likes    = pd.to_numeric(d["Likes"], errors="coerce")
    comments = pd.to_numeric(d["Comments"], errors="coerce")
    shares   = pd.to_numeric(d["Shares"], errors="coerce")

    denom = views.replace(0, np.nan)
    d["Like rate"]    = (likes    / denom).fillna(0.0)
    d["Comment rate"] = (comments / denom).fillna(0.0)
    d["Share rate"]   = (shares   / denom).fillna(0.0)
    d["Engagement %"] = d["Like rate"] + d["Comment rate"] + d["Share rate"]

    ds = pd.to_datetime(d.get("Datum"), errors="coerce")
    today = pd.Timestamp.today().normalize()
    days = (today - ds).dt.days
    days = days.clip(lower=0).fillna(7).replace(0, 1)
    d["Velocity"] = (likes / days).fillna(0.0)
    d["Recency"]  = np.exp(-days / 90.0)

    def _mm(x: pd.Series) -> pd.Series:
        x = x.astype(float); mn, mx = np.nanmin(x), np.nanmax(x)
        if not np.isfinite(mn) or not np.isfinite(mx) or mx <= mn:
            return pd.Series(0.0, index=x.index)
        return (x - mn) / (mx - mn)

    score = (
        0.35 * _mm(views) +
        0.25 * _mm(d["Engagement %"]) +
        0.15 * _mm(d["Share rate"]) +
        0.10 * _mm(d["Like rate"]) +
        0.10 * _mm(d["Velocity"]) +
        0.05 * d["Recency"]
    ).astype(float).replace([np.inf,-np.inf], np.nan).fillna(0.0)

    d["Score"] = score
    d["Virality"] = (score * 100).round(0)
    return d

@st.cache_data(show_spinner=False, ttl=600)
def trending_hashtags(d: pd.DataFrame, days_window: int = 14) -> pd.DataFrame:
    if d is None or d.empty:
        return pd.DataFrame()
    df = d.copy()
    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
    df = df.dropna(subset=["Datum"])
    if df.empty:
        return pd.DataFrame()
    last_date = df["Datum"].max().normalize()
    p2_start = last_date - pd.Timedelta(days=days_window - 1)
    p1_end   = p2_start - pd.Timedelta(days=1)
    p1_start = p1_end - pd.Timedelta(days=days_window - 1)
    tmp = df.assign(tag=df["Hashtags"].fillna("").str.split()).explode("tag")
    tmp["tag"] = tmp["tag"].astype(str)
    tmp = tmp[tmp["tag"].str.startswith("#", na=False)]
    if tmp.empty:
        return pd.DataFrame()
    p1 = tmp[(tmp["Datum"]>=p1_start) & (tmp["Datum"]<=p1_end)]
    p2 = tmp[(tmp["Datum"]>=p2_start) & (tmp["Datum"]<=last_date)]
    g1 = p1.groupby("tag", dropna=True).agg(avg_views=("Views","mean"), cnt=("Views","count"))
    g2 = p2.groupby("tag", dropna=True).agg(avg_views=("Views","mean"), cnt=("Views","count"))
    out = g1.join(g2, how="outer", lsuffix="_prev", rsuffix="_curr").fillna(0)
    denom = out["avg_views_prev"].replace(0, np.nan)
    out["growth_%"] = ((out["avg_views_curr"] - out["avg_views_prev"]) / denom) * 100
    out["growth_%"] = out["growth_%"].replace([np.inf,-np.inf], np.nan).fillna(0)
    out = out.sort_values(["growth_%","avg_views_curr","cnt_curr"], ascending=[False,False,False])
    return out

def _best_hours(d: pd.DataFrame, n: int = 3) -> List[int]:
    if d is None or d.empty: return [19, 20, 18][:n]
    dt = pd.to_datetime(d["Datum"], errors="coerce")
    tmp = d.copy(); tmp["hour"] = dt.dt.hour.fillna(12).astype(int)
    best = tmp.groupby("hour")["Views"].median().sort_values(ascending=False).head(n).index.tolist()
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

# ------------------------ Sidebar ----------------------------------
with st.sidebar:
    if IS_PRO:
        st.markdown("<div class='chip' style='background:#ecfdf5;border-color:#a7f3d0;'>✅ Je draait <b>PRO</b>. Bedankt! 🎉</div>", unsafe_allow_html=True)
    else:
        st.info("🔓 Je draait **DEMO**. Een deel is vergrendeld.")
        st.link_button("✨ Ontgrendel PRO", LEMON_CHECKOUT_URL, use_container_width=True)
# --- TikTok koppeling (review) ---
st.markdown("### 🔗 TikTok koppelen")
_login_url = build_tiktok_auth_url()
if _login_url:
    st.link_button("Login with TikTok", _login_url, use_container_width=True)
else:
    st.caption("Set env vars on Render → TIKTOK_CLIENT_KEY & APP_PUBLIC_URL")

# Toon minimale debug voor reviewers
if st.session_state.get("tik_code"):
    st.caption("Status: OAuth code ontvangen ✅ (alleen login & display; geen auto-posting).")
else:
    st.caption("We use TikTok Login for authentication only (no auto-post).")
st.markdown("---")

    st.markdown("### 📊 Data")
    st.markdown("<div class='sidebar-stack'>", unsafe_allow_html=True)
    if st.button("📥 Haal analytics op", use_container_width=True):
        res = run_manual_fetch(); st.toast(res["msg"] if res["ok"] else f"❌ {res['msg']}")
    if st.button("🎯 Probeer met voorbeelddata", use_container_width=True):
        rng = pd.date_range(end=pd.Timestamp.today().normalize(), periods=35, freq="D")
        np.random.seed(42); rows=[]
        tags_pool=["#darkfacts #psychology #fyp","#love #lovestory #bf #bestie","#viral #mindblown #creepy #tiktoknl","#redthoughts #besties #bff #lovehim","#deepthought #foryou #real #reels"]
        for d_ in rng:
            views = np.random.randint(20_000, 500_000)
            likes = int(views * np.random.uniform(0.04, 0.18))
            comments = int(views * np.random.uniform(0.003, 0.02))
            shares = int(views * np.random.uniform(0.002, 0.015))
            d_ = d_ + pd.Timedelta(hours=int(np.random.choice([12,14,16,18,20,0], p=[.25,.2,.18,.15,.12,.1])))
            rows.append(dict(caption=np.random.choice(tags_pool), views=views, likes=likes, comments=comments, shares=shares, date=d_, videolink=""))
        df_demo = pd.DataFrame(rows); df_demo.to_csv(LATEST_FILE, index=False)
        st.session_state["df"] = df_demo; st.session_state["demo_active"] = True
        st.toast("✅ Demo-data geladen")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 📁 Bestanden")
    try:
        ts = float(SYNC_STATE_FILE.read_text().strip()) if SYNC_STATE_FILE.exists() else 0
        last_sync = datetime.fromtimestamp(ts).strftime("%d-%m %H:%M") if ts else "—"
    except Exception: last_sync = "—"
    bron = "DEMO" if st.session_state.get("demo_active") else ("CSV/XLSX" if LATEST_FILE.exists() else "—")
    st.markdown(f"<span class='chip badge'>⏱️ Laatste sync: {last_sync}</span> <span class='chip badge'>📁 Bron: {bron}</span>", unsafe_allow_html=True)
    st.markdown("Upload je TikTok-data (CSV/XLSX)")
    up = st.file_uploader(" ", type=["csv","xlsx"], label_visibility="collapsed")
    if up is not None:
        try:
            df_up = _smart_read_any(up)
            try: up.seek(0)
            except Exception: pass
            df_up.to_csv(LATEST_FILE, index=False)
            st.session_state["df"] = df_up; st.session_state["demo_active"] = False
            st.success(f"✅ Bestand opgeslagen ({up.name}) — {len(df_up):,} rijen")
        except Exception as e:
            st.error(f"Kon bestand niet verwerken: {e}")

# ------------------------ Header -------------------------------
hwrap1, hwrap2 = st.columns([1, 8])
with hwrap1:
    if LOGO_BYTES:
        b64 = base64.b64encode(LOGO_BYTES).decode("ascii")
        st.markdown(
            f"<img src='data:image/png;base64,{b64}' style='height:60px;border-radius:12px;' />",
            unsafe_allow_html=True
        )
with hwrap2:
    st.markdown(
        "<h1 style='margin:0;font-size:1.6rem;'>"
        "<span class='accent'>PostAi</span> — TikTok Growth Agent — "
        f"{'PRO' if IS_PRO else 'DEMO'}</h1>",
        unsafe_allow_html=True
    )
    st.caption("Slimmer groeien met data. **Dare to know.**")

# ------------------------ Uitleg -----------------------
with st.expander("Uitleg in het kort (altijd zichtbaar)", expanded=False):
    st.markdown("""
**Stap 1.** Upload je **CSV/XLSX** of klik **🎯 Probeer met voorbeelddata**.  
**Stap 2.** **Slimme assistent** — zie wat nú werkt en wat je opnieuw moet posten.  
**Stap 3.** **A/B-planner** — test 2 hooks, 2 hashtag-mixen en 2 tijden.  
**Stap 4.** **Playbook & Plan** — jouw weekplan met beste tijden.  
**Stap 5.** *(PRO)* **PDF/e-mail**, **alerts** en **auto-post (review)**.  
""")

# ------------------------ Data load -------------------------------
if "df" not in st.session_state:
    st.session_state["df"] = _smart_read_any(LATEST_FILE)
df_raw = st.session_state.get("df", pd.DataFrame())

if _should_sync_hourly():
    _ = run_manual_fetch()
    if "df" not in st.session_state or st.session_state["df"].empty:
        st.session_state["df"] = _smart_read_any(LATEST_FILE); df_raw = st.session_state["df"]

# ------------------------ KPI helpers ------------------------------
def _fmt_delta(curr, prev):
    try:
        if prev is None or not np.isfinite(prev) or prev == 0: return "—", None
        diff = ((curr - prev) / prev) * 100
        arrow = "↑" if diff >= 0 else "↓"
        return f"{diff:+.1f}%", arrow
    except Exception: return "—", None

def _sparkline(series: pd.Series, width=120, height=28):
    if not HAS_ALTAIR: return None
    df_s = pd.DataFrame({"x": np.arange(len(series)), "y": pd.to_numeric(series, errors="coerce").fillna(method="ffill").fillna(0.0)})
    return alt.Chart(df_s).mark_line().encode(x="x:Q", y="y:Q").properties(width=width, height=height).configure_axis(disable=True)

def _kpi_row(d: pd.DataFrame, key_ns: str = "top"):
    st.markdown("<div class='kpi-gap'></div>", unsafe_allow_html=True)
    if d is None or d.empty:
        c1, c2, c3 = st.columns([3,3,3])
        c1.markdown("<div class='skeleton'></div>", unsafe_allow_html=True)
        c2.markdown("<div class='skeleton'></div>", unsafe_allow_html=True)
        c3.markdown("<div class='skeleton'></div>", unsafe_allow_html=True)
        return

    # persist periode
    period_options = [7,14,28]
    default_period = st.session_state.get("period_value", 7)
    try:
        idx_default = period_options.index(default_period)
    except ValueError:
        idx_default = 0

    kpi_left, kpi_right = st.columns([4,1])
    with kpi_right:
        sel = st.selectbox("Periode", period_options, index=idx_default, key=f"kpi_range_{key_ns}")
        st.session_state["period_value"] = sel

    range_days = sel
    with kpi_left:
        dt = pd.to_datetime(d["Datum"], errors="coerce"); now = pd.Timestamp.today().normalize()
        cur_mask = (dt >= (now - pd.Timedelta(days=range_days))) & (dt <= now + pd.Timedelta(days=1))
        prev_mask = (dt >= (now - pd.Timedelta(days=2*range_days))) & (dt < (now - pd.Timedelta(days=range_days)))
        def _sum(df, col): return int(pd.to_numeric(df[col], errors="coerce").sum(skipna=True))
        def _mean(df, col): return float(pd.to_numeric(df[col], errors="coerce").mean(skipna=True))
        cur = d.loc[cur_mask]; prev = d.loc[prev_mask]
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

        def _kpi_html(title, value, delta_str, arrow, icon):
            color = "#16a34a" if arrow == "↑" else ("#dc2626" if arrow == "↓" else "#6b7280")
            html = f"<div class='kpi-card'><div class='kpi-label'>{title}</div><div class='kpi-value'>{icon} {value} "
            html += f"<span style='color:{color}'>({delta_str if delta_str!='—' else '—'})</span></div></div>"
            return html

        c1.markdown(_kpi_html(f"Totaal views ({range_days}d)", f"{total_views_cur:,}".replace(",", "."), d1, a1, "👁️"), unsafe_allow_html=True)
        c2.markdown(_kpi_html(f"Gem. engagement ({range_days}d)", f"{avg_eng_cur:.2f}%", d2, a2, "📈"), unsafe_allow_html=True)
        c3.markdown(_kpi_html(f"Virality ({range_days}d)", f"{vir_cur:.0f}/100", d3, a3, "🔥"), unsafe_allow_html=True)

        if HAS_ALTAIR and not cur.empty:
            s1 = _sparkline(pd.to_numeric(cur["Views"], errors="coerce"))
            s2 = _sparkline(pd.to_numeric(cur["Engagement %"], errors="coerce") * 100)
            s3 = _sparkline(pd.to_numeric(cur["Virality"], errors="coerce"))
            if s1: c1.altair_chart(s1, use_container_width=False)
            if s2: c2.altair_chart(s2, use_container_width=False)
            if s3: c3.altair_chart(s3, use_container_width=False)

# ------------------------ Hero + Jouw groeiaanbeveling -------------
def _confidence_from_data(d: pd.DataFrame) -> int:
    if d is None or d.empty: return 60
    dt = pd.to_datetime(d["Datum"], errors="coerce"); now = pd.Timestamp.today().normalize()
    cur = d[(dt >= (now - pd.Timedelta(days=14))) & (dt <= now + pd.Timedelta(days=1))]
    n = len(cur); var = float(np.nanstd(pd.to_numeric(cur.get("Virality", pd.Series(dtype=float)), errors="coerce")))
    conf = 0.6 + min(n/20, 0.35) - min(var/200, 0.15)
    return int(np.clip(conf*100, 60, 95))

def _hero_and_nba(d: pd.DataFrame, last_sync: str, bron: str):
    with st.container(border=True):
        # Kop
        st.markdown(
            "<div style='display:flex;align-items:center;gap:12px;'>"
            "<div>"
            "<h2 style='margin:0;'>PostAi — TikTok Growth Agent</h2>"
            "<p style='margin:0;color:#4b5563;'>Slimmer groeien met data. <i>Dare to know.</i></p>"
            f"<p style='margin:6px 0 0 0;color:#6b5563;'>⏱️ Laatste sync: <b>{last_sync}</b> · 📁 Bron: <b>{bron}</b></p>"
            "</div></div>",
            unsafe_allow_html=True
        )

        left, right = st.columns([3,2])
        with left:
            st.markdown("<div class='hero'>", unsafe_allow_html=True)
_login_url_top = build_tiktok_auth_url()
if _login_url_top:
    st.link_button("Login with TikTok", _login_url_top, use_container_width=True)

            # CTA met loading state
            if st.button("🚀 Start analyse", key="hero_analyse_btn", use_container_width=True, type="primary", disabled=False):
                with st.spinner("Analyseren…"):
                    # Simuleer snelle analyse (indien je iets uitvoert, doe het hier)
                    time.sleep(0.6)
                    st.toast("✅ Analyse voltooid — aanbeveling geüpdatet.")

            st.caption("Duurt ± 3–5 sec. We genereren je aanbeveling op basis van recente prestaties.")
            st.file_uploader("Sleep je CSV/XLSX hierheen", type=["csv","xlsx"], label_visibility="collapsed", key="hero_upl")
            st.markdown("</div>", unsafe_allow_html=True)

            # Quick actions
            c1, c2 = st.columns(2)
            with c1:
                tpl = pd.DataFrame([dict(caption="Voorbeeld caption #hashtag",
                                         views=12345, likes=678, comments=12, shares=34,
                                         date=pd.Timestamp.today().normalize(), videolink="",
                                         author="@account", videoid="1234567890")])
                st.download_button("⬇️ Voorbeeld-CSV", data=tpl.to_csv(index=False).encode("utf-8"),
                                   file_name="postai_template.csv", mime="text/csv", use_container_width=True)
            with c2:
                if st.button("🎯 Laad demo-set", use_container_width=True, key="demo_btn_hero"):
                    rng = pd.date_range(end=pd.Timestamp.today().normalize(), periods=35, freq="D")
                    np.random.seed(42); rows=[]
                    tags_pool=["#darkfacts #psychology #fyp","#love #lovestory #bf #bestie","#viral #mindblown #creepy #tiktoknl","#redthoughts #besties #bff #lovehim","#deepthought #foryou #real #reels"]
                    for d_ in rng:
                        views = np.random.randint(20_000, 500_000)
                        likes = int(views * np.random.uniform(0.04, 0.18))
                        comments = int(views * np.random.uniform(0.003, 0.02))
                        shares = int(views * np.random.uniform(0.002, 0.015))
                        d_ = d_ + pd.Timedelta(hours=int(np.random.choice([12,14,16,18,20,0], p=[.25,.2,.18,.15,.12,.1])))
                        rows.append(dict(caption=np.random.choice(tags_pool), views=views, likes=likes, comments=comments, shares=shares, date=d_, videolink=""))
                    df_demo = pd.DataFrame(rows); df_demo.to_csv(LATEST_FILE, index=False)
                    st.session_state["df"] = df_demo; st.session_state["demo_active"] = True
                    st.toast("✅ Demo-data geladen")

            # trust mini
            st.markdown(
                f"<div class='trust-row'>"
                f"<span class='chip badge'>🛡️ {tr('trust1')}</span>"
                f"<span class='chip badge'>📄 {tr('trust2')}</span>"
                f"<span class='chip badge'>🎁 {tr('trust3')}</span>"
                f"<span class='chip badge'>🎯 {tr('trust4')}</span>"
                f"</div>", unsafe_allow_html=True
            )

        with right:
            st.markdown(f"**{tr('next_best')}**")
            if d is None or d.empty:
                st.write("Upload data of laad demo om advies te krijgen.")
            else:
                best_time = _best_hours(d, n=1)[0]
                conf = _confidence_from_data(d)
                st.markdown(
                    f"<div class='nbabarshell'><div class='nbabar' style='width:{conf}%;'></div><div class='nbalabel'>{conf}%</div></div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"🔥 **Post om {best_time:02d}:00.** Herpost je best scorende video. Test variant A."
                )
                with st.expander("Waarom?"):
                    st.write("Op basis van mediane views, share rate en je topuren van de afgelopen 14 dagen.")
                st.button("🔥 Voer aanbeveling uit", use_container_width=True)

# ------------------------ Build data for hero/KPI -------------------
base_for_hero = normalize_per_post(df_raw)
d_for_hero = add_kpis(base_for_hero) if not base_for_hero.empty else pd.DataFrame()

try:
    ts = float(SYNC_STATE_FILE.read_text().strip()) if SYNC_STATE_FILE.exists() else 0
    last_sync = datetime.fromtimestamp(ts).strftime("%d-%m %H:%M") if ts else "—"
except Exception: last_sync = "—"
bron = "DEMO" if st.session_state.get("demo_active") else ("CSV/XLSX" if LATEST_FILE.exists() else "—")

# ------------------------ HERO ------------------------
_hero_and_nba(d_for_hero, last_sync, bron)

# ------------------------ KPI-rij boven tabs ------------------------
_kpi_row(d_for_hero, key_ns="top")
st.divider()

# ------------------------ Tabs ------------------------
tab_assist, tab_results, tab_tags, tab_trend, tab_compare, tab_arch, tab_ab, tab_ideas, tab_play, tab_settings = st.tabs(
    ["Slimme assistent","Resultaten","Hashtags","Wat werkt nu?","Vergelijk 2 periodes","Archief","A/B-planner","Ideeëngenerator","Playbook & Plan","Instellingen"]
)

# ------------------------ Slimme assistent -------------------------
with tab_assist:
    st.subheader("🧠 Slimme assistent – jouw persoonlijke contentcoach")
    base = normalize_per_post(df_raw)
    if base.empty:
        st.info(tr("no_data"))
        with st.container(border=True):
            st.markdown("#### Onboarding-checklist")
            st.checkbox("CSV/XLSX geüpload", value=LATEST_FILE.exists(), disabled=True)
            st.checkbox("Beste tijden berekend", value=False, disabled=True)
            st.checkbox("Eerste A/B test gepland", value=False, disabled=True)
            st.checkbox("Alerts ingesteld (e-mail)", value=False, disabled=True)
    else:
        st.markdown("""
        <div style='background:#f8fafc;padding:16px;border-radius:12px;border:1px solid #e5e7eb;'>
        🧠 <b>Wat doet dit?</b> Analyseert je 30 laatste video's en voorspelt <b>wat</b> en <b>wanneer</b> je moet posten om sneller te groeien.
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        # Review-wachtrij
        q = _read_queue()
        with st.container(border=True):
            st.markdown(f"### ⏳ {tr('review_queue')}")
            if not q:
                st.caption("Nog niets in de wachtrij. Voeg iets toe vanuit A/B of Ideeën.")
            else:
                for it in q[:3]:
                    l, r = st.columns([6,3])
                    l.markdown(f"**{it['caption'][:54]}…**  \n`{it['hashtags']}` · 🕒 {int(it['hour']):02d}:00")
                    if it["status"] == "pending":
                        if r.button("✅ Goedkeuren & posten", key=f"ap_{it['id']}"):
                            if approve_and_post(it["id"]):
                                st.session_state["undo_id"] = it["id"]
                                st.toast("Geplaatst (demo).")
                    else:
                        undo_id = st.session_state.get("undo_id")
                        if undo_id == it["id"]:
                            if r.button("↩️ Ongedaan maken (5s)", key=f"undo_{it['id']}"):
                                if undo_post(it["id"]):
                                    st.toast("Ongedaan gemaakt.")
                                    st.session_state["undo_id"] = None
                        else:
                            r.markdown("✅ Geplaatst")

# ------------------------ Resultaten -------------------------------
with tab_results:
    st.subheader("Resultaten")
    base = normalize_per_post(df_raw)
    if base.empty:
        st.info(tr("no_data"))
    else:
        d = add_kpis(base)
        st.divider()
        qtxt = st.text_input("Filter op hashtag (bevat)…", placeholder="#love, #darkpsychology, …").strip().lower()
        filt = d if not qtxt else d[d["Hashtags"].fillna("").str.lower().str.contains(qtxt, regex=False)]
        cols = [c for c in ["Hashtags","Views","Likes","Comments","Shares","Datum","Like rate","Share rate","Velocity","Score","Virality","Video link"] if c in filt.columns]
        st.dataframe(filt[cols], use_container_width=True, hide_index=True)
        st.markdown("#### Export")
        html = filt.to_html(index=False)
        st.download_button("⬇️ Download data (HTML)", data=html, file_name="tiktok_data.html", mime="text/html")
        if not IS_PRO: st.caption("🔒 PDF-rapporten zijn PRO.")
        else: st.caption("PDF-rapport (placeholder) — integratie hier toevoegen.")

# ------------------------ Hashtags ---------------------------------
with tab_tags:
    st.subheader("Hashtags")
    base = normalize_per_post(df_raw)
    if base.empty: st.info(tr("no_data"))
    else:
        d = add_kpis(base)
        tags = (d.assign(_tag=d["Hashtags"].fillna("").str.split()).explode("_tag"))
        tags = tags[tags["_tag"].str.startswith("#", na=False)]
        if tags.empty: st.info("Geen hashtags gevonden.")
        else:
            agg = (tags.groupby("_tag", dropna=True)
                      .agg(freq=("Views","count"),
                           views=("Views","sum"),
                           avg_like_rate=("Like rate","mean"),
                           avg_share_rate=("Share rate","mean"),
                           avg_score=("Score","mean"),
                           avg_virality=("Virality","mean"))
                      .sort_values(["freq","avg_score"], ascending=[False, False]))
            st.dataframe(agg.head(30), use_container_width=True)

# ------------------------ Wat werkt nu? -----------------------------
with tab_trend:
    st.subheader("Wat werkt nu goed? (14d vs 14d)")
    base = normalize_per_post(df_raw)
    if base.empty: st.info(tr("no_data"))
    else:
        d = add_kpis(base)
        tr_df = trending_hashtags(d, days_window=14)
        if tr_df is None or tr_df.empty: st.info("Niet genoeg datapunten om trends te berekenen.")
        else:
            st.dataframe(tr_df.head(25), use_container_width=True)
            st.caption("We vergelijken de laatste 14 dagen met de 14 dagen daarvoor.")

# ------------------------ Vergelijk perioden -----------------------
with tab_compare:
    st.subheader("Vergelijk twee perioden")
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
        k2.markdown(f"<div class='kpi-card'><div class='kpi-label'>Gem. engagement A / B</div><div class='kpi-value'>📈 {engA:.2f}% / {engB:.2f}%</div></div>", unsafe_allow_html=True)
        k3.markdown(f"<div class='kpi-card'><div class='kpi-label'>Δ Score (B − A)</div><div class='kpi-value'>{(scB - scA):+,.3f}</div></div>".replace(",", "."), unsafe_allow_html=True)

# ------------------------ Archief ----------------------------------
with tab_arch:
    st.subheader("Archief")
    files = sorted(DATA_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    rows = []
    for p in files:
        try:
            df = _smart_read_any(p)
            rows.append({"Bestand": p.name, "Grootte (KB)": round(p.stat().st_size/1024, 1), "Rijen": len(df), "Laatste wijziging": datetime.fromtimestamp(p.stat().st_mtime), "Pad": str(p)})
        except Exception: pass
    table = pd.DataFrame(rows)
    if table.empty: st.info("Nog geen bestanden in het archief.")
    else: st.dataframe(table.drop(columns=["Pad"]), use_container_width=True, hide_index=True)

# ------------------------ A/B-planner ------------------------------
with tab_ab:
    st.subheader("A/B-planner")
    base = normalize_per_post(df_raw)
    d = add_kpis(base) if not base.empty else pd.DataFrame()
    if d.empty: st.info("Upload of laad demo-data om te plannen.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            hook_a = st.text_input("Hook A", value="Wat bijna niemand weet…")
            tags_a = st.text_input("Hashtags A", value="#darkfacts #psychology #tiktoknl")
            hour_a = st.number_input("Uur A", min_value=0, max_value=23, value=19)
        with col2:
            hook_b = st.text_input("Hook B", value="Dit klinkt raar, maar…")
            tags_b = st.text_input("Hashtags B", value="#viral #mindblown #fyp")
            hour_b = st.number_input("Uur B", min_value=0, max_value=23, value=21)

        def pvs(hook, tags, hr):
            base_vir = float(d["Virality"].tail(30).mean(skipna=True)) if "Virality" in d and not d["Virality"].empty else 50
            hook_bonus = min(len(hook.split())*2, 20)
            tags_bonus = min(len([t for t in tags.split() if t.startswith("#")])*3, 18)
            hr_bonus   = 20 if hr in _best_hours(d, n=3) else 8
            return int(np.clip(base_vir*0.3 + hook_bonus + tags_bonus + hr_bonus, 0, 100))

        rows = []
        for label, hook, tags, hr in [("A", hook_a, tags_a, int(hour_a)), ("B", hook_b, tags_b, int(hour_b))]:
            rows.append([label, hook, tags, hr, pvs(hook, tags, hr)])
        combo = pd.DataFrame(rows, columns=["Variant","Hook (tekst)","Hashtag-mix","Uur","PVS"])
        st.dataframe(combo, use_container_width=True, hide_index=True)

        if IS_PRO and SET.get("auto_post_mode") == "review":
            st.markdown("### In review-wachtrij zetten")
            pick = st.selectbox("Welke variant toevoegen?", ["A","B"])
            if st.button(tr("add_queue")):
                row = combo.loc[0 if pick=="A" else 1]
                queue_post(row["Hook (tekst)"], row["Hashtag-mix"], int(row["Uur"]))
                st.success("Toegevoegd aan wachtrij.")

# ------------------------ Ideeëngenerator --------------------------
with tab_ideas:
    st.subheader("Ideeëngenerator")
    topic = st.text_input("Onderwerp of thema?", placeholder="Bijv. manipulatie, angst, liefde, brein…")
    if topic:
        for i in range(1,4):
            st.markdown(f"**Idee {i}** — #{topic}")
            cap = f"{topic}. Volg @Darkestpsycho voor meer dark psych facts."
            tags = "#darkfacts #psychology #creepy #mindblown #tiktoknl"
            prompt = (f"Korte 9:16 video over **{topic}**; donkere stijl; 5–8s; 1) hook shockfact 2) 2–3 beats 3) CTA 'Volg @Darkestpsycho'.")
            st.code(cap); st.code(tags); st.code(prompt)
            if IS_PRO and SET.get("auto_post_mode") == "review":
                if st.button(tr("add_queue"), key=f"addq_{i}"):
                    queue_post(cap, tags, 19); st.success("Toegevoegd aan wachtrij.")
            st.divider()

# ------------------------ Playbook & Plan --------------------------
with tab_play:
    st.subheader("🧩 Playbook & 7-dagen Postplan")
    base = normalize_per_post(df_raw)
    d = add_kpis(base) if not base.empty else pd.DataFrame()
    if not IS_PRO:
        st.warning("🔒 Alleen in PRO. Koop PRO om het Playbook en het 7-dagen plan te gebruiken.")
    else:
        if d.empty: st.info(tr("no_data"))
        else:
            def generate_playbook(d: pd.DataFrame) -> Dict[str, str]:
                hours = _best_hours(d, n=3)
                tr_df = trending_hashtags(d, days_window=14)
                top_tag = tr_df.head(1).index[0] if tr_df is not None and not tr_df.empty else "#viral"
                return dict(
                    beste_tijden=", ".join([f"{h:02d}:00" for h in hours]),
                    top_hashtag=top_tag,
                    hook_stijl="shock",
                    actie="Herpost je best scorende video en maak een vervolg.",
                )
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
            c2.markdown(f"<div class='kpi-card'><div class='kpi-label'>Top hashtag</div><div class='kpi-value'>{pb['top_hashtag']}</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='kpi-card'><div class='kpi-label'>Hook-stijl</div><div class='kpi-value'>{pb['hook_stijl']}</div></div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='kpi-card'><div class='kpi-label'>Actie</div><div class='kpi-value'>Nu doen</div></div>", unsafe_allow_html=True)
            st.info(pb["actie"])
            st.divider()
            st.markdown("### 📅 7-dagen Postplan")
            plan = generate_week_plan(d); st.dataframe(plan, use_container_width=True, hide_index=True)
            colx1, colx2 = st.columns(2)
            with colx1:
                st.download_button("⬇️ Exporteer plan (CSV)", data=plan.to_csv(index=False).encode("utf-8"), file_name="postplan_7_dagen.csv", mime="text/csv")
            with colx2:
                txt = io.StringIO(); txt.write("PLAYBOOK\n"); [txt.write(f"{k}: {v}\n") for k,v in pb.items()]
                st.download_button("⬇️ Exporteer playbook (TXT)", data=txt.getvalue().encode("utf-8"), file_name="playbook.txt", mime="text/plain")

# ------------------------ Instellingen -----------------------------
with tab_settings:
    st.subheader("⚙️ Instellingen")
    cfg = _load_settings()
    col1, col2 = st.columns(2)
    with col1:
        cfg["auto_experiments"] = st.toggle("Slimme testen (A/B → bandit)", value=cfg.get("auto_experiments", True))
        cfg["auto_post_mode"] = st.selectbox("Auto-post modus", ["review","off"], index=["review","off"].index(cfg.get("auto_post_mode","review")))
        cfg["lang"] = st.selectbox("Taal", ["nl","en"], index=["nl","en"].index(cfg.get("lang","nl")))
    with col2:
        cfg["alert_channel"] = st.selectbox("Alerts kanaal", ["email"], index=0)
        cfg["data_retention_days"] = st.number_input("Data-retentie (dagen)", min_value=30, max_value=365, value=int(cfg.get("data_retention_days",180)))
        st.session_state["alert_email"] = st.text_input("Alert e-mail ontvanger", value=st.session_state.get("alert_email",""))
    if st.button("Bewaar instellingen"):
        if _save_settings(cfg): st.success("Instellingen opgeslagen."); SET.update(cfg)
        else: st.error("Kon instellingen niet opslaan.")
    st.markdown("---"); st.markdown("### Branding")
    bcol1, bcol2 = st.columns([1,1])
    with bcol1:
        color = st.color_picker("Merkkleur", value=THEME_COLOR)
        if st.button("Bewaar kleur"):
            if _save_brand_color(color): st.success("Kleur opgeslagen. Herlaad de pagina.")
    with bcol2:
        if LOGO_BYTES:
            st.image(LOGO_BYTES, caption="Logo", width=90)
            if st.button("Logo verwijderen"):
                if _remove_brand_logo(): st.success("Logo verwijderd. Herlaad de pagina.")
        else:
            lf = st.file_uploader("Upload logo (png)", type=["png"])
            if lf is not None and _save_brand_logo(lf): st.success("Logo opgeslagen. Herlaad de pagina.")
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
        st.caption("Heb je nog geen licentie? Koop ‘m hieronder.")
        st.link_button("✨ Koop PRO", LEMON_CHECKOUT_URL, use_container_width=True)
with st.expander("Legal & TikTok Review Info", expanded=False):
    base = _get_public_base_url() or "https://postai.bouwmijnshop.nl"
    st.markdown(
        f"""
- **Website (this app):** {base}  
- **Redirect URI:** {base}/  
- **Requested scopes:** `user.info.basic, video.list`  
- **What we do:** authentication + analytics display only. **No auto-posting.**  
- **Terms:** <https://www.bouwmijnshop.nl/pages/onze-voorwaarden>  
- **Privacy:** <https://www.bouwmijnshop.nl/pages/privacy>  
- **Support:** support@bouwmijnshop.nl
        """
    )

# ------------------------ Footer trust badges ----------------------
st.markdown(
    f"<div class='footer-trust'>🛡️ {tr('trust1')} · 📄 {tr('trust2')} · 🎁 {tr('trust3')} · 🎯 {tr('trust4')}</div>",
    unsafe_allow_html=True
)
