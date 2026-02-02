# VideoExpress AI - Deployment Guide

## Architecture Overview

```
Desktop (Electron + React) → VPS (FastAPI) → RunPod (GPU Worker) → S3 Storage
```

---

## 1. VPS Backend Setup (Ubuntu 22.04)

### Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3-pip python3.11-venv

# Install FFmpeg
sudo apt install -y ffmpeg

# Install SQLite
sudo apt install -y sqlite3
```

### Deploy Backend

```bash
# Clone or upload backend folder
cd /opt
mkdir videoexpress-backend
cd videoexpress-backend

# Copy backend files
# (Upload via SCP or git clone)

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
nano .env
```

Edit `.env`:
```
RUNPOD_ENDPOINT=https://api.runpod.ai/v2/YOUR_ENDPOINT_ID
RUNPOD_API_KEY=your_runpod_api_key
S3_BUCKET=your-bucket-name
DB_PATH=/opt/videoexpress-backend/jobs.db
```

### Run Backend

```bash
# Test run
uvicorn main:app --host 0.0.0.0 --port 8000

# Production with systemd
sudo nano /etc/systemd/system/videoexpress.service
```

Add:
```ini
[Unit]
Description=VideoExpress AI Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/videoexpress-backend
Environment="PATH=/opt/videoexpress-backend/venv/bin"
ExecStart=/opt/videoexpress-backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable videoexpress
sudo systemctl start videoexpress
sudo systemctl status videoexpress
```

### Setup Nginx (Optional)

```bash
sudo apt install -y nginx

sudo nano /etc/nginx/sites-available/videoexpress
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/videoexpress /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 2. RunPod GPU Worker Setup

### Build Docker Image

```bash
cd runpod_worker

# Build
docker build -t your-dockerhub-username/videoexpress-worker:latest .

# Push to registry
docker login
docker push your-dockerhub-username/videoexpress-worker:latest
```

### Create RunPod Serverless Endpoint

1. Go to https://runpod.io/console/serverless
2. Click "New Endpoint"
3. Configure:
   - **Name**: videoexpress-worker
   - **Docker Image**: `your-dockerhub-username/videoexpress-worker:latest`
   - **GPU Type**: RTX 4090 or A40
   - **Max Workers**: 1
   - **Idle Timeout**: 60 seconds
   - **Environment Variables**:
     ```
     AWS_ACCESS_KEY_ID=your_key
     AWS_SECRET_ACCESS_KEY=your_secret
     S3_BUCKET=your-bucket
     S3_ENDPOINT_URL=https://your-s3-endpoint (optional for R2/MinIO)
     ```

4. Copy the **Endpoint ID** and **API Key**
5. Update VPS backend `.env` with these values

---

## 3. Storage Setup (Cloudflare R2 Recommended)

### Option A: Cloudflare R2 (Free 10GB)

1. Go to https://dash.cloudflare.com/
2. Create R2 bucket: `videoexpress-outputs`
3. Create API token with R2 permissions
4. Get credentials:
   - Access Key ID
   - Secret Access Key
   - Endpoint URL: `https://<account-id>.r2.cloudflarestorage.com`

### Option B: AWS S3

```bash
aws s3 mb s3://videoexpress-outputs
aws s3api put-bucket-cors --bucket videoexpress-outputs --cors-configuration file://cors.json
```

`cors.json`:
```json
{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET"],
    "AllowedHeaders": ["*"]
  }]
}
```

### Option C: Self-Hosted MinIO

```bash
docker run -d \
  -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=admin \
  -e MINIO_ROOT_PASSWORD=your-password \
  -v /data/minio:/data \
  minio/minio server /data --console-address ":9001"
```

---

## 4. Desktop App Configuration

### Update Frontend Environment

Edit `c:\Projects\Videoexpressai\.env.local`:

```
VITE_API_BASE=https://your-vps-domain.com
```

Or for local testing:
```
VITE_API_BASE=http://localhost:8000
```

### Install Dependencies

```bash
cd c:\Projects\Videoexpressai
npm install
```

### Run Desktop App

```bash
npm run dev
```

---

## 5. Testing the System

### Test Backend Health

```bash
curl http://your-vps:8000/health
```

Expected:
```json
{"status": "ok", "runpod_connected": true}
```

### Test Job Creation

```bash
curl -X POST http://your-vps:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "type": "RENDER",
    "params": {
      "prompt": "A cinematic shot of a futuristic city",
      "duration": 5,
      "resolution": "1080p"
    }
  }'
```

Expected:
```json
{"job_id": "uuid-here", "status": "QUEUED", "created_at": "..."}
```

### Check Job Status

```bash
curl http://your-vps:8000/jobs/{job_id}
```

---

## 6. Model Swapping Guide

### Current Model: CogVideoX-5b

To swap to different models, edit `runpod_worker/handler.py`:

#### Wan 2.5 (if available)
```python
pipe = WanPipeline.from_pretrained("Wan-AI/Wan2.5", torch_dtype=torch.float16).to("cuda")
```

#### Stable Video Diffusion (Image-to-Video)
```python
from diffusers import StableVideoDiffusionPipeline
pipe = StableVideoDiffusionPipeline.from_pretrained(
    "stabilityai/stable-video-diffusion-img2vid-xt",
    torch_dtype=torch.float16
).to("cuda")
```

#### AnimateDiff
```python
from diffusers import AnimateDiffPipeline
pipe = AnimateDiffPipeline.from_pretrained(
    "guoyww/animatediff-motion-adapter-v1-5-2",
    torch_dtype=torch.float16
).to("cuda")
```

After changing, rebuild and push Docker image:
```bash
docker build -t your-username/videoexpress-worker:latest .
docker push your-username/videoexpress-worker:latest
```

Then update RunPod endpoint to use new image.

---

## 7. Troubleshooting

### Backend won't start
```bash
# Check logs
sudo journalctl -u videoexpress -f

# Check if port is in use
sudo netstat -tulpn | grep 8000
```

### Jobs stuck in QUEUED
- Check RunPod endpoint is active
- Verify RUNPOD_API_KEY is correct
- Check RunPod dashboard for errors

### Progress not updating
- Ensure frontend is polling every 2s
- Check browser console for errors
- Verify CORS is enabled on backend

### Video not playing
- Check S3 bucket CORS settings
- Verify output URL is publicly accessible
- Check browser console for CORS errors

---

## 8. Cost Estimates (Solo User)

- **VPS**: $5-10/month (Hetzner, DigitalOcean)
- **RunPod GPU**: ~$0.30/hour (RTX 4090, only when generating)
- **Storage**: Free (R2 10GB) or $0.02/GB (S3)
- **Total**: ~$10-20/month for moderate use

---

## 9. Next Steps

### Phase 2 Features (TTS, Lipsync)

Add to `runpod_worker/handler.py`:

```python
# TTS with Qwen3-Audio
if job_type == "TTS":
    from transformers import AutoModelForCausalLM
    tts_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2-Audio")
    audio = tts_model.generate(input_data['text'])
    # Save and upload audio
```

### Phase 3 Features (LoRA Training)

Create separate training endpoint with longer timeout:
- Use RunPod Pods (not serverless) for multi-hour training
- Store checkpoints in S3
- Add training progress callbacks

---

## Support

For issues:
1. Check backend logs: `sudo journalctl -u videoexpress -f`
2. Check RunPod logs in dashboard
3. Verify all environment variables are set
4. Test each component independently

---

**System is now production-ready for solo use!**
