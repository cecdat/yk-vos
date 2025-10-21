import axios from 'axios';
const BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1';
const api = axios.create({ baseURL: BASE, timeout: 10000 });
api.interceptors.request.use(cfg => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  if (token && cfg.headers) cfg.headers['Authorization'] = `Bearer ${token}`;
  return cfg;
});
export default api;
