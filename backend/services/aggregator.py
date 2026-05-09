"""Aggregation layer for combining multi-provider analysis results."""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class ResultAggregator:
    """Aggregates video analysis results from multiple providers."""

    def __init__(self):
        """Initialize the aggregator."""
        self.providers_results = {}
        self.aggregated_result = None

    def add_provider_result(
        self,
        provider_name: str,
        result: Dict[str, Any],
        error: Optional[str] = None
    ) -> None:
        """
        Add result from a provider.
        
        Args:
            provider_name: Name of the provider
            result: Analysis result from provider
            error: Optional error message if analysis failed
        """
        self.providers_results[provider_name] = {
            "result": result,
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def calculate_confidence_aggregate(self) -> float:
        """
        Calculate aggregate confidence from all providers.
        
        Returns:
            Average confidence score (0-1)
        """
        confidences = []
        
        for provider_data in self.providers_results.values():
            if provider_data["error"]:
                continue
                
            result = provider_data["result"]
            if isinstance(result, dict) and "confidence" in result:
                confidences.append(result["confidence"])

        if not confidences:
            return 0.0

        return sum(confidences) / len(confidences)

    def detect_anomalies(self) -> List[str]:
        """
        Detect anomalies or inconsistencies in provider results.
        
        Returns:
            List of anomaly descriptions
        """
        anomalies = []
        results_with_confidence = []

        for provider_name, provider_data in self.providers_results.items():
            if provider_data["error"]:
                anomalies.append(f"{provider_name}: Analysis failed - {provider_data['error']}")
                continue

            result = provider_data["result"]
            if isinstance(result, dict) and "confidence" in result:
                results_with_confidence.append({
                    "provider": provider_name,
                    "confidence": result["confidence"],
                    "result": result.get("result", ""),
                })

        # Check for conflicting results
        if len(results_with_confidence) >= 2:
            confidences = [r["confidence"] for r in results_with_confidence]
            max_conf = max(confidences)
            min_conf = min(confidences)

            if max_conf - min_conf > 0.3:
                high_confidence_providers = [
                    r["provider"] for r in results_with_confidence if r["confidence"] > 0.7
                ]
                low_confidence_providers = [
                    r["provider"] for r in results_with_confidence if r["confidence"] < 0.5
                ]

                if high_confidence_providers and low_confidence_providers:
                    anomalies.append(
                        f"Confidence divergence: {high_confidence_providers} have high confidence, "
                        f"while {low_confidence_providers} have low confidence"
                    )

        return anomalies

    def aggregate(self, video_url: str, video_id: str) -> Dict[str, Any]:
        """
        Aggregate all provider results into a unified response.
        
        Args:
            video_url: URL or path to the video
            video_id: Unique identifier for the video
            
        Returns:
            Aggregated analysis result
        """
        providers_list = []
        errors = []

        for provider_name, provider_data in self.providers_results.items():
            if provider_data["error"]:
                errors.append({
                    "provider": provider_name,
                    "error": provider_data["error"],
                    "timestamp": provider_data["timestamp"],
                })
            else:
                result = provider_data["result"]
                if isinstance(result, dict):
                    providers_list.append({
                        "name": provider_name,
                        **result,
                        "timestamp": provider_data["timestamp"],
                    })
                else:
                    providers_list.append({
                        "name": provider_name,
                        "result": result,
                        "confidence": 0.0,
                        "timestamp": provider_data["timestamp"],
                    })

        anomalies = self.detect_anomalies()
        aggregate_confidence = self.calculate_confidence_aggregate()

        self.aggregated_result = {
            "video_id": video_id,
            "video_url": video_url,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_confidence": aggregate_confidence,
            "providers": providers_list,
            "errors": errors,
            "anomalies": anomalies,
            "provider_count": len(self.providers_results),
            "successful_analyses": len(providers_list),
            "failed_analyses": len(errors),
        }

        return self.aggregated_result

    def to_json(self) -> str:
        """
        Convert aggregated result to JSON string.
        
        Returns:
            JSON string representation
        """
        if self.aggregated_result is None:
            return json.dumps({})

        return json.dumps(self.aggregated_result, indent=2, default=str)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the aggregated results.
        
        Returns:
            Summary dictionary
        """
        if self.aggregated_result is None:
            return {}

        return {
            "video_id": self.aggregated_result.get("video_id"),
            "overall_confidence": self.aggregated_result.get("overall_confidence"),
            "provider_count": self.aggregated_result.get("provider_count"),
            "successful_analyses": self.aggregated_result.get("successful_analyses"),
            "failed_analyses": self.aggregated_result.get("failed_analyses"),
            "anomalies": self.aggregated_result.get("anomalies", []),
        }
