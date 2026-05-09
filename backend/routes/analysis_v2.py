"""
Advanced Analysis Routes - Complete video analysis pipeline
"""
import os
import logging
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename

from backend.services import (
    CaptionService,
    DetectionService,
    TamperingService,
    FaceDetectionService,
    SecurityService,
    TimelineService,
    ExportService
)
from backend.middleware.security import rate_limit
from backend.config import UPLOAD_DIR, RESULTS_DIR

logger = logging.getLogger(__name__)

analysis_v2_bp = Blueprint('analysis_v2', __name__, url_prefix='/api/analysis/v2')

# Initialize services
caption_svc = CaptionService()
detection_svc = DetectionService()
tampering_svc = TamperingService()
face_svc = FaceDetectionService()
security_svc = SecurityService()
timeline_svc = TimelineService()
export_svc = ExportService()

# Allowed extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@analysis_v2_bp.route('/status', methods=['GET'])
@rate_limit(requests_per_minute=60)
def get_status():
    """Get service status and availability"""
    return jsonify({
        "status": "success",
        "services": {
            "caption_generation": caption_svc.available,
            "object_detection": detection_svc.available,
            "tampering_detection": tampering_svc.available,
            "face_detection": face_svc.available,
            "security_services": True,
            "export_services": True
        },
        "timestamp": __import__('datetime').datetime.now(
            __import__('datetime').timezone.utc
        ).isoformat()
    }), 200


@analysis_v2_bp.route('/analyze', methods=['POST'])
@rate_limit(requests_per_minute=10)
def analyze_video():
    """
    Comprehensive video analysis endpoint
    
    Request:
        - video (file): Video file to analyze
        - analyze_captions (bool): Enable caption generation
        - analyze_objects (bool): Enable object detection
        - detect_tampering (bool): Enable tampering detection
        - detect_faces (bool): Enable face detection
    
    Response:
        Complete analysis with all results
    """
    try:
        # Validate file
        if 'video' not in request.files:
            return jsonify({"error": "No video file provided"}), 400
        
        file = request.files['video']
        if not file.filename or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400
        
        # Save uploaded file with timestamp prefix to prevent overwrites
        filename = secure_filename(file.filename)
        from datetime import timezone
        timestamp = __import__('datetime').datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        video_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{filename}")
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file.save(video_path)
        
        # Generate file hash
        hash_result = security_svc.hash_file(video_path)
        file_hash = hash_result['hash']
        
        # Determine which analyses to run
        run_captions = request.form.get('analyze_captions', 'true').lower() == 'true'
        run_objects = request.form.get('analyze_objects', 'true').lower() == 'true'
        run_tampering = request.form.get('detect_tampering', 'true').lower() == 'true'
        run_faces = request.form.get('detect_faces', 'true').lower() == 'true'
        
        # Run analyses
        results = {
            "status": "success",
            "video": {
                "filename": filename,
                "path": video_path,
                "hash": file_hash,
                "size": os.path.getsize(video_path)
            },
            "analyses": {}
        }
        
        # Caption generation
        if run_captions:
            logger.info(f"Running caption analysis on {filename}")
            results["analyses"]["captions"] = caption_svc.generate_captions(video_path)
            results["caption_summary"] = results["analyses"]["captions"].get("summary", "")
        
        # Object detection
        if run_objects:
            logger.info(f"Running object detection on {filename}")
            results["analyses"]["objects"] = detection_svc.detect_objects(video_path)
        
        # Tampering detection
        if run_tampering:
            logger.info(f"Running tampering detection on {filename}")
            results["analyses"]["tampering"] = tampering_svc.detect_tampering(video_path)
        
        # Face detection
        if run_faces:
            logger.info(f"Running face detection on {filename}")
            results["analyses"]["faces"] = face_svc.detect_faces(video_path)
        
        # Generate timeline
        logger.info(f"Generating timeline for {filename}")
        timeline_result = timeline_svc.generate_timeline(
            video_path,
            results["analyses"].get("captions", {}),
            results["analyses"].get("objects", {}),
            results["analyses"].get("faces", {}),
            results["analyses"].get("tampering", {})
        )
        results["timeline"] = timeline_result
        
        # Aggregate confidence scores
        results["confidence_scores"] = _aggregate_confidence(results["analyses"])
        
        # Add metadata
        results["duration_seconds"] = timeline_result.get("duration_seconds", 0)
        results["timestamp"] = __import__('datetime').datetime.now(
            __import__('datetime').timezone.utc
        ).isoformat()
        
        return jsonify({"status": "success", "data": results}), 200
    
    except Exception as e:
        logger.error(f"Error in video analysis: {e}", exc_info=True)
        return jsonify({"status": "error", "error": str(e)}), 500


@analysis_v2_bp.route('/export/json', methods=['POST'])
@rate_limit(requests_per_minute=30)
def export_json():
    """Export analysis results as JSON"""
    try:
        data = request.get_json(silent=True) or {}
        result = export_svc.export_json(data)
        
        if result["status"] == "success":
            return send_file(
                result["output_path"],
                as_attachment=True,
                download_name=f"analysis_report_{__import__('time').time()}.json"
            )
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error exporting JSON: {e}")
        return jsonify({"error": str(e)}), 500


@analysis_v2_bp.route('/export/pdf', methods=['POST'])
@rate_limit(requests_per_minute=20)
def export_pdf():
    """Export analysis results as PDF"""
    try:
        data = request.get_json(silent=True) or {}
        result = export_svc.export_pdf(data)
        
        if result["status"] == "success":
            return send_file(
                result["output_path"],
                as_attachment=True,
                download_name=f"analysis_report_{__import__('time').time()}.pdf"
            )
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error exporting PDF: {e}")
        return jsonify({"error": str(e)}), 500


@analysis_v2_bp.route('/blur-faces', methods=['POST'])
@rate_limit(requests_per_minute=5)
def blur_faces():
    """Blur detected faces in video for privacy"""
    try:
        if 'video' not in request.files:
            return jsonify({"error": "No video file provided"}), 400
        
        file = request.files['video']
        if not file.filename or not allowed_file(file.filename):
            return jsonify({"error": "Invalid file type"}), 400
        
        # Save input file
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_DIR, filename)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file.save(input_path)
        
        # Create output path
        output_filename = f"blurred_{filename}"
        output_path = os.path.join(RESULTS_DIR, output_filename)
        os.makedirs(RESULTS_DIR, exist_ok=True)
        
        # Blur faces
        result = face_svc.blur_faces(input_path, output_path)
        
        if result["status"] == "success":
            return jsonify({
                "status": "success",
                "output_path": output_path,
                "download_url": f"/results/{output_filename}",
                "faces_blurred": result["faces_blurred"],
                "frames_processed": result["frames_processed"]
            }), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.error(f"Error blurring faces: {e}")
        return jsonify({"error": str(e)}), 500


@analysis_v2_bp.route('/verify-integrity', methods=['POST'])
@rate_limit(requests_per_minute=20)
def verify_integrity():
    """Verify video integrity using hash verification"""
    try:
        data = request.get_json(silent=True) or {}
        file_path = data.get("file_path")
        expected_hash = data.get("hash")
        algorithm = data.get("algorithm", "sha256")
        
        if not file_path or not expected_hash:
            return jsonify({"error": "Missing required parameters"}), 400
        
        is_valid = security_svc.verify_hash(file_path, expected_hash, algorithm)
        
        return jsonify({
            "status": "success",
            "valid": is_valid,
            "file_path": file_path,
            "algorithm": algorithm
        }), 200
    
    except Exception as e:
        logger.error(f"Error verifying integrity: {e}")
        return jsonify({"error": str(e)}), 500


def _aggregate_confidence(analyses):
    """Aggregate confidence scores from all analyses"""
    scores = {}
    
    # Caption confidence
    if "captions" in analyses and analyses["captions"].get("status") == "success":
        scores["captions"] = analyses["captions"].get("confidence_average", 0.8)
    
    # Object detection confidence
    if "objects" in analyses and analyses["objects"].get("status") == "success":
        scores["objects"] = 0.85  # Default confidence
    
    # Tampering detection confidence
    if "tampering" in analyses and analyses["tampering"].get("status") == "success":
        scores["tampering"] = 1 - analyses["tampering"].get("overall_risk", 0)
    
    # Face detection confidence
    if "faces" in analyses and analyses["faces"].get("status") == "success":
        scores["faces"] = 0.95  # Haar cascade confidence
    
    # Calculate overall confidence
    if scores:
        scores["overall"] = sum(scores.values()) / len(scores)
    else:
        scores["overall"] = 0.0
    
    return scores
