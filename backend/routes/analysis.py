"""API routes for multi-provider video analysis."""
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
import os
import logging

from backend.services.multi_provider import MultiProviderAnalyzer
from backend.middleware.security import rate_limit, InputValidator, SecurityHeaders
from backend.config import UPLOAD_DIR, RESULTS_DIR, ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")

# Initialize multi-provider analyzer
analyzer = MultiProviderAnalyzer()


@analysis_bp.before_request
def apply_security_headers():
    """Apply security headers to all responses."""
    pass


@analysis_bp.after_request
def add_security_headers(response):
    """Add security headers to response."""
    return SecurityHeaders.add_security_headers(response)


@analysis_bp.route("/status", methods=["GET"])
@rate_limit(requests_per_minute=60)
def get_provider_status():
    """
    Get status of all available providers.
    
    Returns:
        JSON with provider availability and status
    """
    try:
        status = analyzer.get_provider_status()
        
        return jsonify({
            "status": "success",
            "providers": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"Error getting provider status: {e}")
        return jsonify({
            "error": str(e),
            "status": "error",
        }), 500


@analysis_bp.route("/analyze", methods=["POST"])
@rate_limit(requests_per_minute=10)
def analyze_video():
    """
    Analyze video using all available providers.
    
    Request body:
        {
            "video_path": "path/to/video.mp4",
            "video_id": "unique-id",
            "video_url": "https://example.com/video.mp4"
        }
    
    Returns:
        JSON with aggregated analysis results
    """
    try:
        data = request.get_json(silent=True) or {}
        
        # Validate input
        is_valid, error_msg = InputValidator.validate_json_input(
            data,
            required_fields=["video_path", "video_id", "video_url"]
        )
        
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        video_path = data["video_path"]
        video_id = data["video_id"]
        video_url = data["video_url"]

        # Validate file exists
        if not os.path.exists(video_path):
            return jsonify({"error": f"Video file not found: {video_path}"}), 404

        logger.info(f"Starting analysis for video {video_id}")

        # Run multi-provider analysis
        results = analyzer.analyze(video_path, video_id, video_url)

        return jsonify({
            "status": "success",
            "data": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"Error analyzing video: {e}")
        return jsonify({
            "error": str(e),
            "status": "error",
        }), 500


@analysis_bp.route("/analyze/file", methods=["POST"])
@rate_limit(requests_per_minute=10)
def analyze_uploaded_file():
    """
    Analyze uploaded video file.
    
    Multipart form data:
        - video: Video file
        - video_id: Unique identifier for video
    
    Returns:
        JSON with aggregated analysis results
    """
    try:
        # Validate file upload
        if "video" not in request.files:
            return jsonify({"error": "No video file provided"}), 400

        file = request.files["video"]
        video_id = request.form.get("video_id", f"video_{int(datetime.now().timestamp())}")

        # Validate file
        is_valid, error_msg = InputValidator.validate_video_upload(file)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        filepath = os.path.join(UPLOAD_DIR, f"{timestamp}_{filename}")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file.save(filepath)

        logger.info(f"File saved: {filepath}")

        # Generate video URL (for local development)
        video_url = f"/api/videos/{timestamp}_{filename}"

        # Run analysis
        results = analyzer.analyze(filepath, video_id, video_url)

        # Save results
        os.makedirs(RESULTS_DIR, exist_ok=True)
        results_path = os.path.join(RESULTS_DIR, f"analysis_{video_id}.json")
        
        import json
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Analysis results saved: {results_path}")

        return jsonify({
            "status": "success",
            "data": results,
            "video_url": video_url,
            "results_file": results_path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"Error analyzing uploaded file: {e}")
        return jsonify({
            "error": str(e),
            "status": "error",
        }), 500


@analysis_bp.route("/results/<video_id>", methods=["GET"])
@rate_limit(requests_per_minute=30)
def get_analysis_results(video_id):
    """
    Get previously saved analysis results.
    
    Args:
        video_id: Video identifier
    
    Returns:
        JSON with analysis results
    """
    try:
        results_file = os.path.join(RESULTS_DIR, f"analysis_{video_id}.json")

        if not os.path.exists(results_file):
            return jsonify({"error": "Analysis results not found"}), 404

        import json
        with open(results_file, "r") as f:
            results = json.load(f)

        return jsonify({
            "status": "success",
            "data": results,
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving results: {e}")
        return jsonify({
            "error": str(e),
            "status": "error",
        }), 500


@analysis_bp.route("/compare", methods=["POST"])
@rate_limit(requests_per_minute=5)
def compare_analyses():
    """
    Compare analysis results from multiple videos.
    
    Request body:
        {
            "video_ids": ["id1", "id2", "id3"]
        }
    
    Returns:
        Comparative analysis
    """
    try:
        data = request.get_json(silent=True) or {}
        video_ids = data.get("video_ids", [])

        if not video_ids or len(video_ids) < 2:
            return jsonify({
                "error": "At least 2 video IDs required for comparison"
            }), 400

        comparisons = []

        for video_id in video_ids:
            results_file = os.path.join(RESULTS_DIR, f"analysis_{video_id}.json")
            
            if os.path.exists(results_file):
                import json
                with open(results_file, "r") as f:
                    results = json.load(f)
                    comparisons.append(results)

        if not comparisons:
            return jsonify({"error": "No analysis results found"}), 404

        return jsonify({
            "status": "success",
            "data": {
                "count": len(comparisons),
                "analyses": comparisons,
            },
        }), 200

    except Exception as e:
        logger.error(f"Error comparing analyses: {e}")
        return jsonify({
            "error": str(e),
            "status": "error",
        }), 500
