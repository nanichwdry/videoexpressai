import { useState, useEffect } from 'react';
import { getJob, Job } from '../api/client';

export function useJob(jobId: string | null) {
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    if (!jobId) {
      setJob(null);
      return;
    }
    
    let isMounted = true;
    
    const pollJob = async () => {
      try {
        const data = await getJob(jobId);
        
        if (isMounted) {
          setJob(data);
          setError(null);
        }
        
        // Stop polling if job is in terminal state
        if (['SUCCEEDED', 'FAILED', 'CANCELED'].includes(data.status)) {
          return true; // Signal to stop polling
        }
        
        return false;
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Unknown error');
        }
        return false;
      }
    };
    
    // Initial fetch
    pollJob();
    
    // Poll every 2 seconds
    const interval = setInterval(async () => {
      const shouldStop = await pollJob();
      if (shouldStop) {
        clearInterval(interval);
      }
    }, 2000);
    
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [jobId]);
  
  return { job, error };
}
