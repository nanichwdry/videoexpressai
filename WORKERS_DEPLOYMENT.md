# AI Workers Deployment Guide

## Overview

4 separate RunPod serverless workers:
1. **Video Worker** - CogVideoX-2B (text-to-video)
2. **TTS Worker** - Coqui TTS (text-to-speech)
3. **Lipsync Worker** - Wav2Lip (face + audio → lipsync video)
4. **LoRA Worker** - AI-Toolkit (train custom models)

---

## 1. VIDEO WORKER (CogVideoX-2B)

### Build & Push

```bash
cd workers/video_worker
docker build -t YOUR_DOCKERHUB/videoexpress-cogvideox:v1 .
docker push YOUR_DOCKERHUB/videoexpress-cogvideox:v1
```

### RunPod Setup

1. Go to RunPod → Serverless → New Endpoint
2. **Name**: `videoexpress-video`
3. **Container Image**: `YOUR_DOCKERHUB/videoexpress-cogvideox:v1`
4. **GPU**: RTX 4000 Ada (16GB VRAM) or RTX A4000
5. **Container Disk**: 20GB
6. **Environment Variables**:
   ```
   R2_BUCKET=videoexpress-outputs
   R2_PUBLIC_BASE_URL=https://pub-xxx.r2.dev
   AWS_ACCESS_KEY_ID=xxx
   AWS_SECRET_ACCESS_KEY=xxx
   AWS_ENDPOINT_URL=https://xxx.r2.cloudflarestorage.com
   AWS_REGION=auto
   ```
7. **Workers**: Min=0, Max=3
8. **Idle Timeout**: 5 seconds
9. **Execution Timeout**: 600 seconds

### GPU Recommendations

| GPU | VRAM | Cost/min | Speed | Recommended |
|-----|------|----------|-------|-------------|
| RTX 4000 Ada | 16GB | $0.30 | Fast | ✅ Best |
| RTX A4000 | 16GB | $0.28 | Fast | ✅ Good |
| RTX 3090 | 24GB | $0.34 | Medium | ⚠️ Overkill |

### First Test

```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "A cat walking on the beach at sunset",
      "duration": 5
    }
  }'
```

Expected output:
```json
{
  "ok": true,
  "output_url": "https://pub-xxx.r2.dev/videos/xxx/final.mp4",
  "worker_version": "v6-cogvideox",
  "meta": {
    "model": "cogvideox-2b",
    "fps": 8
  }
}
```

---

## 2. TTS WORKER (Coqui TTS)

### Build & Push

```bash
cd workers/tts_worker
docker build -t YOUR_DOCKERHUB/videoexpress-tts:v1 .
docker push YOUR_DOCKERHUB/videoexpress-tts:v1
```

### RunPod Setup

1. **Name**: `videoexpress-tts`
2. **Container Image**: `YOUR_DOCKERHUB/videoexpress-tts:v1`
3. **GPU**: RTX 4000 Ada (8GB VRAM sufficient)
4. **Container Disk**: 10GB
5. **Environment Variables**: Same R2 config as video worker
6. **Workers**: Min=0, Max=2
7. **Execution Timeout**: 300 seconds

### GPU Recommendations

| GPU | VRAM | Cost/min | Speed | Recommended |
|-----|------|----------|-------|-------------|
| RTX 4000 Ada | 16GB | $0.30 | Fast | ✅ Best |
| RTX 3060 | 12GB | $0.20 | Medium | ✅ Budget |

### First Test

```bash
curl -X POST https://api.runpod.ai/v2/YOUR_TTS_ENDPOINT/run \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "text": "Hello, this is a test of the text to speech system."
    }
  }'
```

Expected output:
```json
{
  "ok": true,
  "output_url": "https://pub-xxx.r2.dev/audio/xxx/voice.wav",
  "worker_version": "v1-coqui-tts",
  "meta": {
    "model": "coqui-tts",
    "voice": "ljspeech"
  }
}
```

---

## 3. LIPSYNC WORKER (Wav2Lip)

### Build & Push

```bash
cd workers/lipsync_worker
docker build -t YOUR_DOCKERHUB/videoexpress-lipsync:v1 .
docker push YOUR_DOCKERHUB/videoexpress-lipsync:v1
```

### RunPod Setup

1. **Name**: `videoexpress-lipsync`
2. **Container Image**: `YOUR_DOCKERHUB/videoexpress-lipsync:v1`
3. **GPU**: RTX 4000 Ada (16GB VRAM)
4. **Container Disk**: 15GB
5. **Environment Variables**: Same R2 config
6. **Workers**: Min=0, Max=2
7. **Execution Timeout**: 600 seconds

### GPU Recommendations

| GPU | VRAM | Cost/min | Speed | Recommended |
|-----|------|----------|-------|-------------|
| RTX 4000 Ada | 16GB | $0.30 | Fast | ✅ Best |
| RTX A4000 | 16GB | $0.28 | Fast | ✅ Good |

### First Test

```bash
# First generate TTS audio, then use it for lipsync
curl -X POST https://api.runpod.ai/v2/YOUR_LIPSYNC_ENDPOINT/run \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "face_url": "https://pub-xxx.r2.dev/faces/test.mp4",
      "audio_url": "https://pub-xxx.r2.dev/audio/xxx/voice.wav"
    }
  }'
```

Expected output:
```json
{
  "ok": true,
  "output_url": "https://pub-xxx.r2.dev/lipsync/xxx/final.mp4",
  "worker_version": "v1-wav2lip",
  "meta": {
    "model": "wav2lip-gan"
  }
}
```

---

## 4. LORA TRAINING WORKER

### Build & Push

```bash
cd workers/lora_worker
docker build -t YOUR_DOCKERHUB/videoexpress-lora:v1 .
docker push YOUR_DOCKERHUB/videoexpress-lora:v1
```

### RunPod Setup

1. **Name**: `videoexpress-lora`
2. **Container Image**: `YOUR_DOCKERHUB/videoexpress-lora:v1`
3. **GPU**: RTX 4090 (24GB VRAM) or A6000
4. **Container Disk**: 30GB
5. **Environment Variables**: Same R2 config
6. **Workers**: Min=0, Max=1 (expensive)
7. **Execution Timeout**: 3600 seconds (1 hour)

### GPU Recommendations

| GPU | VRAM | Cost/min | Speed | Recommended |
|-----|------|----------|-------|-------------|
| RTX 4090 | 24GB | $0.69 | Fast | ✅ Best |
| A6000 | 48GB | $0.79 | Fast | ⚠️ Overkill |
| RTX 3090 | 24GB | $0.34 | Medium | ✅ Budget |

### First Test

```bash
curl -X POST https://api.runpod.ai/v2/YOUR_LORA_ENDPOINT/run \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "images": [
        "https://example.com/img1.jpg",
        "https://example.com/img2.jpg",
        "https://example.com/img3.jpg",
        "https://example.com/img4.jpg",
        "https://example.com/img5.jpg"
      ],
      "name": "my_subject"
    }
  }'
```

Expected output:
```json
{
  "ok": true,
  "output_url": "https://pub-xxx.r2.dev/lora/xxx/adapter.safetensors",
  "worker_version": "v1-lora-trainer",
  "meta": {
    "model": "sdxl-lora",
    "steps": 1000
  }
}
```

---

## Backend Configuration

Add to `backend/.env`:

```bash
# Video worker (CogVideoX)
RUNPOD_VIDEO_ENDPOINT=https://api.runpod.ai/v2/YOUR_VIDEO_ENDPOINT_ID

# TTS worker (Coqui)
RUNPOD_TTS_ENDPOINT=https://api.runpod.ai/v2/YOUR_TTS_ENDPOINT_ID

# Lipsync worker (Wav2Lip)
RUNPOD_LIPSYNC_ENDPOINT=https://api.runpod.ai/v2/YOUR_LIPSYNC_ENDPOINT_ID

# LoRA training worker
RUNPOD_LORA_ENDPOINT=https://api.runpod.ai/v2/YOUR_LORA_ENDPOINT_ID

# RunPod API key (same for all)
RUNPOD_API_KEY=your_runpod_api_key
```

---

## Cost Estimates

### Per-Job Costs

| Job Type | GPU | Duration | Cost |
|----------|-----|----------|------|
| Video (5s) | RTX 4000 Ada | ~60s | $0.30 |
| TTS (100 words) | RTX 4000 Ada | ~10s | $0.05 |
| Lipsync (10s) | RTX 4000 Ada | ~30s | $0.15 |
| LoRA Training | RTX 4090 | ~30min | $20.70 |

### Monthly Estimates (100 videos/month)

- 100 videos: $30
- 100 TTS: $5
- 50 lipsync: $7.50
- 5 LoRA trainings: $103.50

**Total: ~$146/month** for moderate usage

---

## Integration Checklist

### 1. Deploy All Workers

- [ ] Build and push video worker Docker image
- [ ] Create RunPod video endpoint
- [ ] Test video generation
- [ ] Build and push TTS worker
- [ ] Create RunPod TTS endpoint
- [ ] Test TTS generation
- [ ] Build and push lipsync worker
- [ ] Create RunPod lipsync endpoint
- [ ] Test lipsync
- [ ] Build and push LoRA worker
- [ ] Create RunPod LoRA endpoint
- [ ] Test LoRA training

### 2. Update Backend

- [ ] Add endpoint URLs to `backend/.env`
- [ ] Import `api_workers.py` in `main.py`
- [ ] Test `/jobs/video` endpoint
- [ ] Test `/jobs/tts` endpoint
- [ ] Test `/jobs/lipsync` endpoint
- [ ] Test `/jobs/lora` endpoint

### 3. Update Frontend

- [ ] Update WanControlPanel to use `/jobs/video`
- [ ] Update VoiceLab to use `/jobs/tts`
- [ ] Update ACTalker to use `/jobs/lipsync`
- [ ] Update TrainingStudio to use `/jobs/lora`

---

## Troubleshooting

### Video Worker

**Issue**: Model download timeout  
**Fix**: Increase container disk to 25GB, first run takes 5-10min

**Issue**: CUDA out of memory  
**Fix**: Use RTX 4000 Ada (16GB) or higher

### TTS Worker

**Issue**: espeak-ng not found  
**Fix**: Dockerfile includes espeak-ng, rebuild image

### Lipsync Worker

**Issue**: Wav2Lip checkpoint not downloading  
**Fix**: Check GitHub releases URL, may need manual download

### LoRA Worker

**Issue**: Training fails with OOM  
**Fix**: Reduce batch_size to 1, use RTX 4090 (24GB)

---

## Next Steps

1. Deploy video worker first (highest priority)
2. Test end-to-end video generation
3. Deploy TTS worker
4. Deploy lipsync worker
5. Deploy LoRA worker last (optional, expensive)

**Start with video worker to get real AI video generation working immediately.**
