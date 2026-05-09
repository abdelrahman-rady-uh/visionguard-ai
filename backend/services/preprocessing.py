import os
import cv2
import numpy as np


class PreprocessingService:
    def __init__(self, target_size=(384, 216), max_frames=48):
        self.target_size = target_size
        self.max_frames = max_frames

    def extract_frames(self, video_path):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return [], {"fps": 0.0, "duration": 0.0, "frame_count": 0, "sample_rate": 1, "sampled_indices": []}

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = frame_count / fps if fps > 0 else 0.0

        sample_rate = 1
        if frame_count > self.max_frames and self.max_frames > 0:
            sample_rate = max(1, frame_count // self.max_frames)

        frames = []
        sampled_indices = []
        idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % sample_rate == 0:
                frame = cv2.resize(frame, self.target_size, interpolation=cv2.INTER_AREA)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.clip(frame, 0, 255).astype("uint8")
                frames.append(frame)
                sampled_indices.append(idx)
            idx += 1

        cap.release()
        return frames, {
            "fps": fps,
            "duration": duration,
            "frame_count": frame_count,
            "sample_rate": sample_rate,
            "sampled_indices": sampled_indices,
        }
