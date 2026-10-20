import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface DemoBannerProps {
  message?: string;
}

export const DemoBanner: React.FC<DemoBannerProps> = ({
  message = 'DEMO / SAMPLE DATA — Simulated conservation intelligence data for academic demonstration.',
}) => {
  return (
    <div className="bg-amber-900/40 border border-amber-500/30 text-amber-200 px-4 py-2 rounded-lg text-xs font-mono flex items-center gap-2 mb-4">
      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
      <span>{message}</span>
    </div>
  );
};
