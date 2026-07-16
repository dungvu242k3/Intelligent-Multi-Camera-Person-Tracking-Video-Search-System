import React from 'react';

export type BadgeVariant = 'success' | 'danger' | 'warning' | 'info' | 'primary';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  style?: React.CSSProperties;
}

export default function Badge({ children, variant = 'info', style }: BadgeProps) {
  const getStyle = (): React.CSSProperties => {
    let background = 'var(--color-border)';
    let color = 'var(--color-text)';
    let border = '1px solid var(--color-border)';

    if (variant === 'success') {
      background = 'var(--color-success-bg)';
      color = 'var(--color-success)';
      border = '1px solid rgba(16, 185, 129, 0.3)';
    } else if (variant === 'danger') {
      background = 'var(--color-danger-bg)';
      color = 'var(--color-danger)';
      border = '1px solid rgba(239, 68, 68, 0.3)';
    } else if (variant === 'warning') {
      background = 'var(--color-warning-bg)';
      color = 'var(--color-warning)';
      border = '1px solid rgba(245, 158, 11, 0.3)';
    } else if (variant === 'primary') {
      background = 'rgba(59, 130, 246, 0.1)';
      color = 'var(--color-primary)';
      border = '1px solid rgba(59, 130, 246, 0.3)';
    }

    return {
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
      padding: '4px 10px',
      borderRadius: 'var(--radius-xl)',
      fontSize: '12px',
      fontWeight: 600,
      fontFamily: 'var(--font-body)',
      background,
      color,
      border,
      textTransform: 'capitalize',
      ...style,
    };
  };

  return <span style={getStyle()}>{children}</span>;
}
