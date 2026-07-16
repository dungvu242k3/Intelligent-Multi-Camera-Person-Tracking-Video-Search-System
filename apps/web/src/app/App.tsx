import { Providers } from './providers.tsx';
import { AppRouter } from './router.tsx';

function App() {
  return (
    <Providers>
      <AppRouter />
    </Providers>
  );
}

export default App;
