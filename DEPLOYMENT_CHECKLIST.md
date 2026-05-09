# DEPLOYMENT CHECKLIST & QUICK START GUIDE

## Pre-Deployment Checklist

### 1. Local Testing ✓
- [ ] Code all tests pass: `pytest tests/`
- [ ] No syntax errors: `python -m py_compile backend/**/*.py`
- [ ] All dependencies installed: `pip list | grep -E "Flask|torch|transformers"`
- [ ] Environment variables configured in `.env`
- [ ] Database initialized
- [ ] Sample video analysis works

### 2. Security Audit ✓
- [ ] API keys not hardcoded (check `.env`, `.gitignore`)
- [ ] Secret key is 32+ characters
- [ ] CORS origins restricted
- [ ] Rate limiting enabled
- [ ] Input validation active
- [ ] Security headers configured

### 3. Configuration Review ✓
- [ ] `requirements.txt` is up to date
- [ ] `gunicorn_config.py` has correct settings
- [ ] `render.yaml` configured for Render
- [ ] `netlify.toml` configured for Netlify
- [ ] Environment variables documented
- [ ] Database path is correct

### 4. File Structure ✓
- [ ] All provider files exist (`providers/*.py`)
- [ ] Aggregator module present (`services/aggregator.py`)
- [ ] Multi-provider module present (`services/multi_provider.py`)
- [ ] Routes registered (`routes/analysis.py`)
- [ ] Middleware implemented (`middleware/security.py`)
- [ ] Frontend dashboard available (`frontend/analysis_dashboard.html`)

---

## Backend Deployment (Render)

### Step 1: Prepare Repository
```bash
# Ensure git is initialized
git init
git add .
git commit -m "Initial commit: Multi-provider video analysis system"

# Push to GitHub (required for Render)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

### Step 2: Create Render Account & Service
1. Go to https://render.com
2. Sign up / Log in
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Select the repository

### Step 3: Configure Render Service
```
Service Name: video-analysis-api
Runtime: Python 3.11
Build Command: pip install -r requirements.txt
Start Command: gunicorn --workers 4 --bind 0.0.0.0:$PORT 'backend.app:app' --timeout 120
```

### Step 4: Set Environment Variables (Render Dashboard)
```
FLASK_ENV                    production
FLASK_DEBUG                  False
SECRET_KEY                   <generate: python -c "import secrets; print(secrets.token_hex(32))">
HUGGINGFACE_API_KEY          hf_<your_token>
DEEPFAKE_API_KEY             <optional>
UPLOAD_DIR                   /tmp/uploads
RESULTS_DIR                  /tmp/results
LOG_PATH                     /tmp/logs
PYTHONUNBUFFERED             1
PORT                         8080
HOST                         0.0.0.0
```

### Step 5: Deploy
- Click "Create Web Service"
- Render automatically deploys on every push
- Monitor logs in Render dashboard
- Copy your service URL: `https://your-app-name.onrender.com`

### Step 6: Test Backend
```bash
curl https://your-app-name.onrender.com/api/analysis/status
```

---

## Frontend Deployment (Netlify)

### Step 1: Update API Endpoint
Edit `frontend/analysis_dashboard.html`:
```javascript
// Line ~3 of script section
const API_BASE_URL = "https://your-render-app.onrender.com";
```

### Step 2: Create Netlify Account
1. Go to https://netlify.com
2. Sign up / Log in
3. Click "Add new site" → "Import an existing project"
4. Connect GitHub

### Step 3: Configure Netlify Deployment
```
Build Command: echo 'Frontend ready to deploy'
Publish Directory: frontend/
```

### Step 4: Set Environment Variables (Netlify Dashboard)
```
REACT_APP_API_URL    https://your-render-app.onrender.com
```

### Step 5: Deploy
- Connect repository
- Netlify automatically deploys on every push
- Copy your site URL: `https://your-site.netlify.app`

### Step 6: Test Frontend
- Open https://your-site.netlify.app/analysis
- Upload a test video
- Verify all providers execute

---

## Quick Start for Local Development

### 1. First Time Setup
```bash
cd "eea omar"

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.production .env  # Windows
cp .env.production .env   # macOS/Linux

# Edit .env and set:
# - FLASK_ENV=development
# - SECRET_KEY=dev-key-12345678901234567890123456
# - HUGGINGFACE_API_KEY=your_token (optional for local)

# Initialize database
python -c "from backend.database import Database; Database().init_db()"

# Create test video directory
mkdir test_videos
```

### 2. Run Server
```bash
python app.py
```

Server starts at: `http://127.0.0.1:5000`

### 3. Access Dashboard
- Analysis Dashboard: http://127.0.0.1:5000/analysis
- Original Dashboard: http://127.0.0.1:5000/dashboard
- Welcome Page: http://127.0.0.1:5000/

### 4. Test System
```bash
python test_system.py http://localhost:8080
```

---

## Testing Checklist

### Unit Tests
```bash
pytest backend/services/test_providers.py -v
pytest backend/services/test_aggregator.py -v
pytest backend/routes/test_analysis.py -v
```

### Integration Tests
```bash
# Start server in one terminal
python app.py

# In another terminal, run system tests
python test_system.py http://localhost:8080
```

### Manual Testing Steps
1. **Upload Video**
   - Click upload area
   - Select MP4 file (under 1GB)
   - Wait for analysis

2. **Verify Providers**
   - Check all providers show in results
   - Verify confidence scores (0-100%)
   - Check metadata is present

3. **Check Errors**
   - Review error messages if any
   - Check logs for detailed errors
   - Verify system didn't crash

4. **Test Rate Limiting**
   - Upload 15 videos rapidly
   - Verify 429 error after limit exceeded

5. **Test Security**
   - Upload invalid file types (blocked?)
   - Check security headers present
   - Verify API keys not exposed

---

## Troubleshooting

### Server Won't Start
```bash
# Check logs
type logs\app_*.log  # Windows
tail -f logs/app_*.log  # macOS/Linux

# Common issues:
# - Port 8080 in use: Change PORT env var
# - Missing dependencies: pip install -r requirements.txt
# - Database locked: Delete database/app.db and reinit
```

### Providers Not Available
```bash
# Check provider status
curl http://localhost:8080/api/analysis/status

# Common issues:
# - HuggingFace: No API key or network issue
# - OpenCV: Library not installed (pip install opencv-python)
# - Deepfake: Transformers not installed
```

### Analysis Times Out
- Reduce video size/length
- Increase timeout in `gunicorn_config.py`
- Check CPU usage
- Enable result caching

### Memory Issues
- Reduce frame sampling in providers
- Use PostgreSQL instead of SQLite
- Implement Redis caching
- Disable unnecessary providers

---

## Performance Optimization

### For Production:
1. **Database**: Switch to PostgreSQL
   ```bash
   pip install psycopg2-binary
   # Update DATABASE_URL
   ```

2. **Caching**: Add Redis
   ```bash
   pip install redis
   # Cache results for 24 hours
   ```

3. **Async Processing**: Use Celery
   ```bash
   pip install celery
   # Process videos in background
   ```

4. **CDN**: Use Cloudinary for files
   ```bash
   pip install cloudinary
   # Set CLOUDINARY_* env vars
   ```

---

## Monitoring & Maintenance

### Check System Health
```bash
# Provider status
curl https://your-api.onrender.com/api/analysis/status

# Check logs (Render)
# Dashboard → Logs

# Check usage (Netlify)
# Site settings → Logs
```

### Regular Tasks
- [ ] Review error logs weekly
- [ ] Update dependencies monthly: `pip list --outdated`
- [ ] Check disk usage (Render free tier limited)
- [ ] Monitor API usage for spikes
- [ ] Backup database

### Scaling
- **Render**: Use paid tier for persistent storage
- **Netlify**: Pro tier for better build minutes
- **Database**: Migrate to Supabase/Railway for PostgreSQL
- **Storage**: Use Cloudinary for unlimited file storage

---

## Rollback Procedure

If deployment fails:

### Render
1. Go to Render Dashboard
2. Select your service
3. Click "Deployments"
4. Find previous working deployment
5. Click "Redeploy"

### Netlify
1. Go to Netlify Dashboard
2. Select your site
3. Click "Deploys"
4. Find previous working deploy
5. Click "Restore"

### Manual Rollback
```bash
git log --oneline
git revert <commit-hash>
git push origin main
# Service auto-redeploys
```

---

## Support & Resources

- **Documentation**: Read PRODUCTION_GUIDE.md
- **API Docs**: Test with curl or Postman
- **Logs**: Check logs/ directory
- **Issues**: Search GitHub issues
- **Render Docs**: https://render.com/docs
- **Netlify Docs**: https://docs.netlify.com

---

## Success Criteria

✓ System is deployed and accessible
✓ All providers are available
✓ Videos can be uploaded and analyzed
✓ Results are returned quickly (< 5 min)
✓ Security headers are present
✓ Rate limiting is working
✓ Logs are being collected
✓ No unhandled errors in logs
✓ Frontend and backend communicate
✓ System is secure

---

**Deployment Date**: ___________
**Deployed By**: ___________
**Backend URL**: ___________
**Frontend URL**: ___________
