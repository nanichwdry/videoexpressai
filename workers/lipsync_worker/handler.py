import os
import time
import traceback
import subprocess
import runpod
import boto3
import httpx
from botocore.exceptions import ClientError, NoCredentialsError

WORKER_VERSION = "v1-wav2lip"
WAV2LIP_REPO = "https://github.com/Rudrabha/Wav2Lip.git"
CHECKPOINT_URL = "https://github.com/Rudrabha/Wav2Lip/releases/download/models/wav2lip_gan.pth"

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

def download_file(url: str, output_path: str):
    log(f"Downloading {url}...")
    with httpx.stream("GET", url, follow_redirects=True, timeout=300) as resp:
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=8192):
                f.write(chunk)
    log(f"Downloaded to {output_path}")

def setup_wav2lip():
    if not os.path.exists("/app/Wav2Lip"):
        log("Cloning Wav2Lip repo...")
        subprocess.run(["git", "clone", WAV2LIP_REPO, "/app/Wav2Lip"], check=True)
    
    checkpoint_path = "/app/Wav2Lip/checkpoints/wav2lip_gan.pth"
    if not os.path.exists(checkpoint_path):
        os.makedirs("/app/Wav2Lip/checkpoints", exist_ok=True)
        download_file(CHECKPOINT_URL, checkpoint_path)

def generate_lipsync(face_url: str, audio_url: str, output_path: str, job):
    log(f"Generating lipsync: face={face_url} audio={audio_url}")
    
    safe_progress(job, 20)
    setup_wav2lip()
    
    safe_progress(job, 40)
    face_path = "/tmp/face.mp4"
    audio_path = "/tmp/audio.wav"
    
    download_file(face_url, face_path)
    download_file(audio_url, audio_path)
    
    safe_progress(job, 60)
    log("Running Wav2Lip inference...")
    
    cmd = [
        "python3", "/app/Wav2Lip/inference.py",
        "--checkpoint_path", "/app/Wav2Lip/checkpoints/wav2lip_gan.pth",
        "--face", face_path,
        "--audio", audio_path,
        "--outfile", output_path,
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(f"Wav2Lip failed: {result.stderr[:2000]}")
    
    if not os.path.exists(output_path):
        raise RuntimeError("Lipsync video not created")
    
    size = os.path.getsize(output_path)
    log(f"Lipsync video created: {size} bytes")

def upload_to_r2(file_path: str, job_id: str) -> str:
    bucket = os.getenv("R2_BUCKET")
    public_base = os.getenv("R2_PUBLIC_BASE_URL").rstrip("/")
    key = f"lipsync/{job_id}/final.mp4"
    
    log(f"Uploading to R2: {key}")
    
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

def handler(job):
    job_id = job.get("id", f"job-{int(time.time())}")
    try:
        log(f"Job started: {job_id}")
        payload = job.get("input", {}) or {}
        
        face_url = payload.get("face_url")
        audio_url = payload.get("audio_url")
        
        if not face_url or not audio_url:
            return {
                "ok": False,
                "error_code": "invalid_input",
                "error_message": "Missing required fields: face_url, audio_url",
                "worker_version": WORKER_VERSION,
            }
        
        safe_progress(job, 10)
        validate_env()
        
        output_path = f"/tmp/{job_id}_lipsync.mp4"
        generate_lipsync(str(face_url), str(audio_url), output_path, job)
        
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
                "model": "wav2lip-gan",
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
    log("Wav2Lip worker starting...")
    runpod.serverless.start({"handler": handler})
