import requests
from dotenv import load_dotenv
import os

# Load .env from current working directory
load_dotenv()

# Read token
token = os.getenv("LATLONG_TOKEN")
if not token:
    raise RuntimeError("LATLONG_TOKEN missing — check your .env file")

url = "https://apihub.latlong.ai/v4/landmarks.json"

params = {
    "lat": 19.163051,
    "lon": 72.839485
}

headers = {
    "X-Authorization-Token": token
}

res = requests.get(url, params=params, headers=headers)

print(res.json())
