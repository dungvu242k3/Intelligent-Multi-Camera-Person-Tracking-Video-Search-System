import { useEffect, useRef, useState } from 'react';
import { Camera, VolumeX, Volume2, Maximize2 } from 'lucide-react';

interface CameraPlayerProps {
  id: string;
  name: string;
  rtspUrl: string;
  isAlertActive?: boolean;
  onAlertResolve?: () => void;
}

interface SimulatedBox {
  id: string;
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
  dx: number;
  dy: number;
  color: string;
}

export default function CameraPlayer({
  name,
  rtspUrl,
  isAlertActive = false,
}: CameraPlayerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isMuted, setIsMuted] = useState(true);
  const [fps] = useState(30);

  // Generate simulated moving targets inside camera canvas
  const boxesRef = useRef<SimulatedBox[]>([
    {
      id: '1',
      label: 'Person #105',
      x: 100,
      y: 120,
      w: 60,
      h: 120,
      dx: 1.5,
      dy: 0.5,
      color: '#3B82F6',
    },
    {
      id: '2',
      label: 'Person #110',
      x: 350,
      y: 200,
      w: 50,
      h: 110,
      dx: -1.2,
      dy: 0.8,
      color: '#10B981',
    },
  ]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;

    const render = () => {
      // Draw simulated camera viewport background
      ctx.fillStyle = '#0F172A'; // Slate 900 base
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Grid background effect representing scanner overlay
      ctx.strokeStyle = 'rgba(51, 65, 85, 0.15)';
      ctx.lineWidth = 1;
      const gridSize = 40;
      for (let x = 0; x < canvas.width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      // Draw camera info text in upper-left corner
      ctx.fillStyle = 'rgba(241, 245, 249, 0.4)';
      ctx.font = '11px monospace';
      ctx.fillText(`STREAM: ${rtspUrl}`, 16, 26);
      ctx.fillText(`DECODER: nvv4l2decoder (Hardware)`, 16, 42);

      // Draw camera status
      ctx.fillStyle = '#10B981';
      ctx.fillRect(16, 54, 8, 8);
      ctx.fillStyle = 'rgba(241, 245, 249, 0.4)';
      ctx.fillText('LIVE', 30, 62);

      // Update and draw simulated boxes
      boxesRef.current.forEach((box) => {
        // Move bounding box
        box.x += box.dx;
        box.y += box.dy;

        // Bounce box coords off boundaries
        if (box.x <= 20 || box.x + box.w >= canvas.width - 20) {
          box.dx *= -1;
        }
        if (box.y <= 60 || box.y + box.h >= canvas.height - 20) {
          box.dy *= -1;
        }

        // Draw bounding box border
        ctx.strokeStyle = isAlertActive ? 'var(--color-danger)' : box.color;
        ctx.lineWidth = 2;
        ctx.strokeRect(box.x, box.y, box.w, box.h);

        // Draw background container label header
        ctx.fillStyle = isAlertActive ? 'var(--color-danger)' : box.color;
        ctx.fillRect(box.x, box.y - 20, box.w, 20);

        // Draw label text
        ctx.fillStyle = 'white';
        ctx.font = '10px sans-serif';
        ctx.fillText(box.label, box.x + 6, box.y - 6);
      });

      // Special overlay indicator for critical alarms (Fire detection simulation)
      if (isAlertActive) {
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.8)';
        ctx.lineWidth = 6;
        ctx.strokeRect(0, 0, canvas.width, canvas.height);

        // Draw alert warning box
        ctx.fillStyle = 'rgba(239, 68, 68, 0.85)';
        ctx.fillRect(canvas.width / 2 - 120, canvas.height / 2 - 25, 240, 50);

        ctx.fillStyle = 'white';
        ctx.font = 'bold 12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('CRITICAL: ALARM ACTIVE', canvas.width / 2, canvas.height / 2 + 5);
        ctx.textAlign = 'left'; // reset text alignment
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [rtspUrl, isAlertActive]);

  return (
    <div
      className="card"
      style={{
        ...styles.container,
        border: isAlertActive ? '2px solid var(--color-danger)' : '1px solid var(--color-border)',
        boxShadow: isAlertActive ? '0 0 15px rgba(239, 68, 68, 0.4)' : 'var(--shadow-md)',
      }}
    >
      {/* Header bar */}
      <div style={styles.header}>
        <div style={styles.nameBlock}>
          <Camera size={14} color="var(--color-primary)" />
          <span style={styles.name}>{name}</span>
        </div>
        <div style={styles.actions}>
          <button
            type="button"
            onClick={() => setIsMuted(!isMuted)}
            style={styles.actionBtn}
            title={isMuted ? 'Unmute Audio' : 'Mute Audio'}
          >
            {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
          </button>
          <button type="button" style={styles.actionBtn} title="Maximize Feed">
            <Maximize2 size={14} />
          </button>
        </div>
      </div>

      {/* Render Canvas Stream */}
      <div style={styles.playerArea}>
        <canvas ref={canvasRef} width={640} height={360} style={styles.canvas} />

        {/* Floating Tracking statistics labels overlay */}
        <div style={styles.statsOverlay}>
          <div style={styles.statLabel}>FPS: {fps}</div>
          <div style={styles.statLabel}>BBOX: {boxesRef.current.length}</div>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    padding: 0,
    backgroundColor: 'var(--color-surface)',
    position: 'relative',
    transition: 'all 200ms ease',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '10px 16px',
    backgroundColor: 'rgba(30, 41, 59, 0.6)',
    borderBottom: '1px solid var(--color-border)',
  },
  nameBlock: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  name: {
    fontSize: '13px',
    fontWeight: 600,
    color: 'var(--color-text)',
  },
  actions: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  actionBtn: {
    background: 'none',
    border: 'none',
    color: 'var(--color-text-secondary)',
    cursor: 'pointer',
    padding: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 'var(--radius-sm)',
    transition: 'color 150ms ease',
  },
  playerArea: {
    position: 'relative',
    width: '100%',
    aspectRatio: '16/9',
  },
  canvas: {
    width: '100%',
    height: '100%',
    display: 'block',
  },
  statsOverlay: {
    position: 'absolute',
    bottom: '12px',
    right: '12px',
    display: 'flex',
    gap: '8px',
    pointerEvents: 'none',
  },
  statLabel: {
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-heading)',
    fontSize: '10px',
    padding: '4px 8px',
    borderRadius: 'var(--radius-sm)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
  },
};
