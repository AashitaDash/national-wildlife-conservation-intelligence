import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { PawPrint, MapPin, TrendingUp, ArrowLeft, X } from 'lucide-react';
import { speciesService, mlService, observationService } from '../services/api';
import { Species, RiskScoreResult, Observation } from '../types';
import { DemoBanner } from '../components/DemoBanner';
import { RiskBadge, RiskIndicatorLabel } from '../components/RiskBadge';
import { EmptyState } from '../components/EmptyState';
import { errorMessage } from '../utils/format';
import { MapView, MapLegend } from '../components/MapView';
import { Skeleton } from '../components/Skeleton';

// ── Shared styles ───────────────────────────────────────
const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
  <div
    className={`bg-white border ${className}`}
    style={{ borderColor: '#e5e0d8', borderRadius: '3px', boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}
  >
    {children}
  </div>
);

const SectionLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <p className="font-mono text-[10px] font-semibold tracking-widest uppercase mb-3" style={{ color: '#94918a' }}>
    {children}
  </p>
);

const IUCN_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  CR: { bg: '#fff1f0', text: '#b91c1c', border: '#fca5a5' },
  EN: { bg: '#fff7ed', text: '#c2410c', border: '#fdba74' },
  VU: { bg: '#fffbeb', text: '#b45309', border: '#fcd34d' },
  NT: { bg: '#fefce8', text: '#854d0e', border: '#fde68a' },
  LC: { bg: '#f0fdf4', text: '#15803d', border: '#86efac' },
};

// ─────────────────────────────────────────────────────────
export const SpeciesDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [species, setSpecies]       = useState<Species | null>(null);
  const [riskData, setRiskData]     = useState<RiskScoreResult | null>(null);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState<string | null>(null);
  const [notFound, setNotFound]     = useState(false);
  const [riskError, setRiskError]   = useState<string | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [selectedStateName, setSelectedStateName] = useState<string | null>(null);
  const [obsError, setObsError]     = useState<string | null>(null);

  const loadDetails = async () => {
    const speciesId = Number(id);
    if (!Number.isInteger(speciesId) || speciesId < 1) { setNotFound(true); setLoading(false); return; }
    setLoading(true); setError(null); setNotFound(false); setRiskError(null); setObsError(null);
    setSelectedStateName(null);
    setSpecies(null); setRiskData(null); setObservations([]);

    const [spRes, riskRes, obsRes] = await Promise.allSettled([
      speciesService.getSpeciesById(speciesId),
      mlService.getSpeciesRisk(speciesId),
      observationService.getObservations({ species_id: speciesId }),
    ]);

    if (spRes.status === 'fulfilled') setSpecies(spRes.value);
    else { if ((spRes.reason as any)?.response?.status === 404) setNotFound(true); else setError(errorMessage(spRes.reason, 'Could not load this species')); }
    if (riskRes.status === 'fulfilled') setRiskData(riskRes.value); else setRiskError(errorMessage(riskRes.reason, 'Risk indicator unavailable'));
    if (obsRes.status === 'fulfilled') setObservations(obsRes.value.items); else setObsError(errorMessage(obsRes.reason, 'Observation data unavailable'));
    setLoading(false);
  };

  useEffect(() => { loadDetails(); }, [id]); // eslint-disable-line

  const backLink = (
    <Link
      to="/species"
      className="inline-flex items-center gap-1.5 text-xs font-mono transition-colors mb-6"
      style={{ color: '#94918a' }}
      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = '#13843a'; }}
      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = '#94918a'; }}
    >
      <ArrowLeft className="w-3.5 h-3.5" />
      BACK TO SPECIES REGISTRY
    </Link>
  );

  if (loading) {
    return (
      <div className="space-y-5 animate-fade-slide-in">
        <Skeleton className="h-3 w-40" />
        <Card className="p-6"><Skeleton className="h-7 w-1/2 mb-2" /><Skeleton className="h-3 w-1/3" /></Card>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <Skeleton className="lg:col-span-2 h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  if (notFound || error || !species) {
    return (
      <div className="space-y-5">
        {backLink}
        <EmptyState
          variant={notFound ? 'empty' : 'error'}
          title={notFound ? 'Species not found' : 'Species profile unavailable'}
          description={notFound ? 'No species exists with this identifier.' : error ?? undefined}
          actionLabel={notFound ? undefined : 'Retry'}
          onAction={notFound ? undefined : loadDetails}
        />
      </div>
    );
  }

  const iucnStyle = species.conservation_status ? (IUCN_STYLES[species.conservation_status] ?? IUCN_STYLES['LC']) : null;

  return (
    <div className="space-y-5 animate-fade-slide-in">
      <DemoBanner />
      {backLink}

      {/* ── Species profile header ── */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="flex flex-col sm:flex-row gap-6 items-start w-full">
            {species.image_url ? (
              <div className="w-full sm:w-48 h-48 shrink-0 bg-[#f0ede6] overflow-hidden" style={{ borderRadius: '3px' }}>
                <img src={species.image_url} alt={species.common_name} className="w-full h-full object-cover" />
              </div>
            ) : (
              <div className="w-full sm:w-48 h-48 shrink-0 bg-[#f0ede6] flex items-center justify-center text-[#94918a] text-[10px] tracking-widest font-mono" style={{ borderRadius: '3px' }}>
                NO IMAGE
              </div>
            )}
            <div className="flex-1 min-w-0">
              {/* Taxonomy breadcrumb */}
            <div className="flex items-center gap-2 mb-2">
              {species.taxonomic_class && (
                <span className="font-mono text-[10px] tracking-widest uppercase" style={{ color: '#94918a' }}>
                  {species.taxonomic_class}
                </span>
              )}
              {species.taxonomic_class && species.conservation_status && (
                <span style={{ color: '#d6d3d1' }}>·</span>
              )}
              {species.conservation_status && iucnStyle && (
                <span
                  className="font-mono text-[10px] font-bold px-1.5 py-0.5"
                  style={{ backgroundColor: iucnStyle.bg, color: iucnStyle.text, border: `1px solid ${iucnStyle.border}`, borderRadius: '2px', letterSpacing: '0.08em' }}
                >
                  IUCN {species.conservation_status}
                </span>
              )}
            </div>
            <h1
              className="font-serif text-3xl font-bold mb-1"
              style={{ color: '#1a1916', fontFamily: "'Newsreader', Georgia, serif" }}
            >
              {species.common_name}
            </h1>
            <p className="font-serif text-base italic mb-4" style={{ color: '#77746c' }}>
              {species.scientific_name}
            </p>
            <div>
              <span className="font-mono text-[10px] tracking-widest uppercase block mb-1" style={{ color: '#94918a' }}>RECORDED OBSERVATIONS</span>
              <span className="font-mono text-lg" style={{ color: '#1a1916' }}>{observations.length}</span>
            </div>
            </div>
          </div>

          {/* Risk indicator panel */}
          {observations.length === 0 ? (
            <div
              className="shrink-0 border p-4"
              style={{ borderColor: '#e5e0d8', borderRadius: '3px', backgroundColor: '#fdfcfa', minWidth: '200px' }}
            >
              <div className="font-mono text-[10px] font-semibold tracking-widest uppercase mb-2" style={{ color: '#94918a' }}>RISK ASSESSMENT</div>
              <p className="text-sm font-medium mb-1" style={{ color: '#1a1916' }}>Insufficient observation data</p>
            </div>
          ) : riskData ? (
            <div
              className="shrink-0 border p-4"
              style={{ borderColor: '#e5e0d8', borderRadius: '3px', backgroundColor: '#fdfcfa', minWidth: '200px' }}
            >
              <RiskIndicatorLabel className="block mb-2" />
              <div className="flex items-center gap-3">
                <RiskBadge level={riskData.risk_level} score={riskData.risk_score} size="lg" showGauge />
                <div>
                  <span className="font-mono text-[10px] block" style={{ color: '#94918a' }}>DECISION-SUPPORT</span>
                  <span className="font-mono text-[10px] block" style={{ color: '#94918a' }}>METRIC</span>
                </div>
              </div>
            </div>
          ) : riskError ? (
            <div className="shrink-0 border p-3 text-[10px] font-mono" style={{ borderColor: '#e5e0d8', borderRadius: '3px', color: '#94918a', maxWidth: '200px' }}>
              Risk indicator unavailable
            </div>
          ) : null}
        </div>
      </Card>

      {/* ── Official Conservation Status section ── */}
      {species.conservation_status && (
        <Card className="p-5">
          <SectionLabel>OFFICIAL CONSERVATION STATUS</SectionLabel>
          <div className="flex items-start gap-4">
            {iucnStyle && (
              <span
                className="font-mono text-lg font-bold px-3 py-1.5 shrink-0"
                style={{ backgroundColor: iucnStyle.bg, color: iucnStyle.text, border: `1px solid ${iucnStyle.border}`, borderRadius: '3px' }}
              >
                {species.conservation_status}
              </span>
            )}
            <div>
              <p className="text-sm font-medium mb-1" style={{ color: '#1a1916' }}>
                IUCN Red List — {species.conservation_status === 'CR' ? 'Critically Endangered' : species.conservation_status === 'EN' ? 'Endangered' : species.conservation_status === 'VU' ? 'Vulnerable' : species.conservation_status === 'LC' ? 'Least Concern' : species.conservation_status}
              </p>
              <p className="text-xs" style={{ color: '#77746c' }}>
                This is the official IUCN Red List conservation status. This is separate from the platform-generated risk indicator above.
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* ── Description + Map + Risk breakdown ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Description + Map */}
        <Card className="lg:col-span-2 p-5 space-y-5">
          <div>
            <SectionLabel>SPECIES OVERVIEW</SectionLabel>
            <p className="text-sm leading-relaxed" style={{ color: '#3d3b36' }}>
              {species.description || 'No ecological description available.'}
            </p>
          </div>

          <div style={{ borderTop: '1px solid #f0ede6', paddingTop: '20px' }}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
              <SectionLabel>GEOGRAPHIC DISTRIBUTION</SectionLabel>
              {selectedStateName && (
                <div className="flex items-center gap-2 px-2.5 py-0.5 bg-[#f0f9f4] border border-[#13843a] rounded text-[11px] font-mono mb-2">
                  <span className="text-[#1a1916] font-semibold">Drilldown State: {selectedStateName}</span>
                  <button
                    onClick={() => setSelectedStateName(null)}
                    className="text-[#dc2626] hover:text-[#991b1b] transition-colors"
                    title="Clear state drilldown"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>
            {obsError ? (
              <EmptyState variant="error" title="Observation locations unavailable" description={obsError} actionLabel="Retry" onAction={loadDetails} />
            ) : observations.length === 0 ? (
              <EmptyState icon={MapPin} title="No recorded observations" description="Observation locations will appear when records exist." />
            ) : (
              <>
                <p className="text-[11px] text-[#77746c] mb-2 font-mono">
                  Click any state boundary to zoom and drill down into that state's distribution.
                </p>
                <MapLegend />
                <div className="mt-2">
                  <MapView
                    observations={observations}
                    selectedStateName={selectedStateName}
                    onStateSelect={(st) => setSelectedStateName((prev) => (prev?.toLowerCase() === st.toLowerCase() ? null : st))}
                    height="260px"
                  />
                </div>
              </>
            )}
          </div>
        </Card>

        {/* Risk factor breakdown */}
        <Card className="p-5 flex flex-col">
          <SectionLabel>PLATFORM RISK ANALYSIS</SectionLabel>
          {observations.length === 0 ? (
            <div className="flex-1 mt-2">
              <p className="text-sm font-medium mb-2" style={{ color: '#1a1916' }}>Insufficient observation data</p>
              <p className="text-xs leading-relaxed" style={{ color: '#77746c' }}>
                No observation records are currently available for this species,
                so a platform-generated risk indicator is not displayed.
              </p>
            </div>
          ) : (
            <>
              <p className="font-mono text-[10px] mb-4 leading-relaxed" style={{ color: '#94918a' }}>
                Random Forest composite risk score. Not an official IUCN designation.
              </p>

              {riskData?.factor_breakdown ? (
                <div className="space-y-2 flex-1">
                  {Object.entries(riskData.factor_breakdown).map(([k, v]) => (
                    <div key={k} className="p-2.5 border" style={{ borderColor: '#f0ede6', borderRadius: '3px', backgroundColor: '#fdfcfa' }}>
                      <div className="flex justify-between mb-1.5 text-xs">
                        <span className="font-medium capitalize" style={{ color: '#3d3b36' }}>{k.replace(/_/g, ' ')}</span>
                        <span className="font-mono font-bold" style={{ color: '#b91c1c' }}>+{v.toFixed(1)}</span>
                      </div>
                      <div className="w-full h-1" style={{ backgroundColor: '#f0ede6', borderRadius: '1px' }}>
                        <div
                          className="h-full"
                          style={{ width: `${Math.min(100, (v / 25) * 100)}%`, backgroundColor: '#dc2626', borderRadius: '1px' }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs font-mono flex-1" style={{ color: '#94918a' }}>
                  {riskError ?? 'No factor breakdown available.'}
                </p>
              )}

              <div
                className="mt-4 p-3 text-[10px] font-mono leading-relaxed"
                style={{ backgroundColor: '#fdfcfa', border: '1px solid #e5e0d8', borderRadius: '3px', color: '#77746c' }}
              >
                {riskData?.disclaimer ?? 'Platform-generated decision-support indicator. Not an official IUCN Red List designation.'}
              </div>
            </>
          )}
        </Card>
      </div>
    </div>
  );
};
