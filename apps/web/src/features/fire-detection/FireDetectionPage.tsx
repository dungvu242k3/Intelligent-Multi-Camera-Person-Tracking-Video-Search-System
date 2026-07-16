import React, { useState, useEffect } from 'react';
import { Flame, Sparkles } from 'lucide-react';
import CameraMap from './components/CameraMap.tsx';
import FireHistorySidebar from './components/FireHistorySidebar.tsx';

interface CameraNode {
  id: string;
  name: string;
  x: number;
  y: number;
}

interface FireEvent {
  id: string;
  camera_id: string;
  camera_name: string;
  timestamp: string;
  severity: 'CRITICAL' | 'WARNING' | 'RESOLVED';
}

export default function FireDetectionPage() {
  // Configured facility cameras list
  const cameras: CameraNode[] = [
    { id: 'cam_1', name: 'Main Lobby Entrance', x: 150, y: 220 },
    { id: 'cam_2', name: 'Loading Dock A', x: 420, y: 150 },
    { id: 'cam_3', name: 'Zone B Aisle 5', x: 420, y: 320 },
    { id: 'cam_4', name: 'HQ Server Room', x: 670, y: 220 },
  ];

  const [activeFires, setActiveFires] = useState<string[]>([]);
  const [events, setEvents] = useState<FireEvent[]>([]);

  // Connect to Gateway WebSockets for real-time alerts
  useEffect(() => {
    const wsUrl = 'ws://localhost:8000/ws';
    logger.info(`Opening WebSocket alert channel link: ${wsUrl}`);
    const socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        logger.info("Realtime alert packet consumed via WebSocket:", payload);
        
        // Match specific fire alarm events broadcasted from API Gateway
        if (payload.event_type === 'fire_alarm' || payload.event_type === 'fire') {
          const alertData = payload.data || {};
          const camId = alertData.camera_id || 'cam_2';
          const camName = cameras.find(c => c.id === camId)?.name || 'Unknown Zone';
          
          const newEvent: FireEvent = {
            id: alertData.alert_id || `alarm-${Date.now()}`,
            camera_id: camId,
            camera_name: camName,
            timestamp: new Date().toLocaleTimeString(),
            severity: alertData.severity || 'CRITICAL'
          };

          // Append to log and update map highlights
          setEvents(prev => [newEvent, ...prev]);
          setActiveFires(prev => prev.includes(camId) ? prev : [...prev, camId]);
        }
      } catch (e) {
        logger.warning("Error parsing WebSocket event data stream payload:", e);
      }
    };

    socket.onclose = () => {
      logger.warning("WebSocket alert channel connection closed.");
    };

    return () => {
      socket.close();
    };
  }, []);

  const triggerMockAlarm = (cameraId: string) => {
    const targetCam = cameras.find(c => c.id === cameraId);
    if (!targetCam) return;

    logger.info(`Simulating fire alert for camera: ${targetCam.name}`);
    const newId = `alarm-${Date.now()}`;
    const newEvent: FireEvent = {
      id: newId,
      camera_id: cameraId,
      camera_name: targetCam.name,
      timestamp: new Date().toLocaleTimeString(),
      severity: 'CRITICAL',
    };

    // Update state to render UI changes immediately
    setEvents((prev) => [newEvent, ...prev]);
    setActiveFires((prev) => prev.includes(cameraId) ? prev : [...prev, cameraId]);
  };

  const handleResolveEvent = (id: string) => {
    setEvents((prev) => 
      prev.map((e) => e.id === id ? { ...e, severity: 'RESOLVED' as const } : e)
    );
    
    // Check if there are other active alerts remaining for this camera
    const resolvedEvent = events.find(e => e.id === id);
    if (resolvedEvent) {
      const remainingAlertsForCam = events.filter(
        e => e.camera_id === resolvedEvent.camera_id && e.id !== id && e.severity !== 'RESOLVED'
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
              <h1 style={styles.title}>Fire Surveillance Center</h1>
            </div>
            <p style={styles.subtitle}>
              Monitor real-time visual alerts and smoke signatures. Red blinking markers represent localized fire incidents.
            </p>
          </div>

          {/* Map Section */}
          <CameraMap 
            cameras={cameras} 
            activeFires={activeFires} 
            onCameraSelect={(id) => triggerMockAlarm(id)} 
          />

          {/* Dev Sim Controllers */}
          <div className="card" style={styles.devCard}>
            <div style={styles.devHeading}>
              <Sparkles size={16} color="var(--color-primary)" />
              <span style={{ fontSize: '13px', fontWeight: 600 }}>Developer Simulation Controls</span>
            </div>
            <div style={styles.btnRow}>
              <button 
                type="button" 
                onClick={() => triggerMockAlarm('cam_2')}
                className="btn-primary" 
                style={styles.simBtn}
              >
                Trigger Fire (Loading Dock A)
              </button>
              <button 
                type="button" 
                onClick={() => triggerMockAlarm('cam_4')}
                className="btn-primary" 
                style={styles.simBtn}
              >
                Trigger Fire (Server Room)
              </button>
              <button 
                type="button" 
                onClick={clearAllAlarms}
                className="btn-secondary" 
                style={styles.clearBtn}
              >
                Clear All Alarms
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
  info: (msg: string, details?: any) => console.log(`[INFO] ${msg}`, details || ''),
  warning: (msg: string, details?: any) => console.warn(`[WARN] ${msg}`, details || '')
};

const styles: Record<string, React.CSSProperties> = {
  page: {
    width: '100%',
  },
  contentLayout: {
    display: 'flex',
    paddingRight: '320px', /* Sidebar offset */
  },
  mainPanel: {
    flex: 1,
    padding: '24px 32px',
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
    maxWidth: '900px',
    margin: '0 auto',
  },
  titleBlock: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    alignItems: 'flex-start',
  },
  titleGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  title: {
    fontSize: '22px',
    color: 'var(--color-text)',
  },
  subtitle: {
    fontSize: '14px',
    color: 'var(--color-text-secondary)',
    maxWidth: '800px',
    textAlign: 'left',
  },
  devCard: {
    padding: '16px 20px',
    backgroundColor: 'rgba(30, 41, 59, 0.2)',
    borderStyle: 'dashed',
  },
  devHeading: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '12px',
    color: 'var(--color-text-secondary)',
  },
  btnRow: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap',
  },
  simBtn: {
    padding: '8px 16px',
    fontSize: '12px',
  },
  clearBtn: {
    padding: '6px 14px',
    fontSize: '12px',
  },
};
