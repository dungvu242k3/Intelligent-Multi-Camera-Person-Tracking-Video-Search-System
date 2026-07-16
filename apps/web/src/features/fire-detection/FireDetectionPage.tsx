import { useCallback, useState } from 'react';
import { Flame, Sparkles } from 'lucide-react';
import { useTranslation } from '../../shared/hooks/useTranslation.ts';
import { useWebSocket } from '../../shared/hooks/useWebSocket.ts';
import { CameraNode, FireEvent, FireSeverity } from '../../shared/types/fireDetection.ts';
import CameraMap from './components/CameraMap.tsx';
import FireHistorySidebar from './components/FireHistorySidebar.tsx';
import { fireDetectionPageStyles as styles } from './FireDetectionPage.styles.ts';

interface FireAlertPayload {
  event_type?: string;
  data?: {
    alert_id?: string;
    camera_id?: string;
    severity?: FireSeverity;
  };
}

const FACILITY_CAMERAS: CameraNode[] = [
  { id: 'cam_1', name: 'Main Lobby Entrance', x: 150, y: 220 },
  { id: 'cam_2', name: 'Loading Dock A', x: 420, y: 150 },
  { id: 'cam_3', name: 'Zone B Aisle 5', x: 420, y: 320 },
  { id: 'cam_4', name: 'HQ Server Room', x: 670, y: 220 },
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function toFireAlertPayload(payload: unknown): FireAlertPayload | null {
  if (!isRecord(payload)) {
    return null;
  }

  const data = isRecord(payload.data) ? payload.data : {};
  return {
    event_type: typeof payload.event_type === 'string' ? payload.event_type : undefined,
    data: {
      alert_id: typeof data.alert_id === 'string' ? data.alert_id : undefined,
      camera_id: typeof data.camera_id === 'string' ? data.camera_id : undefined,
      severity:
        data.severity === FireSeverity.Critical ||
        data.severity === FireSeverity.Warning ||
        data.severity === FireSeverity.Resolved
          ? data.severity
          : undefined,
    },
  };
}

export default function FireDetectionPage() {
  const { t } = useTranslation();

  const [activeFires, setActiveFires] = useState<string[]>([]);
  const [events, setEvents] = useState<FireEvent[]>([]);

  const handleRealtimeMessage = useCallback((payload: unknown) => {
    const alertPayload = toFireAlertPayload(payload);

    if (!alertPayload || (alertPayload.event_type !== 'fire_alarm' && alertPayload.event_type !== 'fire')) {
      return;
    }

    logger.info('Realtime alert packet consumed via WebSocket:', alertPayload);

    const camId = alertPayload.data?.camera_id || 'cam_2';
    const camName = FACILITY_CAMERAS.find((camera) => camera.id === camId)?.name || 'Unknown Zone';

    const newEvent: FireEvent = {
      id: alertPayload.data?.alert_id || `alarm-${Date.now()}`,
      camera_id: camId,
      camera_name: camName,
      timestamp: new Date().toLocaleTimeString(),
      severity: alertPayload.data?.severity || FireSeverity.Critical,
    };

    setEvents((prev) => [newEvent, ...prev]);
    setActiveFires((prev) => (prev.includes(camId) ? prev : [...prev, camId]));
  }, []);

  useWebSocket({ onMessage: handleRealtimeMessage });

  const triggerMockAlarm = (cameraId: string) => {
    const targetCam = FACILITY_CAMERAS.find(c => c.id === cameraId);
    if (!targetCam) return;

    logger.info(`Simulating fire alert for camera: ${targetCam.name}`);
    const newId = `alarm-${Date.now()}`;
    const newEvent: FireEvent = {
      id: newId,
      camera_id: cameraId,
      camera_name: targetCam.name,
      timestamp: new Date().toLocaleTimeString(),
      severity: FireSeverity.Critical,
    };

    // Update state to render UI changes immediately
    setEvents((prev) => [newEvent, ...prev]);
    setActiveFires((prev) => prev.includes(cameraId) ? prev : [...prev, cameraId]);
  };

  const handleResolveEvent = (id: string) => {
    setEvents((prev) => 
      prev.map((e) => e.id === id ? { ...e, severity: FireSeverity.Resolved } : e)
    );
    
    // Check if there are other active alerts remaining for this camera
    const resolvedEvent = events.find(e => e.id === id);
    if (resolvedEvent) {
      const remainingAlertsForCam = events.filter(
        e => e.camera_id === resolvedEvent.camera_id && e.id !== id && e.severity !== FireSeverity.Resolved
      );
      if (remainingAlertsForCam.length === 0) {
        setActiveFires((prev) => prev.filter(cId => cId !== resolvedEvent.camera_id));
      }
    }
  };

  const clearAllAlarms = () => {
    setActiveFires([]);
    setEvents([]);
  };

  return (
    <div style={styles.page}>
      {/* Shift page layout by Sidebar & Header margins */}
      <div style={styles.contentLayout}>
        <div style={styles.mainPanel}>
          {/* Header block */}
          <div style={styles.titleBlock}>
            <div style={styles.titleGroup}>
              <Flame size={28} color="var(--color-danger)" className="pulse-red-glow" />
              <h1 style={styles.title}>{t('fire.title')}</h1>
            </div>
            <p style={styles.subtitle}>
              {t('fire.subtitle')}
            </p>
          </div>

          {/* Map Section */}
          <CameraMap 
            cameras={FACILITY_CAMERAS} 
            activeFires={activeFires} 
            onCameraSelect={(id) => triggerMockAlarm(id)} 
          />

          {/* Dev Sim Controllers */}
          <div className="card" style={styles.devCard}>
            <div style={styles.devHeading}>
              <Sparkles size={16} color="var(--color-primary)" />
              <span style={styles.devHeadingText}>{t('fire.devControls')}</span>
            </div>
            <div style={styles.btnRow}>
              <button 
                type="button" 
                onClick={() => triggerMockAlarm('cam_2')}
                className="btn-primary" 
                style={styles.simBtn}
              >
                {t('fire.btnTriggerDock')}
              </button>
              <button 
                type="button" 
                onClick={() => triggerMockAlarm('cam_4')}
                className="btn-primary" 
                style={styles.simBtn}
              >
                {t('fire.btnTriggerServer')}
              </button>
              <button 
                type="button" 
                onClick={clearAllAlarms}
                className="btn-secondary" 
                style={styles.clearBtn}
              >
                {t('fire.btnClear')}
              </button>
            </div>
          </div>
        </div>

        {/* Realtime Alert Feed Sidebar */}
        <FireHistorySidebar 
          events={events} 
          onResolveEvent={handleResolveEvent} 
        />
      </div>
    </div>
  );
}

// Logger utility wrapper for react scope
const logger = {
  info: (msg: string, details?: unknown) => console.log(`[INFO] ${msg}`, details || ''),
  warning: (msg: string, details?: unknown) => console.warn(`[WARN] ${msg}`, details || '')
};
