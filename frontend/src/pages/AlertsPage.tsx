import React, { useEffect, useState } from 'react';
import { AlertOctagon, Bell, ShieldAlert, CheckCircle2, ChevronDown, Filter, Search, Check } from 'lucide-react';
import { alertService } from '../services/api';
import { Alert } from '../types';
import { DemoBanner } from '../components/DemoBanner';
import { SkeletonRows } from '../components/Skeleton';
import { EmptyState } from '../components/EmptyState';
import { errorMessage } from '../utils/format';

// Backend severities are INFO / WARNING / CRITICAL (HIGH/MEDIUM/LOW styles kept for forward compatibility).
type SeverityFilter = string;
const SEVERITY_ORDER = ['CRITICAL', 'HIGH', 'WARNING', 'MEDIUM', 'INFO', 'LOW'];

const severityStyles: Record<string, { card: string; badge: string; icon: string }> = {
  CRITICAL: {
    card: 'bg-white border-rose-200',
    badge: 'bg-rose-50 text-rose-700 border-rose-200',
    icon: 'text-rose-600',
  },
  HIGH: {
    card: 'bg-white border-orange-200',
    badge: 'bg-orange-50 text-orange-700 border-orange-200',
    icon: 'text-orange-600',
  },
  WARNING: {
    card: 'bg-white border-amber-200',
    badge: 'bg-amber-50 text-amber-700 border-amber-200',
    icon: 'text-amber-600',
  },
  INFO: {
    card: 'bg-white border-cyan-200',
    badge: 'bg-cyan-50 text-cyan-700 border-cyan-200',
    icon: 'text-cyan-600',
  },
  MEDIUM: {
    card: 'bg-white border-amber-200',
    badge: 'bg-amber-50 text-amber-700 border-amber-200',
    icon: 'text-amber-600',
  },
  LOW: {
    card: 'bg-white border-emerald-200',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    icon: 'text-emerald-600',
  },
};

export const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('ALL');
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await alertService.getAlerts();
      setAlerts(res.items);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
      setAlerts([]);
      setError(errorMessage(err, 'Could not load alerts'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleToggleExpand = async (alert: Alert) => {
    const nowExpanding = expandedId !== alert.id;
    setExpandedId(nowExpanding ? alert.id : null);

    if (nowExpanding && !alert.is_read) {
      setActionError(null);
      setAlerts((prev) => prev.map((a) => (a.id === alert.id ? { ...a, is_read: true } : a)));
      try {
        await alertService.markAsRead(alert.id);
      } catch (err) {
        console.error('Mark-as-read failed:', err);
        setAlerts((prev) => prev.map((a) => (a.id === alert.id ? { ...a, is_read: false } : a)));
        setActionError(errorMessage(err, 'Could not mark the alert as read'));
      }
    }
  };

  const handleMarkSingleRead = async (e: React.MouseEvent, alertId: number) => {
    e.stopPropagation();
    setActionError(null);
    setAlerts((prev) => prev.map((a) => (a.id === alertId ? { ...a, is_read: true } : a)));
    try {
      await alertService.markAsRead(alertId);
    } catch (err) {
      console.error('Mark-as-read failed:', err);
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? { ...a, is_read: false } : a)));
      setActionError(errorMessage(err, 'Could not mark the alert as read'));
    }
  };

  const unreadCount = alerts.filter((a) => !a.is_read).length;

  // Filter chips come from severities actually present in the data.
  const severityOptions: SeverityFilter[] = [
    'ALL',
    ...Array.from(new Set(alerts.map((a) => a.severity))).sort(
      (a, b) => SEVERITY_ORDER.indexOf(a) - SEVERITY_ORDER.indexOf(b)
    ),
  ];

  const filteredAlerts = alerts.filter((a) => {
    if (severityFilter !== 'ALL' && a.severity !== severityFilter) return false;
    if (unreadOnly && a.is_read) return false;
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      const matchTitle = a.title?.toLowerCase().includes(q);
      const matchMsg = a.message?.toLowerCase().includes(q);
      const matchType = a.alert_type?.toLowerCase().includes(q);
      if (!matchTitle && !matchMsg && !matchType) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      <DemoBanner />

      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-4">
        <div>
          <p className="font-mono text-[10px] tracking-widest uppercase font-semibold mb-1" style={{ color: '#dc2626' }}>
            SYSTEM ALERTS
          </p>
          <h1 className="font-serif text-3xl font-bold leading-tight flex items-center gap-2" style={{ color: '#1a1916', fontFamily: "'Newsreader', Georgia, serif" }}>
            <AlertOctagon className="w-6 h-6" style={{ color: '#dc2626' }} />
            Conservation Alerts
            {unreadCount > 0 && (
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 ml-2" style={{ backgroundColor: '#dc2626', color: '#fff', borderRadius: '2px' }}>
                {unreadCount} UNREAD
              </span>
            )}
          </h1>
          <p className="text-sm mt-1" style={{ color: '#77746c' }}>
            Automated high-risk notifications & telemetry isolation forest outlier triggers.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 p-3 bg-white border border-[#e5e0d8] rounded-sm">
        {/* Severity & Unread Filter Chips */}
        <div className="flex flex-wrap items-center gap-2 text-[10px] font-mono tracking-widest uppercase font-semibold">
          <Filter className="w-3.5 h-3.5" style={{ color: '#94918a' }} />
          {severityOptions.map((sev) => {
            const count = sev === 'ALL' ? alerts.length : alerts.filter(a => a.severity === sev).length;
            return (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-3 py-1.5 transition-all border ${
                  severityFilter === sev
                    ? 'bg-[#1a1916] text-white border-[#1a1916]'
                    : 'bg-white text-[#94918a] border-[#e5e0d8] hover:border-[#1a1916]'
                }`}
                style={{ borderRadius: '3px' }}
              >
                {sev} ({count})
              </button>
            );
          })}
          <span className="w-px h-4 mx-1" style={{ backgroundColor: '#e5e0d8' }} />
          <button
            onClick={() => setUnreadOnly((v) => !v)}
            className={`px-3 py-1.5 transition-all border flex items-center gap-1.5 ${
              unreadOnly
                ? 'bg-[#dc2626] text-white border-[#dc2626]'
                : 'bg-white text-[#94918a] border-[#e5e0d8] hover:border-[#dc2626]'
            }`}
            style={{ borderRadius: '3px' }}
          >
            <Bell className="w-3 h-3" />
            UNREAD ({unreadCount})
          </button>
        </div>

        {/* Search Input */}
        <div className="relative min-w-[220px]">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#94918a]" />
          <input
            type="text"
            placeholder="Search alerts or species..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1 text-xs border border-[#e5e0d8] rounded focus:outline-none focus:border-[#13843a] bg-[#fdfaf5]"
          />
        </div>
      </div>

      {actionError && (
        <div role="alert" className="p-3 bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs rounded-xl">
          {actionError}
        </div>
      )}

      {loading ? (
        <SkeletonRows count={3} />
      ) : error ? (
        <EmptyState
          variant="error"
          title="Alerts unavailable"
          description={error}
          actionLabel="Retry"
          onAction={loadAlerts}
        />
      ) : filteredAlerts.length === 0 ? (
        <EmptyState
          icon={CheckCircle2}
          title={unreadOnly || severityFilter !== 'ALL' ? 'No alerts match these filters' : 'No active alerts'}
          description={
            unreadOnly || severityFilter !== 'ALL'
              ? 'Try clearing the severity or unread filters above.'
              : 'The platform has no outstanding conservation alerts right now.'
          }
        />
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map((al, idx) => {
            const styles = severityStyles[al.severity] || severityStyles.MEDIUM;
            const isExpanded = expandedId === al.id;
            return (
              <button
                key={al.id}
                onClick={() => handleToggleExpand(al)}
                className={`w-full text-left p-4 rounded-sm border transition-all hover:-translate-y-0.5 animate-fade-slide-in ${styles.card} ${
                  !al.is_read ? 'ring-1 ring-inset ring-amber-500/50' : 'opacity-90'
                }`}
                style={{ animationDelay: `${idx * 50}ms` }}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2">
                    {!al.is_read && (
                      <span
                        className="w-2 h-2 rounded-full bg-amber-500 shrink-0 animate-pulse"
                        title="Unread"
                      />
                    )}
                    <ShieldAlert className={`w-5 h-5 shrink-0 ${styles.icon}`} />
                    <h3 className="text-sm font-bold text-[#1a1916]">{al.title}</h3>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-sm border ${styles.badge}`}>
                      {al.severity}
                    </span>
                    <ChevronDown
                      className={`w-4 h-4 text-[#94918a] transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                    />
                  </div>
                </div>

                {isExpanded && (
                  <div className="animate-fade-slide-in">
                    <p className="text-xs text-[#77746c] leading-relaxed bg-[#fdfaf5] p-3 rounded-sm border border-[#e5e0d8] mb-2">
                      {al.message}
                    </p>
                    <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-[#94918a]">
                      <span>Type: {al.alert_type} &middot; Logged: {new Date(al.created_at).toLocaleString()}</span>
                      {!al.is_read ? (
                        <button
                          type="button"
                          onClick={(e) => handleMarkSingleRead(e, al.id)}
                          className="px-2 py-1 bg-white hover:bg-emerald-50 text-emerald-700 border border-emerald-300 rounded font-bold flex items-center gap-1 transition-colors"
                        >
                          <Check className="w-3 h-3" /> Mark as Read
                        </button>
                      ) : (
                        <span className="text-emerald-700 flex items-center gap-1 font-semibold">
                          <CheckCircle2 className="w-3 h-3" /> Resolved
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
