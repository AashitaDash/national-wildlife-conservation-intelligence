import React from 'react';
import { ShieldAlert, ShieldCheck, AlertCircle } from 'lucide-react';

export const RISK_INDICATOR_LABEL = 'Platform-generated risk indicator';

/** Small caption to sit next to any displayed risk score. Not an IUCN status or a scientific prediction. */
export const RiskIndicatorLabel: React.FC<{ className?: string }> = ({ className = '' }) => (
  <span className={`text-[10px] font-mono text-earthy-500 ${className}`}>{RISK_INDICATOR_LABEL}</span>
);

interface RiskBadgeProps {
  level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string;
  score?: number;
  size?: 'sm' | 'md' | 'lg';
  /** Show a small inline gauge bar next to the score. Only meaningful with size="lg". */
  showGauge?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, score, size = 'md', showGauge = false }) => {
  const getColors = () => {
    switch (level.toUpperCase()) {
      case 'CRITICAL':
        return {
          bg: 'bg-rose-950/60',
          border: 'border-rose-500/50',
          text: 'text-rose-400',
          bar: 'bg-rose-400',
          icon: ShieldAlert,
        };
      case 'HIGH':
        return {
          bg: 'bg-orange-950/60',
          border: 'border-orange-500/50',
          text: 'text-orange-400',
          bar: 'bg-orange-400',
          icon: AlertCircle,
        };
      case 'MEDIUM':
        return {
          bg: 'bg-amber-950/60',
          border: 'border-amber-500/50',
          text: 'text-amber-400',
          bar: 'bg-amber-400',
          icon: AlertCircle,
        };
      case 'LOW':
      default:
        return {
          bg: 'bg-emerald-950/60',
          border: 'border-emerald-500/50',
          text: 'text-emerald-400',
          bar: 'bg-emerald-400',
          icon: ShieldCheck,
        };
    }
  };

  const { bg, border, text, bar, icon: Icon } = getColors();

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 font-medium',
    md: 'text-sm px-3 py-1 font-semibold',
    lg: 'text-base px-4 py-2 font-bold',
  };

  return (
    <span className="inline-flex flex-col items-end gap-1">
      <span
        title={score !== undefined ? RISK_INDICATOR_LABEL : undefined}
        className={`inline-flex items-center gap-1.5 rounded-full border ${bg} ${border} ${text} ${sizeClasses[size]}`}
      >
        <Icon className={size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-5 h-5' : 'w-4 h-4'} />
        <span>{level.toUpperCase()}</span>
        {score !== undefined && (
          <span className="opacity-90 font-mono text-[0.85em] ml-0.5">({score.toFixed(1)}/100)</span>
        )}
      </span>
      {showGauge && size === 'lg' && score !== undefined && (
        <span className="w-28 h-1.5 rounded-full bg-charcoal-800 overflow-hidden block">
          <span
            className={`h-full block rounded-full ${bar} transition-all duration-500`}
            style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
          />
        </span>
      )}
    </span>
  );
};
