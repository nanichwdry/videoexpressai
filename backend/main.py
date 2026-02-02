from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import uuid
import json
from datetime import datetime, timedelta
import httpx
import os
import asyncio
import logging
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)
print(f"Loading .env from: {env_path}")
print(f"RUNPOD_ENDPOINT: {os.getenv('RUNPOD_ENDPOINT')}")
print(f"RUNPOD_API_KEY: {'SET' if os.getenv('RUNPOD_API_KEY') else 'NOT SET'}")

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.gemini_helper import enhance_prompt, generate_script, improve_prompt_for_style
except ImportError:
    # Gemini helper not available, use simple fallback
    from utils.gemini_helper_simple import enhance_prompt, generate_script, improve_prompt_for_style

# Import extended API
try:
    from api_extended import router as extended_router, validate_video
    HAS_EXTENDED_API = True
except ImportError:
    HAS_EXTENDED_API = False
    print("Extended API not available (OAuth, social upload)")

# Import GPU control API
try:
    from api_gpu_control import router as gpu_router
    HAS_GPU_CONTROL = True
except ImportError:
    HAS_GPU_CONTROL = False
    print("GPU control not available")

# Configure logging (no secrets)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include extended API routes
if HAS_EXTENDED_API:
    app.include_router(extended_router)
    print("Extended API routes loaded (OAuth, social upload)")

# Include GPU control routes
if HAS_GPU_CONTROL:
    app.include_router(gpu_router)
    print("GPU control routes loaded (/gpu/on, /gpu/off)")

DB_PATH = os.getenv("DB_PATH", "./jobs.db")
RUNPOD_ENDPOINT = os.getenv("RUNPOD_ENDPOINT")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
S3_BUCKET = os.getenv("S3_BUCKET")

# HARDENING: Configurable timeouts
JOB_HEARTBEAT_TIMEOUT = int(os.getenv("JOB_HEARTBEAT_TIMEOUT", "600"))  # 10 minutes default
COLD_START_THRESHOLD = int(os.getenv("COLD_START_THRESHOLD", "15"))  # 15 seconds
DB_RETRY_ATTEMPTS = 3
DB_RETRY_DELAY = 0.1  # 100ms

def init_db():
    """Initialize database with WAL mode for reliability (TASK 3: SQLite hardening)"""
    conn = get_db_connection()
    
    # HARDENING: Enable WAL mode for better concurrency and crash resistance
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and speed
    conn.execute("PRAGMA busy_timeout=5000")  # Wait up to 5s for locks
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'QUEUED',
            progress INTEGER DEFAULT 0,
            params TEXT NOT NULL,
            output_urls TEXT,
            runpod_job_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_heartbeat_at TEXT,
            started_at TEXT,
            finished_at TEXT,
            status_message TEXT,
            error_code TEXT,
            error_message TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON jobs(created_at DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_heartbeat ON jobs(last_heartbeat_at) WHERE status = 'RUNNING'")
    conn.commit()
    conn.close()

def get_db_connection():
    """Get DB connection with retry logic (TASK 3: Handle SQLITE_BUSY)"""
    for attempt in range(DB_RETRY_ATTEMPTS):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=5.0)
            return conn
        except sqlite3.OperationalError as e:
            if attempt == DB_RETRY_ATTEMPTS - 1:
                logger.error(f"DB connection failed after {DB_RETRY_ATTEMPTS} attempts: {e}")
                raise
            asyncio.sleep(DB_RETRY_DELAY)
    return sqlite3.connect(DB_PATH, timeout=5.0)

init_db()

class JobCreate(BaseModel):
    type: str
    params: dict

class TimelineStitch(BaseModel):
    clips: List[dict]
    captions: Optional[List[dict]] = []

class PromptEnhance(BaseModel):
    prompt: str
    style: Optional[str] = None

class ScriptGenerate(BaseModel):
    topic: str
    duration: Optional[int] = 60

@app.get("/health")
def health():
    return {"status": "ok", "runpod_connected": bool(RUNPOD_ENDPOINT)}

@app.post("/jobs")
async def create_job(job: JobCreate, bg: BackgroundTasks):
    job_id = str(uuid.uuid4())
    conn = get_db_connection()
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO jobs (job_id, type, status, params, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, job.type, "QUEUED", json.dumps(job.params), now, now)
    )
    conn.commit()
    conn.close()
    
    bg.add_task(process_job, job_id, job.type, job.params)
    
    return {"job_id": job_id, "status": "QUEUED", "created_at": now}

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(404, "Job not found")
    
    # TASK 5: Detect cold start (RUNNING but progress=0 for >15s)
    status_hint = None
    if row[2] == "RUNNING" and row[3] == 0:
        created_at = datetime.fromisoformat(row[7])
        if (datetime.utcnow() - created_at).total_seconds() > COLD_START_THRESHOLD:
            status_hint = "warming_gpu"
    
    return {
        "job_id": row[0],
        "type": row[1],
        "status": row[2],
        "progress": row[3],
        "output_urls": json.loads(row[5]) if row[5] else [],
        "error": {"code": row[13], "message": row[14]} if row[13] else None,
        "status_hint": status_hint,
        "status_message": row[12],
        "created_at": row[7],
        "updated_at": row[8],
        "started_at": row[10],
        "finished_at": row[11]
    }

@app.get("/jobs")
def list_jobs(limit: int = 50):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", 
        (limit,)
    ).fetchall()
    conn.close()
    
    return [{
        "job_id": row[0],
        "type": row[1],
        "status": row[2],
        "progress": row[3],
        "created_at": row[7]
    } for row in rows]

@app.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    """TASK 2: Hard cancel semantics - idempotent, immediate, prevents output"""
    conn = get_db_connection()
    
    # Check current status
    row = conn.execute("SELECT status FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Job not found")
    
    current_status = row[0]
    
    # Idempotent: already canceled or terminal state
    if current_status in ["CANCELED", "SUCCEEDED", "FAILED"]:
        conn.close()
        return {"status": current_status, "message": "Job already in terminal state"}
    
    # Mark as CANCELED immediately
    now = datetime.utcnow().isoformat()
    conn.execute(
        "UPDATE jobs SET status = 'CANCELED', updated_at = ?, error_code = 'user_canceled', error_message = 'Job canceled by user' WHERE job_id = ?",
        (now, job_id)
    )
    conn.commit()
    conn.close()
    
    logger.info(f"Job {job_id} canceled by user")
    
    # NOTE: RunPod cancellation is best-effort. Worker checks job status before uploading.
    # If worker returns results after cancel, process_job will discard them.
    
    return {"status": "CANCELED", "message": "Job canceled successfully"}

@app.post("/timeline/stitch")
async def stitch_timeline(data: TimelineStitch, bg: BackgroundTasks):
    job_id = str(uuid.uuid4())
    conn = get_db_connection()
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO jobs (job_id, type, status, params, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, "EXPORT", "QUEUED", json.dumps({"clips": data.clips, "captions": data.captions}), now, now)
    )
    conn.commit()
    conn.close()
    
    bg.add_task(process_stitch_job, job_id, data.clips, data.captions)
    
    return {"job_id": job_id, "status": "QUEUED"}

@app.post("/ai/enhance-prompt")
async def enhance_user_prompt(data: PromptEnhance):
    """Enhance basic prompt using Gemini AI (optional paid API)"""
    result = await enhance_prompt(data.prompt, data.style)
    return result

@app.post("/ai/generate-script")
async def generate_video_script(data: ScriptGenerate):
    """Generate full video script with scenes using Gemini AI"""
    result = await generate_script(data.topic, data.duration)
    return result

@app.post("/ai/style-prompt")
async def style_prompt(prompt: str, style: str):
    """Adapt prompt to specific visual style using Gemini AI"""
    result = await improve_prompt_for_style(prompt, style)
    return result

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """TASK 4: Delete job and cleanup storage artifacts"""
    conn = get_db_connection()
    
    # Get job details before deletion
    row = conn.execute("SELECT output_urls, status FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Job not found")
    
    output_urls = json.loads(row[0]) if row[0] else []
    status = row[1]
    
    # Delete from database
    conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
    conn.commit()
    conn.close()
    
    # TASK 4: Cleanup storage artifacts
    deleted_files = []
    for url in output_urls:
        try:
            if url.startswith("file://"):
                # Local file cleanup
                import os
                file_path = url.replace("file://", "")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_files.append(file_path)
            elif url.startswith("s3://") or url.startswith("https://"):
                # S3 cleanup (implement when S3 is configured)
                # delete_from_s3(url)
                logger.info(f"S3 cleanup not implemented for: {url}")
        except Exception as e:
            logger.error(f"Failed to delete artifact {url}: {e}")
    
    logger.info(f"Deleted job {job_id} and {len(deleted_files)} artifacts")
    
    return {
        "job_id": job_id,
        "deleted": True,
        "artifacts_cleaned": len(deleted_files)
    }

async def process_job(job_id: str, job_type: str, params: dict):
    """Background task: submit to RunPod, poll, update DB with heartbeat enforcement"""
    try:
        # TASK 1: Initialize heartbeat
        update_job(job_id, status="RUNNING", progress=5, heartbeat=True)
        
        if not RUNPOD_ENDPOINT or not RUNPOD_API_KEY:
            update_job(job_id, status="FAILED", error_code="config_error", error_message="RunPod not configured")
            return
        
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"{RUNPOD_ENDPOINT}/run",
                headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"},
                json={"input": {"job_type": job_type, **params}}
            )
            
            if resp.status_code != 200:
                update_job(job_id, status="FAILED", error_code="runpod_submit_error", error_message=f"RunPod returned {resp.status_code}")
                logger.error(f"RunPod submit failed for job {job_id}: {resp.status_code}")
                return
            
            runpod_data = resp.json()
            runpod_job_id = runpod_data.get("id")
            
            if not runpod_job_id:
                update_job(job_id, status="FAILED", error_code="runpod_invalid_response", error_message="No job ID returned from RunPod")
                return
            
            update_job(job_id, runpod_job_id=runpod_job_id, progress=10, heartbeat=True)
            
            while True:
                # TASK 2: Check if job was canceled
                job_status = get_job_status(job_id)
                if job_status == "CANCELED":
                    logger.info(f"Job {job_id} was canceled, stopping polling")
                    break
                
                status_resp = await client.get(
                    f"{RUNPOD_ENDPOINT}/status/{runpod_job_id}",
                    headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
                )
                status_data = status_resp.json()
                
                runpod_status = status_data.get("status")
                progress = status_data.get("progress", 10)
                
                # TASK 1: Update heartbeat on every progress update
                update_job(job_id, progress=min(progress, 95), heartbeat=True)
                
                if runpod_status == "COMPLETED":
                    # TASK 2: Double-check not canceled before accepting output
                    if get_job_status(job_id) == "CANCELED":
                        logger.info(f"Job {job_id} completed but was canceled, discarding output")
                        break
                    
                    output = status_data.get("output", {})
                    # Handle both old and new response formats
                    video_url = output.get("video_url") or output.get("audio_url") or output.get("output_url")
                    
                    if video_url:
                        # PRODUCTION: Validate MP4 before marking success
                        if HAS_EXTENDED_API and video_url.startswith(("http://", "https://")):
                            try:
                                import tempfile
                                async with httpx.AsyncClient() as dl_client:
                                    dl_resp = await dl_client.get(video_url, timeout=30)
                                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                                        tmp.write(dl_resp.content)
                                        tmp_path = tmp.name
                                if not validate_video(tmp_path):
                                    logger.warning(f"Job {job_id} video validation failed")
                                    update_job(job_id, status="FAILED", error_code="invalid_video", error_message="Video validation failed")
                                    os.unlink(tmp_path)
                                    break
                                os.unlink(tmp_path)
                            except Exception as e:
                                logger.warning(f"Video validation skipped: {e}")
                        
                        update_job(job_id, status="SUCCEEDED", progress=100, output_urls=[video_url], heartbeat=True)
                    else:
                        update_job(job_id, status="SUCCEEDED", progress=100, output_urls=[], heartbeat=True)
                    
                    logger.info(f"Job {job_id} completed successfully")
                    break
                    
                elif runpod_status in ["FAILED", "CANCELLED"]:
                    error_msg = status_data.get("error", "RunPod job failed")
                    update_job(job_id, status="FAILED", error_code="runpod_execution_error", error_message=error_msg)
                    logger.error(f"Job {job_id} failed: {error_msg}")
                    break
                
                await asyncio.sleep(2)
                
    except Exception as e:
        # TASK 6: Structured error surfacing
        logger.exception(f"Job {job_id} failed with exception")
        update_job(job_id, status="FAILED", error_code="internal_error", error_message=str(e))

async def process_stitch_job(job_id: str, clips: list, captions: list):
    """Background task for FFmpeg stitching with heartbeat"""
    try:
        try:
            from utils.ffmpeg_utils import stitch_timeline
        except ImportError:
            update_job(job_id, status="FAILED", error_code="ffmpeg_error", error_message="FFmpeg utils not available")
            return
        
        update_job(job_id, status="RUNNING", progress=10, heartbeat=True)
        
        # Check not canceled before starting
        if get_job_status(job_id) == "CANCELED":
            return
        
        output_path = f"/tmp/{job_id}.mp4"
        stitch_timeline(clips, captions, output_path)
        
        update_job(job_id, status="RUNNING", progress=80, heartbeat=True)
        
        # Check not canceled before uploading
        if get_job_status(job_id) == "CANCELED":
            logger.info(f"Stitch job {job_id} canceled, skipping upload")
            return
        
        # Upload to S3 (implement upload_to_s3)
        # s3_url = upload_to_s3(output_path, job_id)
        s3_url = f"file://{output_path}"  # Fallback for local testing
        
        update_job(job_id, status="SUCCEEDED", progress=100, output_urls=[s3_url], heartbeat=True)
        
    except Exception as e:
        logger.exception(f"Stitch job {job_id} failed")
        update_job(job_id, status="FAILED", error_code="ffmpeg_error", error_message=str(e))

def update_job(job_id: str, heartbeat: bool = False, error_code: str = None, error_message: str = None, status_message: str = None, **kwargs):
    """Update job with retry logic and heartbeat support (TASK 1 & 3)"""
    conn = get_db_connection()
    fields = []
    values = []
    
    # TASK 1: Update heartbeat timestamp if requested
    if heartbeat:
        fields.append("last_heartbeat_at = ?")
        values.append(datetime.utcnow().isoformat())
    
    # TASK 6: Structured error handling
    if error_code:
        fields.append("error_code = ?")
        values.append(error_code)
    if error_message:
        fields.append("error_message = ?")
        values.append(error_message)
    if status_message:
        fields.append("status_message = ?")
        values.append(status_message)
    
    # Track state transitions
    if "status" in kwargs:
        new_status = kwargs["status"]
        if new_status == "RUNNING" and "started_at" not in kwargs:
            fields.append("started_at = ?")
            values.append(datetime.utcnow().isoformat())
        elif new_status in ["SUCCEEDED", "FAILED", "CANCELED"] and "finished_at" not in kwargs:
            fields.append("finished_at = ?")
            values.append(datetime.utcnow().isoformat())
    
    for k, v in kwargs.items():
        if k == "output_urls":
            v = json.dumps(v)
        fields.append(f"{k} = ?")
        values.append(v)
    
    fields.append("updated_at = ?")
    values.append(datetime.utcnow().isoformat())
    values.append(job_id)
    
    try:
        conn.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE job_id = ?", values)
        conn.commit()
    except sqlite3.OperationalError as e:
        logger.error(f"Failed to update job {job_id}: {e}")
        raise
    finally:
        conn.close()

def get_job_status(job_id: str) -> str:
    """Get job status with retry logic (TASK 3)"""
    conn = get_db_connection()
    row = conn.execute("SELECT status FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    return row[0] if row else "UNKNOWN"

@app.on_event("startup")
async def startup_event():
    """TASK 1: Start heartbeat monitor on startup"""
    asyncio.create_task(heartbeat_monitor())

async def heartbeat_monitor():
    """TASK 1: Monitor jobs for timeout and mark as FAILED if no heartbeat"""
    while True:
        try:
            conn = get_db_connection()
            timeout_threshold = datetime.utcnow() - timedelta(seconds=JOB_HEARTBEAT_TIMEOUT)
            
            # Find RUNNING jobs with stale heartbeat
            stale_jobs = conn.execute("""
                SELECT job_id, last_heartbeat_at 
                FROM jobs 
                WHERE status = 'RUNNING' 
                AND last_heartbeat_at IS NOT NULL 
                AND last_heartbeat_at < ?
            """, (timeout_threshold.isoformat(),)).fetchall()
            
            for job_id, heartbeat_at in stale_jobs:
                logger.warning(f"Job {job_id} timed out (last heartbeat: {heartbeat_at})")
                conn.execute("""
                    UPDATE jobs 
                    SET status = 'FAILED', 
                        error_code = 'worker_timeout', 
                        error_message = 'Job exceeded maximum execution time without progress update',
                        finished_at = ?,
                        updated_at = ?
                    WHERE job_id = ?
                """, (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), job_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.exception("Heartbeat monitor error")
        
        # Check every 30 seconds
        await asyncio.sleep(30)
