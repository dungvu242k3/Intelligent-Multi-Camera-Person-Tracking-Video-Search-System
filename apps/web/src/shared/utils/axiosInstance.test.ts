import { AxiosError, type AxiosAdapter, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import axiosInstance from './axiosInstance.ts';

const originalAdapter = axiosInstance.defaults.adapter;

function createResponse(config: InternalAxiosRequestConfig, status = 200): AxiosResponse {
  return {
    data: { ok: true },
    status,
    statusText: status === 200 ? 'OK' : 'ERROR',
    headers: {},
    config,
  };
}

function createHttpError(config: InternalAxiosRequestConfig, status: number): AxiosError {
  return new AxiosError('request failed', undefined, config, {}, createResponse(config, status));
}

describe('axiosInstance retry strategy', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    axiosInstance.defaults.adapter = originalAdapter;
  });

  it('retries retryable safe requests', async () => {
    const adapter = vi.fn<AxiosAdapter>()
      .mockImplementationOnce((config) => Promise.reject(createHttpError(config, 500)))
      .mockImplementationOnce((config) => Promise.resolve(createResponse(config)));

    axiosInstance.defaults.adapter = adapter;

    const request = axiosInstance.get('/health');
    await vi.advanceTimersByTimeAsync(300);

    await expect(request).resolves.toMatchObject({ status: 200 });
    expect(adapter).toHaveBeenCalledTimes(2);
  });

  it('does not retry unsafe requests unless explicitly enabled', async () => {
    const adapter = vi.fn<AxiosAdapter>()
      .mockImplementationOnce((config) => Promise.reject(createHttpError(config, 500)));

    axiosInstance.defaults.adapter = adapter;

    await expect(axiosInstance.post('/cameras/test-url', { url: 'rtsp://camera.local/stream' })).rejects.toBeInstanceOf(
      AxiosError
    );
    expect(adapter).toHaveBeenCalledTimes(1);
  });
});
