"""Multi-provider video analyzer with aggregation."""
import logging
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from .aggregator import ResultAggregator
from .providers import (
    HuggingFaceProvider,
    OpenCVFaceDetectionProvider,
    DeepfakeDetectorProvider,
)


logger = logging.getLogger(__name__)


class MultiProviderAnalyzer:
    """Orchestrates analysis across multiple providers with error handling and fallbacks."""

    def __init__(self, timeout: int = 300):
        """
        Initialize multi-provider analyzer.
        
        Args:
            timeout: Timeout in seconds for each provider analysis
        """
        self.timeout = timeout
        self.providers = self._initialize_providers()
        self.aggregator = None

    def _initialize_providers(self) -> Dict[str, Any]:
        """
        Initialize all available providers.
        
        Returns:
            Dictionary of provider instances
        """
        providers = {}

        try:
            providers["HuggingFace"] = HuggingFaceProvider(
                api_key=os.getenv("HUGGINGFACE_API_KEY")
            )
            logger.info("HuggingFace provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize HuggingFace provider: {e}")

        try:
            providers["OpenCV"] = OpenCVFaceDetectionProvider()
            logger.info("OpenCV face detection provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenCV provider: {e}")

        try:
            providers["Deepfake"] = DeepfakeDetectorProvider(
                api_key=os.getenv("DEEPFAKE_API_KEY")
            )
            logger.info("Deepfake detector provider initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Deepfake detector provider: {e}")

        if not providers:
            logger.error("No providers could be initialized!")

        return providers

    def analyze_with_provider(
        self,
        provider_name: str,
        video_path: str
    ) -> tuple[str, Optional[Dict[str, Any]], Optional[str]]:
        """
        Analyze video with a specific provider.
        
        Args:
            provider_name: Name of the provider
            video_path: Path to video file
            
        Returns:
            Tuple of (provider_name, result, error_message)
        """
        try:
            provider = self.providers.get(provider_name)
            if not provider:
                return provider_name, None, f"Provider {provider_name} not available"

            if not provider.is_available:
                return provider_name, None, f"Provider {provider_name} is not available"

            logger.info(f"Starting analysis with {provider_name}")
            result = provider.analyze(video_path)
            logger.info(f"Completed analysis with {provider_name}")

            return provider_name, result, None

        except Exception as e:
            error_msg = f"Error in {provider_name} analysis: {str(e)}"
            logger.error(error_msg)
            return provider_name, None, error_msg

    def analyze(self, video_path: str, video_id: str, video_url: str) -> Dict[str, Any]:
        """
        Analyze video using all available providers.
        
        Args:
            video_path: Path to video file
            video_id: Unique video identifier
            video_url: Public URL of the video
            
        Returns:
            Aggregated analysis results
        """
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return {
                "error": "Video file not found",
                "video_id": video_id,
            }

        logger.info(f"Starting multi-provider analysis for video {video_id}")

        # Create aggregator for this analysis
        self.aggregator = ResultAggregator()

        # Run all providers concurrently
        with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
            futures = {
                executor.submit(self.analyze_with_provider, name, video_path): name
                for name in self.providers.keys()
            }

            for future in as_completed(futures, timeout=self.timeout):
                provider_name, result, error = future.result()

                if error:
                    logger.warning(f"Provider {provider_name} failed: {error}")
                    self.aggregator.add_provider_result(provider_name, {}, error)
                else:
                    self.aggregator.add_provider_result(provider_name, result)

        # Aggregate all results
        aggregated = self.aggregator.aggregate(video_url, video_id)
        logger.info(f"Analysis complete for video {video_id}: "
                   f"{aggregated['successful_analyses']}/{aggregated['provider_count']} providers successful")

        return aggregated

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all providers.
        
        Returns:
            Dictionary with provider status information
        """
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                "available": provider.is_available,
                "name": provider.name,
                "type": provider.__class__.__name__,
            }

        return status
