export enum FireSeverity {
  Critical = 'CRITICAL',
  Warning = 'WARNING',
  Resolved = 'RESOLVED',
}

export interface CameraNode {
  id: string;
  name: string;
  x: number;
  y: number;
}

export interface FireEvent {
  id: string;
  camera_id: string;
  camera_name: string;
  timestamp: string;
  severity: FireSeverity;
}
