import axiosInstance from '../../../shared/utils/axiosInstance.ts';
import {
  DetectionStats,
  CropDetail,
  TimelineEntry,
  VideoTestAcceptedResponse,
  VideoTestReport,
  VideoUrlTestRequest,
} from '../../../shared/types/videoTest.ts';
import { VIDEO_TEST_ENDPOINTS, VIDEO_TEST_REPORT } from '../constants.ts';

export async function submitVideoFile(file: File, signal?: AbortSignal): Promise<VideoTestAcceptedResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axiosInstance.post<VideoTestAcceptedResponse>(VIDEO_TEST_ENDPOINTS.testVideo, formData, {
    signal,
  });

  return response.data;
}

export async function submitVideoUrl(url: string, signal?: AbortSignal): Promise<VideoTestAcceptedResponse> {
  const payload: VideoUrlTestRequest = { url };
  const response = await axiosInstance.post<VideoTestAcceptedResponse>(VIDEO_TEST_ENDPOINTS.testUrl, payload, { signal });

  return response.data;
}

export function buildVideoTestReport(
  stats: DetectionStats,
  timelineData: TimelineEntry[],
  crops: CropDetail[]
): VideoTestReport {
  return {
    test_name: VIDEO_TEST_REPORT.testName,
    summary: {
      total_persons: stats.persons,
      total_fires: stats.fires,
      total_objects: stats.objects,
      average_fps: stats.fps,
    },
    detections_timeline: timelineData,
    captured_keyframe_crops: crops,
  };
}

export function downloadVideoTestReport(report: VideoTestReport): void {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');

  link.href = url;
  link.download = VIDEO_TEST_REPORT.fileName;
  link.click();
  URL.revokeObjectURL(url);
}
