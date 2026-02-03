import os
import time
import traceback
import uuid
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Force all caches to /workspace
os.environ.setdefault("HF_HOME", "/workspace/hf")
os.environ.setdefault("TRANSFORMERS_CACHE", "/workspace/hf")
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", "/workspace/hf")
os.environ.setdefault("DIFFUSERS_CACHE", "/workspace/hf")
os.environ.setdefault("TORCH_HOME", "/workspace/torch")
os.environ.setdefault("TMPDIR", "/workspace/tmp")

# Create directories
for d in ["/workspace/hf", "/workspace/torch", "/workspace/tmp", "/workspace/outputs"]:
    os.makedirs(d, exist_ok=True)

WORKER_VERSION = "v9-pod-http"
BUILD_ID = "v9-20260201-pod"
MODEL_ID = "THUDM/CogVideoX-2b"
OUTPUT_DIR = "/workspace/outputs"

app = FastAPI(title="CogVideoX Worker API")

# Lazy imports
_torch = None
_pipeline_class = None
_export_to_video = None
_pipeline_instance = None

# Job storage
jobs: Dict[str, dict] = {}
executor = ThreadPoolExecutor(max_workers=1)

def lazy_import_ml():
    global _torch, _pipeline_class, _export_to_video
    if _torch is None:
        import torch
        from diffusers.pipelines.cogvideo import CogVideoXPipeline
        from diffusers.utils import export_to_video
        _torch = torch
        _pipeline_class = CogVideoXPipeline
        _export_to_video = export_to_video

def log(msg: str):
    print(f"[{WORKER_VERSION}] {msg}", flush=True)

def validate_env():
    required = ["R2_BUCKET", "R2_PUBLIC_BASE_URL", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_ENDPOINT_URL"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing env vars: {', '.join(missing)}")

def get_s3_client():
    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", "auto"),
        endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

def load_pipeline():
    global _pipeline_instance
    if _pipeline_instance is None:
        lazy_import_ml()
        log(f"Loading {MODEL_ID}...")
        _pipeline_instance = _pipeline_class.from_pretrained(
            MODEL_ID,
            torch_dtype=_torch.float16,
        ).to("cuda")
        _pipeline_instance.enable_model_cpu_offload()
        _pipeline_instance.vae.enable_slicing()
        log("Pipeline loaded")
    return _pipeline_instance

def generate_video_sync(job_id: str, prompt: str, duration: int):
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        
        validate_env()
        
        jobs[job_id]["progress"] = 25
        pipe = load_pipeline()
        
        output_path = os.path.join(OUTPUT_DIR, f"{job_id}_final.mp4")
        
        jobs[job_id]["progress"] = 40
        log(f"Running inference for {job_id}...")
        
        video_frames = pipe(
            prompt=prompt,
            num_frames=49,
            guidance_scale=6.0,
            num_inference_steps=50,
        ).frames[0]
        
        jobs[job_id]["progress"] = 75
        log(f"Generated {len(video_frames)} frames")
        
        jobs[job_id]["progress"] = 90
        _export_to_video(video_frames, output_path, fps=8)
        
        if not os.path.exists(output_path):
            raise RuntimeError("Video file not created")
        
        # Upload to R2
        bucket = os.getenv("R2_BUCKET")
        public_base = os.getenv("R2_PUBLIC_BASE_URL").rstrip("/")
        key = f"videos/{job_id}/final.mp4"
        
        s3 = get_s3_client()
        with open(output_path, "rb") as f:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=f,
                ContentType="video/mp4",
                CacheControl="public, max-age=31536000",
            )
        
        url = f"{public_base}/{key}"
        
        # Cleanup
        try:
            os.remove(output_path)
        except Exception:
            pass
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["output_url"] = url
        log(f"Job {job_id} completed: {url}")
        
    except Exception as e:
        tb = traceback.format_exc()
        log(f"Job {job_id} failed: {e}\n{tb}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

class GenerateRequest(BaseModel):
    prompt: str
    duration: int = 5

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "worker_version": WORKER_VERSION,
        "build_id": BUILD_ID,
        "model": MODEL_ID
    }

@app.post("/generate")
async def generate(req: GenerateRequest):
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(400, "Missing required field: prompt")
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "id": job_id,
        "status": "queued",
        "progress": 0,
        "prompt": req.prompt,
        "duration": req.duration,
        "created_at": time.time()
    }
    
    # Start async processing
    executor.submit(generate_video_sync, job_id, req.prompt, req.duration)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Job submitted successfully"
    }

@app.get("/status/{job_id}")
async def status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    
    job = jobs[job_id]
    response = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "worker_version": WORKER_VERSION,
        "build_id": BUILD_ID
    }
    
    if job["status"] == "completed":
        response["output_url"] = job.get("output_url")
    elif job["status"] == "failed":
        response["error"] = job.get("error")
    
    return response

if __name__ == "__main__":
    import uvicorn
    log(f"BOOT build_id={BUILD_ID} worker_version={WORKER_VERSION}")
    uvicorn.run(app, host="0.0.0.0", port=8001)
