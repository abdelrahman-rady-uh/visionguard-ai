# QUICK REFERENCE CARD
## Multi-Provider Video Analysis System

---

## 🚀 QUICK START (5 minutes)

### Local Development
```powershell
# Windows
.\start_system.ps1

# macOS/Linux
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && python app.py
```

### Access Points
- Dashboard: http://localhost:8080/analysis
- API: http://localhost:8080/api/analysis/
- Status: http://localhost:8080/api/analysis/status

---

## 📌 KEY ENDPOINTS

| Method | Endpoint | Purpose | Rate Limit |
|--------|----------|---------|-----------|
| GET | `/api/analysis/status` | Check providers | 60/min |
| POST | `/api/analysis/analyze/file` | Upload & analyze | 10/min |
| GET | `/api/analysis/results/{id}` | Get results | 30/min |
| POST | `/api/analysis/compare` | Compare videos | 5/min |

---

## 🔧 CONFIGURATION

### Environment Variables
```bash
FLASK_ENV=production              # development or production
FLASK_DEBUG=False                 # Enable/disable debug
SECRET_KEY=<32+ chars>           # Secret key
HUGGINGFACE_API_KEY=hf_xxx       # HuggingFace token
PORT=8080                        # Server port
UPLOAD_DIR=uploads               # Upload directory
RESULTS_DIR=results              # Results directory
LOG_PATH=logs                    # Log directory
```

### Files
- **Config:** `backend/config.py`
- **Environment:** `.env` or `.env.production`
- **Gunicorn:** `gunicorn_config.py`
- **Logging:** `backend/utils/logging_config.py`

---

## 📂 DIRECTORY STRUCTURE

```
backend/
├── services/
│   ├── providers/          # Provider adapters
│   ├── aggregator.py       # Results aggregation
│   └── multi_provider.py   # Orchestration
├── routes/
│   └── analysis.py         # API endpoints
├── middleware/
│   └── security.py         # Rate limiting, validation
└── utils/
    └── logging_config.py   # Logging setup

frontend/
├── analysis_dashboard.html # Main dashboard
└── styles.css             # Dashboard styles

database/
├── app.db                 # SQLite database
└── schema.sql             # Database schema

logs/
├── app_*.log              # Application logs
├── errors_*.log           # Error logs
└── analysis_*.log         # Analysis results
```

---

## 🧪 TESTING

### Run All Tests
```bash
python test_system.py http://localhost:8080
```

### Test Specific Endpoint
```bash
# Provider status
curl http://localhost:8080/api/analysis/status

# Upload video
curl -F "video=@test.mp4" http://localhost:8080/api/analysis/analyze/file

# Get results
curl http://localhost:8080/api/analysis/results/video_id
```

---

## 🚨 TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| Port in use | Change PORT env var |
| Providers not available | Check API keys, network |
| Out of memory | Reduce frame sampling |
| Slow analysis | Check CPU usage, increase timeout |
| Database locked | Delete `database/app.db` and reinit |
| Import errors | Run `pip install -r requirements.txt` |

### Check Logs
```bash
# Windows
type logs\app_*.log

# macOS/Linux
tail -f logs/app_*.log
```

---

## 📦 DEPLOYMENT

### Render Backend
1. Push to GitHub
2. Go to render.com
3. Create web service
4. Set environment variables
5. Deploy

**URL:** https://your-app.onrender.com

### Netlify Frontend
1. Edit `analysis_dashboard.html` with backend URL
2. Go to netlify.com
3. Connect GitHub repo
4. Deploy

**URL:** https://your-site.netlify.app

---

## 🔐 SECURITY CHECKLIST

- [ ] API keys in `.env` file
- [ ] `.env` in `.gitignore`
- [ ] Rate limiting enabled
- [ ] Security headers present
- [ ] HTTPS enforced (production)
- [ ] No hardcoded secrets
- [ ] Input validation active
- [ ] Error messages sanitized

---

## 📊 API RESPONSE FORMAT

### Success
```json
{
  "status": "success",
  "data": { /* results */ },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error
```json
{
  "status": "error",
  "error": "Error description",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 🎯 PROVIDERS

| Provider | Type | Input | Output |
|----------|------|-------|--------|
| HuggingFace | Local | Video | Caption, Quality |
| OpenCV | Local | Video | Face count, Frames |
| Deepfake | Local | Video | Probability, Score |

**Status Check:**
```bash
curl http://localhost:8080/api/analysis/status
```

---

## 📈 PERFORMANCE TIPS

1. **Reduce frame sampling** - Analyze fewer frames
2. **Use result caching** - Avoid re-processing
3. **Scale workers** - Increase Gunicorn workers
4. **Use PostgreSQL** - Better than SQLite
5. **Enable Redis** - Cache results
6. **Use CDN** - For static assets
7. **Monitor logs** - Catch slow operations

---

## 💾 DATABASE

### Initialize
```bash
python -c "from backend.database import Database; Database().init_db()"
```

### Backup
```bash
cp database/app.db database/app.db.backup
```

### Reset
```bash
rm database/app.db
python -c "from backend.database import Database; Database().init_db()"
```

---

## 📝 LOGGING LEVELS

```python
import logging

# Configure
logging.basicConfig(level=logging.DEBUG)

# Levels
logging.DEBUG      # Detailed info for debugging
logging.INFO       # Confirmation things working
logging.WARNING    # Something unexpected
logging.ERROR      # Error occurred
logging.CRITICAL   # Serious error
```

---

## 🔌 API RATE LIMITS

| Endpoint | Limit | Retry After |
|----------|-------|-------------|
| status | 60/min | 60s |
| analyze/file | 10/min | 60s |
| results | 30/min | 60s |
| compare | 5/min | 60s |

**Headers:**
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 28
```

---

## 🎨 DASHBOARD FEATURES

- ✅ Drag-and-drop upload
- ✅ Real-time progress
- ✅ Provider status
- ✅ Confidence bars
- ✅ Anomaly alerts
- ✅ Responsive design
- ✅ Error handling
- ✅ Result export (future)

---

## 🌐 ENVIRONMENT-SPECIFIC SETTINGS

### Development
```bash
FLASK_ENV=development
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
RATE_LIMIT_ENABLED=False  # Optional
```

### Production
```bash
FLASK_ENV=production
FLASK_DEBUG=False
LOG_LEVEL=INFO
RATE_LIMIT_ENABLED=True
SECURE_COOKIE=True
```

---

## 📚 DOCUMENTATION FILES

- `PRODUCTION_GUIDE.md` - Full production guide
- `DEPLOYMENT_CHECKLIST.md` - Deployment steps
- `API_DOCUMENTATION.md` - API reference
- `SYSTEM_SUMMARY.md` - System overview
- `README.md` - Project overview
- `QUICK_REFERENCE.md` - This file!

---

## 🆘 EMERGENCY PROCEDURES

### Server Crash
1. Check logs: `tail -f logs/app_*.log`
2. Stop server: Ctrl+C
3. Fix issue
4. Restart: `python app.py`

### Database Corruption
1. Backup existing: `cp database/app.db database/app.db.corrupt`
2. Reinitialize: `python -c "from backend.database import Database; Database().init_db()"`
3. Restore if needed: `cp database/app.db.corrupt database/app.db`

### Out of Disk Space
1. Clean old uploads: `rm -rf uploads/*.runtime`
2. Clear logs: `rm logs/archive/*.log`
3. Consider PostgreSQL for production

### High CPU Usage
1. Check current analysis: `ps aux | grep python`
2. Reduce workers in gunicorn_config.py
3. Implement request queuing
4. Scale horizontally on Render

---

## 🎓 QUICK API EXAMPLES

### JavaScript
```javascript
const formData = new FormData();
formData.append('video', videoFile);

fetch('/api/analysis/analyze/file', {
  method: 'POST',
  body: formData
}).then(r => r.json());
```

### Python
```python
import requests

r = requests.post(
  'http://localhost:8080/api/analysis/analyze/file',
  files={'video': open('video.mp4', 'rb')}
)
print(r.json())
```

### cURL
```bash
curl -X POST \
  -F "video=@video.mp4" \
  http://localhost:8080/api/analysis/analyze/file
```

---

## ⏱️ TIMEOUTS

| Operation | Timeout | Unit |
|-----------|---------|------|
| Video analysis | 300 | seconds |
| Frame extraction | 60 | seconds |
| API request | 30 | seconds |
| Database query | 10 | seconds |

---

## 💡 USEFUL COMMANDS

```bash
# Check Python version
python --version

# List installed packages
pip list | grep Flask

# Run tests
python -m pytest tests/

# Format code
black backend/

# Lint code
flake8 backend/

# Check syntax
python -m py_compile backend/**/*.py

# Start production server
gunicorn --config gunicorn_config.py backend.app:app

# Monitor logs
tail -f logs/app_*.log | grep ERROR

# Check disk usage
du -sh logs/ uploads/ results/
```

---

## 🔄 CONTINUOUS IMPROVEMENT

- [ ] Monitor error logs daily
- [ ] Update dependencies monthly
- [ ] Review performance metrics
- [ ] Test disaster recovery
- [ ] Update documentation
- [ ] Gather user feedback
- [ ] Plan enhancements
- [ ] Security audit

---

## 📞 CONTACTS

- **Issues:** GitHub Issues
- **Documentation:** PRODUCTION_GUIDE.md
- **API Help:** API_DOCUMENTATION.md
- **Deployment:** DEPLOYMENT_CHECKLIST.md

---

**Last Updated:** April 18, 2026
**Version:** 1.0.0
**Status:** ✅ Production Ready
