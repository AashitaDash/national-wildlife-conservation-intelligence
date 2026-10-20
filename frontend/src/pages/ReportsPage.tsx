import React, { useEffect, useState, useCallback } from 'react';
import {
  FileDown,
  FileText,
  FileSpreadsheet,
  FilePieChart,
  RefreshCw,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
  Filter,
  Loader2,
} from 'lucide-react';
import {
  reportsService,
  ReportTypeMetadata,
  ReportFilterOptions,
  ReportPreviewResponse,
} from '../services/api';
import { DemoBanner } from '../components/DemoBanner';
import { errorMessage } from '../utils/format';

// ── Design atoms ─────────────────────────────────────────────────────────────

const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div
    className={`bg-white border ${className}`}
    style={{
      borderColor: '#e5e0d8',
      borderRadius: '3px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
    }}
  >
    {children}
  </div>
);

const SectionLabel: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <p
    className="font-mono text-[10px] font-semibold tracking-widest uppercase mb-3"
    style={{ color: '#94918a' }}
  >
    {children}
  </p>
);

const Pill: React.FC<{ label: string; active?: boolean; onClick: () => void }> = ({
  label,
  active,
  onClick,
}) => (
  <button
    onClick={onClick}
    className="font-mono text-[9px] font-semibold tracking-widest uppercase px-2.5 py-1 rounded-sm border transition-all"
    style={{
      backgroundColor: active ? '#11682f' : 'transparent',
      color: active ? '#a7ebba' : '#5e5b54',
      borderColor: active ? '#11682f' : '#d9d4cc',
    }}
  >
    {label}
  </button>
);

const FormatIcon: React.FC<{ fmt: string; size?: number }> = ({ fmt, size = 14 }) => {
  if (fmt === 'PDF') return <FilePieChart size={size} />;
  if (fmt === 'XLSX') return <FileSpreadsheet size={size} />;
  return <FileText size={size} />;
};

const FORMAT_COLOR: Record<string, string> = {
  PDF: '#dc2626',
  XLSX: '#16a34a',
  CSV: '#2563eb',
};

// ── Filter panel ─────────────────────────────────────────────────────────────

const TAXONOMIC_CLASSES = ['Aves', 'Mammalia', 'Reptilia', 'Amphibia'];
const IUCN_CATEGORIES = ['CR', 'EN', 'VU', 'NT', 'LC'];

interface FilterPanelProps {
  filters: ReportFilterOptions;
  availableFilters: string[];
  onChange: (f: ReportFilterOptions) => void;
}

const FilterPanel: React.FC<FilterPanelProps> = ({ filters, availableFilters, onChange }) => {
  const has = (key: string) => availableFilters.includes(key);

  return (
    <Card className="p-4">
      <SectionLabel>Report Filters</SectionLabel>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {has('taxonomic_class') && (
          <div>
            <label
              className="block font-mono text-[9px] tracking-widest uppercase mb-1"
              style={{ color: '#94918a' }}
            >
              Taxonomic Class
            </label>
            <select
              value={filters.taxonomic_class ?? ''}
              onChange={(e) =>
                onChange({ ...filters, taxonomic_class: e.target.value || undefined })
              }
              className="w-full font-mono text-[11px] border px-2 py-1.5 rounded-sm"
              style={{ borderColor: '#d9d4cc', color: '#2c2a26', backgroundColor: '#faf8f4' }}
            >
              <option value="">All Classes</option>
              {TAXONOMIC_CLASSES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        )}

        {has('iucn_category') && (
          <div>
            <label
              className="block font-mono text-[9px] tracking-widest uppercase mb-1"
              style={{ color: '#94918a' }}
            >
              IUCN Category
            </label>
            <select
              value={filters.iucn_category ?? ''}
              onChange={(e) =>
                onChange({ ...filters, iucn_category: e.target.value || undefined })
              }
              className="w-full font-mono text-[11px] border px-2 py-1.5 rounded-sm"
              style={{ borderColor: '#d9d4cc', color: '#2c2a26', backgroundColor: '#faf8f4' }}
            >
              <option value="">All Categories</option>
              {IUCN_CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        )}

        {has('start_date') && (
          <div>
            <label
              className="block font-mono text-[9px] tracking-widest uppercase mb-1"
              style={{ color: '#94918a' }}
            >
              From Date
            </label>
            <input
              type="date"
              value={filters.start_date ?? ''}
              onChange={(e) =>
                onChange({ ...filters, start_date: e.target.value || undefined })
              }
              className="w-full font-mono text-[11px] border px-2 py-1.5 rounded-sm"
              style={{ borderColor: '#d9d4cc', color: '#2c2a26', backgroundColor: '#faf8f4' }}
            />
          </div>
        )}

        {has('end_date') && (
          <div>
            <label
              className="block font-mono text-[9px] tracking-widest uppercase mb-1"
              style={{ color: '#94918a' }}
            >
              To Date
            </label>
            <input
              type="date"
              value={filters.end_date ?? ''}
              onChange={(e) => onChange({ ...filters, end_date: e.target.value || undefined })}
              className="w-full font-mono text-[11px] border px-2 py-1.5 rounded-sm"
              style={{ borderColor: '#d9d4cc', color: '#2c2a26', backgroundColor: '#faf8f4' }}
            />
          </div>
        )}

        <div>
          <label
            className="block font-mono text-[9px] tracking-widest uppercase mb-1"
            style={{ color: '#94918a' }}
          >
            Max Rows
          </label>
          <select
            value={filters.limit ?? 1000}
            onChange={(e) => onChange({ ...filters, limit: Number(e.target.value) })}
            className="w-full font-mono text-[11px] border px-2 py-1.5 rounded-sm"
            style={{ borderColor: '#d9d4cc', color: '#2c2a26', backgroundColor: '#faf8f4' }}
          >
            {[250, 500, 1000, 2000, 5000].map((n) => (
              <option key={n} value={n}>
                {n.toLocaleString()} rows
              </option>
            ))}
          </select>
        </div>
      </div>
    </Card>
  );
};

// ── Preview panel ─────────────────────────────────────────────────────────────

interface PreviewPanelProps {
  preview: ReportPreviewResponse;
}

const PreviewPanel: React.FC<PreviewPanelProps> = ({ preview }) => (
  <Card className="p-4">
    <SectionLabel>Live Preview — {preview.title}</SectionLabel>

    {/* Summary metrics */}
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
      <div
        className="rounded-sm p-3 text-center border"
        style={{ backgroundColor: '#f0f7f2', borderColor: '#c8e6d0' }}
      >
        <p className="font-mono text-[9px] tracking-widest uppercase" style={{ color: '#389956' }}>
          Est. Records
        </p>
        <p className="font-mono text-xl font-bold mt-0.5" style={{ color: '#11682f' }}>
          {preview.estimated_records.toLocaleString()}
        </p>
      </div>
      {Object.entries(preview.summary_metrics)
        .slice(0, 3)
        .map(([key, val]) => (
          <div
            key={key}
            className="rounded-sm p-3 text-center border"
            style={{ backgroundColor: '#faf8f4', borderColor: '#e5e0d8' }}
          >
            <p
              className="font-mono text-[9px] tracking-widest uppercase"
              style={{ color: '#94918a' }}
            >
              {key.replace(/_/g, ' ')}
            </p>
            <p className="font-mono text-lg font-bold mt-0.5" style={{ color: '#2c2a26' }}>
              {typeof val === 'number' ? val.toLocaleString() : String(val)}
            </p>
          </div>
        ))}
    </div>

    {/* Sections */}
    <div className="mb-4">
      <p
        className="font-mono text-[9px] font-semibold tracking-widest uppercase mb-2"
        style={{ color: '#94918a' }}
      >
        Report Sections
      </p>
      <div className="flex flex-wrap gap-1.5">
        {preview.sections.map((s) => (
          <span
            key={s}
            className="font-mono text-[9px] px-2 py-0.5 rounded-sm border"
            style={{
              backgroundColor: '#f0f7f2',
              color: '#11682f',
              borderColor: '#c8e6d0',
            }}
          >
            {s}
          </span>
        ))}
      </div>
    </div>

    {/* Scientific limitations */}
    {preview.scientific_limitations.length > 0 && (
      <div
        className="rounded-sm p-3 border"
        style={{ backgroundColor: '#fffbeb', borderColor: '#fde68a' }}
      >
        <div className="flex items-center gap-1.5 mb-1.5">
          <AlertTriangle size={11} style={{ color: '#d97706' }} />
          <span
            className="font-mono text-[9px] font-semibold tracking-widest uppercase"
            style={{ color: '#d97706' }}
          >
            Data Caveats
          </span>
        </div>
        <ul className="space-y-0.5">
          {preview.scientific_limitations.map((lim, i) => (
            <li key={i} className="font-mono text-[10px]" style={{ color: '#78716c' }}>
              • {lim}
            </li>
          ))}
        </ul>
      </div>
    )}
  </Card>
);

// ── Download button ───────────────────────────────────────────────────────────

interface DownloadButtonProps {
  fmt: string;
  reportType: string;
  filters: ReportFilterOptions;
  disabled?: boolean;
}

const DownloadButton: React.FC<DownloadButtonProps> = ({
  fmt,
  reportType,
  filters,
  disabled,
}) => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const handleDownload = async () => {
    setLoading(true);
    setErr(null);
    setSuccess(false);
    try {
      const { blob, filename } = await reportsService.generate(reportType, fmt, filters);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (e) {
      setErr(errorMessage(e, 'Download failed'));
    } finally {
      setLoading(false);
    }
  };

  const color = FORMAT_COLOR[fmt] ?? '#5e5b54';

  return (
    <div className="flex flex-col items-center gap-1">
      <button
        onClick={handleDownload}
        disabled={disabled || loading}
        className="flex items-center gap-2 px-4 py-2.5 rounded-sm border font-mono text-[11px] font-semibold tracking-wider uppercase transition-all"
        style={{
          backgroundColor: disabled || loading ? '#f4f1eb' : '#faf8f4',
          color: disabled || loading ? '#94918a' : color,
          borderColor: disabled || loading ? '#d9d4cc' : color,
          cursor: disabled || loading ? 'not-allowed' : 'pointer',
          minWidth: '110px',
          justifyContent: 'center',
        }}
      >
        {loading ? (
          <Loader2 size={13} className="animate-spin" />
        ) : success ? (
          <CheckCircle size={13} style={{ color: '#16a34a' }} />
        ) : (
          <FormatIcon fmt={fmt} size={13} />
        )}
        {loading ? 'Building…' : success ? 'Saved!' : fmt}
      </button>
      {err && (
        <p className="font-mono text-[9px] text-red-600 text-center max-w-[120px]">{err}</p>
      )}
    </div>
  );
};

// ── Main page ─────────────────────────────────────────────────────────────────

export const ReportsPage: React.FC = () => {
  const [types, setTypes] = useState<ReportTypeMetadata[]>([]);
  const [selected, setSelected] = useState<ReportTypeMetadata | null>(null);
  const [filters, setFilters] = useState<ReportFilterOptions>({ limit: 1000 });
  const [preview, setPreview] = useState<ReportPreviewResponse | null>(null);
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [typesError, setTypesError] = useState<string | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Load report templates on mount
  useEffect(() => {
    (async () => {
      setLoadingTypes(true);
      setTypesError(null);
      try {
        const data = await reportsService.getTypes();
        setTypes(data);
        if (data.length > 0) setSelected(data[0]);
      } catch (e) {
        setTypesError(errorMessage(e, 'Failed to load report templates'));
      } finally {
        setLoadingTypes(false);
      }
    })();
  }, []);

  // Fetch preview whenever type or filters change
  const fetchPreview = useCallback(async () => {
    if (!selected) return;
    setLoadingPreview(true);
    setPreviewError(null);
    setPreview(null);
    try {
      const data = await reportsService.getPreview(selected.type_id, filters);
      setPreview(data);
    } catch (e) {
      setPreviewError(errorMessage(e, 'Preview unavailable'));
    } finally {
      setLoadingPreview(false);
    }
  }, [selected, filters]);

  useEffect(() => {
    fetchPreview();
  }, [fetchPreview]);

  // Reset filters when template changes
  const selectTemplate = (t: ReportTypeMetadata) => {
    setSelected(t);
    setFilters({ limit: 1000 });
    setShowFilters(false);
  };

  return (
    <div className="space-y-6 animate-fade-slide-in">
      <DemoBanner />

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <p
            className="font-mono text-[10px] tracking-widest uppercase font-semibold mb-1"
            style={{ color: '#11682f' }}
          >
            Conservation Intelligence
          </p>
          <h1 className="text-2xl font-bold tracking-tight" style={{ color: '#1a1916' }}>
            Reports &amp; Exports
          </h1>
          <p className="mt-1 text-sm" style={{ color: '#78716c' }}>
            Generate institutional-grade conservation reports from live database records.
          </p>
        </div>
      </div>

      {/* ── Template selector ── */}
      <Card className="p-4">
        <SectionLabel>Select Report Template</SectionLabel>
        {loadingTypes && (
          <div className="flex items-center gap-2 py-4">
            <Loader2 size={14} className="animate-spin" style={{ color: '#11682f' }} />
            <span className="font-mono text-[11px]" style={{ color: '#94918a' }}>
              Loading templates…
            </span>
          </div>
        )}
        {typesError && (
          <div
            className="flex items-center gap-2 p-3 rounded-sm border"
            style={{ backgroundColor: '#fef2f2', borderColor: '#fca5a5', color: '#dc2626' }}
          >
            <AlertTriangle size={13} />
            <span className="font-mono text-[11px]">{typesError}</span>
          </div>
        )}
        {!loadingTypes && !typesError && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {types.map((t) => {
              const isActive = selected?.type_id === t.type_id;
              return (
                <button
                  key={t.type_id}
                  onClick={() => selectTemplate(t)}
                  className="text-left p-3 rounded-sm border transition-all"
                  style={{
                    backgroundColor: isActive ? '#f0f7f2' : '#faf8f4',
                    borderColor: isActive ? '#11682f' : '#e5e0d8',
                    boxShadow: isActive ? '0 0 0 2px #c8e6d0' : 'none',
                  }}
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <p
                      className="font-mono text-[10px] font-semibold tracking-wide"
                      style={{ color: isActive ? '#11682f' : '#2c2a26' }}
                    >
                      {t.name}
                    </p>
                    {isActive && (
                      <ChevronRight size={12} style={{ color: '#11682f', flexShrink: 0 }} />
                    )}
                  </div>
                  <p className="text-[11px] leading-relaxed" style={{ color: '#78716c' }}>
                    {t.description}
                  </p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {t.supported_formats.map((f) => (
                      <span
                        key={f}
                        className="font-mono text-[8px] font-bold px-1.5 py-0.5 rounded-sm"
                        style={{
                          backgroundColor: `${FORMAT_COLOR[f] ?? '#5e5b54'}18`,
                          color: FORMAT_COLOR[f] ?? '#5e5b54',
                        }}
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </Card>

      {/* ── Filter toggle + panel ── */}
      {selected && (
        <>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilters((v) => !v)}
              className="flex items-center gap-1.5 font-mono text-[10px] font-semibold tracking-widest uppercase px-3 py-1.5 rounded-sm border transition-all"
              style={{
                backgroundColor: showFilters ? '#11682f' : 'transparent',
                color: showFilters ? '#a7ebba' : '#5e5b54',
                borderColor: showFilters ? '#11682f' : '#d9d4cc',
              }}
            >
              <Filter size={10} />
              {showFilters ? 'Hide Filters' : 'Apply Filters'}
            </button>
            {showFilters && (
              <button
                onClick={() => setFilters({ limit: 1000 })}
                className="flex items-center gap-1 font-mono text-[10px] uppercase tracking-wider px-2 py-1.5 rounded-sm border"
                style={{ color: '#94918a', borderColor: '#d9d4cc' }}
              >
                <RefreshCw size={9} />
                Reset
              </button>
            )}
          </div>

          {showFilters && (
            <FilterPanel
              filters={filters}
              availableFilters={selected.available_filters}
              onChange={setFilters}
            />
          )}
        </>
      )}

      {/* ── Preview panel ── */}
      {selected && (
        <div className="space-y-3">
          {loadingPreview && (
            <Card className="p-6 flex items-center gap-3">
              <Loader2 size={16} className="animate-spin" style={{ color: '#11682f' }} />
              <span className="font-mono text-[11px]" style={{ color: '#94918a' }}>
                Calculating report scope from live data…
              </span>
            </Card>
          )}

          {previewError && !loadingPreview && (
            <Card className="p-4">
              <div
                className="flex items-center gap-2 p-3 rounded-sm border"
                style={{ backgroundColor: '#fef2f2', borderColor: '#fca5a5', color: '#dc2626' }}
              >
                <AlertTriangle size={13} />
                <span className="font-mono text-[11px]">{previewError}</span>
              </div>
            </Card>
          )}

          {preview && !loadingPreview && <PreviewPanel preview={preview} />}
        </div>
      )}

      {/* ── Download bar ── */}
      {selected && preview && !loadingPreview && (
        <Card className="p-4">
          <SectionLabel>Download Report</SectionLabel>
          <p className="font-mono text-[11px] mb-4" style={{ color: '#78716c' }}>
            Generating <strong style={{ color: '#2c2a26' }}>{preview.title}</strong> —
            approximately{' '}
            <strong style={{ color: '#11682f' }}>
              {preview.estimated_records.toLocaleString()} records
            </strong>
          </p>
          <div className="flex flex-wrap gap-3">
            {selected.supported_formats.map((fmt) => (
              <DownloadButton
                key={fmt}
                fmt={fmt}
                reportType={selected.type_id}
                filters={filters}
              />
            ))}
          </div>
          <p className="font-mono text-[9px] mt-3" style={{ color: '#c0bdb6' }}>
            All reports are generated in real-time from the live database. Downloaded files
            contain actual conservation records and should be handled according to your
            organisation's data governance policy.
          </p>
        </Card>
      )}

      {/* ── Empty state before template selection ── */}
      {!loadingTypes && !typesError && types.length === 0 && (
        <Card className="p-8 text-center">
          <FileDown size={32} className="mx-auto mb-3" style={{ color: '#c0bdb6' }} />
          <p className="font-mono text-sm font-semibold" style={{ color: '#5e5b54' }}>
            No report templates available
          </p>
          <p className="font-mono text-[11px] mt-1" style={{ color: '#94918a' }}>
            The backend returned an empty template list. Check that the reports service is
            running.
          </p>
        </Card>
      )}
    </div>
  );
};
