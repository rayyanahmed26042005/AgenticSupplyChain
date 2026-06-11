import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
  AreaChart, Area,
} from 'recharts';
import { BarChart3 } from 'lucide-react';
import { theme } from '../theme';

const COLORS = ['#6366f1', '#8b5cf6', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6'];

import { useSimulationStore } from '../store/simulationStore';

export default function AnalyticsPage() {
  const { result, metrics } = useSimulationStore();
  const stats = result?.statistics;
  
  const chartData = metrics.length > 200 ? metrics.filter((_: any, i: number) => i % Math.ceil(metrics.length / 200) === 0) : metrics;

  const disruptions = result?.disruptions || [];
  const disruptionTypeCounts: Record<string, number> = {};
  disruptions.forEach((d: any) => {
    const t = d.type || 'unknown';
    disruptionTypeCounts[t] = (disruptionTypeCounts[t] || 0) + 1;
  });
  const pieData = Object.entries(disruptionTypeCounts).map(([name, value]) => ({
    name: name.replace(/_/g, ' '),
    value,
  }));

  // Aggregate by weeks
  const weeklyData: any[] = [];
  for (let i = 0; i < metrics.length; i += 7) {
    const week = metrics.slice(i, i + 7);
    if (week.length === 0) break;
    weeklyData.push({
      week: `W${Math.floor(i / 7) + 1}`,
      avg_demand: Math.round(week.reduce((s: number, m: any) => s + m.demand, 0) / week.length),
      avg_cost: Math.round(week.reduce((s: number, m: any) => s + m.cost, 0) / week.length),
      avg_revenue: Math.round(week.reduce((s: number, m: any) => s + m.revenue, 0) / week.length),
      stockouts: week.filter((m: any) => m.stockout).length,
    });
  }

  return (
    <div className="page-container animate-fadeIn">
      <div className="page-header">
        <h1 className="page-title">Analytics</h1>
        <p className="page-description">Deep dive into supply chain performance metrics and trends</p>
      </div>

      {stats ? (
        <>
          {/* Weekly Trends */}
          <div className="grid-2" style={{ marginBottom: 24 }}>
            <div className="chart-container">
              <div className="chart-header">
                <span className="chart-title">Weekly Demand & Revenue</span>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={weeklyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.chart.grid} />
                  <XAxis dataKey="week" tick={{ fill: theme.chart.text, fontSize: 11 }} />
                  <YAxis tick={{ fill: theme.chart.text, fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="avg_demand" name="Avg Demand" fill={theme.chart.primary} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="avg_revenue" name="Avg Revenue" fill={theme.chart.success} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-container">
              <div className="chart-header">
                <span className="chart-title">Disruption Distribution</span>
              </div>
              {pieData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" outerRadius={100} dataKey="value" label>
                      {pieData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                  No disruptions to visualize
                </div>
              )}
            </div>
          </div>

          {/* Demand Decoder */}
          <div className="glass-card" style={{ marginBottom: 24 }}>
            <div className="section-header">
              <span className="section-title">📊 Demand Decoder (Time-Series Decomposition)</span>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 16 }}>
              Visualizes how daily customer orders decompose into a baseline demand, linear growth trend, seasonality fluctuations, and random noise/spikes.
            </p>
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={theme.chart.grid} />
                <XAxis dataKey="day" tick={{ fill: theme.chart.text, fontSize: 11 }} />
                <YAxis tick={{ fill: theme.chart.text, fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="demand_baseline" name="Baseline" stroke="#6366f1" fill="#6366f115" stackId="1" />
                <Area type="monotone" dataKey="demand_trend" name="Trend growth" stroke="#8b5cf6" fill="#8b5cf615" stackId="1" />
                <Area type="monotone" dataKey="demand_seasonality" name="Seasonality" stroke="#f59e0b" fill="#f59e0b15" stackId="1" />
                <Area type="monotone" dataKey="demand_noise" name="Noise" stroke="#10b981" fill="#10b98115" stackId="1" />
                <Area type="monotone" dataKey="demand_spike" name="Spikes/Promo" stroke="#ef4444" fill="#ef444415" stackId="1" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* P&L Summary */}
          <div className="glass-card">
            <div className="section-header">
              <span className="section-title">💰 Financial Summary</span>
            </div>
            <div className="grid-3">
              <div style={{ padding: 20, background: 'var(--success-bg)', borderRadius: 'var(--radius-lg)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--success)', textTransform: 'uppercase', fontWeight: 600 }}>Total Revenue</div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--success)', marginTop: 8 }}>
                  ${(stats.total_revenue / 1000).toFixed(0)}K
                </div>
              </div>
              <div style={{ padding: 20, background: 'var(--danger-bg)', borderRadius: 'var(--radius-lg)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--danger)', textTransform: 'uppercase', fontWeight: 600 }}>Total Cost</div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--danger)', marginTop: 8 }}>
                  ${(stats.total_cost / 1000).toFixed(0)}K
                </div>
              </div>
              <div style={{ padding: 20, background: stats.profit > 0 ? 'var(--success-bg)' : 'var(--danger-bg)', borderRadius: 'var(--radius-lg)', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: stats.profit > 0 ? 'var(--success)' : 'var(--danger)', textTransform: 'uppercase', fontWeight: 600 }}>Net Profit</div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: stats.profit > 0 ? 'var(--success)' : 'var(--danger)', marginTop: 8 }}>
                  ${(stats.profit / 1000).toFixed(0)}K
                </div>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="glass-card" style={{ textAlign: 'center', padding: 64 }}>
          <BarChart3 size={64} style={{ color: 'var(--text-muted)', opacity: 0.3, marginBottom: 16 }} />
          <h2 style={{ color: 'var(--text-primary)', marginBottom: 8 }}>No Analytics Data</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Run a simulation from the Dashboard or Simulation page first</p>
        </div>
      )}
    </div>
  );
}
