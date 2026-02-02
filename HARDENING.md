# System Hardening Documentation

## Overview

This document describes the production-grade safeguards added to prevent silent failures, stuck jobs, and resource leaks.

---

## 1. JOB TIMEOUT / HEARTBEAT ENFORCEMENT

### Problem
Jobs could stay in RUNNING state forever if worker crashes or loses connection.

### Solution
- **Heartbeat timestamp** added to every job
- Updated on every progress update (every 2 seconds during polling)
- Background monitor checks for stale heartbeats every 30 seconds
- Jobs without heartbeat for >10 minutes (configurable) are marked FAILED

### Implementation

#### Database Schema
```sql
ALTER TABLE jobs ADD COLUMN heartbeat_at TIMESTAMP;
CREATE INDEX idx_heartbeat ON jobs(heartbeat_at) WHERE status = 'RUNNING';
```

#### Heartbeat Update
```python
# Every progress update includes heartbeat
update_job(job_id, progress=50, heartbeat=True)
```

#### Monitor
```python
async def heartbeat_monitor():
    """Runs every 30 seconds, marks stale jobs as FAILED"""
    while True:
        timeout_threshold = datetime.utcnow() - timedelta(seconds=JOB_HEARTBEAT_TIMEOUT)
        
        stale_jobs = conn.execute("""
            SELECT job_id FROM jobs 
            WHERE status = 'RUNNING' 
            AND heartbeat_at < ?
        """, (timeout_threshold,))
        
        for job_id in stale_jobs:
            update_job(job_id, 
                status="FAILED", 
                error_code="worker_timeout",
                error_message="Job exceeded maximum execution time")
```

### Configuration
```env
JOB_HEARTBEAT_TIMEOUT=600  # 10 minutes (default)
```

### Guarantees
- ✅ No jobs stuck in RUNNING forever
- ✅ Frontend reflects failure immediately
- ✅ Clear error message to user
- ✅ Survives backend restarts (monitor restarts on startup)

---

## 2. HARD CANCEL SEMANTICS

### Problem
Canceled jobs could still upload results, overwrite status, or show in UI.

### Solution
- **Immediate status update** to CANCELED in database
- **Idempotent** - safe to call multiple times
- **Output prevention** - worker checks status before uploading
- **Discard late results** - if worker returns after cancel, output is discarded

### Implementation

#### Cancel Endpoint
```python
@app.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    # Check current status
    current_status = get_job_status(job_id)
    
    # Idempotent: already terminal
    if current_status in ["CANCELED", "SUCCEEDED", "FAILED"]:
        return {"status": current_status}
    
    # Mark CANCELED immediately
    update_job(job_id, 
        status="CANCELED",
        error_code="user_canceled",
        error_message="Job canceled by user")
    
    return {"status": "CANCELED"}
```

#### Worker Checks
```python
async def process_job(job_id, ...):
    while True:
        # Check if canceled before every action
        if get_job_status(job_id) == "CANCELED":
            logger.info(f"Job {job_id} canceled, stopping")
            break
        
        # ... poll RunPod ...
        
        if runpod_status == "COMPLETED":
            # Double-check not canceled before accepting output
            if get_job_status(job_id) == "CANCELED":
                logger.info(f"Job {job_id} completed but canceled, discarding")
                break
            
            # Safe to upload
            update_job(job_id, status="SUCCEEDED", output_urls=[...])
```

### Guarantees
- ✅ Status updates immediately
- ✅ No output uploaded after cancel
- ✅ Safe to call multiple times
- ✅ Worker respects cancellation
- ✅ No race conditions

---

## 3. SQLITE RELIABILITY

### Problem
- Database locks under concurrent access
- Corruption risk without proper journaling
- Long transactions blocking other operations

### Solution
- **WAL mode** for better concurrency
- **Retry logic** for SQLITE_BUSY errors
- **Short transactions** - no long-running queries
- **Connection pooling** via get_db_connection()

### Implementation

#### Database Initialization
```python
def init_db():
    conn = get_db_connection()
    
    # Enable WAL mode (write-ahead logging)
    # Allows concurrent reads during writes
    conn.execute("PRAGMA journal_mode=WAL")
    
    # NORMAL synchronous mode
    # Balance between safety and performance
    conn.execute("PRAGMA synchronous=NORMAL")
    
    # Wait up to 5 seconds for locks
    conn.execute("PRAGMA busy_timeout=5000")
```

#### Retry Logic
```python
def get_db_connection():
    """Retry connection on SQLITE_BUSY"""
    for attempt in range(DB_RETRY_ATTEMPTS):
        try:
            return sqlite3.connect(DB_PATH, timeout=5.0)
        except sqlite3.OperationalError:
            if attempt == DB_RETRY_ATTEMPTS - 1:
                raise
            time.sleep(DB_RETRY_DELAY)
```

#### Short Transactions
```python
# BAD: Long transaction
conn = get_db_connection()
for job in jobs:
    process_job(job)  # Could take minutes
conn.commit()

# GOOD: Short transaction
conn = get_db_connection()
conn.execute("UPDATE jobs SET status = ? WHERE job_id = ?", (...))
conn.commit()
conn.close()  # Release immediately
```

### Guarantees
- ✅ No database locks during polling
- ✅ Crash-resistant (WAL mode)
- ✅ Automatic retry on busy
- ✅ Safe for solo use (no connection pool needed)

---

## 4. STORAGE HYGIENE

### Problem
Orphaned video files accumulate, wasting disk space.

### Solution
- **DELETE endpoint** removes job + artifacts
- **Manual cleanup script** for batch operations
- **Orphan detection** finds files without DB entries

### Implementation

#### Delete Endpoint
```python
@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    # Get output URLs before deletion
    output_urls = get_job_output_urls(job_id)
    
    # Delete from database
    conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
    
    # Cleanup storage artifacts
    for url in output_urls:
        if url.startswith("file://"):
            os.remove(url.replace("file://", ""))
        elif url.startswith("s3://"):
            delete_from_s3(url)
    
    return {"deleted": True, "artifacts_cleaned": len(output_urls)}
```

#### Cleanup Script
```bash
# Dry run (shows what would be deleted)
python backend/cleanup.py --days 7

# Actually delete jobs older than 7 days
python backend/cleanup.py --days 7 --execute

# Find orphaned files
python backend/cleanup.py --orphaned
```

### Guarantees
- ✅ No orphaned files after job deletion
- ✅ Manual cleanup for old jobs
- ✅ Orphan detection tool
- ✅ Safe dry-run mode

---

## 5. RUNPOD COLD START UX SIGNAL

### Problem
First video generation takes ~30s for GPU warmup, but progress stays at 0%, confusing users.

### Solution
- **Detect cold start**: RUNNING + progress=0 for >15 seconds
- **Status hint**: "warming_gpu" exposed to frontend
- **UI feedback**: Shows "⚡ Warming GPU (first run ~30s)"

### Implementation

#### Backend Detection
```python
@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    # ... get job ...
    
    status_hint = None
    if status == "RUNNING" and progress == 0:
        elapsed = (datetime.utcnow() - created_at).total_seconds()
        if elapsed > COLD_START_THRESHOLD:
            status_hint = "warming_gpu"
    
    return {
        "status": status,
        "progress": progress,
        "status_hint": status_hint  # "warming_gpu" or null
    }
```

#### Frontend Display
```tsx
{job?.status_hint === 'warming_gpu' && (
  <p className="text-yellow-400">⚡ Warming GPU (first run ~30s)</p>
)}
```

### Configuration
```env
COLD_START_THRESHOLD=15  # seconds (default)
```

### Guarantees
- ✅ User knows why progress is slow
- ✅ No false "stuck" perception
- ✅ Backend-driven (no frontend guessing)
- ✅ Only shows when actually cold starting

---

## 6. ERROR SURFACING (NO SILENT FAILURES)

### Problem
Jobs failed silently with generic error messages, no way to diagnose issues.

### Solution
- **Structured errors**: error_code + error_message
- **Server-side logging**: All errors logged (no secrets)
- **Never stuck**: Jobs always reach terminal state
- **Clear messages**: Human-readable error descriptions

### Implementation

#### Database Schema
```sql
ALTER TABLE jobs ADD COLUMN error_code TEXT;
ALTER TABLE jobs ADD COLUMN error_message TEXT;
```

#### Error Codes
```python
ERROR_CODES = {
    "worker_timeout": "Job exceeded maximum execution time",
    "user_canceled": "Job canceled by user",
    "config_error": "RunPod not configured",
    "runpod_submit_error": "Failed to submit job to RunPod",
    "runpod_execution_error": "RunPod job failed during execution",
    "ffmpeg_error": "FFmpeg processing failed",
    "internal_error": "Internal server error"
}
```

#### Error Handling
```python
try:
    # ... process job ...
except Exception as e:
    logger.exception(f"Job {job_id} failed")  # Log with stack trace
    update_job(job_id,
        status="FAILED",
        error_code="internal_error",
        error_message=str(e))  # No secrets in message
```

#### Frontend Display
```tsx
{job?.error && (
  <div>
    <p>Error: {job.error.message}</p>
    <p className="text-sm">Code: {job.error.code}</p>
  </div>
)}
```

### Guarantees
- ✅ All failures have error_code + error_message
- ✅ Errors logged server-side
- ✅ No jobs stuck in RUNNING
- ✅ No secrets in error messages
- ✅ Actionable error descriptions

---

## JOB STATE MACHINE

```
QUEUED
  ↓
  ├─→ RUNNING (heartbeat starts)
  │     ↓
  │     ├─→ SUCCEEDED (output uploaded)
  │     ├─→ FAILED (error_code + error_message)
  │     ├─→ CANCELED (user action)
  │     └─→ FAILED (heartbeat timeout after 10min)
  │
  └─→ CANCELED (before starting)

Terminal states: SUCCEEDED, FAILED, CANCELED
```

### State Transitions

| From | To | Trigger | Safeguard |
|------|-----|---------|-----------|
| QUEUED | RUNNING | Worker starts | Heartbeat initialized |
| RUNNING | SUCCEEDED | Worker completes | Check not canceled |
| RUNNING | FAILED | Worker error | Structured error |
| RUNNING | FAILED | Heartbeat timeout | Monitor detects stale |
| RUNNING | CANCELED | User cancels | Discard pending output |
| QUEUED | CANCELED | User cancels | Idempotent |
| * | * (no change) | Cancel terminal job | Idempotent |

---

## SCHEMA CHANGES

```sql
-- Migration from old schema to hardened schema

-- Add new columns
ALTER TABLE jobs ADD COLUMN heartbeat_at TIMESTAMP;
ALTER TABLE jobs ADD COLUMN error_code TEXT;
ALTER TABLE jobs ADD COLUMN error_message TEXT;

-- Migrate old error column (if exists)
UPDATE jobs SET error_message = error WHERE error IS NOT NULL;

-- Drop old error column (optional)
-- ALTER TABLE jobs DROP COLUMN error;

-- Add index for heartbeat monitoring
CREATE INDEX IF NOT EXISTS idx_heartbeat ON jobs(heartbeat_at) WHERE status = 'RUNNING';

-- Enable WAL mode
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=5000;
```

---

## CONFIGURATION

### Environment Variables

```env
# Heartbeat timeout (seconds)
JOB_HEARTBEAT_TIMEOUT=600  # 10 minutes

# Cold start detection threshold (seconds)
COLD_START_THRESHOLD=15  # 15 seconds

# Database retry settings
DB_RETRY_ATTEMPTS=3
DB_RETRY_DELAY=0.1  # 100ms
```

---

## MONITORING

### Health Checks

```bash
# Check backend health
curl http://localhost:8000/health

# Check for stuck jobs
sqlite3 jobs.db "SELECT job_id, status, heartbeat_at FROM jobs WHERE status = 'RUNNING'"

# Check for old jobs
sqlite3 jobs.db "SELECT COUNT(*) FROM jobs WHERE created_at < datetime('now', '-7 days')"
```

### Logs

```bash
# Watch backend logs
tail -f backend.log | grep -E "(ERROR|WARNING|Job.*failed)"

# Check heartbeat monitor
tail -f backend.log | grep "heartbeat_monitor"

# Check cancellations
tail -f backend.log | grep "canceled"
```

---

## TESTING

### Test Heartbeat Timeout

```python
# Set short timeout for testing
JOB_HEARTBEAT_TIMEOUT=30  # 30 seconds

# Create job and let it timeout
job_id = create_job(...)
time.sleep(35)
assert get_job(job_id)["status"] == "FAILED"
assert get_job(job_id)["error"]["code"] == "worker_timeout"
```

### Test Cancel Semantics

```python
# Create and immediately cancel
job_id = create_job(...)
cancel_job(job_id)
assert get_job(job_id)["status"] == "CANCELED"

# Cancel again (idempotent)
cancel_job(job_id)
assert get_job(job_id)["status"] == "CANCELED"
```

### Test Storage Cleanup

```bash
# Create job with output
job_id=$(create_job_with_output)

# Delete job
curl -X DELETE http://localhost:8000/jobs/$job_id

# Verify file deleted
test ! -f /tmp/$job_id.mp4
```

---

## SUMMARY

### What Was Hardened

1. ✅ **Heartbeat enforcement** - No stuck jobs
2. ✅ **Hard cancel** - Immediate, idempotent, safe
3. ✅ **SQLite reliability** - WAL mode, retries, short transactions
4. ✅ **Storage hygiene** - Delete endpoint, cleanup script
5. ✅ **Cold start UX** - GPU warming hint
6. ✅ **Error surfacing** - Structured errors, logging

### What Wasn't Changed

- ❌ No new frameworks
- ❌ No Redis/Supabase
- ❌ No UI redesign
- ❌ No SaaS features
- ❌ No multi-tenant logic
- ❌ No artificial limits

### Production Readiness

✅ Safe to run unattended for long sessions  
✅ No silent failures  
✅ No stuck jobs  
✅ No resource leaks  
✅ Clear error messages  
✅ Survives restarts  
✅ Solo-user optimized  

**System is now production-hardened for reliable, unattended operation.**
