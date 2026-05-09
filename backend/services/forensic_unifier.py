"""
Forensic Unifier — Content-Aware Scoring System
================================================

Pipeline (in order):

    1. NORMALIZATION  — convert every model output to 0-100 (high = AI)
    2. CLASSIFICATION — detect content type: face | animal | general
    3. ROUTING        — select only the relevant model groups per content type
    4. SCORING        — apply content-type-specific weighted formula → FAS
    5. UNIFICATION    — FAS drives every section (Core Findings, Confidence
                        Scores, Risk Badge) with zero independent values

Forensic Authenticity Score (FAS):
    100 = Definitely Real / Authentic
    0   = Definitely AI-Generated / Manipulated

All intermediate values are injected into ai_detection.signals so they
appear in the Forensic Breakdown panel and are fully traceable.
"""

# ══════════════════════════════════════════════════════════════════════════════
# 1. NORMALIZATION
# ══════════════════════════════════════════════════════════════════════════════

def _n(value, default=None):
    """
    Normalize any model score to the 0-100 range (high = AI-generated).

    Handles:
      - None / missing values       → returns default
      - 0-1 float probabilities     → scaled × 100
      - Already 0-100 percentages   → clamped and returned
    """
    if value is None:
        return default
    v = float(value)
    # Detect 0-1 probability format: a float between 0 and 1 exclusive
    # (pure integers 0 and 1 are already percentage-compatible)
    if 0.0 < v < 1.0:
        v = v * 100.0
    return round(max(0.0, min(100.0, v)), 2)


def _avg(values):
    """Mean of a list, ignoring Nones. Returns 50.0 if no values."""
    clean = [v for v in values if v is not None]
    return round(sum(clean) / len(clean), 2) if clean else 50.0


# ══════════════════════════════════════════════════════════════════════════════
# 2. CONTENT-TYPE CLASSIFIER
# ══════════════════════════════════════════════════════════════════════════════

_ANIMAL_KEYWORDS = {
    "dog", "cat", "bird", "animal", "horse", "bear", "lion", "tiger",
    "elephant", "wolf", "fox", "rabbit", "deer", "cow", "pig", "sheep",
    "fish", "snake", "monkey", "gorilla", "cheetah", "leopard", "pet",
    "wildlife", "wild", "fauna", "duck", "chicken", "goat", "panda",
    "hamster", "parrot", "crocodile", "whale", "dolphin", "penguin",
}


def classify_content(signals, face_result, caption=""):
    """
    Detect video content type from available forensic signals and metadata.

    Decision logic:
        face    → at least one face detected by any detector
        animal  → no faces, but caption contains animal vocabulary
        general → everything else (landscapes, objects, text, scenes)

    Returns: "face" | "animal" | "general"
    """
    faces_in_frames = int(signals.get("faces_detected_in_frames") or 0)
    total_faces     = int(face_result.get("total_faces") or 0)
    has_faces       = faces_in_frames > 0 or total_faces > 0

    caption_words = set((caption or "").lower().split())
    has_animal    = bool(caption_words & _ANIMAL_KEYWORDS)

    if has_faces:
        return "face"
    if has_animal:
        return "animal"
    return "general"


# ══════════════════════════════════════════════════════════════════════════════
# 3. MODULE ROUTING SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

def route_modules(content_type, signals):
    """
    Select and aggregate the relevant model groups for the given content type.

    Model taxonomy
    ──────────────
    General AI detectors (work for ALL content types):
        sdxl_score        — SDXL / diffusion model detector (ViT)
        ai_detector_score — EfficientNet-B4, GAN + diffusion
        ai_or_not_score   — ViT, large multi-source dataset
        umm_maybe_score   — EfficientNet, general AI content

    Face-swap / deepfake-specific (ONLY valid for face-swap deepfakes):
        deepfake_model_score — EfficientNet-B4, trained on face-swap datasets
        ff_xception_score    — FaceForensics++ Xception, face manipulation

    Heuristic forensic signals (all content types, secondary evidence):
        noise_signal    — photon / sensor noise (real cameras = noisy)
        temporal_signal — frame-to-frame coherence (AI = too smooth)
        edge_signal     — edge density (AI = sparse edges)
        fft_signal      — high-freq spectrum flatness (AI = flat)
        color_signal    — saturation uniformity (AI = uniform)

    Face-content disagreement detection
    ────────────────────────────────────
    When content_type == "face", we compare general_ai_avg vs deepfake_avg.
    A large gap (> 40 points) where general models say AI but deepfake models
    say Real is the signature of AI-GENERATED content with faces — not a face-
    swap deepfake. In that case the routing mode switches to "face_ai_generated"
    and the deepfake models are given minimal weight (they are wrong for this
    content type by design: they were trained only on face-swaps in real videos).

    Returns dict with keys:
        general_ai   float  — avg of 4 general AI detectors
        deepfake     float  — avg of 2 face-swap-specific detectors
        temporal     float  — temporal coherence signal
        heuristics   float  — avg of 5 heuristic signals
        fft          float  — FFT frequency signal (standalone)
        noise        float  — noise artifact signal (standalone)
        mode         str    — routing decision label
        disagreement float  — general_ai − deepfake gap (face content only)
    """
    # ── Raw normalized scores ────────────────────────────────────────────────
    s_deepfake  = _n(signals.get("deepfake_model_score"))
    s_sdxl      = _n(signals.get("sdxl_score"))
    s_ai_det    = _n(signals.get("ai_detector_score"))
    s_ai_or_not = _n(signals.get("ai_or_not_score"))
    s_umm       = _n(signals.get("umm_maybe_score"))
    s_ff_xcept  = _n(signals.get("ff_xception_score"))
    s_face_ai   = _n(signals.get("face_ai_generated_score"))

    s_noise    = _n(signals.get("noise_signal"),    50.0)
    s_temporal = _n(signals.get("temporal_signal"), 50.0)
    s_edge     = _n(signals.get("edge_signal"),     50.0)
    s_fft      = _n(signals.get("fft_signal"),      50.0)
    s_color    = _n(signals.get("color_signal"),    50.0)

    # ── Group averages ───────────────────────────────────────────────────────
    general_ai_inputs = [s_sdxl, s_ai_det, s_ai_or_not, s_umm]
    if content_type == "face":
        general_ai_inputs.append(s_face_ai)
    general_ai_avg = _avg(general_ai_inputs)
    heuristic_avg  = _avg([s_noise, s_temporal, s_edge, s_fft, s_color])

    base = {
        "general_ai":  general_ai_avg,
        "temporal":    s_temporal,
        "heuristics":  heuristic_avg,
        "fft":         s_fft,
        "noise":       s_noise,
        "disagreement": 0.0,
        "deepfake":    50.0,
    }

    # ── Content-type routing ─────────────────────────────────────────────────
    if content_type == "face":
        deepfake_scores = [s for s in [s_deepfake, s_ff_xcept] if s is not None]
        deepfake_avg    = _avg(deepfake_scores) if deepfake_scores else None

        if deepfake_avg is not None:
            # Positive = general AI models say AI, deepfake models say Real
            disagreement = general_ai_avg - deepfake_avg

            if disagreement > 40:
                # AI-generated video containing faces (not a face-swap deepfake).
                # The deepfake-specific models are wrong for this content type:
                # they were trained on face-swaps in real video, not synthetic content.
                # → downweight them heavily; let general AI models carry the verdict.
                mode = "face_ai_generated"
            else:
                # Models broadly agree → genuine face-swap deepfake candidate
                # OR genuinely real face content. Weight both equally.
                mode = "face_deepfake"
        else:
            deepfake_avg = 50.0
            disagreement = 0.0
            mode         = "face_no_spec_model"

        return {**base,
                "deepfake":     round(deepfake_avg, 2),
                "mode":         mode,
                "disagreement": round(max(0.0, disagreement), 2)}

    elif content_type == "animal":
        # Face-swap models are entirely irrelevant for animal content.
        # FFT and noise signals are strong for AI-generated textures (fur, scales).
        return {**base, "mode": "animal"}

    else:  # general
        return {**base, "mode": "general"}


# ══════════════════════════════════════════════════════════════════════════════
# 4. WEIGHTED SCORING SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

# Weight table — one entry per routing mode, all rows sum to 1.0
#
# Justification per mode:
#   face_ai_generated : general AI detectors are correct (65%); deepfake models
#                       are noise for this content type (5%); temporal artifacts
#                       reveal AI motion patterns (15%); heuristics support (15%)
#   face_deepfake     : both model families equally relevant (35%+35%); temporal
#                       is critical for video deepfake detection (15%); heuristics
#                       provide forensic backup (15%)
#   face_no_spec_model: no deepfake model available; general AI carries more
#                       weight (55%); temporal + heuristics fill the gap
#   animal            : face/deepfake models irrelevant (0%); general AI (55%);
#                       heuristics strong for texture analysis (30%); FFT for
#                       frequency artifacts in synthetic fur/scales (15%)
#   general           : general AI detectors primary (55%); heuristics (30%);
#                       temporal for video consistency (15%)

_WEIGHTS = {
    "face_ai_generated": {
        "general_ai": 0.65,
        "deepfake":   0.05,
        "temporal":   0.15,
        "heuristics": 0.15,
    },
    "face_deepfake": {
        "general_ai": 0.35,
        "deepfake":   0.35,
        "temporal":   0.15,
        "heuristics": 0.15,
    },
    "face_no_spec_model": {
        "general_ai": 0.55,
        "deepfake":   0.00,
        "temporal":   0.20,
        "heuristics": 0.25,
    },
    "animal": {
        "general_ai": 0.55,
        "deepfake":   0.00,
        "temporal":   0.15,
        "heuristics": 0.30,
    },
    "general": {
        "general_ai": 0.55,
        "deepfake":   0.00,
        "temporal":   0.15,
        "heuristics": 0.30,
    },
}


def compute_content_score(module_scores, tampering_result):
    """
    Apply content-type-specific weights to produce:
        combined_ai_signal  0-100, high = AI-generated
        fas                 0-100, high = Real (= 100 - combined_ai)
        num_flags           count of tampering boolean flags (0-3)

    FAS formula:
        combined_ai = Σ (module_score × weight)   [from _WEIGHTS table]
        FAS         = 100 − combined_ai

    Tampering is NOT mixed into FAS. It is a separate forensic signal that
    gets its own confidence bar (0 flags = 0%, 3 flags = 90%). Keeping it
    separate avoids inflating or deflating the AI authenticity score with
    an unrelated dimension.
    """
    mode    = module_scores.get("mode", "general")
    weights = _WEIGHTS.get(mode, _WEIGHTS["general"])

    combined_ai = (
        module_scores.get("general_ai", 50.0) * weights["general_ai"] +
        module_scores.get("deepfake",   50.0) * weights["deepfake"]   +
        module_scores.get("temporal",   50.0) * weights["temporal"]   +
        module_scores.get("heuristics", 50.0) * weights["heuristics"]
    )
    combined_ai = round(min(100.0, max(0.0, combined_ai)), 2)
    fas         = round(100.0 - combined_ai, 2)

    dup     = int(bool(tampering_result.get("frame_duplication",     False)))
    removal = int(bool(tampering_result.get("frame_removal",         False)))
    t_inc   = int(bool(tampering_result.get("temporal_inconsistency", False)))
    num_flags = dup + removal + t_inc

    return combined_ai, fas, num_flags


# ══════════════════════════════════════════════════════════════════════════════
# 5. VERDICT + EXPLAINABILITY
# ══════════════════════════════════════════════════════════════════════════════

def _verdict(fas):
    """
    Map FAS to a human-readable verdict.

        80-100  Real
        55-79   Likely Real
        45-54   Inconclusive
        25-44   Likely AI-Generated
         0-24   AI-Generated

    The older 40-59 inconclusive band hid useful majority signals. For
    forensic review, only a narrow 45-55 area should be inconclusive; scores
    outside that range should become actionable "likely" verdicts.
    """
    if   fas >= 80: return "Real"
    elif fas >= 55: return "Likely Real"
    elif fas >= 45: return "Inconclusive"
    elif fas >= 25: return "Likely AI-Generated"
    else:           return "AI-Generated"


def _top_signals(module_scores, num_flags):
    """
    Return the top 3 most decisive forensic signals as human-readable strings.
    Influence = |score − 50|: the further from neutral, the more decisive.
    """
    candidates = [
        ("General AI model consensus", module_scores.get("general_ai", 50.0)),
        ("Temporal coherence",         module_scores.get("temporal",   50.0)),
        ("Heuristic forensics",        module_scores.get("heuristics", 50.0)),
        ("FFT frequency spectrum",     module_scores.get("fft",        50.0)),
        ("Noise artifact analysis",    module_scores.get("noise",      50.0)),
    ]
    if module_scores.get("mode") in ("face_deepfake", "face_ai_generated"):
        candidates.append(("Deepfake face model", module_scores.get("deepfake", 50.0)))

    scored = [
        (name, abs(val - 50.0), "AI" if val > 50 else "Real")
        for name, val in candidates
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    result = [
        f"{name}: {inf:.1f}% signal strength — {direction} indicator"
        for name, inf, direction in scored[:3]
    ]
    if num_flags > 0:
        result.append(f"Tampering: {num_flags} flag(s) detected")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# 6. MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def compute_unified_result(ai_result, tampering_result, face_result, caption=""):
    """
    Single source of truth. All section values derive from this function.

    Input:
        ai_result       — dict from AIDetectionService.detect()
        tampering_result— dict from TamperingService.detect()
        face_result     — dict with faces_detected, total_faces, confidence
        caption         — str, primary video caption (used for content classification)

    Output:
        (forensic_summary, ai_result_unified, tampering_result_unified, face_result_unified)

    Example output for a 4/6 AI-model-consensus face video:
        forensic_authenticity_score : 31.5   (Likely AI-Generated)
        combined_ai_signal          : 68.5
        content_type                : face
        routing_mode                : face_ai_generated
        general_ai_avg              : 90.9   (sdxl=97, ai_det=92, ai_or_not=93.5, umm=81)
        deepfake_model_avg          : 8.7    (deepfake=5.4, ff_xception=12) ← noise, ignored
        model_disagreement          : 82.2   → triggers face_ai_generated mode
        ai_detection.confidence     : 31.5   (same as FAS — shown in bar + text)
        tampering.confidence        : 30.0   (1 flag detected)
        face_detection.confidence   : 61.5   (derived from face density)
    """
    signals = ai_result.get("signals", {})

    # ── Step 1: Classify content ─────────────────────────────────────────────
    content_type = classify_content(signals, face_result, caption)

    # ── Step 2: Route to relevant modules ────────────────────────────────────
    module_scores = route_modules(content_type, signals)

    # ── Step 3: Compute weighted score ───────────────────────────────────────
    combined_ai, fas, num_flags = compute_content_score(module_scores, tampering_result)

    # ── Step 4: Derive all section confidences ───────────────────────────────
    verdict = _verdict(fas)

    # AI Detection confidence = AI generation likelihood.
    # FAS remains available separately as forensic_authenticity_score.
    ai_confidence = combined_ai

    # Tampering evidence strength (purely from boolean flags, no base value)
    #   0 flags → 0%   (no forensic evidence of tampering)
    #   1 flag  → 30%
    #   2 flags → 60%
    #   3 flags → 90%
    tampering_confidence = round(float(num_flags * 30), 2)

    # Face detection confidence derived from face presence across analyzed frames
    faces_in_frames = int(signals.get("faces_detected_in_frames") or 0)
    frames_analyzed = int(signals.get("frames_analyzed") or 1)
    face_density    = faces_in_frames / max(1, frames_analyzed)
    faces_detected  = bool(face_result.get("faces_detected", False))
    if faces_detected:
        face_confidence = round(min(95.0, 55.0 + face_density * 40.0), 2)
    else:
        face_confidence = round(max(70.0, 90.0 - face_density * 50.0), 2)

    # Risk badge score: AI signal + tampering additive penalty (0 = safe, 100 = high risk)
    risk_score = round(min(100.0, combined_ai + num_flags * 8.0), 2)

    # Top contributing signals for the "Why This Verdict?" panel
    top_signals = _top_signals(module_scores, num_flags)

    # ── Step 5: Inject computed intermediates into signals block ─────────────
    # These appear first in Forensic Breakdown so the formula is fully visible.
    signals_unified = {
        "forensic_authenticity_score": fas,
        "ai_generation_likelihood":    combined_ai,
        "combined_ai_signal":          combined_ai,
        "content_type":                content_type,
        "routing_mode":                module_scores["mode"],
        "general_ai_avg":              module_scores["general_ai"],
        "deepfake_model_avg":          module_scores.get("deepfake", 0.0),
        "model_disagreement":          module_scores.get("disagreement", 0.0),
        "heuristic_avg":               module_scores["heuristics"],
    }
    signals_unified.update(signals)  # append all raw model signals below

    reasons = dict(ai_result.get("reasons", {}))
    reasons["verdict"] = verdict
    reasons["top_factors"] = top_signals
    reasons["summary"] = (
        f"Unified forensic calibration estimates {combined_ai:.2f}% AI-generation likelihood "
        f"and {fas:.2f}% authenticity. Final verdict: {verdict}. "
        f"Routing mode: {module_scores['mode']}."
    )
    reasons["model_agreement"] = (
        f"Unified score uses {module_scores['mode']} routing with general AI average "
        f"{module_scores['general_ai']:.2f}%, deepfake-model average "
        f"{module_scores.get('deepfake', 0.0):.2f}%, heuristic average "
        f"{module_scores['heuristics']:.2f}%, and temporal signal "
        f"{module_scores['temporal']:.2f}%."
    )
    if verdict in ("Likely AI-Generated", "AI-Generated"):
        reasons.setdefault("ai_indicators", [])
        reasons["ai_indicators"] = [
            f"Unified calibrated AI-generation likelihood is {combined_ai:.2f}%.",
            *reasons["ai_indicators"],
        ]
    elif verdict in ("Likely Real", "Real"):
        reasons.setdefault("real_indicators", [])
        reasons["real_indicators"] = [
            f"Unified calibrated authenticity score is {fas:.2f}%.",
            *reasons["real_indicators"],
        ]

    # ── Step 6: Assemble unified outputs ─────────────────────────────────────
    ai_result_unified = {
        **ai_result,
        "status":     verdict,
        "confidence": ai_confidence,   # drives Core Findings text AND bar
        "signals":    signals_unified,
        "reasons":    reasons,
    }
    tampering_result_unified = {
        **tampering_result,
        "confidence": tampering_confidence,  # drives Tampering text AND bar
    }
    face_result_unified = {
        **face_result,
        "confidence": face_confidence,       # drives Face Detection bar
    }

    forensic_summary = {
        "forensic_authenticity_score": fas,
        "ai_generation_likelihood":    combined_ai,
        "combined_ai_signal":          combined_ai,
        "forensic_verdict":            verdict,
        "content_type":                content_type,
        "routing_mode":                module_scores["mode"],
        "general_ai_avg":              module_scores["general_ai"],
        "deepfake_model_avg":          module_scores.get("deepfake", 0.0),
        "model_disagreement":          module_scores.get("disagreement", 0.0),
        "risk_score":                  risk_score,
        "top_contributing_signals":    top_signals,
    }

    return forensic_summary, ai_result_unified, tampering_result_unified, face_result_unified
