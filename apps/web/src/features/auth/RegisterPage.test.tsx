import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import axiosInstance from '../../shared/utils/axiosInstance.ts';
import RegisterPage from './RegisterPage.tsx';

vi.mock('../../shared/utils/axiosInstance.ts', () => ({
  default: {
    post: vi.fn(),
  },
  isHttpClientError: vi.fn((error: unknown) => {
    return typeof error === 'object' && error !== null && 'response' in error;
  }),
}));

describe('RegisterPage', () => {
  it('registers a user without sending client-controlled role_id', async () => {
    const user = userEvent.setup();
    vi.mocked(axiosInstance.post).mockResolvedValueOnce({ data: { status: 'success' } });

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/full name/i), 'Jane Operator');
    await user.type(screen.getByLabelText(/email/i), 'jane@example.test');
    await user.type(screen.getByLabelText(/^password$/i), 'StrongPass1');
    await user.type(screen.getByLabelText(/confirm password/i, { selector: 'input' }), 'StrongPass1');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(axiosInstance.post).toHaveBeenCalledTimes(1);
    });

    const [, payload, config] = vi.mocked(axiosInstance.post).mock.calls[0];
    expect(payload).toEqual({
      email: 'jane@example.test',
      password: 'StrongPass1',
      full_name: 'Jane Operator',
    });
    expect(payload).not.toHaveProperty('role_id');
    expect(config).toEqual(expect.objectContaining({ signal: expect.any(AbortSignal) }));
  });
});
