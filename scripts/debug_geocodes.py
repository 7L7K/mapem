import requests
import urllib.parse

PLACES = [
    "compton, los angeles county, california, united states",
    "elwood, will county, illinois, united states",
    "moorehead lake dam, grenada county, mississippi, 38940, united states",
    "h w morehead road, scott county, mississippi, 39152, united states",
]

API_URL = "http://localhost:5050/api/geocode"

print("🔍 Testing geocoding endpoint...\n")

for place in PLACES:
    try:
        encoded = urllib.parse.quote(place)
        full_url = f"{API_URL}?place={encoded}"
        print(f"➡️ Requesting: {place}")
        response = requests.get(full_url)
        response.raise_for_status()

        data = response.json()
        print(f"✅ Response: {data}\n")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed for {place}: {e}\n")
    except Exception as e:
        print(f"🔥 Unexpected error for {place}: {e}\n")
