#!/usr/bin/env python3
import requests
import json

def test_endpoints():
    base_url = "http://localhost:8000"
    
    print("Testing server endpoints...")
    
    # Test /geo endpoint
    try:
        response = requests.get(f"{base_url}/geo")
        print(f"GET /geo: Status {response.status_code}, Response: '{response.text}'")
    except Exception as e:
        print(f"GET /geo error: {e}")
    
    # Test /api/checker endpoint
    try:
        test_data = "0.9739779299619857"
        response = requests.post(f"{base_url}/api/checker", data={"data": test_data})
        print(f"POST /api/checker: Status {response.status_code}, Response: '{response.text}'")
        print(f"Expected: '{test_data}', Got: '{response.text}'")
    except Exception as e:
        print(f"POST /api/checker error: {e}")
    
    # Test TMDB proxy endpoint
    try:
        response = requests.get(f"{base_url}/apitmdb./movie/now_playing?api_key=4ef0d7355d9ffb5151e987764708ce96&language=ru")
        print(f"GET /apitmdb./movie/now_playing: Status {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response has {len(data.get('results', []))} movies")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"GET /apitmdb./movie/now_playing error: {e}")

if __name__ == "__main__":
    test_endpoints() 