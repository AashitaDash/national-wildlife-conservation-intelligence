import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { PawPrint, Search, ArrowRight, X } from 'lucide-react';
import { speciesService } from '../services/api';
import { Species } from '../types';
import { DemoBanner } from '../components/DemoBanner';
import { SkeletonCardGrid } from '../components/Skeleton';
import { EmptyState } from '../components/EmptyState';
import { errorMessage } from '../utils/format';

// ── IUCN Status badge ───────────────────────────────────
const IUCN_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  CR: { bg: '#fff1f0', text: '#b91c1c', border: '#fca5a5' },
  EN: { bg: '#fff7ed', text: '#c2410c', border: '#fdba74' },
  VU: { bg: '#fffbeb', text: '#b45309', border: '#fcd34d' },
  NT: { bg: '#fefce8', text: '#854d0e', border: '#fde68a' },
  LC: { bg: '#f0fdf4', text: '#15803d', border: '#86efac' },
  EX: { bg: '#f8f8f7', text: '#57534e', border: '#d6d3d1' },
  EW: { bg: '#f8f8f7', text: '#57534e', border: '#d6d3d1' },
};

const IUCNBadge: React.FC<{ status: string }> = ({ status }) => {
  const style = IUCN_STYLES[status] ?? { bg: '#f8f8f7', text: '#57534e', border: '#d6d3d1' };
  return (
    <span
      className="font-mono text-[10px] font-bold px-1.5 py-0.5 shrink-0"
      style={{
        backgroundColor: style.bg,
        color: style.text,
        border: `1px solid ${style.border}`,
        borderRadius: '2px',
        letterSpacing: '0.08em',
      }}
    >
      {status}
    </span>
  );
};

// ── Species card ────────────────────────────────────────
const SpeciesCard: React.FC<{ sp: Species; delay: number }> = ({ sp, delay }) => (
  <Link
    to={`/species/${sp.id}`}
    className="group bg-white border flex flex-col justify-between transition-all hover:shadow-md animate-fade-slide-in"
    style={{
      borderColor: '#e5e0d8',
      borderRadius: '3px',
      padding: '20px',
      animationDelay: `${delay}ms`,
    }}
    onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = '#16a34a'; }}
    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = '#e5e0d8'; }}
  >
    <div>
      {sp.image_url ? (
        <div className="w-full h-40 mb-3 bg-[#f0ede6] overflow-hidden" style={{ borderRadius: '2px' }}>
          <img src={sp.image_url} alt={sp.common_name} className="w-full h-full object-cover transition-transform hover:scale-105" />
        </div>
      ) : (
        <div className="w-full h-40 mb-3 bg-[#f0ede6] flex items-center justify-center text-[#94918a] text-[10px] tracking-widest font-mono" style={{ borderRadius: '2px' }}>
          NO VERIFIED IMAGE
        </div>
      )}
      {/* Species header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="min-w-0">
          <h3
            className="font-serif font-bold text-base leading-tight transition-colors"
            style={{ color: '#1a1916', fontFamily: "'Newsreader', Georgia, serif" }}
          >
            {sp.common_name}
          </h3>
          <span
            className="font-serif text-xs italic block mt-0.5"
            style={{ color: '#77746c' }}
          >
            {sp.scientific_name}
          </span>
        </div>
        {(sp.iucn_category || sp.conservation_status) && <IUCNBadge status={sp.iucn_category || sp.conservation_status!} />}
      </div>

      <div className="mb-4">
        <span className="font-mono text-[9px] tracking-widest uppercase block mb-1" style={{ color: '#94918a' }}>RECORDED OBSERVATIONS</span>
        <span className="font-mono text-sm font-semibold" style={{ color: '#1a1916' }}>{sp.total_observations ?? 0}</span>
      </div>

      {/* Description */}
      <p
        className="text-xs leading-relaxed mb-4 line-clamp-3"
        style={{ color: '#5e5b54' }}
      >
        {sp.description || 'No description available for this species.'}
      </p>

      {/* IUCN label */}
      {(sp.iucn_category || sp.conservation_status) && (
        <div className="mb-3">
          <span
            className="font-mono text-[9px] tracking-widest uppercase"
            style={{ color: '#94918a' }}
          >
            Official Conservation Status ·{' '}
          </span>
          <span className="font-mono text-[9px] tracking-widest uppercase font-semibold" style={{ color: '#1a1916' }}>
            IUCN Red List
          </span>
        </div>
      )}
    </div>

    {/* CTA */}
    <div
      className="flex items-center justify-between text-[11px] font-mono font-semibold tracking-wide transition-all"
      style={{ color: '#13843a', paddingTop: '12px', borderTop: '1px solid #f0ede6' }}
    >
      <span>VIEW INTELLIGENCE PROFILE</span>
      <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
    </div>
  </Link>
);

// ── Page ────────────────────────────────────────────────
export const SpeciesCatalogPage: React.FC = () => {
  const [speciesList, setSpeciesList] = useState<Species[]>([]);
  const [searchFilter, setSearchFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const loadSpecies = async (page: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await speciesService.getSpeciesList(page, 24);
      setSpeciesList(res.items);
      setCurrentPage(res.page || 1);
      setTotalPages(res.total_pages || 1);
      setTotalCount(res.total || res.items.length);
    } catch (err) {
      setError(errorMessage(err, 'Could not load the species catalog'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadSpecies(currentPage); }, [currentPage]);

  const filteredList = speciesList.filter(s =>
    (s.common_name    || '').toLowerCase().includes(searchFilter.toLowerCase()) ||
    (s.scientific_name || '').toLowerCase().includes(searchFilter.toLowerCase()),
  );

  return (
    <div className="space-y-6 animate-fade-slide-in">
      <DemoBanner />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <p className="font-mono text-[10px] tracking-widest uppercase font-semibold mb-1" style={{ color: '#13843a' }}>
            SPECIES INTELLIGENCE
          </p>
          <h1
            className="font-serif text-3xl font-bold"
            style={{ color: '#1a1916', fontFamily: "'Newsreader', Georgia, serif" }}
          >
            Species Registry
          </h1>
          <p className="text-sm mt-1" style={{ color: '#77746c' }}>
            Verified IUCN Red List status & multi-factor ML risk monitoring.
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: '#b5b3a9' }} />
          <input
            type="text"
            value={searchFilter}
            onChange={e => setSearchFilter(e.target.value)}
            placeholder="Filter by name..."
            className="w-full pl-9 pr-8 py-2 text-xs outline-none transition-all"
            style={{
              backgroundColor: '#ffffff',
              border: '1px solid #ddd8cf',
              borderRadius: '3px',
              color: '#1a1916',
            }}
            onFocus={e => { e.target.style.borderColor = '#16a34a'; }}
            onBlur={e  => { e.target.style.borderColor = '#ddd8cf'; }}
          />
          {searchFilter && (
            <button
              onClick={() => setSearchFilter('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2"
              style={{ color: '#b5b3a9' }}
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <SkeletonCardGrid count={6} />
      ) : error ? (
        <EmptyState variant="error" title="Species catalog unavailable" description={error} actionLabel="Retry" onAction={() => loadSpecies(currentPage)} />
      ) : filteredList.length === 0 ? (
        <EmptyState
          icon={PawPrint}
          variant="empty"
          title={searchFilter ? `No species match "${searchFilter}"` : 'No species records available'}
          description={searchFilter ? 'Try a different common or scientific name.' : 'Species data will appear once available.'}
          actionLabel={searchFilter ? 'Clear filter' : undefined}
          onAction={searchFilter ? () => setSearchFilter('') : undefined}
        />
      ) : (
        <>
          <p className="font-mono text-[10px] tracking-widest uppercase" style={{ color: '#94918a' }}>
            {searchFilter ? `${filteredList.length} species records matching filter` : `SHOWING ${speciesList.length} OF ${totalCount} SPECIES RECORDS`}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredList.map((sp, idx) => (
              <SpeciesCard key={sp.id} sp={sp} delay={idx * 40} />
            ))}
          </div>
          
          {/* Pagination Controls */}
          {totalPages > 1 && !searchFilter && (
            <div className="flex items-center justify-center space-x-4 mt-8">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                className="px-4 py-2 font-mono text-[11px] font-semibold tracking-wider transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ backgroundColor: '#f0ede6', color: '#5e5b54', borderRadius: '3px' }}
              >
                PREVIOUS
              </button>
              <span className="font-mono text-[11px] font-semibold tracking-wider" style={{ color: '#77746c' }}>
                PAGE {currentPage} OF {totalPages}
              </span>
              <button
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                className="px-4 py-2 font-mono text-[11px] font-semibold tracking-wider transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ backgroundColor: '#13843a', color: '#ffffff', borderRadius: '3px' }}
              >
                NEXT
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};
