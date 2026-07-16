import React, { useState } from 'react';
import { Link2, AlertCircle } from 'lucide-react';

interface UrlInputProps {
  onUrlSubmitted: (url: string) => void;
}

export default function UrlInput({ onUrlSubmitted }: UrlInputProps) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmed = url.trim();
    if (!trimmed) {
      setError("Please specify a stream URL or endpoint path.");
      return;
    }

    const pattern = /^(rtsp:\/\/|http:\/\/|https:\/\/)/i;
    if (!pattern.test(trimmed)) {
      setError("URL must start with rtsp://, http://, or https:// schema.");
      return;
    }

    onUrlSubmitted(trimmed);
  };

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <div style={styles.inputContainer}>
        <Link2 size={20} color="var(--color-text-secondary)" style={styles.icon} />
        <input 
          type="text" 
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="e.g. rtsp://192.168.1.100:554/stream1 or https://example.com/stream.mp4"
          style={styles.input}
        />
      </div>

      <button type="submit" className="btn-primary" style={styles.btn}>
        Analyze URL
      </button>

      {error && (
        <div style={styles.errorCard}>
          <AlertCircle size={20} color="var(--color-danger)" />
          <span style={styles.errorText}>{error}</span>
        </div>
      )}
    </form>
  );
}

const styles: Record<string, React.CSSProperties> = {
  form: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    padding: '12px 0',
  },
  inputContainer: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: 'rgba(30, 41, 59, 0.5)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    padding: '6px 12px',
    width: '100%',
  },
  icon: {
    marginRight: '12px',
  },
  input: {
    flex: 1,
    border: 'none',
    outline: 'none',
    backgroundColor: 'transparent',
    color: 'var(--color-text)',
    fontSize: '14px',
    fontFamily: 'var(--font-body)',
    padding: '10px 0',
  },
  btn: {
    alignSelf: 'flex-start',
    padding: '12px 24px',
    fontSize: '13px',
  },
  errorCard: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '12px',
    backgroundColor: 'var(--color-danger-bg)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    borderRadius: 'var(--radius-md)',
    padding: '12px 16px',
    marginTop: '8px',
    alignSelf: 'flex-start',
  },
  errorText: {
    fontSize: '13px',
    color: 'var(--color-danger)',
  },
};
