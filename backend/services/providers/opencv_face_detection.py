"""OpenCV provider for face detection."""
import cv2
import os
from typing import Dict, Any

from .base import BaseProvider


class OpenCVFaceDetectionProvider(BaseProvider):
    """Provider using OpenCV for face detection."""

    def __init__(self, api_key: Any = None):
        """
        Initialize OpenCV face detection provider.
        
        Args:
            api_key: Not needed for OpenCV (ignored)
        """
        super().__init__("OpenCV-FaceDetection", None)
        self.cascade_path = self._find_cascade_classifier()

    def can_run_without_api_key(self) -> bool:
        """OpenCV can run without API key."""
        return True

    def _find_cascade_classifier(self) -> str:
        """Find OpenCV cascade classifier file."""
        # Common locations for cascade classifiers
        possible_paths = [
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml",
            "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
            "C:\\opencv\\sources\\data\\haarcascades\\haarcascade_frontalface_default.xml",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # Return default even if not found (OpenCV will handle it)
        return cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

    def detect_faces_in_frame(self, frame):
        """
        Detect faces in a single frame.
        
        Args:
            frame: OpenCV frame
            
        Returns:
            Number of faces detected
        """
        try:
            face_cascade = cv2.CascadeClassifier(self.cascade_path)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            return len(faces)
        except Exception:
            return 0

    def analyze(self, video_path: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze video for faces using OpenCV.
        
        Args:
            video_path: Path to video file
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with face detection results
        """
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frames_with_faces = 0
            max_faces_in_frame = 0
            sample_interval = max(1, total_frames // 10)  # Sample 10 frames

            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % sample_interval == 0:
                    num_faces = self.detect_faces_in_frame(frame)
                    if num_faces > 0:
                        frames_with_faces += 1
                    max_faces_in_frame = max(max_faces_in_frame, num_faces)

                frame_count += 1

            cap.release()

            # Calculate confidence
            face_detection_rate = frames_with_faces / max(1, total_frames // sample_interval)
            confidence = min(0.99, face_detection_rate * 1.2)

            result_text = f"Faces detected in {frames_with_faces} sampled frames, max {max_faces_in_frame} in single frame"

            return self.format_result(result_text, confidence, {
                "frames_with_faces": frames_with_faces,
                "max_faces_in_frame": max_faces_in_frame,
                "total_frames_analyzed": total_frames,
            })

        except Exception as e:
            return self.handle_error(e)
