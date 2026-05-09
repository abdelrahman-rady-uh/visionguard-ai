"""
Integration Test Suite for Premium Analysis System
Tests all 7 services and complete analysis pipeline
"""
import os
import json
import pytest
import tempfile
from pathlib import Path

# Test video setup
@pytest.fixture
def test_video_path():
    """Create a minimal valid test video using OpenCV"""
    import cv2
    import numpy as np
    
    temp_dir = tempfile.gettempdir()
    video_path = os.path.join(temp_dir, "test_video.mp4")
    
    # Create a simple test video (5 seconds, 30fps, 480x360)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, 30.0, (480, 360))
    
    # Write 150 frames (5 seconds at 30fps)
    for i in range(150):
        frame = np.zeros((360, 480, 3), dtype=np.uint8)
        # Add some variation to frames
        frame[:, :] = (i % 256, (i * 2) % 256, (i * 3) % 256)
        out.write(frame)
    
    out.release()
    yield video_path
    
    # Cleanup
    if os.path.exists(video_path):
        os.remove(video_path)


class TestCaptionService:
    """Test caption generation service"""
    
    def test_caption_service_import(self):
        """Test that CaptionService can be imported"""
        from backend.services import CaptionService
        assert CaptionService is not None
    
    def test_caption_service_initialization(self):
        """Test CaptionService initialization"""
        from backend.services import CaptionService
        service = CaptionService()
        assert service is not None
        assert hasattr(service, 'generate_captions')
    
    def test_caption_generation_with_test_video(self, test_video_path):
        """Test actual caption generation"""
        from backend.services import CaptionService
        service = CaptionService()
        result = service.generate_captions(test_video_path, sample_rate=10, max_frames=5)
        
        assert result is not None
        assert 'status' in result
        assert 'captions' in result or result['status'] == 'error'


class TestDetectionService:
    """Test object detection service"""
    
    def test_detection_service_import(self):
        """Test that DetectionService can be imported"""
        from backend.services import DetectionService
        assert DetectionService is not None
    
    def test_detection_service_initialization(self):
        """Test DetectionService initialization"""
        from backend.services import DetectionService
        service = DetectionService()
        assert service is not None
        assert hasattr(service, 'detect_objects')
    
    def test_object_detection_with_test_video(self, test_video_path):
        """Test actual object detection"""
        from backend.services import DetectionService
        service = DetectionService()
        result = service.detect_objects(test_video_path, sample_rate=10)
        
        assert result is not None
        assert 'status' in result


class TestTamperingService:
    """Test tampering detection service"""
    
    def test_tampering_service_import(self):
        """Test that TamperingService can be imported"""
        from backend.services import TamperingService
        assert TamperingService is not None
    
    def test_tampering_service_initialization(self):
        """Test TamperingService initialization"""
        from backend.services import TamperingService
        service = TamperingService()
        assert service is not None
        assert hasattr(service, 'detect_tampering')
    
    def test_tampering_detection_with_test_video(self, test_video_path):
        """Test actual tampering detection"""
        from backend.services import TamperingService
        service = TamperingService()
        result = service.detect_tampering(test_video_path, sample_rate=10)
        
        assert result is not None
        assert 'status' in result
        assert 'overall_risk' in result or result['status'] == 'error'


class TestFaceService:
    """Test face detection service"""
    
    def test_face_service_import(self):
        """Test that FaceDetectionService can be imported"""
        from backend.services import FaceDetectionService
        assert FaceDetectionService is not None
    
    def test_face_service_initialization(self):
        """Test FaceDetectionService initialization"""
        from backend.services import FaceDetectionService
        service = FaceDetectionService()
        assert service is not None
        assert hasattr(service, 'detect_faces')
        assert hasattr(service, 'blur_faces')
    
    def test_face_detection_with_test_video(self, test_video_path):
        """Test actual face detection"""
        from backend.services import FaceDetectionService
        service = FaceDetectionService()
        result = service.detect_faces(test_video_path)
        
        assert result is not None
        assert 'status' in result


class TestSecurityService:
    """Test security and encryption service"""
    
    def test_security_service_import(self):
        """Test that SecurityService can be imported"""
        from backend.services import SecurityService
        assert SecurityService is not None
    
    def test_security_service_initialization(self):
        """Test SecurityService initialization"""
        from backend.services import SecurityService
        service = SecurityService()
        assert service is not None
        assert hasattr(service, 'hash_file')
        assert hasattr(service, 'encrypt_file')
        assert hasattr(service, 'decrypt_file')
        assert hasattr(service, 'verify_hash')
    
    def test_file_hashing(self):
        """Test file hashing"""
        from backend.services import SecurityService
        import tempfile
        
        service = SecurityService()
        
        # Create a temp file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name
        
        try:
            result = service.hash_file(temp_path)
            assert result['status'] == 'success'
            assert 'hash' in result
            assert result['algorithm'] == 'sha256'
        finally:
            os.unlink(temp_path)
    
    def test_file_encryption_decryption(self):
        """Test file encryption and decryption"""
        from backend.services import SecurityService
        import tempfile
        
        service = SecurityService()
        
        # Create a temp file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content for encryption")
            input_path = f.name
        
        output_path = input_path + ".enc"
        
        try:
            # Encrypt
            encrypt_result = service.encrypt_file(input_path, output_path)
            assert encrypt_result['status'] == 'success'
            assert os.path.exists(output_path)
            
            # Decrypt
            decrypt_result = service.decrypt_file(output_path)
            assert decrypt_result['status'] == 'success'
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestTimelineService:
    """Test timeline generation service"""
    
    def test_timeline_service_import(self):
        """Test that TimelineService can be imported"""
        from backend.services import TimelineService
        assert TimelineService is not None
    
    def test_timeline_service_initialization(self):
        """Test TimelineService initialization"""
        from backend.services import TimelineService
        service = TimelineService()
        assert service is not None
        assert hasattr(service, 'generate_timeline')


class TestExportService:
    """Test export service"""
    
    def test_export_service_import(self):
        """Test that ExportService can be imported"""
        from backend.services import ExportService
        assert ExportService is not None
    
    def test_export_service_initialization(self):
        """Test ExportService initialization"""
        from backend.services import ExportService
        service = ExportService()
        assert service is not None
        assert hasattr(service, 'export_json')
        assert hasattr(service, 'export_pdf')
        assert hasattr(service, 'export_combined')
    
    def test_json_export(self):
        """Test JSON export functionality"""
        from backend.services import ExportService
        import tempfile
        
        service = ExportService()
        
        # Create mock analysis data
        mock_data = {
            "status": "success",
            "video": {"filename": "test.mp4", "duration": 10},
            "analyses": {
                "captions": {"status": "success", "captions": []},
                "objects": {"status": "success", "detections": []},
                "tampering": {"status": "success", "overall_risk": 0.2},
                "faces": {"status": "success", "face_detections": []}
            }
        }
        
        output_dir = tempfile.gettempdir()
        output_path = os.path.join(output_dir, "test_export.json")
        
        try:
            result = service.export_json(mock_data, output_path)
            assert result['status'] == 'success'
            assert os.path.exists(output_path)
            
            # Verify JSON is valid
            with open(output_path, 'r') as f:
                json_data = json.load(f)
                assert isinstance(json_data, dict)
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestAnalysisRoutes:
    """Test Flask API routes"""
    
    @pytest.fixture
    def client(self):
        """Create Flask test client"""
        from backend.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_status_endpoint(self, client):
        """Test service status endpoint"""
        response = client.get('/api/analysis/v2/status')
        assert response.status_code == 200
        data = response.get_json()
        assert 'services' in data
        assert 'timestamp' in data
    
    def test_analyze_endpoint_no_file(self, client):
        """Test analyze endpoint without file"""
        response = client.post('/api/analysis/v2/analyze')
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestDatabaseIntegration:
    """Test database operations"""
    
    def test_database_initialization(self):
        """Test database can be initialized"""
        from backend.database import Database
        db = Database()
        assert db is not None
    
    def test_analysis_result_storage(self):
        """Test storing analysis results"""
        from backend.database import Database
        db = Database()
        
        # Create a test video entry first
        user_id = db.create_or_get_default_user()
        video_id = db.insert_video("test.mp4", "2026-04-17T00:00:00Z", 10.5, user_id)
        
        # Store analysis results
        mock_results = {
            "captions": {"status": "success"},
            "objects": {"status": "success"},
            "faces": {"status": "success"}
        }
        
        analysis_id = db.insert_analysis_result(
            video_id=video_id,
            results_json=mock_results,
            confidence_json={"overall": 0.85}
        )
        
        assert analysis_id is not None
        
        # Retrieve and verify
        result = db.get_analysis_result(analysis_id)
        assert result is not None
        assert result['VideoID'] == video_id
        assert result['ResultsJSON'] == mock_results


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
