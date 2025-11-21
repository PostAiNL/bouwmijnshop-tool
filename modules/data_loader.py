import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def load_file(uploaded_file):
    """Leest CSV of Excel bestand in."""
    try:
        if uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            return pd.read_excel(uploaded_file)
    except Exception as e:
        return pd.DataFrame() # Leeg frame bij error
    return pd.DataFrame()

def load_demo_data():
    """Genereert realistische dummy data voor de demo modus."""
    # Maak 30 dagen aan data
    dates = [datetime.now() - timedelta(days=x) for x in range(30)]
    
    data = {
        'Datum': dates,
        'Views': np.random.randint(100, 15000, size=30), # Random views tussen 100 en 15k
        'Likes': [],
        'Caption': [f"Video over onderwerp {i}" for i in range(30)],
        'Video titel': [f"Hook {i}: Dit geloof je niet..." for i in range(30)]
    }
    
    # Likes logisch maken t.o.v. views (ongeveer 5-10%)
    for v in data['Views']:
        data['Likes'].append(int(v * np.random.uniform(0.05, 0.12)))
        
    df = pd.DataFrame(data)
    # Zorg voor 1 uitschieter (viral video)
    df.loc[3, 'Views'] = 85000
    df.loc[3, 'Likes'] = 12000
    df.loc[3, 'Caption'] = "Mijn viral video strategie"
    
    return df