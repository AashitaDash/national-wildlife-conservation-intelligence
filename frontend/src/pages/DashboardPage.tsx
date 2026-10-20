import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert, PawPrint, AlertTriangle, Activity,
  ArrowRight, TrendingUp, RefreshCw, Search,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { DemoBanner } from '../components/DemoBanner';
import { RiskBadge, RiskIndicatorLabel } from '../components/RiskBadge';
import { EmptyState } from '../components/EmptyState';
import { errorMessage } from '../utils/format';
import { CountUp } from '../components/CountUp';
import { Skeleton } from '../components/Skeleton';
import { mlService } from '../services/api';
import { ConservationIntelligenceOverview } from '../types';
import { ResponsiveContainer, Tooltip, PieChart, Pie, Cell, Legend } from 'recharts';

const RISK_COLORS: Record<string, string> = {
  CRITICAL: '#dc2626',
  HIGH:     '#ea580c',
  MEDIUM:   '#d97706',
  LOW:      '#16a34a',
};

// ── Shared sub-components ────────────────────────────────
const SectionLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div
    className="font-mono text-[10px] font-semibold tracking-widest uppercase mb-4"
    style={{ color: '#94918a' }}
  >
    {children}
  </div>
);

const Card: React.FC<{ children: React.ReactNode; className?: string; style?: React.CSSProperties }> = ({
  children, className = '', style,
}) => (
  <div
    className={`bg-white border border-stone-200 rounded-sm shadow-sm ${className}`}
    style={{ borderColor: '#e5e0d8', ...style }}
  >
    {children}
  </div>
);

const KpiCard: React.FC<{
  to: string;
  label: string;
  value: React.ReactNode;
  subtext: string;
  icon: React.ReactNode;
  accent: string;
}> = ({ to, label, value, subtext, icon, accent }) => (
  <Link
    to={to}
    className="group block bg-white border border-stone-200 p-5 rounded-sm shadow-sm transition-all hover:shadow-md hover:-translate-y-0.5"
    style={{ borderColor: '#e5e0d8' }}
    onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = accent; }}
    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = '#e5e0d8'; }}
  >
    <div className="flex items-start justify-between gap-2 mb-3">
      <span className="font-mono text-[10px] tracking-widest uppercase font-semibold" style={{ color: '#94918a' }}>
        {label}
      </span>
      <div
        className="w-7 h-7 flex items-center justify-center shrink-0"
        style={{ backgroundColor: `${accent}18`, borderRadius: '3px' }}
      >
        <span style={{ color: accent }}>{icon}</span>
      </div>
    </div>
    <div className="font-mono text-3xl font-bold mb-1" style={{ color: '#1a1916' }}>
      {value}
    </div>
    <p className="font-mono text-[10px]" style={{ color: '#94918a' }}>{subtext}</p>
  </Link>
);

// ─────────────────────────────────────────────────────────
export const DashboardPage: React.FC = () => {
  const { user, primaryRole } = useAuth();
  const [overview, setOverview] = useState<ConservationIntelligenceOverview | null>(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);

  const fetchOverview = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await mlService.getIntelligenceOverview();
      setOverview(data);
    } catch (err: any) {
      setError(
        err?.response?.status === 403
          ? 'Your role does not have permission to view this overview.'
          : errorMessage(err, 'Could not load the conservation intelligence overview'),
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchOverview(); }, []);

  const profiles      = overview?.species_risk_profiles ?? [];
  const criticalCount = profiles.filter(p => p.risk_level === 'CRITICAL').length;
  const riskPieData   = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
    .map(lvl => ({ name: lvl, value: profiles.filter(p => p.risk_level === lvl).length, color: RISK_COLORS[lvl] }))
    .filter(d => d.value > 0);

  return (
    <div className="space-y-8 animate-fade-slide-in">
      <DemoBanner />

      {/* ── Page header ── */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <p className="font-mono text-[10px] tracking-widest uppercase font-semibold mb-1" style={{ color: '#13843a' }}>
            {primaryRole} · CONSERVATION INTELLIGENCE
          </p>
          <h1
            className="font-serif text-3xl font-bold leading-tight"
            style={{ color: '#1a1916', fontFamily: "'Newsreader', Georgia, serif" }}
          >
            Intelligence Hub
          </h1>
          <p className="text-sm mt-1" style={{ color: '#77746c' }}>
            Evidence-driven wildlife monitoring, research and decision support.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/search"
            className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold tracking-wide transition-all"
            style={{ backgroundColor: '#11682f', color: '#fff', borderRadius: '3px' }}
          >
            <Search className="w-3.5 h-3.5" />
            SEARCH REGISTRY
          </Link>
          <button
            onClick={fetchOverview}
            disabled={loading}
            className="p-2 transition-colors"
            style={{ color: '#94918a', border: '1px solid #e5e0d8', borderRadius: '3px', backgroundColor: '#fff' }}
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* ── KPI metrics ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          to="/species"
          label="Species Monitored"
          value={loading ? <Skeleton className="h-7 w-12 inline-block" /> : <CountUp value={overview?.total_species_monitored ?? 0} />}
          subtext="Tracked species records"
          icon={<PawPrint className="w-4 h-4" />}
          accent="#16a34a"
        />
        <KpiCard
          to="/map"
          label="Observations"
          value={loading ? <Skeleton className="h-7 w-14 inline-block" /> : <CountUp value={overview?.total_observations_recorded ?? 0} />}
          subtext="Geolocated field records"
          icon={<Activity className="w-4 h-4" />}
          accent="#0891b2"
        />
        <KpiCard
          to="/threats"
          label="Active Threats"
          value={loading ? <Skeleton className="h-7 w-10 inline-block" /> : <CountUp value={overview?.active_threats_tracked ?? 0} />}
          subtext="Indexed threat mentions"
          icon={<TrendingUp className="w-4 h-4" />}
          accent="#ea580c"
        />
        <KpiCard
          to="/threats"
          label="High-Risk Species"
          value={
            <span style={{ color: '#dc2626' }}>
              {loading ? <Skeleton className="h-7 w-8 inline-block" /> : <CountUp value={criticalCount} />}
            </span>
          }
          subtext="Platform-generated risk indicator"
          icon={<ShieldAlert className="w-4 h-4" />}
          accent="#dc2626"
        />
      </div>

      {/* ── Error state ── */}
      {error && (
        <EmptyState
          variant="error"
          title="Overview unavailable"
          description={error}
          actionLabel="Retry"
          onAction={fetchOverview}
        />
      )}

      {/* ── Main content grid ── */}
      {!error && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Risk distribution chart */}
          <Card className="lg:col-span-2 p-5">
            <div className="flex items-center justify-between mb-1 gap-2 flex-wrap">
              <div>
                <SectionLabel>RISK PROFILES</SectionLabel>
              </div>
              <RiskIndicatorLabel />
            </div>
            <p className="text-xs mb-4" style={{ color: '#77746c' }}>
              Random Forest composite score distribution across profiled species.
            </p>
            {loading ? (
              <Skeleton className="h-56 w-full" />
            ) : riskPieData.length === 0 ? (
              <EmptyState title="No risk profiles" description="Risk profiles will appear once the platform generates them." />
            ) : (
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={riskPieData}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={50}
                      outerRadius={85}
                      paddingAngle={2}
                    >
                      {riskPieData.map(d => <Cell key={d.name} fill={d.color} />)}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        borderColor: '#e5e0d8',
                        borderRadius: '3px',
                        fontSize: '11px',
                        fontFamily: "'JetBrains Mono', monospace",
                        color: '#1a1916',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', fontFamily: "'JetBrains Mono', monospace" }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          {/* Top risk species */}
          <Card className="p-5 flex flex-col">
            <SectionLabel>HIGHEST PRIORITY SPECIES</SectionLabel>
            <RiskIndicatorLabel className="block -mt-2 mb-4" />
            <div className="space-y-2 flex-1">
              {loading && <Skeleton className="h-14 w-full" />}
              {!loading && profiles.length === 0 && (
                <p className="text-xs font-mono" style={{ color: '#94918a' }}>No risk profiles available.</p>
              )}
              {profiles.map((sp, idx) => (
                <div
                  key={sp.species_id}
                  className="flex items-center justify-between gap-3 p-3 border animate-fade-slide-in"
                  style={{
                    borderColor: '#f0ede6',
                    borderRadius: '3px',
                    backgroundColor: '#fdfcfa',
                    animationDelay: `${idx * 60}ms`,
                  }}
                >
                  <div className="min-w-0">
                    <span className="text-xs font-semibold block truncate" style={{ color: '#1a1916' }}>
                      {sp.common_name}
                    </span>
                    {sp.primary_threat && (
                      <span className="font-mono text-[10px] block truncate" style={{ color: '#94918a' }}>
                        {sp.primary_threat}
                      </span>
                    )}
                  </div>
                  <RiskBadge level={sp.risk_level} score={sp.risk_score} size="sm" />
                </div>
              ))}
            </div>
            <Link
              to="/threats"
              className="mt-4 flex items-center justify-center gap-1.5 py-2 text-[11px] font-mono font-semibold tracking-wide transition-all"
              style={{ border: '1px solid #e5e0d8', borderRadius: '3px', color: '#13843a' }}
            >
              VIEW FULL RISK ANALYSIS <ArrowRight className="w-3 h-3" />
            </Link>
          </Card>
        </div>
      )}
    </div>
  );
};
