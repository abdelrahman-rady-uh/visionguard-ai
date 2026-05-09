"""Base provider class for all video analysis service providers."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseProvider(ABC):
    """Abstract base class for all provider integrations."""

    def __init__(self, name: str, api_key: Optional[str] = None):
        """
        Initialize provider.
        
        Args:
            name: Provider name (e.g., 'HuggingFace', 'OpenCV')
            api_key: Optional API key from environment
        """
        self.name = name
        self.api_key = api_key
        self.is_available = api_key is not None or self.can_run_without_api_key()

    @abstractmethod
    def can_run_without_api_key(self) -> bool:
        """Check if provider can run without API key."""
        pass

    @abstractmethod
    def analyze(self, video_path: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze video using this provider.
        
        Args:
            video_path: Path to video file
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with 'result' and 'confidence' fields
        """
        pass

    def format_result(
        self,
        result: Any,
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format result in standard format.
        
        Args:
            result: Raw analysis result
            confidence: Confidence score (0-1)
            metadata: Optional metadata
            
        Returns:
            Standardized result dictionary
        """
        return {
            "provider": self.name,
            "result": result,
            "confidence": min(1.0, max(0.0, confidence)),
            "metadata": metadata or {},
            "available": self.is_available,
        }

    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """
        Handle provider errors gracefully.
        
        Args:
            error: The error that occurred
            
        Returns:
            Fallback result dictionary
        """
        return {
            "provider": self.name,
            "result": "ERROR",
            "confidence": 0.0,
            "error": str(error),
            "available": False,
        }
