import requests
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("LATLONG_TOKEN")

if not token:
    raise RuntimeError("LATLONG_TOKEN missing in .env")

url = "https://apihub.latlong.ai/v4/geovalidation.json"

params = {
    "address": "3/80, IH Colony, MG Road, Goregaon West, Mumbai 400104",
    "latitude": 19.163051,
    "longitude": 72.839485
}

headers = {
    "X-Authorization-Token": token
}

response = requests.get(url, params=params, headers=headers)

print("Status:", response.status_code)
print(response.json())
