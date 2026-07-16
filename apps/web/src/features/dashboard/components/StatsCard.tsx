import React from 'react';

interface StatsCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  description?: string;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
}

export default function StatsCard({
  label,
  value,
  icon,
  description,
  trend,
}: StatsCardProps) {
  return (
    <div className="card" style={styles.card}>
      <div style={styles.header}>
        <span style={styles.label}>{label}</span>
        <div style={styles.iconContainer}>{icon}</div>
      </div>
      <div style={styles.value}>{value}</div>
      {(trend || description) && (
        <div style={styles.footer}>
          {trend && (
            <span
              style={{
                ...styles.trend,
                color: trend.isPositive ? 'var(--color-success)' : 'var(--color-danger)',
              }}
            >
              {trend.value}
            </span>
          )}
          {description && <span style={styles.description}>{description}</span>}
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  card: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    padding: '20px 24px',
    minHeight: '130px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
  },
  label: {
    fontSize: '12px',
    color: 'var(--color-text-secondary)',
    fontWeight: 600,
    fontFamily: 'var(--font-heading)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  iconContainer: {
    width: '32px',
    height: '32px',
    borderRadius: 'var(--radius-sm)',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid var(--color-border)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  value: {
    fontSize: '28px',
    fontWeight: 700,
    color: 'var(--color-text)',
    fontFamily: 'var(--font-heading)',
  },
  footer: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '12px',
    marginTop: 'auto',
  },
  trend: {
    fontWeight: 600,
  },
  description: {
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-body)',
  },
};
