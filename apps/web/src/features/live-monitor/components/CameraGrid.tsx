import CameraPlayer from './CameraPlayer.tsx';

export interface Camera {
  id: string;
  name: string;
  rtsp_url: string;
  location: string;
  status: string;
  fps: number;
}

interface CameraGridProps {
  cameras: Camera[];
  layoutSize: 1 | 2 | 3; // 1x1, 2x2, 3x3
  activeAlerts: string[]; // List of camera IDs that have active alarms
}

export default function CameraGrid({
  cameras,
  layoutSize,
  activeAlerts,
}: CameraGridProps) {
  const getGridTemplate = () => {
    if (layoutSize === 1) return '1fr';
    if (layoutSize === 2) return '1fr 1fr';
    return '1fr 1fr 1fr';
  };

  // Limit rendering count based on layout size
  const maxCamerasCount = layoutSize === 1 ? 1 : layoutSize === 2 ? 4 : 9;
  const visibleCameras = cameras.slice(0, maxCamerasCount);

  return (
    <div
      style={{
        ...styles.grid,
        gridTemplateColumns: getGridTemplate(),
      }}
    >
      {visibleCameras.map((camera) => (
        <CameraPlayer
          key={camera.id}
          id={camera.id}
          name={camera.name}
          rtspUrl={camera.rtsp_url}
          isAlertActive={activeAlerts.includes(camera.id)}
        />
      ))}

      {visibleCameras.length === 0 && (
        <div style={styles.empty}>
          <p>No active surveillance streams registered.</p>
          <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '8px' }}>
            Go to the Cameras page to add camera RTSP endpoints.
          </p>
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  grid: {
    display: 'grid',
    gap: '20px',
    width: '100%',
  },
  empty: {
    gridColumn: '1 / -1',
    padding: '64px 24px',
    textAlign: 'center',
    color: 'var(--color-text-secondary)',
    backgroundColor: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-lg)',
  },
};
