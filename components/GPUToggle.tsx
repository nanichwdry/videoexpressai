import React, { useState, useEffect } from 'react';

export function GPUToggle() {
  const [gpuOn, setGpuOn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check GPU status on mount
  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const res = await fetch('http://localhost:8000/gpu/status');
      const data = await res.json();
      setGpuOn(data.status === 'on');
    } catch (e) {
      console.error('Failed to check GPU status:', e);
    }
  };

  const toggleGPU = async () => {
    setLoading(true);
    setError(null);

    try {
      const endpoint = gpuOn ? '/gpu/off' : '/gpu/on';
      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
      });

      if (!res.ok) {
        throw new Error('Failed to toggle GPU');
      }

      const data = await res.json();
      setGpuOn(data.status === 'on');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const emergencyOff = async () => {
    if (!confirm('Force GPU shutdown? This will stop all running jobs.')) return;

    setLoading(true);
    try {
      await fetch('http://localhost:8000/gpu/emergency-off', { method: 'POST' });
      setGpuOn(false);
    } catch (e) {
      alert('Emergency shutdown failed. Manually disable in RunPod dashboard.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h3>GPU Control</h3>

      <div style={{ marginBottom: '15px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: gpuOn ? '#4caf50' : '#f44336',
            }}
          />
          <span>
            Status: <strong>{gpuOn ? 'ON' : 'OFF'}</strong>
          </span>
        </div>
        <small style={{ color: '#666' }}>
          {gpuOn
            ? '⚡ GPU ready - billing per-second when jobs run'
            : '💤 GPU disabled - zero idle costs'}
        </small>
      </div>

      <button
        onClick={toggleGPU}
        disabled={loading}
        style={{
          padding: '10px 20px',
          backgroundColor: gpuOn ? '#f44336' : '#4caf50',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer',
          marginRight: '10px',
        }}
      >
        {loading ? 'Updating...' : gpuOn ? 'Turn OFF' : 'Turn ON'}
      </button>

      <button
        onClick={emergencyOff}
        disabled={loading || !gpuOn}
        style={{
          padding: '10px 20px',
          backgroundColor: '#ff9800',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading || !gpuOn ? 'not-allowed' : 'pointer',
        }}
      >
        Emergency OFF
      </button>

      {error && (
        <div style={{ marginTop: '10px', color: '#f44336' }}>
          Error: {error}
        </div>
      )}

      <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#fff3cd', borderRadius: '4px' }}>
        <strong>💡 Cost Safety:</strong>
        <ul style={{ margin: '5px 0', paddingLeft: '20px', fontSize: '14px' }}>
          <li>OFF = 0 active workers = $0 idle cost</li>
          <li>ON = 1 active worker = billed only when jobs run</li>
          <li>Cold start delay when turning ON (~10-30s)</li>
          <li>Always turn OFF when not actively using</li>
        </ul>
      </div>
    </div>
  );
}
