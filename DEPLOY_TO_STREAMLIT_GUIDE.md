# 🎨 Deploy Frontend to Streamlit Cloud - Step by Step

## Prerequisites
- ✅ Backend deployed to Render (get your API URL first!)
- GitHub account with your code
- Streamlit Cloud account (free)

---

## Step 1: Get Your Backend URL

Before deploying frontend, you need your Render backend URL:

```
Example: https://polyglot-ghost-api.onrender.com
```

**Copy this URL - you'll need it in Step 6!**

---

## Step 2: Sign Up / Login to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click **"Sign in"**
3. Choose **"Continue with GitHub"** (recommended)
4. Authorize Streamlit to access your repositories

---

## Step 3: Create New App

1. Once logged in, click **"New app"** button (top right)
2. You'll see the "Deploy an app" form

---

## Step 4: Configure Your App

Fill in these settings:

### Repository Settings
```
Repository: your-username/your-repo-name
(Select from dropdown)

Branch: main
(or your default branch)

Main file path: streamlit_app.py
(This is the file we created)
```

---

## Step 5: App Settings (Optional)

```
App URL: (optional custom subdomain)
Example: polyglot-ghost.streamlit.app

If left empty, Streamlit will generate one for you.
```

---

## Step 6: Add Secrets (IMPORTANT!)

This is where you connect your frontend to your backend!

1. Click **"Advanced settings"** (bottom of form)
2. In the **"Secrets"** section, paste this:

```toml
API_URL = "https://your-render-app.onrender.com"
```

**Replace** `your-render-app` with your actual Render app name!

Example:
```toml
API_URL = "https://polyglot-ghost-api.onrender.com"
```

**Important**: 
- Use TOML format (shown above)
- Include the quotes around the URL
- No trailing slash at the end

---

## Step 7: Deploy!

1. Click **"Deploy!"** button
2. Streamlit will start building your app

### What Happens:
- **Installing dependencies** (2-3 minutes)
- **Starting app** (30 seconds)
- **Live!** Your app is running

You'll see logs showing the deployment progress.

---

## Step 8: Access Your App

Once deployment completes:

1. Your app URL will be shown at the top
2. Example: `https://your-app.streamlit.app`
3. Click the URL to open your app!

---

## Step 9: Test Your Deployment

### Test 1: Check API Connection
1. Open your Streamlit app
2. Look at the sidebar
3. You should see: **"API Status: 🟢 Connected"**

If you see 🔴 Not configured, check your secrets!

### Test 2: Set Baseline
1. Click "Choose file" under "Set Signature"
2. Upload a voice file (use one from your dataset)
3. Click "Set as Signature"
4. Wait 30-60 seconds (first request may be slow - cold start)
5. Should see: "✅ Signature successfully established!"

### Test 3: Analyze Voice
1. Upload another voice file under "Test Voice"
2. Click "Analyze Audio"
3. Should see results with confidence scores!

---

## 🎉 Success! Your App is Live!

Your voice authentication system is now accessible worldwide!

### Your URLs:
- **Frontend**: `https://your-app.streamlit.app`
- **Backend**: `https://your-render-app.onrender.com`

---

## 📊 Streamlit Cloud Features

### View Logs
- Click the hamburger menu (☰) in your app
- Select "Manage app"
- Click "Logs" to see real-time logs

### Manage App
- Update secrets
- Reboot app
- View analytics
- Configure settings

### Share Your App
- Your app is public by default (free tier)
- Share the URL with anyone!
- Upgrade to Teams for private apps ($20/month)

---

## 🆓 Free Tier Details

### What You Get:
- Unlimited public apps
- Automatic HTTPS
- Automatic deployments on git push
- Community support
- 1 GB RAM per app
- No cold starts (always on!)

### Limitations:
- Apps are public (anyone can access)
- Community support only
- Streamlit branding

### Upgrade Options:
- **Teams ($20/month)**: Private apps, password protection, custom domains

---

## 🔧 Troubleshooting

### "API Status: 🔴 Not configured"

**Problem**: Frontend can't connect to backend

**Solutions**:
1. Check secrets are set correctly
2. Verify API_URL format: `API_URL = "https://your-app.onrender.com"`
3. No trailing slash in URL
4. Quotes around URL
5. Reboot app after changing secrets

### "Request timed out"

**Problem**: Backend is cold starting (Render free tier)

**Solutions**:
1. Wait 30-60 seconds
2. Try request again
3. This is normal on first request
4. Upgrade Render to Starter ($7/mo) to eliminate

### "Failed to extract features"

**Problem**: Audio file issue

**Solutions**:
1. Ensure file is WAV format
2. Check file size < 10MB
3. Try different audio file
4. Check backend logs in Render

### App Won't Start

**Problem**: Deployment error

**Solutions**:
1. Check logs in Streamlit Cloud
2. Verify `streamlit_app.py` exists
3. Check `requirements-frontend.txt` is correct
4. Ensure all imports are available

---

## 🔄 Update Your App

### Automatic Updates
Every time you push to GitHub:
1. Streamlit detects the change
2. Automatically redeploys
3. App updates in 2-3 minutes

### Manual Reboot
1. Go to app management
2. Click "Reboot app"
3. App restarts with latest code

---

## 🔒 Update Secrets

If you need to change your API URL:

1. Go to your app
2. Click hamburger menu (☰)
3. Select "Settings"
4. Click "Secrets"
5. Update the API_URL
6. Click "Save"
7. App will automatically reboot

---

## 📝 Quick Reference

### Your Configuration
```
Repository: your-username/your-repo
Branch: main
Main file: streamlit_app.py
Secrets: API_URL = "https://your-render-app.onrender.com"
```

### Your App Features
- Voice enrollment (set baseline)
- Voice authentication
- AI detection
- Confidence scoring
- Risk assessment
- Detailed metrics

---

## 🎯 Testing Checklist

- [ ] App loads without errors
- [ ] API status shows 🟢 Connected
- [ ] Can upload audio files
- [ ] Can set baseline voice
- [ ] Can analyze voice samples
- [ ] Results display correctly
- [ ] Confidence scores show
- [ ] Metrics are accurate

---

## 💡 Tips

### Cold Starts (Render Free Tier)
- First request takes 30-60 seconds
- Show user a message: "Backend starting up..."
- Subsequent requests are fast
- Upgrade Render to eliminate

### Audio Files
- Use WAV format
- Keep files under 10MB
- Mono audio works best
- 16kHz sample rate recommended

### Sharing Your App
- Share the URL directly
- No login required (free tier)
- Works on mobile browsers
- Embed in websites (iframe)

---

## 🌐 Custom Domain (Optional)

### For Custom Domain:
1. Upgrade to Streamlit Teams ($20/month)
2. Go to app settings
3. Add custom domain
4. Update DNS records
5. SSL certificate automatic

Example: `voice-auth.yourdomain.com`

---

## 📞 Need Help?

- **Streamlit Docs**: https://docs.streamlit.io
- **Community Forum**: https://discuss.streamlit.io
- **Status Page**: https://status.streamlit.io

---

## ✅ Deployment Complete!

Congratulations! Your voice authentication system is now live!

### What You've Deployed:
- ✅ Backend API on Render
- ✅ Frontend Dashboard on Streamlit Cloud
- ✅ Connected and working
- ✅ Accessible worldwide

### Your Live URLs:
- **App**: `https://your-app.streamlit.app`
- **API**: `https://your-render-app.onrender.com`
- **API Docs**: `https://your-render-app.onrender.com/docs`

---

## 🎉 You're Done!

Share your app URL and start authenticating voices!

**Total Deployment Time**: ~10 minutes
**Total Cost**: $0/month (free tier)
**Uptime**: 24/7

Your voice authentication system with AI detection is now live! 🎤✨

---

## 📈 Next Steps

1. **Test thoroughly** with different voices
2. **Monitor usage** in dashboards
3. **Gather feedback** from users
4. **Upgrade plans** if needed
5. **Add features** as you grow

Enjoy your deployed app! 🚀
