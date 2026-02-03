# RunPod Pod Deployment Guide

## Overview
This guide deploys the CogVideoX worker as an HTTP API inside a RunPod Pod (NOT serverless).

## Architecture
- **Pod**: Long-running GPU instance with HTTP API on port 8001
- **Backend**: Calls Pod HTTP endpoints instead of RunPod serverless
- **Storage**: All caches/temp files use `/workspace` (persistent)

---

## Step 1: Create RunPod Pod

1. Go to https://www.runpod.io/console/pods
2. Click "Deploy"
3. Select GPU: **RTX 4090** (or RTX 3090)
4. Select Template: **RunPod Pytorch 2.1**
5. Container Disk: **50 GB**
6. Volume: **100 GB** (persistent storage)
7. Expose HTTP Ports: **8001**
8. Deploy Pod

---

## Step 2: Bootstrap the Worker

SSH into your Pod:

```bash
# Copy bootstrap script
cd /workspace
curl -O https://raw.githubusercontent.com/nanichwdry/videoexpressai/main/workers/video_worker/bootstrap.sh
chmod +x bootstrap.sh

# Set environment variables (REQUIRED)
export R2_BUCKET=your-bucket-videoexpress-outputs
export R2_PUBLIC_BASE_URL=https://pub-your-id.r2.dev
export AWS_ACCESS_KEY_ID=your-r2-access-key
export AWS_SECRET_ACCESS_KEY=your-r2-secret-key
export AWS_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
export AWS_REGION=auto

# Run bootstrap
./bootstrap.sh
```

The script will:
- Install git, ffmpeg, python3
- Clone the repo
- Create venv
- Install dependencies
- Start uvicorn on 0.0.0.0:8001

---

## Step 3: Get Pod URL

In RunPod console, find your Pod's **HTTP Service URL**:
```
https://your-pod-id-8001.proxy.runpod.net
```

---

## Step 4: Configure Backend

Update `backend/.env`:

```bash
VIDEO_WORKER_BASE_URL=https://your-pod-id-8001.proxy.runpod.net

# Keep existing R2 credentials
R2_BUCKET=your-bucket-videoexpress-outputs
R2_PUBLIC_BASE_URL=https://pub-your-id.r2.dev
AWS_ACCESS_KEY_ID=your-r2-access-key
AWS_SECRET_ACCESS_KEY=your-r2-secret-key
AWS_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
AWS_REGION=auto
```

---

## Step 5: Test Worker

### Test Health Endpoint
```bash
curl https://your-pod-id-8001.proxy.runpod.net/health
```

Expected response:
```json
{
  "status": "healthy",
  "worker_version": "v9-pod-http",
  "build_id": "v9-20260201-pod",
  "model": "THUDM/CogVideoX-2b"
}
```

### Test Video Generation
```bash
curl -X POST https://your-pod-id-8001.proxy.runpod.net/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A golden retriever puppy playing in snow", "duration": 5}'
```

Expected response:
```json
{
  "job_id": "abc-123-def",
  "status": "queued",
  "message": "Job submitted successfully"
}
```

### Check Job Status
```bash
curl https://your-pod-id-8001.proxy.runpod.net/status/abc-123-def
```

Expected response (completed):
```json
{
  "job_id": "abc-123-def",
  "status": "completed",
  "progress": 100,
  "output_url": "https://pub-your-id.r2.dev/videos/abc-123-def/final.mp4",
  "worker_version": "v9-pod-http",
  "build_id": "v9-20260201-pod"
}
```

---

## Step 6: Update Backend Code

Use the new Pod client in your backend:

```python
from backend.pod_worker_client import submit_video_job, get_job_status

# Submit job
result = await submit_video_job(prompt="A cat on the moon", duration=5)
job_id = result["job_id"]

# Check status
status = await get_job_status(job_id)
if status["status"] == "completed":
    video_url = status["output_url"]
```

---

## Cost Comparison

### Serverless (Old)
- Idle: $0.00/hour
- Active: $0.34/hour (RTX 4090)
- Billed per second

### Pod (New)
- Always running: $0.34/hour (RTX 4090)
- No cold starts
- Faster for frequent use

**Recommendation**: Use Pod if generating >2 videos/hour, otherwise use Serverless.

---

## Troubleshooting

### Worker not starting
```bash
# Check logs
cd /workspace/videoexpressai/workers/video_worker
source venv/bin/activate
python3 api_server.py
```

### Out of disk space
```bash
# Check disk usage
df -h /workspace

# Clean cache
rm -rf /workspace/hf/*
rm -rf /workspace/outputs/*
```

### Model download fails
```bash
# Pre-download model
cd /workspace
python3 -c "from diffusers import CogVideoXPipeline; CogVideoXPipeline.from_pretrained('THUDM/CogVideoX-2b')"
```

---

## Persistence

All data in `/workspace` persists across Pod restarts:
- `/workspace/hf` - Model cache
- `/workspace/torch` - PyTorch cache
- `/workspace/outputs` - Temporary video files
- `/workspace/videoexpressai` - Cloned repo

To update code:
```bash
cd /workspace/videoexpressai
git pull
cd workers/video_worker
source venv/bin/activate
pip install -r requirements.txt
python3 api_server.py
```

---

## Auto-Start on Pod Boot

Create systemd service or use RunPod's startup script:

```bash
# In Pod settings, set "Docker Command":
bash -c "cd /workspace && ./bootstrap.sh"
```

---

## Files Created

1. `workers/video_worker/api_server.py` - FastAPI HTTP server
2. `workers/video_worker/bootstrap.sh` - Pod setup script
3. `backend/pod_worker_client.py` - Backend HTTP client
4. `backend/.env.pod.example` - Environment template

---

## Next Steps

1. Deploy Pod with GPU
2. Run bootstrap script with R2 credentials
3. Update backend `.env` with Pod URL
4. Test end-to-end video generation
5. Monitor costs in RunPod dashboard
