import { create } from 'zustand';
import type { AgentState, AgentDecision } from '../types';

interface AgentStoreState {
  agents: Record<string, AgentState>;
  decisions: AgentDecision[];
  performance: Record<string, any>;
  setAgents: (agents: Record<string, AgentState>) => void;
  setDecisions: (decisions: AgentDecision[]) => void;
  setPerformance: (perf: Record<string, any>) => void;
}

export const useAgentStore = create<AgentStoreState>((set) => ({
  agents: {},
  decisions: [],
  performance: {},
  setAgents: (agents) => set({ agents }),
  setDecisions: (decisions) => set({ decisions }),
  setPerformance: (performance) => set({ performance }),
}));
