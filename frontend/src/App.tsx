import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { ProtectedRoute } from './components/ProtectedRoute';

import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { SearchPage } from './pages/SearchPage';
import { SpeciesCatalogPage } from './pages/SpeciesCatalogPage';
import { SpeciesDetailPage } from './pages/SpeciesDetailPage';
import { InteractiveMapPage } from './pages/InteractiveMapPage';
import { ThreatAnalyticsPage } from './pages/ThreatAnalyticsPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { AlertsPage } from './pages/AlertsPage';
import { AdminPage } from './pages/AdminPage';
import { AdminPlatformPage } from './pages/AdminPlatformPage';
import { AIAssistantPage } from './pages/AIAssistantPage';
import { ResearcherDashboardPage } from './pages/ResearcherDashboardPage';
import { SubmitSightingPage } from './pages/SubmitSightingPage';
import { MySubmissionsPage } from './pages/MySubmissionsPage';
import { LeaderboardPage } from './pages/LeaderboardPage';
import { OfficerDashboardPage } from './pages/OfficerDashboardPage';
import { ReportsPage } from './pages/ReportsPage';
import { AwarenessHubPage } from './pages/AwarenessHubPage';
import { FloatingChatWidget } from './components/FloatingChatWidget';

// Determines whether to show the app shell (Navbar + Sidebar)
const PUBLIC_PATHS = ['/login', '/register'];

const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const isPublic = PUBLIC_PATHS.includes(location.pathname);
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  // Close mobile drawer whenever route changes
  React.useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  if (isPublic) {
    // Public pages: full screen, no shell
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#131210' }}>
      {/* Top Header */}
      <Navbar onMenuToggle={() => setMobileMenuOpen(prev => !prev)} />
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Sidebar */}
        <Sidebar isOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />
        {/* Cream Workspace */}
        <main
          className="flex-1 min-w-0 overflow-y-auto"
          style={{ backgroundColor: '#faf8f4' }}
        >
          <div className="max-w-7xl mx-auto w-full p-4 sm:p-6 lg:p-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppShell>
          <Routes>
            {/* Public Auth Routes */}
            <Route path="/login"    element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected Core Platform Routes — Accessible to All Authenticated Users */}
            <Route element={<ProtectedRoute />}>
              <Route path="/"          element={<DashboardPage />} />
              <Route path="/awareness" element={<AwarenessHubPage />} />
              <Route path="/species"   element={<SpeciesCatalogPage />} />
              <Route path="/species/:id" element={<SpeciesDetailPage />} />
              <Route path="/search"    element={<SearchPage />} />
            </Route>

            {/* Researcher & Officer & Admin Shared Intelligence Routes */}
            <Route element={<ProtectedRoute roles={['RESEARCHER', 'FOREST_OFFICER', 'ADMIN', 'NGO']} />}>
              <Route path="/assistant" element={<AIAssistantPage />} />
              <Route path="/documents" element={<DocumentsPage />} />
              <Route path="/threats"   element={<ThreatAnalyticsPage />} />
              <Route path="/map"       element={<InteractiveMapPage />} />
              <Route path="/reports"   element={<ReportsPage />} />
            </Route>

            {/* Officer & Admin Specific Operational Alerts */}
            <Route element={<ProtectedRoute roles={['FOREST_OFFICER', 'ADMIN']} />}>
              <Route path="/alerts"    element={<AlertsPage />} />
              <Route path="/officer"   element={<OfficerDashboardPage />} />
            </Route>

            {/* Field Submission & Observation Workflows (Researcher, Officer, NGO) */}
            <Route element={<ProtectedRoute roles={['RESEARCHER', 'FOREST_OFFICER', 'NGO']} />}>
              <Route path="/submit"         element={<SubmitSightingPage />} />
              <Route path="/my-submissions" element={<MySubmissionsPage />} />
              <Route path="/leaderboard"    element={<LeaderboardPage />} />
            </Route>

            {/* Researcher Workspace */}
            <Route element={<ProtectedRoute roles={['RESEARCHER', 'ADMIN']} />}>
              <Route path="/researcher"     element={<ResearcherDashboardPage />} />
            </Route>

            {/* Admin Governance Only Route */}
            <Route element={<ProtectedRoute roles={['ADMIN']} />}>
              <Route path="/admin" element={<AdminPlatformPage />} />
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <FloatingChatWidget />
        </AppShell>
      </BrowserRouter>
    </AuthProvider>
  );
};

