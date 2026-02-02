# 🚀 VideoExpress AI - Quick Reference

## ⚡ Quick Start (3 Commands)

```bash
# 1. Start backend
start-backend.bat

# 2. Test backend (new terminal)
cd backend && python test_backend.py

# 3. Start frontend (new terminal)
npm run dev
```

---

## 🔗 URLs

| Service | URL | Status |
|---------|-----|--------|
| Frontend | http://localhost:5173 | ✅ Ready |
| Backend | http://localhost:8000 | ✅ Ready |
| API Docs | http://localhost:8000/docs | ✅ Auto-generated |
| Health | http://localhost:8000/health | ✅ Ready |

---

## 📡 API Endpoints

### Health Check
```bash
GET /health
curl http://localhost:8000/health
```

### Create Job
```bash
POST /jobs
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"type":"RENDER","params":{"prompt":"test","duration":5}}'
```

### Get Job Status
```bash
GET /jobs/{job_id}
curl http://localhost:8000/jobs/{job_id}
```

### List Jobs
```bash
GET /jobs?limit=50
curl http://localhost:8000/jobs?limit=10
```

### Cancel Job
```bash
POST /jobs/{job_id}/cancel
curl -X POST http://localhost:8000/jobs/{job_id}/cancel
```

### Stitch Timeline
```bash
POST /timeline/stitch
curl -X POST http://localhost:8000/timeline/stitch \
  -H "Content-Type: application/json" \
  -d '{"clips":[{"url":"s3://...","start":0,"end":5}],"captions":[]}'
```

---

## 🎯 Job Types

| Type | Description | Status |
|------|-------------|--------|
| `RENDER` | Text-to-video | ✅ Ready |
| `IMG2VID` | Image-to-video | ⏳ TODO |
| `TTS` | Text-to-speech | ⏳ TODO |
| `LIPSYNC` | Lip-sync generation | ⏳ TODO |
| `TRAIN_TWIN` | LoRA training | ⏳ TODO |
| `EXPORT` | Timeline stitch | ✅ Ready |

---

## 📊 Job States

```
QUEUED → RUNNING → SUCCEEDED
                 ↘ FAILED
                 ↘ CANCELED
```

---

## 🔧 Configuration

### Backend (.env)
```env
RUNPOD_ENDPOINT=https://api.runpod.ai/v2/YOUR_ENDPOINT_ID
RUNPOD_API_KEY=your_key
S3_BUCKET=your-bucket
DB_PATH=./jobs.db
```

### Frontend (.env.local)
```env
VITE_API_BASE=http://localhost:8000
```

---

## 💻 Code Examples

### Create Job (TypeScript)
```typescript
import { createJob } from './api/client';

const { job_id } = await createJob('RENDER', {
  prompt: 'A cinematic shot of a sunset',
  duration: 5,
  resolution: '1080p'
});
```

### Poll Job (React Hook)
```typescript
import { useJob } from './hooks/useJob';

function VideoGenerator() {
  const [jobId, setJobId] = useState(null);
  const { job, error } = useJob(jobId);
  
  return <div>Progress: {job?.progress}%</div>;
}
```

### Stitch Timeline (TypeScript)
```typescript
import { stitchTimeline } from './api/client';

const { job_id } = await stitchTimeline(
  [{ url: 's3://bucket/clip1.mp4', start: 0, end: 5 }],
  [{ text: 'Hello', start: 0, end: 2 }]
);
```

---

## 🧪 Testing Commands

```bash
# Test backend health
curl http://localhost:8000/health

# Run test suite
cd backend && python test_backend.py

# Check database
sqlite3 backend/jobs.db "SELECT * FROM jobs;"

# View backend logs
# Check terminal where uvicorn is running

# View frontend logs
# Browser console (F12)
```

---

## 🐛 Debugging

### Backend Issues
```bash
# Check Python version
python --version  # Need 3.10+

# Install dependencies
cd backend && pip install -r requirements.txt

# Run with debug logs
uvicorn main:app --reload --log-level debug

# Check port
netstat -ano | findstr :8000
```

### Frontend Issues
```bash
# Install dependencies
npm install

# Clear cache
npm run dev -- --force

# Check environment
cat .env.local
```

### Database Issues
```bash
# Reset database
del backend\jobs.db

# Restart backend (will recreate)
start-backend.bat
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI server |
| `backend/.env` | Backend config |
| `runpod_worker/handler.py` | GPU worker |
| `src/api/client.ts` | API client |
| `src/hooks/useJob.ts` | Job polling |
| `components/WanControlPanel.tsx` | Video generator UI |
| `.env.local` | Frontend config |

---

## 🚨 Common Errors

### "Backend not responding"
```bash
# Start backend
start-backend.bat
```

### "CORS error"
```bash
# Check .env.local
echo %VITE_API_BASE%

# Should be: http://localhost:8000
```

### "Module not found"
```bash
# Backend
cd backend && pip install -r requirements.txt

# Frontend
npm install
```

### "Jobs stuck in QUEUED"
```
Expected without RunPod configured.
Jobs will process once RunPod is setup.
```

---

## 💰 Costs

| Service | Cost |
|---------|------|
| Local Testing | $0 |
| RunPod GPU | $0.30/hr (on-demand) |
| Storage (R2) | $0 (10GB free) |
| VPS | $5-10/mo (optional) |

---

## 📚 Documentation

| File | Description |
|------|-------------|
| `START_HERE.md` | ⭐ Start here! |
| `PROJECT_STRUCTURE.md` | 📦 File overview |
| `IMPLEMENTATION.md` | 📋 What was built |
| `DEPLOYMENT.md` | 🚀 Production guide |
| `backend/README.md` | 📖 API docs |

---

## 🎯 Next Steps

1. ✅ Test locally (today)
2. ⏳ Setup RunPod (1-2 hours)
3. ⏳ Configure storage (30 min)
4. ⏳ Deploy to VPS (2-3 hours)

---

## 🔗 Useful Links

- FastAPI Docs: https://fastapi.tiangolo.com
- RunPod Docs: https://docs.runpod.io
- React Docs: https://react.dev
- Cloudflare R2: https://developers.cloudflare.com/r2

---

**Built for solo creators. No SaaS complexity. Just reliable AI video generation.**
