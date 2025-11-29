import requests
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("LATLONG_TOKEN")

if not token:
    raise RuntimeError("LATLONG_TOKEN missing in .env")

url = "https://apihub.latlong.ai/v4/point_of_interest.json"

params = {
    "latitude": 12.8974787,
    "longitude": 77.5796369,
    "category": "MORTH,Pin Code"
}

headers = {
    "X-Authorization-Token": token
}

res = requests.get(url, params=params, headers=headers)

print("Status:", res.status_code)
print(res.json())
