import { useState, useEffect } from 'react';
import {
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { TrendingUp, TrendingDown, Package, Truck, AlertTriangle, DollarSign, Activity, ShieldCheck } from 'lucide-react';
import { useSimulationStore } from '../store/simulationStore';

import { simulationService } from '../services/simulationService';
import { theme } from '../theme';
import { useAppStore } from '../store/appStore';
import { useAuthStore } from '../store/authStore';

function KPICard({ label, value, change, icon: Icon, color, prefix = '', suffix = '' }: any) {
  return (
    <div className="kpi-card animate-fadeIn" style={{ borderLeft: `3px solid ${color}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span className="kpi-label">{label}</span>
        <div style={{
          width: 36, height: 36, borderRadius: 'var(--radius-md)',
          background: `${color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={18} color={color} />
        </div>
      </div>
      <span className="kpi-value">{prefix}{typeof value === 'number' ? value.toLocaleString() : value}{suffix}</span>
      {change !== undefined && (
        <span className={`kpi-change ${change >= 0 ? 'positive' : 'negative'}`}>
          {change >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          {Math.abs(change).toFixed(1)}%
        </span>
      )}
    </div>
  );
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--bg-secondary)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius-md)', padding: '12px 16px', fontSize: '0.8rem',
    }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: 6 }}>Day {label}</div>
      {payload.map((p: any, i: number) => (
        <div key={i} style={{ color: p.color, display: 'flex', gap: 8, marginTop: 4 }}>
          <span>{p.name}:</span>
          <strong>{typeof p.value === 'number' ? p.value.toLocaleString(undefined, { maximumFractionDigits: 1 }) : p.value}</strong>
        </div>
      ))}
    </div>
  );
};

export default function DashboardPage() {
  const { metrics, result, setResult, setRunning } = useSimulationStore();
  const { showSimulation } = useAppStore();
  const { isAuthenticated } = useAuthStore();
  const [loading, setLoading] = useState(false);

  const stats = result?.statistics;

  useEffect(() => {
    const fetchLatest = async () => {
      try {
        const res: any = await simulationService.getLatest();
        if (res.data) {
          setResult(res.data);
        } else {
          useSimulationStore.getState().reset();
        }
      } catch (e) {
        console.error('Failed to load latest simulation result:', e);
        useSimulationStore.getState().reset();
      }
    };
    fetchLatest();
  }, []);

  const runQuickSim = async () => {
    setLoading(true);
    setRunning(true);
    try {
      const res: any = await simulationService.run({
        simulation_days: 90,
        num_disruptions: 3,
        base_demand: 1000,
        seed: Math.floor(Math.random() * 10000),
      });
      setResult(res.data || res);
    } catch (e) {
      console.error('Simulation failed:', e);
    } finally {
      setLoading(false);
      setRunning(false);
    }
  };

  // Sample every N points for chart performance
  const chartData = metrics.length > 200
    ? metrics.filter((_: any, i: number) => i % Math.ceil(metrics.length / 200) === 0)
    : metrics;

  return (
    <div className="page-container animate-fadeIn">
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">Supply Chain Dashboard</h1>
          <p className="page-description">
            {isAuthenticated ? (
              'Viewing supply chain metrics and AI agent analysis'
            ) : stats ? (
              `Viewing results from ${result?.days}-day simulation with ${result?.disruption_count} disruptions`
            ) : (
              'Run a simulation to see supply chain metrics and AI agent analysis'
            )}
          </p>
        </div>
        {showSimulation && (
          <button className="btn btn-primary btn-lg" onClick={runQuickSim} disabled={loading}>
            <Activity size={18} />
            {loading ? 'Running...' : 'Quick Simulation'}
          </button>
        )}
      </div>

      {/* KPI Cards */}
      {stats ? (
        <>
          <div className="grid-4" style={{ marginBottom: 24 }}>
            <KPICard label="Total Revenue" value={`${(stats.total_revenue / 1000).toFixed(0)}K`} prefix="$"
              icon={DollarSign} color={theme.chart.success} change={5.2} />
            <KPICard label="Avg Demand" value={stats.avg_demand.toFixed(0)}
              icon={Package} color={theme.chart.primary} />
            <KPICard label="On-Time Delivery" value={`${(stats.avg_on_time * 100).toFixed(1)}`} suffix="%"
              icon={Truck} color={stats.avg_on_time > 0.9 ? theme.chart.success : theme.chart.warning} />
            <KPICard label="Supplier Risk" value={`${(stats.avg_supplier_risk * 100).toFixed(1)}`} suffix="%"
              icon={stats.avg_supplier_risk > 0.3 ? AlertTriangle : ShieldCheck}
              color={stats.avg_supplier_risk > 0.3 ? theme.chart.danger : theme.chart.success} />
          </div>

          {/* Charts Row 1 */}
          <div className="grid-2" style={{ marginBottom: 24 }}>
            {/* Demand & Inventory */}
            <div className="chart-container">
              <div className="chart-header">
                <span className="chart-title">Demand & Inventory</span>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.chart.grid} />
                  <XAxis dataKey="day" tick={{ fill: theme.chart.text, fontSize: 11 }} />
                  <YAxis tick={{ fill: theme.chart.text, fontSize: 11 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="inventory" name="Inventory"
                    stroke={theme.chart.primary} fill={`${theme.chart.primary}20`} strokeWidth={2} />
                  <Area type="monotone" dataKey="demand" name="Demand"
                    stroke={theme.chart.secondary} fill={`${theme.chart.secondary}15`} strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Cost & Revenue */}
            <div className="chart-container">
              <div className="chart-header">
                <span className="chart-title">Cost vs Revenue</span>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.chart.grid} />
                  <XAxis dataKey="day" tick={{ fill: theme.chart.text, fontSize: 11 }} />
                  <YAxis tick={{ fill: theme.chart.text, fontSize: 11 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="revenue" name="Revenue" fill={theme.chart.success} radius={[2, 2, 0, 0]} />
                  <Bar dataKey="cost" name="Cost" fill={theme.chart.danger} radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Charts Row 2 */}
          <div className="grid-2" style={{ marginBottom: 24 }}>
            {/* Supplier Risk */}
            <div className="chart-container">
              <div className="chart-header">
                <span className="chart-title">Supplier Risk Over Time</span>
              </div>
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.chart.grid} />
                  <XAxis dataKey="day" tick={{ fill: theme.chart.text, fontSize: 11 }} />
                  <YAxis tick={{ fill: theme.chart.text, fontSize: 11 }} domain={[0, 1]} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="supplier_risk" name="Supplier Risk"
                    stroke={theme.chart.danger} fill={`${theme.chart.danger}20`} strokeWidth={2} />
                  <Area type="monotone" dataKey="on_time_delivery" name="OTD Rate"
                    stroke={theme.chart.success} fill={`${theme.chart.success}15`} strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Disruptions */}
            <div className="chart-container">
              <div className="chart-header">
                <span className="chart-title">Disruption Events</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 250, overflowY: 'auto' }}>
                {result?.disruptions?.length ? result.disruptions.map((d: any, i: number) => (
                  <div key={i} style={{
                    padding: '12px 16px', background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius-md)', borderLeft: `3px solid ${d.severity > 0.5 ? 'var(--danger)' : 'var(--warning)'}`,
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                        {d.type?.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                      </span>
                      <span className={`badge ${d.severity > 0.5 ? 'badge-danger' : 'badge-warning'}`}>
                        Day {d.day}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 4 }}>
                      Severity: {(d.severity * 100).toFixed(0)}%
                      {d.description && ` — ${d.description}`}
                    </div>
                  </div>
                )) : (
                  <div className="empty-state" style={{ padding: 32 }}>
                    <ShieldCheck size={32} />
                    <p style={{ marginTop: 8 }}>No disruptions</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Agent Analysis */}
          {result?.agent_analysis && (
            <div className="glass-card" style={{ marginBottom: 24 }}>
              <div className="section-header">
                <span className="section-title">🤖 AI Agent Analysis</span>
              </div>
              <div className="grid-3">
                <div className="glass-card-sm">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                    Demand Agent
                  </div>
                  <div style={{ fontSize: '1rem', fontWeight: 600 }}>
                    {result.agent_analysis.demand_action?.replace(/_/g, ' ').toUpperCase() || 'N/A'}
                  </div>
                </div>
                <div className="glass-card-sm">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                    Supplier Risk Level
                  </div>
                  <div style={{
                    fontSize: '1rem', fontWeight: 600,
                    color: result.agent_analysis.supplier_risk === 'CRITICAL' ? 'var(--danger)' :
                      result.agent_analysis.supplier_risk === 'HIGH' ? 'var(--warning)' : 'var(--success)',
                  }}>
                    {result.agent_analysis.supplier_risk || 'N/A'}
                  </div>
                </div>
                <div className="glass-card-sm">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>
                    Coordinated Action
                  </div>
                  <div style={{ fontSize: '1rem', fontWeight: 600 }}>
                    {result.agent_analysis.coordinated_action?.replace(/_/g, ' ').toUpperCase() || 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Stats Summary */}
          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">📊 Simulation Summary</span>
            </div>
            <div className="grid-4">
              {[
                { label: 'Total Cost', value: `$${(stats.total_cost / 1000).toFixed(0)}K` },
                { label: 'Profit', value: `$${(stats.profit / 1000).toFixed(0)}K` },
                { label: 'Stockout Days', value: stats.stockout_days },
                { label: 'Stockout Rate', value: `${stats.stockout_rate}%` },
                { label: 'Min Inventory', value: stats.min_inventory.toFixed(0) },
                { label: 'Max Demand', value: stats.max_demand.toFixed(0) },
                { label: 'Max Supplier Risk', value: `${(stats.max_supplier_risk * 100).toFixed(0)}%` },
                { label: 'Min OTD', value: `${(stats.min_on_time * 100).toFixed(0)}%` },
              ].map((item, i) => (
                <div key={i} style={{
                  padding: '12px 16px', background: 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
                    {item.label}
                  </div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {item.value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        /* Empty state */
        <div className="glass-card" style={{ textAlign: 'center', padding: '80px 32px' }}>
          <Activity size={64} style={{ color: 'var(--accent-primary)', opacity: 0.5, marginBottom: 20 }} />
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 12 }}>No Simulation Data</h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: 400, margin: '0 auto 24px' }}>
            Run a simulation to generate supply chain metrics, agent analysis, and disruption scenarios.
          </p>
          <button className="btn btn-primary btn-lg" onClick={runQuickSim} disabled={loading}>
            <Activity size={18} />
            {loading ? 'Running Simulation...' : 'Run Your First Simulation'}
          </button>
        </div>
      )}
    </div>
  );
}
