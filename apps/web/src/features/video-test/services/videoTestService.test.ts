import { describe, expect, it, vi } from 'vitest';
import axiosInstance from '../../../shared/utils/axiosInstance.ts';
import { DetectionClass } from '../../../shared/types/videoTest.ts';
import {
  buildVideoTestReport,
  downloadVideoTestReport,
  submitVideoFile,
  submitVideoUrl,
} from './videoTestService.ts';

vi.mock('../../../shared/utils/axiosInstance.ts', () => ({
  default: {
    post: vi.fn(),
  },
}));

describe('videoTestService', () => {
  it('submits URL tests with AbortController signal support', async () => {
    const signal = new AbortController().signal;
    vi.mocked(axiosInstance.post).mockResolvedValueOnce({ data: { accepted: true } });

    await expect(submitVideoUrl('rtsp://camera.local/stream', signal)).resolves.toEqual({ accepted: true });

    expect(axiosInstance.post).toHaveBeenCalledWith(
      '/cameras/test-url',
      { url: 'rtsp://camera.local/stream' },
      { signal }
    );
  });

  it('submits uploaded video files with AbortController signal support', async () => {
    const signal = new AbortController().signal;
    const file = new File(['video-bytes'], 'sample.mp4', { type: 'video/mp4' });
    vi.mocked(axiosInstance.post).mockResolvedValueOnce({ data: { accepted: true } });

    await expect(submitVideoFile(file, signal)).resolves.toEqual({ accepted: true });

    expect(axiosInstance.post).toHaveBeenCalledWith(
      '/cameras/test-video',
      expect.any(FormData),
      expect.objectContaining({ signal })
    );
  });

  it('builds and downloads a report from current results', () => {
    const report = buildVideoTestReport(
      { persons: 2, fires: 1, objects: 3, fps: 29.5 },
      [{ second: 1, persons: 1, fires: 0, objects: 1 }],
      [
        {
          id: 'crop-1',
          timestamp: '00:01',
          class_name: DetectionClass.Person,
          confidence: 0.91,
          crop_url: 'https://example.test/crop.svg',
        },
      ]
    );

    expect(report.summary).toEqual({
      total_persons: 2,
      total_fires: 1,
      total_objects: 3,
      average_fps: 29.5,
    });

    const createObjectUrl = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:report');
    const revokeObjectUrl = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => undefined);
    const click = vi.fn();
    const createElement = vi.spyOn(document, 'createElement').mockReturnValue({
      click,
      href: '',
      download: '',
    } as unknown as HTMLAnchorElement);

    downloadVideoTestReport(report);

    expect(createObjectUrl).toHaveBeenCalledTimes(1);
    expect(createElement).toHaveBeenCalledWith('a');
    expect(click).toHaveBeenCalledTimes(1);
    expect(revokeObjectUrl).toHaveBeenCalledWith('blob:report');
  });
});
