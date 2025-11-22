import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def load_demo_data():
    """Realistische demo data voor de showcase."""
    dates = [datetime.now() - timedelta(days=x) for x in range(30)]
    # Maak een patroon: in het weekend meer views
    data = []
    for d in dates:
        is_weekend = d.weekday() >= 5
        base_views = np.random.randint(1000, 5000)
        if is_weekend: base_views *= 3 # Meer views in weekend
        
        # Simuleer een 'viral' hit
        if np.random.random() > 0.9: base_views *= 10
        
        likes = int(base_views * np.random.uniform(0.05, 0.15))
        
        data.append({
            "Datum": d,
            "Views": base_views,
            "Likes": likes,
            "Caption": f"Video over tips #{np.random.randint(1,100)} #groei #ondernemen"
        })
        
    return pd.DataFrame(data)

def load_file(uploaded_file):
    """Robuuste loader voor CSV en Excel."""
    try:
        if uploaded_file.name.endswith('.xlsx'):
            return pd.read_excel(uploaded_file)
            
        # CSV proberen met verschillende separators
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, sep=',')
        except:
            try:
                uploaded_file.seek(0)
                return pd.read_csv(uploaded_file, sep=';')
            except:
                return pd.DataFrame()
                
    except Exception as e:
        print(f"Load error: {e}")
        return pd.DataFrame()