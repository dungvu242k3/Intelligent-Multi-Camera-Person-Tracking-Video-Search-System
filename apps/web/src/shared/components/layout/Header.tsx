import React from 'react';
import { Radio, Activity, Globe, LogOut } from 'lucide-react';
import { useTranslation } from '../../hooks/useTranslation.ts';
import { useAuthStore } from '../../stores/authStore.ts';
import { useWebSocket } from '../../hooks/useWebSocket.ts';

export default function Header() {
  const { locale, setLocale, t } = useTranslation();
  const { user, logout } = useAuthStore();
  const { isConnected: wsConnected } = useWebSocket();

  const toggleLanguage = () => {
    setLocale(locale === 'en' ? 'vi' : 'en');
  };

  return (
    <header style={styles.header}>
      {/* Title */}
      <div style={styles.titleContainer}>
        <Activity size={18} color="var(--color-primary)" />
        <span style={styles.title}>{t('header.controlCenter')}</span>
      </div>

      {/* Connection Badges & User Info */}
      <div style={styles.badges}>
        {/* Language Toggle Switch */}
        <button 
          type="button" 
          onClick={toggleLanguage} 
          style={styles.langBtn}
        >
          <Globe size={14} />
          <span>{locale === 'en' ? 'EN' : 'VI'}</span>
        </button>

        {/* WebSocket realtime indicator */}
        <div style={wsConnected ? styles.badgeActive : styles.badgeOffline}>
          <Radio size={14} className={wsConnected ? 'pulse-red-glow' : ''} />
          <span style={styles.badgeText} role="status" aria-live="polite">
            {wsConnected ? t('header.realtimeConnected') : t('header.realtimeOffline')}
          </span>
        </div>

        {/* Operator Profile and Logout Wrapper */}
        {user && (
          <div style={styles.userContainer}>
            <div style={styles.userInfo}>
              <span style={styles.userName}>{user.full_name}</span>
              <span style={styles.userRole}>
                {user.role_id === 1 ? t('auth.roleAdmin') : t('auth.roleOperator')}
              </span>
            </div>
            <button 
              type="button" 
              onClick={logout} 
              style={styles.logoutBtn} 
              title={t('auth.logout')}
              aria-label={t('auth.logout')}
            >
              <LogOut size={15} color="var(--color-danger)" />
            </button>
          </div>
        )}
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
    gap: '16px',
  },
  langBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    backgroundColor: 'var(--color-border)',
    color: 'var(--color-text)',
    border: 'none',
    padding: '6px 12px',
    borderRadius: 'var(--radius-sm)',
    fontSize: '11px',
    fontWeight: 600,
    fontFamily: 'var(--font-heading)',
    cursor: 'pointer',
    transition: 'background-color 150ms ease',
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
  userContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    paddingLeft: '16px',
    borderLeft: '1px solid var(--color-border)',
  },
  userInfo: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
  },
  userName: {
    fontSize: '13px',
    fontWeight: 600,
    color: 'var(--color-text)',
  },
  userRole: {
    fontSize: '10px',
    fontWeight: 500,
    color: 'var(--color-text-secondary)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  logoutBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: '4px',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 150ms ease',
    backgroundColor: 'rgba(239, 68, 68, 0.05)',
  },
};
