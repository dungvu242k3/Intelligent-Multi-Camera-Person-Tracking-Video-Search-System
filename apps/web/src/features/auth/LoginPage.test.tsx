import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useAuthStore } from '../../shared/stores/authStore.ts';
import axiosInstance from '../../shared/utils/axiosInstance.ts';
import LoginPage from './LoginPage.tsx';

vi.mock('../../shared/utils/axiosInstance.ts', () => ({
  default: {
    post: vi.fn(),
  },
  isHttpClientError: vi.fn((error: unknown) => {
    return typeof error === 'object' && error !== null && 'response' in error;
  }),
}));

function encodeJwtPayload(payload: Record<string, string | number>): string {
  const encodedPayload = window
    .btoa(JSON.stringify(payload))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');

  return `header.${encodedPayload}.signature`;
}

describe('LoginPage', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.getState().logout();
  });

  it('authenticates and stores the returned access token through the auth store', async () => {
    const user = userEvent.setup();
    const accessToken = encodeJwtPayload({
      sub: 'user-1',
      email: 'operator@example.test',
      role_id: 2,
      type: 'access',
      exp: Math.floor(Date.now() / 1000) + 3600,
    });

    vi.mocked(axiosInstance.post).mockResolvedValueOnce({
      data: {
        access_token: accessToken,
        token_type: 'bearer',
      },
    });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/email/i), 'operator@example.test');
    await user.type(screen.getByLabelText(/^password$/i), 'StrongPass1');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
    });

    expect(axiosInstance.post).toHaveBeenCalledWith(
      '/auth/login',
      {
        email: 'operator@example.test',
        password: 'StrongPass1',
      },
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
  });
});
