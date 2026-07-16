import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { FileVideo, RotateCcw } from 'lucide-react';
import { useTranslation } from '../../shared/hooks/useTranslation.ts';
import { isHttpClientError } from '../../shared/utils/axiosInstance.ts';
import { VideoTestPhase, VideoTestTab } from '../../shared/types/videoTest.ts';
import VideoUploader from './components/VideoUploader.tsx';
import UrlInput from './components/UrlInput.tsx';
import AnalysisProgress from './components/AnalysisProgress.tsx';
import TestResults from './components/TestResults.tsx';
import VideoTestTabs from './components/VideoTestTabs.tsx';
import { useVideoAnalysisSimulation } from './hooks/useVideoAnalysisSimulation.ts';
import {
  buildVideoTestReport,
  downloadVideoTestReport,
  submitVideoFile,
  submitVideoUrl,
} from './services/videoTestService.ts';
import { videoTestPageStyles as styles } from './VideoTestPage.styles.ts';

export default function VideoTestPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<VideoTestTab>(VideoTestTab.Upload);
  const [backendMessage, setBackendMessage] = useState<string | null>(null);
  const [isSubmittingBackendJob, setIsSubmittingBackendJob] = useState(false);
  const backendRequestRef = useRef<AbortController | null>(null);

  const progressLabels = useMemo(
    () => ({
      uploading: t('vtest.progress.uploading'),
      initDecoder: t('vtest.progress.initDecoder'),
      analyzing: t('vtest.progress.analyzing'),
      aggregating: t('vtest.progress.aggregating'),
    }),
    [t]
  );

  const {
    phase,
    statusText,
    progressPercent,
    stats,
    timelineData,
    crops,
    summary,
    startSimulation,
    resetSimulation,
  } = useVideoAnalysisSimulation(progressLabels);

  const formatSecureError = useCallback(
    (error: unknown): string => {
      if (isHttpClientError(error) && error.response) {
        const { status } = error.response;
        if (status === 401) return t('error.401');
        if (status === 403) return t('error.403');
        if (status === 429) return t('error.429');
        if (status === 500) return t('error.500');
      }

      return t('error.generic');
    },
    [t]
  );

  const beginBackendRequest = useCallback(() => {
    backendRequestRef.current?.abort();
    const controller = new AbortController();
    backendRequestRef.current = controller;
    setBackendMessage(null);
    setIsSubmittingBackendJob(true);
    return controller.signal;
  }, []);

  const endBackendRequest = useCallback((signal: AbortSignal) => {
    if (backendRequestRef.current?.signal === signal) {
      backendRequestRef.current = null;
      setIsSubmittingBackendJob(false);
    }
  }, []);

  const handleFileSelected = useCallback(
    (file: File) => {
      logger.info(`Selected file: ${file.name}. Initializing analysis.`);
      startSimulation();
      const signal = beginBackendRequest();

      void submitVideoFile(file, signal)
        .then((response) => {
          logger.info('Real backend upload succeeded:', response);
          setBackendMessage(null);
        })
        .catch((error: unknown) => {
          if (signal.aborted) {
            return;
          }
          logger.warning('Real backend connection failed. Secure client-side error mapped:', formatSecureError(error));
          setBackendMessage(formatSecureError(error));
        })
        .finally(() => {
          endBackendRequest(signal);
        });
    },
    [beginBackendRequest, endBackendRequest, formatSecureError, startSimulation]
  );

  const handleUrlSubmitted = useCallback(
    (url: string) => {
      logger.info(`Submitted URL: ${url}. Initializing analysis.`);
      startSimulation();
      const signal = beginBackendRequest();

      void submitVideoUrl(url, signal)
        .then((response) => {
          logger.info('Real backend URL submitted:', response);
          setBackendMessage(null);
        })
        .catch((error: unknown) => {
          if (signal.aborted) {
            return;
          }
          logger.warning('Real backend URL post failed. Secure client-side error mapped:', formatSecureError(error));
          setBackendMessage(formatSecureError(error));
        })
        .finally(() => {
          endBackendRequest(signal);
        });
    },
    [beginBackendRequest, endBackendRequest, formatSecureError, startSimulation]
  );

  const downloadReport = useCallback(() => {
    downloadVideoTestReport(buildVideoTestReport(stats, timelineData, crops));
  }, [crops, stats, timelineData]);

  const handleTabChange = useCallback((tab: VideoTestTab) => {
    setActiveTab(tab);
  }, []);

  const handleReset = useCallback(() => {
    backendRequestRef.current?.abort();
    backendRequestRef.current = null;
    setIsSubmittingBackendJob(false);
    setBackendMessage(null);
    resetSimulation();
  }, [resetSimulation]);

  useEffect(() => {
    return () => {
      backendRequestRef.current?.abort();
    };
  }, []);

  const showUploadTab = activeTab === VideoTestTab.Upload;

  return (
    <div style={styles.page}>
      <div style={styles.titleBlock}>
        <div style={styles.titleGroup}>
          <FileVideo size={28} color="var(--color-primary)" />
          <h1 style={styles.title}>{t('vtest.title')}</h1>
        </div>
        <p style={styles.subtitle}>{t('vtest.subtitle')}</p>
      </div>

      {phase === VideoTestPhase.Idle && (
        <div className="card" style={styles.mainCard}>
          <VideoTestTabs activeTab={activeTab} onTabChange={handleTabChange} />

          <div style={styles.tabContent}>
            {showUploadTab ? (
              <VideoUploader onFileSelected={handleFileSelected} />
            ) : (
              <UrlInput onUrlSubmitted={handleUrlSubmitted} />
            )}
          </div>
        </div>
      )}

      {phase === VideoTestPhase.Processing && (
        <div className="card" style={styles.mainCard}>
          {isSubmittingBackendJob && (
            <div style={styles.statusBanner} role="status" aria-live="polite">
              Submitting analysis job to backend...
            </div>
          )}
          {backendMessage && (
            <div style={styles.errorBanner} role="alert">
              {backendMessage}
            </div>
          )}
          <AnalysisProgress statusText={statusText} progressPercent={progressPercent} stats={stats} />
          <button type="button" onClick={handleReset} className="btn-secondary" style={styles.cancelBtn}>
            {t('vtest.cancel')}
          </button>
        </div>
      )}

      {phase === VideoTestPhase.Success && (
        <>
          <TestResults
            summary={summary}
            timelineData={timelineData}
            crops={crops}
            onDownloadReport={downloadReport}
          />
          <button type="button" onClick={handleReset} className="btn-secondary" style={styles.resetBtn}>
            <RotateCcw size={16} />
            <span>{t('vtest.reset')}</span>
          </button>
        </>
      )}
    </div>
  );
}

const logger = {
  info: (message: string, details?: unknown) => console.log(`[INFO] ${message}`, details || ''),
  warning: (message: string, details?: unknown) => console.warn(`[WARN] ${message}`, details || ''),
};
