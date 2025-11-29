import requests, os
from dotenv import load_dotenv

load_dotenv()

headers = {
    "X-Authorization-Token": os.getenv("LATLONG_TOKEN")
}

params = {
    "address": "3/80, IH Colony, MG Road, Goregaon West, Mumbai 400104",
    "accuracy_level": "true"
}

res = requests.get("https://apihub.latlong.ai/v4/geocode.json", headers=headers, params=params)

print(res.json())
