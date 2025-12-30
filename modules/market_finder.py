from apify_client import ApifyClient
import streamlit as st

# ==============================================================================
# ⚠️ PLAK HIERONDER JOUW APIFY API TOKEN (Dezelfde als bij TikTok)
# ==============================================================================
APIFY_TOKEN = "apify_api_Dlkr5QoOydIZCJe6NbXcBHMg4TLHwZ2f1PIA"
# ==============================================================================

def search_amazon_products(keyword="gadgets", max_results=5):
    """
    Gebruikt Apify (E-commerce Scraping Tool) om Amazon te doorzoeken.
    Dit is cruciaal om te kijken of je product niet al te goedkoop op Amazon staat.
    """
    if "PLAK_HIER" in APIFY_TOKEN:
        return []

    client = ApifyClient(APIFY_TOKEN)

    # We stellen hem in om Amazon US te scrapen (daar beginnen trends vaak)
    run_input = {
        "searchTerms": [keyword],
        "maxItems": max_results,
        "country": "US", 
        "language": "en",
        "proxy": {
            "useApifyProxy": True
        }
    }

    try:
        # Start de actor: apify/e-commerce-scraping-tool
        # Dit kost een heel klein beetje Apify tegoed per keer
        run = client.actor("apify/e-commerce-scraping-tool").call(run_input=run_input)

        # Resultaten ophalen
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        results = []
        for item in dataset_items:
            # Alleen items met een prijs en titel toevoegen
            if item.get('title') and item.get('price'):
                results.append({
                    "title": item.get('title'),
                    "price": item.get('price'),
                    "currency": item.get('currency', '$'),
                    "image": item.get('image'),
                    "url": item.get('url'),
                    "rating": item.get('rating', 'N/A'),
                    "reviews": item.get('reviewsCount', 0)
                })
        
        return results

    except Exception as e:
        print(f"Apify Market Fout: {e}")
        return []