import requests
import time
from bs4 import BeautifulSoup

def scrape_shopify_store(url):
    """Bestaande functie voor Product Finder (ongewijzigd)."""
    clean_url = url.replace("https://", "").replace("http://", "").split("/")[0]
    target_url = f"https://{clean_url}/products.json?limit=12" 

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            products = data.get('products', [])
            results = []
            for p in products:
                img = None
                if p.get('images') and len(p['images']) > 0:
                    src = p['images'][0].get('src', '')
                    img = src if src.startswith('http') else f"https:{src}"
                
                price = "???"
                if p.get('variants') and len(p['variants']) > 0:
                    price = p['variants'][0].get('price', '???')
                
                pub_date = p.get('published_at', '')[:10] if p.get('published_at') else ""

                item = {
                    "title": p.get('title', 'Naamloos'),
                    "price": price,
                    "image_url": img,
                    "url": f"https://{clean_url}/products/{p.get('handle')}",
                    "published_at": pub_date
                }
                results.append(item)
            return results
        else: return None 
    except Exception as e:
        print(f"Scrape error: {e}")
        return None

# --- NIEUW: VOOR DE STORE DOCTOR ---
def scrape_homepage_text(url):
    """
    Haalt de tekst, titel en meta-description van een homepage op voor AI analyse.
    """
    if not url.startswith("http"):
        url = "https://" + url
        
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Haal belangrijke elementen op
            title = soup.title.string if soup.title else "Geen titel"
            meta = soup.find("meta", attrs={"name": "description"})
            desc = meta["content"] if meta else "Geen beschrijving"
            
            # Haal zichtbare tekst op (H1, H2, P)
            texts = []
            for tag in soup.find_all(['h1', 'h2', 'h3', 'p', 'span']):
                txt = tag.get_text(strip=True)
                if len(txt) > 20: # Alleen zinnige zinnen
                    texts.append(txt)
            
            # Beperk de tekst tot de eerste 3000 karakters (voor AI limieten)
            full_text = " ".join(texts)[:3000]
            
            return {
                "status": "success",
                "title": title,
                "description": desc,
                "content": full_text
            }
        else:
            return {"status": "error", "message": "Website onbereikbaar"}
    except Exception as e:
        return {"status": "error", "message": str(e)}