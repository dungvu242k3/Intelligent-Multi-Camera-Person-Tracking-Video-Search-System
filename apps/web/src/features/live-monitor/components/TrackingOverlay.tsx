import React from 'react';

interface BBox {
  left: number;
  top: number;
  width: number;
  height: number;
}

interface TrackingOverlayProps {
  label: string;
  bbox: BBox;
  confidence: number;
  color?: string;
  containerWidth: number;
  containerHeight: number;
  videoWidth?: number;
  videoHeight?: number;
}

export default function TrackingOverlay({
  label,
  bbox,
  confidence,
  color = 'var(--color-primary)',
  containerWidth,
  containerHeight,
  videoWidth = 1920,
  videoHeight = 1080,
}: TrackingOverlayProps) {
  // Scale original coordinates to browser element coordinates
  const scaleX = containerWidth / videoWidth;
  const scaleY = containerHeight / videoHeight;

  const left = bbox.left * scaleX;
  const top = bbox.top * scaleY;
  const width = bbox.width * scaleX;
  const height = bbox.height * scaleY;

  return (
    <div
      style={{
        ...styles.box,
        left: `${left}px`,
        top: `${top}px`,
        width: `${width}px`,
        height: `${height}px`,
        borderColor: color,
      }}
    >
      <div style={{ ...styles.labelContainer, backgroundColor: color }}>
        <span style={styles.labelText}>
          {label} ({Math.round(confidence * 100)}%)
        </span>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  box: {
    position: 'absolute',
    border: '2px solid',
    pointerEvents: 'none',
    boxSizing: 'border-box',
    display: 'flex',
    flexDirection: 'column',
    transition: 'all 100ms ease-out',
  },
  labelContainer: {
    position: 'absolute',
    top: '-22px',
    left: '-2px',
    padding: '2px 8px',
    borderRadius: '2px 2px 0 0',
    display: 'inline-flex',
    alignItems: 'center',
    whiteSpace: 'nowrap',
  },
  labelText: {
    color: 'white',
    fontSize: '11px',
    fontWeight: 600,
    fontFamily: 'var(--font-body)',
  },
};
