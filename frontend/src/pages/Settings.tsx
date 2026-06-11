import { useState } from 'react';
import { useAppStore } from '../store/appStore';
import { agentService } from '../services/agentService';
import { Monitor } from 'lucide-react';
import type { AppMode } from '../types';

const modes: { value: AppMode; label: string; description: string }[] = [
  { value: 'simulation', label: 'Simulation', description: 'Generate synthetic data and test agents' },
  { value: 'realtime', label: 'Real-Time', description: 'Connect to live data sources' },
  { value: 'hybrid', label: 'Hybrid', description: 'Combine historical and live data' },
];

export default function SettingsPage() {
  const { mode, setMode, dataSource } = useAppStore();
  const [_, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const switchMode = async (newMode: AppMode) => {
    setSaving(true);
    try {
      await agentService.switchMode(newMode);
      setMode(newMode);
      setMessage(`Switched to ${newMode} mode`);
    } catch (e: any) {
      setMessage(`Error: ${e.detail || e.message || 'Failed to switch mode'}`);
    } finally {
      setSaving(false);
      setTimeout(() => setMessage(''), 3000);
    }
  };

  return (
    <div className="page-container animate-fadeIn">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-description">Configure application mode, data sources, and system preferences</p>
      </div>

      {message && (
        <div style={{
          padding: '12px 20px', marginBottom: 20, borderRadius: 'var(--radius-md)',
          background: message.startsWith('Error') ? 'var(--danger-bg)' : 'var(--success-bg)',
          color: message.startsWith('Error') ? 'var(--danger)' : 'var(--success)',
          fontSize: '0.85rem', fontWeight: 500,
        }}>
          {message}
        </div>
      )}

      {/* Mode Selection */}
      <div className="glass-card" style={{ marginBottom: 24 }}>
        <div className="section-header">
          <span className="section-title">🎛️ Application Mode</span>
        </div>
        <div className="grid-3">
          {modes.map((m) => (
            <div
              key={m.value}
              onClick={() => switchMode(m.value)}
              style={{
                padding: '20px',
                borderRadius: 'var(--radius-lg)',
                border: mode === m.value ? '2px solid var(--accent-primary)' : '1px solid var(--border)',
                background: mode === m.value ? 'var(--bg-hover)' : 'var(--bg-tertiary)',
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <Monitor size={20} color={mode === m.value ? 'var(--accent-primary)' : 'var(--text-muted)'} />
                <span style={{ fontWeight: 700, fontSize: '1rem', color: mode === m.value ? 'var(--accent-primary)' : 'var(--text-primary)' }}>
                  {m.label}
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{m.description}</p>
              {mode === m.value && (
                <span className="badge badge-info" style={{ marginTop: 8 }}>Active</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* System Info */}
      <div className="glass-card">
        <div className="section-header">
          <span className="section-title">ℹ️ System Information</span>
        </div>
        <div className="grid-2">
          {[
            { label: 'Current Mode', value: mode.toUpperCase() },
            { label: 'Data Source', value: dataSource },
            { label: 'Version', value: '1.0.0' },
            { label: 'Environment', value: 'Development' },
          ].map((item, i) => (
            <div key={i} style={{ padding: '12px 16px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>{item.label}</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 600, marginTop: 4, fontFamily: 'var(--font-mono)' }}>{item.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
