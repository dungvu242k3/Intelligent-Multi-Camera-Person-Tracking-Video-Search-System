import React from 'react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend 
} from 'recharts';
import { Download, CheckCircle, Clock, Eye, AlertTriangle } from 'lucide-react';
import { useTranslation } from '../../../shared/hooks/useTranslation.ts';

interface CropDetail {
  id: string;
  timestamp: string;
  class_name: string;
  confidence: number;
  crop_url: string;
}

interface TimelineEntry {
  second: number;
  persons: number;
  fires: number;
  objects: number;
}

interface TestResultsProps {
  summary: {
    persons: number;
    fires: number;
    objects: number;
    fps: number;
    elapsedSeconds: number;
    totalFrames: number;
  };
  timelineData: TimelineEntry[];
  crops: CropDetail[];
  onDownloadReport: () => void;
}

export default function TestResults({ summary, timelineData, crops, onDownloadReport }: TestResultsProps) {
  const { t } = useTranslation();

  return (
    <div style={styles.container}>
      {/* Success Banner */}
      <div style={styles.successBanner}>
        <CheckCircle size={24} color="var(--color-success)" />
        <div style={styles.bannerText}>
          <div style={styles.bannerHeading}>{t('vtest.results.completed')}</div>
          <div style={styles.bannerSub}>
            {t('vtest.results.processed', { 
              frames: summary.totalFrames, 
              secs: summary.elapsedSeconds.toFixed(1), 
              fps: summary.fps.toFixed(1) 
            })}
          </div>
        </div>
        <button type="button" onClick={onDownloadReport} className="btn-primary" style={styles.downloadBtn}>
          <Download size={16} />
          <span>{t('vtest.exportJson')}</span>
        </button>
      </div>

      {/* Charts Grid */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>{t('vtest.results.chartTitle')}</h3>
        <div className="card" style={styles.chartCard}>
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={timelineData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorPersons" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0}/>
                </linearGradient>
                <linearGradient id="colorFires" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#EF4444" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#EF4444" stopOpacity={0.0}/>
                </linearGradient>
                <linearGradient id="colorObjects" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="second" stroke="#94A3B8" tickFormatter={(v) => `${v}s`} />
              <YAxis stroke="#94A3B8" />
              <Tooltip 
                contentStyle={{ backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
                labelStyle={{ color: 'var(--color-text)', fontWeight: 600 }}
              />
              <Legend />
              <Area type="monotone" name="Persons" dataKey="persons" stroke="#3B82F6" fillOpacity={1} fill="url(#colorPersons)" />
              <Area type="monotone" name="Fires" dataKey="fires" stroke="#EF4444" fillOpacity={1} fill="url(#colorFires)" />
              <Area type="monotone" name="Objects" dataKey="objects" stroke="#F59E0B" fillOpacity={1} fill="url(#colorObjects)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Crops Gallery Section */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>{t('vtest.results.galleryTitle')}</h3>
        <div style={styles.cropsGrid}>
          {crops.map((crop) => (
            <div key={crop.id} style={styles.cropCard}>
              <div style={styles.imageWrapper}>
                <img 
                  src={crop.crop_url} 
                  alt={crop.class_name} 
                  style={styles.cropImg}
                  onError={(e) => {
                    // Fallback visual mock avatar placeholder if minio is down
                    e.currentTarget.src = `https://api.dicebear.com/7.x/identicon/svg?seed=${crop.id}`;
                  }}
                />
                <div style={{
                  ...styles.classBadge,
                  backgroundColor: crop.class_name === 'fire' ? 'var(--color-danger)' : 'var(--color-primary)'
                }}>
                  {crop.class_name.toUpperCase()}
                </div>
              </div>
              <div style={styles.cropMeta}>
                <div style={styles.cropTime}>
                  <Clock size={12} />
                  <span>{t('vtest.results.time')}: {crop.timestamp}</span>
                </div>
                <div style={styles.cropConf}>
                  <Eye size={12} />
                  <span>{t('vtest.results.confidence')}: {(crop.confidence * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          ))}
          {crops.length === 0 && (
            <div style={styles.emptyGallery}>
              <AlertTriangle size={28} color="var(--color-text-secondary)" />
              <span style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>{t('vtest.results.emptyGallery')}</span>
            </div>
          )}
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
    gap: '28px',
    padding: '16px 0',
  },
  successBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    backgroundColor: 'var(--color-success-bg)',
    border: '1px solid rgba(16, 185, 129, 0.2)',
    borderRadius: 'var(--radius-lg)',
    padding: '20px',
  },
  bannerText: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-start',
  },
  bannerHeading: {
    fontSize: '16px',
    fontWeight: 600,
    color: 'var(--color-success)',
  },
  bannerSub: {
    fontSize: '13px',
    color: 'var(--color-text-secondary)',
    marginTop: '4px',
  },
  downloadBtn: {
    padding: '10px 20px',
    fontSize: '13px',
  },
  section: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  sectionTitle: {
    fontSize: '16px',
    fontWeight: 600,
    color: 'var(--color-text)',
    fontFamily: 'var(--font-heading)',
  },
  chartCard: {
    padding: '24px 16px 12px 16px',
  },
  cropsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
    gap: '16px',
  },
  cropCard: {
    backgroundColor: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    overflow: 'hidden',
    boxShadow: 'var(--shadow-sm)',
    display: 'flex',
    flexDirection: 'column',
  },
  imageWrapper: {
    width: '100%',
    height: '130px',
    position: 'relative',
    backgroundColor: '#0c1017',
  },
  cropImg: {
    width: '100%',
    height: '100%',
    objectFit: 'contain',
  },
  classBadge: {
    position: 'absolute',
    bottom: '8px',
    left: '8px',
    fontSize: '10px',
    fontWeight: 700,
    color: 'white',
    padding: '4px 8px',
    borderRadius: 'var(--radius-sm)',
    fontFamily: 'var(--font-heading)',
  },
  cropMeta: {
    padding: '12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  cropTime: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '11px',
    color: 'var(--color-text-secondary)',
  },
  cropConf: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '11px',
    color: 'var(--color-text-secondary)',
  },
  emptyGallery: {
    gridColumn: '1 / -1',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '10px',
    padding: '40px',
    backgroundColor: 'var(--color-surface)',
    border: '1px dashed var(--color-border)',
    borderRadius: 'var(--radius-lg)',
  },
};
