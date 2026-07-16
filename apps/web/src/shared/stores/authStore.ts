import { create } from 'zustand';

export interface UserProfile {
  id: string;
  email: string;
  role_id: number;
  full_name?: string;
}

interface DecodedToken {
  sub: string;
  email: string;
  role_id: number;
  full_name?: string;
  exp?: number;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  user: UserProfile | null;
  login: (accessToken: string, refreshToken: string) => void;
  logout: () => void;
  initAuth: () => void;
}

// Custom dependency-free JWT decoder
function decodeJwt(token: string): DecodedToken | null {
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
  } catch (e) {
    return null;
  }
}

function isTokenExpired(decoded: DecodedToken | null): boolean {
  if (!decoded || !decoded.exp) return true;
  // Account for a 10 seconds clock drift buffer
  return decoded.exp * 1000 < (Date.now() + 10000);
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  user: null,

  login: (accessToken: string, refreshToken: string) => {
    localStorage.setItem('mcpt_access_token', accessToken);
    localStorage.setItem('mcpt_refresh_token', refreshToken);
    
    const decoded = decodeJwt(accessToken);
    if (decoded) {
      set({
        accessToken,
        refreshToken,
        isAuthenticated: true,
        user: {
          id: decoded.sub,
          email: decoded.email,
          role_id: decoded.role_id,
          full_name: decoded.full_name || decoded.email.split('@')[0],
        },
      });
    }
  },

  logout: () => {
    localStorage.removeItem('mcpt_access_token');
    localStorage.removeItem('mcpt_refresh_token');
    set({
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      user: null,
    });
  },

  initAuth: () => {
    const accessToken = localStorage.getItem('mcpt_access_token');
    const refreshToken = localStorage.getItem('mcpt_refresh_token');

    if (accessToken && refreshToken) {
      const decoded = decodeJwt(accessToken);
      if (decoded && !isTokenExpired(decoded)) {
        set({
          accessToken,
          refreshToken,
          isAuthenticated: true,
          user: {
            id: decoded.sub,
            email: decoded.email,
            role_id: decoded.role_id,
            full_name: decoded.full_name || decoded.email.split('@')[0],
          },
        });
        return;
      }
    }
    // Clean storage if expired or invalid
    localStorage.removeItem('mcpt_access_token');
    localStorage.removeItem('mcpt_refresh_token');
    set({
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      user: null,
    });
  },
}));
