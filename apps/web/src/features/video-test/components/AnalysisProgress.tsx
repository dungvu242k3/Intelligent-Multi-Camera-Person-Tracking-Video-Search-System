import React from 'react';
import { User, Flame, Package, Gauge, RefreshCw } from 'lucide-react';

interface AnalysisProgressProps {
  statusText: string;
  progressPercent: number;
  stats: {
    persons: number;
    fires: number;
    objects: number;
    fps: number;
  };
}

export default function AnalysisProgress({ statusText, progressPercent, stats }: AnalysisProgressProps) {
  return (
    <div style={styles.container}>
      {/* Progress Info Header */}
      <div style={styles.header}>
        <div style={styles.statusGroup}>
          <RefreshCw size={18} className="pulse-red-glow" color="var(--color-primary)" style={styles.spinner} />
          <span style={styles.statusText}>{statusText}</span>
        </div>
        <span style={styles.percentText}>{progressPercent}%</span>
      </div>

      {/* Progress Bar */}
      <div style={styles.progressBarBg}>
        <div 
          style={{
            ...styles.progressBarFill,
            width: `${progressPercent}%`
          }}
        ></div>
      </div>

      {/* Real-time Counters Grid */}
      <div style={styles.grid}>
        {/* Persons Count */}
        <div style={styles.card}>
          <User size={24} color="#3B82F6" />
          <div style={styles.cardData}>
            <div style={styles.cardVal}>{stats.persons}</div>
            <div style={styles.cardLabel}>Persons Detected</div>
          </div>
        </div>

        {/* Fires Count */}
        <div style={{
          ...styles.card,
          borderColor: stats.fires > 0 ? 'var(--color-danger)' : 'var(--color-border)',
          backgroundColor: stats.fires > 0 ? 'rgba(239, 68, 68, 0.05)' : 'var(--color-surface)',
        }}>
          <Flame size={24} color={stats.fires > 0 ? 'var(--color-danger)' : 'var(--color-text-secondary)'} />
          <div style={styles.cardData}>
            <div style={{
              ...styles.cardVal,
              color: stats.fires > 0 ? 'var(--color-danger)' : 'var(--color-text)'
            }}>{stats.fires}</div>
            <div style={styles.cardLabel}>Fire Incidents</div>
          </div>
        </div>

        {/* Objects Count */}
        <div style={styles.card}>
          <Package size={24} color="#F59E0B" />
          <div style={styles.cardData}>
            <div style={styles.cardVal}>{stats.objects}</div>
            <div style={styles.cardLabel}>Objects Detected</div>
          </div>
        </div>

        {/* Processing Speed */}
        <div style={styles.card}>
          <Gauge size={24} color="#10B981" />
          <div style={styles.cardData}>
            <div style={styles.cardVal}>{stats.fps.toFixed(1)}</div>
            <div style={styles.cardLabel}>Inference (FPS)</div>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    padding: '16px 0',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statusGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  spinner: {
    animation: 'spin 2s linear infinite',
  },
  statusText: {
    fontSize: '15px',
    fontWeight: 600,
    color: 'var(--color-text)',
  },
  percentText: {
    fontSize: '18px',
    fontFamily: 'var(--font-heading)',
    fontWeight: 700,
    color: 'var(--color-primary)',
  },
  progressBarBg: {
    width: '100%',
    height: '10px',
    backgroundColor: 'var(--color-border)',
    borderRadius: 'var(--radius-xl)',
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: 'var(--color-primary)',
    borderRadius: 'var(--radius-xl)',
    boxShadow: '0 0 10px rgba(59, 130, 246, 0.5)',
    transition: 'width 250ms ease-out',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginTop: '10px',
  },
  card: {
    backgroundColor: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    padding: '20px 16px',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    boxShadow: 'var(--shadow-sm)',
    transition: 'border-color 150ms ease',
  },
  cardData: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-start',
  },
  cardVal: {
    fontSize: '24px',
    fontFamily: 'var(--font-heading)',
    fontWeight: 700,
    lineHeight: 1.1,
  },
  cardLabel: {
    fontSize: '12px',
    color: 'var(--color-text-secondary)',
    marginTop: '4px',
    fontWeight: 500,
  },
};
