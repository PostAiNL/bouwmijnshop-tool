import requests
import json
import itertools

def push_product_to_shopify(shop_url, access_token, product_data):
    """
    Pusht product naar Shopify. 
    UPDATE: Ondersteunt nu Multi-Option Matrix (bv. Kleur + Maat combinaties).
    """
    # URL Opschonen
    shop_url = shop_url.replace("https://", "").replace("http://", "").strip()
    if "/" in shop_url: shop_url = shop_url.split("/")[0]
    
    api_url = f"https://{shop_url}/admin/api/2024-01/products.json"
    
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    
    # Data voorbereiden
    price = str(product_data.get("price", "29.95"))
    compare = str(product_data.get("compare_price", "59.95"))
    title = product_data.get("title", "Naamloos Product")
    
    variants = []
    options = []
    
    # Stap 1: Opties structureren
    raw_options = product_data.get("options", [])
    
    if raw_options:
        # Formatteer opties voor Shopify (Name + Values)
        for opt in raw_options:
            options.append({"name": opt["name"], "values": opt["values"]})
        
        # Stap 2: Variant Matrix Genereren (Cartesian Product)
        # Dit zorgt ervoor dat [Rood, Blauw] x [S, M] = 4 varianten worden
        option_values_list = [opt["values"] for opt in raw_options]
        all_combinations = list(itertools.product(*option_values_list))
        
        for combo in all_combinations:
            # Combo is bv ('Rood', 'S')
            variant_title = " / ".join(combo)
            
            variant_data = {
                "price": price,
                "compare_at_price": compare,
                "sku": f"RM-{title[:3].upper()}-{'-'.join(combo)}".replace(" ", ""),
                "inventory_management": None, # Of "shopify" als je voorraad wilt tracken
                "requires_shipping": True
            }
            
            # Wijs opties toe aan option1, option2, option3 (Shopify limiet is 3)
            for i, val in enumerate(combo):
                if i < 3:
                    variant_data[f"option{i+1}"] = val
            
            variants.append(variant_data)
            
    else:
        # Fallback: Geen opties, 1 standaard variant
        variants.append({
            "option1": "Default Title",
            "price": price,
            "compare_at_price": compare,
            "sku": f"RM-{title[:3].upper()}-001",
            "inventory_management": None,
            "requires_shipping": True
        })
        # Shopify vereist geen options array als er maar 1 variant is met "Default Title",
        # maar voor netheid kunnen we options leeg laten.

    images = []
    if product_data.get("image_url"):
        images.append({"src": product_data["image_url"]})

    # Stap 3: Payload bouwen
    payload = {
        "product": {
            "title": title,
            "body_html": product_data.get("description"),
            "vendor": "RM Ecom AI",
            "product_type": product_data.get("niche", "General"),
            "status": "active",
            "images": images,
            "variants": variants,
            "options": options if raw_options else None, # Alleen meesturen als er opties zijn
            "metafields_global_title_tag": product_data.get("meta_title"),
            "metafields_global_description_tag": product_data.get("meta_description")
        }
    }
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        if response.status_code == 201:
            data = response.json()
            return {
                "success": True, 
                "id": data["product"]["id"], 
                "handle": data["product"]["handle"], 
                "msg": f"✅ '{title}' succesvol geïmporteerd met {len(variants)} varianten!"
            }
        else:
            return {"success": False, "msg": f"Shopify Fout ({response.status_code}): {response.text}"}
    except Exception as e:
        return {"success": False, "msg": f"Connectie Fout: {e}"}