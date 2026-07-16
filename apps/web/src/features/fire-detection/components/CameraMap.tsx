import React from 'react';
import { Camera } from 'lucide-react';

interface CameraNode {
  id: string;
  name: string;
  x: number;
  y: number;
}

interface CameraMapProps {
  cameras: CameraNode[];
  activeFires: string[]; // List of camera IDs with active fire events
  onCameraSelect: (id: string) => void;
}

export default function CameraMap({ cameras, activeFires, onCameraSelect }: CameraMapProps) {
  return (
    <div style={styles.mapCard} className="card">
      <div style={styles.mapHeader}>
        <div style={styles.titleGroup}>
          <Camera size={20} color="var(--color-primary)" />
          <h3 style={styles.title}>Facility Interactive Floor Map</h3>
        </div>
        <div style={styles.legend}>
          <div style={styles.legendItem}>
            <div style={styles.legendDotNormal}></div>
            <span style={styles.legendText}>Nominal</span>
          </div>
          <div style={styles.legendItem}>
            <div style={styles.legendDotFire} className="pulse-red-glow"></div>
            <span style={styles.legendText}>Active Fire</span>
          </div>
        </div>
      </div>

      {/* SVG Layout Mapping */}
      <div style={styles.svgWrapper}>
        <svg 
          viewBox="0 0 800 450" 
          width="100%" 
          height="100%" 
          style={styles.svg}
        >
          {/* Grid Background */}
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="1" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Building Walls representation */}
          {/* Outer Boundary */}
          <rect x="20" y="20" width="760" height="410" fill="none" stroke="var(--color-border)" strokeWidth="3" rx="8" />
          
          {/* Office section divider */}
          <line x1="280" y1="20" x2="280" y2="430" stroke="var(--color-border)" strokeWidth="2" strokeDasharray="5,5" />
          {/* Main Warehouse section divider */}
          <line x1="560" y1="20" x2="560" y2="430" stroke="var(--color-border)" strokeWidth="2" strokeDasharray="5,5" />
          
          {/* Area Labels */}
          <text x="150" y="50" fill="var(--color-text-secondary)" fontSize="14" fontFamily="var(--font-heading)" textAnchor="middle">ZONE A: OFFICES</text>
          <text x="420" y="50" fill="var(--color-text-secondary)" fontSize="14" fontFamily="var(--font-heading)" textAnchor="middle">ZONE B: LOADING BAY</text>
          <text x="670" y="50" fill="var(--color-text-secondary)" fontSize="14" fontFamily="var(--font-heading)" textAnchor="middle">ZONE C: SERVER ROOM</text>

          {/* Camera Nodes */}
          {cameras.map((cam) => {
            const hasFire = activeFires.includes(cam.id);
            return (
              <g 
                key={cam.id} 
                style={{ cursor: 'pointer' }}
                onClick={() => onCameraSelect(cam.id)}
              >
                {/* Glowing alert outer circle if active fire */}
                {hasFire && (
                  <circle 
                    cx={cam.x} 
                    cy={cam.y} 
                    r="24" 
                    fill="rgba(239, 68, 68, 0.2)"
                    stroke="var(--color-danger)" 
                    strokeWidth="2"
                    className="pulse-red-glow"
                  />
                )}
                
                {/* Camera Pin circle */}
                <circle 
                  cx={cam.x} 
                  cy={cam.y} 
                  r="14" 
                  fill={hasFire ? 'var(--color-danger)' : 'var(--color-surface)'} 
                  stroke={hasFire ? 'white' : 'var(--color-primary)'}
                  strokeWidth="2"
                  style={{ transition: 'fill 200ms ease' }}
                />

                {/* Camera Number label */}
                <text 
                  x={cam.x} 
                  y={cam.y + 4} 
                  fill={hasFire ? 'white' : 'var(--color-text)'} 
                  fontSize="11" 
                  fontWeight="bold"
                  fontFamily="var(--font-heading)"
                  textAnchor="middle"
                >
                  C{cam.id.replace('cam_', '')}
                </text>

                {/* Bouncing Fire Warning indicator */}
                {hasFire && (
                  <g transform={`translate(${cam.x - 12}, ${cam.y - 42})`}>
                    <path 
                      d="M12 2L2 22h20L12 2z" 
                      fill="var(--color-danger)" 
                      stroke="white" 
                      strokeWidth="1.5" 
                    />
                    <path d="M12 9v5m0 3h.01" stroke="white" strokeWidth="2" strokeLinecap="round" />
                  </g>
                )}

                {/* Label text under camera */}
                <text 
                  x={cam.x} 
                  y={cam.y + 32} 
                  fill="var(--color-text-secondary)" 
                  fontSize="11" 
                  fontWeight="500"
                  textAnchor="middle"
                >
                  {cam.name}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  mapCard: {
    width: '100%',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  mapHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  titleGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  title: {
    fontSize: '16px',
    fontWeight: 600,
    color: 'var(--color-text)',
    fontFamily: 'var(--font-heading)',
  },
  legend: {
    display: 'flex',
    gap: '16px',
    alignItems: 'center',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  legendDotNormal: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    backgroundColor: 'var(--color-surface)',
    border: '2px solid var(--color-primary)',
  },
  legendDotFire: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    backgroundColor: 'var(--color-danger)',
    border: '2px solid white',
  },
  legendText: {
    fontSize: '12px',
    fontWeight: 500,
    color: 'var(--color-text-secondary)',
  },
  svgWrapper: {
    width: '100%',
    backgroundColor: '#070a13', /* Dark radar layout screen */
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--color-border)',
    overflow: 'hidden',
  },
  svg: {
    display: 'block',
  },
};
