import { useState, useEffect } from 'react';
import { useSimulationStore } from '../store/simulationStore';
import { simulationService } from '../services/simulationService';
import {
  LineChart, Line, AreaChart, Area,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { Play } from 'lucide-react';
import { theme } from '../theme';

export default function SimulationPage() {
  const { result, setResult, setRunning, scenarios, setScenarios } = useSimulationStore();
  const [loading, setLoading] = useState(false);
  const [params, setParams] = useState({
    simulation_days: 90,
    num_disruptions: 3,
    base_demand: 1000,
    seed: 42,
  });

  useEffect(() => {
    simulationService.listScenarios().then((res: any) => {
      setScenarios(res.data || []);
    }).catch(() => {});
  }, []);

  const runSim = async () => {
    setLoading(true);
    setRunning(true);
    try {
      const res: any = await simulationService.run(params);
      setResult(res.data || res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRunning(false);
    }
  };

  const runScenario = async (id: string) => {
    setLoading(true);
    setRunning(true);
    try {
      const res: any = await simulationService.runScenario(id);
      setResult(res.data || res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
      setRunning(false);
    }
  };

  const metrics = result?.metrics || [];
  const chartData = metrics.length > 200 ? metrics.filter((_: any, i: number) => i % Math.ceil(metrics.length / 200) === 0) : metrics;

  return (
    <div className="page-container animate-fadeIn">
      <div className="page-header">
        <h1 className="page-title">Simulation Engine</h1>
        <p className="page-description">
          Configure and run supply chain simulations with disruption injection and agent analysis
        </p>
      </div>

      {/* Controls */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Config */}
        <div className="glass-card">
          <div className="section-header">
            <span className="section-title">⚙️ Configuration</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {[
              { label: 'Duration (days)', key: 'simulation_days', min: 7, max: 365 },
              { label: 'Disruptions', key: 'num_disruptions', min: 0, max: 20 },
              { label: 'Base Demand', key: 'base_demand', min: 100, max: 10000 },
              { label: 'Random Seed', key: 'seed', min: 1, max: 99999 },
            ].map((field) => (
              <div key={field.key}>
                <label className="label">{field.label}</label>
                <input
                  type="number"
                  className="input"
                  value={(params as any)[field.key]}
                  min={field.min}
                  max={field.max}
                  onChange={(e) => setParams({ ...params, [field.key]: Number(e.target.value) })}
                />
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 12, marginTop: 20 }}>
            <button className="btn btn-primary btn-lg" onClick={runSim} disabled={loading} style={{ flex: 1 }}>
              <Play size={18} />
              {loading ? 'Running...' : 'Run Simulation'}
            </button>
          </div>
        </div>

        {/* Scenarios */}
        <div className="glass-card">
          <div className="section-header">
            <span className="section-title">📋 Predefined Scenarios</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {scenarios.map((s: any) => (
              <div
                key={s.id}
                style={{
                  padding: '14px 16px',
                  background: 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  border: '1px solid var(--border)',
                  transition: 'all var(--transition-fast)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
                onClick={() => runScenario(s.id)}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{s.name}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 2 }}>
                    {s.simulation_days}d · {s.num_disruptions} disruptions · demand {s.base_demand}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 4 }}>
                  {s.tags?.slice(0, 2).map((t: any) => (
                    <span key={t} className="badge badge-info">{t}</span>
                  ))}
                </div>
              </div>
            ))}
            {scenarios.length === 0 && (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 20, fontSize: '0.85rem' }}>
                Start the backend to load scenarios
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Results */}
      {result && (
        <>
          <div className="grid-2" style={{ marginBottom: 24 }}>
            <div className="chart-container">
              <div className="chart-header">
                <span className="chart-title">Demand & Inventory Dynamics</span>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.chart.grid} />
                  <XAxis dataKey="day" tick={{ fill: theme.chart.text, fontSize: 11 }} />
                  <YAxis tick={{ fill: theme.chart.text, fontSize: 11 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="demand" name="Demand" stroke={theme.chart.primary} fill={`${theme.chart.primary}20`} strokeWidth={2} />
                  <Area type="monotone" dataKey="inventory" name="Inventory" stroke={theme.chart.success} fill={`${theme.chart.success}15`} strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-container">
              <div className="chart-header">
                <span className="chart-title">Risk & On-Time Delivery</span>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.chart.grid} />
                  <XAxis dataKey="day" tick={{ fill: theme.chart.text, fontSize: 11 }} />
                  <YAxis tick={{ fill: theme.chart.text, fontSize: 11 }} domain={[0, 1]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="supplier_risk" name="Supplier Risk" stroke={theme.chart.danger} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="on_time_delivery" name="OTD" stroke={theme.chart.success} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
