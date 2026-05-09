#!/usr/bin/env python3
import sys, os, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"

from backend.services.ai_detection import AIDetectionService

def create_real_frames(num_frames=48, noise_level=0.08):
    frames = []
    h, w = 216, 384
    for i in range(num_frames):
        base = np.random.randint(50, 200, (h, w, 3), dtype=np.uint8)
        for _ in range(3):
            x, y = np.random.randint(20, w-20), np.random.randint(20, h-20)
            cv2.circle(base, (x, y), np.random.randint(10, 30), tuple(np.random.randint(50,200,3).tolist()), -1)
        edges = cv2.Canny(base, 30, 90)
        base[edges > 0] = np.minimum(base[edges > 0] + 30, 255)
        grain = np.random.normal(0, noise_level * 25, (h, w, 3))
        frame = np.clip(base.astype(np.float32) + grain, 0, 255).astype(np.uint8)
        frame = np.roll(frame, (i % 20) * 5 - 50, axis=1)
        frames.append(frame)
    return frames

def create_ai_frames(num_frames=48):
    frames = []
    h, w = 216, 384
    for i in range(num_frames):
        x = np.linspace(0, 1, w)
        y = np.linspace(0, 1, h)
        X, Y = np.meshgrid(x, y)
        r = (128 + 60 * np.sin(X * 2 * np.pi)).astype(np.uint8)
        g = (128 + 60 * np.cos(Y * 2 * np.pi)).astype(np.uint8)
        b = (128 + 40 * np.sin((X + Y) * np.pi)).astype(np.uint8)
        frame = np.stack([r, g, b], axis=2)
        xp = int((np.sin(i * 0.1) + 1) * w / 2)
        yp = int((np.cos(i * 0.08) + 1) * h / 2)
        cv2.circle(frame, (xp, yp), 25, (150, 150, 150), -1)
        frame = cv2.GaussianBlur(cv2.GaussianBlur(frame, (5,5), 2), (5,5), 1)
        noise = np.random.normal(0, 1, (h, w, 3))
        frame = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        frames.append(frame)
    return frames

def test(frames, label, expect_ai):
    print(f"\n{'='*65}")
    print(f"TEST: {label}")
    print(f"{'='*65}")
    detector = AIDetectionService()
    result = detector.detect(frames)
    status = result['status']
    confidence = result['confidence']
    method = result.get('signals', {}).get('detection_method', 'unknown')
    heuristic = result.get('signals', {}).get('heuristic_score', 'N/A')
    fft = result.get('signals', {}).get('fft_signal', 'N/A')
    noise = result.get('signals', {}).get('noise_signal', 'N/A')
    edge = result.get('signals', {}).get('edge_signal', 'N/A')
    color = result.get('signals', {}).get('color_signal', 'N/A')
    temporal = result.get('signals', {}).get('temporal_signal', 'N/A')

    print(f"  Result:     {status}")
    print(f"  Confidence: {confidence:.2f}%")
    print(f"  Method:     {method}")
    print(f"  Signals:")
    print(f"    Heuristic Score : {heuristic}")
    print(f"    Noise Signal    : {noise}")
    print(f"    Edge Signal     : {edge}")
    print(f"    FFT Signal      : {fft}")
    print(f"    Color Signal    : {color}")
    print(f"    Temporal Signal : {temporal}")

    if expect_ai:
        correct = status in ["AI-Generated", "Likely AI-Generated"]
    else:
        correct = status in ["Real", "Likely Real"]

    mark = "[CORRECT]" if correct else "[WRONG]"
    print(f"\n  {mark} - Expected: {'AI-Generated' if expect_ai else 'Real'}, Got: {status}")
    return correct, confidence

print("\n" + "="*65)
print("VisionGuard AI - Detection Test")
print("="*65)

tests = [
    (create_real_frames(48, 0.08),  "REAL Video",               False),
    (create_ai_frames(48),           "AI-GENERATED Video",       True),
    (create_real_frames(48, 0.12),  "REAL Video (High Noise)",  False),
    (create_ai_frames(48),           "AI-GENERATED (Variant)",   True),
]

results = []
for frames, label, expect_ai in tests:
    correct, conf = test(frames, label, expect_ai)
    results.append((label, correct, conf))

print("\n" + "="*65)
print("SUMMARY")
print("="*65)
for label, correct, conf in results:
    mark = "[PASS]" if correct else "[FAIL]"
    print(f"  {mark}  {label:<35} Confidence: {conf:.2f}%")

passed = sum(1 for _, c, _ in results if c)
total = len(results)
accuracy = passed / total * 100
print(f"\n  Overall Accuracy: {accuracy:.1f}% ({passed}/{total} correct)")
if accuracy >= 75:
    print("  VALIDATION PASSED")
else:
    print("  VALIDATION FAILED - below 75% threshold")
print("="*65)
