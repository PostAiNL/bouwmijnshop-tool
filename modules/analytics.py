import pandas as pd
import numpy as np
import re
from datetime import datetime

def parse_smart_number(val):
    if pd.isna(val): return 0
    s = str(val).lower().strip()
    mult = 1
    if 'k' in s: mult = 1000; s = s.replace('k', '')
    if 'm' in s: mult = 1000000; s = s.replace('m', '')
    s = re.sub(r"[^0-9.,]", "", s)
    try:
        if '.' in s and ',' in s: s = s.replace('.', '').replace(',', '.')
        elif ',' in s: s = s.replace(',', '.')
        return int(float(s) * mult)
    except: return 0

def clean_data(df):
    if df.empty: return pd.DataFrame()
    # Maak kolomnamen lowercase en strip spaties
    df.columns = [c.lower().strip().replace(" ", "") for c in df.columns]
    
    # Mapping
    map_cols = {
        'video_views': 'Views', 'views': 'Views', 'play_count': 'Views',
        'likes': 'Likes', 'digg_count': 'Likes',
        'publish_time': 'Datum', 'create_time': 'Datum', 'date': 'Datum',
        'description': 'Caption', 'title': 'Caption', 'caption': 'Caption'
    }
    
    # Hernoem kolommen als ze bestaan
    new_df = pd.DataFrame()
    found_cols = df.columns
    
    # Zoek de juiste kolommen
    for k, v in map_cols.items():
        # Zoek naar partial match (bv 'video publish time')
        for col in found_cols:
            if k in col and v not in new_df.columns:
                new_df[v] = df[col]
    
    # Als we minimale data hebben
    if 'Views' in new_df.columns:
        new_df['Views'] = new_df['Views'].apply(parse_smart_number)
    else: return pd.DataFrame() # Geen views = nutteloos
        
    if 'Likes' in new_df.columns: new_df['Likes'] = new_df['Likes'].apply(parse_smart_number)
    else: new_df['Likes'] = 0
    
    if 'Datum' in new_df.columns:
        new_df['Datum'] = pd.to_datetime(new_df['Datum'], errors='coerce')
    else:
        new_df['Datum'] = datetime.now() # Fallback

    if 'Caption' not in new_df.columns: new_df['Caption'] = "-"
    
    return new_df.dropna(subset=['Views'])

def calculate_kpis(df):
    if df.empty: return df
    d = df.copy()
    # Engagement: (Likes / Views) * 100
    d['Engagement'] = (d['Likes'] / d['Views'].replace(0, 1)) * 100
    return d.sort_values('Datum', ascending=False)

def get_best_posting_time(df):
    if df.empty: return pd.DataFrame({'Uur': [12], 'Views': [0]})
    d = df.copy()
    d['Uur'] = d['Datum'].dt.hour
    # Groepeer op uur en pak gemiddelde views
    stats = d.groupby('Uur')['Views'].mean().reset_index()
    return stats.sort_values('Views', ascending=False).head(24)

def get_trending_hashtags(df):
    if df.empty or 'Caption' not in df.columns: return pd.DataFrame()
    
    # Extract hashtags
    tags = []
    for txt in df['Caption'].astype(str):
        found = re.findall(r"#(\w+)", txt)
        tags.extend(found)
        
    if not tags: return pd.DataFrame(columns=["Hashtag", "Aantal"])
    
    from collections import Counter
    c = Counter(tags)
    return pd.DataFrame(c.most_common(10), columns=["Hashtag", "Aantal"])