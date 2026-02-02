const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export interface Job {
  job_id: string;
  type: string;
  status: 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'CANCELED';
  progress: number;
  output_urls: string[];
  error?: string;
  created_at: string;
  updated_at: string;
}

export async function createJob(type: string, params: any): Promise<{ job_id: string; status: string; created_at: string }> {
  const res = await fetch(`${API_BASE}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type, params })
  });
  
  if (!res.ok) {
    throw new Error(`Failed to create job: ${res.statusText}`);
  }
  
  return res.json();
}

export async function getJob(jobId: string): Promise<Job> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`);
  
  if (!res.ok) {
    throw new Error(`Failed to get job: ${res.statusText}`);
  }
  
  return res.json();
}

export async function listJobs(limit: number = 50): Promise<Job[]> {
  const res = await fetch(`${API_BASE}/jobs?limit=${limit}`);
  
  if (!res.ok) {
    throw new Error(`Failed to list jobs: ${res.statusText}`);
  }
  
  return res.json();
}

export async function cancelJob(jobId: string): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/cancel`, { 
    method: 'POST' 
  });
  
  if (!res.ok) {
    throw new Error(`Failed to cancel job: ${res.statusText}`);
  }
  
  return res.json();
}

export async function stitchTimeline(clips: any[], captions: any[] = []): Promise<{ job_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/timeline/stitch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ clips, captions })
  });
  
  if (!res.ok) {
    throw new Error(`Failed to stitch timeline: ${res.statusText}`);
  }
  
  return res.json();
}

export async function checkHealth(): Promise<{ status: string; runpod_connected: boolean }> {
  const res = await fetch(`${API_BASE}/health`);
  
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  
  return res.json();
}
