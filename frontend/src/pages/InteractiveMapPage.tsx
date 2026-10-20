import React, { useEffect, useMemo, useState } from 'react';
import { 
  MapPin, 
  Filter, 
  X, 
  Radio, 
  Layers, 
  BarChart3, 
  ShieldAlert, 
  ChevronRight, 
  Info,
  Calendar,
  AlertTriangle,
  Compass
} from 'lucide-react';
import { MapView, MapLegend, MapMode, ChoroplethShading } from '../components/MapView';
import { DemoBanner } from '../components/DemoBanner';
import { EmptyState } from '../components/EmptyState';
import { observationService, speciesService, spatialService } from '../services/api';
import { errorMessage, observationDate, observationCount, observationNote } from '../utils/format';
import { Observation, StateMetricSummary, StateDetailResponse } from '../types';

export const InteractiveMapPage: React.FC = () => {
  // Mode States
  const [mapMode, setMapMode] = useState<MapMode>('CHOROPLETH');
  const [choroplethShading, setChoroplethShading] = useState<ChoroplethShading>('SPECIES_RICHNESS');
  const [selectedTaxonomicGroup, setSelectedTaxonomicGroup] = useState<string>('ALL');

  // Observations State
  const [observations, setObservations] = useState<Observation[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedSpecies, setSelectedSpecies] = useState<string>('ALL');
  const [selectedObs, setSelectedObs] = useState<Observation | null>(null);
  const [speciesCatalog, setSpeciesCatalog] = useState<any[]>([]);
  const [totalLoaded, setTotalLoaded] = useState(0);
  const [retryCount, setRetryCount] = useState(0);
  const [activeStateFilter, setActiveStateFilter] = useState<string | null>(null);

  // State-wise Intelligence States
  const [stateMetricsMap, setStateMetricsMap] = useState<Record<string, StateMetricSummary>>({});
  const [selectedStateName, setSelectedStateName] = useState<string | null>(null);
  const [stateDetail, setStateDetail] = useState<StateDetailResponse | null>(null);
  const [stateDetailLoading, setStateDetailLoading] = useState(false);
  const [provenanceNote, setProvenanceNote] = useState<string>('');

  const [error, setError] = useState<string | null>(null);

  const [stateMetricsVersion, setStateMetricsVersion] = useState(0);

  // Load species catalog
  useEffect(() => {
    speciesService.getSpeciesList(1, 1000).then(res => {
      setSpeciesCatalog(res.items);
    }).catch(console.error);
  }, []);

  // Fetch State-wise aggregate metrics whenever taxonomic filter changes
  useEffect(() => {
    const fetchStateMetrics = async () => {
      try {
        const params: Record<string, string> = {};
        if (selectedTaxonomicGroup !== 'ALL') {
          params.taxonomic_group = selectedTaxonomicGroup;
        }
        const res = await spatialService.getStateMetrics(params);
        setStateMetricsMap(res.states || {});
        setStateMetricsVersion(v => v + 1);
        if (res.dataset_disclaimer) {
          setProvenanceNote(res.dataset_disclaimer);
        }
      } catch (err) {
        console.error('Failed to load state metrics:', err);
      }
    };

    fetchStateMetrics();
  }, [selectedTaxonomicGroup]);

  // Fetch state drilldown detail when a state is selected or taxonomic filter changes
  useEffect(() => {
    if (!selectedStateName) {
      setStateDetail(null);
      return;
    }

    const fetchDetail = async () => {
      setStateDetailLoading(true);
      try {
        const params: Record<string, string> = {};
        if (selectedTaxonomicGroup !== 'ALL') {
          params.taxonomic_group = selectedTaxonomicGroup;
        }
        const detail = await spatialService.getStateDetail(selectedStateName, params);
        setStateDetail(detail);
      } catch (err) {
        console.error('Failed to load state detail for', selectedStateName, err);
        setStateDetail(null);
      } finally {
        setStateDetailLoading(false);
      }
    };

    fetchDetail();
  }, [selectedStateName, selectedTaxonomicGroup]);

  // Fetch observation markers
  useEffect(() => {
    const loadMapData = async () => {
      setLoading(true);
      setError(null);
      setSelectedObs(null);
      try {
        let params: Record<string, any> = {};
        if (selectedSpecies !== 'ALL') {
          const sp = speciesCatalog.find(s => s.common_name === selectedSpecies);
          if (sp) {
            params.species_id = sp.id;
          }
        }

        if (selectedTaxonomicGroup !== 'ALL') {
          params.taxonomic_group = selectedTaxonomicGroup;
        }

        // If a state filter is active, use PostGIS containment instead of bbox
        if (activeStateFilter) {
          params.state_name = activeStateFilter;
        }

        const res = await observationService.getMapObservations(params);
        setTotalLoaded(res.total_loaded);
        
        const names = Object.fromEntries(speciesCatalog.map(sp => [sp.id, sp.common_name]));
        
        setObservations(
          res.items.map((o) => ({ ...o, species_name: o.species_name ?? names[o.species_id] }))
        );
      } catch (err) {
        console.error('Failed to load map observations from API:', err);
        setObservations([]);
        setError(errorMessage(err, 'Could not load observations'));
      } finally {
        setLoading(false);
      }
    };

    if (speciesCatalog.length > 0) {
      loadMapData();
    }
  }, [selectedSpecies, speciesCatalog, retryCount, activeStateFilter, selectedTaxonomicGroup]);

  const filteredObservations = observations.filter((o) => {
    if (selectedStatus !== 'ALL' && o.verification_status !== selectedStatus) return false;
    return true;
  });

  const dropdownRef = React.useRef<HTMLDivElement>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [speciesSearch, setSpeciesSearch] = useState('');

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredCatalog = useMemo(() => {
    let list = speciesCatalog;
    if (speciesSearch) {
      const lower = speciesSearch.toLowerCase();
      list = list.filter(sp => 
        (sp.common_name && sp.common_name.toLowerCase().includes(lower)) || 
        (sp.scientific_name && sp.scientific_name.toLowerCase().includes(lower))
      );
    }
    return list;
  }, [speciesCatalog, speciesSearch]);

  const handleStateClick = (stateName: string) => {
    setSelectedStateName(stateName);
    setSelectedObs(null);
  };

  const handleDrilldownToObservations = (stateName: string) => {
    setActiveStateFilter(stateName);
    setMapMode('OBSERVATIONS');
    setSelectedStateName(stateName);
  };

  const clearStateFilter = () => {
    setActiveStateFilter(null);
    setSelectedStateName(null);
  };

  return (
    <div className="space-y-6">
      <DemoBanner />

      {/* Header & Main Controls */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4 mb-4">
        <div>
          <p className="font-mono text-[10px] tracking-widest uppercase font-semibold mb-1" style={{ color: '#13843a' }}>
            SPATIAL INTELLIGENCE · POSTGIS JOIN ENGINE
          </p>
          <h1 className="font-serif text-3xl font-bold leading-tight flex items-center gap-2" style={{ color: '#1a1916', fontFamily: "'Newsreader', Georgia, serif" }}>
            <MapPin className="w-6 h-6" style={{ color: '#13843a' }} />
            India Wildlife & Biodiversity Spatial Intelligence
          </h1>
          <p className="text-sm mt-1" style={{ color: '#77746c' }}>
            State-wise biodiversity choropleth, conservation risk intelligence, and exact observation spatial distributions across 36 States & UTs.
          </p>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 p-1 bg-white border border-[#e5e0d8] rounded shadow-xs">
          <button
            onClick={() => setMapMode('CHOROPLETH')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-medium rounded transition-all ${
              mapMode === 'CHOROPLETH'
                ? 'bg-[#13843a] text-white shadow-xs'
                : 'text-[#5e5b54] hover:bg-[#f5f3ee]'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            State Choropleth
          </button>
          <button
            onClick={() => setMapMode('INTELLIGENCE')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-medium rounded transition-all ${
              mapMode === 'INTELLIGENCE'
                ? 'bg-[#13843a] text-white shadow-xs'
                : 'text-[#5e5b54] hover:bg-[#f5f3ee]'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            Conservation Risk
          </button>
          <button
            onClick={() => setMapMode('OBSERVATIONS')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-medium rounded transition-all ${
              mapMode === 'OBSERVATIONS'
                ? 'bg-[#13843a] text-white shadow-xs'
                : 'text-[#5e5b54] hover:bg-[#f5f3ee]'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Observation Points ({totalLoaded})
          </button>
        </div>
      </div>

      {/* Secondary Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-white border border-[#e5e0d8] rounded shadow-xs">
        {/* Left Sub-Controls based on Mode */}
        <div className="flex flex-wrap items-center gap-4">
          {mapMode === 'CHOROPLETH' && (
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] uppercase font-bold text-[#94918a]">Shading:</span>
              <div className="flex items-center gap-1">
                {(['SPECIES_RICHNESS', 'OBSERVATION_COUNT', 'VERIFIED_RECORDS'] as ChoroplethShading[]).map(mode => (
                  <button
                    key={mode}
                    onClick={() => setChoroplethShading(mode)}
                    className={`px-2.5 py-1 text-[11px] font-mono rounded transition-colors ${
                      choroplethShading === mode
                        ? 'bg-[#1a1916] text-white font-semibold'
                        : 'bg-[#f5f3ee] text-[#5e5b54] hover:bg-[#eae7df]'
                    }`}
                  >
                    {mode === 'SPECIES_RICHNESS' ? 'Species Richness' : mode === 'OBSERVATION_COUNT' ? 'Observation Count' : 'Verified Records'}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Taxonomic Group Filter for State Aggregations */}
          {(mapMode === 'CHOROPLETH' || mapMode === 'INTELLIGENCE') && (
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] uppercase font-bold text-[#94918a]">Taxa:</span>
              <div className="flex items-center gap-1">
                {['ALL', 'Mammalia', 'Aves', 'Reptilia', 'Amphibia'].map(group => (
                  <button
                    key={group}
                    onClick={() => setSelectedTaxonomicGroup(group)}
                    className={`px-2.5 py-1 text-[11px] font-mono rounded transition-colors ${
                      selectedTaxonomicGroup === group
                        ? 'bg-[#13843a] text-white font-semibold'
                        : 'bg-[#f5f3ee] text-[#5e5b54] hover:bg-[#eae7df]'
                    }`}
                  >
                    {group}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Observations Mode Filters */}
          {mapMode === 'OBSERVATIONS' && activeStateFilter && (
            <div className="flex items-center gap-2 px-2.5 py-1 bg-[#f0f9f4] border border-[#13843a] rounded text-xs font-mono">
              <MapPin className="w-3.5 h-3.5 text-[#13843a]" />
              <span className="text-[#1a1916] font-semibold">Filtered: {activeStateFilter}</span>
              <button
                onClick={clearStateFilter}
                className="ml-1 text-[#dc2626] hover:text-[#991b1b] transition-colors"
                title="Clear state filter"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {mapMode === 'OBSERVATIONS' && (
            <div className="flex flex-wrap items-center gap-3">
              {/* Status Filter */}
              <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase">
                <span className="font-bold text-[#94918a]">Status:</span>
                <button
                  onClick={() => setSelectedStatus('ALL')}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    selectedStatus === 'ALL' ? 'bg-[#13843a] text-white' : 'bg-[#f5f3ee] text-[#5e5b54]'
                  }`}
                >
                  ALL ({totalLoaded})
                </button>
                <button
                  onClick={() => setSelectedStatus('VERIFIED')}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    selectedStatus === 'VERIFIED' ? 'bg-[#13843a] text-white' : 'bg-[#f5f3ee] text-[#5e5b54]'
                  }`}
                >
                  VERIFIED
                </button>
              </div>

              {/* Species Filter Dropdown */}
              {speciesCatalog.length > 0 && (
                <div className="relative w-64" ref={dropdownRef}>
                  <button
                    onClick={() => setDropdownOpen(!dropdownOpen)}
                    className="w-full text-left px-2.5 py-1 bg-white hover:bg-[#f5f3ef] transition-colors border text-xs flex items-center justify-between"
                    style={{ 
                      borderRadius: '3px', 
                      borderColor: dropdownOpen ? '#13843a' : '#e5e0d8',
                      color: selectedSpecies === 'ALL' ? '#1a1916' : '#13843a',
                      fontWeight: selectedSpecies === 'ALL' ? 'normal' : '600'
                    }}
                  >
                    <span className="truncate">
                      {selectedSpecies === 'ALL' ? 'All Species' : selectedSpecies}
                    </span>
                    <span className="text-[10px] text-earthy-400 ml-2">▼</span>
                  </button>

                  {dropdownOpen && (
                    <div className="absolute z-[9999] mt-1 w-80 bg-white border border-[#e5e0d8] shadow-xl max-h-[350px] flex flex-col rounded">
                      <div className="p-2 border-b border-[#e5e0d8] sticky top-0 bg-white z-10">
                        <input
                          autoFocus
                          type="text"
                          placeholder="Search species..."
                          className="w-full px-2.5 py-1 text-xs border border-[#e5e0d8] focus:outline-none focus:border-[#13843a] rounded"
                          value={speciesSearch}
                          onChange={(e) => setSpeciesSearch(e.target.value)}
                        />
                      </div>
                      <div className="overflow-y-auto flex-1 overscroll-contain">
                        {(!speciesSearch || "all species".includes(speciesSearch.toLowerCase())) && (
                          <button
                            onClick={() => { setSelectedSpecies('ALL'); setDropdownOpen(false); setSpeciesSearch(''); }}
                            className={`w-full text-left px-3 py-2 hover:bg-[#f5f3ef] text-xs ${
                              selectedSpecies === 'ALL' ? 'bg-[#f5f3ef] font-semibold text-[#13843a]' : 'text-[#1a1916]'
                            }`}
                          >
                            All Species
                          </button>
                        )}
                        {filteredCatalog.map(sp => (
                          <button
                            key={sp.id}
                            onClick={() => { setSelectedSpecies(sp.common_name); setDropdownOpen(false); setSpeciesSearch(''); }}
                            className={`w-full text-left px-3 py-1.5 hover:bg-[#f5f3ef] border-t border-[#f5f3ef] text-xs ${
                              selectedSpecies === sp.common_name ? 'bg-[#f0f9f4] text-[#13843a]' : 'text-[#1a1916]'
                            }`}
                          >
                            <div className="font-semibold">{sp.common_name}</div>
                            <div className="text-[10px] text-[#77746c] italic font-serif">{sp.scientific_name}</div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Clear selection if any */}
        {(selectedStateName || selectedObs || activeStateFilter) && (
          <button
            onClick={() => { setSelectedStateName(null); setSelectedObs(null); setActiveStateFilter(null); }}
            className="text-xs font-mono text-[#dc2626] hover:text-[#991b1b] flex items-center gap-1 transition-colors"
          >
            <X className="w-3.5 h-3.5" /> Clear Selection
          </button>
        )}
      </div>

      {/* Main Map & Side Panel Grid */}
      {loading ? (
        <div className="bg-[#f5f3ee] border border-[#e5e0d8] rounded-xl h-[640px] animate-pulse flex items-center justify-center">
          <span className="font-mono text-xs text-[#94918a]">Loading PostGIS Spatial Map Layer...</span>
        </div>
      ) : error ? (
        <EmptyState
          variant="error"
          title="Observation map unavailable"
          description={error}
          actionLabel="Retry"
          onAction={() => setRetryCount(c => c + 1)}
        />
      ) : (
        <div className="bg-white border border-[#e5e0d8] p-4 rounded-xl space-y-3 shadow-xs">
          {/* Dynamic Map Legend Bar */}
          <div className="flex items-center justify-between">
            <MapLegend mapMode={mapMode} choroplethShading={choroplethShading} />
            <div className="text-[11px] font-mono text-[#94918a] hidden sm:block">
              {mapMode !== 'OBSERVATIONS' ? 'Click any state for full biodiversity drilldown' : 'Click observation markers to view record details'}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Map Container */}
            <div className="lg:col-span-2">
              <MapView
                mapMode={mapMode}
                choroplethShading={choroplethShading}
                stateMetrics={stateMetricsMap}
                stateMetricsVersion={stateMetricsVersion}
                selectedStateName={selectedStateName}
                onStateSelect={handleStateClick}
                observations={filteredObservations}
                height="640px"
                selectedObservationId={selectedObs?.id ?? null}
                onObservationClick={(obs) => { setSelectedObs(obs); setSelectedStateName(null); }}
              />
            </div>

            {/* Side Intelligence Panel */}
            <div className="bg-[#fcfbf9] border border-[#e5e0d8] rounded-xl p-4 h-[640px] overflow-y-auto">
              {/* Case 1: State Selected Drilldown */}
              {selectedStateName ? (
                <div className="space-y-4 animate-fadeIn">
                  <div className="flex items-center justify-between border-b border-[#e5e0d8] pb-3">
                    <div>
                      <span className="font-mono text-[10px] tracking-widest uppercase font-semibold text-[#13843a]">
                        STATE INTELLIGENCE
                      </span>
                      <h2 className="font-serif text-2xl font-bold text-[#1a1916]">
                        {selectedStateName}
                      </h2>
                    </div>
                    {stateMetricsMap[selectedStateName] && (
                      <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded ${
                        stateMetricsMap[selectedStateName].highest_risk_level === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                        stateMetricsMap[selectedStateName].highest_risk_level === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                        stateMetricsMap[selectedStateName].highest_risk_level === 'MEDIUM' ? 'bg-amber-100 text-amber-800' :
                        'bg-emerald-100 text-emerald-800'
                      }`}>
                        {stateMetricsMap[selectedStateName].highest_risk_level || 'LOW'} RISK
                      </span>
                    )}
                  </div>

                  {stateDetailLoading ? (
                    <div className="py-12 text-center text-xs font-mono text-[#94918a] animate-pulse">
                      Analyzing PostGIS spatial intersections & taxonomy...
                    </div>
                  ) : stateDetail ? (
                    <div className="space-y-4 text-xs font-mono">
                      {/* Metric Summary Cards */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="bg-white p-2.5 rounded border border-[#e5e0d8]">
                          <span className="text-[10px] text-[#77746c] uppercase block">Distinct Species</span>
                          <span className="text-xl font-bold text-[#1a1916]">
                            {stateDetail.summary.distinct_species_count}
                          </span>
                        </div>
                        <div className="bg-white p-2.5 rounded border border-[#e5e0d8]">
                          <span className="text-[10px] text-[#77746c] uppercase block">Total Records</span>
                          <span className="text-xl font-bold text-[#1a1916]">
                            {stateDetail.summary.total_observation_records}
                          </span>
                        </div>
                        <div className="bg-white p-2.5 rounded border border-[#e5e0d8]">
                          <span className="text-[10px] text-[#77746c] uppercase block">Verified Data</span>
                          <span className="text-xl font-bold text-[#13843a]">
                            {stateDetail.summary.verified_records}
                          </span>
                        </div>
                        <div className="bg-white p-2.5 rounded border border-[#e5e0d8]">
                          <span className="text-[10px] text-[#77746c] uppercase block">Unverified / Citizen</span>
                          <span className="text-xl font-bold text-[#b45309]">
                            {stateDetail.summary.unverified_records}
                          </span>
                        </div>
                      </div>

                      {/* Taxonomic Composition Breakdown */}
                      <div className="bg-white p-3 rounded border border-[#e5e0d8] space-y-2">
                        <span className="font-bold text-[11px] uppercase tracking-wider text-[#1a1916] block">
                          Taxonomic Composition
                        </span>
                        {Object.keys(stateDetail.summary.taxonomic_breakdown).length === 0 ? (
                          <p className="text-[11px] text-[#94918a]">No taxonomic classes indexed in polygon.</p>
                        ) : (
                          <div className="space-y-1.5">
                            {Object.entries(stateDetail.summary.taxonomic_breakdown).map(([cls, count]) => {
                              const pct = Math.round((count / (stateDetail.summary.total_observation_records || 1)) * 100);
                              return (
                                <div key={cls} className="space-y-0.5">
                                  <div className="flex justify-between text-[11px]">
                                    <span className="text-[#5e5b54]">{cls}</span>
                                    <span className="font-semibold text-[#1a1916]">{count} ({pct}%)</span>
                                  </div>
                                  <div className="w-full bg-[#f0ede6] h-1.5 rounded-full overflow-hidden">
                                    <div 
                                      className="bg-[#13843a] h-full rounded-full" 
                                      style={{ width: `${Math.min(pct, 100)}%` }}
                                    />
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>

                      {/* Top Recorded Species */}
                      <div className="bg-white p-3 rounded border border-[#e5e0d8] space-y-2">
                        <span className="font-bold text-[11px] uppercase tracking-wider text-[#1a1916] block">
                          Top Recorded Species
                        </span>
                        {(!stateDetail.summary.top_recorded_species || stateDetail.summary.top_recorded_species.length === 0) ? (
                          <p className="text-[11px] text-[#94918a]">No records found for this state.</p>
                        ) : (
                          <div className="divide-y divide-[#f0ede6]">
                            {stateDetail.summary.top_recorded_species.map((sp) => (
                              <div key={sp.species_id} className="py-1.5 flex justify-between items-center">
                                <div>
                                  <div className="font-semibold text-[#1a1916]">{sp.common_name}</div>
                                  <div className="text-[10px] text-[#77746c] italic font-serif">{sp.scientific_name}</div>
                                </div>
                                <div className="text-right">
                                  <span className="text-[11px] font-bold text-[#13843a]">{sp.records_count}</span>
                                  <span className={`ml-2 text-[9px] px-1 py-0.2 rounded font-mono ${
                                    sp.iucn_category === 'CR' ? 'bg-red-100 text-red-800' :
                                    sp.iucn_category === 'EN' ? 'bg-orange-100 text-orange-800' :
                                    sp.iucn_category === 'VU' ? 'bg-amber-100 text-amber-800' :
                                    'bg-gray-100 text-gray-700'
                                  }`}>
                                    {sp.iucn_category || 'LC'}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Action to switch to observation points */}
                      <button
                        onClick={() => handleDrilldownToObservations(selectedStateName)}
                        className="w-full py-2.5 px-3 bg-[#13843a] hover:bg-[#0f6b2e] text-white font-mono text-xs font-semibold rounded flex items-center justify-center gap-2 transition-colors shadow-xs"
                      >
                        <Compass className="w-4 h-4" />
                        Explore Observations in {selectedStateName}
                      </button>
                    </div>
                  ) : null}
                </div>
              ) : selectedObs ? (
                /* Case 2: Individual Observation Marker Selected */
                <div className="space-y-3 animate-fadeIn">
                  <div className="flex items-center gap-2 text-[#13843a]">
                    <Radio className="w-4 h-4" />
                    <span className="text-xs font-mono font-bold uppercase">Selected Observation</span>
                  </div>
                  <h3 className="text-base font-bold text-[#1a1916]">
                    {selectedObs.species_name || `Observation #${selectedObs.id}`}
                  </h3>
                  <div className="text-xs font-mono text-[#5e5b54] space-y-2">
                    <div className="flex justify-between border-b border-[#e5e0d8] pb-1.5">
                      <span>Coordinates</span>
                      <span className="text-[#1a1916] text-right">
                        {selectedObs.latitude.toFixed(4)}, {selectedObs.longitude.toFixed(4)}
                      </span>
                    </div>
                    {selectedObs.location_name && (
                      <div className="flex justify-between border-b border-[#e5e0d8] pb-1.5">
                        <span>Protected Area / Locality</span>
                        <span className="text-[#1a1916] text-right">{selectedObs.location_name}</span>
                      </div>
                    )}
                    {observationCount(selectedObs) !== undefined && (
                      <div className="flex justify-between border-b border-[#e5e0d8] pb-1.5">
                        <span>Observed Count</span>
                        <span className="text-[#1a1916]">{observationCount(selectedObs)}</span>
                      </div>
                    )}
                    <div className="flex justify-between border-b border-[#e5e0d8] pb-1.5">
                      <span>Status</span>
                      <span className={selectedObs.verification_status === 'VERIFIED' ? 'text-[#13843a] font-bold' : 'text-[#b45309] font-bold'}>
                        {selectedObs.verification_status}
                      </span>
                    </div>
                    {observationDate(selectedObs) && (
                      <div className="flex justify-between border-b border-[#e5e0d8] pb-1.5">
                        <span>Observation Date</span>
                        <span className="text-[#1a1916]">{observationDate(selectedObs)}</span>
                      </div>
                    )}
                  </div>
                  {observationNote(selectedObs) && (
                    <p className="text-xs text-[#5e5b54] leading-relaxed bg-white p-3 rounded border border-[#e5e0d8] italic">
                      "{observationNote(selectedObs)}"
                    </p>
                  )}
                </div>
              ) : (
                /* Case 3: Default Empty State - Prompt User */
                <div className="h-full flex flex-col items-center justify-center text-center text-xs font-mono text-[#94918a] px-4 space-y-3">
                  <div className="w-12 h-12 rounded-full bg-[#f0ede6] flex items-center justify-center text-[#13843a]">
                    <BarChart3 className="w-6 h-6" />
                  </div>
                  <div className="font-bold text-[#1a1916] text-sm font-sans">State-wise Wildlife Intelligence</div>
                  <p className="max-w-[260px] text-[#77746c] leading-relaxed">
                    Click any State or Union Territory boundary on the map to inspect its biodiversity richness, verified observation ratios, taxonomic distribution, and ML conservation risk score.
                  </p>
                  {provenanceNote && (
                    <div className="mt-4 p-2.5 bg-white border border-[#e5e0d8] rounded text-[10px] text-[#77746c] text-left leading-normal">
                      <span className="font-bold text-[#1a1916] block mb-1">Authoritative GeoJSON Provenance:</span>
                      {provenanceNote}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

