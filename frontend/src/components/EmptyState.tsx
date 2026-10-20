import React from 'react';
import { LucideIcon, Inbox, AlertCircle, RefreshCw } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  variant?: 'empty' | 'error';
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  variant = 'empty',
}) => {
  const Icon = icon || (variant === 'error' ? AlertCircle : Inbox);
  const isError = variant === 'error';

  return (
    <div
      className={`flex flex-col items-center justify-center text-center py-12 px-6 border border-[#d1cdbc] animate-fade-slide-in ${
        isError
          ? 'bg-[#fdfaf5] border-rose-500/50'
          : 'bg-[#fdfaf5]'
      }`}
    >
      <div
        className={`p-3 mb-3 border ${
          isError
            ? 'bg-rose-50 border-rose-200 text-rose-600'
            : 'bg-[#f0ede6] border-[#e6e2d6] text-[#0f0e0c]'
        }`}
      >
        <Icon className="w-5 h-5" />
      </div>
      <h3 className={`font-serif text-lg font-bold ${isError ? 'text-rose-700' : 'text-[#0f0e0c]'}`}>
        {title}
      </h3>
      {description && (
        <p className="text-sm font-sans text-neutral-600 mt-1 max-w-sm leading-relaxed">{description}</p>
      )}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="mt-4 inline-flex items-center gap-1.5 text-xs font-mono font-semibold px-4 py-2 bg-[#0f0e0c] text-white border border-[#0f0e0c] hover:bg-[#1a1917] transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>{actionLabel}</span>
        </button>
      )}
    </div>
  );
};
