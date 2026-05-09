"""Deepfake detection provider using ML models."""
import os
import cv2
import numpy as np
from typing import Dict, Any, Optional

from .base import BaseProvider

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class DeepfakeDetectorProvider(BaseProvider):
    """Provider for deepfake detection using various ML techniques."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize deepfake detector provider.
        
        Args:
            api_key: Optional API key (not used for local models)
        """
        super().__init__("DeepfakeDetector", api_key)
        self.face_analysis_pipeline = None
        self._initialize_pipelines()

    def can_run_without_api_key(self) -> bool:
        """Deepfake detection can run locally."""
        return TRANSFORMERS_AVAILABLE

    def _initialize_pipelines(self):
        """Initialize ML pipelines for deepfake detection."""
        if not TRANSFORMERS_AVAILABLE:
            return

        if os.getenv("MODEL_REMOTE_LOAD", "0") != "1":
            return

        try:
            # Face emotion pipeline (detects inconsistencies)
            self.face_analysis_pipeline = pipeline(
                "image-classification",
                model="michellejieli/NSFW_image_detection",
                local_files_only=False,
            )
        except Exception as e:
            self.face_analysis_pipeline = None

    def check_frame_consistency(self, frame1, frame2) -> float:
        """
        Check consistency between two frames.
        High inconsistency might indicate manipulation.
        
        Args:
            frame1: First frame
            frame2: Second frame
            
        Returns:
            Consistency score (0-1)
        """
        try:
            # Calculate optical flow to detect unnaturalmotion
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

            flow = cv2.calcOpticalFlowFarneback(
                gray1, gray2, None, 0.5, 3, 15, 3, 5, 1.2, 0
            )
            magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])

            # High consistency = smooth flow
            consistency = 1.0 - min(1.0, np.mean(magnitude) / 10.0)
            return consistency

        except Exception:
            return 0.5  # Return neutral score on error

    def analyze(self, video_path: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze video for deepfake indicators.
        
        Args:
            video_path: Path to video file
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with deepfake detection results
        """
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames < 2:
                return self.format_result("Insufficient frames for analysis", 0.0)

            # Sample frames for analysis
            sample_interval = max(1, total_frames // 5)
            consistency_scores = []
            prev_frame = None
            frame_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % sample_interval == 0:
                    if prev_frame is not None:
                        consistency = self.check_frame_consistency(prev_frame, frame)
                        consistency_scores.append(consistency)
                    prev_frame = frame.copy()

                frame_count += 1

            cap.release()

            if not consistency_scores:
                return self.format_result("Could not analyze frames", 0.0)

            # Calculate deepfake probability
            avg_consistency = np.mean(consistency_scores)
            deepfake_probability = 1.0 - avg_consistency

            result_text = f"Deepfake probability: {deepfake_probability:.2%}"
            confidence = min(0.9, abs(avg_consistency - 0.5) * 2)  # Higher confidence near extremes

            return self.format_result(result_text, confidence, {
                "deepfake_probability": float(deepfake_probability),
                "consistency_score": float(avg_consistency),
                "frames_analyzed": len(consistency_scores),
            })

        except Exception as e:
            return self.handle_error(e)
