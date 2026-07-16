import { create } from 'zustand';

export interface UserProfile {
  id: string;
  email: string;
  role_id: number;
  full_name?: string;
}

interface DecodedToken {
  sub: string;
  email?: string;
  role_id?: number;
  full_name?: string;
  exp?: number;
  type?: 'access' | 'refresh';
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isInitialized: boolean;
  user: UserProfile | null;
  login: (accessToken: string, refreshToken?: string | null) => void;
  setAccessToken: (accessToken: string, refreshToken?: string | null) => void;
  getRefreshToken: () => string | null;
  logout: () => void;
  initAuth: () => void;
}

const ACCESS_TOKEN_STORAGE_KEY = 'mcpt_access_token';
const LEGACY_REFRESH_TOKEN_STORAGE_KEY = 'mcpt_refresh_token';
const TOKEN_EXPIRY_BUFFER_MS = 10_000;

let inMemoryRefreshToken: string | null = null;

// Custom dependency-free JWT decoder
export function decodeJwt(token: string): DecodedToken | null {
  try {
    const base64Url = token.split('.')[1];
    if (!base64Url) return null;
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      window
        .atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export function isTokenExpired(decoded: DecodedToken | null, bufferMs = TOKEN_EXPIRY_BUFFER_MS): boolean {
  if (!decoded || !decoded.exp) return true;
  return decoded.exp * 1000 - bufferMs <= Date.now();
}

export function isAccessTokenUsable(token: string | null, bufferMs = TOKEN_EXPIRY_BUFFER_MS): boolean {
  const decoded = token ? decodeJwt(token) : null;
  return !!decoded && decoded.type === 'access' && !isTokenExpired(decoded, bufferMs);
}

function buildUserProfile(decoded: DecodedToken): UserProfile | null {
  if (!decoded.sub || !decoded.email || typeof decoded.role_id !== 'number') {
    return null;
  }

  return {
    id: decoded.sub,
    email: decoded.email,
    role_id: decoded.role_id,
    full_name: decoded.full_name || decoded.email.split('@')[0],
  };
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isInitialized: false,
  user: null,

  login: (accessToken: string, refreshToken?: string | null) => {
    useAuthStore.getState().setAccessToken(accessToken, refreshToken);
  },

  setAccessToken: (accessToken: string, refreshToken?: string | null) => {
    const decoded = decodeJwt(accessToken);
    const user = decoded?.type === 'access' ? buildUserProfile(decoded) : null;

    if (!user || isTokenExpired(decoded)) {
      useAuthStore.getState().logout();
      return;
    }

    localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, accessToken);
    localStorage.removeItem(LEGACY_REFRESH_TOKEN_STORAGE_KEY);

    if (refreshToken) {
      inMemoryRefreshToken = refreshToken;
    }

    set({
      accessToken,
      refreshToken: inMemoryRefreshToken,
      isAuthenticated: true,
      isInitialized: true,
      user,
    });
  },

  getRefreshToken: () => inMemoryRefreshToken,

  logout: () => {
    inMemoryRefreshToken = null;
    localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
    localStorage.removeItem(LEGACY_REFRESH_TOKEN_STORAGE_KEY);
    set({
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isInitialized: true,
      user: null,
    });
  },

  initAuth: () => {
    const accessToken = localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
    const legacyRefreshToken = localStorage.getItem(LEGACY_REFRESH_TOKEN_STORAGE_KEY);
    localStorage.removeItem(LEGACY_REFRESH_TOKEN_STORAGE_KEY);

    if (legacyRefreshToken) {
      inMemoryRefreshToken = legacyRefreshToken;
    }

    if (accessToken && isAccessTokenUsable(accessToken)) {
      const decoded = decodeJwt(accessToken);
      const user = decoded ? buildUserProfile(decoded) : null;

      if (user) {
        set({
          accessToken,
          refreshToken: inMemoryRefreshToken,
          isAuthenticated: true,
          isInitialized: true,
          user,
        });
        return;
      }
    }

    localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
    set({
      accessToken: null,
      refreshToken: inMemoryRefreshToken,
      isAuthenticated: false,
      isInitialized: true,
      user: null,
    });
  },
}));
