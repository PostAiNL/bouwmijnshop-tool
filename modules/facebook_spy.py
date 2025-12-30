from apify_client import ApifyClient
import streamlit as st
import urllib.parse
from datetime import datetime
import re

# ==============================================================================
# ⚠️ PLAK HIERONDER JOUW APIFY API TOKEN
# ==============================================================================
APIFY_TOKEN = "apify_api_Dlkr5QoOydIZCJe6NbXcBHMg4TLHwZ2f1PIA"
# ==============================================================================

def clean_html(raw_html):
    """Verwijderd HTML tags uit tekst."""
    if not raw_html: return ""
    clean = re.sub('<[^<]+?>', '', str(raw_html))
    return clean.strip()

def parse_days_active(item_data, snapshot):
    """
    Zoekt agressief naar een startdatum in de data en berekent dagen actief.
    """
    potential_dates = [
        item_data.get('startDate'),
        item_data.get('creationTime'),
        item_data.get('publishDate'),
        snapshot.get('creation_time'),
        snapshot.get('start_date')
    ]

    found_date = None

    for date_val in potential_dates:
        if date_val:
            try:
                # Optie A: Timestamp
                if isinstance(date_val, (int, float)):
                    if date_val > 2000000000: date_val /= 1000
                    found_date = datetime.fromtimestamp(date_val)
                    break
                # Optie B: Tekst
                elif isinstance(date_val, str):
                    date_str = date_val.split('T')[0]
                    found_date = datetime.strptime(date_str, "%Y-%m-%d")
                    break
            except:
                continue
    
    if found_date:
        found_date = found_date.replace(tzinfo=None)
        now = datetime.now().replace(tzinfo=None)
        diff = (now - found_date).days
        return max(1, diff) # Minimaal 1 dag
    
    return 1

@st.cache_data(ttl=7200, show_spinner=False)
def search_facebook_ads(keyword, country="NL", max_results=30): # <--- AANGEPAST NAAR 30
    if "PLAK_HIER" in APIFY_TOKEN: return []

    try:
        client = ApifyClient(APIFY_TOKEN)

        base_url = "https://www.facebook.com/ads/library/?"
        country_code = country if country != "ALL" else "ALL"
        
        params = {
            "active_status": "active",
            "ad_type": "all",
            "country": country_code,
            "media_type": "video",
            "q": keyword,
            "search_type": "keyword_unordered"
        }
        target_url = base_url + urllib.parse.urlencode(params)

        run_input = {
            "urls": [{"url": target_url}], 
            "maxItems": max_results,
            "pageLimit": 1 # 1 pagina is genoeg voor 30 items
        }

        run = client.actor("curious_coder/facebook-ads-library-scraper").call(run_input=run_input)

        if not run: return []

        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        results = []
        for item in dataset_items:
            snapshot = item.get('snapshot', {})
            
            # Media logic
            media_url, is_video = None, False
            videos = snapshot.get('videos', [])
            images = snapshot.get('images', [])
            cards = snapshot.get('cards', [])

            if videos:
                media_url = videos[0].get('video_preview_image_url') or videos[0].get('video_hd_url')
                is_video = True
            elif cards:
                 if cards[0].get('video_preview_image_url'):
                     media_url = cards[0].get('video_preview_image_url')
                     is_video = True
                 else:
                     media_url = cards[0].get('original_image_url')
            elif images:
                media_url = images[0].get('original_image_url')

            # Tekst logic
            raw_text = (
                snapshot.get('body', {}).get('markup', {}).get('__html') or 
                snapshot.get('body', {}).get('text') or 
                item.get('adBody') or
                snapshot.get('title') or 
                "Geen tekst beschikbaar."
            )
            if (not raw_text or "Geen tekst" in raw_text) and cards:
                 raw_text = cards[0].get('body') or cards[0].get('title')

            caption = clean_html(raw_text)

            # Data logic
            days_active = parse_days_active(item, snapshot)
            shop_link = snapshot.get('link_url') or snapshot.get('cta_link')
            ad_id = item.get('id', '0')
            
            if not shop_link: shop_link = f"https://www.facebook.com/ads/library/?id={ad_id}"

            if media_url:
                results.append({
                    "page_name": snapshot.get('page_name', 'Onbekend'),
                    "page_profile_picture_url": snapshot.get('page_profile_picture_url', ''),
                    "caption": caption,
                    "media": media_url,
                    "is_video": is_video,
                    "days_active": days_active,
                    "shop_link": shop_link,
                    "ad_id": ad_id
                })
            
        return results

    except Exception as e:
        print(f"Scrape Fout: {e}")
        return []