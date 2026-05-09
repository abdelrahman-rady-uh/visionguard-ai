#!/usr/bin/env python3
"""
Full AI Detection Test - Real Videos + Synthetic AI frames
Tests the complete ensemble (ML models + heuristics) when available,
falls back to heuristics-only gracefully.
"""
import sys, os, cv2, numpy as np, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"

from backend.services.ai_detection import AIDetectionService

# ─── Video loader ────────────────────────────────────────────────────────────
def load_video_frames(path, max_frames=48):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return [], {}
    total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps    = cap.get(cv2.CAP_PROP_FPS)
    w      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    dur    = total / fps if fps > 0 else 0
    step   = max(1, total // max_frames)
    frames = []
    for i in range(0, total, step):
        if len(frames) >= max_frames:
            break
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, frame = cap.read()
        if ok:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    return frames, {"total_frames": total, "fps": fps, "width": w, "height": h, "duration_sec": round(dur,1)}

# ─── Synthetic frame generators ──────────────────────────────────────────────
def make_real_frames(n=48):
    h, w = 480, 854
    frames = []
    rng = np.random.default_rng(42)
    for i in range(n):
        base = rng.integers(40, 220, (h, w, 3), dtype=np.uint8)
        for _ in range(5):
            x, y = rng.integers(30, w-30), rng.integers(30, h-30)
            r = int(rng.integers(15, 50))
            col = tuple(int(v) for v in rng.integers(40, 210, 3))
            cv2.circle(base, (x, y), r, col, -1)
        # natural texture
        for _ in range(3):
            x1,y1 = rng.integers(0,w-80), rng.integers(0,h-80)
            x2,y2 = x1+rng.integers(40,80), y1+rng.integers(40,80)
            col = tuple(int(v) for v in rng.integers(40,210,3))
            cv2.rectangle(base,(x1,y1),(x2,y2),col,-1)
        edges = cv2.Canny(base, 40, 120)
        base[edges > 0] = np.minimum(base[edges > 0].astype(int) + 40, 255).astype(np.uint8)
        # camera sensor noise
        noise = rng.normal(0, 8, (h, w, 3))
        frame = np.clip(base.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        # motion
        offset = int(np.sin(i * 0.3) * 12)
        frame = np.roll(frame, offset, axis=1)
        frames.append(frame)
    return frames

def make_ai_frames(n=48):
    h, w = 480, 854
    frames = []
    for i in range(n):
        x = np.linspace(0, 2*np.pi, w)
        y = np.linspace(0, 2*np.pi, h)
        X, Y = np.meshgrid(x, y)
        r = (128 + 55*np.sin(X + i*0.05)).astype(np.uint8)
        g = (128 + 55*np.cos(Y + i*0.04)).astype(np.uint8)
        b = (128 + 40*np.sin((X+Y)*0.5 + i*0.03)).astype(np.uint8)
        frame = np.stack([r, g, b], axis=2)
        # AI smoothing - applied multiple times
        for _ in range(3):
            frame = cv2.GaussianBlur(frame, (7,7), 2)
        # perfectly uniform shapes (AI characteristic)
        xp = int((np.sin(i*0.12)+1) * w/2)
        yp = int((np.cos(i*0.09)+1) * h/2)
        cv2.ellipse(frame, (xp,yp), (40,25), 0, 0, 360, (160,160,160), -1)
        # minimal noise (AI videos are too clean)
        noise = np.random.normal(0, 0.8, (h, w, 3))
        frame = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)
        frames.append(frame)
    return frames

# ─── Printer ─────────────────────────────────────────────────────────────────
def run_test(label, frames, video_path=None):
    print(f"\n{'='*68}")
    print(f"  TEST: {label}")
    print(f"{'='*68}")
    t0 = time.time()
    svc = AIDetectionService()
    result = svc.detect(frames, video_path=video_path)
    elapsed = time.time() - t0

    status     = result["status"]
    confidence = result["confidence"]
    signals    = result.get("signals", {})
    reasons    = result.get("reasons", {})
    method     = signals.get("detection_method", "unknown")

    print(f"  Result    : {status}")
    print(f"  Confidence: {confidence:.2f}%")
    print(f"  AI Score  : {signals.get('final_ai_score', 'N/A')}")
    print(f"  Method    : {method}")
    print(f"  Time      : {elapsed:.1f}s")
    print()
    print("  [ ML Models ]")
    ml_scores = [
        ("Deepfake face (EfficientNet-B4)",   signals.get("deepfake_model_score")),
        ("SDXL/Diffusion (ViT)",              signals.get("sdxl_score")),
        ("AI image detector (EfficientNet)",  signals.get("ai_detector_score")),
        ("AIorNot (ViT-B/16)",                signals.get("ai_or_not_score")),
        ("umm-maybe classifier",              signals.get("umm_maybe_score")),
        ("FaceForensics++ Xception",          signals.get("ff_xception_score")),
    ]
    any_ml = False
    for name, score in ml_scores:
        if score is not None:
            any_ml = True
            bar = "#" * int(score / 5)
            print(f"    {name:<38} {score:5.1f}%  [{bar:<20}]")
    if not any_ml:
        print("    (no ML models loaded - heuristics only)")
    print()
    print("  [ Forensic Heuristics ]")
    heuristics = [
        ("Noise signal (low=AI, high=Real)", signals.get("noise_signal")),
        ("Temporal consistency",             signals.get("temporal_signal")),
        ("Edge density",                     signals.get("edge_signal")),
        ("FFT frequency spectrum",           signals.get("fft_signal")),
        ("Color saturation uniformity",      signals.get("color_signal")),
    ]
    for name, score in heuristics:
        if score is not None:
            bar = "#" * int(score / 5)
            print(f"    {name:<38} {score:5.1f}%  [{bar:<20}]")
    print()
    faces = signals.get("faces_detected_in_frames", 0)
    print(f"  Faces detected : {faces}")
    print(f"  Frames analyzed: {signals.get('frames_analyzed', len(frames))}")
    if reasons.get("summary"):
        print(f"\n  Summary: {reasons['summary']}")
    if reasons.get("top_factors"):
        print("  Top signals:")
        for f in reasons["top_factors"][:3]:
            print(f"    - {f}")
    return status, confidence, signals

# ─── Main ────────────────────────────────────────────────────────────────────
REAL_VIDEO_1 = r"c:\Users\compumarts\Desktop\eea omar\uploads\20260417234909_WhatsApp_Video_2026-04-17_at_2.40.40_AM.mp4"
REAL_VIDEO_2 = r"c:\Users\compumarts\Desktop\eea omar\uploads\20260417234926_WhatsApp_Video_2026-04-17_at_1.45.04_AM.mp4"

print("\n" + "="*68)
print("  VisionGuard AI v10.0 - Full Detection Test Suite")
print("  Testing: Real WhatsApp videos + Synthetic AI frames")
print("="*68)

tests = []

# Real videos (user's actual WhatsApp footage)
print("\n[*] Loading real WhatsApp video 1...")
frames1, meta1 = load_video_frames(REAL_VIDEO_1)
if frames1:
    print(f"    {meta1['total_frames']} frames, {meta1['fps']}fps, {meta1['width']}x{meta1['height']}, {meta1['duration_sec']}s")
    s, c, sig = run_test("YOUR WhatsApp Video 1 (Real video)", frames1, REAL_VIDEO_1)
    tests.append(("WhatsApp Video 1", s, c, "Real"))

print("\n[*] Loading real WhatsApp video 2...")
frames2, meta2 = load_video_frames(REAL_VIDEO_2)
if frames2:
    print(f"    {meta2['total_frames']} frames, {meta2['fps']}fps, {meta2['width']}x{meta2['height']}, {meta2['duration_sec']}s")
    s, c, sig = run_test("YOUR WhatsApp Video 2 (Real video)", frames2, REAL_VIDEO_2)
    tests.append(("WhatsApp Video 2", s, c, "Real"))

# Synthetic AI frames
print("\n[*] Generating synthetic AI-generated frames...")
ai_frames = make_ai_frames(48)
s, c, sig = run_test("SYNTHETIC AI-Generated Video", ai_frames)
tests.append(("Synthetic AI Video", s, c, "AI"))

# Synthetic real frames
print("\n[*] Generating synthetic real-looking frames...")
real_frames = make_real_frames(48)
s, c, sig = run_test("SYNTHETIC Real-Looking Video", real_frames)
tests.append(("Synthetic Real Video", s, c, "Real"))

# ─── Final summary ───────────────────────────────────────────────────────────
print("\n" + "="*68)
print("  FINAL RESULTS SUMMARY")
print("="*68)
print(f"  {'Video':<30} {'Result':<22} {'Confidence':>10}  {'Verdict'}")
print(f"  {'-'*65}")
correct = 0
for label, status, conf, expected in tests:
    if expected == "Real":
        ok = status in ("Real", "Likely Real")
    else:
        ok = status in ("AI-Generated", "Likely AI-Generated")
    verdict = "[CORRECT]" if ok else "[WRONG]"
    if ok:
        correct += 1
    print(f"  {label:<30} {status:<22} {conf:>9.2f}%  {verdict}")

accuracy = correct / len(tests) * 100 if tests else 0
print(f"\n  Overall accuracy: {accuracy:.0f}% ({correct}/{len(tests)})")
print("="*68)
