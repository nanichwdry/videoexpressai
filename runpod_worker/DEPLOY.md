# RunPod Worker Deployment - Step by Step

## What This Does

This is a **minimal working worker** that:
- ✅ Boots and accepts jobs
- ✅ Echoes back your prompt
- ✅ Returns fake success
- ❌ Doesn't generate videos yet (that's next step)

**Purpose**: Prove the pipeline works before adding heavy AI models.

---

## Step 1: Build Docker Image (5 min)

```bash
cd runpod_worker

# Build
docker build -t YOUR_DOCKERHUB_USERNAME/videoexpress-worker:v1 .

# Test locally (optional)
docker run --rm YOUR_DOCKERHUB_USERNAME/videoexpress-worker:v1
# Should print: "Starting RunPod Handler..."
```

---

## Step 2: Push to Docker Hub (2 min)

```bash
# Login
docker login

# Push
docker push YOUR_DOCKERHUB_USERNAME/videoexpress-worker:v1
```

---

## Step 3: Create RunPod Endpoint (5 min)

1. Go to: https://runpod.io/console/serverless

2. Click **"New Endpoint"**

3. Configure:
   - **Name**: `videoexpress-worker`
   - **Docker Image**: `YOUR_DOCKERHUB_USERNAME/videoexpress-worker:v1`
   - **GPU Type**: Any (even CPU works for this test)
   - **Max Workers**: 1
   - **Idle Timeout**: 60 seconds
   - **Environment Variables**: (none needed yet)

4. Click **"Deploy"**

5. **Copy the Endpoint ID** (looks like: `abc123def456`)

---

## Step 4: Configure Backend (1 min)

Edit `backend/.env`:

```env
RUNPOD_ENDPOINT=https://api.runpod.ai/v2/YOUR_ENDPOINT_ID
RUNPOD_API_KEY=your_NEW_api_key_here
```

**Replace**:
- `YOUR_ENDPOINT_ID` with the ID from step 3
- `your_NEW_api_key_here` with your new (not exposed) API key

---

## Step 5: Test End-to-End (2 min)

### Start Backend
```bash
cd backend
python -m uvicorn main:app --reload
```

### Test Health
```bash
curl http://localhost:8000/health
```

Should show: `{"status": "ok", "runpod_connected": true}`

### Create Test Job
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"type":"RENDER","params":{"prompt":"test video"}}'
```

Copy the `job_id` from response.

### Check Job Status
```bash
curl http://localhost:8000/jobs/YOUR_JOB_ID
```

Should show:
- `status: "RUNNING"` → `"SUCCEEDED"`
- `progress: 0` → `100`
- `output_urls: []` (empty for now, that's expected)

---

## Step 6: Test in UI (1 min)

1. Start frontend: `npm run dev`
2. Open: http://localhost:5173
3. Go to WanControlPanel
4. Enter prompt: "test video"
5. Click "Ignite Engine"
6. Watch progress bar go 0% → 100%
7. Status should show "SUCCEEDED"

---

## Troubleshooting

### "runpod_connected": false
- Check `RUNPOD_ENDPOINT` has correct endpoint ID
- Check `RUNPOD_API_KEY` is valid (not the exposed one!)

### Job stuck in QUEUED
- Check RunPod dashboard: https://runpod.io/console/serverless
- Click your endpoint → "Logs"
- Look for errors

### Job fails immediately
- Check worker logs in RunPod dashboard
- Common issue: Docker image not found (check Docker Hub)

---

## Next Steps

Once this works:

1. **Add video model** (CogVideoX, Wan2.5, etc.)
2. **Add S3 upload** (for output videos)
3. **Add progress callbacks** (for real-time updates)

But get this baseline working first!

---

## Quick Reference

```bash
# Build
docker build -t USERNAME/videoexpress-worker:v1 .

# Push
docker push USERNAME/videoexpress-worker:v1

# Test backend
curl http://localhost:8000/health

# Create job
curl -X POST http://localhost:8000/jobs \
  -d '{"type":"RENDER","params":{"prompt":"test"}}'

# Check status
curl http://localhost:8000/jobs/JOB_ID
```

---

**Once this works, you have a complete pipeline. Then we add the AI model.**
