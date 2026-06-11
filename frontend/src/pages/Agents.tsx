import { useState, useEffect } from 'react';
import { agentService } from '../services/agentService';
import { Cpu, Brain, Shield, Workflow, RefreshCw, Play, Lightbulb, Package } from 'lucide-react';

const agentIcons: Record<string, any> = {
  demand: Brain,
  inventory: Package,
  supplier: Shield,
  coordinator: Workflow,
};

const agentColors: Record<string, string> = {
  demand: '#6366f1',
  inventory: '#3b82f6',
  supplier: '#22c55e',
  coordinator: '#f59e0b',
};

const agentOrder = ['demand', 'inventory', 'supplier', 'coordinator'];

const renderAgentDetails = (name: string, agent: any) => {
  const metrics = agent.performance || {};

  if (name === 'demand') {
    const forecastDemand = metrics.forecast_demand || 'No data';
    const trend = metrics.trend || '';
    const confidence = metrics.forecast_confidence || '';
    const range = metrics.forecast_range || '';
    const method = metrics.forecast_method || '';

    return (
      <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Forecast Demand</div>
          <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)', marginTop: 2 }}>{forecastDemand}</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Trend</div>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: 2 }}>{trend}</div>
          </div>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Confidence</div>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: 2 }}>{confidence}</div>
          </div>
        </div>
        <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Forecast Range</div>
          <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: 2 }}>{range}</div>
        </div>
        <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Forecast Method</div>
          <div style={{ fontWeight: 600, fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 2 }}>{method}</div>
        </div>
      </div>
    );
  }

  if (name === 'inventory') {
    const daysOfSupply = metrics.days_of_supply || 'No data';
    const coverageStatus = metrics.coverage_status || '';
    const currentInventory = metrics.current_inventory || '';
    const safetyStock = metrics.safety_stock || '';
    const reorderPoint = metrics.reorder_point || '';
    const recommendedOrderQty = metrics.recommended_order_quantity || '';

    const getCoverageBadgeClass = (status: string) => {
      if (status === 'CRITICAL') return 'badge-danger';
      if (status === 'LOW') return 'badge-warning';
      if (status === 'EXCESS') return 'badge-info';
      return 'badge-success';
    };

    return (
      <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: 8 }}>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Days of Supply</div>
            <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)', marginTop: 2 }}>{daysOfSupply}</div>
          </div>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 2 }}>Coverage</div>
            <div>
              <span className={`badge ${getCoverageBadgeClass(coverageStatus)}`} style={{ fontSize: '0.7rem' }}>{coverageStatus}</span>
            </div>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Current Inventory</div>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: 2 }}>{currentInventory}</div>
          </div>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Safety Stock</div>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: 2 }}>{safetyStock}</div>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 8 }}>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Reorder Point</div>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: 2 }}>{reorderPoint}</div>
          </div>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Recommended Qty</div>
            <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--accent-primary)', marginTop: 2 }}>{recommendedOrderQty}</div>
          </div>
        </div>
      </div>
    );
  }

  if (name === 'supplier') {
    const riskScore = metrics.supplier_risk_score || '';
    const riskLevel = metrics.risk_level || '';
    const primaryRiskFactor = metrics.primary_risk_factor || '';
    const onTimeDelivery = metrics.on_time_delivery || '';
    const disruptionProbability = metrics.disruption_probability || '';

    const getRiskBadgeClass = (level: string) => {
      if (level === 'CRITICAL') return 'badge-danger';
      if (level === 'HIGH') return 'badge-warning';
      if (level === 'MEDIUM') return 'badge-info';
      return 'badge-success';
    };

    return (
      <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: 8 }}>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Risk Score</div>
            <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)', marginTop: 2 }}>{riskScore}</div>
          </div>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 2 }}>Risk Level</div>
            <div>
              <span className={`badge ${getRiskBadgeClass(riskLevel)}`} style={{ fontSize: '0.7rem' }}>{riskLevel}</span>
            </div>
          </div>
        </div>
        <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Primary Risk Factor</div>
          <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: 2 }}>{primaryRiskFactor}</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>On-Time Delivery</div>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: 2 }}>{onTimeDelivery}</div>
          </div>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Disruption Prob.</div>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: 2 }}>{disruptionProbability}</div>
          </div>
        </div>
      </div>
    );
  }

  if (name === 'coordinator') {
    const finalAction = metrics.final_action || ' ';
    const orderQuantity = metrics.order_quantity || '';
    const primaryAlloc = metrics.primary_supplier_allocation || '';
    const backupAlloc = metrics.backup_supplier_allocation || '';
    const conflictRes = metrics.conflict_resolution || '';

    return (
      <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Final Action</div>
          <div style={{ fontWeight: 800, fontSize: '1.15rem', color: 'var(--accent-primary)', marginTop: 2 }}>{finalAction}</div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: 8 }}>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Order Quantity</div>
            <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-primary)', marginTop: 2 }}>{orderQuantity}</div>
          </div>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Conflict Resolution</div>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--success)', marginTop: 2 }}>{conflictRes}</div>
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Primary Allocation</div>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: 2 }}>{primaryAlloc}</div>
          </div>
          <div style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Backup Allocation</div>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--text-primary)', marginTop: 2 }}>{backupAlloc}</div>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Record<string, any>>({});
  const [decisions, setDecisions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const [selectedDecision, setSelectedDecision] = useState<any | null>(null);
  const [explanation, setExplanation] = useState<any | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);

  const fetchExplanation = async (d: any) => {
    setSelectedDecision(d);
    setLoadingExplanation(true);
    try {
      const res: any = await agentService.explainDecision(d);
      setExplanation(res.data || res);
    } catch (err) {
      console.error("Failed to explain decision:", err);
      setExplanation(null);
    } finally {
      setLoadingExplanation(false);
    }
  };

  const fetchData = async () => {
    try {
      const [statusRes, decisionsRes]: any[] = await Promise.all([
        agentService.getAllStatus(),
        agentService.getDecisions(20),
      ]);
      setAgents(statusRes.data || {});
      setDecisions(decisionsRes.data || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const runAgents = async () => {
    setLoading(true);
    try {
      await agentService.runAgents();
      await fetchData();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const resetAgents = async () => {
    try {
      await agentService.resetAgents();
      await fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  // Sort agents in the defined order
  const sortedAgents = agentOrder
    .filter((name) => agents[name])
    .map((name) => [name, agents[name]] as [string, any]);

  return (
    <div className="page-container animate-fadeIn">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="page-title">AI Agents</h1>
          <p className="page-description">
            Monitor autonomous supply chain agents, view decisions, and analyze performance
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={resetAgents}>
            <RefreshCw size={16} /> Reset
          </button>
          <button className="btn btn-primary" onClick={runAgents} disabled={loading}>
            <Play size={16} /> {loading ? 'Running...' : 'Run Cycle'}
          </button>
        </div>
      </div>

      {/* Agent Cards */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        {sortedAgents.map(([name, agent]: [string, any]) => {
          const Icon = agentIcons[name] || Cpu;
          const color = agentColors[name] || '#6366f1';
          const isCoordinator = name === 'coordinator';

          return (
            <div
              key={name}
              className="glass-card"
              style={{
                borderTop: isCoordinator ? `4px solid ${color}` : `3px solid ${color}`,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'all 0.3s ease',
                ...(isCoordinator && {
                  boxShadow: '0 8px 30px rgba(245, 158, 11, 0.2)',
                  border: '1px solid rgba(245, 158, 11, 0.4)',
                  background: 'linear-gradient(180deg, var(--bg-secondary) 0%, rgba(245, 158, 11, 0.04) 100%)',
                })
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                      width: 44, height: 44, borderRadius: 'var(--radius-md)',
                      background: `${color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <Icon size={22} color={color} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '1rem' }}>{agent.name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{agent.role?.replace(/_/g, ' ')}</div>
                    </div>
                  </div>
                  {isCoordinator && (
                    <span style={{
                      fontSize: '0.65rem',
                      background: 'rgba(245, 158, 11, 0.15)',
                      color: 'var(--accent-primary)',
                      padding: '4px 8px',
                      borderRadius: 12,
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em'
                    }}>
                      Decision Hub
                    </span>
                  )}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
                  <div style={{ padding: '10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Status</div>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem', marginTop: 2 }}>
                      <span className={`badge ${agent.status === 'idle' ? 'badge-success' : agent.status === 'error' ? 'badge-danger' : 'badge-info'}`}>
                        {agent.status}
                      </span>
                    </div>
                  </div>
                  <div style={{ padding: '10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Decisions</div>
                    <div style={{ fontWeight: 700, fontSize: '1.1rem', marginTop: 2 }}>{agent.decisions_made}</div>
                  </div>
                </div>

                {/* Custom Agent Details */}
                {renderAgentDetails(name, agent)}
              </div>
            </div>
          );
        })}

        {Object.keys(agents).length === 0 && (
          <div className="glass-card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: 48 }}>
            <Cpu size={48} style={{ color: 'var(--text-muted)', opacity: 0.4, marginBottom: 16 }} />
            <p style={{ color: 'var(--text-secondary)' }}>Start the backend and run a simulation to see agent states</p>
          </div>
        )}
      </div>

      {/* Decision History */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedDecision ? '1.2fr 1fr' : '1fr', gap: 24, transition: 'all 0.3s ease' }}>
        <div className="glass-card">
          <div className="section-header">
            <span className="section-title">📝 Recent Decisions</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{decisions.length} decisions</span>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: 16 }}>
            Click on any decision item below to trigger the Decision Explainer panel and view feature weights.
          </p>
          {decisions.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {decisions.slice(-10).reverse().map((d, i) => (
                <div
                  key={i}
                  onClick={() => fetchExplanation(d)}
                  style={{
                    padding: '14px 16px',
                    background: selectedDecision === d ? 'var(--bg-hover)' : 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius-md)',
                    borderLeft: selectedDecision === d ? '3px solid var(--accent-primary)' : '3px solid transparent',
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                      {d.summary?.coordinated_action?.replace(/_/g, ' ') || 'Agent Decision'}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {new Date(d.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                    <span>Demand: <strong>{d.summary?.demand_action || '—'}</strong></span>
                    <span>Inventory: <strong>{d.summary?.inventory_action?.replace(/_/g, ' ') || '—'}</strong></span>
                    <span>Risk: <strong>{d.summary?.supplier_risk || '—'}</strong></span>
                    {d.summary?.conflict_resolved && (
                      <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>Conflict Resolved</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)' }}>
              <Lightbulb size={32} style={{ opacity: 0.4, marginBottom: 8 }} />
              <p>Run agent cycles or a simulation to generate decisions</p>
            </div>
          )}
        </div>

        {/* Explainability Side Panel */}
        {selectedDecision && (
          <div className="glass-card animate-fadeIn" style={{ position: 'relative' }}>
            <button
              onClick={() => setSelectedDecision(null)}
              style={{
                position: 'absolute', top: 16, right: 16,
                background: 'transparent', border: 'none', color: 'var(--text-secondary)',
                cursor: 'pointer', fontSize: '1.25rem', fontWeight: 'bold'
              }}
            >
              ×
            </button>
            <div className="section-header">
              <span className="section-title">🔍 Decision Explainer</span>
            </div>

            {loadingExplanation ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: 48, gap: 16 }}>
                <div className="loading-spinner" />
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Analyzing decision paths...</span>
              </div>
            ) : explanation ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 24, paddingBottom: 16 }}>
                {/* 1. Executive Recommendation */}
                <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: 16 }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 6, letterSpacing: '0.05em', fontWeight: 600 }}>Executive Recommendation</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 12 }}>
                    <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.02em' }}>
                      {explanation.action?.replace(/_/g, ' ')}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                      Confidence: <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{((explanation.confidence || 0.87) * 100).toFixed(0)}%</strong>
                    </div>
                  </div>

                  {/* Confidence Bar */}
                  <div style={{ height: 6, background: 'var(--bg-tertiary)', borderRadius: 3, overflow: 'hidden', marginBottom: 16 }}>
                    <div style={{ width: `${(explanation.confidence || 0.87) * 100}%`, height: '100%', background: 'var(--accent-gradient)' }} />
                  </div>

                  {/* Business Impact Box */}
                  <div style={{ padding: '12px 14px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', borderLeft: '3px solid var(--accent-primary)', marginBottom: 16 }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', marginBottom: 4 }}>Business Impact</div>
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.4, margin: 0, whiteSpace: 'pre-line' }}>
                      {explanation.business_impact}
                    </p>
                  </div>

                  {/* KPI Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                    {[
                      { label: 'Expected Service Level', value: explanation.expected_service_level || '98.4%', color: 'var(--success)' },
                      { label: 'Stockout Probability', value: explanation.stockout_probability || '3.2%', color: 'var(--danger)' },
                      { label: 'Disruption Probability', value: explanation.disruption_probability || '4.8%', color: 'var(--warning)' },
                    ].map((kpi, idx) => (
                      <div key={idx} style={{ padding: '8px 10px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', textAlign: 'center' }}>
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', lineHeight: 1.2, height: 26, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{kpi.label}</div>
                        <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 4, color: kpi.color, fontFamily: 'var(--font-mono)' }}>{kpi.value}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 2. Agent Reasoning Trace */}
                <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: 16 }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 12, letterSpacing: '0.05em', fontWeight: 600 }}>Agent Reasoning Trace</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {[
                      { agent: 'Demand Analysis Agent', text: explanation.agent_traces?.demand, color: '#6366f1' },
                      { agent: 'Inventory Optimization Agent', text: explanation.agent_traces?.inventory, color: '#3b82f6' },
                      { agent: 'Supplier Risk Agent', text: explanation.agent_traces?.supplier, color: '#22c55e' },
                      { agent: 'Coordinator Agent', text: explanation.agent_traces?.coordinator, color: '#f59e0b' },
                    ].map((trace, idx) => (
                      <div key={idx} style={{ padding: '10px 12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', borderLeft: `3px solid ${trace.color}` }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>{trace.agent}</div>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.35 }}>{trace.text}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 3. SHAP Analysis: Top Factors */}
                <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: 16 }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 12, letterSpacing: '0.05em', fontWeight: 600 }}>Top Factors Influencing Decision</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {explanation.feature_importance?.map((feat: any, idx: number) => (
                      <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                          <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{feat.name}</span>
                          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{feat.value}</span>
                            <span style={{ color: 'var(--accent-primary)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                              {feat.contribution}
                            </span>
                          </div>
                        </div>
                        <div style={{ height: 4, background: 'var(--bg-tertiary)', borderRadius: 2, overflow: 'hidden' }}>
                          <div style={{ width: `${feat.importance * 100}%`, height: '100%', background: 'var(--accent-primary)' }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 4. Alternatives Considered */}
                <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: 16 }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 12, letterSpacing: '0.05em', fontWeight: 600 }}>Alternatives Considered</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {explanation.alternatives_considered?.map((alt: any, idx: number) => (
                      <div key={idx} style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)', display: 'flex', justifyContent: 'space-between' }}>
                          <span>{idx + 1}. {alt.name}</span>
                          <span className={`badge ${alt.status === 'Active' ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.65rem', padding: '1px 5px' }}>{alt.status}</span>
                        </div>
                        <p style={{ margin: '2px 0 0 0', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {alt.reason}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 5. Event Log */}
                <div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 12, letterSpacing: '0.05em', fontWeight: 600 }}>Recent Supply Chain Events</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8, paddingLeft: 12, borderLeft: '2px solid var(--border)' }}>
                    {explanation.event_log?.map((evt: any, idx: number) => (
                      <div key={idx} style={{ position: 'relative', fontSize: '0.78rem' }}>
                        <div style={{
                          position: 'absolute', left: -17, top: 5,
                          width: 8, height: 8, borderRadius: '50%', background: evt.event?.includes('⚠️') ? 'var(--warning)' : 'var(--accent-primary)',
                        }} />
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)', marginRight: 8, fontFamily: 'var(--font-mono)' }}>{evt.time}</span>
                        <span style={{ color: 'var(--text-secondary)' }}>{evt.event}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                Explanation detail unavailable
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
