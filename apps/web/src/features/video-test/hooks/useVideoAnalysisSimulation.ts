import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  CropDetail,
  DetectionClass,
  DetectionStats,
  TestSummary,
  TimelineEntry,
  VideoTestPhase,
} from '../../../shared/types/videoTest.ts';
import { VIDEO_TEST_SIMULATION } from '../constants.ts';

interface ProgressLabels {
  uploading: string;
  initDecoder: string;
  analyzing: string;
  aggregating: string;
}

interface MutableSimulationState {
  progressPercent: number;
  personCount: number;
  fireCount: number;
  objectCount: number;
  timeline: TimelineEntry[];
}

interface UseVideoAnalysisSimulationResult {
  phase: VideoTestPhase;
  statusText: string;
  progressPercent: number;
  stats: DetectionStats;
  timelineData: TimelineEntry[];
  crops: CropDetail[];
  summary: TestSummary;
  startSimulation: () => void;
  resetSimulation: () => void;
}

function createCropUrl(seed: string): string {
  return `https://api.dicebear.com/7.x/identicon/svg?seed=${seed}`;
}

function buildCropGallery(personCount: number, fireCount: number): CropDetail[] {
  const crops: CropDetail[] = [];

  if (personCount > 0) {
    for (let index = 0; index < Math.min(personCount, VIDEO_TEST_SIMULATION.maxPersonCrops); index += 1) {
      crops.push({
        id: `p-${index}`,
        timestamp: `00:0${index + 1}`,
        class_name: DetectionClass.Person,
        confidence: 0.88 + index * 0.02,
        crop_url: createCropUrl(`person-${index}`),
      });
    }
  }

  if (fireCount > 0) {
    crops.push({
      id: 'f-0',
      timestamp: '00:05',
      class_name: DetectionClass.Fire,
      confidence: 0.94,
      crop_url: createCropUrl('fire-0'),
    });
  }

  return crops;
}

export function useVideoAnalysisSimulation(labels: ProgressLabels): UseVideoAnalysisSimulationResult {
  const [phase, setPhase] = useState<VideoTestPhase>(VideoTestPhase.Idle);
  const [statusText, setStatusText] = useState('');
  const [progressPercent, setProgressPercent] = useState(0);
  const [stats, setStats] = useState<DetectionStats>(VIDEO_TEST_SIMULATION.initialStats);
  const [timelineData, setTimelineData] = useState<TimelineEntry[]>([]);
  const [crops, setCrops] = useState<CropDetail[]>([]);

  const intervalRef = useRef<number | null>(null);
  const simulationRef = useRef<MutableSimulationState>({
    progressPercent: VIDEO_TEST_SIMULATION.initialProgressPercent,
    personCount: 0,
    fireCount: 0,
    objectCount: 0,
    timeline: [],
  });

  const clearSimulationInterval = useCallback(() => {
    if (intervalRef.current !== null) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const finishSimulation = useCallback(() => {
    const { personCount, fireCount, timeline } = simulationRef.current;

    clearSimulationInterval();
    setPhase(VideoTestPhase.Success);
    setProgressPercent(VIDEO_TEST_SIMULATION.finalProgressPercent);
    setTimelineData(timeline);
    setCrops(buildCropGallery(personCount, fireCount));
  }, [clearSimulationInterval]);

  const startSimulation = useCallback(() => {
    clearSimulationInterval();
    simulationRef.current = {
      progressPercent: VIDEO_TEST_SIMULATION.initialProgressPercent,
      personCount: 0,
      fireCount: 0,
      objectCount: 0,
      timeline: [],
    };

    setPhase(VideoTestPhase.Processing);
    setStatusText(labels.uploading);
    setProgressPercent(VIDEO_TEST_SIMULATION.initialProgressPercent);
    setStats(VIDEO_TEST_SIMULATION.initialStats);
    setTimelineData([]);
    setCrops([]);

    intervalRef.current = window.setInterval(() => {
      const simulation = simulationRef.current;
      simulation.progressPercent += VIDEO_TEST_SIMULATION.progressStepPercent;

      if (simulation.progressPercent <= VIDEO_TEST_SIMULATION.uploadCompletePercent) {
        setStatusText(labels.uploading);
      } else if (simulation.progressPercent <= VIDEO_TEST_SIMULATION.decoderReadyPercent) {
        setStatusText(labels.initDecoder);
      } else if (simulation.progressPercent <= VIDEO_TEST_SIMULATION.analysisCompletePercent) {
        const second = Math.floor(
          (simulation.progressPercent - VIDEO_TEST_SIMULATION.decoderReadyPercent) /
            VIDEO_TEST_SIMULATION.analysisSecondsDivisor
        );

        const personIncrement = Math.random() > VIDEO_TEST_SIMULATION.personDetectionChance ? 1 : 0;
        const fireIncrement = VIDEO_TEST_SIMULATION.fireDetectionProgressMarks.includes(
          simulation.progressPercent
        )
          ? 1
          : 0;
        const objectIncrement = Math.random() > VIDEO_TEST_SIMULATION.objectDetectionChance ? 1 : 0;

        simulation.personCount += personIncrement;
        simulation.fireCount += fireIncrement;
        simulation.objectCount += objectIncrement;
        simulation.timeline.push({
          second,
          persons: personIncrement,
          fires: fireIncrement,
          objects: objectIncrement,
        });

        setStatusText(
          `${labels.analyzing} ${Math.floor(
            simulation.progressPercent * VIDEO_TEST_SIMULATION.frameCountMultiplier
          )}/${VIDEO_TEST_SIMULATION.totalFrames}`
        );
        setStats({
          persons: simulation.personCount,
          fires: simulation.fireCount,
          objects: simulation.objectCount,
          fps: VIDEO_TEST_SIMULATION.baseFps + Math.random() * VIDEO_TEST_SIMULATION.fpsJitter,
        });
      } else if (simulation.progressPercent < VIDEO_TEST_SIMULATION.finalProgressPercent) {
        setStatusText(labels.aggregating);
      } else {
        finishSimulation();
      }

      setProgressPercent(Math.min(simulation.progressPercent, VIDEO_TEST_SIMULATION.finalProgressPercent));
    }, VIDEO_TEST_SIMULATION.intervalMs);
  }, [clearSimulationInterval, finishSimulation, labels.aggregating, labels.analyzing, labels.initDecoder, labels.uploading]);

  const resetSimulation = useCallback(() => {
    clearSimulationInterval();
    setPhase(VideoTestPhase.Idle);
    setStatusText('');
    setProgressPercent(0);
    setStats(VIDEO_TEST_SIMULATION.initialStats);
    setTimelineData([]);
    setCrops([]);
  }, [clearSimulationInterval]);

  useEffect(() => {
    return () => {
      clearSimulationInterval();
    };
  }, [clearSimulationInterval]);

  const summary = useMemo<TestSummary>(
    () => ({
      ...stats,
      elapsedSeconds: VIDEO_TEST_SIMULATION.elapsedSeconds,
      totalFrames: VIDEO_TEST_SIMULATION.totalFrames,
    }),
    [stats]
  );

  return {
    phase,
    statusText,
    progressPercent,
    stats,
    timelineData,
    crops,
    summary,
    startSimulation,
    resetSimulation,
  };
}
