const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export interface Job {
  job_id: string;
  type: string;
  status: 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'CANCELED';
  progress: number;
  output_urls: string[];
  error?: {
    code: string;
    message: string;
  };
  status_hint?: 'warming_gpu' | null;
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

export async function deleteJob(jobId: string): Promise<{ deleted: boolean; artifacts_cleaned: number }> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`, { 
    method: 'DELETE' 
  });
  
  if (!res.ok) {
    throw new Error(`Failed to delete job: ${res.statusText}`);
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

// Gemini AI Integration (Optional - for prompt enhancement)

export async function enhancePrompt(prompt: string, style?: string): Promise<{
  enhanced_prompt: string;
  original_prompt: string;
  used_gemini: boolean;
  error?: string;
}> {
  const res = await fetch(`${API_BASE}/ai/enhance-prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, style })
  });
  
  if (!res.ok) {
    throw new Error(`Failed to enhance prompt: ${res.statusText}`);
  }
  
  return res.json();
}

export async function generateScript(topic: string, duration: number = 60): Promise<{
  title: string;
  scenes: Array<{
    scene_number: number;
    duration: number;
    visual_prompt: string;
    narration: string;
  }>;
  used_gemini: boolean;
  error?: string;
}> {
  const res = await fetch(`${API_BASE}/ai/generate-script`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, duration })
  });
  
  if (!res.ok) {
    throw new Error(`Failed to generate script: ${res.statusText}`);
  }
  
  return res.json();
}

export async function stylePrompt(prompt: string, style: string): Promise<{
  improved_prompt: string;
  used_gemini: boolean;
  error?: string;
}> {
  const res = await fetch(`${API_BASE}/ai/style-prompt?prompt=${encodeURIComponent(prompt)}&style=${encodeURIComponent(style)}`, {
    method: 'POST'
  });
  
  if (!res.ok) {
    throw new Error(`Failed to style prompt: ${res.statusText}`);
  }
  
  return res.json();
}
