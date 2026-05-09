import requests
from pathlib import Path

try:
    video_path = list(Path("uploads").glob("*.mp4"))[0]
    print(f"Found video: {video_path.name}")
    print(f"File size: {video_path.stat().st_size / (1024*1024):.2f} MB")
    
    print("\nTesting API connection...")
    response = requests.post(
        "http://127.0.0.1:5000/api/analysis/v2/analyze",
        files={"video": open(video_path, "rb")},
        timeout=180
    )
    
    if response.status_code == 200:
        data = response.json()
        print("\n[SUCCESS] Analysis Results:")
        print(f"Response status: {response.status_code}")
        print(f"Data keys: {list(data.keys())}")
        
        if "data" in data and "analyses" in data["data"]:
            analyses = data["data"]["analyses"]
            print(f"\nAnalyses performed: {list(analyses.keys())}")
            
            for service, result in analyses.items():
                status = result.get("status", "unknown")
                print(f"  [{status.upper()}] {service}")
    else:
        print(f"Error: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
