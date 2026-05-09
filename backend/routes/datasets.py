from flask import Blueprint, jsonify, request
import json
import os

datasets_bp = Blueprint("datasets", __name__)

METADATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "celeb-df-v2-metadata.json")

@datasets_bp.route("/api/datasets", methods=["GET"])
def get_datasets():
    """List all available datasets for AI Detection."""
    datasets = []
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Try to extract size from distribution
                size = "Unknown"
                if "distribution" in data and len(data["distribution"]) > 0:
                    for dist in data["distribution"]:
                        if "contentSize" in dist:
                            size = dist["contentSize"]
                            break
                            
                datasets.append({
                    "id": "celeb-df-v2",
                    "name": data.get("name", "Celeb DF (v2)"),
                    "description": data.get("description", ""),
                    "url": data.get("url", ""),
                    "keywords": data.get("keywords", []),
                    "size": size
                })
        except Exception as e:
            pass # ignore errors, return empty list
            
    # Can also return a mock dataset to show variety
    datasets.append({
        "id": "faceforensics-plus",
        "name": "FaceForensics++",
        "description": "FaceForensics++ is a forensics dataset consisting of 1000 original video sequences that have been manipulated with four automated face manipulation methods: Deepfakes, Face2Face, FaceSwap and NeuralTextures.",
        "url": "https://github.com/ondyari/FaceForensics",
        "keywords": ["face manipulation", "deepfakes", "video data"],
        "size": "Multiple GBs"
    })
            
    return jsonify({"datasets": datasets})

@datasets_bp.route("/api/datasets/<dataset_id>", methods=["GET"])
def get_dataset(dataset_id):
    """Get metadata for a specific dataset."""
    if dataset_id == "celeb-df-v2":
        if os.path.exists(METADATA_PATH):
            try:
                with open(METADATA_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return jsonify(data)
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    if dataset_id == "faceforensics-plus":
        return jsonify({
            "name": "FaceForensics++",
            "description": "FaceForensics++ is a forensics dataset consisting of 1000 original video sequences that have been manipulated with four automated face manipulation methods.",
            "url": "https://github.com/ondyari/FaceForensics"
        })
        
    return jsonify({"error": "Dataset not found"}), 404

@datasets_bp.route("/api/datasets/<dataset_id>/sync", methods=["POST"])
def sync_dataset(dataset_id):
    """Mock endpoint to trigger a sync/download of the dataset to the local AI model."""
    if dataset_id in ["celeb-df-v2", "faceforensics-plus"]:
        return jsonify({
            "status": "success",
            "message": f"Dataset {dataset_id} synchronization started. This will run in the background to update AI detection models.",
            "job_id": f"job_sync_{dataset_id}_123"
        })
    return jsonify({"error": "Dataset not found"}), 404
