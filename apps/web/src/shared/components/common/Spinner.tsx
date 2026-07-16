import React from 'react';

interface SpinnerProps {
  label?: string;
}

export default function Spinner({ label = 'Loading' }: SpinnerProps) {
  return (
    <div style={styles.container} role="status" aria-live="polite" aria-label={label}>
      <div style={styles.spinner} aria-hidden="true" />
      <span style={styles.label}>{label}</span>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '160px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    color: 'var(--color-text-secondary)',
  },
  spinner: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    border: '3px solid var(--color-border)',
    borderTopColor: 'var(--color-primary)',
    animation: 'spin 900ms linear infinite',
  },
  label: {
    fontSize: '13px',
    fontWeight: 600,
  },
};
