import React, { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  Compass,
  FileText,
  HelpCircle,
  Layers,
  MapPin,
  Shield,
  ShieldAlert,
  Calendar,
  ExternalLink,
  Check,
} from 'lucide-react';
import { AnomalyResult } from '../types';
import { mlService } from '../services/api';

interface AnomalyCardProps {
  anomaly: AnomalyResult;
  onStatusChange?: (id: number, status: string) => void;
}

export const AnomalyCard: React.FC<AnomalyCardProps> = ({ anomaly, onStatusChange }) => {
  const [expanded, setExpanded] = useState(false);
  const [acknowledged, setAcknowledged] = useState(anomaly.acknowledged ?? false);
  const [acking, setAcking] = useState(false);

  const handleAcknowledge = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!anomaly.id) return;
    setAcking(true);
    try {
      await mlService.acknowledgeAnomaly(anomaly.id);
      setAcknowledged(true);
      if (onStatusChange) onStatusChange(anomaly.id, 'ACKNOWLEDGED');
    } catch (err) {
      console.error('Failed to acknowledge anomaly:', err);
    } finally {
      setAcking(false);
    }
  };

  const iso = anomaly.isolation_score ?? anomaly.anomaly_score ?? 0;
  const isOutlier = (anomaly.is_anomaly ?? true) || iso < 0;
  const severity = anomaly.operational_severity || (iso < -0.1 ? 'CRITICAL' : iso < -0.05 ? 'HIGH' : 'MEDIUM');

  const severityBadge = {
    CRITICAL: 'bg-rose-50 text-rose-800 border-rose-300',
    HIGH:     'bg-orange-50 text-orange-800 border-orange-300',
    MEDIUM:   'bg-amber-50 text-amber-800 border-amber-300',
    LOW:      'bg-emerald-50 text-emerald-800 border-emerald-300',
  }[severity] || 'bg-amber-50 text-amber-800 border-amber-300';

  const evidenceBadge = {
    HIGH:         'bg-emerald-50 text-emerald-700 border-emerald-200',
    MEDIUM:       'bg-amber-50 text-amber-700 border-amber-200',
    LOW:          'bg-orange-50 text-orange-700 border-orange-200',
    INSUFFICIENT: 'bg-rose-50 text-rose-700 border-rose-200',
  }[anomaly.evidence_strength || 'INSUFFICIENT'];

  return (
    <div
      className={`border rounded-sm transition-all bg-white shadow-sm hover:shadow-md ${
        isOutlier ? 'border-amber-300/80' : 'border-[#e5e0d8]'
      }`}
    >
      {/* Header bar */}
      <div className="p-4 cursor-pointer" onClick={() => setExpanded((v) => !v)}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
          <div className="flex items-start gap-2.5 min-w-0">
            {isOutlier ? (
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            ) : (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            )}
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h4 className="text-sm font-bold text-[#1a1916]">
                  {anomaly.species?.common_name || 'Conservation Target'}{' '}
                  {anomaly.species?.scientific_name && (
                    <span className="text-xs font-normal italic text-[#77746c]">
                      ({anomaly.species.scientific_name})
                    </span>
                  )}
                </h4>
                <span className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 border rounded-sm ${severityBadge}`}>
                  {severity} SEVERITY
                </span>
                {acknowledged && (
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-sm font-semibold">
                    ACKNOWLEDGED
                  </span>
                )}
              </div>
              <p className="text-xs font-mono text-[#94918a] mt-0.5 flex items-center gap-2">
                <span>{anomaly.anomaly_type?.replace(/_/g, ' ') || 'SPATIAL-TEMPORAL OUTLIER'}</span>
                {anomaly.location?.name && (
                  <>
                    <span>&middot;</span>
                    <span className="flex items-center gap-1 text-[#77746c]">
                      <MapPin className="w-3 h-3 text-emerald-700" />
                      {anomaly.location.name}
                    </span>
                  </>
                )}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 self-end sm:self-center shrink-0">
            <div className="text-right">
              <span className="text-[10px] font-mono text-[#94918a] uppercase block">Isolation Score</span>
              <span
                className={`text-sm font-mono font-bold ${
                  iso < -0.05 ? 'text-rose-600' : iso < 0 ? 'text-amber-600' : 'text-emerald-600'
                }`}
                title="Isolation Forest decision score: negative = outlier, positive = inlier"
              >
                {typeof iso === 'number' ? iso.toFixed(4) : '—'}
              </span>
            </div>
            <ChevronDown className={`w-4 h-4 text-[#94918a] transition-transform ${expanded ? 'rotate-180' : ''}`} />
          </div>
        </div>

        {/* Causal explanation */}
        <p className="text-xs text-[#1a1916] bg-[#fdfaf5] p-3 rounded-sm border border-[#e5e0d8] leading-relaxed">
          {anomaly.explanation}
        </p>

        {/* Actionable Metrics Grid: What changed? Against what baseline? Over what window? */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3 text-xs font-mono">
          <div className="bg-[#fdfaf5] p-2.5 rounded-sm border border-[#e5e0d8]">
            <span className="text-[10px] text-[#94918a] uppercase block">Observed (30d)</span>
            <span className="text-xs font-bold text-[#1a1916]">
              {typeof anomaly.observation_count === 'number' ? `${anomaly.observation_count} records` : '—'}
            </span>
          </div>

          <div className="bg-[#fdfaf5] p-2.5 rounded-sm border border-[#e5e0d8]">
            <span className="text-[10px] text-[#94918a] uppercase block">Expected Baseline</span>
            <span className="text-xs font-bold text-[#1a1916]">
              {typeof anomaly.expected_baseline === 'number' ? `${anomaly.expected_baseline} / 30d` : 'Historical 90d avg'}
            </span>
          </div>

          <div className="bg-[#fdfaf5] p-2.5 rounded-sm border border-[#e5e0d8]">
            <span className="text-[10px] text-[#94918a] uppercase block">Deviation</span>
            <span
              className={`text-xs font-bold ${
                typeof anomaly.deviation_percentage === 'number' && anomaly.deviation_percentage < 0
                  ? 'text-rose-600'
                  : 'text-emerald-700'
              }`}
            >
              {typeof anomaly.deviation_percentage === 'number'
                ? `${anomaly.deviation_percentage > 0 ? '+' : ''}${anomaly.deviation_percentage}%`
                : 'Significant Outlier'}
            </span>
          </div>

          <div className="bg-[#fdfaf5] p-2.5 rounded-sm border border-[#e5e0d8]">
            <span className="text-[10px] text-[#94918a] uppercase block">Evidence Strength</span>
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-sm border inline-block mt-0.5 ${evidenceBadge}`}>
              {anomaly.evidence_strength || 'EVALUATED'}
            </span>
          </div>
        </div>
      </div>

      {/* Expanded deep-dive drawer */}
      {expanded && (
        <div className="p-4 pt-0 space-y-4 border-t border-[#e5e0d8] bg-[#faf8f5]/50 animate-fade-slide-in">
          {/* 1. Score Interpretation */}
          {anomaly.score_interpretation && (
            <div className="mt-3 p-3 bg-white rounded-sm border border-[#e5e0d8]">
              <h5 className="text-[10px] font-mono uppercase tracking-wider font-bold text-[#94918a] mb-1">
                Model Score Interpretation
              </h5>
              <p className="text-xs text-[#77746c] leading-relaxed">
                {anomaly.score_interpretation} (Note: Isolation Forest produces tree isolation depth scores, not class probabilities).
              </p>
            </div>
          )}

          {/* 2. Working Hypotheses (What might explain this?) */}
          {anomaly.hypotheses && anomaly.hypotheses.length > 0 && (
            <div className="p-3 bg-white rounded-sm border border-[#e5e0d8]">
              <h5 className="text-[10px] font-mono uppercase tracking-wider font-bold text-[#94918a] mb-2 flex items-center gap-1.5">
                <HelpCircle className="w-3.5 h-3.5 text-amber-600" />
                Working Ecological &amp; Operational Hypotheses
              </h5>
              <ul className="space-y-1 text-xs text-[#77746c]">
                {anomaly.hypotheses.map((hypo, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-amber-600 font-bold">&bull;</span>
                    <span>{hypo}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 3. Investigation Guidance (What should an officer or researcher investigate next?) */}
          {anomaly.investigation_guidance && (
            <div className="p-3 bg-emerald-50/60 rounded-sm border border-emerald-200">
              <h5 className="text-[10px] font-mono uppercase tracking-wider font-bold text-emerald-800 mb-1 flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-emerald-700" />
                Actionable Investigation Protocol
              </h5>
              <p className="text-xs text-emerald-900 leading-relaxed font-sans">
                {anomaly.investigation_guidance}
              </p>
            </div>
          )}

          {/* 4. Ground-truth Evidence (Related scientific documents and threats) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {anomaly.related_threats && anomaly.related_threats.length > 0 && (
              <div className="p-3 bg-white rounded-sm border border-[#e5e0d8]">
                <h5 className="text-[10px] font-mono uppercase tracking-wider font-bold text-[#94918a] mb-2 flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-600" /> Co-occurring Threats
                </h5>
                <div className="space-y-1">
                  {anomaly.related_threats.map((t, idx) => (
                    <div key={idx} className="flex items-center justify-between text-xs py-1 border-b border-[#f0ede6] last:border-b-0">
                      <span className="text-[#1a1916] truncate">{t.category_name}</span>
                      <span className="font-mono text-[10px] text-rose-600 font-semibold">{t.mention_count} docs</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {anomaly.related_documents && anomaly.related_documents.length > 0 && (
              <div className="p-3 bg-white rounded-sm border border-[#e5e0d8]">
                <h5 className="text-[10px] font-mono uppercase tracking-wider font-bold text-[#94918a] mb-2 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-emerald-700" /> Corroborating Intelligence
                </h5>
                <div className="space-y-1">
                  {anomaly.related_documents.slice(0, 3).map((d) => (
                    <div key={d.id} className="text-xs py-1 border-b border-[#f0ede6] last:border-b-0">
                      <p className="text-[#1a1916] font-medium truncate" title={d.title}>{d.title}</p>
                      <span className="text-[10px] font-mono text-[#94918a]">Doc ID #{d.id}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Action Footer */}
          <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-[10px] font-mono text-[#94918a]">
            <span>Fingerprint: {anomaly.fingerprint || 'fp-auto'} &middot; Window: 30d</span>
            {!acknowledged ? (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleAcknowledge}
                  disabled={acking}
                  className="px-3 py-1.5 bg-[#1a1916] hover:bg-[#2c2b26] disabled:opacity-50 text-white rounded-sm font-bold flex items-center gap-1.5 transition-colors"
                >
                  <Check className="w-3 h-3" />
                  {acking ? 'UPDATING...' : 'ACKNOWLEDGE FOR FIELD AUDIT'}
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-emerald-700 font-semibold flex-wrap">
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Acknowledged by Intelligence Desk
                </span>
                {anomaly.acknowledged_at && (
                  <span className="text-[9px] text-[#77746c] font-normal">
                    ({new Date(anomaly.acknowledged_at).toLocaleDateString()})
                  </span>
                )}
                {anomaly.investigation_notes && (
                  <span className="text-[10px] text-stone-700 italic block w-full mt-1">
                    Note: "{anomaly.investigation_notes}"
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

