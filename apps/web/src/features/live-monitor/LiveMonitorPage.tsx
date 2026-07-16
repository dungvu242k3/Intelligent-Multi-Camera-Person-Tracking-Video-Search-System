import { useEffect, useState } from 'react';
import { Tv, Radio, AlertTriangle } from 'lucide-react';
import axiosInstance from '../../shared/utils/axiosInstance.ts';
import { useWebSocket } from '../../shared/hooks/useWebSocket.ts';
import CameraGrid from './components/CameraGrid.tsx';
import Button from '../../shared/components/common/Button.tsx';

interface Camera {
  id: string;
  name: string;
  rtsp_url: string;
  location: string;
  status: string;
  fps: number;
}

interface LiveAlertLog {
  id: string;
  camera_id: string;
  camera_name: string;
  event_type: string;
  timestamp: string;
  message: string;
}

export default function LiveMonitorPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [layoutSize, setLayoutSize] = useState<1 | 2 | 3>(2); // Default to 2x2 grid
  const [activeAlerts, setActiveAlerts] = useState<string[]>([]);
  const [alertLogs, setAlertLogs] = useState<LiveAlertLog[]>([]);

  useEffect(() => {
    const fetchCameras = async () => {
      try {
        const res = await axiosInstance.get<Camera[]>('/cameras');
        setCameras(res.data.filter(c => c.status?.toLowerCase() === 'online'));
      } catch (err) {
        console.error('Failed to fetch cameras:', err);
      }
    };
    void fetchCameras();
  }, []);

  // Hook WebSocket to receive live telemetry matching & safety alert alarms
  useWebSocket({
    onMessage: (payload: any) => {
      if (!payload) return;

      const eventType = payload.event_type;
      const data = payload.data || {};
      const cameraId = data.camera_id;

      if (!cameraId) return;

      const cameraName = cameras.find(c => c.id === cameraId)?.name || 'Unknown Node';

      if (eventType === 'fire_alarm' || eventType === 'fire') {
        // Trigger active visual overlay state on grid
        setActiveAlerts((prev) => prev.includes(cameraId) ? prev : [...prev, cameraId]);

        // Add log entry
        const newLog: LiveAlertLog = {
          id: data.alert_id || `fire-${Date.now()}`,
          camera_id: cameraId,
          camera_name: cameraName,
          event_type: 'fire',
          timestamp: new Date().toLocaleTimeString(),
          message: 'CRITICAL: Fire/Smoke signature detected on GPU pipelines!',
        };
        setAlertLogs((prev) => [newLog, ...prev.slice(0, 49)]);
      } else if (eventType === 'tracking_match') {
        const newLog: LiveAlertLog = {
          id: data.event_id || `match-${Date.now()}`,
          camera_id: cameraId,
          camera_name: cameraName,
          event_type: 'match',
          timestamp: new Date().toLocaleTimeString(),
          message: `Cross-Camera Track Match: Person #${data.person_uuid?.substring(0, 6)} matched (${Math.round(data.confidence * 100)}% conf).`,
        };
        setAlertLogs((prev) => [newLog, ...prev.slice(0, 49)]);
      }
    },
  });

  const clearAlarms = () => {
    setActiveAlerts([]);
    setAlertLogs([]);
  };

  return (
    <div style={styles.page}>
      <div style={styles.splitLayout}>
        {/* Left main: Grid Player panel */}
        <div style={styles.mainPanel}>
          {/* Header block */}
          <div style={styles.header}>
            <div style={styles.titleBlock}>
              <Tv size={26} color="var(--color-primary)" />
              <div>
                <h1 style={styles.title}>Live Control Room</h1>
                <p style={styles.subtitle}>
                  Multi-Camera grid tracking feed. Displays YOLO bounding boxes and matches ReID vectors.
                </p>
              </div>
            </div>

            {/* Layout grid configuration controls */}
            <div style={styles.controlRow}>
              <div style={styles.layoutToggle}>
                <button
                  type="button"
                  onClick={() => setLayoutSize(1)}
                  style={{
                    ...styles.toggleBtn,
                    backgroundColor: layoutSize === 1 ? 'var(--color-border)' : 'transparent',
                    color: layoutSize === 1 ? 'var(--color-text)' : 'var(--color-text-secondary)',
                  }}
                  title="Single Screen Feed"
                >
                  1x1
                </button>
                <button
                  type="button"
                  onClick={() => setLayoutSize(2)}
                  style={{
                    ...styles.toggleBtn,
                    backgroundColor: layoutSize === 2 ? 'var(--color-border)' : 'transparent',
                    color: layoutSize === 2 ? 'var(--color-text)' : 'var(--color-text-secondary)',
                  }}
                  title="Quad Screen Feed"
                >
                  2x2
                </button>
                <button
                  type="button"
                  onClick={() => setLayoutSize(3)}
                  style={{
                    ...styles.toggleBtn,
                    backgroundColor: layoutSize === 3 ? 'var(--color-border)' : 'transparent',
                    color: layoutSize === 3 ? 'var(--color-text)' : 'var(--color-text-secondary)',
                  }}
                  title="Control Room Grid"
                >
                  3x3
                </button>
              </div>

              {activeAlerts.length > 0 && (
                <Button variant="danger" onClick={clearAlarms}>
                  Clear Active Alarms ({activeAlerts.length})
                </Button>
              )}
            </div>
          </div>

          {/* Grid display */}
          <CameraGrid
            cameras={cameras}
            layoutSize={layoutSize}
            activeAlerts={activeAlerts}
          />
        </div>

        {/* Right column: live side feed logs */}
        <div className="card" style={styles.sidebar}>
          <div style={styles.sidebarHeader}>
            <Radio size={16} color="var(--color-danger)" className="pulse-red-glow" />
            <h3 style={styles.sidebarTitle}>Security Event Console</h3>
          </div>

          <div style={styles.logsList}>
            {alertLogs.length === 0 && (
              <div style={styles.emptyLogs}>
                Console connected. Awaiting telemetry matching events from downstream inference engines...
              </div>
            )}

            {alertLogs.map((log) => {
              const isFire = log.event_type === 'fire';
              return (
                <div
                  key={log.id}
                  style={{
                    ...styles.logItem,
                    borderColor: isFire ? 'var(--color-danger)' : 'var(--color-border)',
                    backgroundColor: isFire ? 'rgba(239, 68, 68, 0.03)' : 'transparent',
                  }}
                >
                  <div style={styles.logHeader}>
                    <div style={styles.logCategory}>
                      {isFire ? (
                        <AlertTriangle size={12} color="var(--color-danger)" />
                      ) : (
                        <Tv size={12} color="var(--color-secondary)" />
                      )}
                      <span
                        style={{
                          ...styles.logCategoryText,
                          color: isFire ? 'var(--color-danger)' : 'var(--color-secondary)',
                        }}
                      >
                        {isFire ? 'Safety Alert' : 'ReID Match'}
                      </span>
                    </div>
                    <span style={styles.logTime}>{log.timestamp}</span>
                  </div>
                  <p style={styles.logMsg}>{log.message}</p>
                  <div style={styles.logFooter}>
                    <span>Cam: {log.camera_name}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    padding: '24px',
  },
  splitLayout: {
    display: 'grid',
    gridTemplateColumns: '1fr 320px',
    gap: '24px',
    alignItems: 'start',
  },
  mainPanel: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: '16px',
  },
  titleBlock: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  title: {
    fontSize: '22px',
    color: 'var(--color-text)',
    fontFamily: 'var(--font-heading)',
  },
  subtitle: {
    fontSize: '13px',
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-body)',
    marginTop: '4px',
  },
  controlRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  layoutToggle: {
    display: 'inline-flex',
    backgroundColor: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    padding: '2px',
  },
  toggleBtn: {
    padding: '6px 12px',
    border: 'none',
    borderRadius: 'var(--radius-sm)',
    fontSize: '12px',
    fontWeight: 600,
    fontFamily: 'var(--font-heading)',
    cursor: 'pointer',
    transition: 'all 150ms ease',
  },
  sidebar: {
    padding: 0,
    height: 'calc(100vh - 120px)',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  sidebarHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '16px 20px',
    borderBottom: '1px solid var(--color-border)',
    backgroundColor: 'rgba(30, 41, 59, 0.4)',
  },
  sidebarTitle: {
    fontSize: '14px',
    color: 'var(--color-text)',
    fontFamily: 'var(--font-heading)',
  },
  logsList: {
    flex: 1,
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    padding: '16px',
  },
  emptyLogs: {
    padding: '32px 16px',
    textAlign: 'center',
    color: 'var(--color-text-secondary)',
    fontSize: '12px',
    lineHeight: 1.5,
  },
  logItem: {
    borderLeft: '3px solid',
    padding: '12px',
    borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
    backgroundColor: 'rgba(255, 255, 255, 0.01)',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    boxShadow: 'var(--shadow-sm)',
  },
  logHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logCategory: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  logCategoryText: {
    fontSize: '10px',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    fontFamily: 'var(--font-heading)',
  },
  logTime: {
    fontSize: '10px',
    fontFamily: 'var(--font-heading)',
    color: 'var(--color-text-secondary)',
  },
  logMsg: {
    fontSize: '12px',
    color: 'var(--color-text)',
    lineHeight: 1.4,
  },
  logFooter: {
    fontSize: '10px',
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-body)',
  },
};
