"""
Add these endpoints to backend/main.py or import as module
"""

# Add to existing imports
RUNPOD_VIDEO_ENDPOINT = os.getenv("RUNPOD_VIDEO_ENDPOINT")  # CogVideoX worker
RUNPOD_TTS_ENDPOINT = os.getenv("RUNPOD_TTS_ENDPOINT")      # Coqui TTS worker
RUNPOD_LIPSYNC_ENDPOINT = os.getenv("RUNPOD_LIPSYNC_ENDPOINT")  # Wav2Lip worker
RUNPOD_LORA_ENDPOINT = os.getenv("RUNPOD_LORA_ENDPOINT")    # LoRA training worker

# Video generation (replace existing /jobs endpoint logic)
@app.post("/jobs/video")
async def create_video_job(prompt: str, duration: int = 5, bg: BackgroundTasks = None):
    """Generate AI video using CogVideoX"""
    job_id = str(uuid.uuid4())
    conn = get_db_connection()
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO jobs (job_id, type, status, params, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, "VIDEO", "QUEUED", json.dumps({"prompt": prompt, "duration": duration}), now, now)
    )
    conn.commit()
    conn.close()
    
    bg.add_task(process_runpod_job, job_id, RUNPOD_VIDEO_ENDPOINT, {"prompt": prompt, "duration": duration})
    
    return {"job_id": job_id, "status": "QUEUED", "type": "VIDEO"}

# TTS generation
@app.post("/jobs/tts")
async def create_tts_job(text: str, bg: BackgroundTasks):
    """Generate voice audio using Coqui TTS"""
    job_id = str(uuid.uuid4())
    conn = get_db_connection()
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO jobs (job_id, type, status, params, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, "TTS", "QUEUED", json.dumps({"text": text}), now, now)
    )
    conn.commit()
    conn.close()
    
    bg.add_task(process_runpod_job, job_id, RUNPOD_TTS_ENDPOINT, {"text": text})
    
    return {"job_id": job_id, "status": "QUEUED", "type": "TTS"}

# Lipsync
@app.post("/jobs/lipsync")
async def create_lipsync_job(face_url: str, audio_url: str, bg: BackgroundTasks):
    """Generate lipsync video using Wav2Lip"""
    job_id = str(uuid.uuid4())
    conn = get_db_connection()
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO jobs (job_id, type, status, params, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, "LIPSYNC", "QUEUED", json.dumps({"face_url": face_url, "audio_url": audio_url}), now, now)
    )
    conn.commit()
    conn.close()
    
    bg.add_task(process_runpod_job, job_id, RUNPOD_LIPSYNC_ENDPOINT, {"face_url": face_url, "audio_url": audio_url})
    
    return {"job_id": job_id, "status": "QUEUED", "type": "LIPSYNC"}

# LoRA training
@app.post("/jobs/lora")
async def create_lora_job(images: list[str], name: str, bg: BackgroundTasks):
    """Train LoRA model"""
    job_id = str(uuid.uuid4())
    conn = get_db_connection()
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO jobs (job_id, type, status, params, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (job_id, "LORA", "QUEUED", json.dumps({"images": images, "name": name}), now, now)
    )
    conn.commit()
    conn.close()
    
    bg.add_task(process_runpod_job, job_id, RUNPOD_LORA_ENDPOINT, {"images": images, "name": name})
    
    return {"job_id": job_id, "status": "QUEUED", "type": "LORA"}

# Generic RunPod job processor (replaces process_job)
async def process_runpod_job(job_id: str, endpoint: str, params: dict):
    """Submit to any RunPod endpoint and poll for results"""
    try:
        update_job(job_id, status="RUNNING", progress=5, heartbeat=True)
        
        if not endpoint or not RUNPOD_API_KEY:
            update_job(job_id, status="FAILED", error_code="config_error", error_message="RunPod not configured")
            return
        
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"{endpoint}/run",
                headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"},
                json={"input": params}
            )
            
            if resp.status_code != 200:
                update_job(job_id, status="FAILED", error_code="runpod_submit_error", error_message=f"RunPod returned {resp.status_code}")
                return
            
            runpod_data = resp.json()
            runpod_job_id = runpod_data.get("id")
            
            if not runpod_job_id:
                update_job(job_id, status="FAILED", error_code="runpod_invalid_response", error_message="No job ID returned")
                return
            
            update_job(job_id, runpod_job_id=runpod_job_id, progress=10, heartbeat=True)
            
            # Poll for completion
            while True:
                if get_job_status(job_id) == "CANCELED":
                    break
                
                status_resp = await client.get(
                    f"{endpoint}/status/{runpod_job_id}",
                    headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"}
                )
                status_data = status_resp.json()
                
                runpod_status = status_data.get("status")
                progress = status_data.get("progress", 10)
                
                update_job(job_id, progress=min(progress, 95), heartbeat=True)
                
                if runpod_status == "COMPLETED":
                    if get_job_status(job_id) == "CANCELED":
                        break
                    
                    output = status_data.get("output", {})
                    output_url = output.get("output_url")
                    
                    if output_url:
                        update_job(job_id, status="SUCCEEDED", progress=100, output_urls=[output_url], heartbeat=True)
                    else:
                        update_job(job_id, status="SUCCEEDED", progress=100, output_urls=[], heartbeat=True)
                    break
                    
                elif runpod_status in ["FAILED", "CANCELLED"]:
                    error_msg = status_data.get("error", "RunPod job failed")
                    update_job(job_id, status="FAILED", error_code="runpod_execution_error", error_message=error_msg)
                    break
                
                await asyncio.sleep(2)
                
    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        update_job(job_id, status="FAILED", error_code="internal_error", error_message=str(e))
