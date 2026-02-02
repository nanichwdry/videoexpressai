"""
Test script for VideoExpress AI Backend
Run this to verify your backend is working correctly
"""

import requests
import time
import json

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    try:
        resp = requests.get(f"{API_BASE}/health")
        print(f"✓ Health check: {resp.json()}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_create_job():
    """Test job creation"""
    print("\nTesting job creation...")
    try:
        resp = requests.post(
            f"{API_BASE}/jobs",
            json={
                "type": "RENDER",
                "params": {
                    "prompt": "A test video of a sunset",
                    "duration": 5,
                    "resolution": "1080p"
                }
            }
        )
        data = resp.json()
        print(f"✓ Job created: {data['job_id']}")
        return data['job_id']
    except Exception as e:
        print(f"✗ Job creation failed: {e}")
        return None

def test_get_job(job_id):
    """Test job status retrieval"""
    print(f"\nTesting job status for {job_id}...")
    try:
        resp = requests.get(f"{API_BASE}/jobs/{job_id}")
        data = resp.json()
        print(f"✓ Job status: {data['status']} ({data['progress']}%)")
        return data
    except Exception as e:
        print(f"✗ Job status failed: {e}")
        return None

def test_list_jobs():
    """Test job listing"""
    print("\nTesting job listing...")
    try:
        resp = requests.get(f"{API_BASE}/jobs?limit=10")
        data = resp.json()
        print(f"✓ Found {len(data)} jobs")
        for job in data[:3]:
            print(f"  - {job['job_id']}: {job['type']} ({job['status']})")
        return True
    except Exception as e:
        print(f"✗ Job listing failed: {e}")
        return False

def test_cancel_job(job_id):
    """Test job cancellation"""
    print(f"\nTesting job cancellation for {job_id}...")
    try:
        resp = requests.post(f"{API_BASE}/jobs/{job_id}/cancel")
        data = resp.json()
        print(f"✓ Job canceled: {data['status']}")
        return True
    except Exception as e:
        print(f"✗ Job cancellation failed: {e}")
        return False

def main():
    print("=" * 60)
    print("VideoExpress AI Backend Test Suite")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n⚠ Backend is not running. Start it with: start-backend.bat")
        return
    
    # Test 2: Create job
    job_id = test_create_job()
    if not job_id:
        print("\n⚠ Job creation failed. Check backend logs.")
        return
    
    # Test 3: Get job status
    time.sleep(1)
    job = test_get_job(job_id)
    
    # Test 4: List jobs
    test_list_jobs()
    
    # Test 5: Cancel job
    if job and job['status'] in ['QUEUED', 'RUNNING']:
        test_cancel_job(job_id)
    
    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)
    print("\nNote: If RunPod is not configured, jobs will fail.")
    print("Configure RunPod in backend/.env to test full workflow.")

if __name__ == "__main__":
    main()
