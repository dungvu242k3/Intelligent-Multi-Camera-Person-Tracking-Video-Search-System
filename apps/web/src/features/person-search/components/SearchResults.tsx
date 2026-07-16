import { useState } from 'react';
import { Clock, Video, HelpCircle } from 'lucide-react';
import axiosInstance from '../../../shared/utils/axiosInstance.ts';
import Badge from '../../../shared/components/common/Badge.tsx';
import Button from '../../../shared/components/common/Button.tsx';

interface SearchResult {
  person_id: string;
  score: number;
  payload: Record<string, any>;
}

interface TrailPoint {
  event_id: string;
  camera_id: string;
  timestamp: string;
  bbox: {
    left: number;
    top: number;
    width: number;
    height: number;
  };
  crop_path: string;
}

interface SearchResultsProps {
  results: SearchResult[];
  isLoading?: boolean;
}

export default function SearchResults({ results, isLoading = false }: SearchResultsProps) {
  const [selectedPersonId, setSelectedPersonId] = useState<string | null>(null);
  const [trailPoints, setTrailPoints] = useState<TrailPoint[]>([]);
  const [isTrailLoading, setIsTrailLoading] = useState(false);

  const handleFetchTrail = async (personId: string) => {
    setSelectedPersonId(personId);
    setIsTrailLoading(true);
    try {
      const res = await axiosInstance.get<{ person_id: string; trail_points: TrailPoint[] }>(
        `/tracking/trail/${personId}`
      );
      setTrailPoints(res.data.trail_points || []);
    } catch (err) {
      console.error('Failed to load person trail history:', err);
      setTrailPoints([]);
    } finally {
      setIsTrailLoading(false);
    }
  };

  const getMinioUrl = (cropPath: string) => {
    if (!cropPath) return 'https://placehold.co/120x120/1e293b/f1f5f9?text=Crop';
    const baseUrl = import.meta.env.VITE_MINIO_URL || 'http://localhost:9000';
    return `${baseUrl}/${cropPath}`;
  };

  return (
    <div style={styles.container}>
      {/* Search results listing */}
      <div style={styles.resultsCol}>
        <h3 style={styles.sectionTitle}>Matched Identities</h3>
        <div style={styles.list}>
          {isLoading && (
            <div style={styles.empty}>
              <span className="pulse-red-glow" style={{ color: 'var(--color-primary)' }}>
                Querying vector database indices...
              </span>
            </div>
          )}

          {!isLoading && results.length === 0 && (
            <div style={styles.empty}>
              <HelpCircle size={24} color="var(--color-text-secondary)" style={{ marginBottom: '8px' }} />
              <span>No matched profiles found in vector store.</span>
            </div>
          )}

          {!isLoading &&
            results.map((match) => {
              const isSelected = selectedPersonId === match.person_id;
              return (
                <div
                  key={match.person_id}
                  style={{
                    ...styles.matchCard,
                    borderColor: isSelected ? 'var(--color-primary)' : 'var(--color-border)',
                    boxShadow: isSelected ? '0 0 10px rgba(59, 130, 246, 0.15)' : 'none',
                  }}
                >
                  <div style={styles.matchHeader}>
                    <div style={styles.matchMeta}>
                      <span style={styles.personTitle}>Person #{match.person_id.substring(0, 8)}</span>
                      <Badge variant={match.score > 0.85 ? 'success' : 'info'}>
                        Similarity: {Math.round(match.score * 100)}%
                      </Badge>
                    </div>
                    <Button variant="secondary" onClick={() => handleFetchTrail(match.person_id)}>
                      Trace Trail
                    </Button>
                  </div>
                  <div style={styles.matchPayload}>
                    {match.payload.last_seen_camera && (
                      <span style={styles.metaLabel}>Last seen at Camera {match.payload.last_seen_camera}</span>
                    )}
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* Interactive Vertical Trail Timeline */}
      <div style={styles.timelineCol}>
        <h3 style={styles.sectionTitle}>Movement Timeline Trail</h3>

        <div style={styles.timelineBox}>
          {isTrailLoading && (
            <div style={styles.empty}>
              <span className="pulse-red-glow" style={{ color: 'var(--color-primary)' }}>
                Reconstructing travel path...
              </span>
            </div>
          )}

          {!isTrailLoading && !selectedPersonId && (
            <div style={styles.empty}>
              <span>Select an identity from the left to map their chronological cross-camera coordinates.</span>
            </div>
          )}

          {!isTrailLoading && selectedPersonId && trailPoints.length === 0 && (
            <div style={styles.empty}>
              <span>No historical coordinate trails found.</span>
            </div>
          )}

          {!isTrailLoading && selectedPersonId && trailPoints.length > 0 && (
            <div style={styles.timelineList}>
              {trailPoints.map((point, idx) => (
                <div key={point.event_id} style={styles.timelineItem}>
                  {/* Vertical bar */}
                  {idx < trailPoints.length - 1 && <div style={styles.verticalBar} />}

                  {/* Bullet */}
                  <div style={styles.bullet}>
                    <Clock size={10} color="white" />
                  </div>

                  {/* Info block */}
                  <div style={styles.infoCard}>
                    <img
                      src={getMinioUrl(point.crop_path)}
                      alt="Crop Keyframe"
                      style={styles.keyframeImg}
                      onError={(e) => {
                        (e.target as HTMLImageElement).src =
                          'https://placehold.co/120x120/1e293b/f1f5f9?text=No+Image';
                      }}
                    />
                    <div style={styles.infoDetails}>
                      <div style={styles.infoRow}>
                        <span style={styles.camName}>
                          <Video size={12} color="var(--color-primary)" />
                          <span>Camera {point.camera_id}</span>
                        </span>
                        <span style={styles.timestamp}>{new Date(point.timestamp).toLocaleTimeString()}</span>
                      </div>
                      <p style={styles.coords}>
                        Bounding Box: [{Math.round(point.bbox.left)}, {Math.round(point.bbox.top)},{' '}
                        {Math.round(point.bbox.width)}, {Math.round(point.bbox.height)}]
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'grid',
    gridTemplateColumns: '1.2fr 1fr',
    gap: '24px',
    marginTop: '20px',
  },
  resultsCol: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  timelineCol: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  sectionTitle: {
    fontSize: '14px',
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-heading)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  matchCard: {
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--color-surface)',
    padding: '16px 20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    transition: 'all 150ms ease',
  },
  matchHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  matchMeta: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    alignItems: 'flex-start',
  },
  personTitle: {
    fontSize: '15px',
    fontWeight: 600,
    color: 'var(--color-text)',
  },
  matchPayload: {
    fontSize: '12px',
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-body)',
  },
  empty: {
    padding: '64px 24px',
    textAlign: 'center',
    color: 'var(--color-text-secondary)',
    backgroundColor: 'rgba(15, 23, 42, 0.2)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    fontSize: '13px',
    lineHeight: 1.5,
  },
  timelineBox: {
    backgroundColor: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    minHeight: '400px',
    padding: '24px',
    overflowY: 'auto',
  },
  timelineList: {
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
    paddingLeft: '12px',
  },
  timelineItem: {
    position: 'relative',
    display: 'flex',
    alignItems: 'flex-start',
    gap: '20px',
  },
  verticalBar: {
    position: 'absolute',
    left: '8px',
    top: '24px',
    bottom: '-28px',
    width: '2px',
    backgroundColor: 'var(--color-border)',
  },
  bullet: {
    width: '18px',
    height: '18px',
    borderRadius: '50%',
    backgroundColor: 'var(--color-primary)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 2,
    marginTop: '12px',
  },
  infoCard: {
    flex: 1,
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    backgroundColor: 'rgba(15, 23, 42, 0.3)',
    padding: '12px',
    display: 'flex',
    gap: '12px',
  },
  keyframeImg: {
    width: '54px',
    height: '54px',
    borderRadius: 'var(--radius-sm)',
    objectFit: 'cover',
    border: '1px solid var(--color-border)',
  },
  infoDetails: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  infoRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  camName: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '12px',
    fontWeight: 600,
    color: 'var(--color-text)',
  },
  timestamp: {
    fontSize: '10px',
    fontFamily: 'var(--font-heading)',
    color: 'var(--color-text-secondary)',
  },
  coords: {
    fontSize: '11px',
    fontFamily: 'var(--font-heading)',
    color: 'var(--color-text-secondary)',
  },
};
