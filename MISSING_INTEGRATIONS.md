# Missing AI Integrations Checklist

## 1. Video Generation (PRIORITY 1)

### Replace FFmpeg Placeholder with CogVideoX-2b

**Worker Changes (runpod_worker/handler.py):**
```python
# Replace generate_video() function with:
from diffusers import CogVideoXPipeline
import torch

def generate_video(prompt: str, duration: int, output_path: str):
    pipe = CogVideoXPipeline.from_pretrained(
        "THUDM/CogVideoX-2b",
        torch_dtype=torch.float16
    ).to("cuda")
    
    num_frames = duration * 8  # 8 fps
    video = pipe(
        prompt=prompt,
        num_frames=num_frames,
        guidance_scale=6.0,
    ).frames[0]
    
    # Save as MP4
    export_to_video(video, output_path, fps=8)
```

**Dockerfile Changes:**
```dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
RUN pip install diffusers transformers accelerate torch
```

**RunPod Template:**
- GPU: RTX 4000 Ada (16GB VRAM)
- Container Disk: 20GB
- Estimated: $0.30/min

---

## 2. Audio Generation (PRIORITY 2)

### Add ElevenLabs TTS to Backend

**File: backend/api_audio.py**
```python
from elevenlabs import generate, set_api_key

@app.post("/audio/generate")
async def generate_audio(text: str, voice: str = "Adam"):
    set_api_key(os.getenv("ELEVENLABS_API_KEY"))
    audio = generate(text=text, voice=voice)
    
    # Upload to R2
    audio_url = upload_audio_to_r2(audio, job_id)
    return {"audio_url": audio_url}
```

**Requirements:**
```bash
pip install elevenlabs
```

**Cost:** $0.30 per 1000 characters

---

## 3. Lipsync (PRIORITY 3)

### Deploy ACTalker Worker

**New Worker: runpod_worker_actalker/**

```python
# handler_actalker.py
from actalker import ACTalker

def handler(job):
    avatar_url = job["input"]["avatar_url"]
    audio_url = job["input"]["audio_url"]
    
    # Download inputs
    avatar = download_file(avatar_url)
    audio = download_file(audio_url)
    
    # Run ACTalker
    model = ACTalker.load()
    output = model.generate(avatar, audio)
    
    # Upload to R2
    url = upload_to_r2(output, job_id)
    return {"output_url": url}
```

**RunPod Setup:**
- New endpoint: `actalker-worker`
- GPU: RTX 4000 Ada
- Model: ACTalker checkpoint

**Backend Integration:**
```python
@app.post("/avatar/lipsync")
async def create_lipsync(data: LipsyncRequest):
    job_id = create_job("LIPSYNC", data.dict())
    dispatch_to_runpod(ACTALKER_ENDPOINT, job_id, data.dict())
    return {"job_id": job_id}
```

---

## 4. Digital Twin Training (PRIORITY 4)

### Deploy LoRA Training Worker

**New Worker: runpod_worker_training/**

```python
# handler_training.py
from kohya_ss import train_lora

def handler(job):
    images = job["input"]["images"]
    name = job["input"]["name"]
    
    # Download training images
    dataset = download_images(images)
    
    # Train LoRA
    lora_path = train_lora(
        dataset=dataset,
        base_model="stabilityai/stable-diffusion-xl-base-1.0",
        steps=1000,
    )
    
    # Upload LoRA weights to R2
    url = upload_to_r2(lora_path, job_id)
    return {"lora_url": url}
```

**RunPod Setup:**
- GPU: RTX 4090 (24GB VRAM)
- Training time: ~30 min
- Cost: ~$0.50 per training

---

## Quick Start: Minimal Working System

### Phase 1: Video Only (1 hour)
1. Replace FFmpeg with CogVideoX-2b in worker
2. Rebuild Docker image
3. Update RunPod endpoint
4. Test video generation

### Phase 2: Add Audio (30 min)
1. Get ElevenLabs API key
2. Add audio generation endpoint
3. Test TTS

### Phase 3: Add Lipsync (2 hours)
1. Deploy ACTalker worker
2. Add lipsync endpoint
3. Test avatar animation

### Phase 4: Add Training (4 hours)
1. Deploy training worker
2. Add training endpoint
3. Test LoRA training

---

## Current Status

| Feature | Status | Priority | Effort |
|---------|--------|----------|--------|
| Video (FFmpeg) | ✅ Working | - | Done |
| Video (AI) | ❌ Missing | P1 | 1h |
| Audio (TTS) | ❌ Missing | P2 | 30m |
| Lipsync | ❌ Missing | P3 | 2h |
| Training | ❌ Missing | P4 | 4h |
| Social Upload | ✅ Ready | - | Done |
| Job Queue | ✅ Working | - | Done |
| Storage (R2) | ✅ Working | - | Done |

---

## Recommended Next Step

**Replace FFmpeg with CogVideoX-2b** (Priority 1)

This gives you real AI video generation in ~1 hour of work.

Would you like me to implement this now?
