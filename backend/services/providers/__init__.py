"""
Provider service adapters for multi-provider video analysis.
Each provider handles authentication, requests, and response formatting.
"""
from .base import BaseProvider
from .huggingface_service import HuggingFaceProvider
from .opencv_face_detection import OpenCVFaceDetectionProvider
from .deepfake_detector import DeepfakeDetectorProvider

__all__ = [
    "BaseProvider",
    "HuggingFaceProvider",
    "OpenCVFaceDetectionProvider",
    "DeepfakeDetectorProvider",
]
