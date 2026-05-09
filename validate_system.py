import io
import os
import cv2
import numpy as np

os.environ.setdefault("CAPTION_REMOTE_LOAD", "0")
from backend.app import app


def build_sample_video(path):
    width, height = 320, 240
    fps = 12
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(path, fourcc, fps, (width, height))
    for i in range(36):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.rectangle(frame, (20 + i * 3 % 200, 50), (120 + i * 3 % 200, 160), (0, 180, 255), -1)
        cv2.putText(frame, f"F{i}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        writer.write(frame)
    writer.release()


def run_validation():
    os.makedirs("results", exist_ok=True)
    sample_path = os.path.join("results", "sample_test.mp4")
    build_sample_video(sample_path)
    with app.test_client() as client:
        with open(sample_path, "rb") as f:
            data = {"video": (io.BytesIO(f.read()), "sample_test.mp4")}
        up = client.post("/api/upload", data=data, content_type="multipart/form-data")
        assert up.status_code == 200, up.data.decode()
        upj = up.get_json()

        an = client.post(f"/api/analyze/{upj['video_id']}", json={"runtime_path": upj["runtime_path"]})
        assert an.status_code == 200, an.data.decode()
        res = an.get_json()

        assert "caption" in res and "ai_detection" in res and "tampering" in res and "face_detection" in res and "shot_events" in res
        print("VALIDATION_OK")
        print(res["caption"])
        print(res["ai_detection"])
        print(res["tampering"])
        print(res["face_detection"])
        print({"shot_events_count": len(res.get("shot_events", []))})


if __name__ == "__main__":
    run_validation()


