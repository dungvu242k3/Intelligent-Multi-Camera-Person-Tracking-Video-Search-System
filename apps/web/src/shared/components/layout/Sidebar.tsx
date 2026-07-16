import { NavLink } from 'react-router-dom';
import { useTranslation } from '../../hooks/useTranslation.ts';
import { 
  LayoutDashboard, 
  Tv, 
  Search, 
  Camera, 
  FileVideo, 
  Flame,
  ShieldAlert
} from 'lucide-react';

export default function Sidebar() {
  const { t } = useTranslation();
  
  const links = [
    { to: '/', label: t('nav.dashboard'), icon: LayoutDashboard },
    { to: '/live', label: t('nav.liveMonitor'), icon: Tv },
    { to: '/search', label: t('nav.personSearch'), icon: Search },
    { to: '/cameras', label: t('nav.cameras'), icon: Camera },
    { to: '/video-test', label: t('nav.videoTest'), icon: FileVideo },
    { to: '/fire-detection', label: t('nav.fireAlarms'), icon: Flame },
  ];

  return (
    <aside style={styles.sidebar}>
      {/* Brand Logo Header */}
      <div style={styles.brand}>
        <ShieldAlert size={28} color="var(--color-cta)" />
        <span style={styles.brandText}>MCPT SYSTEM</span>
      </div>
      
      {/* Navigation List */}
      <nav style={styles.nav}>
        {links.map((link) => {
          const Icon = link.icon;
          return (
            <NavLink
              key={link.to}
              to={link.to}
              style={({ isActive }) => ({
                ...styles.link,
                backgroundColor: isActive ? 'var(--color-border)' : 'transparent',
                color: isActive ? 'var(--color-text)' : 'var(--color-text-secondary)',
              })}
            >
              <Icon size={20} />
              <span style={styles.linkLabel}>{link.label}</span>
            </NavLink>
          );
        })}
      </nav>
      
      {/* System Footer Info */}
      <div style={styles.footer}>
        <span style={styles.version}>v1.0.0 (Production)</span>
      </div>
    </aside>
  );
}

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    width: '240px',
    backgroundColor: 'var(--color-surface)',
    borderRight: '1px solid var(--color-border)',
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    position: 'fixed',
    top: 0,
    left: 0,
    zIndex: 100,
  },
  brand: {
    height: '70px',
    borderBottom: '1px solid var(--color-border)',
    display: 'flex',
    alignItems: 'center',
    padding: '0 20px',
    gap: '12px',
  },
  brandText: {
    fontFamily: 'var(--font-heading)',
    fontSize: '16px',
    fontWeight: 700,
    letterSpacing: '1px',
    color: 'var(--color-text)',
  },
  nav: {
    flex: 1,
    padding: '20px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  link: {
    display: 'flex',
    alignItems: 'center',
    padding: '12px 16px',
    borderRadius: 'var(--radius-md)',
    textDecoration: 'none',
    gap: '12px',
    fontFamily: 'var(--font-body)',
    fontSize: '14px',
    fontWeight: 500,
    transition: 'background-color 150ms ease, color 150ms ease',
  },
  linkLabel: {
    marginTop: '2px',
  },
  footer: {
    padding: '16px 20px',
    borderTop: '1px solid var(--color-border)',
    display: 'flex',
    alignItems: 'center',
  },
  version: {
    fontSize: '11px',
    fontFamily: 'var(--font-heading)',
    color: 'var(--color-text-secondary)',
  },
};
