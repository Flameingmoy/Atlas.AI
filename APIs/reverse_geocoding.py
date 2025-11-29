import requests
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("LATLONG_TOKEN")

url = "https://apihub.latlong.ai/v4/reverse_geocode.json"

params = {
    "latitude": 12.9306361,
    "longitude": 77.5783206
}

headers = {
    "X-Authorization-Token": token
}

res = requests.get(url, params=params, headers=headers)

print("Status:", res.status_code)
print(res.text)
