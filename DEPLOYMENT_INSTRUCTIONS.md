# Deployment Instructions - The Polyglot Ghost Voice Authenticator

## Current Status
Your Docker deployment is fully configured and ready to launch. All files are in place:
- Dockerfile (with curl for health checks)
- docker-compose.yml
- .dockerignore
- .env (with API keys)
- requirements.txt (optimized)
- Application code (backend + frontend)

## Prerequisites Check
1. Docker Desktop must be running
2. Docker Compose is installed (confirmed: v2.39.2)

## Deployment Steps

### Step 1: Start Docker Desktop
Before running any Docker commands, ensure Docker Desktop is running on your Windows machine.

### Step 2: Build the Docker Image
```bash
docker-compose build
```

This will:
- Pull Python 3.11-slim base image
- Install system dependencies (gcc, portaudio, ffmpeg, curl)
- Install Python packages from requirements.txt
- Copy application files
- Configure Streamlit to run on port 8501

Expected build time: 5-10 minutes (depending on internet speed)

### Step 3: Start the Container
```bash
docker-compose up -d
```

The `-d` flag runs it in detached mode (background).

### Step 4: Verify Deployment
```bash
# Check if container is running
docker ps

# View logs
docker-compose logs -f

# Check health status
docker inspect polyglot-ghost --format='{{.State.Health.Status}}'
```

### Step 5: Access the Dashboard
Open your browser and navigate to:
```
http://localhost:8501
```

You should see "The Polyglot Ghost Voice Authenticator" dashboard.

## Testing the Deployment

### Test 1: Enroll a Voice
1. Go to "1. Set Signature (Baseline)" section
2. Upload a voice sample from `dataset/real/` (e.g., `clip_0.wav`)
3. Click "Set as Signature"
4. Verify you see "Signature successfully established!"

### Test 2: Authenticate Same Voice
1. Go to "2. Test Voice" section
2. Upload the same voice file
3. Click "Analyze Audio"
4. Expected result: "IDENTITY MATCH" and "Voice Appears Human"

### Test 3: Test Different Voice
1. Upload a different voice from `dataset/real/`
2. Expected result: "IDENTITY MISMATCH"

### Test 4: Test AI Clone
1. Upload a voice from `dataset/fake/`
2. Expected result: "AI GENERATED VOICE DETECTED"

## Managing the Container

### View Logs
```bash
docker-compose logs -f
```

### Stop the Container
```bash
docker-compose down
```

### Restart the Container
```bash
docker-compose restart
```

### Rebuild After Code Changes
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

### Issue: Port 8501 Already in Use
Edit `docker-compose.yml` and change the port mapping:
```yaml
ports:
  - "8502:8501"  # Use 8502 instead
```

Then access at `http://localhost:8502`

### Issue: Container Exits Immediately
Check logs:
```bash
docker-compose logs
```

Common causes:
- Missing dependencies in requirements.txt
- Syntax errors in Python code
- Port conflicts

### Issue: Health Check Failing
```bash
# Check health status
docker inspect polyglot-ghost --format='{{.State.Health.Status}}'

# View health check logs
docker inspect polyglot-ghost --format='{{range .State.Health.Log}}{{.Output}}{{end}}'
```

### Issue: Audio Processing Errors
Ensure the dataset folder is properly mounted:
```bash
docker exec polyglot-ghost ls -la /app/dataset/real
```

## Performance Notes

### Resource Usage
- CPU: ~2 cores during audio processing
- RAM: ~2-4 GB
- Disk: ~2 GB for image

### Optimization Tips
1. Use smaller audio files (< 30 seconds)
2. Ensure audio is mono, 16kHz sample rate
3. Keep dataset folder organized

## Production Deployment

### Option 1: Cloud Hosting (Recommended)
See `README_DOCKER.md` for detailed instructions on:
- AWS ECS
- Google Cloud Run
- Azure Container Instances
- Heroku

### Option 2: VPS Deployment
1. Push image to Docker Hub:
```bash
docker tag polyglot-ghost yourusername/polyglot-ghost:latest
docker push yourusername/polyglot-ghost:latest
```

2. On your VPS:
```bash
docker pull yourusername/polyglot-ghost:latest
docker run -d -p 8501:8501 \
  -v /path/to/dataset:/app/dataset \
  -v /path/to/.env:/app/.env \
  yourusername/polyglot-ghost:latest
```

### Option 3: Reverse Proxy with HTTPS
Use nginx or Caddy to add HTTPS:

nginx config:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## Security Checklist

- [ ] .env file is not committed to git (already in .gitignore)
- [ ] API keys are stored securely
- [ ] Container runs as non-root user (optional enhancement)
- [ ] HTTPS enabled for production
- [ ] Firewall rules configured
- [ ] Regular security updates

## Next Steps

1. Start Docker Desktop
2. Run `docker-compose build`
3. Run `docker-compose up -d`
4. Access `http://localhost:8501`
5. Test with voice samples from dataset
6. Monitor logs for any issues

## Support

If you encounter issues:
1. Check Docker Desktop is running
2. Review logs: `docker-compose logs`
3. Verify port availability: `netstat -an | findstr 8501`
4. Ensure .env file has valid API keys
5. Check dataset folder permissions

---

Your deployment is ready! Just start Docker Desktop and run the build command.
