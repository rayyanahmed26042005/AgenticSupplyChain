import { create } from 'zustand';
import type { SimulationResult, SimulationMetric, Disruption, Scenario } from '../types';

interface SimulationState {
  result: SimulationResult | null;
  metrics: SimulationMetric[];
  disruptions: Disruption[];
  scenarios: Scenario[];
  isRunning: boolean;
  progress: number;
  setResult: (result: SimulationResult) => void;
  setMetrics: (metrics: SimulationMetric[]) => void;
  setDisruptions: (disruptions: Disruption[]) => void;
  setScenarios: (scenarios: Scenario[]) => void;
  setRunning: (running: boolean) => void;
  setProgress: (progress: number) => void;
  reset: () => void;
}

export const useSimulationStore = create<SimulationState>((set) => ({
  result: null,
  metrics: [],
  disruptions: [],
  scenarios: [],
  isRunning: false,
  progress: 0,
  setResult: (result) =>
    set({
      result,
      metrics: result.metrics || [],
      disruptions: result.disruptions || [],
    }),
  setMetrics: (metrics) => set({ metrics }),
  setDisruptions: (disruptions) => set({ disruptions }),
  setScenarios: (scenarios) => set({ scenarios }),
  setRunning: (isRunning) => set({ isRunning }),
  setProgress: (progress) => set({ progress }),
  reset: () =>
    set({ result: null, metrics: [], disruptions: [], isRunning: false, progress: 0 }),
}));
