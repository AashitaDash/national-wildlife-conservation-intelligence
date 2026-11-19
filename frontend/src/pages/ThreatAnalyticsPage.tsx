import React, { useEffect, useState } from 'react';
import { TrendingUp, ShieldAlert, AlertTriangle, Filter } from 'lucide-react';
import { mlService, speciesService } from '../services/api';
import { RiskScoreResult, AnomalyResult } from '../types';
import { DemoBanner } from '../components/DemoBanner';
import { RiskBadge, RiskIndicatorLabel } from '../components/RiskBadge';
import { errorMessage } from '../utils/format';
import { AnomalyCard } from '../components/AnomalyCard';
import { SkeletonRows } from '../components/Skeleton';
import { EmptyState } from '../components/EmptyState';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';

type RiskFilter = 'ALL' | 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
const RISK_COLORS: Record<string, string> = { CRITICAL: '#dc2626', HIGH: '#ea580c', MEDIUM: '#d97706', LOW: '#16a34a' };

const FILTER_OPTIONS: { value: RiskFilter; label: string }[] = [
  { value: 'ALL',      label: 'ALL LEVELS' },
  { value: 'CRITICAL', label: 'CRITICAL'   },
  { value: 'HIGH',     label: 'HIGH'       },
  { value: 'MEDIUM',   label: 'MEDIUM'     },
  { value: 'LOW',      label: 'LOW'        },
];

const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div className={`bg-white border ${className}`} style={{ borderColor: '#e5e0d8', borderRadius: '3px', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}>
    {children}
  </div>
);

const SectionLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <p className="font-mono text-[10px] font-semibold tracking-widest uppercase mb-3" style={{ color: '#94918a' }}>
    {children}
  </p>
);

export const ThreatAnalyticsPage: React.FC = () => {
  const [riskItems, setRiskItems]       = useState<RiskScoreResult[]>([]);
  const [anomalyItems, setAnomalyItems] = useState<AnomalyResult[]>([]);
  const [loading, setLoading]           = useState(true);
  const [error, setError]               = useState<string | null>(null);
  const [speciesNames, setSpeciesNames] = useState<Record<number, string>>({});
  const [riskFilter, setRiskFilter]     = useState<RiskFilter>('ALL');

  const loadAnalytics = async () => {
    setLoading(true); setError(null);
    try {
      const [riskRes, anomalyRes, speciesRes] = await Promise.allSettled([
        mlService.getRiskScores(), mlService.getAnomalies(), speciesService.getSpeciesList(),
      ]);
      if (riskRes.status   === 'rejected') throw riskRes.reason;
      if (anomalyRes.status === 'rejected') throw anomalyRes.reason;
      setRiskItems(riskRes.value.items);
      setAnomalyItems(anomalyRes.value.items);
      if (speciesRes.status === 'fulfilled') {
        setSpeciesNames(Object.fromEntries(speciesRes.value.items.map(sp => [sp.id, sp.common_name])));
      }
    } catch (err) {
      setError(errorMessage(err, 'Could not load threat analytics'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAnalytics(); }, []);

  const nameFor = (item: RiskScoreResult): string =>
    item.species_name || (item.species_id !== undefined ? speciesNames[item.species_id] || `Species #${item.species_id}` : 'Unknown');

  const filtered  = riskFilter === 'ALL' ? riskItems : riskItems.filter(r => r.risk_level === riskFilter);
  const chartData = filtered.map(item => ({ name: nameFor(item).split('(')[0].trim(), score: item.risk_score, level: item.risk_level }));

  return (
    <div className="space-y-6 animate-fade-slide-in">
      <DemoBanner />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <p className="font-mono text-[10px] tracking-widest uppercase font-semibold mb-1" style={{ color: '#dc2626' }}>
            ML RISK ANALYTICS
          </p>
          <h1 className="font-serif text-3xl font-bold" style={{ color: '#1a1916', fontFamily: "'Newsreader', Georgia, serif" }}>
            Threat Analytics
          </h1>
          <p className="text-sm mt-1" style={{ color: '#77746c' }}>
            Random Forest vulnerability classification & Isolation Forest observation/spatial anomaly detection.
          </p>
        </div>

        {/* Filter chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <Filter className="w-3.5 h-3.5 shrink-0" style={{ color: '#94918a' }} />
          {FILTER_OPTIONS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setRiskFilter(value)}
              className="px-2.5 py-1 font-mono text-[10px] font-semibold tracking-widest transition-all"
              style={{
                borderRadius: '3px',
                border: `1px solid ${riskFilter === value ? '#dc2626' : '#e5e0d8'}`,
                backgroundColor: riskFilter === value ? '#fff1f0' : '#fff',
                color: riskFilter === value ? '#dc2626' : '#94918a',
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <SkeletonRows count={4} />
      ) : error ? (
        <EmptyState variant="error" title="Threat analytics unavailable" description={error} actionLabel="Retry" onAction={loadAnalytics} />
      ) : (
        <div className="space-y-5">
          {/* Risk score chart */}
          <Card className="p-5">
            <SectionLabel>COMPARATIVE ML RISK SCORES</SectionLabel>
            <RiskIndicatorLabel className="block -mt-1 mb-3" />
            {chartData.length === 0 ? (
              <EmptyState icon={ShieldAlert} title="No species at this risk level" description="Try a different filter." />
            ) : (
              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <XAxis dataKey="name" stroke="#94918a" fontSize={10} fontFamily="JetBrains Mono, monospace" />
                    <YAxis domain={[0, 100]} stroke="#94918a" fontSize={10} fontFamily="JetBrains Mono, monospace" />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#fff', borderColor: '#e5e0d8', borderRadius: '3px', fontSize: '11px', fontFamily: "'JetBrains Mono', monospace" }}
                      cursor={{ fill: 'rgba(0,0,0,0.03)' }}
                    />
                    <Bar dataKey="score" name="Risk Score" radius={[2, 2, 0, 0]}>
                      {chartData.map((entry, idx) => <Cell key={idx} fill={RISK_COLORS[entry.level] || '#dc2626'} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          {/* Risk items + anomalies */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Risk assessments */}
            <Card className="p-5">
              <SectionLabel>RANDOM FOREST SPECIES ASSESSMENTS</SectionLabel>
              <RiskIndicatorLabel className="block -mt-1 mb-4" />
              {filtered.length === 0 ? (
                <p className="text-xs font-mono py-4" style={{ color: '#94918a' }}>No species at this risk level.</p>
              ) : (
                <div className="space-y-2">
                  {filtered.map((item, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 border animate-fade-slide-in"
                      style={{ borderColor: '#f0ede6', borderRadius: '3px', backgroundColor: '#fdfcfa', animationDelay: `${idx * 50}ms` }}
                    >
                      <div className="min-w-0">
                        <h4 className="text-xs font-semibold truncate" style={{ color: '#1a1916' }}>{nameFor(item)}</h4>
                        {typeof item.confidence === 'number' && (
                          <span className="font-mono text-[10px]" style={{ color: '#94918a' }}>
                            Confidence: {(item.confidence * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                      <RiskBadge level={item.risk_level} score={item.risk_score} size="sm" />
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* Anomalies */}
            <Card className="p-5">
              <SectionLabel>ISOLATION FOREST TELEMETRY ANOMALIES</SectionLabel>
              {anomalyItems.length === 0 ? (
                <p className="text-xs font-mono py-4" style={{ color: '#94918a' }}>No telemetry anomalies detected.</p>
              ) : (
                <div className="space-y-2">
                  {anomalyItems.map((anom, idx) => (
                    <AnomalyCard key={anom.id ?? idx} anomaly={{ ...anom, is_anomaly: anom.is_anomaly ?? true }} />
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

