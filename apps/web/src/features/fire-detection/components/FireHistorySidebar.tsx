import React from 'react';
import { Flame, CheckCircle, Clock, MapPin, ShieldAlert } from 'lucide-react';

interface FireEvent {
  id: string;
  camera_id: string;
  camera_name: string;
  timestamp: string;
  severity: 'CRITICAL' | 'WARNING' | 'RESOLVED';
  crop_url?: string;
}

interface FireHistorySidebarProps {
  events: FireEvent[];
  onResolveEvent: (id: string) => void;
}

export default function FireHistorySidebar({ events, onResolveEvent }: FireHistorySidebarProps) {
  return (
    <div style={styles.container}>
      {/* Title */}
      <div style={styles.header}>
        <ShieldAlert size={20} color="var(--color-danger)" />
        <h3 style={styles.title}>Fire Alerts Incident Log</h3>
      </div>

      {/* Events Scroll Feed */}
      <div style={styles.list}>
        {events.map((event) => {
          const isCritical = event.severity === 'CRITICAL';
          const isResolved = event.severity === 'RESOLVED';
          
          return (
            <div 
              key={event.id} 
              style={{
                ...styles.card,
                borderColor: isCritical ? 'var(--color-danger)' : isResolved ? 'var(--color-success)' : 'var(--color-warning)',
                backgroundColor: isCritical ? 'rgba(239, 68, 68, 0.03)' : 'var(--color-surface)',
              }}
            >
              {/* Top Row: Camera + Status Badge */}
              <div style={styles.topRow}>
                <div style={styles.camNameGroup}>
                  <MapPin size={14} color="var(--color-text-secondary)" />
                  <span style={styles.camName}>{event.camera_name}</span>
                </div>
                <div style={{
                  ...styles.badge,
                  color: isCritical ? 'var(--color-danger)' : isResolved ? 'var(--color-success)' : 'var(--color-warning)',
                  backgroundColor: isCritical ? 'rgba(239, 68, 68, 0.1)' : isResolved ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                }}>
                  {event.severity}
                </div>
              </div>

              {/* Timestamp Row */}
              <div style={styles.metaRow}>
                <Clock size={12} color="var(--color-text-secondary)" />
                <span style={styles.time}>{event.timestamp}</span>
              </div>

              {/* Event Content / Alert message */}
              <div style={styles.alertContent}>
                <Flame size={18} color={isResolved ? 'var(--color-success)' : 'var(--color-danger)'} />
                <span style={styles.alertText}>
                  {isResolved 
                    ? 'Fire safety verification check: RESOLVED.' 
                    : 'CRITICAL: Flame/Smoke signature detected on GPU analytics engine!'
                  }
                </span>
              </div>

              {/* Resolve Actions Button */}
              {!isResolved && (
                <button 
                  type="button" 
                  onClick={() => onResolveEvent(event.id)}
                  style={styles.resolveBtn}
                >
                  <CheckCircle size={14} />
                  <span>Mark as Resolved</span>
                </button>
              )}
            </div>
          );
        })}

        {events.length === 0 && (
          <div style={styles.emptyCard}>
            <CheckCircle size={28} color="var(--color-success)" />
            <span style={styles.emptyHeading}>All Zones Nominal</span>
            <span style={styles.emptyText}>No active fire signature warnings detected.</span>
          </div>
        )}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '320px',
    backgroundColor: 'var(--color-surface)',
    borderLeft: '1px solid var(--color-border)',
    display: 'flex',
    flexDirection: 'column',
    height: 'calc(100vh - 70px)', /* Full height minus header */
    position: 'fixed',
    top: '70px',
    right: 0,
    zIndex: 98,
  },
  header: {
    padding: '20px 24px',
    borderBottom: '1px solid var(--color-border)',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  title: {
    fontSize: '15px',
    fontWeight: 600,
    color: 'var(--color-text)',
    fontFamily: 'var(--font-heading)',
  },
  list: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  card: {
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    boxShadow: 'var(--shadow-sm)',
    transition: 'all 200ms ease',
  },
  topRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  camNameGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  camName: {
    fontSize: '13px',
    fontWeight: 600,
    color: 'var(--color-text)',
  },
  badge: {
    fontSize: '9px',
    fontWeight: 700,
    padding: '3px 8px',
    borderRadius: 'var(--radius-sm)',
    fontFamily: 'var(--font-heading)',
  },
  metaRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '11px',
    color: 'var(--color-text-secondary)',
  },
  time: {
    marginTop: '1px',
  },
  alertContent: {
    display: 'flex',
    gap: '10px',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(30, 41, 59, 0.4)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-sm)',
    padding: '8px 10px',
  },
  alertText: {
    fontSize: '12px',
    color: 'var(--color-text)',
    lineHeight: 1.4,
    textAlign: 'left',
  },
  resolveBtn: {
    alignSelf: 'flex-start',
    background: 'none',
    border: 'none',
    color: 'var(--color-success)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '12px',
    fontWeight: 600,
    padding: '4px 0',
  },
  emptyCard: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px 20px',
    textAlign: 'center',
    gap: '12px',
    border: '1px dashed var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'rgba(30, 41, 59, 0.2)',
    marginTop: '20px',
  },
  emptyHeading: {
    fontSize: '14px',
    fontWeight: 600,
    color: 'var(--color-success)',
  },
  emptyText: {
    fontSize: '12px',
    color: 'var(--color-text-secondary)',
    lineHeight: 1.4,
  },
};
