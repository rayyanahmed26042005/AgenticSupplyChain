import { create } from 'zustand';
import type { AppMode, DataSourceType, ModeInfo } from '../types';

interface AppState {
  mode: AppMode;
  dataSource: DataSourceType;
  modeInfo: ModeInfo | null;
  sidebarCollapsed: boolean;
  loading: boolean;
  error: string | null;
  showSimulation: boolean;
  setMode: (mode: AppMode) => void;
  setDataSource: (source: DataSourceType) => void;
  setModeInfo: (info: ModeInfo) => void;
  toggleSidebar: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setShowSimulation: (show: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  mode: 'simulation',
  dataSource: 'manual',
  modeInfo: null,
  sidebarCollapsed: false,
  loading: false,
  error: null,
  showSimulation: false,
  setMode: (mode) => set({ mode }),
  setDataSource: (source) => set({ dataSource: source }),
  setModeInfo: (info) => set({ modeInfo: info }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setShowSimulation: (show) => set({ showSimulation: show }),
}));
