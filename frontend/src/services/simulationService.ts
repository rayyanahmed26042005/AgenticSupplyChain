import api from './api';
import type { SimulationRequest } from '../types';

export const simulationService = {
  run: (params: SimulationRequest) => api.post('/simulation/run', params),
  getState: () => api.get('/simulation/state'),
  pause: () => api.post('/simulation/pause'),
  resume: () => api.post('/simulation/resume'),
  stop: () => api.post('/simulation/stop'),
  
  // Scenarios
  listScenarios: () => api.get('/simulation/scenarios'),
  getScenario: (id: string) => api.get(`/simulation/scenarios/${id}`),
  createScenario: (data: any) => api.post('/simulation/scenarios', data),
  runScenario: (id: string) => api.post(`/simulation/scenarios/${id}/run`),
  
  // Disruptions
  getDisruptionTypes: () => api.get('/simulation/disruptions/types'),
  generateDisruption: (type: string, severity?: number) =>
    api.post(`/simulation/disruptions/generate?disruption_type=${type}${severity ? `&severity=${severity}` : ''}`),
  
  // History
  getHistory: () => api.get('/simulation/history'),
  getSaved: (id: string) => api.get(`/simulation/history/${id}`),
  getLatest: () => api.get('/simulation/latest'),
};
