import os
import json
import requests
from pathlib import Path

video_dir = Path("uploads")
videos = list(video_dir.glob("*.mp4"))

test_video = str(videos[0])

with open(test_video, 'rb') as f:
    files = {'video': f}
    data = {
        'analyze_captions': 'true',
        'analyze_objects': 'true',
        'detect_tampering': 'true',
        'detect_faces': 'true'
    }
    
    response = requests.post(
        'http://127.0.0.1:5000/api/analysis/v2/analyze',
        files=files,
        data=data,
        timeout=180
    )
    
    resp = response.json()
    
    # Print all top-level keys
    print("Top-level keys in response:")
    for key in resp.keys():
        print(f"  - {key}: {type(resp[key])}")
    
    # Print the complete response to file
    with open('response_dump.json', 'w') as out:
        json.dump(resp, out, indent=2)
    
    print("\nFull response saved to response_dump.json")
    
    # Print a sample of the first 1000 chars
    print("\nFirst part of response:")
    print(json.dumps(resp, indent=2)[:1000])
