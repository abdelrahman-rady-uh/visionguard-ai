import os
import re
import traceback
import json
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request, send_from_directory, send_file, Response, session as flask_session
from werkzeug.utils import secure_filename

from backend.config import ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH, RESULTS_DIR, UPLOAD_DIR, SECRET_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from backend.database import Database
from backend.services.analyzer import VideoAnalyzer
from backend.utils.audit import AuditLogger
from backend.utils.security import SecurityService
from backend.utils.logging_config import setup_logging
from backend.routes import analysis_bp, analysis_v2_bp
from backend.routes.datasets import datasets_bp
from backend.routes.auth import auth_bp, init_auth
from backend.middleware.security import SecurityHeaders

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image as RLImage
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# Setup logging
setup_logging(log_dir=os.getenv("LOG_PATH", "logs"), log_level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend"),
    static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend"),
    static_url_path="",
)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["SECRET_KEY"] = SECRET_KEY
app.config["GOOGLE_CLIENT_ID"] = GOOGLE_CLIENT_ID
app.config["GOOGLE_CLIENT_SECRET"] = GOOGLE_CLIENT_SECRET

# Register security headers
@app.after_request
def add_security_headers_to_response(response):
    """Add security headers to all responses."""
    return SecurityHeaders.add_security_headers(response)

# Register blueprints
app.register_blueprint(analysis_bp)
app.register_blueprint(analysis_v2_bp)
app.register_blueprint(datasets_bp)
app.register_blueprint(auth_bp)
init_auth(app)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

db = Database()
audit = AuditLogger()
security = SecurityService()
analyzer = VideoAnalyzer(audit)

# Server-side store for decrypted runtime paths, keyed by video_id.
# Avoids exposing server file paths to clients and prevents path-traversal attacks.
_runtime_paths: dict = {}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/upload")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/analysis")
def analysis_dashboard():
    """Multi-provider analysis dashboard."""
    return render_template("analysis_dashboard.html")


@app.route("/forensics")
def forensics():
    return render_template("forensics.html")


@app.route("/datasets")
def datasets_page():
    return render_template("datasets.html")


@app.route("/api/upload", methods=["POST"])
def upload_video():
    session_id = request.headers.get("X-Session-ID", "local-session")
    try:
        if "video" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["video"]
        if not file.filename:
            return jsonify({"error": "Empty filename"}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": "Unsupported file type"}), 400

        filename = secure_filename(file.filename)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        plaintext_name = f"{timestamp}_{filename}"
        plaintext_path = os.path.join(UPLOAD_DIR, plaintext_name)
        file.save(plaintext_path)

        file_hash = security.sha256_file(plaintext_path)
        encrypted_name = plaintext_name + ".enc"
        encrypted_path = os.path.join(UPLOAD_DIR, encrypted_name)
        security.encrypt_file(plaintext_path, encrypted_path)
        os.remove(plaintext_path)

        decrypted_runtime_path = os.path.join(UPLOAD_DIR, f"{plaintext_name}.runtime")
        security.decrypt_file(encrypted_path, decrypted_runtime_path)

        user_id = flask_session.get("user_id") or db.create_or_get_default_user()
        video_id = db.insert_video(encrypted_name, datetime.now(timezone.utc).isoformat(), 0.0, user_id)
        audit.log("video_uploaded", session_id, {"video_id": video_id, "hash": file_hash, "encrypted_path": encrypted_name})

        # Store path server-side so the client never touches the filesystem path.
        _runtime_paths[video_id] = decrypted_runtime_path

        return jsonify(
            {
                "video_id": video_id,
                "filename": encrypted_name,
                "sha256": file_hash,
            }
        )
    except Exception as exc:
        audit.log("upload_failed", session_id, {"error": str(exc), "trace": traceback.format_exc()})
        return jsonify({"error": str(exc)}), 500


@app.route("/api/analyze/<int:video_id>", methods=["POST"])
def analyze_video(video_id):
    session_id = request.headers.get("X-Session-ID", "local-session")
    try:
        runtime_path = _runtime_paths.pop(video_id, None)
        if not runtime_path or not os.path.exists(runtime_path):
            return jsonify({"error": "Runtime video path missing or already consumed"}), 400

        try:
            result = analyzer.analyze(runtime_path, video_id)
        finally:
            # Always delete the plaintext runtime file regardless of analysis outcome.
            try:
                os.remove(runtime_path)
            except OSError:
                pass

        db.insert_caption(result["caption"]["caption"], video_id)
        db.insert_ai_detection(result["ai_detection"]["status"], result["ai_detection"]["confidence"], video_id)
        db.insert_tampering(result["tampering"]["tampering_type"], video_id)
        face_detection_id = db.insert_face_detection(result["face_detection"]["faces_detected"], video_id)
        db.insert_privacy_alert(result["face_detection"]["alert"], face_detection_id)
        db.insert_analysis_result(video_id, result)

        audit.log("video_analyzed", session_id, {"video_id": video_id, "result_summary": result["ai_detection"]["status"]})

        return jsonify(result)
    except Exception as exc:
        audit.log("analysis_failed", session_id, {"video_id": video_id, "error": str(exc), "trace": traceback.format_exc()})
        return jsonify({"error": str(exc)}), 500


@app.route("/api/export/json", methods=["POST"])
def export_json():
    """Export analysis results as JSON"""
    try:
        payload = request.get_json(silent=True) or {}
        analysis_data = payload.get("data", {})
        
        export_data = {
            "exportDate": datetime.now(timezone.utc).isoformat(),
            "system": "VisionGuard AI",
            "version": "1.0",
            "analysis": analysis_data
        }
        
        filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(RESULTS_DIR, filename)
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return send_file(filepath, as_attachment=True, download_name=filename, mimetype='application/json')
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/export/pdf", methods=["POST"])
def export_pdf():
    """Export analysis results as PDF"""
    try:
        if not REPORTLAB_AVAILABLE:
            return jsonify({"error": "PDF generation not available. Install reportlab."}), 501
        
        payload = request.get_json(silent=True) or {}
        analysis_data = payload.get("data", {})
        
        filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(RESULTS_DIR, filename)
        
        # Create PDF
        doc = SimpleDocTemplate(filepath, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2ad4ff'),
            spaceAfter=30,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph("VisionGuard AI - Analysis Report", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Metadata
        meta = analysis_data.get('metadata', {})
        data_items = [
            ["Field", "Value"],
            ["Generated", datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ["Duration", f"{meta.get('duration', 0):.2f}s"],
            ["FPS", f"{meta.get('fps', 0):.2f}"],
            ["Frames Sampled", str(meta.get('frame_count', 0))],
        ]
        
        t = Table(data_items, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ad4ff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.3*inch))
        
        # AI Detection Results
        story.append(Paragraph("AI Detection Results", styles['Heading2']))
        ai_det = analysis_data.get('ai_detection', {})
        ai_items = [
            ["Status", ai_det.get('status', '-')],
            ["Confidence", f"{ai_det.get('confidence', 0):.2f}%"],
        ]
        
        t2 = Table(ai_items, colWidths=[2*inch, 4*inch])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4cffc2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(t2)
        story.append(Spacer(1, 0.2*inch))
        
        # Caption
        story.append(Paragraph("Generated Caption", styles['Heading2']))
        caption_text = analysis_data.get('caption', {}).get('caption', 'N/A')
        story.append(Paragraph(caption_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Tampering Detection
        story.append(Paragraph("Tampering Analysis", styles['Heading2']))
        tamp = analysis_data.get('tampering', {})
        tamp_items = [
            ["Type", tamp.get('tampering_type', '-')],
            ["Frame Duplication", str(tamp.get('frame_duplication', False))],
            ["Frame Removal", str(tamp.get('frame_removal', False))],
            ["Temporal Inconsistency", str(tamp.get('temporal_inconsistency', False))],
            ["Confidence", f"{tamp.get('confidence', 0):.2f}%"],
        ]
        
        t3 = Table(tamp_items, colWidths=[2*inch, 4*inch])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffb24a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(t3)
        story.append(Spacer(1, 0.2*inch))
        
        # Face Detection
        story.append(Paragraph("Face Detection & Privacy", styles['Heading2']))
        face = analysis_data.get('face_detection', {})
        face_items = [
            ["Faces Detected", str(face.get('faces_detected', False))],
            ["Total Faces", str(face.get('total_faces', 0))],
            ["Alert", face.get('alert', 'N/A')],
            ["Confidence", f"{face.get('confidence', 0):.2f}%"],
        ]
        
        t4 = Table(face_items, colWidths=[2*inch, 4*inch])
        t4.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff5e7a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(t4)
        story.append(Spacer(1, 0.3*inch))
        
        # Build PDF
        doc.build(story)
        
        return send_file(filepath, as_attachment=True, download_name=filename, mimetype='application/pdf')
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/video/<int:video_id>")
def stream_video(video_id):
    """Decrypt and stream the stored video with Range support (enables seeking)."""
    try:
        filename = db.get_video_filename(video_id)
        if not filename:
            return jsonify({"error": "Video not found"}), 404

        encrypted_path = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(encrypted_path):
            return jsonify({"error": "Encrypted file missing"}), 404

        # Decrypt the video entirely into memory — no temp file left on disk.
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        with open(encrypted_path, "rb") as f:
            raw = f.read()
        nonce, ciphertext = raw[:12], raw[12:]
        plaintext = AESGCM(security.key).decrypt(nonce, ciphertext, None)

        # Derive MIME type from the original extension (strip ".enc").
        original_name = filename[:-4] if filename.endswith(".enc") else filename
        ext = original_name.rsplit(".", 1)[-1].lower()
        mime = {"mp4": "video/mp4", "avi": "video/x-msvideo", "mov": "video/quicktime"}.get(ext, "video/mp4")

        total = len(plaintext)
        range_header = request.headers.get("Range")

        if range_header:
            m = re.search(r"bytes=(\d+)-(\d*)", range_header)
            start = int(m.group(1)) if m else 0
            end   = int(m.group(2)) if m and m.group(2) else total - 1
            end   = min(end, total - 1)
            chunk = plaintext[start:end + 1]
            return Response(
                chunk,
                status=206,
                mimetype=mime,
                headers={
                    "Content-Range":  f"bytes {start}-{end}/{total}",
                    "Accept-Ranges":  "bytes",
                    "Content-Length": str(len(chunk)),
                },
            )

        return Response(
            plaintext,
            status=200,
            mimetype=mime,
            headers={
                "Accept-Ranges":  "bytes",
                "Content-Length": str(total),
            },
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/results/<path:filename>")
def serve_results(filename):
    # Resolve MIME type for video files so browsers accept them correctly.
    mime_map = {
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }
    ext = os.path.splitext(filename)[1].lower()
    mime = mime_map.get(ext)
    return send_from_directory(
        RESULTS_DIR,
        filename,
        mimetype=mime,
        conditional=True,   # enables Range / partial-content (needed for video seeking)
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
