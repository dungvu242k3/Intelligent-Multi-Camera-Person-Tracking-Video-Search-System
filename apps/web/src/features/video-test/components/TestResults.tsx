import React, { memo, useCallback } from 'react';
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
import { CropDetail, DetectionClass, TestSummary, TimelineEntry } from '../../../shared/types/videoTest.ts';
import { testResultsStyles as styles } from './TestResults.styles.ts';

interface TestResultsProps {
  summary: TestSummary;
  timelineData: TimelineEntry[];
  crops: CropDetail[];
  onDownloadReport: () => void;
}

const chartMargin = { top: 10, right: 10, left: -20, bottom: 0 };
const tooltipContentStyle = { backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' };
const tooltipLabelStyle = { color: 'var(--color-text)', fontWeight: 600 };

function TestResults({ summary, timelineData, crops, onDownloadReport }: TestResultsProps) {
  const { t } = useTranslation();
  const handleCropImageError = useCallback((event: React.SyntheticEvent<HTMLImageElement>) => {
    const seed = event.currentTarget.dataset.cropId || 'fallback';
    event.currentTarget.src = `https://api.dicebear.com/7.x/identicon/svg?seed=${seed}`;
  }, []);

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
          <Download size={16} aria-hidden="true" />
          <span>{t('vtest.exportJson')}</span>
        </button>
      </div>

      {/* Charts Grid */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>{t('vtest.results.chartTitle')}</h3>
        <div className="card" style={styles.chartCard}>
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={timelineData} margin={chartMargin}>
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
                contentStyle={tooltipContentStyle}
                labelStyle={tooltipLabelStyle}
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
                  data-crop-id={crop.id}
                  onError={handleCropImageError}
                />
                <div style={{
                  ...styles.classBadge,
                  backgroundColor: crop.class_name === DetectionClass.Fire ? 'var(--color-danger)' : 'var(--color-primary)'
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
            <div style={styles.emptyGallery} role="status">
              <AlertTriangle size={28} color="var(--color-text-secondary)" aria-hidden="true" />
              <span style={styles.emptyText}>{t('vtest.results.emptyGallery')}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default memo(TestResults);
