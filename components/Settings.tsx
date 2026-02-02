import React, { useState, useEffect } from 'react';

export function Settings() {
  const [secrets, setSecrets] = useState<Record<string, string>>({});
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [health, setHealth] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSecrets();
    checkHealth();
  }, []);

  const loadSecrets = async () => {
    if (!window.electron) return;
    const keys = await window.electron.secrets.list();
    const loaded: Record<string, string> = {};
    for (const key of keys) {
      const value = await window.electron.secrets.get(key);
      if (value) loaded[key] = '***';
    }
    setSecrets(loaded);
  };

  const checkHealth = async () => {
    if (!window.electron) return;
    const status = await window.electron.health.check();
    setHealth(status);
  };

  const saveSecret = async () => {
    if (!newKey || !newValue || !window.electron) return;
    await window.electron.secrets.set(newKey, newValue);
    setNewKey('');
    setNewValue('');
    loadSecrets();
  };

  const deleteSecret = async (key: string) => {
    if (!window.electron) return;
    await window.electron.secrets.delete(key);
    loadSecrets();
  };

  const connectOAuth = async (provider: 'youtube' | 'instagram') => {
    if (!window.electron) return;
    setLoading(true);
    try {
      const result = await window.electron.oauth.open(provider);
      if (result.success) {
        alert(`${provider} connected successfully!`);
        checkHealth();
      }
    } catch (e) {
      alert(`Failed to connect ${provider}: ${e}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px' }}>
      <h2>Settings</h2>

      <div style={{ marginBottom: '30px' }}>
        <h3>System Health</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
          {Object.entries(health).map(([service, ok]) => (
            <div
              key={service}
              style={{
                padding: '10px',
                background: ok ? '#d4edda' : '#f8d7da',
                border: `1px solid ${ok ? '#c3e6cb' : '#f5c6cb'}`,
                borderRadius: '4px',
              }}
            >
              <strong>{service}</strong>: {ok ? '✓ Connected' : '✗ Disconnected'}
            </div>
          ))}
        </div>
        <button onClick={checkHealth} style={{ marginTop: '10px' }}>
          Refresh Health
        </button>
      </div>

      <div style={{ marginBottom: '30px' }}>
        <h3>API Keys (Encrypted)</h3>
        <div style={{ marginBottom: '10px' }}>
          <input
            placeholder="Key (e.g., OPENAI_API_KEY)"
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
            style={{ marginRight: '10px', padding: '8px', width: '200px' }}
          />
          <input
            type="password"
            placeholder="Value"
            value={newValue}
            onChange={(e) => setNewValue(e.target.value)}
            style={{ marginRight: '10px', padding: '8px', width: '300px' }}
          />
          <button onClick={saveSecret}>Save</button>
        </div>
        <div>
          {Object.entries(secrets).map(([key, value]) => (
            <div
              key={key}
              style={{
                padding: '8px',
                background: '#f8f9fa',
                marginBottom: '5px',
                display: 'flex',
                justifyContent: 'space-between',
              }}
            >
              <span>
                <strong>{key}</strong>: {value}
              </span>
              <button onClick={() => deleteSecret(key)} style={{ color: 'red' }}>
                Delete
              </button>
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: '30px' }}>
        <h3>Social Media Connections</h3>
        <button
          onClick={() => connectOAuth('youtube')}
          disabled={loading}
          style={{ marginRight: '10px', padding: '10px 20px' }}
        >
          {loading ? 'Connecting...' : 'Connect YouTube'}
        </button>
        <button
          onClick={() => connectOAuth('instagram')}
          disabled={loading}
          style={{ padding: '10px 20px' }}
        >
          {loading ? 'Connecting...' : 'Connect Instagram'}
        </button>
      </div>

      <div style={{ marginTop: '30px', padding: '15px', background: '#fff3cd', border: '1px solid #ffc107' }}>
        <strong>Note:</strong> API keys are encrypted using OS-level secure storage. OAuth tokens are stored
        encrypted in Supabase.
      </div>
    </div>
  );
}
