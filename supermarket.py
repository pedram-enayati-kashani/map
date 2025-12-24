import requests
import json

MANUAL_BBOX = {
    # English
    "Tehran": (35.60, 51.20, 35.80, 51.60),
    "Isfahan": (32.60, 51.50, 32.80, 51.80),
    "Mashhad": (36.20, 59.40, 36.40, 59.70),
    "Shiraz": (29.50, 52.40, 29.70, 52.70),
    "Tabriz": (38.00, 46.20, 38.20, 46.40),
    "Karaj": (35.75, 50.90, 35.90, 51.10),
    "Qom": (34.60, 50.80, 34.75, 51.00),
    # Persian
    "تهران": (35.60, 51.20, 35.80, 51.60),
    "اصفهان": (32.60, 51.50, 32.80, 51.80),
    "مشهد": (36.20, 59.40, 36.40, 59.70),
    "شیراز": (29.50, 52.40, 29.70, 52.70),
    "تبریز": (38.00, 46.20, 38.20, 46.40),
    "کرج": (35.75, 50.90, 35.90, 51.10),
    "قم": (34.60, 50.80, 34.75, 51.00),
}

def nominatim(city_name):
    queries = [f"{city_name}, Iran", city_name]
    for query in queries:
        try:
            resp = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "json", "limit": 1},
                headers={"User-Agent": "SupermarketFinder (pedram@example.com)"},
                timeout=8
            )
            if resp.ok and resp.json():
                bbox = resp.json()[0]["boundingbox"]
                south, north, west, east = map(float, bbox)
                return (south, west, north, east)
        except Exception:
            continue
    return None

def supermarkets():
    city_name = input("city: ").strip()
    if not city_name:
        print(json.dumps({"error": "City name is required"}, indent=2))
        return
    bbox = nominatim(city_name)
    if bbox is None:
        bbox = MANUAL_BBOX.get(city_name.strip())
    
    if bbox is None:
        return {
            "error": "City not found",
            "message": f"Could not locate '{city_name}'. Try major cities like Tehran, Isfahan, etc."
        }

    south, west, north, east = bbox
    bbox_str = f"{south},{west},{north},{east}"

    query = f"""
        [out:json][timeout:30];
        (
        node["shop"="supermarket"]({bbox_str});
        node["shop"="convenience"]({bbox_str});
        node["shop"="grocery"]({bbox_str});
        node["shop"="yes"]({bbox_str});
        node["name"~"supermarket|سوپرمارکت|فروشگاه",i]({bbox_str});
        );
        out body;
    """

    try:
        resp = requests.post("https://overpass-api.de/api/interpreter", data=query, timeout=40)
        if not resp.ok:
            return {"error": "Overpass API error", "code": resp.status_code}

        data = resp.json()
        results = []
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            address = " ".join(filter(None, [
                tags.get("addr:street"),
                tags.get("addr:housenumber"),
                tags.get("addr:city")
            ])) or "No address"
            results.append({
                "name": tags.get("name", "Unnamed"),
                "phone": tags.get("phone"),
                "location": {"lat": el.get("lat"), "lng": el.get("lon")},
                "address": address
            })

        return {
            "city": city_name,
            "source": "OpenStreetMap",
            "total": len(results),
            "data": results
        }
    except Exception as e:
        return {"error": "Request failed", "details": str(e)}

def main():
    result = supermarkets()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()