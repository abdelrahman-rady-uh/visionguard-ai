import requests
import json
from pathlib import Path

print("\n" + "="*100)
print("🎬 AI DETECTION SYSTEMS COMPARISON REPORT".center(100))
print("="*100)

try:
    # Use a test video from uploads
    video_path = list(Path("uploads").glob("*.mp4"))[0]
    
    print(f"\n📹 Test Video: {video_path.name}")
    print(f"   File Size: {video_path.stat().st_size / (1024*1024):.2f} MB")
    
    # Upload and analyze
    with open(video_path, 'rb') as f:
        response = requests.post(
            'http://127.0.0.1:5000/api/analysis/v2/analyze',
            files={'video': f},
            timeout=180
        )
    
    data = response.json()
    analyses = data.get('data', {}).get('analyses', {})
    
    print(f"\n⏳ Uploading & Running All AI Detection Services...")
    print("   Services: Captions | Face Detection | Object Detection | Tampering Analysis\n")
    
    # ============ FACE DETECTION ============
    print("="*100)
    print("1️⃣  FACE DETECTION SERVICE".ljust(100))
    print("="*100)
    faces_result = analyses.get('faces', {})
    
    if faces_result.get('status') == 'success':
        face_data = faces_result.get('data', {})
        print(f"✅ Status: SUCCESS")
        print(f"\n📊 RESULTS:")
        print(f"   • Total Faces Detected: {face_data.get('faces_detected', 0)}")
        print(f"   • Unique People: {face_data.get('estimated_unique_people', 0)}")
        print(f"   • Confidence Score: {face_data.get('confidence', 0):.2%}")
        print(f"   • Privacy Risk: {face_data.get('privacy_concerns', 'None detected')}")
        
        detections = face_data.get('face_detections', [])
        if detections:
            print(f"\n   Top Detections (first 5):")
            for i, det in enumerate(detections[:5], 1):
                frame = det.get('frame', 0)
                x, y, w, h = det.get('bbox', [0, 0, 0, 0])
                print(f"      {i}. Frame {frame}: Position ({x}, {y}), Size {w}x{h}")
    else:
        print(f"❌ Status: {faces_result.get('status', 'ERROR')}")
        print(f"   Error: {faces_result.get('error', 'No details')}")
    
    # ============ OBJECT DETECTION ============
    print("\n" + "="*100)
    print("2️⃣  OBJECT DETECTION SERVICE".ljust(100))
    print("="*100)
    objects_result = analyses.get('objects', {})
    
    if objects_result.get('status') == 'success':
        obj_data = objects_result.get('data', {})
        print(f"✅ Status: SUCCESS")
        print(f"\n📊 RESULTS:")
        print(f"   • Total Objects Detected: {obj_data.get('total_detections', 0)}")
        print(f"   • Avg Objects Per Frame: {obj_data.get('average_objects_per_frame', 0):.1f}")
        print(f"   • Unique Classes: {len(set(d.get('class', '') for d in obj_data.get('detections', [])))}")
        print(f"   • Confidence Score: {obj_data.get('confidence', 0):.2%}")
        
        detections = obj_data.get('detections', [])
        if detections:
            # Count by class
            classes = {}
            for det in detections:
                cls = det.get('class', 'unknown')
                classes[cls] = classes.get(cls, 0) + 1
            
            print(f"\n   Detected Object Classes:")
            for cls, count in sorted(classes.items(), key=lambda x: x[1], reverse=True):
                print(f"      • {cls}: {count} detections")
            
            # Show sample detections
            print(f"\n   Sample Detections (first 3):")
            for i, det in enumerate(detections[:3], 1):
                cls = det.get('class', 'unknown')
                frame = det.get('frame', 0)
                conf = det.get('confidence', 0)
                bbox = det.get('bbox', [0, 0, 0, 0])
                print(f"      {i}. {cls} @ Frame {frame} (confidence: {conf:.2%}, box: {bbox})")
    else:
        print(f"❌ Status: {objects_result.get('status', 'ERROR')}")
    
    # ============ TAMPERING DETECTION ============
    print("\n" + "="*100)
    print("3️⃣  TAMPERING ANALYSIS SERVICE".ljust(100))
    print("="*100)
    tampering_result = analyses.get('tampering', {})
    
    if tampering_result.get('status') == 'success':
        tamp_data = tampering_result.get('data', {})
        print(f"✅ Status: SUCCESS")
        print(f"\n📊 RESULTS:")
        
        tampering_detected = tamp_data.get('tampering_detected', False)
        risk_level = tamp_data.get('risk_level', 'LOW')
        overall_risk = tamp_data.get('overall_risk', 0)
        integrity_score = tamp_data.get('integrity_score', 0)
        
        print(f"   • Tampering Detected: {'⚠️  YES' if tampering_detected else '✅ NO'}")
        print(f"   • Risk Level: {risk_level}")
        print(f"   • Overall Risk Score: {overall_risk:.2%}")
        print(f"   • Integrity Score: {integrity_score:.2%}")
        print(f"   • Confidence: {tamp_data.get('confidence', 0):.2%}")
        
        indicators = tamp_data.get('indicators', [])
        if indicators:
            print(f"\n   Detected Issues:")
            for ind in indicators[:5]:
                print(f"      ⚠️  {ind}")
    else:
        print(f"❌ Status: {tampering_result.get('status', 'ERROR')}")
    
    # ============ CAPTION SERVICE ============
    print("\n" + "="*100)
    print("4️⃣  CAPTION/DESCRIPTION SERVICE".ljust(100))
    print("="*100)
    captions_result = analyses.get('captions', {})
    
    if captions_result.get('status') == 'success':
        cap_data = captions_result.get('data', {})
        print(f"✅ Status: SUCCESS")
        print(f"\n📊 RESULTS:")
        print(f"   • Frames Analyzed: {cap_data.get('total_frames_analyzed', 0)}")
        print(f"   • Captions Generated: {len(cap_data.get('captions', []))}")
        print(f"   • Avg Confidence: {cap_data.get('confidence_average', 0):.2%}")
        
        captions = cap_data.get('captions', [])
        if captions:
            print(f"\n   Generated Captions (first 3):")
            for i, cap in enumerate(captions[:3], 1):
                print(f"      {i}. {cap}")
        
        summary = cap_data.get('summary', '')
        if summary:
            print(f"\n   Summary: {summary[:150]}...")
    else:
        print(f"❌ Status: {captions_result.get('status', 'UNAVAILABLE')}")
        print(f"   Note: The 'image-to-text' task is not available in current HuggingFace version")
    
    # ============ COMPARISON & BEST ANSWERS ============
    print("\n" + "="*100)
    print("🏆 COMPARISON ANALYSIS".ljust(100))
    print("="*100)
    
    services_status = {
        'Face Detection': faces_result.get('status') == 'success',
        'Object Detection': objects_result.get('status') == 'success',
        'Tampering Analysis': tampering_result.get('status') == 'success',
        'Captions': captions_result.get('status') == 'success',
    }
    
    print("\n📈 Service Performance:")
    for service, success in services_status.items():
        status_icon = "✅" if success else "❌"
        print(f"   {status_icon} {service}")
    
    successful = sum(1 for v in services_status.values() if v)
    print(f"\n   Overall: {successful}/4 services operational")
    
    # Confidence scores
    print("\n📊 Confidence Scores:")
    scores = {}
    
    if faces_result.get('status') == 'success':
        face_conf = faces_result.get('data', {}).get('confidence', 0)
        scores['Face Detection'] = face_conf
        print(f"   • Face Detection: {face_conf:.2%}")
    
    if objects_result.get('status') == 'success':
        obj_conf = objects_result.get('data', {}).get('confidence', 0)
        scores['Object Detection'] = obj_conf
        print(f"   • Object Detection: {obj_conf:.2%}")
    
    if tampering_result.get('status') == 'success':
        tamp_conf = tampering_result.get('data', {}).get('confidence', 0)
        scores['Tampering Analysis'] = tamp_conf
        print(f"   • Tampering Analysis: {tamp_conf:.2%}")
    
    if captions_result.get('status') == 'success':
        cap_conf = captions_result.get('data', {}).get('confidence_average', 0)
        scores['Captions'] = cap_conf
        print(f"   • Captions: {cap_conf:.2%}")
    
    # Best answer
    if scores:
        best_service = max(scores, key=scores.get)
        best_score = scores[best_service]
        avg_score = sum(scores.values()) / len(scores)
        
        print(f"\n🏆 BEST ANSWER:")
        print(f"   Most Confident Service: {best_service} ({best_score:.2%})")
        print(f"   Average Confidence: {avg_score:.2%}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   1. Use {best_service} as primary detection method")
        print(f"   2. Cross-reference with Object Detection for comprehensive analysis")
        print(f"   3. Use Tampering Analysis to verify integrity")
        print(f"   4. For full context, combine all successful services")
    
    print("\n" + "="*100)
    print("✅ Analysis Complete!".center(100))
    print("="*100 + "\n")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
