import { writable, derived } from 'svelte/store';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const AUTH_TOKEN_KEY = 'automation_lab_auth_token';
const AUTH_USER_KEY = 'automation_lab_auth_user';

function safeParse(value) {
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function readInitialAuth() {
  if (typeof window === 'undefined') {
    return { token: null, user: null };
  }

  return {
    token: window.localStorage.getItem(AUTH_TOKEN_KEY),
    user: safeParse(window.localStorage.getItem(AUTH_USER_KEY)),
  };
}

function persistAuth(token, user) {
  if (typeof window === 'undefined') return;

  if (token) {
    window.localStorage.setItem(AUTH_TOKEN_KEY, token);
  } else {
    window.localStorage.removeItem(AUTH_TOKEN_KEY);
  }

  if (user) {
    window.localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  } else {
    window.localStorage.removeItem(AUTH_USER_KEY);
  }
}

const initialAuth = readInitialAuth();

export const authToken = writable(initialAuth.token);
export const authUser = writable(initialAuth.user);
export const isAuthenticated = derived(authToken, ($authToken) => Boolean($authToken));

async function postJson(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const message = await response.text();
    const error = new Error(message || 'Login failed.');
    error.status = response.status;
    throw error;
  }

  return response.json();
}

export async function login(email, password) {
  const payload = await postJson('/login', { email, password });
  authToken.set(payload.token || null);
  authUser.set(payload.user || { email });
  persistAuth(payload.token || null, payload.user || { email });
  return payload;
}

export function logout() {
  authToken.set(null);
  authUser.set(null);
  persistAuth(null, null);
}
