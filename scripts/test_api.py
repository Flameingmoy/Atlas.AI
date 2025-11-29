import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    print("Testing /health...")
    try:
        resp = requests.get(f"http://localhost:8000/health") # Note: Health might be at root or api/v1 depending on router
        # My router was included with prefix /api/v1, but I put health in the router.
        # Let's check main.py... app.include_router(router, prefix="/api/v1")
        # So it should be /api/v1/health
        resp = requests.get(f"{BASE_URL}/health")
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
    except Exception as e:
        print(f"Failed: {e}")

def test_scoring():
    print("\nTesting /analyze/score...")
    payload = {
        "traffic": 8.5,
        "competition": 2.0, # Low competition
        "demand": 7.0,
        "access": 9.0,
        "synergy": 5.0
    }
    try:
        resp = requests.post(f"{BASE_URL}/analyze/score", params=payload)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
    except Exception as e:
        print(f"Failed: {e}")

def test_clustering():
    print("\nTesting /analyze/clusters...")
    # Generate some dummy points around Austin
    points = [
        [30.26, -97.74], [30.261, -97.741], [30.262, -97.742], # Cluster 1
        [30.30, -97.70], [30.301, -97.701], [30.302, -97.702], # Cluster 2
        [30.40, -97.80] # Noise
    ]
    try:
        resp = requests.post(f"{BASE_URL}/analyze/clusters", json=points)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_health()
    test_scoring()
    test_clustering()
