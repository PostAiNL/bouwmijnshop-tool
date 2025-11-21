import pandas as pd
import numpy as np
from datetime import datetime

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Schoont de data op, converteert datums en nummers."""
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Kolom mapping (case insensitive)
    cols = {c.lower().replace(" ", ""): c for c in df.columns}
    
    # Helper voor veilige conversie
    def to_int(val):
        try:
            s = str(val).lower().replace(',', '').replace('.', '')
            if 'k' in s: return int(float(s.replace('k', '')) * 1000)
            if 'm' in s: return int(float(s.replace('m', '')) * 1000000)
            return int(s)
        except: return 0

    # Standaardiseer DataFrame
    d = pd.DataFrame()
    
    # Zoek kolommen (flexibel)
    views_col = cols.get('views') or cols.get('weergaven') or cols.get('plays')
    date_col = cols.get('date') or cols.get('datum') or cols.get('time') or cols.get('posttime')
    likes_col = cols.get('likes') or cols.get('hartjes')
    
    if not views_col or not date_col:
        return pd.DataFrame() # Minimale vereisten

    d['Views'] = df[views_col].apply(to_int)
    d['Likes'] = df[likes_col].apply(to_int) if likes_col else 0
    d['Shares'] = df.get('Shares', 0) # Als deze kolom bestaat
    d['Caption'] = df.get('Caption', df.get('Video titel', ''))
    
    # Datum parsing (krachtig)
    d['Datum'] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
    d = d.dropna(subset=['Datum']) # Verwijder rijen zonder datum
    
    return d.sort_values('Datum', ascending=False)

def calculate_kpis(df: pd.DataFrame):
    """Berekent geavanceerde KPI's voor de 10/10 ervaring."""
    if df.empty: return df
    
    # 1. Engagement Rate (Likes + Shares / Views)
    # We voegen een kleine epsilon toe om deling door nul te voorkomen
    df['Engagement'] = ((df['Likes'] + df.get('Shares', 0)) / (df['Views'] + 1)) * 100
    
    # 2. Viral Score (Weighted: Views tellen zwaarder, maar engagement corrigeert)
    # We gebruiken logaritmische schaal voor views om viral hits te normaliseren
    log_views = np.log1p(df['Views'])
    scaled_views = (log_views - log_views.min()) / (log_views.max() - log_views.min() + 0.001)
    df['Viral Score'] = (scaled_views * 70) + (np.clip(df['Engagement'], 0, 20) * 1.5)
    df['Viral Score'] = df['Viral Score'].clip(0, 100).round(0)
    
    return df

def get_best_posting_time(df: pd.DataFrame) -> int:
    """Bepaalt het beste uur obv historische prestaties (mediaan views per uur)."""
    if df.empty: return 19 # Fallback
    
    df['Hour'] = df['Datum'].dt.hour
    # We filteren uren met minder dan 3 posts om toeval te voorkomen
    hourly_stats = df.groupby('Hour')['Views'].median()
    
    if hourly_stats.empty: return 19
    return int(hourly_stats.idxmax())

def get_consistency_streak(df: pd.DataFrame) -> int:
    """Nieuwe Feature: Berekent hoeveel dagen op rij er gepost is (Gamification)."""
    if df.empty: return 0
    
    dates = df['Datum'].dt.date.sort_values(ascending=False).unique()
    if len(dates) == 0: return 0
    
    today = datetime.now().date()
    streak = 0
    
    # Check of de laatste post vandaag of gisteren was om streak te behouden
    if (today - dates[0]).days > 1:
        return 0
        
    # Tel terug
    current_check = dates[0]
    for d in dates:
        if (current_check - d).days <= 1:
            streak += 1
            current_check = d
        else:
            break
    return streak