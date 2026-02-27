# Quick Start Deployment Guide

## Architecture Overview

```
┌─────────────────────────────────────┐
│   Streamlit Cloud (Frontend)       │
│   https://app.streamlit.app        │
│   - User Interface                  │
│   - Audio Recording/Upload          │
│   - Results Display                 │
└──────────────┬──────────────────────┘
               │ HTTP API Calls
               ▼
┌─────────────────────────────────────┐
│   Render (Backend API)              │
│   https://api.onrender.com          │
│   - FastAPI Server                  │
│   - Audio Processing                │
│   - Feature Extraction              │
│   - Voice Analysis                  │
└─────────────────────────────────────┘
```

## Why This Architecture?

- **Streamlit Cloud**: Free, optimized for Streamlit apps, no cold starts
- **Render**: Free tier for backend API, easy Python deployment
- **Separation**: Frontend and backend can scale independently

## Step-by-Step Deployment

### Step 1: Push Code to GitHub

```bash
# Add all deployment files
git add .
git commit -m "Add Render + Streamlit Cloud deployment"
git push origin main
```

### Step 2: Deploy Backend to Render (5 minutes)

1. Go to https://dashboard.render.com
2. Sign up/login with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: `polyglot-ghost-api`
   - **Region**: Oregon
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements-backend.txt`
   - **Start Command**: `cd backend && uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
6. Click "Create Web Service"
7. Wait 5-10 minutes for deployment
8. **SAVE YOUR API URL**: `https://polyglot-ghost-api.onrender.com`

### Step 3: Deploy Frontend to Streamlit Cloud (3 minutes)

1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Configure:
   - **Repository**: your-repo-name
   - **Branch**: main
   - **Main file path**: `streamlit_app.py`
5. Click "Advanced settings"
6. Add secrets (paste your Render API URL):
   ```toml
   API_URL = "https://polyglot-ghost-api.onrender.com"
   ```
7. Click "Deploy"
8. Wait 2-3 minutes
9. **YOUR APP IS LIVE**: `https://your-app.streamlit.app`

## Testing Your Deployment

### Test 1: Check Backend Health
```bash
curl https://your-render-app.onrender.com/health
```

Expected: `{"status": "healthy"}`

### Test 2: Open Frontend
1. Go to your Streamlit Cloud URL
2. Check API status in sidebar (should show 🟢 Connected)

### Test 3: Enroll Voice
1. Upload a voice from `dataset/real/clip_0.wav`
2. Click "Set as Signature"
3. Wait 30-60 seconds (first request may be slow due to cold start)
4. Should see "Signature successfully established!"

### Test 4: Verify Voice
1. Upload the same voice file
2. Click "Analyze Audio"
3. Should see "IDENTITY MATCH" and "Voice Appears Human"

### Test 5: Test Different Voice
1. Upload a different voice from `dataset/real/`
2. Should see "IDENTITY MISMATCH"

### Test 6: Test AI Clone
1. Upload a voice from `dataset/fake/`
2. Should see "AI GENERATED VOICE DETECTED"

## Important Notes

### Cold Starts (Render Free Tier)
- Backend spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- Show user a message: "Backend starting up, please wait..."
- Subsequent requests are fast

### File Size Limits
- Streamlit Cloud: 200MB per file
- Render Free: 100MB request limit
- Recommended: Keep audio files under 10MB

### Free Tier Limits
- **Render**: 750 hours/month (enough for 24/7)
- **Streamlit Cloud**: Unlimited public apps
- **Total Cost**: $0/month

## Troubleshooting

### "API Status: 🔴 Not configured"
- Check secrets in Streamlit Cloud settings
- Verify API_URL is set correctly
- Redeploy frontend

### "Request timed out"
- Backend is cold starting (wait 30-60 seconds)
- Try again
- If persists, check Render logs

### "Error connecting to API"
- Check backend is running on Render
- Test health endpoint: `curl https://your-api.onrender.com/health`
- Check CORS settings in `backend/api.py`

### "Failed to extract features"
- Verify audio file is valid WAV format
- Check file isn't corrupted
- Try a different audio file

## Upgrading for Production

### Remove Cold Starts ($7/month)
- Upgrade Render to Starter plan
- Backend stays always-on
- No more 30-60 second delays

### Private App ($20/month)
- Upgrade Streamlit Cloud to Teams
- Password-protected apps
- Custom domains

### Total Production Cost
- Render Starter: $7/month
- Streamlit Teams: $20/month
- **Total**: $27/month

## File Checklist

Make sure these files exist:
- ✅ `backend/api.py` - FastAPI backend
- ✅ `streamlit_app.py` - Streamlit frontend
- ✅ `requirements-backend.txt` - Backend dependencies
- ✅ `requirements-frontend.txt` - Frontend dependencies
- ✅ `render.yaml` - Render configuration (optional)
- ✅ `.streamlit/config.toml` - Streamlit theme
- ✅ All backend modules in `backend/` folder

## Next Steps

1. ✅ Deploy backend to Render
2. ✅ Get API URL
3. ✅ Deploy frontend to Streamlit Cloud
4. ✅ Add API_URL to secrets
5. ✅ Test end-to-end
6. 🎉 Share your app!

## Support Resources

- **Render Docs**: https://render.com/docs
- **Streamlit Docs**: https://docs.streamlit.io
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Render Community**: https://community.render.com
- **Streamlit Community**: https://discuss.streamlit.io

## Your URLs

After deployment, save these:
- **Backend API**: `https://polyglot-ghost-api.onrender.com`
- **Frontend App**: `https://your-app.streamlit.app`
- **API Docs**: `https://polyglot-ghost-api.onrender.com/docs`

---

## Deployment Complete! 🎉

Your voice authentication system is now live and accessible from anywhere!

**Total Time**: ~10 minutes
**Total Cost**: $0/month (free tier)
**Uptime**: 24/7 (with cold starts on free tier)

Share your app URL with users and start authenticating voices!
