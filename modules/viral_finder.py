from apify_client import ApifyClient
import streamlit as st
import random

# ⚠️ PLAK HIERONDER JOUW APIFY API TOKEN
APIFY_TOKEN = "apify_api_Dlkr5QoOydIZCJe6NbXcBHMg4TLHwZ2f1PIA"

def estimate_sales_revenue(views, likes):
    """Schatting van sales en omzet."""
    conversion_rate = 0.0015 # 0.15%
    avg_price = 29.95
    est_sales = int(views * conversion_rate)
    est_revenue = int(est_sales * avg_price)
    viral_score = min(100, int((likes / views * 500) + (views / 10000)))
    return est_sales, est_revenue, viral_score

@st.cache_data(ttl=3600, show_spinner=False)
def search_tiktok_winning_products(keyword, min_views, sort_by="views"):
    """
    Slimmere scraper: Voegt 'buy' intent keywords toe als de zoekterm te algemeen is.
    """
    if "PLAK_HIER" in APIFY_TOKEN:
        return []

    client = ApifyClient(APIFY_TOKEN)

    # SLIMME TRUC: Als het woord 'mode' of 'kleding' bevat, voeg 'haul' of 'musthave' toe
    # Dit filtert de grappige filmpjes eruit en toont producten.
    search_term = keyword
    if " " not in keyword: # Als het maar 1 woord is, maak het specifieker
        search_term = f"{keyword} musthave"

    # We zoeken nu op trefwoorden (zoekfunctie) ipv alleen hashtags
    # Dit geeft betere resultaten voor producten.
    run_input = {
        "searchQueries": [search_term], 
        "resultsPerPage": 20,
        "searchSection": "",
        "shouldDownloadCovers": True,
    }

    try:
        # Gebruik een algemenere scraper die ook op zoekwoorden werkt, niet alleen hashtags
        # We gebruiken nog steeds de tiktok-scraper, maar nu via searchQueries
        run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        results = []
        for item in dataset_items:
            views = item.get('playCount', 0)
            likes = item.get('diggCount', 0)
            
            if views >= min_views:
                est_sales, est_revenue, score = estimate_sales_revenue(views, likes)
                
                results.append({
                    "id": item.get('id', str(random.randint(1000,9999))),
                    "desc": item.get('text', 'Geen titel'),
                    "views": views,
                    "likes": likes,
                    "cover": item.get('videoMeta', {}).get('coverUrl', ''),
                    "url": item.get('webVideoUrl', ''),
                    "author": item.get('authorMeta', {}).get('name', 'Unknown'),
                    "est_revenue": est_revenue,
                    "viral_score": score,
                    "days_ago": random.randint(1, 7) # Mockup voor demo
                })
        
        # Sorteren
        if sort_by == "revenue": results.sort(key=lambda x: x['est_revenue'], reverse=True)
        elif sort_by == "score": results.sort(key=lambda x: x['viral_score'], reverse=True)
        else: results.sort(key=lambda x: x['views'], reverse=True)
            
        return results[:6] # Top 6 resultaten

    except Exception as e:
        print(f"Apify Fout: {e}")
        return []