import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  PawPrint,
  MapPin,
  ShieldAlert,
  FileText,
  AlertOctagon,
  Settings,
  Database,
  Bot,
  Compass,
  PlusCircle,
  FileCheck,
  Trophy,
  ShieldCheck,
  Users,
  DownloadCloud,
  BookOpen,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

const BASE_NAV_ITEMS = [
  { to: '/',          label: 'INTELLIGENCE HUB',  icon: LayoutDashboard },
  { to: '/assistant', label: 'AI ASSISTANT',      icon: Bot             },
  { to: '/species',   label: 'SPECIES REGISTRY',   icon: PawPrint        },
  { to: '/map',       label: 'SPATIAL MAP',         icon: MapPin          },
  { to: '/threats',   label: 'THREATS & ML RISK',  icon: ShieldAlert     },
  { to: '/documents', label: 'NLP DOCUMENTS',       icon: FileText        },
  { to: '/alerts',    label: 'ALERTS & ANOMALIES', icon: AlertOctagon    },
  { to: '/reports',   label: 'REPORTS & EXPORTS',  icon: DownloadCloud   },
];

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { hasRole, primaryRole } = useAuth();

  // Role-tailored navigation items
  const items: { to: string; label: string; icon: any }[] = [];

  const isAdmin = primaryRole === 'ADMIN' || hasRole('ADMIN');
  const isOfficer = primaryRole === 'FOREST_OFFICER' || hasRole('FOREST_OFFICER');
  const isResearcher = primaryRole === 'RESEARCHER' || hasRole('RESEARCHER');
  const isPublic = !isAdmin && !isOfficer && !isResearcher;

  // 1. General Public Experience: Clean, read-only educational awareness
  if (isPublic) {
    items.push(
      { to: '/',          label: 'OVERVIEW',         icon: LayoutDashboard },
      { to: '/awareness', label: 'AWARENESS HUB',    icon: BookOpen },
      { to: '/species',   label: 'SPECIES REGISTRY', icon: PawPrint }
    );
  } else if (isAdmin) {
    // 2. Administrator Experience: High-level platform governance + shared awareness
    items.push(
      { to: '/admin',     label: 'GOVERNANCE CONSOLE', icon: Settings },
      { to: '/awareness', label: 'AWARENESS HUB',    icon: BookOpen },
      { to: '/',          label: 'INTELLIGENCE HUB', icon: LayoutDashboard },
      { to: '/assistant', label: 'AI ASSISTANT',       icon: Bot },
      { to: '/species',   label: 'SPECIES REGISTRY',    icon: PawPrint },
      { to: '/map',       label: 'SPATIAL MAP',         icon: MapPin },
      { to: '/threats',   label: 'THREATS & ML RISK',   icon: ShieldAlert },
      { to: '/documents', label: 'NLP DOCUMENTS',       icon: FileText },
      { to: '/alerts',    label: 'ALERTS & ANOMALIES',  icon: AlertOctagon },
      { to: '/reports',   label: 'REPORTS & EXPORTS',   icon: DownloadCloud }
    );
  } else if (isOfficer) {
    // 3. Forest Officer Experience: Operational field workspace + shared awareness
    items.push(
      { to: '/officer',   label: 'OFFICER DESK',       icon: ShieldCheck },
      { to: '/awareness', label: 'AWARENESS HUB',    icon: BookOpen },
      { to: '/assistant', label: 'AI ASSISTANT',       icon: Bot },
      { to: '/documents', label: 'ASK THE CORPUS / NLP', icon: FileText },
      { to: '/map',       label: 'SPATIAL MAP & GIS',  icon: MapPin },
      { to: '/alerts',    label: 'THREAT ALERTS & ANOMALIES', icon: AlertOctagon },
      { to: '/threats',   label: 'THREAT ANALYTICS',   icon: ShieldAlert },
      { to: '/species',   label: 'SPECIES REGISTRY',    icon: PawPrint },
      { to: '/reports',   label: 'OPERATIONAL REPORTS',icon: DownloadCloud },
      { to: '/submit',    label: 'RECORD OBSERVATION', icon: PlusCircle },
      { to: '/my-submissions', label: 'FIELD RECORDS', icon: FileCheck }
    );
  } else if (isResearcher) {
    // 4. Researcher Experience: Investigation workspace + shared awareness
    items.push(
      { to: '/researcher', label: 'RESEARCH STATION',  icon: Compass },
      { to: '/awareness',  label: 'AWARENESS HUB',    icon: BookOpen },
      { to: '/assistant',  label: 'AI ASSISTANT',      icon: Bot },
      { to: '/documents',  label: 'ASK THE CORPUS / NLP', icon: FileText },
      { to: '/species',    label: 'SPECIES REGISTRY',  icon: PawPrint },
      { to: '/map',        label: 'SPATIAL MAP',       icon: MapPin },
      { to: '/threats',    label: 'THREAT ANALYTICS',  icon: ShieldAlert },
      { to: '/reports',    label: 'RESEARCH REPORTS',  icon: DownloadCloud },
      { to: '/submit',     label: 'LOG SIGHTING',      icon: PlusCircle },
      { to: '/my-submissions', label: 'MY FIELD LOGS', icon: FileCheck },
      { to: '/leaderboard', label: 'HONOR ROLL',       icon: Trophy }
    );
  }

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/60 lg:hidden backdrop-blur-xs transition-opacity"
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed lg:static top-14 bottom-0 left-0 z-40 w-64 lg:w-56 shrink-0 flex flex-col border-r transition-transform duration-200 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
        style={{
          backgroundColor: '#1a1916',
          borderRightColor: '#2a2924',
          minHeight: 'calc(100vh - 3.5rem)',
        }}
      >
      {/* Navigation */}
      <nav className="flex-1 px-2 pt-4 pb-2 space-y-0.5">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            onClick={() => {
              if (onClose) onClose();
            }}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-3 py-2.5 text-[10px] font-mono font-semibold tracking-widest uppercase transition-all rounded-sm ${
                isActive
                  ? 'text-white'
                  : 'text-[#5e5b54] hover:text-[#c5c0b5]'
              }`
            }
            style={({ isActive }) => ({
              backgroundColor: isActive ? '#11682f' : 'transparent',
            })}
          >
            {({ isActive }) => (
              <>
                <Icon
                  className="w-3.5 h-3.5 shrink-0"
                  style={{ color: isActive ? '#a7ebba' : '#5e5b54' }}
                />
                <span>{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* System status footer */}
      <div className="px-3 pb-4 pt-2" style={{ borderTop: '1px solid #2a2924' }}>
        <div className="flex items-center gap-1.5 mb-1 mt-3">
          <Database className="w-3 h-3" style={{ color: '#3fc067' }} />
          <span
            className="font-mono text-[9px] font-semibold tracking-widest uppercase"
            style={{ color: '#3fc067' }}
          >
            SYSTEM STATUS
          </span>
        </div>
        <p className="font-mono text-[9px] leading-relaxed" style={{ color: '#3a3a35' }}>
          PostGIS 3.4 · pgvector 0.8<br />
          FastAPI · PyTorch · FAISS
        </p>
      </div>
    </aside>
    </>
  );
};

