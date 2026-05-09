import cv2
import numpy as np


class EventTimelineService:
    def _hist_distance(self, f1, f2):
        hsv1 = cv2.cvtColor(f1, cv2.COLOR_RGB2HSV)
        hsv2 = cv2.cvtColor(f2, cv2.COLOR_RGB2HSV)
        h1 = cv2.calcHist([hsv1], [0, 1], None, [30, 32], [0, 180, 0, 256])
        h2 = cv2.calcHist([hsv2], [0, 1], None, [30, 32], [0, 180, 0, 256])
        h1 = cv2.normalize(h1, h1).flatten()
        h2 = cv2.normalize(h2, h2).flatten()
        # Convert correlation into distance-like score.
        corr = cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL)
        return float(1.0 - corr)

    def build_timeline(self, frames, meta, caption_service, max_shots=8):
        if len(frames) < 2:
            return []

        distances = [self._hist_distance(frames[i - 1], frames[i]) for i in range(1, len(frames))]
        d = np.array(distances, dtype=np.float32)
        threshold = float(np.mean(d) + 1.1 * np.std(d))
        threshold = max(0.16, threshold)

        boundaries = [0]
        for i, val in enumerate(distances, start=1):
            if val >= threshold:
                boundaries.append(i)
        boundaries.append(len(frames) - 1)

        # Remove near-duplicate boundaries.
        clean = [boundaries[0]]
        for b in boundaries[1:]:
            if b - clean[-1] >= 2:
                clean.append(b)
        boundaries = clean
        if boundaries[-1] != len(frames) - 1:
            boundaries.append(len(frames) - 1)

        fps = float(meta.get("fps") or 0.0)
        sampled_indices = meta.get("sampled_indices") or list(range(len(frames)))

        shots = []
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            if end <= start:
                continue
            mid = (start + end) // 2
            cap = caption_service.caption_from_frame(frames[mid])

            if fps > 0 and mid < len(sampled_indices) and start < len(sampled_indices) and end < len(sampled_indices):
                t_mid = sampled_indices[mid] / fps
                t_start = sampled_indices[start] / fps
                t_end = sampled_indices[end] / fps
            else:
                t_mid = float(mid)
                t_start = float(start)
                t_end = float(end)

            shots.append(
                {
                    "shot": i + 1,
                    "time": round(t_mid, 2),
                    "start_time": round(t_start, 2),
                    "end_time": round(t_end, 2),
                    "event": cap["caption"],
                    "confidence": cap["confidence"],
                }
            )

        if len(shots) > max_shots:
            step = max(1, len(shots) // max_shots)
            shots = shots[::step][:max_shots]
        return shots
