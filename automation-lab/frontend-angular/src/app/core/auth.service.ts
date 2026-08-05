import { signal } from '@angular/core';
import { apiFetch } from './api.client';

export const authTokenKey = 'angular_lab_token';

export class AuthService {
  private _user = signal<any>(null);

  get user() {
    return this._user();
  }

  isAuthenticated() {
    return !!localStorage.getItem(authTokenKey);
  }

  async login(email: string, password: string) {
    const body = JSON.stringify({ email, password });
    const res = await apiFetch('/login', { method: 'POST', body });
    if (res && res.token) {
      localStorage.setItem(authTokenKey, res.token);
      this._user.set(res.user || null);
      return res;
    }
    throw new Error('Login failed');
  }

  logout() {
    localStorage.removeItem(authTokenKey);
    this._user.set(null);
  }
}

export const authService = new AuthService();
