declare global {
  interface Window { __API_BASE__?: string }
}

import { environment } from '../../environments/environment';

export const API_BASE = (typeof window !== 'undefined' && window.__API_BASE__) || environment.apiBase || 'http://localhost:8000';

export async function apiFetch(path: string, options?: RequestInit) {
  const url = API_BASE + path;
  const opts: RequestInit = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };
  const res = await fetch(url, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  const contentType = res.headers.get('content-type') || '';
  if (contentType.includes('application/json')) return res.json();
  return res.text();
}
