# Docker Deployment Guide - The Polyglot Ghost

## Quick Start

### Prerequisites
- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)

### 1. Build and Run

```bash
# Build the Docker image
docker-compose build

# Start the container
docker-compose up -d

# View logs
docker-compose logs -f
```

The dashboard will be available at: **http://localhost:8501**

### 2. Stop the Container

```bash
docker-compose down
```

## Manual Docker Commands

### Build Image
```bash
docker build -t polyglot-ghost .
```

### Run Container
```bash
docker run -d \
  --name polyglot-ghost \
  -p 8501:8501 \
  -v $(pwd)/dataset:/app/dataset \
  -v $(pwd)/.env:/app/.env \
  polyglot-ghost
```

### View Logs
```bash
docker logs -f polyglot-ghost
```

### Stop Container
```bash
docker stop polyglot-ghost
docker rm polyglot-ghost
```

## Environment Variables

Create a `.env` file with your API keys:

```env
ELEVENLABS_API_KEY=your_api_key_here
```

## Volumes

The following directories are mounted as volumes:
- `./dataset` - Voice samples (persisted)
- `./.env` - Environment variables

## Port Mapping

- **8501** - Streamlit dashboard (HTTP)

## Health Check

The container includes a health check that monitors the Streamlit service:
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Start period: 40 seconds

Check health status:
```bash
docker ps
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs

# Rebuild without cache
docker-compose build --no-cache
```

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8502:8501"  # Use 8502 instead
```

### Permission issues
```bash
# Fix dataset permissions
chmod -R 755 dataset/
```

## Production Deployment

### Using Docker Hub

1. **Tag and push image:**
```bash
docker tag polyglot-ghost yourusername/polyglot-ghost:latest
docker push yourusername/polyglot-ghost:latest
```

2. **Pull and run on server:**
```bash
docker pull yourusername/polyglot-ghost:latest
docker run -d -p 8501:8501 yourusername/polyglot-ghost:latest
```

### Using Cloud Platforms

#### AWS ECS
```bash
# Push to ECR
aws ecr get-login-password --region region | docker login --username AWS --password-stdin account.dkr.ecr.region.amazonaws.com
docker tag polyglot-ghost:latest account.dkr.ecr.region.amazonaws.com/polyglot-ghost:latest
docker push account.dkr.ecr.region.amazonaws.com/polyglot-ghost:latest
```

#### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/polyglot-ghost
gcloud run deploy polyglot-ghost --image gcr.io/PROJECT-ID/polyglot-ghost --platform managed
```

#### Azure Container Instances
```bash
# Create container
az container create \
  --resource-group myResourceGroup \
  --name polyglot-ghost \
  --image polyglot-ghost:latest \
  --dns-name-label polyglot-ghost \
  --ports 8501
```

#### Heroku
```bash
# Login to Heroku Container Registry
heroku container:login

# Push and release
heroku container:push web -a your-app-name
heroku container:release web -a your-app-name
```

## Resource Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 2 GB

**Recommended:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 5 GB

## Security Notes

1. **Never commit `.env` file** with real API keys
2. **Use secrets management** in production (AWS Secrets Manager, etc.)
3. **Enable HTTPS** with reverse proxy (nginx, Caddy)
4. **Restrict network access** with firewall rules
5. **Regular updates** - rebuild image with latest dependencies

## Monitoring

### Container Stats
```bash
docker stats polyglot-ghost
```

### Resource Usage
```bash
docker exec polyglot-ghost ps aux
docker exec polyglot-ghost df -h
```

## Backup

### Backup Dataset
```bash
docker cp polyglot-ghost:/app/dataset ./dataset_backup
```

### Restore Dataset
```bash
docker cp ./dataset_backup polyglot-ghost:/app/dataset
```

## Support

For issues and questions:
- Check logs: `docker-compose logs`
- Verify health: `docker ps`
- Restart: `docker-compose restart`
