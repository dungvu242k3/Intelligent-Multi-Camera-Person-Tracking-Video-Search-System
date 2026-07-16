import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

export default class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = {
    error: null,
  };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('[ERROR_BOUNDARY]', error, errorInfo);
  }

  handleRetry = (): void => {
    this.setState({ error: null });
  };

  render(): React.ReactNode {
    if (!this.state.error) {
      return this.props.children;
    }

    return (
      <main style={styles.page} role="alert" aria-live="assertive">
        <section className="card" style={styles.card}>
          <AlertTriangle size={32} color="var(--color-danger)" aria-hidden="true" />
          <div style={styles.copy}>
            <h1 style={styles.title}>Application error</h1>
            <p style={styles.message}>
              The interface could not render this view safely. You can retry without losing the current session.
            </p>
          </div>
          <button type="button" className="btn-primary" style={styles.button} onClick={this.handleRetry}>
            <RotateCcw size={16} aria-hidden="true" />
            <span>Retry</span>
          </button>
        </section>
      </main>
    );
  }
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '24px',
    backgroundColor: 'var(--color-background)',
  },
  card: {
    maxWidth: '520px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-start',
    gap: '18px',
  },
  copy: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  title: {
    fontSize: '20px',
    color: 'var(--color-text)',
  },
  message: {
    fontSize: '14px',
    lineHeight: 1.5,
    color: 'var(--color-text-secondary)',
  },
  button: {
    padding: '10px 18px',
  },
};
