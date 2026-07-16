import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import VideoTestPage from './VideoTestPage.tsx';
import { submitVideoFile, submitVideoUrl } from './services/videoTestService.ts';

vi.mock('./services/videoTestService.ts', async () => {
  const actual = await vi.importActual<typeof import('./services/videoTestService.ts')>('./services/videoTestService.ts');

  return {
    ...actual,
    submitVideoFile: vi.fn(),
    submitVideoUrl: vi.fn(),
  };
});

describe('VideoTestPage', () => {
  it('starts upload analysis and aborts the backend request when cancelled', async () => {
    const user = userEvent.setup();
    let capturedSignal: AbortSignal | undefined;

    vi.mocked(submitVideoFile).mockImplementation((_file: File, signal?: AbortSignal) => {
      capturedSignal = signal;
      return new Promise(() => undefined);
    });
    vi.mocked(submitVideoUrl).mockResolvedValue({ accepted: true });

    const { container } = render(<VideoTestPage />);
    const fileInput = container.querySelector<HTMLInputElement>('#video-file-input');
    expect(fileInput).not.toBeNull();

    const file = new File(['video-bytes'], 'incident.mp4', { type: 'video/mp4' });
    await user.upload(fileInput as HTMLInputElement, file);

    expect(submitVideoFile).toHaveBeenCalledWith(file, expect.any(AbortSignal));
    expect(await screen.findByText(/submitting analysis job to backend/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /cancel/i }));

    await waitFor(() => {
      expect(capturedSignal?.aborted).toBe(true);
    });
  });
});
