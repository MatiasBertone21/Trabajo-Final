import axios from 'axios';

/** @deprecated Usar `api/axiosConfig.ts` (mismo cliente). Se mantiene por compatibilidad. */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});
