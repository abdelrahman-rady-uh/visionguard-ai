import cv2
import numpy as np
from backend.utils.security import normalize_confidence


class TamperingService:
    def _dhash(self, gray, hash_size=8):
        resized = cv2.resize(gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
        diff = resized[:, 1:] > resized[:, :-1]
        return diff.astype(np.uint8).flatten()

    def _hamming(self, h1, h2):
        return int(np.sum(h1 != h2))

    def detect(self, frames):
        if len(frames) < 4:
            return {
                "tampering_type": "Insufficient frames",
                "frame_duplication": False,
                "frame_removal": False,
                "temporal_inconsistency": False,
                "confidence": 0.0,
                "details": {},
            }

        diffs = []
        flow_mag = []
        hashes = []
        duplicate_hits = 0
        abrupt_jumps = 0

        grays = [cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in frames]
        for i, gray in enumerate(grays):
            hashes.append(self._dhash(gray))
            if i == 0:
                continue

            prev = grays[i - 1]
            diff = float(np.mean(cv2.absdiff(prev, gray)))
            diffs.append(diff)

            ham = self._hamming(hashes[i - 1], hashes[i])
            if ham <= 3 and diff < 2.5:
                duplicate_hits += 1

            flow = cv2.calcOpticalFlowFarneback(prev, gray, None, 0.5, 3, 17, 3, 5, 1.1, 0)
            mag = float(np.mean(np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)))
            flow_mag.append(mag)

        if diffs:
            d = np.array(diffs, dtype=np.float32)
            mean_diff = float(np.mean(d))
            std_diff = float(np.std(d))
            p95 = float(np.percentile(d, 95))
            abrupt_jumps = int(np.sum(d > max(mean_diff + 2.2 * std_diff, p95)))
        else:
            mean_diff = 0.0
            std_diff = 0.0
            p95 = 0.0

        if flow_mag:
            f = np.array(flow_mag, dtype=np.float32)
            flow_std = float(np.std(f))
            flow_p95 = float(np.percentile(f, 95))
        else:
            flow_std = 0.0
            flow_p95 = 0.0

        frame_duplication = duplicate_hits >= max(1, len(frames) // 12)
        frame_removal = abrupt_jumps >= max(1, len(frames) // 16)
        temporal_inconsistency = flow_std > 2.8 or flow_p95 > 9.0

        labels = []
        if frame_duplication:
            labels.append("frame duplication")
        if frame_removal:
            labels.append("frame removal")
        if temporal_inconsistency:
            labels.append("temporal inconsistencies")
        tampering_type = ", ".join(labels) if labels else "No major tampering signals"

        confidence_raw = 30 + 24 * int(frame_duplication) + 23 * int(frame_removal) + 23 * int(temporal_inconsistency)
        confidence = normalize_confidence(confidence_raw)

        return {
            "tampering_type": tampering_type,
            "frame_duplication": frame_duplication,
            "frame_removal": frame_removal,
            "temporal_inconsistency": temporal_inconsistency,
            "confidence": confidence,
            "details": {
                "duplicate_hits": int(duplicate_hits),
                "abrupt_jumps": int(abrupt_jumps),
                "mean_diff": round(mean_diff, 3),
                "std_diff": round(std_diff, 3),
                "flow_std": round(flow_std, 3),
                "flow_p95": round(flow_p95, 3),
            },
        }
