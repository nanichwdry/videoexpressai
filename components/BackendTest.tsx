import React, { useState, useEffect } from 'react';
import { checkHealth, createJob, listJobs } from '../src/api/client';
import { useJob } from '../src/hooks/useJob';

/**
 * Test component to verify backend integration
 * Add this to your app temporarily to test the connection
 */
export const BackendTest: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const { job, error } = useJob(jobId);

  useEffect(() => {
    // Test health endpoint
    checkHealth()
      .then(setHealth)
      .catch(err => console.error('Health check failed:', err));

    // List recent jobs
    listJobs(5)
      .then(setJobs)
      .catch(err => console.error('List jobs failed:', err));
  }, []);

  const handleTestJob = async () => {
    try {
      const { job_id } = await createJob('RENDER', {
        prompt: 'Test video generation',
        duration: 5,
        resolution: '1080p'
      });
      setJobId(job_id);
    } catch (err) {
      console.error('Create job failed:', err);
    }
  };

  return (
    <div className="p-8 bg-zinc-900 text-white">
      <h2 className="text-2xl font-bold mb-6">Backend Integration Test</h2>

      {/* Health Check */}
      <div className="mb-6 p-4 bg-zinc-800 rounded">
        <h3 className="font-bold mb-2">Health Check</h3>
        {health ? (
          <div>
            <p>Status: <span className="text-green-400">{health.status}</span></p>
            <p>RunPod: <span className={health.runpod_connected ? 'text-green-400' : 'text-yellow-400'}>
              {health.runpod_connected ? 'Connected' : 'Not configured'}
            </span></p>
          </div>
        ) : (
          <p className="text-red-400">Backend not responding</p>
        )}
      </div>

      {/* Recent Jobs */}
      <div className="mb-6 p-4 bg-zinc-800 rounded">
        <h3 className="font-bold mb-2">Recent Jobs</h3>
        {jobs.length > 0 ? (
          <ul className="space-y-2">
            {jobs.map(j => (
              <li key={j.job_id} className="text-sm">
                {j.job_id.slice(0, 8)}... - {j.type} - {j.status}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-zinc-500">No jobs yet</p>
        )}
      </div>

      {/* Test Job Creation */}
      <div className="mb-6 p-4 bg-zinc-800 rounded">
        <h3 className="font-bold mb-2">Test Job</h3>
        <button
          onClick={handleTestJob}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded"
        >
          Create Test Job
        </button>

        {job && (
          <div className="mt-4">
            <p>Job ID: {job.job_id.slice(0, 8)}...</p>
            <p>Status: <span className="text-purple-400">{job.status}</span></p>
            <p>Progress: {job.progress}%</p>
            {job.error && <p className="text-red-400">Error: {job.error}</p>}
            {job.output_urls?.[0] && (
              <a href={job.output_urls[0]} target="_blank" className="text-blue-400 underline">
                View Output
              </a>
            )}
          </div>
        )}

        {error && <p className="text-red-400 mt-2">Error: {error}</p>}
      </div>
    </div>
  );
};
