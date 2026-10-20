import React from 'react';
import { Sparkles, BookOpen, Layers } from 'lucide-react';

interface NLPSummaryBoxProps {
  summary: string;
  sentenceCount?: number;
  embeddingDim?: number;
}

export const NLPSummaryBox: React.FC<NLPSummaryBoxProps> = ({
  summary,
  sentenceCount,
  embeddingDim = 384,
}) => {
  return (
    <div className="bg-gradient-to-br from-emerald-950/30 via-charcoal-900/60 to-charcoal-950 border border-emerald-500/30 rounded-xl p-4 shadow-xl">
      <div className="flex items-center justify-between mb-3 border-b border-emerald-500/20 pb-2.5">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <Sparkles className="w-4 h-4" />
          </div>
          <h3 className="text-sm font-semibold text-emerald-300 uppercase tracking-wider">
            AI-Generated Conservation Intelligence Summary
          </h3>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono text-emerald-400/70">
          {sentenceCount && (
            <span className="flex items-center gap-1">
              <BookOpen className="w-3.5 h-3.5" />
              {sentenceCount} Sentences
            </span>
          )}
          <span className="flex items-center gap-1 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/30">
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
            {embeddingDim}d pgvector
          </span>
        </div>
      </div>

      <p className="text-sm text-earthy-200 leading-relaxed font-sans bg-charcoal-950/60 p-3.5 rounded-lg border border-charcoal-800/80">
        {summary}
      </p>
    </div>
  );
};
