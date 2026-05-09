#!/usr/bin/env python3
"""
AI Detection System Diagnostics
Detailed signal analysis to identify detection failures
"""

import sys
sys.path.insert(0, '.')
import numpy as np
import cv2
from backend.services.ai_detection import AIDetectionService
import json

def create_obvious_ai_video():
    """Create OBVIOUSLY AI-generated video - uniform, blurred"""
    frames = []
    for i in range(30):
        # Perfect uniformity = AI characteristic
        frame = np.full((480, 640, 3), 128, dtype=np.uint8)
        # Heavy Gaussian blur = AI smoothing
        for _ in range(5):
            frame = cv2.GaussianBlur(frame, (21, 21), 0)
        frames.append(frame)
    return frames

def create_obvious_real_video():
    """Create OBVIOUSLY real video - varied noise, texture"""
    frames = []
    np.random.seed(42)
    for i in range(30):
        # Random natural variation
        frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
        # Add edges - natural content
        for _ in range(2):
            frame = cv2.filter2D(frame, -1, np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]))
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        frames.append(frame)
    return frames

def create_custom_test_video(description, properties):
    """Create video with specific properties for testing"""
    frames = []
    
    for i in range(30):
        if "uniform" in properties:
            frame = np.full((480, 640, 3), 128, dtype=np.uint8)
        else:
            frame = np.random.randint(100, 150, (480, 640, 3), dtype=np.uint8)
        
        if "blurred" in properties:
            for _ in range(10):
                frame = cv2.GaussianBlur(frame, (31, 31), 0)
        
        if "noise" in properties:
            noise = np.random.normal(0, 15, frame.shape).astype(np.int16)
            frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        if "edges" in properties:
            edges = cv2.Canny(frame[:,:,0], 50, 150)
            frame[:,:,0] = np.maximum(frame[:,:,0], edges)
        
        frames.append(frame)
    
    return frames

def analyze_signals_detailed(service, frames, video_name):
    """Run detection and print detailed signal analysis"""
    print(f"\n{'='*100}")
    print(f"ANALYZING: {video_name}")
    print(f"{'='*100}\n")
    
    print(f"Video Properties:")
    print(f"  Frames: {len(frames)}")
    print(f"  Resolution: {frames[0].shape[1]}x{frames[0].shape[0]}")
    print(f"  Channels: {frames[0].shape[2]}\n")
    
    # Manual signal analysis
    print("SIGNAL CALCULATIONS (Manual):")
    print("-" * 100)
    
    # 1. Temporal consistency
    diffs = []
    for i in range(1, min(len(frames), 15)):
        prev = cv2.cvtColor(frames[i-1], cv2.COLOR_RGB2GRAY).astype(np.float32)
        curr = cv2.cvtColor(frames[i], cv2.COLOR_RGB2GRAY).astype(np.float32)
        diff = np.mean(np.abs(curr - prev)) / 255.0
        diffs.append(diff)
    
    avg_diff = np.mean(diffs)
    print(f"Temporal Consistency:")
    print(f"  Avg frame difference: {avg_diff:.6f}")
    print(f"  Min diff: {np.min(diffs):.6f}, Max: {np.max(diffs):.6f}")
    print(f"  Analysis: {'VERY CONSISTENT (AI)' if avg_diff < 0.02 else 'VARIED (REAL)'}")
    
    # 2. Edge density
    edge_densities = []
    for frame in frames[:15]:
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_ratio = np.mean(edges > 0)
        edge_densities.append(edge_ratio)
    
    avg_edges = np.mean(edge_densities)
    print(f"\nEdge Strength:")
    print(f"  Avg edge density: {avg_edges:.6f}")
    print(f"  Min: {np.min(edge_densities):.6f}, Max: {np.max(edge_densities):.6f}")
    print(f"  Analysis: {'LOW EDGES (AI/BLURRED)' if avg_edges < 0.08 else 'HIGH EDGES (REAL/DETAILED)'}")
    
    # 3. Color variance
    color_imbalances = []
    for frame in frames[:10]:
        b, g, r = cv2.split(frame.astype(np.float32) / 255.0)
        b_var, g_var, r_var = np.var(b), np.var(g), np.var(r)
        imbalance = abs(b_var - g_var) + abs(g_var - r_var)
        color_imbalances.append(imbalance)
    
    avg_imbalance = np.mean(color_imbalances)
    print(f"\nColor Variance:")
    print(f"  Avg channel imbalance: {avg_imbalance:.6f}")
    print(f"  Analysis: {'UNBALANCED (AI)' if avg_imbalance < 0.004 else 'BALANCED (REAL)'}")
    
    # 4. Noise level
    noise_levels = []
    for frame in frames[:10]:
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_32F)
        noise = np.std(laplacian) / 255.0
        noise_levels.append(noise)
    
    avg_noise = np.mean(noise_levels)
    print(f"\nNoise Content:")
    print(f"  Avg noise level: {avg_noise:.6f}")
    print(f"  Analysis: {'CLEAN/NO NOISE (AI)' if avg_noise < 0.02 else 'NOISY (REAL)'}")
    
    # 5. Blur level (Laplacian variance)
    blur_levels = []
    for frame in frames[:10]:
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_32F)
        sharpness = np.var(laplacian) / (255**2)
        blur_levels.append(sharpness)
    
    avg_sharpness = np.mean(blur_levels)
    print(f"\nBlur Level (Sharpness):")
    print(f"  Avg sharpness: {avg_sharpness:.6f}")
    print(f"  Analysis: {'OVER-BLURRED (AI)' if avg_sharpness < 0.002 else 'SHARP (REAL)'}")
    
    # Now run actual detection
    print(f"\n{'='*100}")
    print("DETECTION ENGINE RESULTS:")
    print(f"{'='*100}\n")
    
    result = service.detect(frames)
    
    print(f"Status: {result['status']}")
    print(f"Confidence: {result['confidence']:.2f}%")
    print(f"AI Score: {result['signals'].get('final_ai_score', 'N/A')}")
    
    print(f"\nDetailed Signals:")
    for signal_name, signal_value in result['signals'].items():
        if signal_name not in ['frames_analyzed', 'detection_method']:
            print(f"  {signal_name:.<50} {signal_value}")
    
    return result

def main():
    service = AIDetectionService()
    
    print("\n" + "="*100)
    print("VISIONGUARD AI - DETECTION SYSTEM DIAGNOSTICS")
    print("="*100)
    
    # Test 1: Obviously AI (uniform + blurred)
    print("\n[TEST 1] Obviously AI-Generated Video (Uniform + Heavily Blurred)")
    ai_video = create_obvious_ai_video()
    result_ai = analyze_signals_detailed(service, ai_video, "OBVIOUS_AI")
    
    # Test 2: Obviously Real (varied + noisy)
    print("\n\n[TEST 2] Obviously Real Video (Varied + Noisy)")
    real_video = create_obvious_real_video()
    result_real = analyze_signals_detailed(service, real_video, "OBVIOUS_REAL")
    
    # Test 3: Intermediate case
    print("\n\n[TEST 3] Intermediate Case (Some variation, moderate blur)")
    intermediate = create_custom_test_video("moderate", ["noise", "edges"])
    result_intermediate = analyze_signals_detailed(service, intermediate, "INTERMEDIATE")
    
    # Summary
    print(f"\n{'='*100}")
    print("DIAGNOSTIC SUMMARY")
    print(f"{'='*100}\n")
    
    print("Obviously AI Video:")
    print(f"  → Status: {result_ai['status']}")
    print(f"  → Confidence: {result_ai['confidence']:.2f}%")
    print(f"  → Expected: AI-Generated ✓" if "AI" in result_ai['status'] else f"  → Expected: AI-Generated ✗ WRONG")
    
    print("\nObviously Real Video:")
    print(f"  → Status: {result_real['status']}")
    print(f"  → Confidence: {result_real['confidence']:.2f}%")
    print(f"  → Expected: Real ✓" if "Real" in result_real['status'] else f"  → Expected: Real ✗ WRONG")
    
    print("\nIntermediate Video:")
    print(f"  → Status: {result_intermediate['status']}")
    print(f"  → Confidence: {result_intermediate['confidence']:.2f}%")
    
    # Check if signals are different
    if result_ai['signals'].get('final_ai_score') == result_real['signals'].get('final_ai_score'):
        print("\n⚠️  CRITICAL ISSUE: AI and REAL videos have IDENTICAL AI scores!")
        print("   This means the detection signals are NOT working properly.")
    else:
        print(f"\n✓ Signals are differentiated:")
        print(f"  AI Score: {result_ai['signals'].get('final_ai_score')}")
        print(f"  Real Score: {result_real['signals'].get('final_ai_score')}")

if __name__ == '__main__':
    main()
