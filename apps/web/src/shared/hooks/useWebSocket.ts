import { useEffect, useRef, useSyncExternalStore } from 'react';
import { isAccessTokenUsable, useAuthStore } from '../stores/authStore.ts';
import { refreshAccessToken } from '../utils/axiosInstance.ts';

export type WebSocketStatus = 'idle' | 'connecting' | 'open' | 'reconnecting' | 'closed' | 'error';

type MessageHandler = (payload: unknown, event: MessageEvent<string>) => void;
type StatusHandler = () => void;

interface UseWebSocketOptions {
  onMessage?: MessageHandler;
}

interface UseWebSocketResult {
  status: WebSocketStatus;
  isConnected: boolean;
  send: (payload: string | Record<string, unknown>) => boolean;
}

const BASE_RECONNECT_DELAY_MS = 1_000;
const MAX_RECONNECT_DELAY_MS = 30_000;
const HEARTBEAT_INTERVAL_MS = 25_000;
const ALLOWED_WEBSOCKET_PROTOCOLS = new Set(['ws:', 'wss:']);

export function resolveWebSocketUrl(accessToken: string): string {
  const configuredUrl = import.meta.env.VITE_WS_URL as string | undefined;

  const url = configuredUrl ? new URL(configuredUrl, window.location.origin) : new URL('/ws', window.location.origin);
  if (!configuredUrl) {
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  }

  if (!ALLOWED_WEBSOCKET_PROTOCOLS.has(url.protocol)) {
    throw new Error('Configured websocket URL must use ws:// or wss://');
  }

  if (window.location.protocol === 'https:' && url.protocol !== 'wss:') {
    throw new Error('Secure pages must use wss:// websocket connections');
  }

  url.searchParams.set('token', accessToken);
  return url.toString();
}

class SharedWebSocketClient {
  private socket: WebSocket | null = null;
  private status: WebSocketStatus = 'idle';
  private subscribers = 0;
  private reconnectAttempt = 0;
  private reconnectTimer: number | null = null;
  private heartbeatTimer: number | null = null;
  private closeTimer: number | null = null;
  private readonly messageHandlers = new Set<MessageHandler>();
  private readonly statusHandlers = new Set<StatusHandler>();

  getSnapshot = (): WebSocketStatus => this.status;

  subscribeStatus = (handler: StatusHandler): (() => void) => {
    this.statusHandlers.add(handler);
    return () => {
      this.statusHandlers.delete(handler);
    };
  };

  addSubscriber(): void {
    this.subscribers += 1;
    this.cancelDeferredClose();
    void this.connect();
  }

  removeSubscriber(): void {
    this.subscribers = Math.max(0, this.subscribers - 1);

    if (this.subscribers === 0) {
      this.closeTimer = window.setTimeout(() => {
        if (this.subscribers === 0) {
          this.disconnect();
        }
      }, 250);
    }
  }

  addMessageHandler(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => {
      this.messageHandlers.delete(handler);
    };
  }

  send(payload: string | Record<string, unknown>): boolean {
    if (this.socket?.readyState !== WebSocket.OPEN) {
      return false;
    }

    this.socket.send(typeof payload === 'string' ? payload : JSON.stringify(payload));
    return true;
  }

  disconnect(): void {
    this.clearReconnectTimer();
    this.clearHeartbeat();
    this.cancelDeferredClose();

    const socket = this.socket;
    this.socket = null;

    if (socket && socket.readyState !== WebSocket.CLOSED && socket.readyState !== WebSocket.CLOSING) {
      socket.onopen = null;
      socket.onmessage = null;
      socket.onerror = null;
      socket.onclose = null;
      socket.close(1000, 'No active subscribers');
    }

    this.setStatus('closed');
  }

  private async connect(): Promise<void> {
    if (this.subscribers === 0) {
      return;
    }

    if (this.socket?.readyState === WebSocket.OPEN || this.socket?.readyState === WebSocket.CONNECTING) {
      return;
    }

    this.clearReconnectTimer();
    this.setStatus(this.reconnectAttempt > 0 ? 'reconnecting' : 'connecting');

    const accessToken = await this.getUsableAccessToken();
    if (!accessToken) {
      useAuthStore.getState().logout();
      this.disconnect();
      return;
    }

    if (this.subscribers === 0) {
      return;
    }

    let socket: WebSocket;
    try {
      socket = new WebSocket(resolveWebSocketUrl(accessToken));
    } catch (error) {
      console.error('[WEBSOCKET_SECURITY]', error);
      this.setStatus('error');
      return;
    }

    this.socket = socket;

    socket.onopen = () => {
      if (this.socket !== socket) return;
      this.reconnectAttempt = 0;
      this.setStatus('open');
      this.startHeartbeat();
    };

    socket.onmessage = (event: MessageEvent<string>) => {
      if (this.socket !== socket) return;
      const payload = this.parseMessage(event.data);
      this.messageHandlers.forEach((handler) => handler(payload, event));
    };

    socket.onerror = () => {
      if (this.socket !== socket) return;
      this.setStatus('error');
    };

    socket.onclose = (event) => {
      if (this.socket !== socket) return;
      this.socket = null;
      this.clearHeartbeat();
      this.setStatus('closed');

      if (this.subscribers > 0 && event.code !== 1000) {
        if (event.code === 4001) {
          void refreshAccessToken().then((token) => {
            if (!token) {
              this.disconnect();
              return;
            }
            this.scheduleReconnect();
          });
          return;
        }

        this.scheduleReconnect();
      }
    };
  }

  private async getUsableAccessToken(): Promise<string | null> {
    const accessToken = useAuthStore.getState().accessToken;

    if (isAccessTokenUsable(accessToken, 15_000)) {
      return accessToken;
    }

    return refreshAccessToken();
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer !== null || this.subscribers === 0) {
      return;
    }

    this.reconnectAttempt += 1;
    const exponentialDelay = BASE_RECONNECT_DELAY_MS * 2 ** (this.reconnectAttempt - 1);
    const jitter = Math.floor(Math.random() * 250);
    const delay = Math.min(exponentialDelay + jitter, MAX_RECONNECT_DELAY_MS);

    this.setStatus('reconnecting');
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      void this.connect();
    }, delay);
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();
    this.heartbeatTimer = window.setInterval(() => {
      this.send({ type: 'ping', sent_at: new Date().toISOString() });
    }, HEARTBEAT_INTERVAL_MS);
  }

  private clearHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      window.clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private cancelDeferredClose(): void {
    if (this.closeTimer !== null) {
      window.clearTimeout(this.closeTimer);
      this.closeTimer = null;
    }
  }

  private setStatus(nextStatus: WebSocketStatus): void {
    if (this.status === nextStatus) {
      return;
    }

    this.status = nextStatus;
    this.statusHandlers.forEach((handler) => handler());
  }

  private parseMessage(data: string): unknown {
    try {
      return JSON.parse(data);
    } catch {
      return data;
    }
  }
}

const sharedWebSocketClient = new SharedWebSocketClient();

useAuthStore.subscribe((state) => {
  if (!state.isAuthenticated) {
    sharedWebSocketClient.disconnect();
  }
});

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketResult {
  const messageHandlerRef = useRef(options.onMessage);
  messageHandlerRef.current = options.onMessage;

  const status = useSyncExternalStore(
    sharedWebSocketClient.subscribeStatus,
    sharedWebSocketClient.getSnapshot,
    sharedWebSocketClient.getSnapshot
  );

  useEffect(() => {
    sharedWebSocketClient.addSubscriber();
    return () => {
      sharedWebSocketClient.removeSubscriber();
    };
  }, []);

  useEffect(() => {
    if (!messageHandlerRef.current) {
      return undefined;
    }

    return sharedWebSocketClient.addMessageHandler((payload, event) => {
      messageHandlerRef.current?.(payload, event);
    });
  }, []);

  return {
    status,
    isConnected: status === 'open',
    send: sharedWebSocketClient.send.bind(sharedWebSocketClient),
  };
}
