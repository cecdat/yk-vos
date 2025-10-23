import axios from 'axios';
const BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1';
// 增加超时时间：VOS API 可能响应较慢
const api = axios.create({ baseURL: BASE, timeout: 60000 }); // 60秒
api.interceptors.request.use(cfg => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  if (token && cfg.headers) cfg.headers['Authorization'] = `Bearer ${token}`;
  return cfg;
});
export default api;
