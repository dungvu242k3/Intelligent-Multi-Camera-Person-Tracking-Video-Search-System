import React, { useState } from 'react';
import Button from '../../../shared/components/common/Button.tsx';

interface CameraFormProps {
  initialValues?: {
    name: string;
    rtsp_url: string;
    location: string;
    fps: number;
  };
  onSubmit: (values: { name: string; rtsp_url: string; location: string; fps: number }) => Promise<void>;
  isLoading?: boolean;
  isEdit?: boolean;
}

export default function CameraForm({
  initialValues,
  onSubmit,
  isLoading = false,
  isEdit = false,
}: CameraFormProps) {
  const [name, setName] = useState(initialValues?.name || '');
  const [rtspUrl, setRtspUrl] = useState(initialValues?.rtsp_url || '');
  const [location, setLocation] = useState(initialValues?.location || '');
  const [fps, setFps] = useState(initialValues?.fps || 30);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedName = name.trim();
    const trimmedRtsp = rtspUrl.trim();
    const trimmedLoc = location.trim();

    if (!trimmedName || !trimmedRtsp || !trimmedLoc) {
      setError('All fields are required.');
      return;
    }

    // Basic URL validation
    if (!trimmedRtsp.toLowerCase().startsWith('rtsp://') &&
        !trimmedRtsp.toLowerCase().startsWith('http://') &&
        !trimmedRtsp.toLowerCase().startsWith('https://')) {
      setError('URL must start with rtsp://, http://, or https://');
      return;
    }

    if (fps < 1 || fps > 120) {
      setError('FPS must be between 1 and 120.');
      return;
    }

    try {
      await onSubmit({
        name: trimmedName,
        rtsp_url: trimmedRtsp,
        location: trimmedLoc,
        fps: Number(fps),
      });
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'An error occurred during submission.');
    }
  };

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      {error && <div style={styles.error}>{error}</div>}

      <div style={styles.field}>
        <label htmlFor="cam-name" style={styles.label}>Camera Name</label>
        <input
          id="cam-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Loading Dock A"
          style={styles.input}
          required
        />
      </div>

      <div style={styles.field}>
        <label htmlFor="cam-rtsp" style={styles.label}>RTSP/Stream URL</label>
        <input
          id="cam-rtsp"
          type="text"
          value={rtspUrl}
          onChange={(e) => setRtspUrl(e.target.value)}
          placeholder="rtsp://admin:pass@192.168.1.100:554/live"
          style={styles.input}
          required
          disabled={isEdit} // RTSP URL is unique and cannot be updated easily on backend
        />
      </div>

      <div style={styles.grid}>
        <div style={styles.field}>
          <label htmlFor="cam-loc" style={styles.label}>Location Coordinates</label>
          <input
            id="cam-loc"
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g. 21.0285,105.8542"
            style={styles.input}
            required
          />
        </div>

        <div style={styles.field}>
          <label htmlFor="cam-fps" style={styles.label}>Target FPS</label>
          <input
            id="cam-fps"
            type="number"
            value={fps}
            onChange={(e) => setFps(Number(e.target.value))}
            min={1}
            max={120}
            style={styles.input}
            required
          />
        </div>
      </div>

      <div style={styles.btnRow}>
        <Button variant="primary" type="submit" isLoading={isLoading} style={styles.submitBtn}>
          {isEdit ? 'Save Camera Details' : 'Register Stream Endpoint'}
        </Button>
      </div>
    </form>
  );
}

const styles: Record<string, React.CSSProperties> = {
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  label: {
    fontSize: '13px',
    color: 'var(--color-text-secondary)',
    fontWeight: 600,
    fontFamily: 'var(--font-heading)',
    textTransform: 'uppercase',
  },
  input: {
    padding: '12px 16px',
    backgroundColor: 'rgba(15, 23, 42, 0.4)', // transparent dark
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--color-text)',
    fontSize: '14px',
    fontFamily: 'var(--font-body)',
    outline: 'none',
    transition: 'border-color 150ms ease',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '16px',
  },
  error: {
    padding: '12px 16px',
    backgroundColor: 'var(--color-danger-bg)',
    color: 'var(--color-danger)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    borderRadius: 'var(--radius-md)',
    fontSize: '13px',
    fontWeight: 500,
  },
  btnRow: {
    marginTop: '8px',
    display: 'flex',
    justifyContent: 'flex-end',
  },
  submitBtn: {
    width: '100%',
  },
};
