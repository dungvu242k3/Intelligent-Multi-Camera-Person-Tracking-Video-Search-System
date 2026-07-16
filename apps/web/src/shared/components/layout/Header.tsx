import React, { useEffect, useState } from 'react';
import { Radio, Activity } from 'lucide-react';

export default function Header() {
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    // Check gateway websocket connectivity status
    const socket = new WebSocket('ws://localhost:8000/ws');
    
    socket.onopen = () => {
      setWsConnected(true);
    };
    
    socket.onclose = () => {
      setWsConnected(false);
    };
    
    socket.onerror = () => {
      setWsConnected(false);
    };

    return () => {
      socket.close();
    };
  }, []);

  return (
    <header style={styles.header}>
      {/* Title */}
      <div style={styles.titleContainer}>
        <Activity size={18} color="var(--color-primary)" />
        <span style={styles.title}>Control Center</span>
      </div>

      {/* Connection Badges */}
      <div style={styles.badges}>
        {/* API Server status */}
        <div style={styles.badge}>
          <div style={styles.dotActive}></div>
          <span style={styles.badgeText}>API Core: Online</span>
        </div>

        {/* WebSocket realtime indicator */}
        <div style={wsConnected ? styles.badgeActive : styles.badgeOffline}>
          <Radio size={14} className={wsConnected ? 'pulse-red-glow' : ''} />
          <span style={styles.badgeText}>
            Realtime events: {wsConnected ? 'Connected' : 'Offline'}
          </span>
        </div>
      </div>
    </header>
  );
}

const styles: Record<string, React.CSSProperties> = {
  header: {
    height: '70px',
    backgroundColor: 'var(--color-surface)',
    borderBottom: '1px solid var(--color-border)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 24px',
    position: 'fixed',
    top: 0,
    left: '240px',
    right: 0,
    zIndex: 99,
  },
  titleContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  title: {
    fontFamily: 'var(--font-heading)',
    fontSize: '15px',
    fontWeight: 600,
    color: 'var(--color-text)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  badges: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.2)',
    padding: '6px 12px',
    borderRadius: 'var(--radius-xl)',
  },
  badgeActive: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    border: '1px solid rgba(16, 185, 129, 0.3)',
    color: 'var(--color-success)',
    padding: '6px 12px',
    borderRadius: 'var(--radius-xl)',
  },
  badgeOffline: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    color: 'var(--color-danger)',
    padding: '6px 12px',
    borderRadius: 'var(--radius-xl)',
  },
  dotActive: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: 'var(--color-primary)',
  },
  badgeText: {
    fontSize: '12px',
    fontWeight: 600,
    fontFamily: 'var(--font-body)',
  },
};
