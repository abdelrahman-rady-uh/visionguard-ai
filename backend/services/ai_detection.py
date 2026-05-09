#!/usr/bin/env python3
"""
AI Detection Service v10.0 — 6-Model ML Ensemble + Reasoning Engine

HuggingFace models (auto-download):
  pipe1  dima806/deepfake_vs_real_image_detection  EfficientNet-B4  face-level deepfakes
  pipe2  Organika/sdxl-detector                    ViT              diffusion / SDXL artefacts
  pipe3  haywoodsloan/ai-image-detector-deploy     EfficientNet-B4  diffusion / GAN content
  pipe4  Nahrawy/AIorNot                           ViT-B/16         large-dataset general AI detector
  pipe5  umm-maybe/AI-image-detector               EfficientNet     general AI (SD, MJ, DALL-E)

FaceForensics++ model (local weights):
  pipe6  Xception trained on FF++ all-manipulations dataset

Heuristics v2 (noise · temporal · edge · FFT · color):
  noise    — photon / sensor noise absent in AI frames
  temporal — frame-to-frame inconsistency typical of AI
  edge     — unnaturally sparse edge density
  fft      — flat high-freq spectrum / upsampling checkerboard artefacts
  color    — oversaturated or suspiciously uniform colour histogram

Output includes 'reasons' block:
  verdict, summary, top_factors, ai_indicators, real_indicators, model_agreement
"""

import os
import cv2
import numpy as np
import logging
from PIL import Image
from backend.utils.security import normalize_confidence

# Disable tqdm progress bars to prevent OSError on stderr in server environments
os.environ.setdefault("TQDM_DISABLE", "1")

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline, AutoImageProcessor
    import transformers
    transformers.utils.logging.disable_progress_bar()
    import torch
    import torch.nn.functional as F
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers/torch not installed — heuristics-only mode")

_MODELS_DIR      = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
_YUNET_PATH      = os.path.join(_MODELS_DIR, "face_detection_yunet_2023mar.onnx")
_FF_WEIGHT_DIR   = os.path.join(_MODELS_DIR, "faceforensics", "extracted")
_HIRES_LONG_EDGE = 640
_HIRES_FRAMES    = 20


class AIDetectionService:
    """
    6-model ensemble + heuristics v2 with full human-readable reasoning.

    Ensemble weights (all 6 models + heuristics available):
      FACE mode    — pipe1 35% · pipe2 10% · pipe3 7% · pipe4 13% · pipe5 8% · pipe6 15% · heuristics 12%
      NO-FACE mode — pipe1 6%  · pipe2 15% · pipe3 15% · pipe4 20% · pipe5 15% · pipe6 16% · heuristics 13%
    Any unavailable model's weight redistributes proportionally to the rest.
    """

    def __init__(self):
        self._pipe1    = None   # dima806 deepfake/face
        self._pipe2    = None   # Organika sdxl
        self._pipe3    = None   # haywoodsloan ai-detect
        self._pipe4    = None   # Nahrawy AIorNot
        self._pipe5    = None   # umm-maybe AI-image-detector
        self._pipe6    = None   # FaceForensics++ Xception (local)
        self._pipe7    = None   # human faces AI vs real
        self._ff_device = "cpu"
        self._face_det = None
        self._models_loaded = False

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_models(self):
        if self._models_loaded:
            return
        self._models_loaded = True
        if not TRANSFORMERS_AVAILABLE:
            return
        device = 0 if torch.cuda.is_available() else -1
        self._ff_device = "cuda" if torch.cuda.is_available() else "cpu"

        # ── HuggingFace pipelines ─────────────────────────────────────
        for attr, model_id in [
            ("_pipe1", "dima806/deepfake_vs_real_image_detection"),
            ("_pipe2", "Organika/sdxl-detector"),
            ("_pipe3", "haywoodsloan/ai-image-detector-deploy"),
            ("_pipe5", "umm-maybe/AI-image-detector"),
            ("_pipe7", "dima806/human_faces_ai_vs_real_image_detection"),
        ]:
            try:
                setattr(self, attr,
                        pipeline("image-classification", model=model_id, device=device))
                logger.info(f"Loaded: {model_id}")
            except Exception as e:
                logger.error(f"Failed to load {model_id}: {e}")

        # Nahrawy/AIorNot — old preprocessor_config.json: supply explicit ViT processor
        try:
            vit_proc = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224")
            self._pipe4 = pipeline(
                "image-classification",
                model="Nahrawy/AIorNot",
                image_processor=vit_proc,
                device=device,
            )
            logger.info("Loaded: Nahrawy/AIorNot (explicit ViT processor)")
        except Exception as e:
            logger.error(f"Failed to load Nahrawy/AIorNot: {e}")

        # ── FaceForensics++ Xception ──────────────────────────────────
        self._load_ff_xception()

        # ── YuNet face detector ───────────────────────────────────────
        try:
            self._face_det = cv2.FaceDetectorYN.create(
                _YUNET_PATH, "", (320, 320),
                score_threshold=0.55, nms_threshold=0.3, top_k=5,
            )
            logger.info("Loaded: YuNet face detector")
        except Exception as e:
            logger.error(f"YuNet load failed: {e}")

    def _load_ff_xception(self):
        """Load the FaceForensics++ Xception model from local weights."""
        if not TRANSFORMERS_AVAILABLE:
            return
        try:
            from backend.models.xception_model import build_xception_ff, load_faceforensics_weights
        except ImportError as e:
            logger.error(f"Cannot import xception_model: {e}")
            return

        model = build_xception_ff(num_classes=2, dropout=0.0)

        # Search for the best weight file: prefer all_manipulations, fall back to any .p / .pth
        weight_path = None
        _FF_SUBSET = os.path.join(_FF_WEIGHT_DIR,
                                   "faceforensics++_models_subset", "face_detection", "xception")
        candidates = [
            os.path.join(_FF_SUBSET, "all_raw.p"),          # best: all manipulations, raw quality
            os.path.join(_FF_SUBSET, "all_c23.p"),           # fallback: c23 compression
            os.path.join(_FF_SUBSET, "all_c40.p"),           # fallback: c40 compression
            os.path.join(_FF_WEIGHT_DIR, "all_raw.p"),
        ]
        # Also scan recursively for any .p / .pth files
        if os.path.isdir(_FF_WEIGHT_DIR):
            for root, _, files in os.walk(_FF_WEIGHT_DIR):
                for fn in files:
                    if fn.endswith((".p", ".pth", ".pt")):
                        candidates.append(os.path.join(root, fn))

        for c in candidates:
            if os.path.exists(c):
                weight_path = c
                break

        if weight_path is None:
            logger.warning("FF++ weights not found — Xception model will use random weights "
                           "(reduced accuracy until weights extracted)")
            self._pipe6 = model.eval().to(self._ff_device)
            return

        if load_faceforensics_weights(model, weight_path):
            model.eval().to(self._ff_device)
            self._pipe6 = model
            logger.info(f"Loaded: FaceForensics++ Xception from {weight_path}")
        else:
            logger.error("FF++ weight loading failed — Xception disabled")

    # ------------------------------------------------------------------
    # Frame / face utilities
    # ------------------------------------------------------------------

    def _extract_hires_frames(self, video_path, n_frames):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        total  = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        long_e = max(orig_w, orig_h)
        target = (int(orig_w * _HIRES_LONG_EDGE / long_e),
                  int(orig_h * _HIRES_LONG_EDGE / long_e)) if long_e > _HIRES_LONG_EDGE else None

        indices = list(dict.fromkeys(np.linspace(0, total - 1, min(n_frames, total), dtype=int)))
        frames  = []
        for fi in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(fi))
            ok, frame = cap.read()
            if not ok:
                continue
            if target:
                frame = cv2.resize(frame, target, interpolation=cv2.INTER_AREA)
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        cap.release()
        return frames

    def _extract_faces(self, frame_rgb, min_size=48):
        if self._face_det is None:
            return []
        try:
            h, w = frame_rgb.shape[:2]
            self._face_det.setInputSize((w, h))
            _, faces = self._face_det.detect(cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR))
            if faces is None:
                return []
            crops = []
            for face in faces[:3]:
                x, y, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])
                if fw < min_size or fh < min_size:
                    continue
                pad = int(0.25 * max(fw, fh))
                x1, y1 = max(0, x - pad), max(0, y - pad)
                x2, y2 = min(w, x + fw + pad), min(h, y + fh + pad)
                crops.append(frame_rgb[y1:y2, x1:x2])
            return crops
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Label → fake-probability mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _to_fake_prob(results):
        _FAKE_KEYS  = ("fake", "artificial", "ai generated", "ai image",
                       "deepfake", "sdxl", "generated", "diffusion")
        _REAL_KEYS  = ("real", "human", "genuine", "authentic",
                       "original", "not ai", "not_ai", "natural", "photo")
        _FAKE_EXACT = {"ai", "1", "yes", "true", "fake"}
        _REAL_EXACT = {"not ai", "0", "no", "false", "real"}

        for r in results:
            lbl   = r["label"].lower().replace("-", " ").replace("_", " ").strip()
            score = float(r["score"])
            if any(k in lbl for k in _FAKE_KEYS):
                return score
            if any(k in lbl for k in _REAL_KEYS):
                return 1.0 - score
            if lbl in _FAKE_EXACT:
                return score
            if lbl in _REAL_EXACT:
                return 1.0 - score
        return 0.5

    # ------------------------------------------------------------------
    # Model runners
    # ------------------------------------------------------------------

    def _run_pipe1(self, frames):
        """Model 1 — face crops preferred, whole-frame fallback."""
        if self._pipe1 is None:
            return None, 0
        inputs, faces_found = [], 0
        for frame in frames:
            crops = self._extract_faces(frame)
            if crops:
                faces_found += 1
                for c in crops[:2]:
                    inputs.append(Image.fromarray(c).resize((224, 224)))
            else:
                inputs.append(Image.fromarray(frame).resize((224, 224)))
        if not inputs:
            return None, 0
        try:
            scores = [self._to_fake_prob(r) for r in self._pipe1(inputs, top_k=2)]
            return float(np.mean(scores)), faces_found
        except Exception as e:
            logger.error(f"pipe1 error: {e}")
            return None, 0

    def _run_frame_pipe(self, pipe, frames, name):
        if pipe is None:
            return None
        inputs = [Image.fromarray(f).resize((224, 224)) for f in frames]
        try:
            scores = [self._to_fake_prob(r) for r in pipe(inputs, top_k=2)]
            return float(np.mean(scores))
        except Exception as e:
            logger.error(f"{name} error: {e}")
            return None

    def _run_ff_xception(self, frames):
        """Model 6 — FaceForensics++ Xception, prefers face crops."""
        if self._pipe6 is None:
            return None
        try:
            from backend.models.xception_model import preprocess_for_xception
            tensors = []
            for frame in frames[:12]:
                crops = self._extract_faces(frame)
                srcs = crops[:2] if crops else [frame]
                for src in srcs:
                    tensors.append(preprocess_for_xception(src))
            if not tensors:
                return None
            batch = torch.cat(tensors, dim=0).to(self._ff_device)
            with torch.no_grad():
                logits = self._pipe6(batch)
                probs = F.softmax(logits, dim=1)
                fake_p = probs[:, 1].cpu().numpy()
            return float(np.mean(fake_p))
        except Exception as e:
            logger.error(f"FF++ Xception error: {e}")
            return None

    def _run_face_ai_pipe(self, frames):
        """Model 7 - AI-generated human-face detector, face crops only."""
        if self._pipe7 is None:
            return None
        inputs = []
        for frame in frames[:16]:
            crops = self._extract_faces(frame)
            for crop in crops[:3]:
                inputs.append(Image.fromarray(crop).resize((224, 224)))
        if not inputs:
            return None
        try:
            scores = [self._to_fake_prob(r) for r in self._pipe7(inputs, top_k=2)]
            return float(np.mean(scores))
        except Exception as e:
            logger.error(f"face-ai detector error: {e}")
            return None
    # ------------------------------------------------------------------
    # Heuristics v2
    # ------------------------------------------------------------------

    def _heuristic(self, frames):
        noise    = self._h_noise(frames)
        temporal = self._h_temporal(frames)
        edge     = self._h_edge(frames)
        fft      = self._h_fft(frames)
        color    = self._h_color(frames)
        score    = (noise * 0.30 + temporal * 0.25 + edge * 0.15
                    + fft  * 0.20 + color   * 0.10)
        return score, noise, temporal, edge, fft, color

    def _h_noise(self, frames):
        levels = []
        for f in frames[:12]:
            gray = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY).astype(np.float32)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            levels.append(float(np.std(gray - blur)))
        avg = np.mean(levels) if levels else 5.0
        if   avg < 1.5: return 0.88
        elif avg < 3.0: return 0.68
        elif avg < 5.0: return 0.42
        elif avg < 8.0: return 0.18
        else:           return 0.05

    def _h_temporal(self, frames):
        diffs = []
        for i in range(1, min(len(frames), 20)):
            p = cv2.cvtColor(frames[i-1], cv2.COLOR_RGB2GRAY).astype(np.float32)
            c = cv2.cvtColor(frames[i],   cv2.COLOR_RGB2GRAY).astype(np.float32)
            diffs.append(float(np.mean(np.abs(c - p)) / 255.0))
        avg = np.mean(diffs) if diffs else 0.05
        if   avg < 0.003: return 0.88
        elif avg < 0.008: return 0.68
        elif avg < 0.015: return 0.42
        elif avg < 0.025: return 0.18
        else:             return 0.05

    def _h_edge(self, frames):
        densities = []
        for f in frames[:12]:
            gray = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY)
            densities.append(float(np.mean(cv2.Canny(gray, 50, 150) > 0)))
        avg = np.mean(densities) if densities else 0.10
        if   avg < 0.03: return 0.82
        elif avg < 0.06: return 0.58
        elif avg < 0.10: return 0.32
        elif avg < 0.15: return 0.12
        else:            return 0.04

    def _h_fft(self, frames):
        """Flat high-freq spectrum / upsampling checkerboard = AI signal."""
        scores = []
        for f in frames[:10]:
            gray = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY).astype(np.float32)
            h, w = gray.shape
            cy, cx = h // 2, w // 2
            mag    = np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(gray))))
            r_low  = max(3, min(cy, cx) // 20)
            low    = mag[cy - r_low:cy + r_low, cx - r_low:cx + r_low].mean()
            r_inner = int(min(cy, cx) * 0.75)
            hf_mask = np.ones((h, w), bool)
            hf_mask[cy - r_inner:cy + r_inner, cx - r_inner:cx + r_inner] = False
            high   = mag[hf_mask].mean() if hf_mask.any() else low * 0.3
            if low > 0:
                ratio = high / low
                scores.append(float(np.clip((ratio - 0.35) / 0.30 * 0.80 + 0.05, 0.05, 0.90)))
        return float(np.mean(scores)) if scores else 0.45

    def _h_color(self, frames):
        """Unnaturally uniform saturation = AI signal."""
        scores = []
        for f in frames[:12]:
            hsv      = cv2.cvtColor(f, cv2.COLOR_RGB2HSV)
            sat      = hsv[:, :, 1].astype(np.float32)
            sat_std  = float(np.std(sat))
            sat_mean = float(np.mean(sat))
            if   sat_std < 15:                        scores.append(0.82)
            elif sat_std < 28:                        scores.append(0.60)
            elif sat_mean > 180 and sat_std < 45:     scores.append(0.55)
            elif sat_std < 50:                        scores.append(0.35)
            else:                                     scores.append(0.12)
        return float(np.mean(scores)) if scores else 0.40

    # ------------------------------------------------------------------
    # Ensemble
    # ------------------------------------------------------------------

    def _ensemble(self, s1, s2, s3, s4, s5, s6, s7, heuristic, faces_found):
        if faces_found > 0:
            base_weights = [(s1, 0.24), (s2, 0.08), (s3, 0.06),
                            (s4, 0.10), (s5, 0.07), (s6, 0.12),
                            (s7, 0.23)]
            heuristic_w  = 0.10
        else:
            base_weights = [(s1, 0.06), (s2, 0.15), (s3, 0.15),
                            (s4, 0.20), (s5, 0.15), (s6, 0.16),
                            (s7, 0.00)]
            heuristic_w  = 0.13

        available = [(s, w) for s, w in base_weights if s is not None]
        if not available:
            return float(np.clip(heuristic * 100, 0, 100)), "Heuristics only"

        used_model_w = sum(w for _, w in available)
        total_w      = used_model_w + heuristic_w
        ml_score     = sum(s * w for s, w in available) / used_model_w
        raw          = (ml_score * used_model_w + heuristic * heuristic_w) / total_w

        label_map = {0: "deepfake-det", 1: "sdxl-det",
                     2: "ai-image-det", 3: "AIorNot",
                     4: "umm-maybe",    5: "FF++-Xception",
                     6: "face-ai-det"}
        active = [label_map[i] for i, (s, _) in enumerate(base_weights) if s is not None]
        mode   = "face-mode" if faces_found > 0 else "no-face-mode"
        return float(np.clip(raw * 100, 0, 100)), \
               f"Ensemble[{mode}] ({', '.join(active)}) + heuristics-v2"

    # ------------------------------------------------------------------
    # Reasoning engine
    # ------------------------------------------------------------------

    def _generate_reasons(self, s1, s2, s3, s4, s5, s6, s7,
                          h_noise, h_temporal, h_edge, h_fft, h_color,
                          faces_found, status, ai_score):
        """
        Produce a human-readable explanation dict that answers:
          - WHY is this AI-generated or real?
          - Which specific signals drove the decision?
          - How much do the models agree?
        """
        ai_indicators   = []
        real_indicators = []
        model_votes_ai  = 0
        model_votes_real = 0
        model_count      = 0

        # ── Per-model verdicts ────────────────────────────────────────
        model_info = [
            (s1, "Deepfake face detector (EfficientNet-B4, trained on face-swap datasets)"),
            (s2, "SDXL/Diffusion detector (ViT, specialized for diffusion-model outputs)"),
            (s3, "General AI image detector (EfficientNet-B4, GAN + diffusion content)"),
            (s4, "AIorNot (ViT, large dataset: Stable Diffusion, Midjourney, DALL-E)"),
            (s5, "AI image classifier (EfficientNet, general AI-generated content)"),
            (s6, "FaceForensics++ Xception (trained on 1000s of face-manipulation videos)"),
            (s7, "Human-face AI detector (trained on AI-generated vs real face images)"),
        ]
        for score, label in model_info:
            if score is None:
                continue
            model_count += 1
            pct = round(score * 100)
            if score >= 0.65:
                ai_indicators.append(
                    f"{label}: {pct}% AI confidence — strong manipulation signal")
                model_votes_ai += 1
            elif score >= 0.50:
                ai_indicators.append(
                    f"{label}: {pct}% AI confidence — leans artificial")
                model_votes_ai += 1
            elif score <= 0.35:
                real_indicators.append(
                    f"{label}: {round((1-score)*100)}% real confidence — no manipulation detected")
                model_votes_real += 1
            else:
                real_indicators.append(
                    f"{label}: {pct}% (ambiguous — near threshold)")

        # ── Heuristic verdicts ────────────────────────────────────────
        heuristic_map = [
            (h_noise,    "Camera sensor noise",
             "Real cameras always produce natural photon noise; AI images are suspiciously clean.",
             "Natural sensor noise present — consistent with genuine camera footage."),
            (h_temporal, "Frame-to-frame temporal consistency",
             "Frames are nearly identical — AI video generators often lack natural motion dynamics.",
             "Natural motion variation between frames — consistent with real video."),
            (h_edge,     "Edge density",
             "Edge map is unusually sparse — AI images often lack the fine structural detail of real photos.",
             "Rich edge structure present — consistent with real photographic content."),
            (h_fft,      "Frequency spectrum (FFT analysis)",
             "Frequency spectrum is too flat — real camera footage follows a natural 1/f noise profile; "
             "AI/GAN outputs often show upsampling artefacts.",
             "Natural 1/f frequency falloff — consistent with real camera optics."),
            (h_color,    "Colour saturation distribution",
             "Colour saturation is suspiciously uniform or over-saturated — AI models often produce "
             "an unnaturally 'clean' or hyper-vivid palette.",
             "Natural colour variation present — consistent with real-world lighting."),
        ]
        for score, name, ai_msg, real_msg in heuristic_map:
            pct = round(score * 100)
            if score >= 0.65:
                ai_indicators.append(f"{name} ({pct}%): {ai_msg}")
            elif score >= 0.50:
                ai_indicators.append(f"{name} ({pct}%): moderately suspicious — {ai_msg.split('—')[0].strip()}")
            elif score <= 0.30:
                real_indicators.append(f"{name} ({pct}%): {real_msg}")

        # ── Face context ──────────────────────────────────────────────
        if faces_found > 0:
            face_note = (f"{faces_found} face(s) detected — deepfake / face-manipulation "
                         "models were weighted more heavily in this analysis.")
        else:
            face_note = ("No faces detected — general AI-content detectors "
                         "were weighted more heavily.")

        # ── Model agreement ───────────────────────────────────────────
        if model_count == 0:
            agreement = "No ML models available — heuristics only."
        else:
            pct_agree_ai = round(model_votes_ai / model_count * 100)
            if model_votes_ai == model_count:
                agreement = f"UNANIMOUS — all {model_count} models agree this is AI-generated."
            elif model_votes_ai >= model_count * 0.75:
                agreement = (f"STRONG CONSENSUS — {model_votes_ai}/{model_count} models "
                             f"({pct_agree_ai}%) say AI-generated.")
            elif model_votes_ai > model_votes_real:
                agreement = (f"MAJORITY — {model_votes_ai}/{model_count} models lean AI, "
                             f"{model_votes_real}/{model_count} lean real.")
            elif model_votes_real > model_votes_ai:
                agreement = (f"MAJORITY — {model_votes_real}/{model_count} models lean real, "
                             f"{model_votes_ai}/{model_count} lean AI.")
            elif model_votes_ai == model_votes_real:
                agreement = (f"SPLIT — {model_votes_ai}/{model_count} models lean AI, "
                             f"{model_votes_real}/{model_count} lean real. Heuristics broke the tie.")
            else:
                agreement = f"{model_votes_ai}/{model_count} models lean AI."

        # ── Top factors (most impactful signals) ─────────────────────
        all_scored = []
        named_scores = [
            (s1, "deepfake face model"), (s2, "SDXL/diffusion model"),
            (s3, "AI image model"),      (s4, "AIorNot model"),
            (s5, "umm-maybe model"),     (s6, "FF++ Xception"),
            (s7, "human-face AI model"),
            (h_noise, "noise heuristic"), (h_temporal, "temporal heuristic"),
            (h_edge,  "edge heuristic"),  (h_fft, "FFT heuristic"),
            (h_color, "colour heuristic"),
        ]
        for score, name in named_scores:
            if score is None:
                continue
            # Distance from 0.5 = confidence of the signal's vote
            all_scored.append((abs(score - 0.5), score, name))

        all_scored.sort(reverse=True)
        top_factors = []
        for _, score, name in all_scored[:5]:
            pct = round(score * 100)
            direction = "AI" if score >= 0.5 else "real"
            top_factors.append(
                f"{name}: {pct}% — strongest vote for {direction}"
            )

        # ── One-sentence summary ──────────────────────────────────────
        score_word = (
            "overwhelming" if ai_score >= 80 else
            "strong"       if ai_score >= 65 else
            "moderate"     if ai_score >= 55 else
            "weak"         if ai_score >= 43 else
            "low"          if ai_score >= 30 else
            "very low"
        )
        if status in ("AI-Generated", "Likely AI-Generated"):
            summary = (
                f"This content shows {score_word} signs of AI generation (composite score "
                f"{round(ai_score)}%). {agreement}"
            )
        elif status in ("Real", "Likely Real"):
            summary = (
                f"This content shows {score_word} signs of being genuine/real (composite AI "
                f"score {round(ai_score)}%). {agreement}"
            )
        else:
            summary = (
                f"The analysis is inconclusive (composite score {round(ai_score)}%) — "
                f"signals are mixed. {agreement}"
            )

        return {
            "verdict":         status,
            "summary":         summary,
            "face_context":    face_note,
            "model_agreement": agreement,
            "top_factors":     top_factors,
            "ai_indicators":   ai_indicators,
            "real_indicators": real_indicators,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, frames, video_path=None):
        if len(frames) < 3:
            return {
                "status": "Inconclusive", "confidence": 50.0,
                "signals":  {"error": "Insufficient frames for analysis"},
                "reasons":  {"verdict": "Inconclusive", "summary": "Not enough frames to analyse.",
                             "top_factors": [], "ai_indicators": [],
                             "real_indicators": [], "model_agreement": "N/A"},
                "frame_analysis": [],
            }
        try:
            self._load_models()
            hires = self._extract_hires_frames(video_path, _HIRES_FRAMES) if video_path else []
            if not hires:
                hires = frames[:_HIRES_FRAMES]

            s1, faces_found = self._run_pipe1(hires)
            s2  = self._run_frame_pipe(self._pipe2, hires[:12], "pipe2")
            s3  = self._run_frame_pipe(self._pipe3, hires[:12], "pipe3")
            s4  = self._run_frame_pipe(self._pipe4, hires[:12], "pipe4/AIorNot")
            s5  = self._run_frame_pipe(self._pipe5, hires[:12], "pipe5/umm-maybe")
            s6  = self._run_ff_xception(hires)
            s7  = self._run_face_ai_pipe(hires)

            heuristic, h_noise, h_temporal, h_edge, h_fft, h_color = self._heuristic(frames)
            ai_score, method = self._ensemble(s1, s2, s3, s4, s5, s6, s7,
                                              heuristic, faces_found)
            status, confidence = self._classify(ai_score)
            reasons = self._generate_reasons(
                s1, s2, s3, s4, s5, s6, s7,
                h_noise, h_temporal, h_edge, h_fft, h_color,
                faces_found, status, ai_score,
            )

            signals = {
                "deepfake_model_score":     round(s1 * 100, 2) if s1 is not None else None,
                "sdxl_score":               round(s2 * 100, 2) if s2 is not None else None,
                "ai_detector_score":        round(s3 * 100, 2) if s3 is not None else None,
                "ai_or_not_score":          round(s4 * 100, 2) if s4 is not None else None,
                "umm_maybe_score":          round(s5 * 100, 2) if s5 is not None else None,
                "ff_xception_score":        round(s6 * 100, 2) if s6 is not None else None,
                "face_ai_generated_score":  round(s7 * 100, 2) if s7 is not None else None,
                "heuristic_score":          round(heuristic  * 100, 2),
                "noise_signal":             round(h_noise    * 100, 2),
                "temporal_signal":          round(h_temporal * 100, 2),
                "edge_signal":              round(h_edge     * 100, 2),
                "fft_signal":               round(h_fft      * 100, 2),
                "color_signal":             round(h_color    * 100, 2),
                "final_ai_score":           round(ai_score,   2),
                "faces_detected_in_frames": faces_found,
                "frames_analyzed":          len(frames),
                "hires_frames_used":        len(hires),
                "detection_method":         method,
            }

            return {
                "status":         status,
                "confidence":     confidence,
                "signals":        signals,
                "reasons":        reasons,
                "frame_analysis": [],
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "status": "Analysis Error", "confidence": 0.0,
                "signals": {"error": str(e)},
                "reasons": {"verdict": "Error", "summary": f"Analysis failed: {e}",
                            "top_factors": [], "ai_indicators": [],
                            "real_indicators": [], "model_agreement": "N/A"},
                "frame_analysis": [],
            }

    def _classify(self, ai_score):
        if ai_score >= 72:
            status     = "AI-Generated"
            confidence = normalize_confidence(min(99.0, 86.0 + (ai_score - 72) * 0.46))
        elif ai_score >= 57:
            status     = "Likely AI-Generated"
            confidence = normalize_confidence(min(95.0, 73.0 + (ai_score - 57) * 0.87))
        elif ai_score >= 43:
            status     = "Inconclusive"
            confidence = normalize_confidence(55.0 + abs(ai_score - 50.0) * 0.43)
        elif ai_score >= 28:
            status     = "Likely Real"
            confidence = normalize_confidence(min(95.0, 73.0 + (43.0 - ai_score) * 0.87))
        else:
            status     = "Real"
            confidence = normalize_confidence(min(99.0, 86.0 + (28.0 - ai_score) * 0.46))
        return status, confidence
