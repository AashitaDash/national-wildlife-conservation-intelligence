import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert, PawPrint, AlertTriangle, Activity,
  ArrowRight, TrendingUp, RefreshCw, Search,
  BookOpen, Sparkles, MapPin, Feather, Globe, HelpCircle, FileText
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { DemoBanner } from '../components/DemoBanner';
import { RiskBadge, RiskIndicatorLabel } from '../components/RiskBadge';
import { EmptyState } from '../components/EmptyState';
import { errorMessage } from '../utils/format';
import { CountUp } from '../components/CountUp';
import { Skeleton } from '../components/Skeleton';
import { mlService, speciesService } from '../services/api';
import { ConservationIntelligenceOverview, Species } from '../types';
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
  const { user, primaryRole, hasRole } = useAuth();
  const [overview, setOverview] = useState<ConservationIntelligenceOverview | null>(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);

  const isPublic = !hasRole('ADMIN') && !hasRole('FOREST_OFFICER') && !hasRole('RESEARCHER') && !hasRole('NGO');

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
  const ALL_RISK_LEVELS = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
  const riskCounts = ALL_RISK_LEVELS.reduce((acc, lvl) => {
    acc[lvl] = profiles.filter(p => p.risk_level === lvl).length;
    return acc;
  }, {} as Record<string, number>);

  const riskPieData = ALL_RISK_LEVELS
    .map(lvl => ({ name: lvl, value: riskCounts[lvl], color: RISK_COLORS[lvl] }))
    .filter(d => d.value > 0);

  // ─────────────────────────────────────────────────────────
  // GENERAL PUBLIC EXPERIENCE — Clean, read-only educational wildlife awareness
  // ─────────────────────────────────────────────────────────
  if (isPublic) {
    return (
      <div className="space-y-8 animate-fade-slide-in">
        <DemoBanner />

        {/* ── Public Page header ── */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-[#e5e0d8] pb-6">
          <div>
            <p className="font-mono text-[10px] tracking-widest uppercase font-semibold mb-1" style={{ color: '#11682f' }}>
              CITIZEN WILDLIFE AWARENESS PORTAL
            </p>
            <h1
              className="font-serif text-3xl font-bold leading-tight"
              style={{ color: '#1a1916', fontFamily: "'Newsreader', Georgia, serif" }}
            >
              National Wildlife & Conservation Overview
            </h1>
            <p className="text-sm mt-1" style={{ color: '#77746c' }}>
              Learn about India&apos;s protected species, ecological sanctuaries, biodiversity habitats, and conservation updates.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to="/species"
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold tracking-wide transition-all"
              style={{ backgroundColor: '#11682f', color: '#fff', borderRadius: '3px' }}
            >
              <Search className="w-3.5 h-3.5" />
              EXPLORE SPECIES REGISTRY
            </Link>
          </div>
        </div>

        {/* ── Public Statistics Overview ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            to="/species"
            label="Monitored Species"
            value={loading ? <Skeleton className="h-7 w-12 inline-block" /> : <CountUp value={overview?.total_species_monitored ?? 0} />}
            subtext="Catalogued indigenous species"
            icon={<PawPrint className="w-4 h-4" />}
            accent="#16a34a"
          />
          <div className="bg-white border border-[#e5e0d8] p-5 rounded-sm shadow-sm">
            <div className="flex items-start justify-between gap-2 mb-3">
              <span className="font-mono text-[10px] tracking-widest uppercase font-semibold" style={{ color: '#94918a' }}>
                Protected Sanctuaries
              </span>
              <div className="w-7 h-7 flex items-center justify-center shrink-0 bg-[#0891b218] rounded-xs text-[#0891b2]">
                <Globe className="w-4 h-4" />
              </div>
            </div>
            <div className="font-mono text-3xl font-bold mb-1 text-[#1a1916]">
              106+
            </div>
            <p className="font-mono text-[10px] text-[#94918a]">National parks & biosphere reserves</p>
          </div>
          <div className="bg-white border border-[#e5e0d8] p-5 rounded-sm shadow-sm">
            <div className="flex items-start justify-between gap-2 mb-3">
              <span className="font-mono text-[10px] tracking-widest uppercase font-semibold" style={{ color: '#94918a' }}>
                Recorded Sightings
              </span>
              <div className="w-7 h-7 flex items-center justify-center shrink-0 bg-[#ea580c18] rounded-xs text-[#ea580c]">
                <Activity className="w-4 h-4" />
              </div>
            </div>
            <div className="font-mono text-3xl font-bold mb-1 text-[#1a1916]">
              {loading ? <Skeleton className="h-7 w-14 inline-block" /> : <CountUp value={overview?.total_observations_recorded ?? 0} />}
            </div>
            <p className="font-mono text-[10px] text-[#94918a]">Verified field observations</p>
          </div>
          <Link to="/map" className="block">
            <div className="bg-white border border-[#e5e0d8] p-5 rounded-sm shadow-sm hover:border-[#11682f] transition-colors">
              <div className="flex items-start justify-between gap-2 mb-3">
                <span className="font-mono text-[10px] tracking-widest uppercase font-semibold" style={{ color: '#94918a' }}>
                  Spatial Map
                </span>
                <div className="w-7 h-7 flex items-center justify-center shrink-0 bg-[#16a34a18] rounded-xs text-[#16a34a]">
                  <MapPin className="w-4 h-4" />
                </div>
              </div>
              <div className="font-mono text-2xl font-bold mb-1 text-[#11682f]">
                Explore
              </div>
              <p className="font-mono text-[10px] text-[#94918a]">Interactive wildlife map & habitats</p>
            </div>
          </Link>
        </div>

        {/* ── Public Educational Content & Verified Updates ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Featured Species Awareness */}
          <Card className="lg:col-span-2 p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#f0ede6] pb-3">
              <div>
                <SectionLabel>SPECIES SPOTLIGHT & BIODIVERSITY</SectionLabel>
                <h3 className="font-serif font-bold text-lg text-[#1f1e1a]">India&apos;s Iconic Wildlife Heritage</h3>
              </div>
              <Link to="/species" className="text-xs font-mono font-bold text-[#11682f] hover:underline flex items-center gap-1">
                View All <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
            <p className="text-xs text-[#736f66] leading-relaxed">
              India is home to nearly 7-8% of all recorded biodiversity globally across rich forest, wetland, mountain, and coastal ecosystems.
              Explore our national species registry to learn about habitats, dietary behaviors, and regional distribution.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="p-3.5 rounded border border-[#f0ede6] bg-[#fdfcfa]">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#11682f]"></span>
                  <h4 className="font-semibold text-xs text-[#1f1e1a]">Royal Bengal Tiger (Panthera tigris)</h4>
                </div>
                <p className="text-[11px] text-[#736f66] leading-normal">
                  Apex carnivore native to Sundarbans, Western Ghats, and Central Indian tiger corridors. Focus of Project Tiger conservation initiatives.
                </p>
              </div>
              <div className="p-3.5 rounded border border-[#f0ede6] bg-[#fdfcfa]">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#11682f]"></span>
                  <h4 className="font-semibold text-xs text-[#1f1e1a]">Asian Elephant (Elephas maximus)</h4>
                </div>
                <p className="text-[11px] text-[#736f66] leading-normal">
                  Keystone herbivore shaping forest vegetation across elephant reserves in Southern, Central, and North-Eastern India.
                </p>
              </div>
              <div className="p-3.5 rounded border border-[#f0ede6] bg-[#fdfcfa]">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#11682f]"></span>
                  <h4 className="font-semibold text-xs text-[#1f1e1a]">Great Indian One-Horned Rhinoceros</h4>
                </div>
                <p className="text-[11px] text-[#736f66] leading-normal">
                  Rebounded from near extinction in Kaziranga and Manas floodplains through dedicated anti-poaching and flood shelter management.
                </p>
              </div>
              <div className="p-3.5 rounded border border-[#f0ede6] bg-[#fdfcfa]">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#11682f]"></span>
                  <h4 className="font-semibold text-xs text-[#1f1e1a]">Snow Leopard (Panthera uncia)</h4>
                </div>
                <p className="text-[11px] text-[#736f66] leading-normal">
                  Solitary high-altitude predator inhabiting alpine and sub-alpine regions of Ladakh, Himachal Pradesh, and Uttarakhand.
                </p>
              </div>
            </div>
          </Card>

          {/* Conservation Education & Threats Overview */}
          <Card className="p-6 flex flex-col justify-between">
            <div>
              <SectionLabel>COMMUNITY CONSERVATION</SectionLabel>
              <h3 className="font-serif font-bold text-lg text-[#1f1e1a] mb-2">Threats & Wildlife Protection</h3>
              <p className="text-xs text-[#736f66] leading-relaxed mb-4">
                Understanding human-wildlife coexistence, forest encroachment, and climate impacts helps communities support sustainable ecosystems.
              </p>
              <div className="space-y-3">
                <div className="p-3 bg-[#faf9f6] rounded border border-[#f0ede6]">
                  <span className="font-mono text-[10px] font-bold text-[#b45309] uppercase block mb-1">
                    Habitat Fragmentation
                  </span>
                  <p className="text-[11px] text-[#736f66]">
                    Linear infrastructure and development divide contiguous forest corridors, creating challenges for migratory megafauna.
                  </p>
                </div>
                <div className="p-3 bg-[#faf9f6] rounded border border-[#f0ede6]">
                  <span className="font-mono text-[10px] font-bold text-[#11682f] uppercase block mb-1">
                    Community Coexistence
                  </span>
                  <p className="text-[11px] text-[#736f66]">
                    Eco-development committees and prompt conflict mitigation empower fringe villages living adjacent to protected forests.
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-[#f0ede6]">
              <div className="flex items-center gap-2 text-xs font-mono text-[#11682f] font-semibold">
                <BookOpen className="w-4 h-4" />
                <span>Wildlife Protection Act, 1972</span>
              </div>
              <p className="text-[10px] text-[#94918a] mt-1">
                All wildlife sightings are verified by authorized Forest Officers before inclusion in the national registry.
              </p>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────
  // PRIVILEGED / OPERATIONAL DASHBOARD (Officers, Researchers, Admins)
  // ─────────────────────────────────────────────────────────
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
                      stroke="none"
                      style={{ outline: 'none' }}
                    >
                      {riskPieData.map(d => (
                        <Cell key={d.name} fill={d.color} stroke="none" style={{ outline: 'none' }} />
                      ))}
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
                    <Legend
                      wrapperStyle={{ fontSize: '11px', fontFamily: "'JetBrains Mono', monospace" }}
                      content={() => (
                        <div className="flex items-center justify-center gap-4 mt-2 flex-wrap text-[11px] font-mono">
                          {ALL_RISK_LEVELS.map(lvl => (
                            <div key={lvl} className="flex items-center gap-1.5">
                              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: RISK_COLORS[lvl] }} />
                              <span style={{ color: '#484640' }}>{lvl}</span>
                              <span className="font-bold text-[#1a1916]">({riskCounts[lvl] ?? 0})</span>
                            </div>
                          ))}
                        </div>
                      )}
                    />
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
