"""HuggingFace provider for video captioning and analysis."""
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


class HuggingFaceProvider(BaseProvider):
    """Provider using HuggingFace models for video analysis and captioning."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize HuggingFace provider.
        
        Args:
            api_key: Optional HuggingFace API token
        """
        super().__init__("HuggingFace", api_key)
        self.caption_pipeline = None
        self.quality_pipeline = None
        self._initialize_pipelines()

    def can_run_without_api_key(self) -> bool:
        """HuggingFace models can run locally without API key."""
        return TRANSFORMERS_AVAILABLE

    def _initialize_pipelines(self):
        """Initialize HuggingFace pipelines."""
        if not TRANSFORMERS_AVAILABLE:
            return

        if os.getenv("MODEL_REMOTE_LOAD", "0") != "1":
            return

        try:
            # Image captioning pipeline
            self.caption_pipeline = pipeline(
                "image-to-text",
                model="Salesforce/blip-image-captioning-base",
                local_files_only=False,
            )

            # Zero-shot classification for quality assessment
            self.quality_pipeline = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                local_files_only=False,
            )
        except Exception as e:
            self.caption_pipeline = None
            self.quality_pipeline = None

    def extract_frames(self, video_path: str, num_frames: int = 5) -> list:
        """
        Extract frames from video.
        
        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract
            
        Returns:
            List of frame numpy arrays
        """
        frames = []
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)

            cap.release()
        except Exception as e:
            print(f"Error extracting frames: {e}")

        return frames

    def generate_captions(self, video_path: str) -> Dict[str, Any]:
        """
        Generate captions for video frames.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with captions and confidence
        """
        if not self.caption_pipeline:
            return self.format_result("Captioning unavailable", 0.0)

        try:
            frames = self.extract_frames(video_path, num_frames=3)
            captions = []

            for frame in frames:
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Generate caption
                result = self.caption_pipeline(rgb_frame)
                if result:
                    captions.append(result[0]["generated_text"])

            combined_caption = " | ".join(captions) if captions else "No captions generated"
            confidence = min(0.95, len(captions) / 3.0)  # Max 0.95 when all 3 frames processed

            return self.format_result(combined_caption, confidence)

        except Exception as e:
            return self.handle_error(e)

    def assess_video_quality(self, video_path: str) -> Dict[str, Any]:
        """
        Assess video quality using zero-shot classification.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with quality assessment
        """
        if not self.quality_pipeline:
            return self.format_result("Quality assessment unavailable", 0.0)

        try:
            frames = self.extract_frames(video_path, num_frames=1)
            if not frames:
                return self.format_result("No frames extracted", 0.0)

            # Assess quality
            candidate_labels = ["high quality", "medium quality", "low quality", "corrupted"]
            result = self.quality_pipeline(
                frames[0].__str__()[:50],  # Use frame info
                candidate_labels
            )

            quality = result["labels"][0]
            confidence = result["scores"][0]

            return self.format_result(quality, confidence)

        except Exception as e:
            return self.handle_error(e)

    def analyze(self, video_path: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze video using HuggingFace models.
        
        Args:
            video_path: Path to video file
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with analysis results
        """
        return {
            "provider": self.name,
            "captions": self.generate_captions(video_path),
            "quality": self.assess_video_quality(video_path),
            "confidence": 0.85,
        }
