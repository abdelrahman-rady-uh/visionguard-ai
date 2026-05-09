#!/usr/bin/env python3
"""
AI Detection Calibration System
Learns from real video test results to improve accuracy
"""

import sys
sys.path.insert(0, '.')
import json
import os
from pathlib import Path

class DetectionCalibrator:
    """Adaptive threshold calibration based on real results"""
    
    def __init__(self, calibration_file="calibration.json"):
        self.calibration_file = calibration_file
        self.calibration_data = self.load_calibration()
    
    def load_calibration(self):
        """Load existing calibration or create new"""
        if os.path.exists(self.calibration_file):
            with open(self.calibration_file) as f:
                return json.load(f)
        
        return {
            "version": "6.0",
            "tested_videos": [],
            "thresholds": {
                "frequency_manipulation": {"low": 0.3, "high": 0.7},
                "temporal_anomaly": {"low": 0.3, "high": 0.7},
                "facial_inconsistency": {"low": 0.2, "high": 0.8},
                "gan_artifacts": {"low": 0.3, "high": 0.7},
                "eye_region_manipulation": {"low": 0.2, "high": 0.7},
                "color_space_anomaly": {"low": 0.2, "high": 0.5},
                "biological_signals": {"low": 0.3, "high": 0.7},
            },
            "weights": {
                "frequency": 0.25,
                "temporal": 0.22,
                "facial": 0.20,
                "gan": 0.15,
                "eye": 0.10,
                "color": 0.05,
                "biological": 0.03,
            },
            "classification_thresholds": {
                "ai_generated_threshold": 70,
                "likely_ai_threshold": 55,
                "inconclusive_threshold": 45,
                "likely_real_threshold": 35,
            }
        }
    
    def save_calibration(self):
        """Save calibration to file"""
        with open(self.calibration_file, 'w') as f:
            json.dump(self.calibration_data, f, indent=2)
        print(f"✓ Calibration saved to {self.calibration_file}")
    
    def record_test(self, video_name, expected_class, detected_status, ai_score, signals):
        """Record a test result for calibration"""
        test_record = {
            "video_name": video_name,
            "expected_class": expected_class,  # "AI-Generated" or "Real"
            "detected_status": detected_status,
            "ai_score": ai_score,
            "signals": signals,
            "correct": self._is_correct(expected_class, detected_status),
        }
        
        self.calibration_data["tested_videos"].append(test_record)
        self.save_calibration()
        
        return test_record
    
    def _is_correct(self, expected, detected):
        """Check if detection matches expectation"""
        expected_lower = expected.lower()
        detected_lower = detected.lower()
        
        if "ai" in expected_lower and "ai" in detected_lower:
            return True
        if "real" in expected_lower and "real" in detected_lower:
            return True
        return False
    
    def get_accuracy(self):
        """Calculate current detection accuracy"""
        if not self.calibration_data["tested_videos"]:
            return None
        
        correct = sum(1 for t in self.calibration_data["tested_videos"] if t["correct"])
        total = len(self.calibration_data["tested_videos"])
        return correct / total * 100
    
    def suggest_threshold_adjustments(self):
        """Suggest new thresholds based on test results"""
        tests = self.calibration_data["tested_videos"]
        
        if len(tests) < 5:
            return "Need at least 5 test results to suggest adjustments"
        
        # Analyze which signals are most predictive
        ai_videos = [t for t in tests if "ai" in t["expected_class"].lower()]
        real_videos = [t for t in tests if "real" in t["expected_class"].lower()]
        
        suggestions = []
        
        # Find signals that best separate AI from real
        if ai_videos and real_videos:
            for signal_name in self.calibration_data["thresholds"]:
                ai_signal_values = []
                real_signal_values = []
                
                for test in ai_videos:
                    if signal_name in test["signals"]:
                        ai_signal_values.append(test["signals"][signal_name])
                
                for test in real_videos:
                    if signal_name in test["signals"]:
                        real_signal_values.append(test["signals"][signal_name])
                
                if ai_signal_values and real_signal_values:
                    ai_mean = sum(ai_signal_values) / len(ai_signal_values)
                    real_mean = sum(real_signal_values) / len(real_signal_values)
                    
                    if ai_mean > real_mean:
                        new_low = real_mean + (ai_mean - real_mean) * 0.2
                        new_high = ai_mean - (ai_mean - real_mean) * 0.2
                        suggestions.append(
                            f"Adjust {signal_name}: Low threshold {self.calibration_data['thresholds'][signal_name]['low']:.3f} → {new_low:.3f}"
                        )
        
        return suggestions
    
    def print_status(self):
        """Print calibration status"""
        print("\n" + "="*80)
        print("CALIBRATION STATUS")
        print("="*80)
        
        test_count = len(self.calibration_data["tested_videos"])
        print(f"\nTests Performed: {test_count}")
        
        accuracy = self.get_accuracy()
        if accuracy is not None:
            print(f"Current Accuracy: {accuracy:.1f}%")
        
        print("\nCurrent Thresholds:")
        for name, thresholds in self.calibration_data["classification_thresholds"].items():
            print(f"  {name}: {thresholds}")
        
        print("\nSignal Weights:")
        for signal, weight in self.calibration_data["weights"].items():
            print(f"  {signal}: {weight:.3f}")
        
        if test_count >= 5:
            print("\nSuggested Adjustments:")
            suggestions = self.suggest_threshold_adjustments()
            if isinstance(suggestions, str):
                print(f"  {suggestions}")
            else:
                for suggestion in suggestions:
                    print(f"  • {suggestion}")

def main():
    """Interactive calibration tool"""
    calibrator = DetectionCalibrator()
    
    print("\n" + "="*80)
    print("AI DETECTION CALIBRATION TOOL")
    print("="*80)
    
    calibrator.print_status()
    
    print("\n" + "="*80)
    print("MANUAL CALIBRATION")
    print("="*80)
    print("\nUsage: Record test results manually")
    print("1. Upload video and note the detected result")
    print("2. Edit this script to add test record")
    print("3. Run this script to update calibration")
    print("\nExample:")
    print("  calibrator.record_test(")
    print("    'deepfake_video.mp4',")
    print("    'AI-Generated',  # Expected class")
    print("    'Real',  # What system detected (WRONG)")
    print("    25.5,  # AI score")
    print("    {'frequency_manipulation': 0.35, ...}")
    print("  )")
    
    # Example: You can add manual test records here
    # calibrator.record_test(
    #     "test_video.mp4",
    #     "AI-Generated",
    #     "Real",
    #     28.5,
    #     {...signals...}
    # )

if __name__ == '__main__':
    main()
