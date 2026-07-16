import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from '../shared/components/layout/MainLayout.tsx';
import DashboardPage from '../features/dashboard/DashboardPage.tsx';
import LiveMonitorPage from '../features/live-monitor/LiveMonitorPage.tsx';
import PersonSearchPage from '../features/person-search/PersonSearchPage.tsx';
import CameraManagementPage from '../features/camera-management/CameraManagementPage.tsx';
import VideoTestPage from '../features/video-test/VideoTestPage.tsx';
import FireDetectionPage from '../features/fire-detection/FireDetectionPage.tsx';

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/live" element={<LiveMonitorPage />} />
          <Route path="/search" element={<PersonSearchPage />} />
          <Route path="/cameras" element={<CameraManagementPage />} />
          <Route path="/video-test" element={<VideoTestPage />} />
          <Route path="/fire-detection" element={<FireDetectionPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
