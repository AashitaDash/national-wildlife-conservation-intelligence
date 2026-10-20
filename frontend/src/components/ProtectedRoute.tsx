import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { RoleName } from '../types';

interface ProtectedRouteProps {
  roles?: RoleName[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ roles }) => {
  const { user, loading, hasRole } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-charcoal-950 flex items-center justify-center text-earthy-400 font-mono text-xs">
        Authenticating session...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (roles && !hasRole(roles)) {
    return (
      <div className="p-8 text-center bg-charcoal-950 min-h-screen flex flex-col items-center justify-center">
        <h2 className="text-xl font-bold text-rose-400 mb-2">403 — Unauthorized Access</h2>
        <p className="text-earthy-400 text-sm max-w-md mb-4">
          Your current role does not have permission to view this section of the platform.
        </p>
        <Navigate to="/" replace />
      </div>
    );
  }

  return <Outlet />;
};
