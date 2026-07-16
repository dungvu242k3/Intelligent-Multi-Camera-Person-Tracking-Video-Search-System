import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore.ts';

interface ProtectedRouteProps {
  allowAnonymous?: boolean;
}

export default function ProtectedRoute({ allowAnonymous = false }: ProtectedRouteProps) {
  const { isAuthenticated } = useAuthStore();

  if (allowAnonymous) {
    // Public authentication routes (login/register)
    // If user is already authenticated, redirect to root dashboard path
    return isAuthenticated ? <Navigate to="/" replace /> : <Outlet />;
  }

  // Guarded private dashboard routes
  // If user is not authenticated, redirect to login gate
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}
