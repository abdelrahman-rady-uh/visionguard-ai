#!/usr/bin/env python3
"""Test API endpoints"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_endpoints():
    print("Testing API Endpoints...\n")
    
    # Test welcome page
    print("1. Testing Welcome Page (GET /)")
    response = requests.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
    
    # Test upload page
    print("2. Testing Upload Page (GET /upload)")
    response = requests.get(f"{BASE_URL}/upload")
    print(f"   Status: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
    
    # Test dashboard page
    print("3. Testing Dashboard Page (GET /dashboard)")
    response = requests.get(f"{BASE_URL}/dashboard")
    print(f"   Status: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
    
    # Test PDF export endpoint
    print("\n4. Testing PDF Export (POST /api/export/pdf)")
    test_data = {
        "data": {
            "metadata": {},
            "analysis": {
                "ai_detection": {"status": "Likely AI-Generated", "confidence": 76.96},
                "tampering": {"tampering_type": "None", "confidence": 5.0},
                "caption": {"caption": "Test caption"},
                "face_detection": {"faces_detected": False, "total_faces": 0}
            }
        }
    }
    response = requests.post(
        f"{BASE_URL}/api/export/pdf",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code} {'✓ PDF Created' if response.status_code == 200 else f'✗ Error: {response.status_code}'}")
    if response.status_code == 200:
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        print(f"   File Size: {len(response.content)} bytes")
    else:
        print(f"   Response: {response.text[:200]}")
    
    # Test JSON export endpoint
    print("\n5. Testing JSON Export (POST /api/export/json)")
    response = requests.post(
        f"{BASE_URL}/api/export/json",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code} {'✓ JSON Created' if response.status_code == 200 else f'✗ Error: {response.status_code}'}")
    if response.status_code == 200:
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        print(f"   File Size: {len(response.content)} bytes")
    else:
        print(f"   Response: {response.text[:200]}")
    
    print("\n✓ All tests completed!")

if __name__ == "__main__":
    try:
        test_endpoints()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server at http://127.0.0.1:5000")
        print("Make sure the server is running: python run_server.py")
    except Exception as e:
        print(f"❌ Error: {e}")
