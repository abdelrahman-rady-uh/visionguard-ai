#!/usr/bin/env python3
"""
Diagnostic: tests the AI detection pipeline end-to-end.
Creates two synthetic videos (real-looking noise vs clean AI-looking),
runs them through AIDetectionService, and prints raw model scores.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import cv2
import numpy as np
import tempfile

def make_video(path, frames=30, style="noise"):
    """Create a short test video."""
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(path, fourcc, 15.0, (640, 360))
    for i in range(frames):
        if style == "noise":
            # Natural looking — random pixel noise + colour variation
            base = np.array([120 + 20*np.sin(i*0.3), 100, 80], dtype=np.float32)
            frame = np.random.normal(0, 25, (360, 640, 3)) + base
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        else:
            # AI-looking — perfectly smooth gradient, zero noise
            t = i / frames
            r = int(50 + 50*t)
            g = int(80 + 40*np.sin(t*np.pi))
            b = int(120 + 30*t)
            frame = np.full((360, 640, 3), [b, g, r], dtype=np.uint8)
            # Add smooth gradient only
            y_grad = np.linspace(0, 20, 360).reshape(-1, 1, 1).astype(np.uint8)
            frame = np.clip(frame.astype(np.int16) + y_grad, 0, 255).astype(np.uint8)
        out.write(frame)
    out.release()

def run_test():
    from backend.services.ai_detection import AIDetectionService
    from backend.services.preprocessing import PreprocessingService

    print("\n=== Loading models (may take 10-30s) ===")
    svc = AIDetectionService()
    pre = PreprocessingService()

    print("\nModels status:")
    print(f"  pipe1 (deepfake):         {'LOADED' if svc._pipe1 else 'FAILED'}")
    print(f"  pipe2 (sdxl):             {'LOADED' if svc._pipe2 else 'FAILED'}")
    print(f"  pipe3 (ai-image-detect):  {'LOADED' if svc._pipe3 else 'FAILED'}")
    print(f"  pipe4 (AIorNot):          {'LOADED' if svc._pipe4 else 'FAILED'}")
    print(f"  pipe5 (umm-maybe):        {'LOADED' if svc._pipe5 else 'FAILED'}")
    print(f"  face detector:            {'LOADED' if svc._face_det else 'FAILED'}")

    # --- Test raw model label output ---
    if svc._pipe1:
        print("\n=== RAW LABEL TEST: pipe1 (deepfake model) ===")
        try:
            from PIL import Image
            test_img = Image.fromarray(np.random.randint(100, 200, (224, 224, 3), dtype=np.uint8))
            result = svc._pipe1(test_img, top_k=None)
            print(f"  Labels returned: {[r['label'] for r in result]}")
            print(f"  Full result: {result}")
        except Exception as e:
            print(f"  ERROR: {e}")

    if svc._pipe2:
        print("\n=== RAW LABEL TEST: pipe2 (sdxl detector) ===")
        try:
            from PIL import Image
            test_img = Image.fromarray(np.random.randint(100, 200, (224, 224, 3), dtype=np.uint8))
            result = svc._pipe2(test_img, top_k=None)
            print(f"  Labels returned: {[r['label'] for r in result]}")
            print(f"  Full result: {result}")
        except Exception as e:
            print(f"  ERROR: {e}")

    if svc._pipe3:
        print("\n=== RAW LABEL TEST: pipe3 (ai-image-detector) ===")
        try:
            from PIL import Image
            test_img = Image.fromarray(np.random.randint(100, 200, (224, 224, 3), dtype=np.uint8))
            result = svc._pipe3(test_img, top_k=None)
            print(f"  Labels returned: {[r['label'] for r in result]}")
            print(f"  Full result: {result}")
        except Exception as e:
            print(f"  ERROR: {e}")

    if svc._pipe4:
        print("\n=== RAW LABEL TEST: pipe4 (Nahrawy/AIorNot) ===")
        try:
            from PIL import Image
            test_img = Image.fromarray(np.random.randint(100, 200, (224, 224, 3), dtype=np.uint8))
            result = svc._pipe4(test_img, top_k=None)
            print(f"  Labels returned: {[r['label'] for r in result]}")
            print(f"  Full result: {result}")
        except Exception as e:
            print(f"  ERROR: {e}")

    if svc._pipe5:
        print("\n=== RAW LABEL TEST: pipe5 (umm-maybe/AI-image-detector) ===")
        try:
            from PIL import Image
            test_img = Image.fromarray(np.random.randint(100, 200, (224, 224, 3), dtype=np.uint8))
            result = svc._pipe5(test_img, top_k=None)
            print(f"  Labels returned: {[r['label'] for r in result]}")
            print(f"  Full result: {result}")
        except Exception as e:
            print(f"  ERROR: {e}")

    # --- Full pipeline test ---
    with tempfile.TemporaryDirectory() as tmp:
        real_vid = os.path.join(tmp, "real.mp4")
        ai_vid   = os.path.join(tmp, "ai.mp4")
        make_video(real_vid, 30, "noise")
        make_video(ai_vid,   30, "smooth")

        for label, path in [("REAL video (noise)", real_vid), ("AI video (smooth)", ai_vid)]:
            print(f"\n=== TESTING: {label} ===")
            frames, meta = pre.extract_frames(path)
            print(f"  Frames extracted: {len(frames)}, size: {frames[0].shape if frames else 'none'}")
            result = svc.detect(frames, video_path=path)
            print(f"  Status:     {result['status']}")
            print(f"  Confidence: {result['confidence']}")
            sig = result['signals']
            print(f"  deepfake_model_score: {sig.get('deepfake_model_score')}")
            print(f"  sdxl_score:           {sig.get('sdxl_score')}")
            print(f"  ai_detector_score:    {sig.get('ai_detector_score')}")
            print(f"  ai_or_not_score:      {sig.get('ai_or_not_score')}")
            print(f"  umm_maybe_score:      {sig.get('umm_maybe_score')}")
            print(f"  heuristic_score:      {sig.get('heuristic_score')}")
            print(f"  noise_signal:         {sig.get('noise_signal')}")
            print(f"  temporal_signal:      {sig.get('temporal_signal')}")
            print(f"  edge_signal:          {sig.get('edge_signal')}")
            print(f"  fft_signal:           {sig.get('fft_signal')}")
            print(f"  color_signal:         {sig.get('color_signal')}")
            print(f"  final_ai_score:       {sig.get('final_ai_score')}")
            print(f"  detection_method:     {sig.get('detection_method')}")

if __name__ == "__main__":
    run_test()
