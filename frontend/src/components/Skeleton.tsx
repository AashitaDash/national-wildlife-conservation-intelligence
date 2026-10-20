import React from 'react';

interface SkeletonProps {
  className?: string;
}

/** A single pulsing placeholder block matching the platform's slate theme. */
export const Skeleton: React.FC<SkeletonProps> = ({ className = 'h-4 w-full' }) => (
  <div className={`animate-skeleton bg-charcoal-800/80 rounded-md ${className}`} />
);

/** A grid of card-shaped skeletons, for catalog / list pages while data loads. */
export const SkeletonCardGrid: React.FC<{ count?: number; className?: string }> = ({
  count = 6,
  className = 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4',
}) => (
  <div className={className}>
    {Array.from({ length: count }).map((_, i) => (
      <div
        key={i}
        className="bg-charcoal-900/60 border border-charcoal-800 p-5 rounded-2xl space-y-3"
      >
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-3 w-1/3" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-5/6" />
        <Skeleton className="h-8 w-full rounded-xl mt-2" />
      </div>
    ))}
  </div>
);

/** A stack of row-shaped skeletons, for lists such as alerts. */
export const SkeletonRows: React.FC<{ count?: number }> = ({ count = 4 }) => (
  <div className="space-y-3">
    {Array.from({ length: count }).map((_, i) => (
      <div key={i} className="bg-charcoal-900/60 border border-charcoal-800 p-4 rounded-xl space-y-2">
        <Skeleton className="h-3.5 w-2/5" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-3/4" />
      </div>
    ))}
  </div>
);
