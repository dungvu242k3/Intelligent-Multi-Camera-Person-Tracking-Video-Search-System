import React, { memo, useCallback, useState } from 'react';
import { Link2, AlertCircle } from 'lucide-react';
import { useTranslation } from '../../../shared/hooks/useTranslation.ts';
import { STREAM_URL_PATTERN } from '../constants.ts';

interface UrlInputProps {
  onUrlSubmitted: (url: string) => void;
}

function UrlInput({ onUrlSubmitted }: UrlInputProps) {
  const { t } = useTranslation();
  const [url, setUrl] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmed = url.trim();
    if (!trimmed) {
      setError(t('vtest.url.errEmpty'));
      return;
    }

    if (!STREAM_URL_PATTERN.test(trimmed)) {
      setError(t('vtest.url.errSchema'));
      return;
    }

    onUrlSubmitted(trimmed);
  }, [onUrlSubmitted, t, url]);

  const handleUrlChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value);
  }, []);

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <label htmlFor="video-url-input" style={styles.label}>
        {t('vtest.tabUrl')}
      </label>
      <div style={styles.inputContainer}>
        <Link2 size={20} color="var(--color-text-secondary)" style={styles.icon} />
        <input 
          id="video-url-input"
          type="text" 
          value={url}
          onChange={handleUrlChange}
          placeholder={t('vtest.url.placeholder')}
          aria-invalid={!!error}
          aria-describedby={error ? 'video-url-error' : undefined}
          style={styles.input}
        />
      </div>

      <button type="submit" className="btn-primary" style={styles.btn}>
        {t('vtest.url.btn')}
      </button>

      {error && (
        <div style={styles.errorCard} role="alert" id="video-url-error">
          <AlertCircle size={20} color="var(--color-danger)" />
          <span style={styles.errorText}>{error}</span>
        </div>
      )}
    </form>
  );
}

export default memo(UrlInput);

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
  label: {
    fontSize: '12px',
    fontWeight: 600,
    color: 'var(--color-text)',
    textTransform: 'uppercase',
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
