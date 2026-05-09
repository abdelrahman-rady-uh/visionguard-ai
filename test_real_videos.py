#!/usr/bin/env python3
"""
Real Video Testing & Calibration System
Analyzes uploaded videos and shows detailed forensic signals
"""

import sys
sys.path.insert(0, '.')
import os
import json
import cv2
import numpy as np
from backend.services.ai_detection import AIDetectionService
from pathlib import Path

def analyze_video_file(video_path, service):
    """Extract frames and analyze"""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {video_path}")
    print(f"{'='*80}\n")
    
    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found: {video_path}")
        return None
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: Cannot open video file: {video_path}")
        return None
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Video Properties:")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps}")
    print(f"  Total Frames: {total_frames}")
    
    # Extract frames (sample every Nth frame to avoid memory issues)
    frames = []
    frame_count = 0
    sample_rate = max(1, total_frames // 60)  # Extract ~60 frames
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % sample_rate == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)
        
        frame_count += 1
    
    cap.release()
    
    print(f"\n✓ Extracted {len(frames)} frames for analysis\n")
    
    if len(frames) < 3:
        print("ERROR: Not enough frames for analysis")
        return None
    
    # Run detection
    print("Running AI Detection...")
    result = service.detect(frames)
    
    # Display results
    print(f"\n{'='*80}")
    print("DETECTION RESULTS")
    print(f"{'='*80}\n")
    
    print(f"Status: {result['status']}")
    print(f"Confidence: {result['confidence']:.2f}%\n")
    
    print("Forensic Signals:")
    for signal, value in result['signals'].items():
        if signal != 'frames_analyzed' and signal != 'detection_method':
            print(f"  {signal:.<45} {value}")
    
    print(f"\nDetection Method: {result['signals'].get('detection_method', 'Unknown')}")
    
    # Frame analysis
    if result.get('frame_analysis'):
        print(f"\n{'='*80}")
        print("FRAME-BY-FRAME ANALYSIS (First 5 frames)")
        print(f"{'='*80}\n")
        
        for frame_data in result['frame_analysis'][:5]:
            print(f"Frame {frame_data['frame_number']}:")
            if 'brightness' in frame_data:
                bright = frame_data['brightness']
                print(f"  Brightness: mean={bright['mean']}, std={bright['std']}, range=[{bright['min']}-{bright['max']}]")
            if 'edges' in frame_data:
                edges = frame_data['edges']
                print(f"  Edges: {edges['edge_ratio']:.4f} ratio, {edges['total_edges']} pixels")
            if 'sharpness' in frame_data:
                sharp = frame_data['sharpness']
                print(f"  Sharpness: {sharp['sharpness_score']:.4f}")
            if 'noise' in frame_data:
                noise_data = frame_data['noise']
                print(f"  Noise: {noise_data['estimated_noise']:.4f}")
            print()
    
    return result

def main():
    """Test all uploaded videos"""
    service = AIDetectionService()
    
    # Check for videos in uploads directory
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        print(f"ERROR: {uploads_dir} directory not found")
        return
    
    # Find video files
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv']
    video_files = []
    
    for file in os.listdir(uploads_dir):
        if os.path.isfile(os.path.join(uploads_dir, file)):
            # Look for non-encrypted original files
            if not file.endswith('.enc') and not file.endswith('.runtime'):
                ext = os.path.splitext(file)[1].lower()
                if ext in video_extensions:
                    video_files.append(os.path.join(uploads_dir, file))
    
    if not video_files:
        print("No video files found in uploads directory")
        print("\nTo test with real videos:")
        print("1. Upload videos through http://127.0.0.1:5000/upload")
        print("2. Or place video files in the 'uploads' directory")
        print("3. Run this script again")
        return
    
    print(f"\nFound {len(video_files)} video(s) to test\n")
    
    # Test each video
    results = {}
    for video_path in video_files:
        try:
            result = analyze_video_file(video_path, service)
            if result:
                results[video_path] = result
        except Exception as e:
            print(f"ERROR analyzing {video_path}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    if results:
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}\n")
        
        for video_path, result in results.items():
            filename = os.path.basename(video_path)
            print(f"{filename}")
            print(f"  Status: {result['status']}")
            print(f"  Confidence: {result['confidence']:.2f}%")
            print(f"  AI Score: {result['signals'].get('final_ai_score', 'N/A')}\n")

if __name__ == '__main__':
    main()
