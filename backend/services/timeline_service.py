"""
Timeline Service - Generate structured timeline with key frames and captions
"""
import cv2
import logging
import os
from typing import Dict, Any, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class TimelineService:
    """Generate timeline data with key frames and event descriptions"""
    
    def __init__(self, screenshots_dir: str = "results/screenshots"):
        """
        Initialize timeline service
        
        Args:
            screenshots_dir: Directory to store key frame screenshots
        """
        self.screenshots_dir = screenshots_dir
        os.makedirs(screenshots_dir, exist_ok=True)
    
    def generate_timeline(
        self,
        video_path: str,
        captions: List[Dict],
        detections: List[Dict],
        face_detections: List[Dict],
        tampering_data: Dict
    ) -> Dict[str, Any]:
        """
        Generate comprehensive timeline with all analysis data
        
        Args:
            video_path: Path to video file
            captions: Caption data
            detections: Object detection data
            face_detections: Face detection data
            tampering_data: Tampering detection results
        
        Returns:
            Timeline data structure
        """
        try:
            timeline_events = []
            
            # Extract key frames from captions
            if captions.get("status") == "success":
                for caption in captions.get("captions", []):
                    event = self._create_timeline_event(
                        timestamp=caption["timestamp"],
                        timestamp_seconds=caption["timestamp_seconds"],
                        event_type="caption",
                        description=caption["caption"],
                        frame_number=caption["frame_number"],
                        video_path=video_path,
                        confidence=caption["confidence"]
                    )
                    timeline_events.append(event)
            
            # Add detection events
            if detections and detections.get("status") == "success":
                for detection in detections.get("detections", []):
                    if detection["objects_detected"] > 0:
                        event = self._create_timeline_event(
                            timestamp=detection["timestamp"],
                            timestamp_seconds=detection["timestamp_seconds"],
                            event_type="object_detection",
                            description=f"{detection['objects_detected']} objects detected",
                            frame_number=detection["frame_number"],
                            video_path=video_path,
                            confidence=detection["confidence"],
                            metadata=detection["object_types"]
                        )
                        timeline_events.append(event)
            
            # Add face detection events
            if face_detections and face_detections.get("status") == "success":
                for face_det in face_detections.get("face_detections", []):
                    if face_det["face_count"] > 0:
                        event = self._create_timeline_event(
                            timestamp=face_det["timestamp"],
                            timestamp_seconds=face_det["timestamp_seconds"],
                            event_type="face_detected",
                            description=f"{face_det['face_count']} face(s) detected",
                            frame_number=face_det["frame_number"],
                            video_path=video_path,
                            confidence=0.95,
                            metadata={"privacy_alert": True}
                        )
                        timeline_events.append(event)
            
            # Add tampering alerts
            for indicator in tampering_data.get("indicators", []):
                if indicator["risk_level"] > 0.3:
                    event = self._create_timeline_event(
                        timestamp=indicator["timestamp"],
                        timestamp_seconds=indicator["timestamp_seconds"],
                        event_type="tampering_alert",
                        description=f"Potential tampering: {indicator['risk_type']}",
                        frame_number=indicator["frame_number"],
                        video_path=video_path,
                        confidence=indicator["risk_level"],
                        metadata={
                            "risk_level": indicator["risk_level"],
                            "details": indicator["details"]
                        }
                    )
                    timeline_events.append(event)
            
            # Sort by timestamp
            timeline_events.sort(key=lambda x: x["timestamp_seconds"])
            
            return {
                "status": "success",
                "timeline": timeline_events,
                "total_events": len(timeline_events),
                "duration_seconds": self._extract_duration(video_path),
                "generated_at": self._get_timestamp()
            }
        
        except Exception as e:
            logger.error(f"Error generating timeline: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timeline": []
            }
    
    def _create_timeline_event(
        self,
        timestamp: str,
        timestamp_seconds: float,
        event_type: str,
        description: str,
        frame_number: int,
        video_path: str,
        confidence: float,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Create individual timeline event with optional screenshot"""
        
        event = {
            "timestamp": timestamp,
            "timestamp_seconds": timestamp_seconds,
            "event_type": event_type,
            "description": description,
            "frame_number": frame_number,
            "confidence": confidence,
            "screenshot": None,
            "metadata": metadata or {}
        }
        
        # Capture screenshot
        try:
            screenshot_path = self._capture_screenshot(
                video_path, frame_number, timestamp
            )
            if screenshot_path:
                event["screenshot"] = screenshot_path
        except Exception as e:
            logger.warning(f"Failed to capture screenshot: {e}")
        
        return event
    
    def _capture_screenshot(self, video_path: str, frame_number: int, timestamp: str) -> str:
        """
        Capture screenshot from specific frame
        
        Args:
            video_path: Path to video
            frame_number: Frame index
            timestamp: Timestamp for naming
        
        Returns:
            Path to saved screenshot or None
        """
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Clean timestamp for filename
                safe_timestamp = timestamp.replace(":", "-")
                screenshot_path = os.path.join(
                    self.screenshots_dir,
                    f"frame_{safe_timestamp}.jpg"
                )
                
                cv2.imwrite(screenshot_path, frame)
                return screenshot_path
            
            return None
        
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
    
    @staticmethod
    def _extract_duration(video_path: str) -> float:
        """Extract video duration in seconds"""
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            return total_frames / fps
        except:
            return 0.0
    
    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp"""
        return datetime.now(timezone.utc).isoformat()
