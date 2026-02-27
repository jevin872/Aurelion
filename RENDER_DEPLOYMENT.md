# Render Backend Deployment Guide

## Overview
Deploy the FastAPI backend to Render for voice authentication processing.

## Prerequisites
- GitHub account
- Render account (free tier available at https://render.com)
- Code pushed to GitHub repository

## Files Created
- `backend/api.py` - FastAPI application with endpoints
- `requirements-backend.txt` - Backend dependencies
- `render.yaml` - Render configuration (optional, can use dashboard)

## API Endpoints

### GET /
- Health check and API info
- Returns: `{"message": "...", "version": "1.0.0", "status": "running"}`

### GET /health
- Health check endpoint
- Returns: `{"status": "healthy"}`

### POST /api/set-baseline
- Set baseline voice signature
- Body: multipart/form-data with audio file
- Returns: `{"success": true, "message": "..."}`

### POST /api/analyze
- Analyze voice against baseline
- Body: multipart/form-data with audio file
- Query params: `strictness` (strict/normal/relaxed/very_relaxed)
- Returns: Full analysis results with confidence, verdict, etc.

### POST /api/reset
- Reset baseline signature
- Returns: `{"success": true, "message": "..."}`

## Deployment Steps

### Option 1: Using Render Dashboard (Recommended)

1. **Push Code to GitHub**
   ```bash
   git add .
   git commit -m "Add Render backend deployment"
   git push origin main
   ```

2. **Create New Web Service on Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your repository

3. **Configure Service**
   - **Name**: `polyglot-ghost-api`
   - **Region**: Oregon (or closest to you)
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: Python 3
   - **Build Command**: 
     ```bash
     pip install -r requirements-backend.txt
     ```
   - **Start Command**: 
     ```bash
     cd backend && uvicorn api:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: Free

4. **Add Environment Variables**
   - Click "Environment" tab
   - Add variables:
     - `PYTHON_VERSION` = `3.11.0`
     - `ELEVENLABS_API_KEY` = `your_api_key` (optional)
     - `HF_TOKEN` = `your_token` (optional)

5. **Deploy**
   - Click "Create Web Service"
   - Wait 5-10 minutes for build and deployment
   - Your API will be available at: `https://polyglot-ghost-api.onrender.com`

### Option 2: Using render.yaml (Infrastructure as Code)

1. **Push Code with render.yaml**
   ```bash
   git add render.yaml
   git commit -m "Add render.yaml"
   git push origin main
   ```

2. **Create Blueprint on Render**
   - Go to https://dashboard.render.com
   - Click "New +" → "Blueprint"
   - Connect your repository
   - Render will automatically detect `render.yaml`
   - Click "Apply"

3. **Add Environment Variables**
   - Go to your service settings
   - Add the environment variables as listed above

## Testing the Deployment

### Test Health Endpoint
```bash
curl https://your-app.onrender.com/health
```

Expected response:
```json
{"status": "healthy"}
```

### Test Set Baseline
```bash
curl -X POST https://your-app.onrender.com/api/set-baseline \
  -F "file=@dataset/real/clip_0.wav"
```

### Test Analysis
```bash
curl -X POST "https://your-app.onrender.com/api/analyze?strictness=normal" \
  -F "file=@dataset/real/clip_1.wav"
```

## Important Notes

### Free Tier Limitations
- Service spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds (cold start)
- 750 hours/month free (enough for one service running 24/7)

### Cold Start Handling
Add this to your frontend to handle cold starts:
```python
import time
import requests

def call_api_with_retry(url, max_retries=3, timeout=60):
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            return response
        except requests.Timeout:
            if i < max_retries - 1:
                time.sleep(5)
                continue
            raise
```

### CORS Configuration
The API is configured to allow all origins (`allow_origins=["*"]`). For production, update this in `backend/api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-app.vercel.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Monitoring

### View Logs
- Go to your service on Render dashboard
- Click "Logs" tab
- View real-time logs

### Check Metrics
- Click "Metrics" tab
- View CPU, memory, and request metrics

## Troubleshooting

### Build Fails
- Check `requirements-backend.txt` for typos
- Verify Python version compatibility
- Check build logs for specific errors

### Service Won't Start
- Verify start command is correct
- Check that `backend/api.py` exists
- Ensure port binding uses `$PORT` environment variable

### API Returns 500 Errors
- Check logs for Python exceptions
- Verify all backend modules are present
- Test locally first: `cd backend && uvicorn api:app --reload`

### Audio Processing Errors
- Ensure uploaded files are valid WAV format
- Check file size limits (Render free tier: 100MB request limit)
- Verify librosa and soundfile are installed correctly

## Local Testing

Before deploying, test locally:

```bash
# Install dependencies
pip install -r requirements-backend.txt

# Run server
cd backend
uvicorn api:app --reload --port 8000

# Test in browser
open http://localhost:8000
```

## Upgrading to Paid Plan

For production use, consider upgrading:
- **Starter Plan ($7/month)**: No spin-down, faster builds
- **Standard Plan ($25/month)**: More resources, better performance
- **Pro Plan ($85/month)**: High performance, priority support

## Next Steps

1. Deploy backend to Render
2. Note your API URL: `https://your-app.onrender.com`
3. Use this URL in Vercel frontend deployment
4. Test all endpoints
5. Monitor logs for any issues

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- FastAPI Docs: https://fastapi.tiangolo.com

---

Your backend API URL will be: `https://polyglot-ghost-api.onrender.com`

Save this URL for the Vercel frontend deployment!
