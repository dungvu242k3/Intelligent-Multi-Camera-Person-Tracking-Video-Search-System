import { Providers } from './providers.tsx';
import { AppRouter } from './router.tsx';
import ErrorBoundary from '../shared/components/common/ErrorBoundary.tsx';

function App() {
  return (
    <ErrorBoundary>
      <Providers>
        <AppRouter />
      </Providers>
    </ErrorBoundary>
  );
}

export default App;
