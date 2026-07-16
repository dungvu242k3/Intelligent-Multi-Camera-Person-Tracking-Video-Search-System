import axios from 'axios';
import { useAuthStore } from '../stores/authStore.ts';

const axiosInstance = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Inject Access Token if authenticated
axiosInstance.interceptors.request.use(
  (config) => {
    const { accessToken } = useAuthStore.getState();
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor: Global error handler & auth session cleanup on 401
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    // If backend returns 401 (Unauthorized / Expired session), clean auth state and redirect
    if (error.response && error.response.status === 401) {
      const { logout } = useAuthStore.getState();
      logout();
      
      // Prevent redirect loop if already on login page
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
