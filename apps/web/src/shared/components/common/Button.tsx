import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export default function Button({
  children,
  variant = 'primary',
  isLoading = false,
  icon,
  style,
  disabled,
  ...props
}: ButtonProps) {
  const getButtonClass = () => {
    if (variant === 'primary') return 'btn-primary';
    if (variant === 'secondary') return 'btn-secondary';
    return ''; // Handle danger variant dynamically
  };

  const getStyle = (): React.CSSProperties => {
    let baseStyle: React.CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '8px',
      cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
      opacity: disabled || isLoading ? 0.6 : 1,
      transition: 'all 150ms ease',
    };

    if (variant === 'danger') {
      baseStyle = {
        ...baseStyle,
        backgroundColor: 'var(--color-danger)',
        color: 'white',
        border: 'none',
        padding: '10px 20px',
        borderRadius: 'var(--radius-md)',
        fontWeight: 600,
      };
    }

    return { ...baseStyle, ...style };
  };

  return (
    <button
      className={getButtonClass()}
      style={getStyle()}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <span
          style={{
            width: '14px',
            height: '14px',
            border: '2px solid rgba(255,255,255,0.3)',
            borderTopColor: 'white',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }}
        />
      )}
      {!isLoading && icon}
      <span>{children}</span>
    </button>
  );
}
