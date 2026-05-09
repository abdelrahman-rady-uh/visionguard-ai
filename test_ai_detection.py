#!/usr/bin/env python3
"""
AI Detection Testing and Validation Framework
Tests the new AI detection system with synthetic test data
"""

import sys
import os
import cv2
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.ai_detection import AIDetectionService


def create_synthetic_real_video(num_frames=48, noise_level=0.05):
    """
    Create synthetic frames that look like real video:
    - Natural noise and grain
    - Realistic motion
    - Natural color variation
    - Sharp edges and details
    """
    frames = []
    height, width = 216, 384
    
    # Create base image with natural features
    for frame_idx in range(num_frames):
        # Create base with natural colors
        base = np.random.randint(50, 200, (height, width, 3), dtype=np.uint8)
        
        # Add realistic shapes and objects
        for _ in range(3):
            x = np.random.randint(20, width-20)
            y = np.random.randint(20, height-20)
            radius = np.random.randint(10, 30)
            color = tuple(np.random.randint(50, 200, 3).tolist())
            cv2.circle(base, (x, y), radius, color, -1)
        
        # Add edges with varying intensity
        edges = cv2.Canny(base, 30, 90)
        base[edges > 0] = np.minimum(base[edges > 0] + 30, 255)
        
        # Add natural noise/grain
        grain = np.random.normal(0, noise_level * 25, (height, width, 3))
        frame = np.clip(base.astype(np.float32) + grain, 0, 255).astype(np.uint8)
        
        # Add realistic motion (object movement)
        motion_amount = 5
        offset = (frame_idx % 20) * motion_amount - 50
        frame = np.roll(frame, offset, axis=1)
        
        frames.append(frame)
    
    return frames


def create_synthetic_ai_video(num_frames=48):
    """
    Create synthetic frames that look like AI-generated video:
    - Over-smooth appearance
    - Unnatural consistency
    - Weak edges and details
    - Too-clean (low noise)
    - Unnatural color uniformity
    """
    frames = []
    height, width = 216, 384
    
    # Create base with smooth gradients (AI characteristic)
    for frame_idx in range(num_frames):
        # Create smooth gradient base (unnatural smoothness)
        x = np.linspace(0, 1, width)
        y = np.linspace(0, 1, height)
        X, Y = np.meshgrid(x, y)
        
        # Smooth gradients
        r_channel = (128 + 60 * np.sin(X * 2 * np.pi)).astype(np.uint8)
        g_channel = (128 + 60 * np.cos(Y * 2 * np.pi)).astype(np.uint8)
        b_channel = (128 + 40 * np.sin((X + Y) * np.pi)).astype(np.uint8)
        
        frame = np.stack([r_channel, g_channel, b_channel], axis=2)
        
        # Add some subtle shapes but very smooth
        for _ in range(2):
            x_pos = int((np.sin(frame_idx * 0.1) + 1) * width / 2)
            y_pos = int((np.cos(frame_idx * 0.08) + 1) * height / 2)
            radius = 25
            cv2.circle(frame, (x_pos, y_pos), radius, (150, 150, 150), -1)
        
        # Apply Gaussian blur multiple times (AI smoothing characteristic)
        frame = cv2.GaussianBlur(frame, (5, 5), 2)
        frame = cv2.GaussianBlur(frame, (5, 5), 1)
        
        # Minimal noise (AI videos are too clean)
        minimal_noise = np.random.normal(0, 1, (height, width, 3))
        frame = np.clip(frame.astype(np.float32) + minimal_noise, 0, 255).astype(np.uint8)
        
        frames.append(frame)
    
    return frames


def test_detection(frames, label):
    """Test AI detection on given frames"""
    print(f"\n{'='*70}")
    print(f"Testing: {label}")
    print(f"{'='*70}")
    print(f"Number of frames: {len(frames)}")
    
    detector = AIDetectionService()
    result = detector.detect(frames)
    
    print(f"\nDetection Results:")
    print(f"  Status: {result['status']}")
    print(f"  Confidence: {result['confidence']:.2f}%")
    
    print(f"\nForensic Signals:")
    signals = result.get('signals', {})
    for signal_name, signal_value in signals.items():
        if signal_name != 'error':
            print(f"  {signal_name}: {signal_value}")
    
    # Determine if detection is correct
    is_ai_generated = "AI" in label
    correct_detection = False
    
    if is_ai_generated:
        correct_detection = result['status'] in ["AI-Generated", "Likely AI-Generated"]
    else:
        correct_detection = result['status'] in ["Real", "Likely Real"]
    
    status_icon = "✓" if correct_detection else "✗"
    print(f"\n{status_icon} Detection Accuracy: {'CORRECT' if correct_detection else 'INCORRECT'}")
    
    return result, correct_detection


def main():
    """Run comprehensive AI detection tests"""
    print("\n" + "="*70)
    print("VisionGuard AI - Detection System Validation")
    print("="*70)
    
    results = {
        'real': [],
        'ai': []
    }
    
    # Test 1: Synthetic Real Video
    print("\n[TEST 1] Creating synthetic REAL video frames...")
    real_frames = create_synthetic_real_video(num_frames=48, noise_level=0.08)
    result_real, correct_real = test_detection(real_frames, "REAL Video")
    results['real'].append(correct_real)
    
    # Test 2: Synthetic AI Video
    print("\n[TEST 2] Creating synthetic AI-GENERATED video frames...")
    ai_frames = create_synthetic_ai_video(num_frames=48)
    result_ai, correct_ai = test_detection(ai_frames, "AI-GENERATED Video")
    results['ai'].append(correct_ai)
    
    # Test 3: Another real video variant
    print("\n[TEST 3] Creating second REAL video variant...")
    real_frames_2 = create_synthetic_real_video(num_frames=48, noise_level=0.12)
    result_real2, correct_real2 = test_detection(real_frames_2, "REAL Video (High Noise)")
    results['real'].append(correct_real2)
    
    # Test 4: Another AI video variant
    print("\n[TEST 4] Creating second AI-GENERATED video variant...")
    ai_frames_2 = create_synthetic_ai_video(num_frames=48)
    result_ai2, correct_ai2 = test_detection(ai_frames_2, "AI-GENERATED Video (Variant)")
    results['ai'].append(correct_ai2)
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    real_accuracy = sum(results['real']) / len(results['real']) * 100 if results['real'] else 0
    ai_accuracy = sum(results['ai']) / len(results['ai']) * 100 if results['ai'] else 0
    overall_accuracy = (sum(results['real']) + sum(results['ai'])) / (len(results['real']) + len(results['ai'])) * 100
    
    print(f"\nReal Video Detection Accuracy: {real_accuracy:.1f}% ({sum(results['real'])}/{len(results['real'])})")
    print(f"AI-Generated Detection Accuracy: {ai_accuracy:.1f}% ({sum(results['ai'])}/{len(results['ai'])})")
    print(f"\nOverall Accuracy: {overall_accuracy:.1f}%")
    
    if overall_accuracy >= 90:
        print("\n✓ VALIDATION PASSED - System accuracy >= 90%")
    else:
        print(f"\n✗ VALIDATION FAILED - Accuracy {overall_accuracy:.1f}% < 90%")
        print("\nRecommendations:")
        print("  - Review threshold values in AIDetectionService")
        print("  - Adjust signal weights if needed")
        print("  - Consider collecting more training data")
    
    print("\n" + "="*70)
    return overall_accuracy >= 90


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
