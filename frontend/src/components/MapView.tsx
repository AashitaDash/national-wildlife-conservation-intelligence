import React from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  GeoJSON,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';

import { Observation, Location, StateMetricSummary } from '../types';
import {
  observationDate,
  observationCount,
  observationNote,
} from '../utils/format';

// ============================================================
// DEFAULT INDIA VIEW
// ============================================================

const INDIA_CENTER: [number, number] = [22.5, 82.0];
const INDIA_ZOOM = 5;

const INDIA_BOUNDARY_URL = '/geo/india-boundary.geojson';
const INDIA_STATES_URL = '/geo/india-states.geojson';

// ============================================================
// CUSTOM MARKER
// ============================================================

const createCustomIcon = (
  color: string = '#10b981',
  selected: boolean = false,
  isFuzzy: boolean = false
) => {
  const size = selected ? 18 : 12;

  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `
      <div style="
        background-color: ${color};
        width: ${size}px;
        height: ${size}px;
        border-radius: 50%;
        border: 2px solid #ffffff;
        box-shadow: 0 0 ${selected ? 12 : 6}px ${color};
        ${isFuzzy ? 'border-style: dashed; opacity: 0.85;' : ''}
        transition: all 0.15s ease;
      "></div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

// ============================================================
// COLOR SCALES FOR CHOROPLETH MODES
// ============================================================

export type ChoroplethShading = 'SPECIES_RICHNESS' | 'OBSERVATION_COUNT' | 'VERIFIED_RECORDS' | 'CONSERVATION_RISK';

export function getChoroplethColor(
  stateName: string,
  stateMetrics: Record<string, StateMetricSummary> | undefined,
  shadingMode: ChoroplethShading
): string {
  if (!stateMetrics) return '#e5e2da';
  const metric = stateMetrics[stateName];
  if (!metric) return '#f4f2ec';

  if (shadingMode === 'CONSERVATION_RISK') {
    const risk = (metric.highest_risk_level || 'LOW').toUpperCase();
    if (risk === 'CRITICAL') return '#991b1b'; // Dark Red
    if (risk === 'HIGH') return '#ea580c';     // Orange
    if (risk === 'MEDIUM') return '#eab308';   // Yellow
    return '#10b981';                          // Emerald
  }

  // Numerical metrics
  let val = 0;
  if (shadingMode === 'SPECIES_RICHNESS') val = metric.distinct_species_count;
  else if (shadingMode === 'OBSERVATION_COUNT') val = metric.total_observation_records;
  else if (shadingMode === 'VERIFIED_RECORDS') val = metric.verified_records;

  if (val === 0) return '#f5f3ee';

  if (shadingMode === 'SPECIES_RICHNESS') {
    // Range ~1 to 300
    if (val > 250) return '#064e3b';
    if (val > 200) return '#047857';
    if (val > 100) return '#059669';
    if (val > 50)  return '#10b981';
    if (val > 20)  return '#6ee7b7';
    return '#a7f3d0';
  }

  // OBSERVATION_COUNT & VERIFIED_RECORDS
  // Range ~1 to 4500
  if (val > 3000) return '#1e3a8a';
  if (val > 2000) return '#2563eb';
  if (val > 1000) return '#3b82f6';
  if (val > 300)  return '#60a5fa';
  if (val > 50)   return '#93c5fd';
  return '#bfdbfe';
}

// Controller to fit bounds when selected state changes
const MapBoundsController: React.FC<{
  selectedStateName?: string | null;
  statesGeoJson?: any;
}> = ({ selectedStateName, statesGeoJson }) => {
  const map = useMap();

  React.useEffect(() => {
    if (!selectedStateName || !statesGeoJson) return;

    try {
      const feat = statesGeoJson.features.find(
        (f: any) =>
          f.properties?.name?.toLowerCase() === selectedStateName.toLowerCase() ||
          f.properties?.st_nm?.toLowerCase() === selectedStateName.toLowerCase()
      );
      if (feat) {
        const layer = L.geoJSON(feat);
        map.fitBounds(layer.getBounds(), { padding: [30, 30], maxZoom: 8 });
      }
    } catch (e) {
      console.error('Failed to zoom to state bounds', e);
    }
  }, [selectedStateName, statesGeoJson, map]);

  return null;
};

// ============================================================
// MAP VIEW PROPS
// ============================================================

export type MapMode = 'OBSERVATIONS' | 'CHOROPLETH' | 'INTELLIGENCE';

interface MapViewProps {
  mapMode?: MapMode;
  choroplethShading?: ChoroplethShading;
  stateMetrics?: Record<string, StateMetricSummary>;
  stateMetricsVersion?: number;
  selectedStateName?: string | null;
  onStateSelect?: (stateName: string) => void;

  observations?: Observation[];
  locations?: Location[];

  center?: [number, number];
  zoom?: number;
  height?: string;

  selectedObservationId?: number | null;
  onObservationClick?: (obs: Observation) => void;
}

export const MapView: React.FC<MapViewProps> = ({
  mapMode = 'OBSERVATIONS',
  choroplethShading = 'SPECIES_RICHNESS',
  stateMetrics,
  stateMetricsVersion = 0,
  selectedStateName = null,
  onStateSelect,

  observations = [],
  locations = [],

  center = INDIA_CENTER,
  zoom = INDIA_ZOOM,
  height = '560px',

  selectedObservationId = null,
  onObservationClick,
}) => {
  const [indiaBoundary, setIndiaBoundary] = React.useState<any>(null);
  const [indiaStates, setIndiaStates] = React.useState<any>(null);
  const [boundaryError, setBoundaryError] = React.useState(false);

  // Load authoritative India National Outline (local bundled)
  React.useEffect(() => {
    fetch(INDIA_BOUNDARY_URL)
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then(setIndiaBoundary)
      .catch((err) => {
        console.error('Failed to load official India national boundary:', err);
        setBoundaryError(true);
      });
  }, []);

  // Load authoritative India 37 States & UTs (local bundled)
  React.useEffect(() => {
    fetch(INDIA_STATES_URL)
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then(setIndiaStates)
      .catch((err) => {
        console.error('Failed to load official India states GeoJSON:', err);
      });
  }, []);

  // Compute style per state polygon
  const getStateStyle = (feature: any) => {
    const stName = feature?.properties?.name || feature?.properties?.st_nm || '';
    const isSelected = selectedStateName && selectedStateName.toLowerCase() === stName.toLowerCase();

    if (mapMode === 'OBSERVATIONS') {
      return {
        color: isSelected ? '#11682f' : '#88847c',
        weight: isSelected ? 2.5 : 0.8,
        opacity: isSelected ? 1 : 0.6,
        fillColor: isSelected ? '#d8f3e1' : 'transparent',
        fillOpacity: isSelected ? 0.2 : 0,
      };
    }

    // CHOROPLETH or INTELLIGENCE
    const shading = mapMode === 'INTELLIGENCE' ? 'CONSERVATION_RISK' : choroplethShading;
    const fillColor = getChoroplethColor(stName, stateMetrics, shading);

    return {
      color: isSelected ? '#000000' : '#4b5563',
      weight: isSelected ? 3 : 1,
      opacity: 0.9,
      fillColor,
      fillOpacity: isSelected ? 0.85 : 0.7,
    };
  };

  return (
    <div
      style={{ height, width: '100%' }}
      className="rounded-xl overflow-hidden border border-[#2a2924] shadow-xl relative z-0"
    >
      <MapContainer
        center={center}
        zoom={zoom}
        minZoom={4}
        maxZoom={12}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%' }}
      >
        <MapBoundsController selectedStateName={selectedStateName} statesGeoJson={indiaStates} />

        {/* Basemap OpenStreetMap */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* State Boundaries Layer (with Interactive Choropleth & tooltips) */}
        {indiaStates && (
          <GeoJSON
            key={`states-layer-${mapMode}-${choroplethShading}-${selectedStateName}-${stateMetricsVersion}`}
            data={indiaStates}
            style={getStateStyle}
            onEachFeature={(feature, layer) => {
              const stName = feature?.properties?.name || feature?.properties?.st_nm || '';
              const metrics = stateMetrics ? stateMetrics[stName] : null;

              // Tooltip hover
              let tooltipHtml = `<strong style="font-family: serif; font-size: 13px;">${stName}</strong>`;
              if (metrics) {
                tooltipHtml += `
                  <div style="font-size: 10px; font-family: monospace; margin-top: 3px; line-height: 1.3;">
                    <span>Species: <b>${metrics.distinct_species_count}</b></span><br/>
                    <span>Records: <b>${metrics.total_observation_records.toLocaleString()}</b></span><br/>
                    <span>Verified: <b>${metrics.verified_records.toLocaleString()}</b></span><br/>
                    ${metrics.highest_risk_level ? `<span style="color: ${metrics.highest_risk_level === 'CRITICAL' ? '#b91c1c' : '#b45309'}">Risk: <b>${metrics.highest_risk_level}</b></span>` : ''}
                  </div>
                `;
              } else {
                tooltipHtml += `<div style="font-size: 10px; color: #6b7280; font-family: monospace;">No dataset records</div>`;
              }

              layer.bindTooltip(tooltipHtml, { sticky: true, direction: 'auto', opacity: 0.95 });

              layer.on({
                click: () => {
                  if (onStateSelect) {
                    onStateSelect(stName);
                  }
                },
                mouseover: (e) => {
                  const target = e.target;
                  if (selectedStateName?.toLowerCase() !== stName.toLowerCase()) {
                    target.setStyle({ weight: 2, color: '#11682f' });
                  }
                },
                mouseout: (e) => {
                  const target = e.target;
                  if (selectedStateName?.toLowerCase() !== stName.toLowerCase()) {
                    target.setStyle(getStateStyle(feature));
                  }
                },
              });
            }}
          />
        )}

        {/* National Boundary Line */}
        {indiaBoundary && (
          <GeoJSON
            data={indiaBoundary}
            style={{ color: '#111827', weight: 2.2, opacity: 0.95, fill: false }}
          />
        )}

        {/* Observation Markers (Shown in OBSERVATIONS mode, or when selected in state) */}
        {mapMode === 'OBSERVATIONS' &&
          observations.map((obs) => {
            if (
              typeof obs.latitude !== 'number' ||
              typeof obs.longitude !== 'number' ||
              !Number.isFinite(obs.latitude) ||
              !Number.isFinite(obs.longitude)
            ) {
              return null;
            }

            const isSensitive = obs.metadata?.is_fuzzy || (obs as any).is_fuzzy;
            const markerColor = obs.verification_status === 'VERIFIED' ? '#10b981' : '#f59e0b';

            return (
              <Marker
                key={`obs-${obs.id}`}
                position={[obs.latitude, obs.longitude]}
                icon={createCustomIcon(
                  markerColor,
                  selectedObservationId === obs.id,
                  Boolean(isSensitive)
                )}
                eventHandlers={
                  onObservationClick
                    ? {
                        click: () => onObservationClick(obs),
                      }
                    : undefined
                }
              >
                <Popup>
                  <div className="text-gray-900 text-xs font-sans w-52 p-1">
                    {obs.species_image_url && (
                      <div className="w-full h-24 mb-2 overflow-hidden rounded bg-gray-100">
                        <img
                          src={obs.species_image_url}
                          alt={obs.species_name}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    )}
                    <strong className="block text-sm text-emerald-800 font-bold">
                      {obs.species_name || `Observation #${obs.id}`}
                    </strong>
                    <div className="font-serif italic text-gray-600 text-[11px] mb-1">
                      {obs.metadata?.species_scientific_name || ''}
                    </div>

                    <p className="my-1">
                      <strong>Coordinates:</strong>{' '}
                      {obs.latitude.toFixed(3)}, {obs.longitude.toFixed(3)}
                      {isSensitive && (
                        <span className="ml-1 text-[9px] font-mono px-1 bg-amber-100 text-amber-800 rounded">
                          Fuzzed (Protection)
                        </span>
                      )}
                    </p>

                    <p className="my-1">
                      {observationCount(obs) !== undefined && (
                        <>
                          <strong>Count:</strong> {observationCount(obs)} |{' '}
                        </>
                      )}
                      <strong>Status:</strong>{' '}
                      <span className="font-semibold">{obs.verification_status}</span>
                    </p>

                    {obs.provenance && (
                      <p className="text-[10px] text-gray-500 font-mono my-0.5">
                        Source: {obs.provenance}
                      </p>
                    )}

                    {observationDate(obs) && (
                      <span className="text-[10px] text-gray-400 font-mono block mt-1">
                        Date: {observationDate(obs)}
                      </span>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}

        {/* Protected Areas / Locations */}
        {mapMode === 'OBSERVATIONS' &&
          locations.map((loc) => {
            if (
              loc.latitude === undefined ||
              loc.latitude === null ||
              loc.longitude === undefined ||
              loc.longitude === null
            )
              return null;

            return (
              <Marker
                key={`loc-${loc.id}`}
                position={[loc.latitude, loc.longitude]}
                icon={createCustomIcon('#0284c7')}
              >
                <Popup>
                  <div className="text-gray-900 text-xs font-sans p-1">
                    <strong className="block text-sm text-sky-800 font-bold">{loc.name}</strong>
                    <p className="my-1 text-gray-600">
                      <strong>State:</strong> {loc.state || 'India'}
                    </p>
                    {loc.is_protected_area && (
                      <span className="bg-sky-100 text-sky-800 font-semibold px-1.5 py-0.5 rounded text-[10px]">
                        Protected Reserve
                      </span>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}
      </MapContainer>

      {boundaryError && (
        <div className="absolute bottom-2 left-2 z-[1000] bg-white/90 border border-red-200 text-red-700 text-[10px] px-2 py-1 rounded shadow">
          India boundary layer preview mode
        </div>
      )}
    </div>
  );
};

// ============================================================
// DYNAMIC MAP LEGEND
// ============================================================

export const MapLegend: React.FC<{
  mapMode?: MapMode;
  choroplethShading?: ChoroplethShading;
}> = ({ mapMode = 'OBSERVATIONS', choroplethShading = 'SPECIES_RICHNESS' }) => {
  if (mapMode === 'CHOROPLETH') {
    const isRichness = choroplethShading === 'SPECIES_RICHNESS';
    const shades = isRichness
      ? [
          { color: '#f5f3ee', label: '0' },
          { color: '#a7f3d0', label: '1 - 20' },
          { color: '#6ee7b7', label: '21 - 50' },
          { color: '#10b981', label: '51 - 100' },
          { color: '#047857', label: '101 - 200' },
          { color: '#064e3b', label: '200+' },
        ]
      : [
          { color: '#f5f3ee', label: '0' },
          { color: '#bfdbfe', label: '1 - 50' },
          { color: '#93c5fa', label: '51 - 300' },
          { color: '#60a5fa', label: '301 - 1,000' },
          { color: '#2563eb', label: '1,001 - 2,500' },
          { color: '#1e3a8a', label: '2,500+' },
        ];

    return (
      <div className="flex flex-wrap items-center gap-3 text-[10px] font-mono text-[#5e5b54] px-1 bg-white/80 p-2 rounded border border-[#e2ded5]">
        <span className="font-bold text-[#1f1e1a] uppercase">
          {isRichness ? 'Species Richness:' : choroplethShading === 'VERIFIED_RECORDS' ? 'Verified Records:' : 'Total Records:'}
        </span>
        {shades.map((s) => (
          <span key={s.label} className="flex items-center gap-1.5">
            <span
              className="w-3 h-3 rounded-xs border border-black/20"
              style={{ backgroundColor: s.color }}
            />
            <span>{s.label}</span>
          </span>
        ))}
      </div>
    );
  }

  if (mapMode === 'INTELLIGENCE') {
    return (
      <div className="flex flex-wrap items-center gap-3 text-[10px] font-mono text-[#5e5b54] px-1 bg-white/80 p-2 rounded border border-[#e2ded5]">
        <span className="font-bold text-[#1f1e1a] uppercase">Conservation Threat & Risk:</span>
        {[
          { color: '#10b981', label: 'Low Ecological Pressure' },
          { color: '#eab308', label: 'Moderate Risk' },
          { color: '#ea580c', label: 'High Priority' },
          { color: '#991b1b', label: 'Critical Threat Level' },
        ].map((s) => (
          <span key={s.label} className="flex items-center gap-1.5">
            <span
              className="w-3 h-3 rounded-xs border border-black/20"
              style={{ backgroundColor: s.color }}
            />
            <span>{s.label}</span>
          </span>
        ))}
      </div>
    );
  }

  // OBSERVATIONS mode
  return (
    <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-[#5e5b54] px-1">
      <span className="flex items-center gap-1.5">
        <span className="w-2.5 h-2.5 rounded-full bg-[#10b981] shadow-[0_0_6px_#10b981]" />
        Verified Observation
      </span>
      <span className="flex items-center gap-1.5">
        <span className="w-2.5 h-2.5 rounded-full bg-[#f59e0b] shadow-[0_0_6px_#f59e0b]" />
        Pending / Citizen Record
      </span>
      <span className="flex items-center gap-1.5">
        <span className="w-2.5 h-2.5 rounded-full bg-[#0284c7] shadow-[0_0_6px_#0284c7]" />
        Protected Reserve Locus
      </span>
      <span className="flex items-center gap-1.5">
        <span className="w-2.5 h-2.5 rounded-full border-2 border-dashed border-[#f59e0b]" />
        Obfuscated Grid (CR/EN Species)
      </span>
      <span className="flex items-center gap-1.5">
        <span className="w-4 h-[2px] bg-[#111827]" />
        Authoritative State Boundary
      </span>
    </div>
  );
};