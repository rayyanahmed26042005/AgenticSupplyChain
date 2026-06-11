import api from './api';

export const agentService = {
  getAllStatus: () => api.get('/agents/status'),
  getAgentStatus: (name: string) => api.get(`/agents/${name}/status`),
  getDecisions: (count?: number) => api.get(`/agents/decisions?count=${count || 10}`),
  getAgentDecisions: (name: string, count?: number) => api.get(`/agents/${name}/decisions?count=${count || 10}`),
  getPerformance: () => api.get('/agents/performance'),
  runAgents: (env?: any) => api.post('/agents/run', env),
  resetAgents: () => api.post('/agents/reset'),
  explainDecision: (decision: any) => api.post('/agents/explain', decision),
  
  // Forecast
  forecastDemand: (data: number[], horizon?: number) =>
    api.post('/forecast/demand', { data, horizon: horizon || 7 }),
  
  // Supplier risk
  predictRisk: (data: any) => api.post('/supplier/risk', data),
  
  // Admin
  getMode: () => api.get('/admin/mode'),
  switchMode: (mode: string) => api.post('/admin/mode', { mode }),
  switchDataSource: (source: string) => api.post('/admin/data-source', { source }),
  getAvailableSources: () => api.get('/admin/data-sources'),
  getEvents: (count?: number) => api.get(`/admin/events?count=${count || 50}`),
};
