import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import ErrorBoundary from './ErrorBoundary.tsx';

function preventExpectedRenderError(event: ErrorEvent): void {
  event.preventDefault();
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    window.addEventListener('error', preventExpectedRenderError);
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  afterEach(() => {
    window.removeEventListener('error', preventExpectedRenderError);
  });

  it('renders a retryable fallback and recovers when the child stops throwing', async () => {
    const user = userEvent.setup();
    let shouldThrow = true;

    function FlakyChild() {
      if (shouldThrow) {
        throw new Error('render failure');
      }

      return <div>Recovered view</div>;
    }

    render(
      <ErrorBoundary>
        <FlakyChild />
      </ErrorBoundary>
    );

    expect(screen.getByRole('alert')).toHaveTextContent('Application error');

    shouldThrow = false;
    await user.click(screen.getByRole('button', { name: /retry/i }));

    expect(screen.getByText('Recovered view')).toBeInTheDocument();
  });
});
