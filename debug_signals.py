#!/usr/bin/env python3
"""
Debug script to understand AI detection signal values
"""

import sys
import os
import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.ai_detection import AIDetectionService


def test_signals():
    """Debug individual signal calculations"""
    detector = AIDetectionService()
    
    # Create a simple real-like frame
    print("Creating test frames...")
    frames = []
    for i in range(15):
        # Create a frame with some complexity
        frame = np.random.randint(50, 200, (216, 384, 3), dtype=np.uint8)
        # Add some shapes
        for _ in range(2):
            x = np.random.randint(20, 364)
            y = np.random.randint(20, 196)
            cv2.circle(frame, (x, y), 15, (100, 150, 200), -1)
        frames.append(frame)
    
    print("\nTesting individual signals...")
    
    # Test each signal
    t = detector._calc_temporal_consistency(frames)
    print(f"Temporal Consistency: {t}")
    
    e = detector._calc_edge_strength(frames)
    print(f"Edge Strength: {e}")
    
    c = detector._calc_color_variance(frames)
    print(f"Color Variance: {c}")
    
    n = detector._calc_noise_content(frames)
    print(f"Noise Content: {n}")
    
    b = detector._calc_blur_level(frames)
    print(f"Blur Level: {b}")
    
    comp = detector._calc_compression_artifacts(frames)
    print(f"Compression Artifacts: {comp}")
    
    m = detector._calc_motion_variance(frames)
    print(f"Motion Variance: {m}")
    
    # Test fusion
    ai_score = detector._compute_ai_likelihood(t, e, c, n, b, comp, m)
    print(f"\nFused AI Score: {ai_score}")
    
    # Test classification
    status, conf = detector._classify(ai_score)
    print(f"Classification: {status} ({conf}%)")


if __name__ == "__main__":
    test_signals()
