# VideoExpress AI - Production Desktop Deployment

## Architecture Overview

**Desktop App Stack:**
- Electron (main process) - System tray, backend auto-start, secure storage, OAuth popups
- React (renderer) - UI with existing tabs (WanControlPanel, VoiceLab, ACTalker, TrainingStudio, SocialHub, Settings)
- FastAPI (backend) - Job queue, RunPod dispatch, Supabase sync, OAuth callbacks
- SQLite (local) - Job persistence with WAL mode
- Supabase (cloud) - Projects, renders, encrypted OAuth tokens, audit logs
- RunPod (GPU) - Video generation workers (v5-production)
- Cloudflare R2 - Video storage with public URLs
- Sentry - Error tracking (main + backend)

## Setup Instructions

### 1. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend/Electron
npm install
```

### 2. Configure Environment

Copy `.env.production.template` to `backend/.env` and fill in:

```bash
# Required
RUNPOD_ENDPOINT=https://api.runpod.ai/v2/grgdeymymquj03
RUNPOD_API_KEY=your_key
R2_BUCKET=videoexpress-outputs
R2_PUBLIC_BASE_URL=https://pub-xxx.r2.dev
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_ENDPOINT_URL=https://xxx.r2.cloudflarestorage.com
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_KEY=xxx
SENTRY_DSN=https://xxx@sentry.io/xxx
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
INSTAGRAM_CLIENT_ID=xxx
INSTAGRAM_CLIENT_SECRET=xxx
```

### 3. Setup Supabase

```bash
cd supabase
# Copy schema.sql content and run in Supabase SQL Editor
# Or use migration script:
python migrate_supabase.py
```

### 4. Setup Sentry

1. Create project at sentry.io
2. Get DSN and add to `.env`
3. Sentry auto-captures errors in Electron main + FastAPI backend

### 5. Setup OAuth

**YouTube:**
1. Go to Google Cloud Console
2. Create OAuth 2.0 credentials
3. Add redirect URI: `http://localhost:8000/oauth/youtube/callback`
4. Add Client ID/Secret to `.env`

**Instagram:**
1. Go to Meta for Developers
2. Create app with Instagram Basic Display
3. Add redirect URI: `http://localhost:8000/oauth/instagram/callback`
4. Add Client ID/Secret to `.env`

### 6. Development Mode

```bash
# Terminal 1: Backend
cd backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
npm run dev

# Terminal 3: Electron
npm run dev:electron
```

Or use concurrently:
```bash
npm run dev
```

### 7. Production Build

**Windows:**
```bash
npm run make
# Output: out/make/squirrel.windows/x64/VideoExpressAI-1.0.0 Setup.exe
```

**Mac:**
```bash
npm run make
# Output: out/make/VideoExpress AI.dmg
```

**Code Signing (Required for Distribution):**

Windows:
```bash
set WINDOWS_CERT_FILE=path\to\cert.pfx
set WINDOWS_CERT_PASSWORD=your_password
npm run make
```

Mac:
```bash
export APPLE_ID=your@email.com
export APPLE_PASSWORD=app-specific-password
export APPLE_TEAM_ID=TEAM123
export APPLE_IDENTITY="Developer ID Application: Your Name (TEAM123)"
npm run make
```

## User Experience

### First Launch

1. App starts, shows splash screen
2. Backend auto-starts in background (no terminal)
3. Health checks run:
   - Backend: ✓
   - RunPod: ✓
   - Supabase: ✓
   - R2: ✓
4. Main window opens with status indicators
5. System tray icon appears

### Settings Page

- **API Keys**: User enters OpenAI/Gemini/ElevenLabs keys → encrypted via Electron safeStorage
- **OAuth**: Click "Connect YouTube" → popup opens → user authorizes → tokens saved to Supabase (encrypted)
- **Health Status**: Real-time indicators for all services

### Video Generation Workflow

1. User enters prompt in WanControlPanel
2. Click "Generate" → job created in SQLite + Supabase
3. Backend dispatches to RunPod warm worker (~1s delay)
4. Progress updates every 2s (10% → 30% → 85% → 100%)
5. Video uploaded to R2, public URL returned
6. Video player shows result
7. User can upload to YouTube/Instagram via SocialHub

### Reliability Features

- **Heartbeat Monitor**: Jobs timeout after 10min without progress
- **Hard Cancel**: Immediate cancellation, discards output
- **SQLite WAL**: Prevents database locks
- **Retry Logic**: Auto-retry RunPod 5xx errors (max 1 retry)
- **MP4 Validation**: ffprobe check before marking success
- **Sentry**: All errors captured with context
- **Minimize Safe**: Jobs continue in background, no crashes

## File Structure

```
videoexpress-ai/
├── electron/
│   ├── main.ts          # Main process (tray, backend, OAuth)
│   ├── preload.ts       # IPC bridge
│   └── types.d.ts       # TypeScript declarations
├── backend/
│   ├── main.py          # Existing FastAPI with hardening
│   ├── api_extended.py  # OAuth, social upload, health
│   ├── .env             # Production config
│   └── requirements.txt # Python deps
├── supabase/
│   ├── schema.sql       # Database schema
│   └── migrate_supabase.py
├── components/
│   ├── Settings.tsx     # New settings page
│   ├── WanControlPanel.tsx
│   ├── SocialHub.tsx
│   └── ...
├── forge.config.ts      # Electron Forge config
├── package.electron.json
└── .env.production.template
```

## Integration with Existing Code

### Backend (main.py)

Add to imports:
```python
from api_extended import router as extended_router
app.include_router(extended_router)
```

### Frontend (App.tsx)

Add Settings tab:
```tsx
import { Settings } from './components/Settings';

// In tabs array:
{ id: 'settings', label: 'Settings', component: Settings }
```

### Health Check on Startup

```tsx
useEffect(() => {
  if (window.electron) {
    window.electron.health.onStatus((status) => {
      console.log('Health:', status);
      // Show toast/banner if services down
    });
  }
}, []);
```

## Why SQLite is Safe (No Redis/BullMQ Needed)

1. **WAL Mode**: Concurrent reads during writes
2. **Heartbeat Monitor**: Detects stuck jobs
3. **Retry Logic**: Handles transient failures
4. **Supabase Sync**: Cloud backup of job state
5. **Single User**: No multi-tenant concurrency issues
6. **Process Isolation**: Backend runs as child process, survives minimize

**Edge Cases Covered:**
- App minimized → Backend continues, heartbeat active
- App crashes → Backend survives, jobs resume on restart
- Worker timeout → Heartbeat monitor fails job after 10min
- Database lock → Retry logic with 5s timeout

## Build Commands Summary

```bash
# Development
npm run dev                    # All services with hot reload

# Production Build
npm run build                  # Build frontend + Electron app

# Package
npm run make                   # Create installer (Windows .exe or Mac .dmg)

# Publish (requires code signing)
npm run publish                # Build + upload to distribution server
```

## Distribution

**Windows:**
- Squirrel installer with auto-update support
- Requires code signing certificate for SmartScreen bypass

**Mac:**
- DMG with drag-to-Applications
- Requires Apple Developer account + notarization

**Auto-Update:**
- Configure `electron-forge publish` with S3/GitHub releases
- App checks for updates on startup

## Troubleshooting

**Backend won't start:**
- Check Python installed: `python --version`
- Check uvicorn: `pip install uvicorn`
- Check logs in Electron console

**OAuth fails:**
- Verify redirect URIs match exactly
- Check Client ID/Secret in `.env`
- Ensure localhost:8000 accessible

**Video upload fails:**
- Check R2 credentials
- Verify bucket public access
- Check CORS settings

**Sentry not capturing:**
- Verify DSN in `.env`
- Check network (firewall/proxy)

## Security Notes

- API keys encrypted via OS keychain (Windows Credential Manager / macOS Keychain)
- OAuth tokens encrypted at rest in Supabase
- No secrets in localStorage or plain files
- HTTPS for all external APIs
- RLS policies on Supabase tables

## Next Steps

1. Replace FFmpeg placeholder with real AI model (CogVideoX-2b)
2. Implement ACTalker lipsync worker
3. Implement LoRA training worker
4. Add video preview/trim in timeline
5. Add batch generation queue
6. Add project templates
7. Add analytics dashboard
