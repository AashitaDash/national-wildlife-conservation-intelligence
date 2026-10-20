import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Search as SearchIcon,
  Sparkles,
  FileText,
  PawPrint,
  MapPin,
  AlertTriangle,
  Layers,
  ArrowRight,
  Filter,
  CheckCircle2,
  X,
  SearchX,
} from 'lucide-react';
import { searchService } from '../services/api';
import { SearchResponse } from '../types';
import { DemoBanner } from '../components/DemoBanner';
import { RiskBadge } from '../components/RiskBadge';
import { NLPSummaryBox } from '../components/NLPSummaryBox';
import { AnomalyCard } from '../components/AnomalyCard';
import { MapView, MapLegend } from '../components/MapView';
import { EmptyState } from '../components/EmptyState';
import { RiskIndicatorLabel } from '../components/RiskBadge';
import { errorMessage } from '../utils/format';

export const SearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || 'elephant habitat loss Odisha';
  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [selectedStateName, setSelectedStateName] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    setError(null);
    setSelectedStateName(null);
    try {
      const data = await searchService.search(searchQuery);
      setResults(data);
    } catch (err: any) {
      console.error('Search API error:', err);
      setError(errorMessage(err, 'Search execution failed'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialQuery) {
      executeSearch(initialQuery);
    }
  }, []);

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchParams({ q: query });
    executeSearch(query);
  };

  const handlePresetClick = (presetQuery: string) => {
    setQuery(presetQuery);
    setSearchParams({ q: presetQuery });
    executeSearch(presetQuery);
  };

  const handleClear = () => {
    setQuery('');
    setResults(null);
    setSelectedStateName(null);
    setError(null);
    setSearchParams({});
  };

  return (
    <div className="space-y-6">
      <DemoBanner />

      {/* Search Bar Header */}
      <div className="bg-white border border-[#e5e0d8] p-6 rounded-sm shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <div className="p-1.5 rounded-sm bg-emerald-50 text-emerald-700 border border-emerald-200">
            <Sparkles className="w-4 h-4" />
          </div>
          <span className="text-[10px] font-mono font-bold text-emerald-700 uppercase tracking-wider">
            Multi-Facet Semantic Intelligence Search
          </span>
        </div>

        <form onSubmit={handleFormSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <SearchIcon className="w-5 h-5 text-[#94918a] absolute left-4 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. elephant habitat loss Odisha"
              className="w-full pl-12 pr-10 py-3 bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm text-sm text-[#1a1916] placeholder-[#94918a] focus:outline-none focus:border-emerald-700 focus:ring-1 focus:ring-emerald-700 font-serif transition-all"
            />
            {query && (
              <button
                type="button"
                onClick={handleClear}
                aria-label="Clear search"
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#94918a] hover:text-[#1a1916] transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-[#1a1916] hover:bg-[#2c2b26] disabled:opacity-50 text-white font-mono tracking-wide text-xs rounded-sm flex items-center gap-2 transition-all shrink-0 uppercase"
          >
            {loading ? 'SEARCHING VECTOR SPACE...' : 'SEARCH'}
          </button>
        </form>

        {/* Query presets */}
        <div className="flex items-center gap-2 mt-4 text-[10px] font-mono">
          <span className="text-[#94918a] uppercase tracking-wider">Sample Queries:</span>
          <button
            onClick={() => handlePresetClick('elephant habitat loss Odisha')}
            className="bg-[#fdfaf5] hover:bg-[#f5eedc] px-2.5 py-1 rounded-sm border border-[#e5e0d8] text-emerald-700 hover:text-emerald-800 transition-all font-semibold"
          >
            "elephant habitat loss Odisha"
          </button>
          <button
            onClick={() => handlePresetClick('tiger poaching Corbett')}
            className="bg-[#fdfaf5] hover:bg-[#f5eedc] px-2.5 py-1 rounded-sm border border-[#e5e0d8] text-cyan-700 hover:text-cyan-800 transition-all font-semibold"
          >
            "tiger poaching Corbett"
          </button>
          <button
            onClick={() => handlePresetClick('rhino flood Kaziranga')}
            className="bg-[#fdfaf5] hover:bg-[#f5eedc] px-2.5 py-1 rounded-sm border border-[#e5e0d8] text-amber-700 hover:text-amber-800 transition-all font-semibold"
          >
            "rhino flood Kaziranga"
          </button>
        </div>
      </div>

      {error && (
        <EmptyState
          variant="error"
          icon={AlertTriangle}
          title="Search execution failed"
          description={error}
          actionLabel="Retry search"
          onAction={() => executeSearch(query)}
        />
      )}

      {loading && (
        <div className="space-y-4 animate-fade-slide-in">
          <div className="bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm p-4 space-y-2">
            <div className="animate-skeleton h-3 w-1/3 bg-[#e5e0d8] rounded-sm" />
            <div className="animate-skeleton h-3 w-2/3 bg-[#e5e0d8] rounded-sm" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm p-4 space-y-2">
                <div className="animate-skeleton h-3 w-1/2 bg-[#e5e0d8] rounded-sm" />
                <div className="animate-skeleton h-3 w-full bg-[#e5e0d8] rounded-sm" />
                <div className="animate-skeleton h-3 w-3/4 bg-[#e5e0d8] rounded-sm" />
              </div>
            ))}
          </div>
          <p className="text-center text-[10px] font-mono font-semibold text-emerald-700 tracking-wider uppercase">
            Executing 384-dimensional pgvector cosine distance query &amp; NLP extraction...
          </p>
        </div>
      )}

      {results && !loading && (
        <div className="space-y-6 animate-fade-slide-in">
          {/* Result count summary */}
          <div className="flex items-center justify-between text-[10px] font-mono text-[#94918a] px-1 uppercase tracking-wider">
            <span>
              <span className="text-[#1a1916] font-bold">{results.total_results}</span> results for{' '}
              <span className="text-emerald-700 font-bold">"{results.query}"</span>
            </span>
            {results.nlp_summary && (
              <span className="flex items-center gap-1 text-emerald-700 font-bold">
                <Sparkles className="w-3.5 h-3.5" />
                AI-Enhanced Semantic Results
              </span>
            )}
          </div>

          {results.total_results === 0 &&
          results.documents.length === 0 &&
          results.matched_species.length === 0 &&
          results.matched_locations.length === 0 ? (
            <EmptyState
              icon={SearchX}
              title="No matches found"
              description="Try a broader query, or check spelling of species, locations, or threat terms."
            />
          ) : (
            <>
          {/* AI NLP Summary Section */}
          {results.nlp_summary && (
            <NLPSummaryBox
              summary={results.nlp_summary}
            />
          )}

          {/* Risk & Anomaly Overview Grid — only rendered when the API returned these values */}
          {((results.risk_level && typeof results.risk_score === 'number') || results.anomaly_info) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {results.risk_level && typeof results.risk_score === 'number' && (
                <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm flex items-center justify-between gap-3">
                  <div>
                    <RiskIndicatorLabel className="block mb-1" />
                    <h4 className="text-sm font-semibold text-[#1a1916]">
                      {results.matched_species.length > 0
                        ? results.matched_species[0].common_name
                        : 'Target Corridor'}
                    </h4>
                  </div>
                  <RiskBadge level={results.risk_level} score={results.risk_score} size="lg" showGauge />
                </div>
              )}

              {results.anomaly_info && <AnomalyCard anomaly={results.anomaly_info} />}
            </div>
          )}

          {/* Matched Entities Facets */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Species */}
            <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm">
              <span className="text-[10px] font-mono text-[#94918a] uppercase tracking-wider flex items-center gap-1.5 mb-2 font-semibold">
                <PawPrint className="w-3.5 h-3.5 text-emerald-700" />
                Matched Species ({results.matched_species.length})
              </span>
              <div className="space-y-1.5">
                {results.matched_species.map((sp) => (
                  <div key={sp.id} className="text-xs text-[#1a1916] bg-[#fdfaf5] p-2 rounded-sm border border-[#e5e0d8]">
                    <span className="font-semibold block">{sp.common_name}</span>
                    <span className="text-[10px] text-[#77746c] font-serif italic">{sp.scientific_name}</span>
                    {sp.conservation_status && (
                      <span className="ml-2 text-[10px] bg-[#e5e0d8] text-[#1a1916] px-1 py-0.2 rounded-sm font-mono font-bold">
                        {sp.conservation_status}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Locations */}
            <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm">
              <span className="text-[10px] font-mono text-[#94918a] uppercase tracking-wider flex items-center gap-1.5 mb-2 font-semibold">
                <MapPin className="w-3.5 h-3.5 text-emerald-700" />
                Matched Locations ({results.matched_locations.length})
              </span>
              <div className="space-y-1.5">
                {results.matched_locations.map((loc) => (
                  <div key={loc.id} className="text-xs text-[#1a1916] bg-[#fdfaf5] p-2 rounded-sm border border-[#e5e0d8]">
                    <span className="font-semibold block">{loc.name}</span>
                    <span className="text-[10px] text-[#77746c] font-mono">{loc.state || 'Odisha'}, {loc.country || 'India'}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Threats */}
            <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm">
              <span className="text-[10px] font-mono text-[#94918a] uppercase tracking-wider flex items-center gap-1.5 mb-2 font-semibold">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                Matched Threats ({results.matched_threats.length})
              </span>
              <div className="space-y-1.5">
                {results.matched_threats.map((th) => (
                  <div key={th.id} className="text-xs text-[#1a1916] bg-[#fdfaf5] p-2 rounded-sm border border-[#e5e0d8]">
                    <span className="font-semibold block">{th.name}</span>
                    <span className="text-[10px] text-amber-700 font-mono font-semibold">{th.code}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Topics */}
            <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm">
              <span className="text-[10px] font-mono text-[#94918a] uppercase tracking-wider flex items-center gap-1.5 mb-2 font-semibold">
                <Layers className="w-3.5 h-3.5 text-amber-600" />
                Topics & Domains ({results.matched_topics.length})
              </span>
              <div className="space-y-1.5">
                {results.matched_topics.map((tp) => (
                  <div key={tp.id} className="text-xs text-[#1a1916] bg-[#fdfaf5] p-2 rounded-sm border border-[#e5e0d8]">
                    <span className="font-semibold block">{tp.name}</span>
                    <span className="text-[10px] text-amber-700 font-mono font-semibold">{tp.code}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Spatial Map View for Matched Observations */}
          <div className="bg-white border border-[#e5e0d8] p-5 rounded-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
              <h3 className="text-sm font-semibold text-[#1a1916] flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-700" />
                PostGIS Geolocation Coordinates for Search Corpus
              </h3>
              {selectedStateName && (
                <div className="flex items-center gap-2 px-2.5 py-1 bg-[#f0f9f4] border border-[#13843a] rounded text-xs font-mono">
                  <span className="text-[#1a1916] font-semibold">Drilldown State: {selectedStateName}</span>
                  <button
                    onClick={() => setSelectedStateName(null)}
                    className="text-[#dc2626] hover:text-[#991b1b] transition-colors"
                    title="Clear state drilldown"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
            <p className="text-xs text-[#77746c] mb-3 font-mono">
              Click any state boundary to zoom and drill down into that state's geographic area.
            </p>
            <div className="mb-3">
              <MapLegend />
            </div>
            <MapView
              observations={results.related_observations}
              locations={results.matched_locations}
              selectedStateName={selectedStateName}
              onStateSelect={(st) => setSelectedStateName((prev) => (prev?.toLowerCase() === st.toLowerCase() ? null : st))}
              height="350px"
            />
          </div>

          {/* Ranked Documents List */}
          <div className="bg-white border border-[#e5e0d8] p-5 rounded-sm space-y-4">
            <h3 className="text-sm font-semibold text-[#1a1916] flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-700" />
              pgvector Ranked Documents ({results.documents.length} Matches)
            </h3>

            {results.documents.length === 0 ? (
              <p className="text-xs font-mono text-[#94918a] text-center py-6">
                No ranked documents matched this query.
              </p>
            ) : (
            <div className="space-y-3">
              {results.documents.map((doc, idx) => (
                <div
                  key={doc.id}
                  className="bg-[#fdfaf5] border border-[#e5e0d8] hover:border-emerald-700/40 hover:-translate-y-0.5 p-4 rounded-sm transition-all animate-fade-slide-in"
                  style={{ animationDelay: `${idx * 50}ms` }}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <h4 className="text-sm font-bold text-[#1a1916] hover:underline hover:text-emerald-800 font-serif">
                      {doc.title}
                    </h4>
                    {doc.similarity_score !== undefined && (
                      <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-sm bg-emerald-50 text-emerald-700 border border-emerald-200 shrink-0">
                        Similarity {doc.similarity_score.toFixed(3)}
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-[#77746c] leading-relaxed mb-3">
                    {doc.summary}
                  </p>

                  <div className="flex items-center justify-between text-[10px] font-mono text-[#94918a] border-t border-[#e5e0d8] pt-2">
                    <span>{doc.provenance || 'Official Conservation Corpus'}</span>
                    <span>{doc.publication_date || '2026-09-27'}</span>
                  </div>
                </div>
              ))}
            </div>
            )}
          </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};
