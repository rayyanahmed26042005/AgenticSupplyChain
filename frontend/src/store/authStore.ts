import { create } from 'zustand';
import { useSimulationStore } from './simulationStore';

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'customer' | 'admin';
  oauth_provider?: string | null;
}

interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  user: User | null;
  login: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => {
  const token = localStorage.getItem('auth_token');
  const storedUser = localStorage.getItem('auth_user');
  
  let user: User | null = null;
  if (storedUser) {
    try {
      user = JSON.parse(storedUser);
    } catch (e) {
      console.error('Error parsing stored user:', e);
    }
  }
  
  const isAuthenticated = !!token && !!user;

  return {
    isAuthenticated,
    token,
    user,
    login: (token, user) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('auth_user', JSON.stringify(user));
      set({ isAuthenticated: true, token, user });
    },
    logout: () => {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      useSimulationStore.getState().reset();
      set({ isAuthenticated: false, token: null, user: null });
    },
  };
});
