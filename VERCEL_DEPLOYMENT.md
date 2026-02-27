# Vercel Frontend Deployment Guide

## Overview
Deploy the Streamlit frontend to Vercel to provide the user interface for voice authentication.

## Prerequisites
- GitHub account
- Vercel account (free tier available at https://vercel.com)
- Backend deployed on Render (get the API URL first)
- Code pushed to GitHub repository

## Files Created
- `frontend/dashboard_api.py` - Modified dashboard that calls backend API
- `requirements-frontend.txt` - Frontend dependencies
- `vercel.json` - Vercel configuration

## Important Note About Streamlit on Vercel

Streamlit is designed for long-running processes and doesn't work well with Vercel's serverless architecture. Here are your options:

### Option 1: Deploy Streamlit to Streamlit Cloud (Recommended)

Streamlit Cloud is the official hosting platform for Streamlit apps and is FREE.

#### Steps:

1. **Create streamlit_app.py in root**
   ```bash
   # Copy the API-enabled dashboard
   cp frontend/dashboard_api.py streamlit_app.py
   ```

2. **Create requirements.txt for Streamlit Cloud**
   ```bash
   cp requirements-frontend.txt requirements.txt
   ```

3. **Push to GitHub**
   ```bash
   git add streamlit_app.py requirements.txt
   git commit -m "Add Streamlit Cloud deployment"
   git push origin main
   ```

4. **Deploy on Streamlit Cloud**
   - Go to https://share.streamlit.io
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file: `streamlit_app.py`
   - Click "Deploy"

5. **Add Environment Variable**
   - In Streamlit Cloud dashboard, go to app settings
   - Add secret:
     ```toml
     API_URL = "https://your-render-app.onrender.com"
     ```

6. **Access Your App**
   - Your app will be at: `https://your-app.streamlit.app`

### Option 2: Deploy Frontend to Render (Alternative)

Since Streamlit works better on traditional hosting, you can deploy both backend and frontend to Render:

1. **Create render-frontend.yaml**
   ```yaml
   services:
     - type: web
       name: polyglot-ghost-frontend
       env: python
       region: oregon
       plan: free
       buildCommand: pip install -r requirements-frontend.txt
       startCommand: streamlit run frontend/dashboard_api.py --server.port=$PORT --server.address=0.0.0.0
       envVars:
         - key: API_URL
           value: https://your-backend-app.onrender.com
   ```

2. **Deploy on Render**
   - Follow same steps as backend deployment
   - Use the configuration above

### Option 3: Create React Frontend for Vercel (Advanced)

If you want to use Vercel, you'll need to create a React/Next.js frontend instead of Streamlit.

## Recommended Deployment Architecture

```
┌─────────────────────────────────────┐
│   Streamlit Cloud (Frontend)       │
│   https://app.streamlit.app        │
│   - User Interface                  │
│   - Audio Recording                 │
│   - Results Display                 │
└──────────────┬──────────────────────┘
               │ HTTP Requests
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

## Deployment Steps (Streamlit Cloud)

### 1. Prepare Files

Create `streamlit_app.py` in project root:
```python
import os
import streamlit as st
import requests

# Get API URL from environment or secrets
API_URL = os.getenv("API_URL", st.secrets.get("API_URL", "http://localhost:8000"))

st.set_page_config(page_title="Polyglot Ghost Voice Auth", layout="wide")

st.title("The Polyglot Ghost Voice Authenticator")
st.markdown("Authenticate whether the speaking voice matches the signature voice AND detect if it's an AI clone.")

# Initialize session state
if 'baseline_set' not in st.session_state:
    st.session_state.baseline_set = False

# Sidebar for controls
with st.sidebar:
    st.header("Settings")
    st.markdown(f"**API Status:** {'🟢 Connected' if API_URL else '🔴 Not configured'}")
    
    strictness = st.selectbox(
        "Matching Strictness", 
        ["strict", "normal", "relaxed", "very_relaxed"], 
        index=1,
        help="Strict: High security, low tolerance. Very Relaxed: High tolerance for sickness/microphone differences"
    )
    
    if st.button("Reset Baseline"):
        try:
            response = requests.post(f"{API_URL}/api/reset", timeout=60)
            if response.status_code == 200:
                st.session_state.baseline_set = False
                st.success("Baseline reset successfully!")
            else:
                st.error("Failed to reset baseline")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Two-column layout
col1, col2 = st.columns(2)

with col1:
    st.header("1. Set Signature (Baseline)")
    st.markdown("Record or upload your voice to establish an identity signature.")
    
    baseline_audio = st.audio_input("Record Baseline Voice")
    baseline_upload = st.file_uploader("Or Upload Baseline (.wav)", type=['wav'], key="base_upload")
    
    baseline_to_use = baseline_audio if baseline_audio else baseline_upload
    
    if baseline_to_use is not None:
        st.audio(baseline_to_use)
        if st.button("Set as Signature"):
            with st.spinner("Extracting signature features... (may take 30-60s on first request)"):
                try:
                    files = {"file": ("baseline.wav", baseline_to_use, "audio/wav")}
                    response = requests.post(f"{API_URL}/api/set-baseline", files=files, timeout=120)
                    
                    if response.status_code == 200:
                        st.session_state.baseline_set = True
                        st.success("Signature successfully established!")
                    else:
                        error_detail = response.json().get("detail", "Unknown error")
                        st.error(f"Failed: {error_detail}")
                except requests.Timeout:
                    st.warning("Request timed out. The backend may be starting up (cold start). Please try again in 30 seconds.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

with col2:
    st.header("2. Test Voice")
    st.markdown("Record or upload the test voice to verify against the signature.")
    
    test_audio = st.audio_input("Record Test Voice")
    test_upload = st.file_uploader("Or Upload Test (.wav)", type=['wav'], key="test_upload")
    
    test_to_use = test_audio if test_audio else test_upload
    
    if test_to_use is not None:
        st.audio(test_to_use)
        
        if st.button("Analyze Audio"):
            if not st.session_state.baseline_set:
                st.warning("Please set a Signature Voice in Step 1 first!")
            else:
                with st.spinner("Analyzing..."):
                    try:
                        files = {"file": ("test.wav", test_to_use, "audio/wav")}
                        response = requests.post(
                            f"{API_URL}/api/analyze",
                            files=files,
                            params={"strictness": strictness},
                            timeout=120
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            st.divider()
                            
                            if result["is_ai_generated"]:
                                st.error("AI GENERATED VOICE DETECTED")
                            else:
                                st.success("Voice Appears Human")
                            
                            if result["is_match"]:
                                st.success("IDENTITY MATCH: This matches the Signature Voice!")
                            else:
                                st.warning("IDENTITY MISMATCH: This is a different person!")
                            
                            st.markdown("### Analysis Metrics")
                            m_col1, m_col2, m_col3 = st.columns(3)
                            m_col1.metric("Confidence Score", f"{result['confidence']:.1%}")
                            m_col2.metric("Identity Deviation", f"{result['deviation']:.1%}")
                            m_col3.metric("Risk Level", result['risk_level'])
                            
                            with st.expander("Detailed Feature Breakdown"):
                                st.json({
                                    "Verdict": result['verdict'],
                                    "MFCC Similarity": f"{result['mfcc_similarity']:.1%}",
                                    "Spectral Similarity": f"{result['spectral_similarity']:.1%}",
                                    "Phase Similarity": f"{result['phase_similarity']:.1%}"
                                })
                        else:
                            error_detail = response.json().get("detail", "Unknown error")
                            st.error(f"Analysis failed: {error_detail}")
                    except requests.Timeout:
                        st.warning("Request timed out. Please try again.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

st.markdown("---")
st.markdown("Backend API on Render | Frontend on Streamlit Cloud")
```

### 2. Create .streamlit/config.toml

```bash
mkdir -p .streamlit
```

Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false
```

### 3. Push to GitHub

```bash
git add streamlit_app.py .streamlit/ requirements-frontend.txt
git commit -m "Add Streamlit Cloud deployment"
git push origin main
```

### 4. Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect GitHub repository
4. Configure:
   - **Repository**: your-repo
   - **Branch**: main
   - **Main file path**: streamlit_app.py
5. Click "Advanced settings"
6. Add secrets:
   ```toml
   API_URL = "https://your-render-backend.onrender.com"
   ```
7. Click "Deploy"

### 5. Test Your Deployment

1. Wait for deployment (2-3 minutes)
2. Access your app at: `https://your-app.streamlit.app`
3. Test baseline setting
4. Test voice analysis
5. Verify API connection

## Troubleshooting

### API Connection Errors
- Verify API_URL in secrets is correct
- Check backend is running on Render
- Test backend health: `curl https://your-api.onrender.com/health`

### Cold Start Delays
- First request may take 30-60 seconds (Render free tier)
- Show user a message about cold starts
- Increase timeout to 120 seconds

### Audio Upload Fails
- Check file format (must be WAV)
- Verify file size (< 10MB recommended)
- Test with sample files from dataset

### CORS Errors
- Update backend CORS settings with your Streamlit Cloud URL
- Redeploy backend after CORS changes

## Cost Breakdown

### Free Tier (Recommended for Testing)
- **Streamlit Cloud**: Free (unlimited public apps)
- **Render Backend**: Free (750 hours/month)
- **Total**: $0/month

### Production Tier
- **Streamlit Cloud**: Free (or $20/month for private apps)
- **Render Backend**: $7/month (Starter plan, no cold starts)
- **Total**: $7-27/month

## Next Steps

1. Deploy backend to Render first
2. Get backend API URL
3. Deploy frontend to Streamlit Cloud
4. Configure API_URL in secrets
5. Test end-to-end functionality
6. Share your app URL!

## Support

- Streamlit Docs: https://docs.streamlit.io
- Streamlit Community: https://discuss.streamlit.io
- Render Docs: https://render.com/docs

---

Your app will be live at: `https://your-app.streamlit.app`
