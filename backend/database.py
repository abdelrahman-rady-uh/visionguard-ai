import os
import sqlite3
from contextlib import contextmanager
from backend.config import DATABASE_PATH


class Database:
    def __init__(self):
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        self._initialize()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _initialize(self):
        self._create_schema()
        self._migrate()

    def _migrate(self):
        """Add new columns to existing tables without dropping data."""
        migrations = [
            "ALTER TABLE Users ADD COLUMN GoogleID TEXT",
            "ALTER TABLE Users ADD COLUMN Picture TEXT",
        ]
        with self.connection() as conn:
            for sql in migrations:
                try:
                    conn.execute(sql)
                except Exception:
                    pass  # Column already exists

    def _create_schema(self):
        schema_sql = """
        CREATE TABLE IF NOT EXISTS Users (
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT NOT NULL,
            Email TEXT NOT NULL UNIQUE,
            Password TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Videos (
            VideoID INTEGER PRIMARY KEY AUTOINCREMENT,
            FileName TEXT NOT NULL,
            UploadDate TEXT NOT NULL,
            Duration REAL DEFAULT 0,
            UserID INTEGER,
            FOREIGN KEY(UserID) REFERENCES Users(UserID)
        );

        CREATE TABLE IF NOT EXISTS AnalysisResults (
            AnalysisID INTEGER PRIMARY KEY AUTOINCREMENT,
            VideoID INTEGER NOT NULL,
            ResultsJSON TEXT NOT NULL,
            TimelineJSON TEXT,
            ConfidenceScoresJSON TEXT,
            CreatedAt TEXT NOT NULL,
            UpdatedAt TEXT NOT NULL,
            ExportedFormats TEXT DEFAULT '',
            FOREIGN KEY(VideoID) REFERENCES Videos(VideoID)
        );

        CREATE TABLE IF NOT EXISTS Captions (
            CaptionID INTEGER PRIMARY KEY AUTOINCREMENT,
            CaptionText TEXT NOT NULL,
            VideoID INTEGER NOT NULL,
            FOREIGN KEY(VideoID) REFERENCES Videos(VideoID)
        );

        CREATE TABLE IF NOT EXISTS AI_Detection (
            DetectionID INTEGER PRIMARY KEY AUTOINCREMENT,
            AIStatus TEXT NOT NULL,
            ConfidenceScore REAL NOT NULL,
            VideoID INTEGER NOT NULL,
            FOREIGN KEY(VideoID) REFERENCES Videos(VideoID)
        );

        CREATE TABLE IF NOT EXISTS Tampering (
            TamperingID INTEGER PRIMARY KEY AUTOINCREMENT,
            TamperingType TEXT NOT NULL,
            VideoID INTEGER NOT NULL,
            FOREIGN KEY(VideoID) REFERENCES Videos(VideoID)
        );

        CREATE TABLE IF NOT EXISTS Face_Detection (
            FaceDetectionID INTEGER PRIMARY KEY AUTOINCREMENT,
            FaceDetected INTEGER NOT NULL,
            VideoID INTEGER NOT NULL,
            FOREIGN KEY(VideoID) REFERENCES Videos(VideoID)
        );

        CREATE TABLE IF NOT EXISTS Privacy_Alert (
            AlertID INTEGER PRIMARY KEY AUTOINCREMENT,
            AlertMessage TEXT NOT NULL,
            FaceDetectionID INTEGER NOT NULL,
            FOREIGN KEY(FaceDetectionID) REFERENCES Face_Detection(FaceDetectionID)
        );

        CREATE INDEX IF NOT EXISTS idx_videos_user ON Videos(UserID);
        CREATE INDEX IF NOT EXISTS idx_analysis_video ON AnalysisResults(VideoID);
        CREATE INDEX IF NOT EXISTS idx_captions_video ON Captions(VideoID);
        CREATE INDEX IF NOT EXISTS idx_ai_video ON AI_Detection(VideoID);
        CREATE INDEX IF NOT EXISTS idx_tampering_video ON Tampering(VideoID);
        CREATE INDEX IF NOT EXISTS idx_face_video ON Face_Detection(VideoID);
        CREATE INDEX IF NOT EXISTS idx_privacy_face ON Privacy_Alert(FaceDetectionID);
        """

        with self.connection() as conn:
            conn.executescript(schema_sql)

    def create_or_get_default_user(self):
        with self.connection() as conn:
            cur = conn.execute("SELECT UserID FROM Users WHERE Email = ?", ("local@system.ai",))
            row = cur.fetchone()
            if row:
                return row[0]
            cur = conn.execute(
                "INSERT INTO Users(Username, Email, Password) VALUES (?, ?, ?)",
                ("local_user", "local@system.ai", "local_password")
            )
            return cur.lastrowid

    def get_or_create_google_user(self, google_id, email, name, picture):
        """Return user_id for a Google OAuth user, creating or updating as needed."""
        with self.connection() as conn:
            # Check by google_id first
            cur = conn.execute("SELECT UserID FROM Users WHERE GoogleID = ?", (google_id,))
            row = cur.fetchone()
            if row:
                # Update picture in case it changed
                conn.execute("UPDATE Users SET Picture = ? WHERE UserID = ?", (picture, row[0]))
                return row[0]
            # Check by email (may be a legacy local account)
            cur = conn.execute("SELECT UserID FROM Users WHERE Email = ?", (email,))
            row = cur.fetchone()
            if row:
                conn.execute(
                    "UPDATE Users SET GoogleID = ?, Picture = ?, Username = ? WHERE UserID = ?",
                    (google_id, picture, name, row[0])
                )
                return row[0]
            # Brand-new user
            cur = conn.execute(
                "INSERT INTO Users(Username, Email, Password, GoogleID, Picture) VALUES (?, ?, ?, ?, ?)",
                (name, email, "", google_id, picture)
            )
            return cur.lastrowid

    def get_user_history(self, user_id):
        """Return a list of analysis summaries for a user, newest first."""
        with self.connection() as conn:
            cur = conn.execute(
                """
                SELECT
                    v.VideoID,
                    v.FileName,
                    v.UploadDate,
                    ai.AIStatus,
                    ai.ConfidenceScore,
                    c.CaptionText,
                    t.TamperingType,
                    fd.FaceDetected
                FROM Videos v
                LEFT JOIN (
                    SELECT VideoID, AIStatus, ConfidenceScore
                    FROM AI_Detection
                    GROUP BY VideoID
                ) ai ON ai.VideoID = v.VideoID
                LEFT JOIN (
                    SELECT VideoID, CaptionText
                    FROM Captions
                    GROUP BY VideoID
                ) c ON c.VideoID = v.VideoID
                LEFT JOIN (
                    SELECT VideoID, TamperingType
                    FROM Tampering
                    GROUP BY VideoID
                ) t ON t.VideoID = v.VideoID
                LEFT JOIN (
                    SELECT VideoID, FaceDetected
                    FROM Face_Detection
                    GROUP BY VideoID
                ) fd ON fd.VideoID = v.VideoID
                WHERE v.UserID = ?
                ORDER BY v.UploadDate DESC
                LIMIT 50
                """,
                (user_id,)
            )
            rows = cur.fetchall()
            import re
            history = []
            for row in rows:
                raw_name = row[1] or ""
                clean_name = raw_name[:-4] if raw_name.endswith(".enc") else raw_name
                clean_name = re.sub(r"^\d{14}_", "", clean_name)
                history.append({
                    "video_id": row[0],
                    "file_name": clean_name,
                    "upload_date": row[2],
                    "ai_status": row[3],
                    "confidence": round(float(row[4] or 0), 2),
                    "caption": (row[5] or "")[:120],
                    "tampering_type": row[6],
                    "faces_detected": bool(row[7]),
                })
            return history

    def get_full_analysis_result(self, video_id, user_id):
        """Return the stored full result JSON for a video, verifying ownership."""
        import json, re
        with self.connection() as conn:
            cur = conn.execute(
                "SELECT FileName, UserID FROM Videos WHERE VideoID = ?", (video_id,)
            )
            row = cur.fetchone()
            if not row or row[1] != user_id:
                return None
            raw_name = row[0] or ""
            clean_name = raw_name[:-4] if raw_name.endswith(".enc") else raw_name
            clean_name = re.sub(r"^\d{14}_", "", clean_name)

            cur = conn.execute(
                "SELECT ResultsJSON FROM AnalysisResults WHERE VideoID = ? ORDER BY CreatedAt DESC LIMIT 1",
                (video_id,)
            )
            ar = cur.fetchone()
            result_data = json.loads(ar[0]) if ar and ar[0] else {}

            return {
                "videoUrl": f"/api/video/{video_id}",
                "fileName": clean_name,
                "fileSize": None,
                "sha256": None,
                "result": result_data,
            }

    def get_video_filename(self, video_id):
        with self.connection() as conn:
            cur = conn.execute("SELECT FileName FROM Videos WHERE VideoID = ?", (video_id,))
            row = cur.fetchone()
            return row[0] if row else None

    def insert_video(self, filename, upload_date, duration, user_id):
        with self.connection() as conn:
            cur = conn.execute(
                "INSERT INTO Videos(FileName, UploadDate, Duration, UserID) VALUES (?, ?, ?, ?)",
                (filename, upload_date, duration, user_id)
            )
            return cur.lastrowid

    def insert_caption(self, caption_text, video_id):
        with self.connection() as conn:
            conn.execute("INSERT INTO Captions(CaptionText, VideoID) VALUES (?, ?)", (caption_text, video_id))

    def insert_ai_detection(self, status, confidence, video_id):
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO AI_Detection(AIStatus, ConfidenceScore, VideoID) VALUES (?, ?, ?)",
                (status, float(confidence), video_id)
            )

    def insert_tampering(self, tampering_type, video_id):
        with self.connection() as conn:
            conn.execute("INSERT INTO Tampering(TamperingType, VideoID) VALUES (?, ?)", (tampering_type, video_id))

    def insert_face_detection(self, face_detected, video_id):
        with self.connection() as conn:
            cur = conn.execute(
                "INSERT INTO Face_Detection(FaceDetected, VideoID) VALUES (?, ?)",
                (1 if face_detected else 0, video_id)
            )
            return cur.lastrowid

    def insert_privacy_alert(self, alert_message, face_detection_id):
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO Privacy_Alert(AlertMessage, FaceDetectionID) VALUES (?, ?)",
                (alert_message, face_detection_id)
            )

    def insert_analysis_result(self, video_id, results_json, timeline_json=None, confidence_json=None):
        """Store analysis results in database"""
        import json
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        with self.connection() as conn:
            cur = conn.execute(
                """INSERT INTO AnalysisResults(VideoID, ResultsJSON, TimelineJSON, 
                   ConfidenceScoresJSON, CreatedAt, UpdatedAt) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (video_id, json.dumps(results_json), json.dumps(timeline_json) if timeline_json else None,
                 json.dumps(confidence_json) if confidence_json else None, now, now)
            )
            return cur.lastrowid

    def get_analysis_result(self, analysis_id):
        """Retrieve analysis result by ID"""
        import json
        with self.connection() as conn:
            cur = conn.execute(
                "SELECT * FROM AnalysisResults WHERE AnalysisID = ?",
                (analysis_id,)
            )
            row = cur.fetchone()
            if row:
                return {
                    'AnalysisID': row[0],
                    'VideoID': row[1],
                    'ResultsJSON': json.loads(row[2]) if row[2] else None,
                    'TimelineJSON': json.loads(row[3]) if row[3] else None,
                    'ConfidenceScoresJSON': json.loads(row[4]) if row[4] else None,
                    'CreatedAt': row[5],
                    'UpdatedAt': row[6],
                    'ExportedFormats': row[7]
                }
            return None

    def get_analysis_by_video(self, video_id):
        """Retrieve analysis results by video ID"""
        import json
        with self.connection() as conn:
            cur = conn.execute(
                "SELECT * FROM AnalysisResults WHERE VideoID = ? ORDER BY CreatedAt DESC LIMIT 1",
                (video_id,)
            )
            row = cur.fetchone()
            if row:
                return {
                    'AnalysisID': row[0],
                    'VideoID': row[1],
                    'ResultsJSON': json.loads(row[2]) if row[2] else None,
                    'TimelineJSON': json.loads(row[3]) if row[3] else None,
                    'ConfidenceScoresJSON': json.loads(row[4]) if row[4] else None,
                    'CreatedAt': row[5],
                    'UpdatedAt': row[6],
                    'ExportedFormats': row[7]
                }
            return None

    def update_exported_formats(self, analysis_id, formats):
        """Update the exported formats for an analysis result"""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        with self.connection() as conn:
            conn.execute(
                "UPDATE AnalysisResults SET ExportedFormats = ?, UpdatedAt = ? WHERE AnalysisID = ?",
                (','.join(formats), now, analysis_id)
            )
