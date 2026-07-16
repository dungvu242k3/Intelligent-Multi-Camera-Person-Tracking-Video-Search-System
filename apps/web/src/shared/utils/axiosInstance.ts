import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../stores/authStore.ts';

interface TokenRefreshResponse {
  access_token: string;
  token_type: string;
}

interface RetriableRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
  _retryCount?: number;
  retry?: {
    retries?: number;
    retryUnsafeMethods?: boolean;
  };
}

const getApiBaseUrl = (): string => {
  return import.meta.env.VITE_API_BASE_URL || '/api/v1';
};

const DEFAULT_RETRY_COUNT = 2;
const RETRY_BASE_DELAY_MS = 300;
const RETRYABLE_STATUS_CODES = new Set([408, 429, 500, 502, 503, 504]);
const SAFE_RETRY_METHODS = new Set(['get', 'head', 'options']);

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function shouldRetryRequest(error: AxiosError, request: RetriableRequestConfig): boolean {
  if (axios.isCancel(error) || error.code === 'ERR_CANCELED') {
    return false;
  }

  if (error.response?.status === 401) {
    return false;
  }

  const method = request.method?.toLowerCase() || 'get';
  const retryUnsafeMethods = request.retry?.retryUnsafeMethods === true;
  if (!SAFE_RETRY_METHODS.has(method) && !retryUnsafeMethods) {
    return false;
  }

  if (!error.response) {
    return true;
  }

  return RETRYABLE_STATUS_CODES.has(error.response.status);
}

const axiosInstance = axios.create({
  baseURL: getApiBaseUrl(),
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

const refreshClient = axios.create({
  baseURL: getApiBaseUrl(),
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

let refreshPromise: Promise<string | null> | null = null;

export async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    const { setAccessToken, logout } = useAuthStore.getState();

    try {
      const response = await refreshClient.post<TokenRefreshResponse>('/auth/refresh', {});

      setAccessToken(response.data.access_token);
      return response.data.access_token;
    } catch {
      logout();
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export function isHttpClientError(error: unknown): error is AxiosError {
  return axios.isAxiosError(error);
}

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

// Response interceptor: single-flight refresh and retry once on expired credentials
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetriableRequestConfig | undefined;

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      const accessToken = await refreshAccessToken();

      if (accessToken) {
        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return axiosInstance(originalRequest);
      }
    }

    if (originalRequest && shouldRetryRequest(error, originalRequest)) {
      const retryLimit = originalRequest.retry?.retries ?? DEFAULT_RETRY_COUNT;
      const retryCount = originalRequest._retryCount ?? 0;

      if (retryCount < retryLimit) {
        originalRequest._retryCount = retryCount + 1;
        const retryAfterHeader = error.response?.headers?.['retry-after'];
        const retryAfterSeconds = typeof retryAfterHeader === 'string' ? Number(retryAfterHeader) : NaN;
        const retryDelay = Number.isFinite(retryAfterSeconds)
          ? retryAfterSeconds * 1000
          : RETRY_BASE_DELAY_MS * 2 ** retryCount;

        await delay(retryDelay);
        return axiosInstance(originalRequest);
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
