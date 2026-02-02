import os
import time
import traceback
import runpod
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from TTS.api import TTS

WORKER_VERSION = "v1-coqui-tts"
MODEL_NAME = "tts_models/en/ljspeech/tacotron2-DDC"

def log(msg: str):
    print(f"[{WORKER_VERSION}] {msg}", flush=True)

def safe_progress(job, pct: int):
    try:
        pct = max(0, min(100, int(pct)))
        runpod.serverless.progress_update(job, pct)
    except Exception as e:
        log(f"progress_update failed (ignored): {e}")

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

# Global TTS model
_tts = None

def load_tts():
    global _tts
    if _tts is None:
        log(f"Loading {MODEL_NAME}...")
        _tts = TTS(MODEL_NAME, gpu=True)
        log("TTS model loaded")
    return _tts

def generate_audio(text: str, output_path: str, job):
    log(f"Generating audio: text='{text[:50]}...'")
    
    safe_progress(job, 30)
    tts = load_tts()
    
    safe_progress(job, 60)
    log("Running TTS inference...")
    tts.tts_to_file(text=text, file_path=output_path)
    
    if not os.path.exists(output_path):
        raise RuntimeError("Audio file not created")
    
    size = os.path.getsize(output_path)
    log(f"Audio created: {size} bytes")

def upload_to_r2(file_path: str, job_id: str) -> str:
    bucket = os.getenv("R2_BUCKET")
    public_base = os.getenv("R2_PUBLIC_BASE_URL").rstrip("/")
    key = f"audio/{job_id}/voice.wav"
    
    log(f"Uploading to R2: {key}")
    
    s3 = get_s3_client()
    with open(file_path, "rb") as f:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=f,
            ContentType="audio/wav",
            CacheControl="public, max-age=31536000",
        )
    
    url = f"{public_base}/{key}"
    log(f"Upload complete: {url}")
    return url

def handler(job):
    job_id = job.get("id", f"job-{int(time.time())}")
    try:
        log(f"Job started: {job_id}")
        payload = job.get("input", {}) or {}
        
        text = payload.get("text")
        
        if not text or not str(text).strip():
            return {
                "ok": False,
                "error_code": "invalid_input",
                "error_message": "Missing required field: text",
                "worker_version": WORKER_VERSION,
            }
        
        safe_progress(job, 10)
        validate_env()
        
        output_path = f"/tmp/{job_id}_voice.wav"
        generate_audio(str(text), output_path, job)
        
        safe_progress(job, 85)
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
            "meta": {
                "model": "coqui-tts",
                "voice": "ljspeech",
            },
        }
    
    except ValueError as e:
        log(f"Config error: {e}")
        return {"ok": False, "error_code": "config_error", "error_message": str(e), "worker_version": WORKER_VERSION}
    except RuntimeError as e:
        log(f"Runtime error: {e}")
        return {"ok": False, "error_code": "runtime_error", "error_message": str(e), "worker_version": WORKER_VERSION}
    except Exception as e:
        tb = traceback.format_exc()
        log(f"Unexpected error: {e}\n{tb}")
        return {"ok": False, "error_code": "internal_error", "error_message": str(e), "worker_version": WORKER_VERSION}

if __name__ == "__main__":
    log("Coqui TTS worker starting...")
    runpod.serverless.start({"handler": handler})
