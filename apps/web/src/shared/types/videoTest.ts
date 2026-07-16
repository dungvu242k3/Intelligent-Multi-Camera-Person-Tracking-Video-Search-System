export enum VideoTestTab {
  Upload = 'upload',
  Url = 'url',
}

export enum VideoTestPhase {
  Idle = 'idle',
  Processing = 'processing',
  Success = 'success',
}

export enum DetectionClass {
  Person = 'person',
  Fire = 'fire',
  Object = 'object',
}

export interface DetectionStats {
  persons: number;
  fires: number;
  objects: number;
  fps: number;
}

export interface CropDetail {
  id: string;
  timestamp: string;
  class_name: DetectionClass;
  confidence: number;
  crop_url: string;
}

export interface TimelineEntry {
  second: number;
  persons: number;
  fires: number;
  objects: number;
}

export interface TestSummary extends DetectionStats {
  elapsedSeconds: number;
  totalFrames: number;
}

export interface VideoTestReport {
  test_name: string;
  summary: {
    total_persons: number;
    total_fires: number;
    total_objects: number;
    average_fps: number;
  };
  detections_timeline: TimelineEntry[];
  captured_keyframe_crops: CropDetail[];
}

export interface VideoUrlTestRequest {
  url: string;
}

export interface VideoTestAcceptedResponse {
  accepted: boolean;
  job_id: string;
  source_type: 'file' | 'url';
  status: 'accepted';
  message: string;
  filename?: string | null;
  url?: string | null;
  size_bytes?: number | null;
}
