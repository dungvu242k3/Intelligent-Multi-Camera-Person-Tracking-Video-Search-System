import { afterEach, describe, expect, it, vi } from 'vitest';
import { resolveWebSocketUrl } from './useWebSocket.ts';

describe('resolveWebSocketUrl', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('uses the current origin websocket endpoint and attaches the access token', () => {
    const url = new URL(resolveWebSocketUrl('access-token'));

    expect(url.protocol).toBe('ws:');
    expect(url.pathname).toBe('/ws');
    expect(url.searchParams.get('token')).toBe('access-token');
  });

  it('rejects non-websocket protocols', () => {
    vi.stubEnv('VITE_WS_URL', 'https://api.example.test/ws');

    expect(() => resolveWebSocketUrl('access-token')).toThrow(/must use ws:\/\/ or wss:\/\//i);
  });

  it('rejects insecure websocket URLs on HTTPS pages', () => {
    vi.stubEnv('VITE_WS_URL', 'ws://api.example.test/ws');
    vi.spyOn(window, 'location', 'get').mockReturnValue({
      ...window.location,
      protocol: 'https:',
    } as Location);

    expect(() => resolveWebSocketUrl('access-token')).toThrow(/secure pages must use wss/i);
  });
});
