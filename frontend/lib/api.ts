import axios from 'axios';

// API基址配置：支持内外网访问
// 1. 生产环境：使用相对路径（通过Next.js代理转发到后端），支持任何域名和端口
// 2. 开发环境：如果设置环境变量则使用，否则使用localhost:3001
const getBaseURL = () => {
  // 优先使用环境变量
  if (process.env.NEXT_PUBLIC_API_BASE) {
    return process.env.NEXT_PUBLIC_API_BASE;
  }
  
  // 开发环境：使用相对路径（会被Next.js代理）
  return '/api/v1';
};

const BASE = getBaseURL();

// 增加超时时间：VOS API 可能响应较慢
const api = axios.create({ baseURL: BASE, timeout: 60000 }); // 60秒

console.log('API Base URL:', BASE);

// 请求拦截器：添加 token
api.interceptors.request.use(cfg => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  if (token && cfg.headers) cfg.headers['Authorization'] = `Bearer ${token}`;
  return cfg;
});

// 响应拦截器：处理会话超时
api.interceptors.response.use(
  response => response,
  error => {
    // 检查是否是401或403错误（会话超时或无权限）
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      // 清除 token
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        // 延迟跳转，避免多个请求同时重定向
        setTimeout(() => {
          if (window.location.pathname !== '/login') {
            window.location.href = '/login?timeout=1';
          }
        }, 100);
      }
    }
    // 捕获JWT过期错误（通常表现为401）
    if (error.message && error.message.includes('expired')) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        setTimeout(() => {
          if (window.location.pathname !== '/login') {
            window.location.href = '/login?timeout=1';
          }
        }, 100);
      }
    }
    return Promise.reject(error);
  }
);

export default api;
