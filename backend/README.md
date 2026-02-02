# VideoExpress AI Backend System

Complete backend implementation for solo, self-hosted AI video platform.

## System Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Desktop    │─────▶│  VPS Backend │─────▶│ RunPod GPU   │─────▶│  S3 Storage  │
│ Electron+React│      │   FastAPI    │      │   Worker     │      │   R2/MinIO   │
└──────────────┘      └──────────────┘      └──────────────┘      └──────────────┘
     Polls                Job Queue           Video Gen              Output URLs
    /jobs/{id}           SQLite DB            CogVideoX              Public Access
```

## Quick Start (Local Testing)

### 1. Start Backend

```bash
# Windows
start-backend.bat

# Linux/Mac
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Configure Environment

Edit `backend/.env`:
```
RUNPOD_ENDPOINT=https://api.runpod.ai/v2/YOUR_ENDPOINT_ID
RUNPOD_API_KEY=your_key_here
S3_BUCKET=your-bucket
DB_PATH=./jobs.db
```

### 3. Start Frontend

```bash
npm run dev
```

Visit: http://localhost:5173

## API Endpoints

### Health Check
```
GET /health
Response: {"status": "ok", "runpod_connected": true}
```

### Create Job
```
POST /jobs
Body: {
  "type": "RENDER | IMG2VID | TTS | LIPSYNC | TRAIN_TWIN | EXPORT",
  "params": {
    "prompt": "A cinematic shot...",
    "duration": 5,
    "resolution": "1080p"
  }
}
Response: {"job_id": "uuid", "status": "QUEUED", "created_at": "..."}
```

### Get Job Status
```
GET /jobs/{job_id}
Response: {
  "job_id": "uuid",
  "type": "RENDER",
  "status": "RUNNING",
  "progress": 45,
  "output_urls": [],
  "error": null
}
```

### List Jobs
```
GET /jobs?limit=50
Response: [{"job_id": "...", "type": "...", "status": "...", ...}]
```

### Cancel Job
```
POST /jobs/{job_id}/cancel
Response: {"status": "CANCELED"}
```

### Stitch Timeline
```
POST /timeline/stitch
Body: {
  "clips": [
    {"url": "s3://...", "start": 0, "end": 5}
  ],
  "captions": [
    {"text": "Hello", "start": 0, "end": 2}
  ]
}
Response: {"job_id": "uuid", "status": "QUEUED"}
```

## Job States

```
QUEUED → RUNNING → SUCCEEDED
                 ↘ FAILED
                 ↘ CANCELED
```

## Database Schema

```sql
CREATE TABLE jobs (
    job_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'QUEUED',
    progress INTEGER DEFAULT 0,
    params JSON NOT NULL,
    output_urls JSON,
    error TEXT,
    runpod_job_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Job Types

| Type | Description | Params |
|------|-------------|--------|
| `RENDER` | Text-to-video | `prompt`, `duration`, `resolution` |
| `IMG2VID` | Image-to-video | `image_url`, `duration`, `motion` |
| `TTS` | Text-to-speech | `text`, `voice_preset` |
| `LIPSYNC` | Lip-sync generation | `video_url`, `audio_url` |
| `TRAIN_TWIN` | LoRA training | `images[]`, `name` |
| `EXPORT` | Timeline stitch | `clips[]`, `captions[]` |

## Frontend Integration

### API Client

```typescript
import { createJob, getJob } from './src/api/client';

// Create job
const { job_id } = await createJob('RENDER', {
  prompt: 'A futuristic city',
  duration: 5,
  resolution: '1080p'
});

// Poll for status
const job = await getJob(job_id);
console.log(job.progress); // 0-100
```

### React Hook

```typescript
import { useJob } from './src/hooks/useJob';

function VideoGenerator() {
  const [jobId, setJobId] = useState(null);
  const { job, error } = useJob(jobId);
  
  return (
    <div>
      <p>Progress: {job?.progress}%</p>
      {job?.output_urls?.[0] && (
        <video src={job.output_urls[0]} controls />
      )}
    </div>
  );
}
```

## RunPod Worker

### Handler Structure

```python
def handler(job):
    input_data = job['input']
    job_type = input_data['job_type']
    
    if job_type == "RENDER":
        # Generate video
        video = pipe(prompt=input_data['prompt'])
        
        # Upload to S3
        url = upload_to_s3(video, job['id'])
        
        return {"video_url": url, "progress": 100}
```

### Progress Updates

```python
runpod.serverless.progress_update(job, 30)  # 30% complete
runpod.serverless.progress_update(job, 70)  # 70% complete
```

## FFmpeg Timeline Stitching

```python
from backend.utils.ffmpeg_utils import stitch_timeline

clips = [
    {"url": "s3://bucket/clip1.mp4", "start": 0, "end": 5},
    {"url": "s3://bucket/clip2.mp4", "start": 0, "end": 3}
]

captions = [
    {"text": "Hello World", "start": 0, "end": 2},
    {"text": "Welcome", "start": 3, "end": 5}
]

output = stitch_timeline(clips, captions, "/tmp/final.mp4")
```

## Model Swapping

Edit `runpod_worker/handler.py`:

```python
# Current: CogVideoX
pipe = CogVideoXPipeline.from_pretrained("THUDM/CogVideoX-5b", ...)

# Swap to Stable Video Diffusion
from diffusers import StableVideoDiffusionPipeline
pipe = StableVideoDiffusionPipeline.from_pretrained(
    "stabilityai/stable-video-diffusion-img2vid-xt",
    torch_dtype=torch.float16
).to("cuda")

# Swap to AnimateDiff
from diffusers import AnimateDiffPipeline
pipe = AnimateDiffPipeline.from_pretrained(
    "guoyww/animatediff-motion-adapter-v1-5-2",
    torch_dtype=torch.float16
).to("cuda")
```

## Storage Options

### Cloudflare R2 (Recommended)
- Free 10GB
- No egress fees
- S3-compatible API

### AWS S3
- Pay per GB
- Egress fees apply
- Native integration

### Self-Hosted MinIO
- Full control
- No external costs
- Requires server

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- VPS setup (Ubuntu)
- RunPod configuration
- Storage setup
- Nginx reverse proxy
- Systemd service
- SSL certificates

## Cost Breakdown (Solo User)

| Service | Cost | Notes |
|---------|------|-------|
| VPS | $5-10/mo | Hetzner, DigitalOcean |
| RunPod GPU | $0.30/hr | Only when generating |
| Storage | Free-$2/mo | R2 10GB free, then $0.015/GB |
| **Total** | **$10-20/mo** | Moderate use (~30 videos/mo) |

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.10+

# Check port availability
netstat -ano | findstr :8000

# Check logs
uvicorn main:app --log-level debug
```

### Jobs stuck in QUEUED
- Verify RunPod endpoint is active
- Check `RUNPOD_API_KEY` in `.env`
- Test RunPod manually: `curl -H "Authorization: Bearer $KEY" $ENDPOINT/health`

### Progress not updating
- Frontend should poll every 2s
- Backend polls RunPod every 2s
- Check browser console for errors

### Video won't play
- Verify S3 bucket CORS settings
- Check output URL is publicly accessible
- Try opening URL directly in browser

## Development Roadmap

### Phase 1 (Current)
- ✅ Text-to-video (RENDER)
- ✅ Job queue + progress
- ✅ Timeline stitching
- ✅ Caption burning
- ⏳ Image-to-video (IMG2VID)

### Phase 2
- ⏳ TTS (Qwen3-Audio)
- ⏳ Lip-sync (Wav2Lip)
- ⏳ Screen recording

### Phase 3
- ⏳ Video inpainting
- ⏳ Motion brush
- ⏳ LoRA training

## File Structure

```
Videoexpressai/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── requirements.txt     # Python deps
│   ├── .env                 # Config
│   └── utils/
│       └── ffmpeg_utils.py  # Timeline stitching
├── runpod_worker/
│   ├── handler.py           # GPU worker
│   ├── requirements.txt     # Worker deps
│   └── Dockerfile           # Container image
├── frontend/
│   └── src/
│       ├── api/
│       │   └── client.ts    # API client
│       └── hooks/
│           └── useJob.ts    # Job polling hook
├── components/
│   └── WanControlPanel.tsx  # Video generator UI
├── DEPLOYMENT.md            # Production guide
└── start-backend.bat        # Quick start script
```

## Support

For issues or questions:
1. Check logs: `uvicorn main:app --log-level debug`
2. Verify environment variables
3. Test each component independently
4. Check RunPod dashboard for GPU errors

---

**Built for solo creators. No SaaS complexity. Just reliable AI video generation.**
