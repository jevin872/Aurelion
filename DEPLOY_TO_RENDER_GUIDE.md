# 🚀 Deploy to Render - Step by Step Guide

## Prerequisites
- GitHub account
- Your code pushed to GitHub
- Render account (free - sign up at https://render.com)

---

## Step 1: Push Your Code to GitHub

```bash
# Add all files
git add .

# Commit
git commit -m "Ready for Render deployment"

# Push to GitHub
git push origin main
```

**Wait for push to complete before proceeding.**

---

## Step 2: Sign Up / Login to Render

1. Go to https://render.com
2. Click "Get Started" or "Sign In"
3. Choose "Sign in with GitHub" (recommended)
4. Authorize Render to access your GitHub repositories

---

## Step 3: Create New Web Service

1. Once logged in, you'll see the Render Dashboard
2. Click the **"New +"** button (top right)
3. Select **"Web Service"** from the dropdown

![New Web Service](https://render.com/docs/images/new-web-service.png)

---

## Step 4: Connect Your Repository

### Option A: If Repository is Listed
1. Find your repository in the list
2. Click **"Connect"** next to it

### Option B: If Repository Not Listed
1. Click **"Configure account"** link
2. Grant Render access to your repository
3. Return to Render and refresh
4. Click **"Connect"** next to your repository

---

## Step 5: Configure Your Service

Fill in these settings:

### Basic Settings
```
Name: polyglot-ghost-api
(or any name you prefer - this will be in your URL)

Region: Oregon (US West)
(or choose closest to you)

Branch: main
(or your default branch)

Root Directory: (leave empty)
```

### Build & Deploy Settings
```
Runtime: Python 3

Build Command:
pip install -r requirements-backend.txt

Start Command:
cd backend && uvicorn api:app --host 0.0.0.0 --port $PORT
```

**Important**: Copy these commands exactly as shown!

### Instance Type
```
Plan: Free
(You can upgrade later if needed)
```

---

## Step 6: Add Environment Variables (Optional)

Scroll down to **"Environment Variables"** section:

Click **"Add Environment Variable"** and add:

```
Key: PYTHON_VERSION
Value: 3.11.0
```

If you're using ElevenLabs (optional):
```
Key: ELEVENLABS_API_KEY
Value: your_api_key_here
```

If you're using Hugging Face (optional):
```
Key: HF_TOKEN
Value: your_token_here
```

---

## Step 7: Deploy!

1. Scroll to the bottom
2. Click **"Create Web Service"**
3. Render will start building your application

### What Happens Next:
- **Building**: Installing dependencies (5-8 minutes)
- **Deploying**: Starting your service (1-2 minutes)
- **Live**: Your API is running!

You'll see logs in real-time showing the build progress.

---

## Step 8: Get Your API URL

Once deployment is complete:

1. Look at the top of the page
2. You'll see your URL: `https://polyglot-ghost-api.onrender.com`
3. **Copy this URL** - you'll need it for the frontend!

---

## Step 9: Test Your Deployment

### Test 1: Health Check
Open in browser or use curl:
```
https://your-app-name.onrender.com/health
```

Expected response:
```json
{"status":"healthy"}
```

### Test 2: API Documentation
Open in browser:
```
https://your-app-name.onrender.com/docs
```

You should see the FastAPI interactive documentation!

---

## Step 10: Save Your URL

**IMPORTANT**: Save your Render URL! You'll need it for:
- Streamlit Cloud frontend deployment
- Testing your API
- Sharing with others

Example URL format:
```
https://polyglot-ghost-api.onrender.com
```

---

## 🎉 Success! Your Backend is Live!

Your API is now accessible worldwide at your Render URL.

### What's Next?

1. **Test your API** using the `/docs` endpoint
2. **Deploy Frontend** to Streamlit Cloud (see next guide)
3. **Connect Frontend to Backend** using your Render URL

---

## 📊 Render Dashboard Features

### View Logs
- Click "Logs" tab to see real-time logs
- Useful for debugging

### Monitor Performance
- Click "Metrics" tab
- See CPU, memory, and request metrics

### Manage Settings
- Click "Settings" tab
- Update environment variables
- Change instance type
- Configure custom domains

---

## 🆓 Free Tier Details

### What You Get:
- 750 hours/month (enough for 24/7)
- Automatic HTTPS
- Automatic deployments on git push
- Health checks
- Logs and metrics

### Limitations:
- Service spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds (cold start)
- 512 MB RAM
- 0.1 CPU

### Upgrade Options:
- **Starter ($7/month)**: No spin-down, faster, 512 MB RAM
- **Standard ($25/month)**: More resources, better performance

---

## 🔧 Troubleshooting

### Build Fails

**Error**: "Could not find requirements-backend.txt"
**Solution**: Make sure file is in root directory and pushed to GitHub

**Error**: "No module named 'X'"
**Solution**: Add missing package to requirements-backend.txt

### Service Won't Start

**Error**: "Port already in use"
**Solution**: Make sure start command uses `$PORT` variable

**Error**: "Module not found"
**Solution**: Check that all backend files are in `backend/` folder

### Service Crashes

1. Check logs in Render dashboard
2. Look for Python errors
3. Test locally first: `python backend/api.py`

---

## 📝 Quick Reference

### Your Configuration
```yaml
Name: polyglot-ghost-api
Runtime: Python 3
Build: pip install -r requirements-backend.txt
Start: cd backend && uvicorn api:app --host 0.0.0.0 --port $PORT
Plan: Free
```

### Your URLs
```
API Base: https://your-app.onrender.com
Health: https://your-app.onrender.com/health
Docs: https://your-app.onrender.com/docs
Set Baseline: POST https://your-app.onrender.com/api/set-baseline
Analyze: POST https://your-app.onrender.com/api/analyze
```

---

## 🎯 Next Steps

After your backend is deployed:

1. ✅ Backend deployed to Render
2. ⏭️ Deploy frontend to Streamlit Cloud
3. ⏭️ Connect frontend to backend
4. ⏭️ Test end-to-end

**Continue to**: [Deploy Frontend to Streamlit Cloud](DEPLOY_TO_STREAMLIT_GUIDE.md)

---

## 💡 Tips

### Automatic Deployments
- Every time you push to GitHub, Render automatically redeploys
- Great for continuous deployment!

### Custom Domain
- Upgrade to paid plan
- Add your custom domain in Settings
- Point your DNS to Render

### Environment Variables
- Never commit API keys to GitHub
- Always use environment variables
- Update them in Render dashboard

---

## 📞 Need Help?

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Status Page**: https://status.render.com

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Repository connected
- [ ] Service configured
- [ ] Environment variables added
- [ ] Service deployed
- [ ] Health check passed
- [ ] API URL saved
- [ ] Ready for frontend deployment

---

**Your backend API is now live and ready to use!** 🎉

Save your Render URL and proceed to deploy the frontend to Streamlit Cloud.
