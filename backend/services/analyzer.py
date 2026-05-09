import traceback
from backend.services.preprocessing import PreprocessingService
from backend.services.captioning import CaptionService
from backend.services.ai_detection import AIDetectionService
from backend.services.tampering import TamperingService
from backend.services.face_privacy import FacePrivacyService
from backend.services.event_timeline import EventTimelineService
from backend.services.forensic_unifier import compute_unified_result


class VideoAnalyzer:
    def __init__(self, logger):
        self.logger = logger
        self.preprocessing = PreprocessingService()
        self.captioner = CaptionService()
        self.ai_detector = AIDetectionService()
        self.tampering = TamperingService()
        self.face_privacy = FacePrivacyService()
        self.timeline = EventTimelineService()

    def analyze(self, video_path, video_id):
        try:
            frames, meta = self.preprocessing.extract_frames(video_path)
            caption = self.captioner.generate_caption(frames)
            ai_result = self.ai_detector.detect(frames, video_path=video_path)
            tampering = self.tampering.detect(frames)
            face = self.face_privacy.detect_and_blur(frames, video_id, video_path=video_path, meta=meta)
            shot_events = self.timeline.build_timeline(frames, meta, self.captioner)

            face_data = {
                "faces_detected": face["faces_detected"],
                "alert":          face["alert"],
                "confidence":     face["confidence"],
                "total_faces":    face.get("total_faces", 0),
            }

            caption_text = caption.get("caption", "") if isinstance(caption, dict) else ""
            forensic, ai_result, tampering, face_data = compute_unified_result(
                ai_result, tampering, face_data, caption_text
            )

            return {
                "metadata":        meta,
                "caption":         caption,
                "ai_detection":    ai_result,
                "tampering":       tampering,
                "face_detection":  face_data,
                "forensic":        forensic,
                "shot_events":     shot_events,
                "preview_path":    face["preview_path"],
                "face_frames":     face.get("face_frames", []),
            }
        except Exception as exc:  # pragma: no cover
            self.logger.log("analysis_failed", details={"error": str(exc), "trace": traceback.format_exc()})
            return {
                "metadata": {"fps": 0.0, "duration": 0.0, "frame_count": 0, "sample_rate": 1, "sampled_indices": []},
                "caption": {"caption": "Analysis failed.", "confidence": 0.0},
                "ai_detection": {"status": "Real", "confidence": 0.0, "signals": {}},
                "tampering": {
                    "tampering_type": "Analysis failed",
                    "frame_duplication": False,
                    "frame_removal": False,
                    "temporal_inconsistency": False,
                    "confidence": 0.0,
                    "details": {},
                },
                "face_detection": {"faces_detected": False, "alert": "Analysis failed.", "confidence": 0.0, "total_faces": 0},
                "forensic": {
                    "forensic_authenticity_score": 0.0,
                    "forensic_verdict": "Analysis failed",
                    "risk_score": 0.0,
                    "top_contributing_signals": [],
                },
                "shot_events":   [],
                "preview_path":  None,
                "face_frames":   [],
            }
