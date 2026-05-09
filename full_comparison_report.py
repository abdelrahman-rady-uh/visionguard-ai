import requests
import json
from pathlib import Path

print("\n" + "="*100)
print("AI DETECTION SYSTEMS COMPARISON REPORT".center(100))
print("="*100)

try:
    video_path = list(Path("uploads").glob("*.mp4"))[0]
    
    print(f"\n[*] Test Video: {video_path.name}")
    print(f"    File Size: {video_path.stat().st_size / (1024*1024):.2f} MB")
    
    with open(video_path, 'rb') as f:
        response = requests.post(
            'http://127.0.0.1:5000/api/analysis/v2/analyze',
            files={'video': f},
            timeout=180
        )
    
    data = response.json()
    analyses = data.get('data', {}).get('analyses', {})
    
    print(f"\n[*] Running All AI Detection Services...")
    print("    Services: Face Detection | Object Detection | Tampering Analysis | Captions\n")
    
    # FACE DETECTION
    print("="*100)
    print("1. FACE DETECTION SERVICE".ljust(100))
    print("="*100)
    faces_result = analyses.get('faces', {})
    
    if faces_result.get('status') == 'success':
        face_data = faces_result.get('data', {})
        print(f"[+] Status: SUCCESS")
        print(f"\n[RESULTS]:")
        print(f"    Total Faces Detected: {face_data.get('faces_detected', 0)}")
        print(f"    Unique People: {face_data.get('estimated_unique_people', 0)}")
        print(f"    Confidence Score: {face_data.get('confidence', 0):.2%}")
        print(f"    Privacy Concerns: {face_data.get('privacy_concerns', 'None')}")
        
        detections = face_data.get('face_detections', [])
        if detections:
            print(f"\n    Sample Detections (first 3):")
            for i, det in enumerate(detections[:3], 1):
                frame = det.get('frame', 0)
                bbox = det.get('bbox', [0,0,0,0])
                print(f"      {i}. Frame {frame}: bbox {bbox}")
    else:
        print(f"[-] Status: {faces_result.get('status', 'ERROR')}")
    
    # OBJECT DETECTION
    print("\n" + "="*100)
    print("2. OBJECT DETECTION SERVICE".ljust(100))
    print("="*100)
    objects_result = analyses.get('objects', {})
    
    if objects_result.get('status') == 'success':
        obj_data = objects_result.get('data', {})
        print(f"[+] Status: SUCCESS")
        print(f"\n[RESULTS]:")
        print(f"    Total Objects Detected: {obj_data.get('total_detections', 0)}")
        print(f"    Avg Objects Per Frame: {obj_data.get('average_objects_per_frame', 0):.1f}")
        
        detections = obj_data.get('detections', [])
        if detections:
            classes_count = {}
            for det in detections:
                cls = det.get('class', 'unknown')
                classes_count[cls] = classes_count.get(cls, 0) + 1
            
            print(f"    Unique Classes: {len(classes_count)}")
            print(f"    Confidence Score: {obj_data.get('confidence', 0):.2%}")
            print(f"\n    Top 5 Classes:")
            for cls, count in sorted(classes_count.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"      - {cls}: {count} detections")
    else:
        print(f"[-] Status: {objects_result.get('status', 'ERROR')}")
    
    # TAMPERING DETECTION
    print("\n" + "="*100)
    print("3. TAMPERING ANALYSIS SERVICE".ljust(100))
    print("="*100)
    tampering_result = analyses.get('tampering', {})
    
    if tampering_result.get('status') == 'success':
        tamp_data = tampering_result.get('data', {})
        print(f"[+] Status: SUCCESS")
        print(f"\n[RESULTS]:")
        
        tampering_detected = tamp_data.get('tampering_detected', False)
        print(f"    Tampering Detected: {'YES' if tampering_detected else 'NO'}")
        print(f"    Risk Level: {tamp_data.get('risk_level', 'LOW')}")
        print(f"    Overall Risk Score: {tamp_data.get('overall_risk', 0):.2%}")
        print(f"    Integrity Score: {tamp_data.get('integrity_score', 0):.2%}")
        print(f"    Confidence: {tamp_data.get('confidence', 0):.2%}")
        
        indicators = tamp_data.get('indicators', [])
        if indicators:
            print(f"\n    Detected Issues:")
            for ind in indicators[:3]:
                print(f"      - {ind}")
    else:
        print(f"[-] Status: {tampering_result.get('status', 'ERROR')}")
    
    # CAPTIONS
    print("\n" + "="*100)
    print("4. CAPTION/DESCRIPTION SERVICE".ljust(100))
    print("="*100)
    captions_result = analyses.get('captions', {})
    
    if captions_result.get('status') == 'success':
        cap_data = captions_result.get('data', {})
        print(f"[+] Status: SUCCESS")
        print(f"\n[RESULTS]:")
        print(f"    Frames Analyzed: {cap_data.get('total_frames_analyzed', 0)}")
        print(f"    Captions Generated: {len(cap_data.get('captions', []))}")
        print(f"    Avg Confidence: {cap_data.get('confidence_average', 0):.2%}")
    else:
        print(f"[-] Status: UNAVAILABLE")
        print(f"    Note: image-to-text task not available in current HuggingFace version")
    
    # COMPARISON
    print("\n" + "="*100)
    print("COMPARISON ANALYSIS".ljust(100))
    print("="*100)
    
    services = {
        'Face Detection': faces_result.get('status') == 'success',
        'Object Detection': objects_result.get('status') == 'success',
        'Tampering Analysis': tampering_result.get('status') == 'success',
        'Captions': captions_result.get('status') == 'success',
    }
    
    print("\n[SERVICE PERFORMANCE]:")
    successful_count = 0
    for service, success in services.items():
        icon = "[+]" if success else "[-]"
        print(f"    {icon} {service}")
        if success:
            successful_count += 1
    
    print(f"\n    Overall: {successful_count}/4 services operational")
    
    # CONFIDENCE SCORES
    print("\n[CONFIDENCE SCORES]:")
    scores = {}
    
    if faces_result.get('status') == 'success':
        conf = faces_result.get('data', {}).get('confidence', 0)
        scores['Face Detection'] = conf
        print(f"    Face Detection: {conf:.2%}")
    
    if objects_result.get('status') == 'success':
        conf = objects_result.get('data', {}).get('confidence', 0)
        scores['Object Detection'] = conf
        print(f"    Object Detection: {conf:.2%}")
    
    if tampering_result.get('status') == 'success':
        conf = tampering_result.get('data', {}).get('confidence', 0)
        scores['Tampering Analysis'] = conf
        print(f"    Tampering Analysis: {conf:.2%}")
    
    if captions_result.get('status') == 'success':
        conf = captions_result.get('data', {}).get('confidence_average', 0)
        scores['Captions'] = conf
        print(f"    Captions: {conf:.2%}")
    
    # RECOMMENDATIONS
    if scores:
        best_service = max(scores, key=scores.get)
        best_score = scores[best_service]
        avg_score = sum(scores.values()) / len(scores) if scores else 0
        
        print(f"\n[BEST ANSWER]:")
        print(f"    Most Confident Service: {best_service} ({best_score:.2%})")
        print(f"    Average Confidence: {avg_score:.2%}")
        
        print(f"\n[RECOMMENDATIONS]:")
        print(f"    1. Use {best_service} as primary detection method")
        print(f"    2. Cross-reference with Object Detection for comprehensive analysis")
        print(f"    3. Use Tampering Analysis to verify video integrity")
        print(f"    4. Combine all successful services for complete insight")
    
    print("\n" + "="*100)
    print("Analysis Complete!".center(100))
    print("="*100 + "\n")

except Exception as e:
    print(f"\n[-] Error: {e}")
    import traceback
    traceback.print_exc()
