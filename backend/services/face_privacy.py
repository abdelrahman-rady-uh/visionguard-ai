import os
import urllib.request
import cv2
from backend.config import RESULTS_DIR
from backend.utils.security import normalize_confidence


class FacePrivacyService:
    def __init__(self):
        self.cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(self.cascade_path)
        self.yunet = self._load_yunet_detector()

    def _load_yunet_detector(self):
        services_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(os.path.dirname(services_dir), "models")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, "face_detection_yunet_2023mar.onnx")

        if not os.path.exists(model_path):
            try:
                url = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
                urllib.request.urlretrieve(url, model_path)
            except Exception:
                return None

        try:
            if hasattr(cv2, "FaceDetectorYN_create"):
                return cv2.FaceDetectorYN_create(model_path, "", (320, 320), 0.6, 0.3, 5000)
        except Exception:
            return None
        return None

    def _detect_faces(self, bgr):
        h, w = bgr.shape[:2]
        faces = []

        if self.yunet is not None:
            try:
                self.yunet.setInputSize((w, h))
                _, det = self.yunet.detect(bgr)
                if det is not None:
                    for row in det:
                        x, y, fw, fh = int(row[0]), int(row[1]), int(row[2]), int(row[3])
                        x  = max(0, x)
                        y  = max(0, y)
                        fw = max(1, min(fw, w - x))
                        fh = max(1, min(fh, h - y))
                        faces.append((x, y, fw, fh))
            except Exception:
                faces = []

        if not faces:
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            # More sensitive thresholds: smaller minSize, fewer required neighbours,
            # finer scale steps — catches faces that are far away or partially turned.
            for scale, neighbors in [(1.05, 3), (1.1, 4)]:
                detected = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=scale,
                    minNeighbors=neighbors,
                    minSize=(20, 20),
                )
                if len(detected) > 0:
                    faces = [(int(x), int(y), int(fw), int(fh)) for (x, y, fw, fh) in detected]
                    break

        return faces

    @staticmethod
    def _cover_face(frame, x, y, w, h):
        """Fill the face region with a solid black rectangle."""
        frame[y:y + h, x:x + w] = 0

    def detect_and_blur(self, frames, video_id, video_path=None, meta=None):
        """
        Detect faces in every sampled frame, cover them with black rectangles,
        and return per-frame face positions so the browser can overlay them
        on the original video without needing to re-encode anything.
        """
        if not frames:
            return {
                "faces_detected": False,
                "alert": "No frames available for face analysis.",
                "confidence": 0.0,
                "preview_path": None,
                "blurred_video_path": None,
                "face_frames": [],
            }

        os.makedirs(RESULTS_DIR, exist_ok=True)
        total_faces   = 0
        face_frames   = []          # [{timestamp, faces:[{x_pct,y_pct,w_pct,h_pct}]}]
        blurred_frames = []

        fps             = float((meta or {}).get("fps") or 0)
        sampled_indices = list((meta or {}).get("sampled_indices") or range(len(frames)))
        # Preprocessed frame dimensions (set by PreprocessingService)
        frame_w, frame_h = 384, 216

        for i, frame in enumerate(frames):
            bgr  = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            h, w = bgr.shape[:2]
            faces = self._detect_faces(bgr)
            total_faces += len(faces)

            # Timestamp of this sampled frame in the original video
            if fps > 0 and i < len(sampled_indices):
                ts = round(sampled_indices[i] / fps, 3)
            else:
                ts = float(i)

            if faces:
                # Store coordinates as fractions of the preprocessed frame so
                # the browser can scale them to whatever display size is used.
                face_frames.append({
                    "timestamp": ts,
                    "faces": [
                        {
                            "x_pct": round(x / w, 4),
                            "y_pct": round(y / h, 4),
                            "w_pct": round(fw / w, 4),
                            "h_pct": round(fh / h, 4),
                        }
                        for (x, y, fw, fh) in faces
                    ],
                })

            for (x, y, fw, fh) in faces:
                self._cover_face(bgr, x, y, fw, fh)
            blurred_frames.append(bgr)

        # Single-frame preview image (middle frame, faces already blacked out)
        sample_bgr   = blurred_frames[len(blurred_frames) // 2]
        preview_path = os.path.join(RESULTS_DIR, f"blur_preview_{video_id}.jpg")
        cv2.imwrite(preview_path, sample_bgr)

        faces_detected = total_faces > 0
        alert = "Privacy alert: faces detected and blurred." if faces_detected else "No faces detected."
        conf  = normalize_confidence(88 if faces_detected else 75)
        return {
            "faces_detected":     faces_detected,
            "alert":              alert,
            "confidence":         conf,
            "preview_path":       preview_path,
            "blurred_video_path": None,   # no longer used; overlay is client-side
            "face_frames":        face_frames,
            "total_faces":        int(total_faces),
        }
