"""
Caption Service - AI-powered video caption generation
Generates detailed, scene-aware descriptions of video content
"""
import os
import cv2
import logging
from typing import List, Dict, Any
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class CaptionService:
    """Generate detailed captions for video frames."""

    def __init__(self):
        """Initialize caption generation with optional local transformer loading."""
        self.available = False
        self._caption_mode = "fallback"
        self._attempted = False
        self._torch = None
        self._processor = None
        self._model = None

    def _initialize_model(self):
        if self._attempted:
            return
        self._attempted = True

        local_only = os.getenv("CAPTION_REMOTE_LOAD", "0") != "1"

        try:
            import torch
            from transformers import BlipProcessor, BlipForConditionalGeneration

            model_id = "Salesforce/blip-image-captioning-base"
            self._processor = BlipProcessor.from_pretrained(model_id, local_files_only=local_only)
            self._model = BlipForConditionalGeneration.from_pretrained(model_id, local_files_only=local_only)
            self._model.eval()
            self._torch = torch
            self.available = True
            self._caption_mode = "blip"
        except Exception as exc:
            logger.info("Caption model unavailable, using heuristic fallback: %s", exc)

    def _fallback_caption(self, frame) -> tuple[str, float]:
        mean_brightness = float(frame.mean())
        blue_mean = float(frame[:, :, 0].mean())
        green_mean = float(frame[:, :, 1].mean())
        red_mean = float(frame[:, :, 2].mean())

        tone = "dark" if mean_brightness < 80 else "bright" if mean_brightness > 170 else "normal-lit"
        if red_mean > green_mean + 12 and red_mean > blue_mean + 12:
            color_hint = "with warm dominant colors"
        elif blue_mean > red_mean + 12 and blue_mean > green_mean + 12:
            color_hint = "with cool dominant colors"
        else:
            color_hint = "with balanced colors"

        return f"A {tone} video scene {color_hint}.", 58.0

    def _generate_frame_caption(self, frame) -> tuple[str, float]:
        self._initialize_model()

        if self.available and self._processor is not None and self._model is not None and self._torch is not None:
            try:
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                inputs = self._processor(images=image, return_tensors="pt")
                with self._torch.no_grad():
                    output = self._model.generate(**inputs, max_new_tokens=28, num_beams=4)
                caption = self._processor.tokenizer.decode(output[0], skip_special_tokens=True).strip()
                if caption:
                    return caption, 92.0
            except Exception as exc:
                logger.warning("Caption generation failed for frame; falling back to heuristic caption: %s", exc)

        return self._fallback_caption(frame)

    def generate_captions(
        self,
        video_path: str,
        sample_rate: int = 30,
        max_frames: int = 20
    ) -> Dict[str, Any]:
        """
        Generate detailed captions for video content.
        """
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            captions = []
            frame_count = 0
            analyzed_frames = 0

            while cap.isOpened() and analyzed_frames < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % sample_rate == 0:
                    try:
                        frame_resized = cv2.resize(frame, (512, 512))
                        caption_text, confidence = self._generate_frame_caption(frame_resized)
                        timestamp_sec = frame_count / fps
                        time_str = self._format_timestamp(timestamp_sec)

                        captions.append({
                            "timestamp": time_str,
                            "timestamp_seconds": timestamp_sec,
                            "caption": caption_text,
                            "frame_number": frame_count,
                            "confidence": confidence,
                        })
                        analyzed_frames += 1
                    except Exception as exc:
                        logger.error("Error generating caption for frame %s: %s", frame_count, exc)

                frame_count += 1

            cap.release()

            summary = self._generate_summary(captions)

            return {
                "status": "success",
                "captions": captions,
                "total_frames_analyzed": analyzed_frames,
                "total_frames": total_frames,
                "duration_seconds": total_frames / fps if fps else 0,
                "summary": summary,
                "confidence_average": float(np.mean([c["confidence"] for c in captions])) if captions else 0.0,
                "mode": self._caption_mode,
            }

        except Exception as exc:
            logger.error("Error in caption generation: %s", exc)
            return {
                "status": "error",
                "error": str(exc),
                "captions": [],
                "summary": "Caption generation failed",
            }

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds to HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    @staticmethod
    def _generate_summary(captions: List[Dict]) -> str:
        """Generate summary from multiple captions."""
        if not captions:
            return "No captions generated"

        summary = ". ".join(c["caption"] for c in captions[:3])
        if len(summary) > 200:
            summary = summary[:200] + "..."
        return summary
