import { useState } from 'react';
import { Search, Sliders } from 'lucide-react';
import axiosInstance from '../../shared/utils/axiosInstance.ts';
import ImageUpload from './components/ImageUpload.tsx';
import SearchResults from './components/SearchResults.tsx';

interface SearchResult {
  person_id: string;
  score: number;
  payload: Record<string, any>;
}

export default function PersonSearchPage() {
  const [embedding, setEmbedding] = useState<number[] | null>(null);
  const [targetName, setTargetName] = useState<string | null>(null);
  const [targetThumb, setTargetThumb] = useState<string | null>(null);

  // Search parameters
  const [threshold, setThreshold] = useState(0.75);
  const [limit, setLimit] = useState(5);

  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSelectEmbedding = (emb: number[], name: string, thumb: string) => {
    setEmbedding(emb);
    setTargetName(name);
    setTargetThumb(thumb);
    setResults([]);
  };

  const handleExecuteSearch = async () => {
    if (!embedding) return;
    setIsLoading(true);
    try {
      const res = await axiosInstance.post<{ results: SearchResult[] }>('/search/by-image', {
        embedding,
        threshold,
        limit,
      });
      setResults(res.data.results || []);
    } catch (err) {
      console.error('Vector database search query failed:', err);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      {/* Title block */}
      <div style={styles.headerBlock}>
        <div style={styles.titleGroup}>
          <Search size={26} color="var(--color-primary)" />
          <h1 style={styles.title}>ReID Vector Search</h1>
        </div>
        <p style={styles.subtitle}>
          Trace person coordinate timelines across multi-camera nodes. Upload target crops or select suspect cards to query.
        </p>
      </div>

      <div style={styles.splitLayout}>
        {/* Left Column: Image Uploader & Parameter configuration */}
        <div className="card" style={styles.configCard}>
          <ImageUpload onSelectEmbedding={handleSelectEmbedding} isLoading={isLoading} />

          {/* Slider configurations */}
          <div style={styles.paramSection}>
            <div style={styles.paramHeader}>
              <Sliders size={14} color="var(--color-text-secondary)" />
              <span style={styles.paramTitle}>Search Parameters</span>
            </div>

            <div style={styles.field}>
              <div style={styles.fieldLabelRow}>
                <span>Similarity Threshold</span>
                <span style={styles.fieldVal}>{Math.round(threshold * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.50"
                max="0.99"
                step="0.05"
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                style={styles.slider}
              />
            </div>

            <div style={styles.field}>
              <div style={styles.fieldLabelRow}>
                <span>Max Match Count</span>
                <span style={styles.fieldVal}>{limit}</span>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                step="1"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                style={styles.slider}
              />
            </div>

            <button
              type="button"
              onClick={handleExecuteSearch}
              className="btn-primary"
              disabled={!embedding || isLoading}
              style={styles.searchBtn}
            >
              <Search size={16} />
              <span>Query Qdrant Index</span>
            </button>
          </div>
        </div>

        {/* Right Column: Display targets selected and query results */}
        <div style={styles.resultsCol}>
          {targetThumb && (
            <div className="card" style={styles.targetBanner}>
              <div style={styles.bannerLeft}>
                <img src={targetThumb} alt="Target avatar" style={styles.bannerAvatar} />
                <div>
                  <div style={styles.bannerSub}>Active Query Target</div>
                  <div style={styles.bannerName}>{targetName}</div>
                </div>
              </div>
              <div style={styles.bannerRight}>
                <span style={styles.vectorLabel}>512-D Embedding Registered</span>
              </div>
            </div>
          )}

          <SearchResults results={results} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  headerBlock: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  titleGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  title: {
    fontSize: '24px',
    color: 'var(--color-text)',
    fontFamily: 'var(--font-heading)',
  },
  subtitle: {
    fontSize: '14px',
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-body)',
  },
  splitLayout: {
    display: 'grid',
    gridTemplateColumns: '400px 1fr',
    gap: '24px',
    alignItems: 'start',
  },
  configCard: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  paramSection: {
    borderTop: '1px solid var(--color-border)',
    paddingTop: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  paramHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  paramTitle: {
    fontSize: '12px',
    fontWeight: 600,
    color: 'var(--color-text-secondary)',
    fontFamily: 'var(--font-heading)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  fieldLabelRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '13px',
    color: 'var(--color-text)',
    fontFamily: 'var(--font-body)',
  },
  fieldVal: {
    fontWeight: 600,
    color: 'var(--color-primary)',
    fontFamily: 'var(--font-heading)',
  },
  slider: {
    width: '100%',
    cursor: 'pointer',
  },
  searchBtn: {
    width: '100%',
    marginTop: '8px',
  },
  resultsCol: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  targetBanner: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 20px',
    backgroundColor: 'rgba(59, 130, 246, 0.05)',
    borderColor: 'rgba(59, 130, 246, 0.3)',
  },
  bannerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  bannerAvatar: {
    width: '46px',
    height: '46px',
    borderRadius: 'var(--radius-sm)',
    objectFit: 'cover',
    border: '1px solid var(--color-primary)',
  },
  bannerSub: {
    fontSize: '10px',
    color: 'var(--color-primary)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    fontWeight: 600,
  },
  bannerName: {
    fontSize: '15px',
    fontWeight: 600,
    color: 'var(--color-text)',
  },
  bannerRight: {
    display: 'flex',
    alignItems: 'center',
  },
  vectorLabel: {
    fontSize: '11px',
    fontFamily: 'var(--font-heading)',
    color: 'var(--color-text-secondary)',
    backgroundColor: 'rgba(15, 23, 42, 0.4)',
    padding: '6px 12px',
    borderRadius: 'var(--radius-sm)',
    border: '1px solid var(--color-border)',
  },
};
