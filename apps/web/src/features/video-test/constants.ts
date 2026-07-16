import { DetectionStats } from '../../shared/types/videoTest.ts';

export const VIDEO_TEST_ENDPOINTS = {
  testVideo: '/cameras/test-video',
  testUrl: '/cameras/test-url',
} as const;

export const VIDEO_UPLOAD_CONSTRAINTS = {
  acceptedExtensions: ['.mp4', '.avi', '.mkv', '.mov'] as readonly string[],
  acceptedMimeTypes: 'video/mp4,video/x-msvideo,video/x-matroska,video/quicktime',
  maxFileSizeBytes: 250 * 1024 * 1024,
  bytesPerMegabyte: 1024 * 1024,
} as const;

export const VIDEO_TEST_SIMULATION = {
  initialProgressPercent: 5,
  progressStepPercent: 5,
  uploadCompletePercent: 20,
  decoderReadyPercent: 40,
  analysisCompletePercent: 80,
  finalProgressPercent: 100,
  frameCountMultiplier: 25,
  totalFrames: 2_500,
  elapsedSeconds: 22.4,
  intervalMs: 500,
  analysisSecondsDivisor: 4,
  personDetectionChance: 0.4,
  objectDetectionChance: 0.7,
  fireDetectionProgressMarks: [60, 75] as readonly number[],
  baseFps: 28.5,
  fpsJitter: 2,
  maxPersonCrops: 4,
  initialStats: {
    persons: 0,
    fires: 0,
    objects: 0,
    fps: 0,
  } satisfies DetectionStats,
} as const;

export const VIDEO_TEST_REPORT = {
  fileName: 'mcpt_test_analysis_report.json',
  testName: 'Simulated Video Detections Run',
} as const;

export const STREAM_URL_PATTERN = /^(rtsp:\/\/|http:\/\/|https:\/\/)/i;
