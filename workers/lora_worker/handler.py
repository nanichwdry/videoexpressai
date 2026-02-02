import os
import time
import traceback
import subprocess
import runpod
import boto3
import httpx
from botocore.exceptions import ClientError, NoCredentialsError

WORKER_VERSION = "v1-lora-trainer"

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

def train_lora(image_urls: list, name: str, output_dir: str, job):
    log(f"Training LoRA: name={name} images={len(image_urls)}")
    
    safe_progress(job, 20)
    dataset_dir = "/tmp/dataset"
    os.makedirs(dataset_dir, exist_ok=True)
    
    # Download training images
    for i, url in enumerate(image_urls):
        img_path = f"{dataset_dir}/{i:04d}.jpg"
        download_file(url, img_path)
    
    safe_progress(job, 40)
    log(f"Downloaded {len(image_urls)} images")
    
    # Create training config
    config = f"""
job: extension
config:
  name: {name}
  process:
    - type: sd_trainer
      training_folder: {dataset_dir}
      device: cuda:0
      network:
        type: lora
        linear: 16
        linear_alpha: 16
      save:
        dtype: float16
        save_every: 250
        max_step_saves_to_keep: 1
      datasets:
        - folder_path: {dataset_dir}
          caption_ext: txt
          caption_dropout_rate: 0.05
      train:
        batch_size: 1
        steps: 1000
        gradient_accumulation_steps: 1
        train_unet: true
        train_text_encoder: false
        learning_rate: 0.0001
        optimizer: AdamW8bit
      model:
        name_or_path: stabilityai/stable-diffusion-xl-base-1.0
        is_flux: false
      sample:
        sampler: ddpm
        sample_every: 250
        width: 1024
        height: 1024
        prompts:
          - {name} portrait
        neg: ""
        seed: 42
        walk_seed: true
        guidance_scale: 7
        sample_steps: 20
"""
    
    config_path = "/tmp/train_config.yaml"
    with open(config_path, "w") as f:
        f.write(config)
    
    safe_progress(job, 50)
    log("Starting LoRA training...")
    
    # Run AI-Toolkit training
    cmd = [
        "python3", "-m", "toolkit.job",
        "--config", config_path,
        "--output_dir", output_dir,
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode != 0:
        raise RuntimeError(f"Training failed: {result.stderr[:2000]}")
    
    safe_progress(job, 90)
    
    # Find output LoRA file
    lora_files = [f for f in os.listdir(output_dir) if f.endswith(".safetensors")]
    if not lora_files:
        raise RuntimeError("No LoRA file generated")
    
    lora_path = os.path.join(output_dir, lora_files[0])
    log(f"LoRA trained: {lora_path}")
    return lora_path

def upload_to_r2(file_path: str, job_id: str) -> str:
    bucket = os.getenv("R2_BUCKET")
    public_base = os.getenv("R2_PUBLIC_BASE_URL").rstrip("/")
    key = f"lora/{job_id}/adapter.safetensors"
    
    log(f"Uploading to R2: {key}")
    
    s3 = get_s3_client()
    with open(file_path, "rb") as f:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=f,
            ContentType="application/octet-stream",
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
        
        image_urls = payload.get("images", [])
        name = payload.get("name", "subject")
        
        if not image_urls or len(image_urls) < 5:
            return {
                "ok": False,
                "error_code": "invalid_input",
                "error_message": "Need at least 5 training images",
                "worker_version": WORKER_VERSION,
            }
        
        safe_progress(job, 10)
        validate_env()
        
        output_dir = f"/tmp/{job_id}_output"
        os.makedirs(output_dir, exist_ok=True)
        
        lora_path = train_lora(image_urls, name, output_dir, job)
        
        public_url = upload_to_r2(lora_path, job_id)
        
        safe_progress(job, 100)
        return {
            "ok": True,
            "output_url": public_url,
            "worker_version": WORKER_VERSION,
            "meta": {
                "model": "sdxl-lora",
                "steps": 1000,
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
    log("LoRA training worker starting...")
    runpod.serverless.start({"handler": handler})
