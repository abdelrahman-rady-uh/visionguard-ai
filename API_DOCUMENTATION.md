# Multi-Provider Video Analysis API Documentation

## Base URL
- Development: `http://localhost:8080`
- Production: `https://your-render-app.onrender.com`

## Authentication
Currently uses rate limiting by IP address. Future versions will support API tokens.

## Response Format
All responses are JSON with this structure:
```json
{
  "status": "success|error",
  "data": { /* response data */ },
  "timestamp": "2024-01-15T10:30:00Z",
  "error": "error message if applicable"
}
```

---

## Endpoints

### 1. Provider Status
Get status of all available analysis providers.

**Request:**
```http
GET /api/analysis/status
```

**cURL Example:**
```bash
curl -X GET http://localhost:8080/api/analysis/status
```

**Response:**
```json
{
  "status": "success",
  "providers": {
    "HuggingFace": {
      "available": true,
      "name": "HuggingFace",
      "type": "HuggingFaceProvider"
    },
    "OpenCV": {
      "available": true,
      "name": "OpenCV-FaceDetection",
      "type": "OpenCVFaceDetectionProvider"
    },
    "Deepfake": {
      "available": true,
      "name": "DeepfakeDetector",
      "type": "DeepfakeDetectorProvider"
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Rate Limit:** 60 requests/minute

---

### 2. Analyze Uploaded Video
Upload and analyze a video file with all providers.

**Request:**
```http
POST /api/analysis/analyze/file
Content-Type: multipart/form-data

- video: <video file>
- video_id: <unique identifier (optional)>
```

**cURL Example:**
```bash
curl -X POST http://localhost:8080/api/analysis/analyze/file \
  -F "video=@path/to/video.mp4" \
  -F "video_id=my-video-001"
```

**Python Example:**
```python
import requests

with open('video.mp4', 'rb') as f:
    files = {'video': f}
    data = {'video_id': 'test-video-001'}
    
    response = requests.post(
        'http://localhost:8080/api/analysis/analyze/file',
        files=files,
        data=data
    )
    
    result = response.json()
    print(result['data'])
```

**Response (Success):**
```json
{
  "status": "success",
  "data": {
    "video_id": "my-video-001",
    "video_url": "/api/videos/20240115_103000_video.mp4",
    "analysis_timestamp": "2024-01-15T10:30:45Z",
    "overall_confidence": 0.87,
    "providers": [
      {
        "name": "HuggingFace",
        "provider": "HuggingFace",
        "result": "A group of people having a conversation in an office setting",
        "confidence": 0.92,
        "metadata": {
          "captions": [
            "A man and woman talking",
            "People in business attire"
          ]
        },
        "available": true,
        "timestamp": "2024-01-15T10:30:42Z"
      },
      {
        "name": "OpenCV",
        "provider": "OpenCV-FaceDetection",
        "result": "Faces detected in 8 sampled frames, max 2 in single frame",
        "confidence": 0.85,
        "metadata": {
          "frames_with_faces": 8,
          "max_faces_in_frame": 2,
          "total_frames_analyzed": 150
        },
        "available": true,
        "timestamp": "2024-01-15T10:30:44Z"
      },
      {
        "name": "Deepfake",
        "provider": "DeepfakeDetector",
        "result": "Deepfake probability: 8.50%",
        "confidence": 0.78,
        "metadata": {
          "deepfake_probability": 0.085,
          "consistency_score": 0.915,
          "frames_analyzed": 10
        },
        "available": true,
        "timestamp": "2024-01-15T10:30:43Z"
      }
    ],
    "errors": [],
    "anomalies": [],
    "provider_count": 3,
    "successful_analyses": 3,
    "failed_analyses": 0
  },
  "video_url": "/api/videos/20240115_103000_video.mp4",
  "results_file": "results/analysis_my-video-001.json",
  "timestamp": "2024-01-15T10:30:45Z"
}
```

**Response (Error):**
```json
{
  "status": "error",
  "error": "File type not allowed. Allowed: mp4, avi, mov, mkv, webm"
}
```

**Allowed File Types:** MP4, AVI, MOV, MKV, WEBM
**Max File Size:** 1GB
**Rate Limit:** 10 requests/minute
**Timeout:** 300 seconds (5 minutes)

---

### 3. Get Analysis Results
Retrieve previously saved analysis results.

**Request:**
```http
GET /api/analysis/results/{video_id}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8080/api/analysis/results/my-video-001
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "video_id": "my-video-001",
    "overall_confidence": 0.87,
    "providers": [
      /* ... provider results ... */
    ],
    "anomalies": []
  }
}
```

**Rate Limit:** 30 requests/minute

---

### 4. Compare Multiple Videos
Compare analysis results from multiple videos to identify patterns or inconsistencies.

**Request:**
```http
POST /api/analysis/compare
Content-Type: application/json

{
  "video_ids": ["video-001", "video-002", "video-003"]
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8080/api/analysis/compare \
  -H "Content-Type: application/json" \
  -d '{
    "video_ids": ["video-001", "video-002", "video-003"]
  }'
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "count": 3,
    "analyses": [
      {
        "video_id": "video-001",
        "overall_confidence": 0.87,
        /* ... analysis data ... */
      },
      {
        "video_id": "video-002",
        "overall_confidence": 0.92,
        /* ... analysis data ... */
      },
      {
        "video_id": "video-003",
        "overall_confidence": 0.79,
        /* ... analysis data ... */
      }
    ]
  }
}
```

**Rate Limit:** 5 requests/minute

---

## Analyze with Existing File Path
Analyze a video from an existing file path on the server.

**Request:**
```http
POST /api/analysis/analyze
Content-Type: application/json

{
  "video_path": "/path/to/video.mp4",
  "video_id": "my-video-001",
  "video_url": "https://example.com/video.mp4"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8080/api/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "video_path": "/uploads/video.mp4",
    "video_id": "my-video",
    "video_url": "https://example.com/video.mp4"
  }'
```

**Rate Limit:** 10 requests/minute

---

## Error Handling

### Common Error Codes

| Status | Message | Cause |
|--------|---------|-------|
| 400 | No file provided | Missing video in multipart form |
| 400 | File type not allowed | Invalid video format |
| 400 | File is too large | File exceeds 1GB limit |
| 400 | Missing required fields | Missing video_path or video_id |
| 404 | Video file not found | Path doesn't exist |
| 404 | Analysis results not found | No results saved for video_id |
| 429 | Rate limit exceeded | Too many requests |
| 500 | Internal server error | Provider error (check logs) |

### Error Response Example:
```json
{
  "status": "error",
  "error": "File is too large. Maximum size: 1.0GB"
}
```

---

## Rate Limiting

The API uses IP-based rate limiting:

| Endpoint | Limit |
|----------|-------|
| GET /api/analysis/status | 60 req/min |
| POST /api/analysis/analyze/file | 10 req/min |
| POST /api/analysis/analyze | 10 req/min |
| GET /api/analysis/results/{id} | 30 req/min |
| POST /api/analysis/compare | 5 req/min |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 28
```

When limit exceeded:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

---

## Response Fields Explained

### overall_confidence (0-1)
Average confidence from all successful providers. Higher = more reliable.

### provider_count
Total number of providers attempted (including failed ones).

### successful_analyses
Number of providers that completed successfully.

### failed_analyses
Number of providers that failed.

### anomalies
Array of detected inconsistencies (e.g., conflicting provider results).

### metadata
Provider-specific additional data. Varies by provider.

---

## Provider Details

### HuggingFace Provider
- **Capabilities:** Video captioning, quality assessment
- **Models:** Salesforce/blip-image-captioning-base
- **Returns:** 
  - `result`: Generated caption text
  - `metadata`: Frame captions and quality scores

### OpenCV Face Detection
- **Capabilities:** Face detection in frames
- **Algorithm:** Haar Cascade Classifier
- **Returns:**
  - `result`: Summary of face detection results
  - `metadata.frames_with_faces`: Number of frames with faces
  - `metadata.max_faces_in_frame`: Maximum faces in any frame

### Deepfake Detection
- **Capabilities:** Deepfake probability detection
- **Method:** Frame consistency analysis
- **Returns:**
  - `result`: Deepfake probability percentage
  - `metadata.deepfake_probability`: Numeric score (0-1)
  - `metadata.consistency_score`: Frame consistency (0-1)

---

## Usage Examples

### JavaScript/Fetch
```javascript
async function analyzeVideo(videoFile) {
  const formData = new FormData();
  formData.append('video', videoFile);
  formData.append('video_id', `video_${Date.now()}`);

  const response = await fetch('/api/analysis/analyze/file', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  console.log(result.data);
}
```

### Python/Requests
```python
import requests
import json

def analyze_video(video_path):
    with open(video_path, 'rb') as f:
        files = {'video': f}
        data = {'video_id': f'video_{int(time.time())}'}
        
        response = requests.post(
            'http://localhost:8080/api/analysis/analyze/file',
            files=files,
            data=data,
            timeout=300
        )
        
        return response.json()

result = analyze_video('sample.mp4')
print(json.dumps(result, indent=2))
```

### Node.js/Fetch
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function analyzeVideo(videoPath) {
  const form = new FormData();
  form.append('video', fs.createReadStream(videoPath));
  form.append('video_id', `video_${Date.now()}`);

  const response = await axios.post(
    'http://localhost:8080/api/analysis/analyze/file',
    form,
    { headers: form.getHeaders(), timeout: 300000 }
  );

  return response.data;
}
```

---

## WebHooks (Future)
Coming soon: Real-time analysis updates via WebSocket/SSE.

## API Versioning
Current version: v1 (implied in `/api/analysis/`)
Future versions will use `/api/v2/` for breaking changes.

---

## Support
- **Issues:** Check logs in `logs/` directory
- **Status:** Visit `/api/analysis/status`
- **Docs:** See PRODUCTION_GUIDE.md
