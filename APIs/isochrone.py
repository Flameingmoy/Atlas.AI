import requests
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("LATLONG_TOKEN")

if not token:
    raise RuntimeError("LATLONG_TOKEN missing in .env")

url = "https://apihub.latlong.ai/v4/isochrone.json"

params = {
    "latitude": 12.9149,
    "longitude": 77.52068,
    "distance_limit": 1  # in kilometers
}

headers = {
    "X-Authorization-Token": token
}

response = requests.get(url, params=params, headers=headers)

print("Status:", response.status_code)
print(response.json())
