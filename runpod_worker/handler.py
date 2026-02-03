import os
import time
import traceback
import runpod  # type: ignore
import boto3  # type: ignore
from botocore.exceptions import ClientError, NoCredentialsError  # type: ignore

# Force all temp operations to /runpod-volume
os.environ.setdefault("TMPDIR", "/runpod-volume/tmp")
os.makedirs(os.environ["TMPDIR"], exist_ok=True)

WORKER_VERSION = "v8-diskfix"
BUILD_ID = "v8-20260201-1"
MODEL_ID = "THUDM/CogVideoX-2b"

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/workspace/tmp")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Lazy imports - only load heavy deps when needed
_torch = None
_pipeline_class = None
_export_to_video = None
_pipeline_instance = None

def lazy_import_ml():
    global _torch, _pipeline_class, _export_to_video
    if _torch is None:
        import torch  # type: ignore
        from diffusers.pipelines.cogvideo import CogVideoXPipeline  # type: ignore
        from diffusers.utils import export_to_video  # type: ignore
        _torch = torch
        _pipeline_class = CogVideoXPipeline
        _export_to_video = export_to_video

def log(msg: str):
    print(f"[{WORKER_VERSION}] {msg}", flush=True)

def log_disk(path="/runpod-volume"):
    try:
        st = os.statvfs(path)
        free_gb = (st.f_bavail * st.f_frsize) / (1024**3)
        log(f"disk free at {path}: {free_gb:.2f} GB")
    except Exception as e:
        log(f"disk check failed: {e}")

def safe_progress(job, pct: int):
    """Progress updates must never crash the job."""
    try:
        pct = max(0, min(100, int(pct)))
        runpod.serverless.progress_update(job, pct)
    except Exception as e:
        log(f"progress_update failed (ignored): {e}")

def validate_env():
    required = [
        "R2_BUCKET",
        "R2_PUBLIC_BASE_URL",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_ENDPOINT_URL",
    ]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")

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
        
        # Safe VAE optimization
        if hasattr(_pipeline_instance, "vae"):
            vae = _pipeline_instance.vae
            if hasattr(vae, "enable_slicing"):
                vae.enable_slicing()
                log("VAE slicing enabled")
            elif hasattr(vae, "enable_tiling"):
                vae.enable_tiling()
                log("VAE tiling enabled")
            else:
                log("VAE slicing/tiling not supported (ok)")
        
        log("Pipeline loaded")
    return _pipeline_instance

def generate_video(prompt: str, duration: int, output_path: str, job):
    log(f"Generating video: prompt='{prompt[:50]}...' duration={duration}s")
    
    safe_progress(job, 25)
    pipe = load_pipeline()
    
    # CogVideoX generates 49 frames (6s at 8fps)
    num_frames = 49
    fps = 8
    
    safe_progress(job, 40)
    log("Running inference...")
    
    video_frames = pipe(
        prompt=prompt,
        num_frames=num_frames,
        guidance_scale=6.0,
        num_inference_steps=50,
    ).frames[0]
    
    safe_progress(job, 75)
    log(f"Generated {len(video_frames)} frames")
    
    safe_progress(job, 90)
    log("Encoding MP4...")
    _export_to_video(video_frames, output_path, fps=fps)
    
    if not os.path.exists(output_path):
        raise RuntimeError("Video file not created")
    
    size = os.path.getsize(output_path)
    log(f"MP4 created: {size} bytes")

def upload_to_r2(file_path: str, job_id: str) -> str:
    bucket = os.getenv("R2_BUCKET")
    public_base = os.getenv("R2_PUBLIC_BASE_URL").rstrip("/")
    key = f"videos/{job_id}/final.mp4"

    log(f"Uploading to R2 bucket={bucket} key={key}")

    try:
        s3 = get_s3_client()
        with open(file_path, "rb") as f:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=f,
                ContentType="video/mp4",
                CacheControl="public, max-age=31536000",
            )
        url = f"{public_base}/{key}"
        log(f"Upload complete: {url}")
        return url
    except NoCredentialsError:
        raise RuntimeError("R2 credentials not configured")
    except ClientError as e:
        msg = e.response.get("Error", {}).get("Message", str(e))
        raise RuntimeError(f"R2 upload failed: {msg}")

def handler(job):
    job_id = job.get("id", f"job-{int(time.time())}")
    try:
        log(f"Job started: {job_id}")
        log_disk("/runpod-volume")
        log_disk("/tmp")
        
        payload = job.get("input", {}) or {}

        prompt = payload.get("prompt")
        duration = payload.get("duration", 5)

        if not prompt or not str(prompt).strip():
            return {
                "ok": False,
                "error_code": "invalid_input",
                "error_message": "Missing required field: prompt",
                "worker_version": WORKER_VERSION,
                "build_id": BUILD_ID,
            }

        safe_progress(job, 10)
        validate_env()

        output_path = os.path.join(OUTPUT_DIR, f"{job_id}_final.mp4")
        generate_video(str(prompt), int(duration), output_path, job)

        public_url = upload_to_r2(output_path, job_id)

        try:
            os.remove(output_path)
        except Exception:
            pass

        safe_progress(job, 100)
        return {
            "ok": True,
            "output_url": public_url,
            "worker_version": WORKER_VERSION,
            "build_id": BUILD_ID,
            "meta": {
                "model": "cogvideox-2b",
                "fps": 8,
            },
        }

    except (ValueError, ImportError) as e:
        log(f"Config/Import error: {e}")
        return {"ok": False, "error_code": "config_error", "error_message": str(e), "worker_version": WORKER_VERSION, "build_id": BUILD_ID}
    except RuntimeError as e:
        log(f"Runtime error: {e}")
        return {"ok": False, "error_code": "runtime_error", "error_message": str(e), "worker_version": WORKER_VERSION, "build_id": BUILD_ID}
    except Exception as e:
        tb = traceback.format_exc()
        log(f"Unexpected error: {e}\n{tb}")
        return {"ok": False, "error_code": "internal_error", "error_message": str(e), "worker_version": WORKER_VERSION, "build_id": BUILD_ID}

if __name__ == "__main__":
    log(f"BOOT build_id={BUILD_ID} worker_version={WORKER_VERSION}")
    runpod.serverless.start({"handler": handler})
