import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, Search, LogOut, Bell, User as UserIcon, Menu } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const ROLE_LABELS: Record<string, string> = {
  ADMIN: 'ADMIN',
  RESEARCHER: 'RESEARCHER',
  FOREST_OFFICER: 'OFFICER',
  NGO: 'NGO',
  CITIZEN: 'CITIZEN',
};

interface NavbarProps {
  onMenuToggle?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onMenuToggle }) => {
  const { user, logout, primaryRole } = useAuth();
  const navigate = useNavigate();

  const initials = user
    ? (user.full_name || user.username || 'U').slice(0, 2).toUpperCase()
    : '??';

  return (
    <header
      className="h-14 flex items-center justify-between px-3 sm:px-5 shrink-0 border-b relative z-30"
      style={{
        backgroundColor: '#131210',
        borderBottomColor: '#2a2924',
      }}
    >
      {/* ── Left / Brand ── */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Mobile menu toggle */}
        <button
          onClick={onMenuToggle}
          className="lg:hidden p-1.5 rounded text-[#a8a49c] hover:text-white hover:bg-[#23221d] transition-colors focus:outline-none focus:ring-1 focus:ring-[#1fa34a]"
          aria-label="Toggle Navigation Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <Link to="/" className="flex items-center gap-2.5 sm:gap-3 group">
          <div
            className="w-8 h-8 flex items-center justify-center shrink-0"
            style={{ backgroundColor: '#11682f', borderRadius: '3px' }}
          >
            <Shield className="w-4 h-4 text-white" />
          </div>
          <div className="leading-none">
            <span
              className="block font-mono text-[11px] sm:text-xs font-semibold tracking-wider sm:tracking-widest uppercase truncate max-w-[150px] sm:max-w-none"
              style={{ color: '#f0ede6', letterSpacing: '0.14em' }}
            >
              WILDLIFE INTELLIGENCE
            </span>
            <span
              className="hidden sm:block font-mono text-[9px] tracking-widest uppercase"
              style={{ color: '#5e5b54', letterSpacing: '0.14em' }}
            >
              CONSERVATION DECISION SUPPORT
            </span>
          </div>
        </Link>
      </div>

      {/* ── Right controls ── */}
      <div className="flex items-center gap-3">
        {/* Search bar */}
        <button
          onClick={() => navigate('/search')}
          className="hidden lg:flex items-center gap-2 px-3 py-1.5 text-xs transition-all"
          style={{
            backgroundColor: '#1f1e1a',
            border: '1px solid #2e2d28',
            borderRadius: '3px',
            color: '#77746c',
            width: '220px',
          }}
        >
          <Search className="w-3.5 h-3.5 shrink-0" style={{ color: '#5e5b54' }} />
          <span>Search registry...</span>
          <span
            className="ml-auto font-mono text-[9px] px-1.5 py-0.5"
            style={{ backgroundColor: '#2a2924', borderRadius: '2px', color: '#5e5b54' }}
          >
            ⌘K
          </span>
        </button>

        {user ? (
          <div className="flex items-center gap-2">
            {/* Alerts bell */}
            <Link
              to="/alerts"
              title="Alerts"
              className="w-8 h-8 flex items-center justify-center transition-colors"
              style={{ color: '#77746c', borderRadius: '3px' }}
              onMouseEnter={e => (e.currentTarget.style.color = '#f0ede6')}
              onMouseLeave={e => (e.currentTarget.style.color = '#77746c')}
            >
              <Bell className="w-4 h-4" />
            </Link>

            {/* User info */}
            <div
              className="hidden sm:flex items-center gap-2.5 px-3 py-1.5"
              style={{
                backgroundColor: '#1f1e1a',
                border: '1px solid #2e2d28',
                borderRadius: '3px',
              }}
            >
              <div
                className="w-6 h-6 flex items-center justify-center text-xs font-bold font-mono shrink-0"
                style={{
                  backgroundColor: '#0f5126',
                  color: '#a7ebba',
                  borderRadius: '2px',
                }}
              >
                {initials}
              </div>
              <div className="hidden md:block leading-none">
                <span className="block text-xs font-medium" style={{ color: '#d1cfc8' }}>
                  {user.username}
                </span>
                <span
                  className="block font-mono text-[9px] tracking-widest uppercase mt-0.5"
                  style={{ color: '#77746c' }}
                >
                  {ROLE_LABELS[primaryRole] ?? primaryRole}
                </span>
              </div>
            </div>

            {/* Logout */}
            <button
              onClick={logout}
              title="Sign out"
              className="w-8 h-8 flex items-center justify-center transition-colors"
              style={{ color: '#77746c', borderRadius: '3px' }}
              onMouseEnter={e => (e.currentTarget.style.color = '#f87171')}
              onMouseLeave={e => (e.currentTarget.style.color = '#77746c')}
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link
              to="/login"
              className="text-xs px-3 py-1.5 transition-colors"
              style={{ color: '#94918a', borderRadius: '3px' }}
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="text-xs font-semibold px-3 py-1.5 transition-colors"
              style={{
                backgroundColor: '#11682f',
                color: '#fff',
                borderRadius: '3px',
              }}
            >
              Register
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};
