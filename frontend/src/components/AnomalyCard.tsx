import React from 'react';
import { Activity, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { AnomalyResult } from '../types';

interface AnomalyCardProps {
  anomaly: AnomalyResult;
}

export const AnomalyCard: React.FC<AnomalyCardProps> = ({ anomaly }) => {
  return (
    <div
      className={`rounded-xl border p-4 backdrop-blur-sm transition-all ${
        anomaly.is_anomaly
          ? 'bg-rose-950/20 border-rose-500/40 shadow-lg shadow-rose-950/20'
          : 'bg-charcoal-900/40 border-charcoal-800'
      }`}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          {anomaly.is_anomaly ? (
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 animate-pulse" />
          ) : (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          )}
          <div>
            <h4 className="text-sm font-semibold text-earthy-100">
              {anomaly.is_anomaly ? 'Telemetry / Spatial Anomaly Detected' : 'Normal Baseline Operations'}
            </h4>
            {anomaly.anomaly_type && (
              <span className="text-xs font-mono text-rose-300/80">{anomaly.anomaly_type}</span>
            )}
          </div>
        </div>

        <div className="text-right">
          <span className="text-xs text-earthy-400 block font-mono">Isolation Score</span>
          <span
            className={`font-mono text-sm font-bold ${
              (anomaly.is_anomaly ?? true) ? 'text-rose-400' : 'text-emerald-400'
            }`}
          >
            {typeof (anomaly.isolation_score ?? anomaly.anomaly_score) === 'number' 
              ? (anomaly.isolation_score ?? anomaly.anomaly_score)!.toFixed(3) 
              : '—'}
          </span>
        </div>
      </div>

      {anomaly.species && (
        <div className="mb-3 px-3 py-2 bg-charcoal-900/50 rounded-md border border-charcoal-800">
          <div className="text-xs font-semibold text-earthy-100 flex justify-between">
            <span>{anomaly.species.common_name}</span>
            <span className="text-earthy-400 italic">{anomaly.species.scientific_name}</span>
          </div>
          {anomaly.location && (
            <div className="text-[11px] text-earthy-300 mt-1">Location: {anomaly.location.name}</div>
          )}
        </div>
      )}

      <p className="text-xs text-earthy-300 leading-relaxed bg-charcoal-950/40 p-2.5 rounded-lg border border-charcoal-800/80 mb-3">
        {anomaly.explanation}
      </p>

      {anomaly.investigation_guidance && (
        <div className="mb-3 px-3 py-2 bg-cyan-950/20 rounded-md border border-cyan-900/40">
          <div className="text-xs font-semibold text-cyan-400 mb-1">Investigation Guidance</div>
          <div className="text-xs text-cyan-200/80 leading-relaxed">{anomaly.investigation_guidance}</div>
        </div>
      )}

      {(anomaly.related_threats && anomaly.related_threats.length > 0) && (
        <div className="mb-3">
          <div className="text-[11px] uppercase tracking-wider text-earthy-400 font-semibold mb-1 border-b border-charcoal-800 pb-1">
            Related Threats
          </div>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {anomaly.related_threats.map((threat, idx) => (
              <span key={idx} className="inline-flex items-center gap-1 bg-rose-950/40 border border-rose-900/60 text-rose-300 text-[10px] px-2 py-0.5 rounded-full">
                {threat.category_name} <span className="opacity-60 text-[9px]">({threat.mention_count})</span>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-2 text-xs font-mono mb-2">
        {anomaly.evidence_strength && (
          <div className="bg-charcoal-900/60 p-2 rounded border border-charcoal-800">
            <span className="text-earthy-400 block text-[10px] uppercase">Evidence Strength</span>
            <span className={`font-semibold ${
              anomaly.evidence_strength === 'HIGH' ? 'text-rose-400' :
              anomaly.evidence_strength === 'MEDIUM' ? 'text-amber-400' :
              'text-earthy-300'
            }`}>{anomaly.evidence_strength}</span>
          </div>
        )}
        {typeof anomaly.observation_count === 'number' && (
          <div className="bg-charcoal-900/60 p-2 rounded border border-charcoal-800">
            <span className="text-earthy-400 block text-[10px] uppercase">Observations (30d)</span>
            <span className="text-earthy-200 font-semibold">{anomaly.observation_count}</span>
          </div>
        )}
      </div>

      {anomaly.metrics && Object.keys(anomaly.metrics).length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
          {Object.entries(anomaly.metrics).map(([key, val]) => (
            <div key={key} className="bg-charcoal-900/60 p-2 rounded border border-charcoal-800">
              <span className="text-earthy-400 block text-[10px] capitalize">
                {key.replace(/_/g, ' ')}
              </span>
              <span className="text-earthy-200 font-semibold">{String(val)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
