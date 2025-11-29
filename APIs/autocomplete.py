import requests
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("LATLONG_TOKEN")

if not token:
    raise RuntimeError("LATLONG_TOKEN missing in .env")

url = "https://apihub.latlong.ai/v4/autocomplete.json"

params = {
    "query": "delhi",
    # Optional:
    # "lat": 28.61,
    # "lon": 77.23,
    # "limit": 10,
    # "language": "en"
}

headers = {
    "X-Authorization-Token": token
}

response = requests.get(url, params=params, headers=headers)

print("Status:", response.status_code)
print(response.json())
