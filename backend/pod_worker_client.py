"""
Pod-based Video Worker Client
Replaces RunPod serverless calls with HTTP API calls to Pod worker
"""

import os
import httpx
from typing import Optional

VIDEO_WORKER_BASE_URL = os.getenv("VIDEO_WORKER_BASE_URL", "http://localhost:8001")

async def submit_video_job(prompt: str, duration: int = 5) -> dict:
    """Submit video generation job to Pod worker"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{VIDEO_WORKER_BASE_URL}/generate",
            json={"prompt": prompt, "duration": duration}
        )
        response.raise_for_status()
        return response.json()

async def get_job_status(job_id: str) -> dict:
    """Get job status from Pod worker"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{VIDEO_WORKER_BASE_URL}/status/{job_id}")
        response.raise_for_status()
        return response.json()

async def check_worker_health() -> dict:
    """Check if Pod worker is healthy"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{VIDEO_WORKER_BASE_URL}/health")
        response.raise_for_status()
        return response.json()
