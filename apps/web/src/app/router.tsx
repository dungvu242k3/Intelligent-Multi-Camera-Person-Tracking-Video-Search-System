import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useAuthStore } from '../shared/stores/authStore.ts';
import { refreshAccessToken } from '../shared/utils/axiosInstance.ts';
import ProtectedRoute from '../shared/components/routes/ProtectedRoute.tsx';
import MainLayout from '../shared/components/layout/MainLayout.tsx';
import Spinner from '../shared/components/common/Spinner.tsx';
import LoginPage from '../features/auth/LoginPage.tsx';
import RegisterPage from '../features/auth/RegisterPage.tsx';
import DashboardPage from '../features/dashboard/DashboardPage.tsx';
import LiveMonitorPage from '../features/live-monitor/LiveMonitorPage.tsx';
import PersonSearchPage from '../features/person-search/PersonSearchPage.tsx';
import CameraManagementPage from '../features/camera-management/CameraManagementPage.tsx';
import VideoTestPage from '../features/video-test/VideoTestPage.tsx';
import FireDetectionPage from '../features/fire-detection/FireDetectionPage.tsx';

export function AppRouter() {
  const { initAuth } = useAuthStore();
  const [isBootstrappingAuth, setIsBootstrappingAuth] = useState(true);

  // Run initial local storage token decoding checks on boot
  useEffect(() => {
    initAuth();
    const shouldRefresh = !useAuthStore.getState().isAuthenticated;

    if (shouldRefresh) {
      void refreshAccessToken().finally(() => {
        setIsBootstrappingAuth(false);
      });
      return;
    }

    setIsBootstrappingAuth(false);
  }, [initAuth]);

  if (isBootstrappingAuth) {
    return <Spinner label="Restoring secure session" />;
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Public Authentication routes (Access permitted only when NOT logged in) */}
        <Route element={<ProtectedRoute allowAnonymous />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>

        {/* Guarded Operator Private routes (Access locks down if unauthorized) */}
        <Route element={<ProtectedRoute />}>
          <Route element={<MainLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/live" element={<LiveMonitorPage />} />
            <Route path="/search" element={<PersonSearchPage />} />
            <Route path="/cameras" element={<CameraManagementPage />} />
            <Route path="/video-test" element={<VideoTestPage />} />
            <Route path="/fire-detection" element={<FireDetectionPage />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
