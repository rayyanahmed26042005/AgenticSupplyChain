// ============= Core Types =============

export type AppMode = 'simulation' | 'realtime' | 'hybrid';
export type DataSourceType = 'csv' | 'kafka' | 'api' | 'manual' | 'kaggle' | 'database';

export interface ModeInfo {
  current_mode: AppMode;
  data_source: DataSourceType;
  name: string;
  description: string;
  features: string[];
  data_sources: string[];
}

// ============= Simulation =============

export interface SimulationRequest {
  simulation_days: number;
  num_disruptions: number;
  base_demand: number;
  seed: number;
}

export interface SimulationMetric {
  day: number;
  demand: number;
  inventory: number;
  supplier_risk: number;
  on_time_delivery: number;
  cost: number;
  revenue: number;
  stockout: boolean;
  timestamp: string;
}

export interface Disruption {
  id?: string;
  day: number;
  type: string;
  description?: string;
  severity: number;
  impact?: number;
  resolved?: boolean;
}

export interface SimulationStatistics {
  avg_demand: number;
  max_demand: number;
  avg_inventory: number;
  min_inventory: number;
  avg_supplier_risk: number;
  max_supplier_risk: number;
  avg_on_time: number;
  min_on_time: number;
  total_cost: number;
  total_revenue: number;
  profit: number;
  stockout_days: number;
  stockout_rate: number;
}

export interface SimulationResult {
  simulation_id: string;
  status: string;
  days: number;
  disruptions: Disruption[];
  disruption_count: number;
  metrics: SimulationMetric[];
  statistics: SimulationStatistics;
  agent_analysis?: AgentSummary;
}

// ============= Agents =============

export interface AgentState {
  agent_id: string;
  name: string;
  role: string;
  status: string;
  decisions_made: number;
  memory_size: number;
  performance: Record<string, number>;
}

export interface AgentDecision {
  timestamp: string;
  agent: string;
  decision: {
    action: string;
    reasoning: string;
    [key: string]: any;
  };
  result: Record<string, any>;
}

export interface AgentSummary {
  demand_action: string;
  supplier_risk: string;
  coordinated_action: string;
  conflict_resolved: boolean;
}

// ============= Scenario =============

export interface Scenario {
  id: string;
  name: string;
  description: string;
  simulation_days: number;
  base_demand: number;
  num_disruptions: number;
  seed: number;
  tags: string[];
}

// ============= Forecast =============

export interface ForecastResult {
  forecast: number[];
  confidence_lower: number[];
  confidence_upper: number[];
  horizon: number;
  method: string;
  current_level: number;
  current_trend: number;
  trend_direction: string;
}

// ============= API Response =============

export interface APIResponse<T = any> {
  status: string;
  data: T;
  message: string;
  timestamp: string;
}

// ============= Supplier =============

export interface SupplierRiskResult {
  composite_risk: number;
  risk_level: string;
  factor_scores: Record<string, any>;
  top_risk_factors: any[];
  recommendation: string;
}

// ============= Dataset =============

export interface DatasetInfo {
  source: string;
  timestamp: string;
  rows: number;
}
