import api from './api';
import type { User } from '../store/authStore';

interface AuthResponse {
  status: string;
  message: string;
  data: {
    token: string;
    user: User;
  };
}

export const authService = {
  async signup(data: any): Promise<AuthResponse> {
    return api.post('/auth/signup', data);
  },

  async login(data: any): Promise<AuthResponse> {
    return api.post('/auth/login', data);
  },

  async oauth(data: { email: string; name: string; provider: string; uid: string }): Promise<AuthResponse> {
    return api.post('/auth/oauth', data);
  },

  async getMe(): Promise<{ data: User }> {
    return api.get('/auth/me');
  }
};
