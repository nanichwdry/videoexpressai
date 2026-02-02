# Production Worker Integration Guide

## What This Worker Does

✅ Accepts prompt + duration
✅ Generates MP4 video (currently test video with FFmpeg)
✅ Uploads to Cloudflare R2
✅ Returns public playable URL
✅ Never hangs or fails silently
✅ Optimized for solo use (1 warm worker)

---

## Current Implementation

**Video Generation**: FFmpeg test video (black screen with prompt text)

**Location**: `handler.py` → `generate_video()` function (lines 45-80)

---

## How to Add Real Video Model

### Option 1: CogVideoX (Recommended)

Replace `generate_video()` with:

```python
from diffusers import CogVideoXPipeline
from diffusers.utils import export_to_video
import torch

# Load model once at startup (outside handler)
pipe = CogVideoXPipeline.from_pretrained(
    "THUDM/CogVideoX-2b",
    torch_dtype=torch.float16
).to("cuda")

def generate_video(prompt, duration, output_path):
    log(f"Generating video: prompt='{prompt}', duration={duration}s")
    
    num_frames = duration * 8  # 8fps
    
    video_frames = pipe(
        prompt=prompt,
        num_frames=num_frames,
        guidance_scale=6.0,
        num_inference_steps=50
    ).frames[0]
    
    export_to_video(video_frames, output_path, fps=8)
    
    if not os.path.exists(output_path):
        raise RuntimeError("Video generation failed")
    
    log(f"Video generated: {output_path}")
```

**Update Dockerfile**:
```dockerfile
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel
# ... rest stays same
```

**Update requirements.txt**:
```
runpod
boto3
torch
diffusers
transformers
accelerate
```

---

### Option 2: Wan2.5 (If Available)

Replace with Wan2.5 pipeline (similar structure to CogVideoX)

---

### Option 3: FFmpeg from Images

Keep current FFmpeg approach but generate from image sequence:

```python
def generate_video(prompt, duration, output_path):
    # 1. Generate images with Stable Diffusion
    # 2. Save as /tmp/frame_*.png
    # 3. Use FFmpeg to create video from images
    
    cmd = [
        "ffmpeg", "-y",
        "-framerate", "8",
        "-i", "/tmp/frame_%04d.png",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    subprocess.run(cmd, check=True)
```

---

## Progress Mapping to UI

The backend polls RunPod and mirrors progress to frontend:

| Worker Progress | What's Happening | UI Shows |
|----------------|------------------|----------|
| 0% | Job received | "Starting..." |
| 10% | Environment validated | "Initializing..." |
| 30% | Video generation started | "Generating video..." |
| 70% | Video generated | "Processing..." |
| 85% | Uploading to R2 | "Uploading..." |
| 100% | Complete | Video player appears |

**Cold Start Detection**: If progress stays at 0% for >15s, UI shows "⚡ Warming GPU"

---

## Environment Variables (RunPod)

Set these in RunPod endpoint settings:

```
R2_BUCKET=videoexpress-outputs
R2_PUBLIC_BASE_URL=https://pub-xxxxx.r2.dev
AWS_ACCESS_KEY_ID=your_r2_access_key
AWS_SECRET_ACCESS_KEY=your_r2_secret_key
AWS_ENDPOINT_URL=https://xxxxx.r2.cloudflarestorage.com
AWS_REGION=auto
```

---

## Build & Deploy

```bash
# Build
docker build -t yourusername/videoexpress-worker:v5 .

# Push
docker push yourusername/videoexpress-worker:v5
```

Update RunPod endpoint:
- Image: `yourusername/videoexpress-worker:v5`
- GPU: RTX 4090 or A40 (if using AI model)
- Max Workers: 1
- Active Workers: 1
- Idle Timeout: 120s

---

## Testing

```powershell
cd backend
.\test-api.ps1
```

Check job status:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/jobs/JOB_ID" | ConvertTo-Json
```

Should show:
- `status: "SUCCEEDED"`
- `progress: 100`
- `output_urls: ["https://pub-xxxxx.r2.dev/videos/JOB_ID/final.mp4"]`

---

## Troubleshooting

### "Missing required env vars"
- Check RunPod endpoint environment variables
- All 5 R2 variables must be set

### "Video generation failed"
- Check RunPod logs for FFmpeg errors
- Verify FFmpeg is installed in Docker image

### "R2 upload failed"
- Verify R2 credentials are correct
- Check bucket name matches
- Ensure bucket has public access enabled

### Video doesn't play
- Check R2 public URL is accessible
- Verify ContentType is "video/mp4"
- Check browser console for CORS errors

---

## Performance Notes

**First Run**: 30-60s (cold start + generation)
**Subsequent Runs**: 5-10s (warm worker)

**Optimization**:
- Keep 1 worker warm (already configured)
- Model stays loaded in memory
- R2 upload is fast (~1-2s for 5s video)

---

## Next Steps

1. ✅ Test current FFmpeg implementation
2. ⏳ Add real video model (CogVideoX/Wan2.5)
3. ⏳ Optimize inference speed
4. ⏳ Add image-to-video support
5. ⏳ Add audio/music generation

**Current worker is production-ready for testing the pipeline!**
