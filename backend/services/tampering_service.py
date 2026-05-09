"""
Tampering Detection Service - Video integrity and manipulation detection
Uses optical flow and frame consistency analysis
"""
import cv2
import logging
from typing import Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class TamperingService:
    """Detect potential video tampering and manipulations"""
    
    def __init__(self):
        """Initialize tampering detection"""
        self.available = True
    
    def detect_tampering(
        self,
        video_path: str,
        sample_rate: int = 15
    ) -> Dict[str, Any]:
        """
        Detect potential tampering in video using optical flow analysis
        
        Args:
            video_path: Path to video file
            sample_rate: Frame sampling rate
        
        Returns:
            Tampering detection results with confidence scores
        """
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            tampering_indicators = []
            prev_gray = None
            frame_count = 0
            analyzed_frames = 0
            
            while cap.isOpened() and analyzed_frames < 30:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_count % sample_rate == 0:
                    try:
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        
                        if prev_gray is not None:
                            # Calculate optical flow
                            flow = cv2.calcOpticalFlowFarneback(
                                prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
                            )
                            
                            # Calculate motion consistency
                            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                            motion_score = np.mean(mag)
                            
                            # Detect sudden motion changes (potential tampering)
                            tampering_risk = self._assess_tampering_risk(flow, motion_score)
                            
                            timestamp_sec = frame_count / fps
                            time_str = self._format_timestamp(timestamp_sec)
                            
                            if tampering_risk["risk_level"] > 0.3:  # Above threshold
                                tampering_indicators.append({
                                    "timestamp": time_str,
                                    "timestamp_seconds": timestamp_sec,
                                    "frame_number": frame_count,
                                    "risk_level": round(tampering_risk["risk_level"], 3),
                                    "risk_type": tampering_risk["type"],
                                    "motion_score": round(motion_score, 3),
                                    "details": tampering_risk["details"]
                                })
                        
                        prev_gray = gray
                        analyzed_frames += 1
                    
                    except Exception as e:
                        logger.error(f"Error analyzing tampering in frame {frame_count}: {e}")
                
                frame_count += 1
            
            cap.release()
            
            # Calculate overall tampering probability
            overall_risk = np.mean([t["risk_level"] for t in tampering_indicators]) if tampering_indicators else 0
            
            return {
                "status": "success",
                "tampering_detected": len(tampering_indicators) > 0,
                "overall_risk": round(overall_risk, 3),
                "risk_level": "HIGH" if overall_risk > 0.7 else "MEDIUM" if overall_risk > 0.4 else "LOW",
                "indicators": tampering_indicators,
                "total_suspicious_frames": len(tampering_indicators),
                "total_frames_analyzed": analyzed_frames,
                "integrity_score": round(1 - overall_risk, 3)
            }
        
        except Exception as e:
            logger.error(f"Error in tampering detection: {e}")
            return {
                "status": "error",
                "error": str(e),
                "indicators": []
            }
    
    @staticmethod
    def _assess_tampering_risk(flow: np.ndarray, motion_score: float) -> Dict[str, Any]:
        """Assess tampering risk based on optical flow"""
        
        # Analyze flow magnitude and angle consistency
        mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        
        # Calculate standard deviation (inconsistency indicator)
        flow_std = np.std(mag)
        
        # Risk calculation
        risk_level = 0.0
        risk_type = "none"
        details = []
        
        # High motion inconsistency
        if flow_std > 10:
            risk_level += 0.3
            risk_type = "high_motion_inconsistency"
            details.append("Sudden or inconsistent motion detected")
        
        # Sudden motion changes
        if motion_score > 50:
            risk_level += 0.2
            details.append("Abnormal motion magnitude")
        
        # Localized motion anomalies
        extreme_motion = np.sum(mag > np.percentile(mag, 95))
        if extreme_motion > (mag.size * 0.15):
            risk_level += 0.2
            details.append("Localized motion anomalies detected")
        
        risk_level = min(risk_level, 1.0)  # Cap at 1.0
        
        return {
            "risk_level": risk_level,
            "type": risk_type,
            "details": details
        }
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds to MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
