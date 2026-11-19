import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  FileText,
  Sparkles,
  Layers,
  MapPin,
  Building2,
  CalendarDays,
  ShieldAlert,
  ChevronDown,
  Shield,
  Upload,
  File as FileIcon,
  X,
  CheckCircle2,
  AlertCircle,
  BookOpen,
  HelpCircle,
  Trash2,
  Search,
  AlertTriangle,
} from 'lucide-react';
import { nlpService, nlpIntelligenceService, SynthesisResult, QAResult, SourceDocumentSummary } from '../services/api';
import { NLPAnalysisResult } from '../types';
import { DemoBanner } from '../components/DemoBanner';
import { NLPSummaryBox } from '../components/NLPSummaryBox';
import { EmptyState } from '../components/EmptyState';
import { entityLabel } from '../utils/format';

const EntityChip: React.FC<{ label: string; colorClass: string }> = ({ label, colorClass }) => (
  <span className={`inline-flex items-center px-2 py-0.5 rounded-sm text-[10px] font-mono font-semibold border ${colorClass}`}>
    {label}
  </span>
);

const MAX_PDF_MB = 10;
const PDF_PROCESSING_STEPS = [
  'Extracting document text\u2026',
  'Analysing conservation entities\u2026',
  'Detecting threats\u2026',
  'Classifying topics\u2026',
  'Generating summary\u2026',
  'Creating 384-d embedding\u2026',
];

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

// Evidence-strength badge
const STRENGTH_STYLE: Record<string, { bg: string; text: string; border: string }> = {
  HIGH:         { bg: 'bg-emerald-50', text: 'text-emerald-800', border: 'border-emerald-300' },
  MEDIUM:       { bg: 'bg-amber-50',   text: 'text-amber-800',   border: 'border-amber-300' },
  LOW:          { bg: 'bg-orange-50',  text: 'text-orange-800',  border: 'border-orange-300' },
  INSUFFICIENT: { bg: 'bg-rose-50',    text: 'text-rose-800',    border: 'border-rose-300' },
};

const EvidenceStrengthBadge: React.FC<{ strength: string; rationale: string }> = ({ strength, rationale }) => {
  const s = STRENGTH_STYLE[strength] || STRENGTH_STYLE.INSUFFICIENT;
  return (
    <div className={`${s.bg} border ${s.border} rounded-sm px-4 py-3`}>
      <div className="flex items-center gap-2 mb-1">
        <Shield className={`w-4 h-4 ${s.text}`} />
        <span className={`text-[10px] font-mono font-bold uppercase tracking-widest ${s.text}`}>
          Evidence Strength: {strength}
        </span>
      </div>
      <p className={`text-[11px] ${s.text}`}>{rationale}</p>
    </div>
  );
};

type MainTab = 'analysis' | 'brief' | 'ask';

// ─── Conservation Brief Tab ───────────────────────────────────────────────────
const ConservationBriefTab: React.FC = () => {
  const [allDocs, setAllDocs] = useState<SourceDocumentSummary[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [searchFilter, setSearchFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SynthesisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAllEvidence, setShowAllEvidence] = useState(false);

  useEffect(() => {
    setDocsLoading(true);
    nlpIntelligenceService.listDocuments()
      .then(docs => setAllDocs(docs))
      .catch(() => setAllDocs([]))
      .finally(() => setDocsLoading(false));
  }, []);

  const filteredDocs = allDocs.filter(d =>
    d.title.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const toggleDoc = (id: number) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const handleGenerate = async () => {
    if (selectedIds.length === 0) { setError('Please select at least one document.'); return; }
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await nlpIntelligenceService.synthesize(selectedIds);
      setResult(res);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Synthesis failed. Please try again.');
    } finally { setLoading(false); }
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="font-mono text-[10px] tracking-widest uppercase font-semibold mb-1 text-emerald-700">MULTI-DOCUMENT NLP SYNTHESIS</p>
        <h2 className="font-serif text-2xl font-bold text-[#1a1916] flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-emerald-700" /> Conservation Intelligence Brief
        </h2>
        <p className="text-sm mt-1 text-[#77746c]">Synthesise evidence across selected conservation documents. All results are grounded in the indexed corpus.</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-[#e5e0d8] p-5 rounded-sm space-y-4">
          <h3 className="text-sm font-semibold text-[#1a1916]">Select Documents</h3>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 w-3.5 h-3.5 text-[#94918a]" />
            <input id="brief-doc-search" type="text" placeholder="Filter by title\u2026" value={searchFilter}
              onChange={e => setSearchFilter(e.target.value)}
              className="w-full pl-8 pr-3 py-2 bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm text-sm text-[#1a1916] focus:outline-none focus:border-emerald-700" />
          </div>
          <div className="border border-[#e5e0d8] rounded-sm overflow-hidden">
            <div className="max-h-64 overflow-y-auto divide-y divide-[#e5e0d8]">
              {docsLoading ? (
                <div className="p-4 text-center text-xs text-[#94918a]">Loading documents\u2026</div>
              ) : filteredDocs.length === 0 ? (
                <div className="p-4 text-center text-xs text-[#94918a]">
                  {allDocs.length === 0 ? 'No indexed documents found.' : 'No matching documents.'}
                </div>
              ) : (
                filteredDocs.map(doc => {
                  const checked = selectedIds.includes(doc.id);
                  return (
                    <label key={doc.id} htmlFor={`doc-check-${doc.id}`}
                      className={`flex items-start gap-3 px-3 py-2.5 cursor-pointer transition-colors ${checked ? 'bg-emerald-50' : 'hover:bg-[#fdfaf5]'}`}>
                      <input id={`doc-check-${doc.id}`} type="checkbox" checked={checked} onChange={() => toggleDoc(doc.id)} className="mt-0.5 accent-emerald-700" />
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-[#1a1916] leading-snug line-clamp-2">{doc.title}</p>
                        <p className="text-[10px] font-mono text-[#94918a] mt-0.5">
                          {doc.source_type}{doc.author ? ` \u00b7 ${doc.author}` : ''} \u00b7 ID {doc.id}
                        </p>
                      </div>
                    </label>
                  );
                })
              )}
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-[#94918a]">{selectedIds.length} document{selectedIds.length !== 1 ? 's' : ''} selected</span>
            {selectedIds.length > 0 && (
              <button onClick={() => setSelectedIds([])} className="text-[10px] font-mono text-rose-600 hover:text-rose-700 flex items-center gap-1">
                <Trash2 className="w-3 h-3" /> Clear all
              </button>
            )}
          </div>
          {error && (
            <div className="flex items-center gap-2 bg-rose-50 border border-rose-200 rounded-sm px-3 py-2 text-xs text-rose-700">
              <AlertCircle className="w-4 h-4 shrink-0" />{error}
            </div>
          )}
          <button id="btn-generate-brief" onClick={handleGenerate} disabled={loading || selectedIds.length === 0}
            className="w-full py-2.5 bg-[#1a1916] hover:bg-[#2c2b26] disabled:opacity-40 text-white font-mono tracking-wide text-xs rounded-sm flex items-center justify-center gap-2 transition-all">
            <Sparkles className="w-4 h-4" />
            {loading ? 'SYNTHESISING CORPUS\u2026' : 'GENERATE INTELLIGENCE BRIEF'}
          </button>
        </div>
        <div className="space-y-4">
          {loading && (
            <div className="bg-[#fdfaf5] border border-[#e5e0d8] p-6 rounded-sm space-y-2">
              <div className="animate-skeleton h-4 w-2/3 bg-[#e5e0d8] rounded-sm" />
              <div className="animate-skeleton h-3 w-full bg-[#e5e0d8] rounded-sm" />
              <div className="animate-skeleton h-3 w-5/6 bg-[#e5e0d8] rounded-sm" />
              <div className="animate-skeleton h-20 w-full bg-[#e5e0d8] rounded-sm mt-2" />
            </div>
          )}
          {!loading && result && (
            <div className="space-y-4 animate-fade-slide-in">
              <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm">
                <div className="flex items-center gap-2 mb-3">
                  <span className="font-mono text-[10px] tracking-widest uppercase font-bold text-emerald-700">Conservation Intelligence Brief</span>
                  <span className="font-mono text-[10px] text-[#94918a]">\u00b7 {result.documents_analyzed} document{result.documents_analyzed !== 1 ? 's' : ''} analysed</span>
                </div>
                {result.conflicting_evidence && (
                  <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-sm px-3 py-2 mb-3 text-xs text-amber-800">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    <strong>Conflicting evidence detected</strong> across retrieved documents. Review source documents carefully.
                  </div>
                )}
                <p className="text-sm text-[#1a1916] leading-relaxed">{result.summary}</p>
              </div>
              {result.species.length > 0 && (
                <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm space-y-2">
                  <h4 className="text-[10px] font-mono font-bold text-[#94918a] uppercase tracking-wider flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-emerald-700" /> Species Identified
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {result.species.map((sp, i) => (
                      <div key={i} className="bg-emerald-50 border border-emerald-200 rounded-sm px-2 py-1">
                        <span className="text-xs font-semibold text-emerald-800">{sp.common_name}</span>
                        {sp.scientific_name && <span className="text-[10px] text-emerald-600 block italic">{sp.scientific_name}</span>}
                        {sp.iucn_category && <span className="text-[9px] font-mono text-emerald-700">{sp.iucn_category}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {result.threats.length > 0 && (
                <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm space-y-2">
                  <h4 className="text-[10px] font-mono font-bold text-[#94918a] uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-rose-600" /> Key Threats
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {result.threats.map((th, i) => (
                      <EntityChip key={i} label={`${th.category_name} \u00b7 ${th.document_count}d`} colorClass="bg-rose-50 text-rose-700 border-rose-200" />
                    ))}
                  </div>
                </div>
              )}
              {result.topics.length > 0 && (
                <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm space-y-2">
                  <h4 className="text-[10px] font-mono font-bold text-[#94918a] uppercase tracking-wider flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-emerald-700" /> Key Topics
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {result.topics.map((tp, i) => (
                      <EntityChip key={i} label={`${tp.topic} \u00b7 ${tp.document_count}d`} colorClass="bg-emerald-50 text-emerald-700 border-emerald-200" />
                    ))}
                  </div>
                </div>
              )}
              <EvidenceStrengthBadge strength={result.evidence_strength} rationale={result.evidence_strength_rationale} />
              {result.evidence.length > 0 && (
                <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm space-y-2">
                  <h4 className="text-[10px] font-mono font-bold text-[#94918a] uppercase tracking-wider">
                    Supporting Evidence ({result.evidence.length} sentences)
                  </h4>
                  {(showAllEvidence ? result.evidence : result.evidence.slice(0, 3)).map((ev, i) => (
                    <div key={i} className="bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm p-3 space-y-1">
                      <p className="text-[11px] text-[#1a1916] leading-relaxed italic">"{ev.sentence}"</p>
                      <p className="text-[10px] font-mono text-[#94918a]">Source: {ev.document_title} \u00b7 Doc ID {ev.document_id}</p>
                    </div>
                  ))}
                  {result.evidence.length > 3 && (
                    <button onClick={() => setShowAllEvidence(v => !v)}
                      className="w-full flex items-center justify-center gap-1 text-[10px] font-mono text-emerald-700 hover:text-emerald-800 py-1.5 font-semibold">
                      {showAllEvidence ? 'SHOW FEWER' : `SHOW ALL ${result.evidence.length}`}
                      <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showAllEvidence ? 'rotate-180' : ''}`} />
                    </button>
                  )}
                </div>
              )}
              {result.source_documents.length > 0 && (
                <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm space-y-2">
                  <h4 className="text-[10px] font-mono font-bold text-[#94918a] uppercase tracking-wider">Source Documents ({result.source_documents.length})</h4>
                  {result.source_documents.map(sd => (
                    <div key={sd.id} className="flex items-start gap-2 bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm px-3 py-2">
                      <FileText className="w-3.5 h-3.5 text-emerald-700 shrink-0 mt-0.5" />
                      <div>
                        <p className="text-xs font-semibold text-[#1a1916]">{sd.title}</p>
                        <p className="text-[10px] font-mono text-[#94918a]">{sd.source_type}{sd.author ? ` \u00b7 ${sd.author}` : ''} \u00b7 ID {sd.id}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          {!loading && !result && (
            <div className="bg-[#fdfaf5] border border-[#e5e0d8] p-8 rounded-sm text-center text-[10px] font-mono text-[#94918a] uppercase tracking-wider">
              Select documents and click \u201cGenerate Intelligence Brief\u201d to synthesise conservation evidence.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ─── Ask the Corpus Tab ───────────────────────────────────────────────────────
const EXAMPLE_QUESTIONS = [
  'What are the major threats to Asian elephants?',
  'Which documents discuss habitat fragmentation?',
  'What conservation issues are associated with Similipal?',
  'Which species are associated with human-wildlife conflict?',
  'What topics are most frequently discussed in the retrieved documents?',
  'Which documents mention agricultural expansion?',
];

const AskTheCorpusTab: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QAResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAllEvidence, setShowAllEvidence] = useState(false);

  const handleAsk = async (q?: string) => {
    const q_text = (q ?? question).trim();
    if (!q_text) { setError('Please enter a question.'); return; }
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await nlpIntelligenceService.ask(q_text, topK);
      setResult(res);
      if (q) setQuestion(q);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Question answering failed. Please try again.');
    } finally { setLoading(false); }
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="font-mono text-[10px] tracking-widest uppercase font-semibold mb-1 text-emerald-700">EVIDENCE-GROUNDED QUESTION ANSWERING</p>
        <h2 className="font-serif text-2xl font-bold text-[#1a1916] flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-emerald-700" /> Ask the Conservation Corpus
        </h2>
        <p className="text-sm mt-1 text-[#77746c]">
          Ask questions across the indexed conservation literature. Answers are grounded in retrieved evidence \u2014 not general knowledge.
        </p>
      </div>
      <div className="bg-white border border-[#e5e0d8] p-5 rounded-sm space-y-4">
        <div>
          <label className="block text-[10px] font-mono text-[#94918a] uppercase tracking-wider mb-1">Your Question</label>
          <textarea id="corpus-question-input" rows={3} value={question} onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAsk(); } }}
            placeholder="Ask a question about the indexed conservation corpus\u2026"
            className="w-full p-3 bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm text-sm text-[#1a1916] focus:outline-none focus:border-emerald-700 font-sans leading-relaxed resize-none" />
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-[10px] font-mono text-[#94918a] uppercase tracking-wider whitespace-nowrap">Top-K documents</label>
            <select value={topK} onChange={e => setTopK(Number(e.target.value))}
              className="px-2 py-1 bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm text-xs text-[#1a1916] focus:outline-none">
              {[3, 5, 8, 10].map(k => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
          <button id="btn-ask-corpus" onClick={() => handleAsk()} disabled={loading || !question.trim()}
            className="flex-1 py-2.5 bg-[#1a1916] hover:bg-[#2c2b26] disabled:opacity-40 text-white font-mono tracking-wide text-xs rounded-sm flex items-center justify-center gap-2 transition-all">
            <HelpCircle className="w-4 h-4" />
            {loading ? 'SEARCHING CORPUS\u2026' : 'ASK THE CORPUS'}
          </button>
        </div>
        {error && (
          <div className="flex items-center gap-2 bg-rose-50 border border-rose-200 rounded-sm px-3 py-2 text-xs text-rose-700">
            <AlertCircle className="w-4 h-4 shrink-0" />{error}
          </div>
        )}
        <div>
          <p className="text-[10px] font-mono text-[#94918a] uppercase tracking-wider mb-2">Example Questions</p>
          <div className="flex flex-wrap gap-1.5">
            {EXAMPLE_QUESTIONS.map((q, i) => (
              <button key={i} onClick={() => handleAsk(q)} disabled={loading}
                className="text-[10px] font-mono border border-[#e5e0d8] bg-[#fdfaf5] hover:border-emerald-400 hover:bg-emerald-50 text-[#77746c] hover:text-emerald-700 px-2 py-1 rounded-sm transition-colors disabled:opacity-50">
                {q}
              </button>
            ))}
          </div>
        </div>
      </div>
      {loading && (
        <div className="bg-[#fdfaf5] border border-[#e5e0d8] p-6 rounded-sm space-y-2">
          <div className="animate-skeleton h-4 w-2/3 bg-[#e5e0d8] rounded-sm" />
          <div className="animate-skeleton h-3 w-full bg-[#e5e0d8] rounded-sm" />
          <div className="animate-skeleton h-3 w-5/6 bg-[#e5e0d8] rounded-sm" />
          <div className="animate-skeleton h-20 w-full bg-[#e5e0d8] rounded-sm mt-2" />
        </div>
      )}
      {!loading && result && (
        <div className="space-y-4 animate-fade-slide-in">
          <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm">
            <p className="text-[10px] font-mono text-[#94918a] uppercase tracking-wider mb-1">Question</p>
            <p className="text-sm font-semibold text-[#1a1916]">{result.question}</p>
          </div>
          {result.conflicting_evidence && (
            <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-sm px-4 py-3 text-xs text-amber-800">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <div>
                <strong className="block">Conflicting Evidence Detected</strong>
                Retrieved documents contain statements that may contradict each other. Review source documents carefully.
              </div>
            </div>
          )}
          <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm">
            <p className="text-[10px] font-mono text-[#94918a] uppercase tracking-wider mb-2">Answer</p>
            <p className="text-sm text-[#1a1916] leading-relaxed">{result.answer}</p>
            {(result.retrieved_species.length > 0 || result.retrieved_threats.length > 0) && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {result.retrieved_species.map((sp, i) => (
                  <EntityChip key={`sp-${i}`} label={sp} colorClass="bg-emerald-50 text-emerald-700 border-emerald-200" />
                ))}
                {result.retrieved_threats.map((th, i) => (
                  <EntityChip key={`th-${i}`} label={th} colorClass="bg-rose-50 text-rose-700 border-rose-200" />
                ))}
              </div>
            )}
          </div>
          <EvidenceStrengthBadge strength={result.evidence_strength} rationale={result.evidence_strength_rationale} />
          {result.evidence.length > 0 && (
            <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm space-y-2">
              <h4 className="text-[10px] font-mono font-bold text-[#94918a] uppercase tracking-wider">
                Supporting Evidence ({result.evidence.length} sentences)
              </h4>
              {(showAllEvidence ? result.evidence : result.evidence.slice(0, 4)).map((ev, i) => (
                <div key={i} className="bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm p-3 space-y-1">
                  <p className="text-[11px] text-[#1a1916] leading-relaxed italic">"{ev.sentence}"</p>
                  <p className="text-[10px] font-mono text-[#94918a]">Source: {ev.document_title} \u00b7 Doc ID {ev.document_id}</p>
                </div>
              ))}
              {result.evidence.length > 4 && (
                <button onClick={() => setShowAllEvidence(v => !v)}
                  className="w-full flex items-center justify-center gap-1 text-[10px] font-mono text-emerald-700 hover:text-emerald-800 py-1.5 font-semibold">
                  {showAllEvidence ? 'SHOW FEWER' : `SHOW ALL ${result.evidence.length}`}
                  <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showAllEvidence ? 'rotate-180' : ''}`} />
                </button>
              )}
            </div>
          )}
          {result.source_documents.length > 0 && (
            <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm space-y-2">
              <h4 className="text-[10px] font-mono font-bold text-[#94918a] uppercase tracking-wider">Source Documents ({result.source_documents.length})</h4>
              {result.source_documents.map(sd => (
                <div key={sd.id} className="flex items-start gap-2 bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm px-3 py-2">
                  <FileText className="w-3.5 h-3.5 text-emerald-700 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-[#1a1916] truncate">{sd.title}</p>
                    <p className="text-[10px] font-mono text-[#94918a]">
                      {sd.source_type} \u00b7 ID {sd.id}
                      {sd.relevance_score != null && ` \u00b7 Relevance ${(sd.relevance_score * 100).toFixed(0)}%`}
                    </p>
                    {sd.snippet && <p className="text-[11px] text-[#77746c] mt-0.5 line-clamp-2">{sd.snippet}</p>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      {!loading && !result && (
        <div className="bg-[#fdfaf5] border border-[#e5e0d8] p-8 rounded-sm text-center text-[10px] font-mono text-[#94918a] uppercase tracking-wider">
          Enter a question or select an example above to query the indexed conservation corpus.
        </div>
      )}
    </div>
  );
};

// ─── Main DocumentsPage ───────────────────────────────────────────────────────
export const DocumentsPage: React.FC = () => {
  const [mainTab, setMainTab] = useState<MainTab>('analysis');

  // Existing Document Analysis state (preserved verbatim)
  const [activeTab, setActiveTab] = useState<'text' | 'pdf'>('text');
  const [nlpResult, setNlpResult] = useState<NLPAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAllThreats, setShowAllThreats] = useState(false);
  const [processingStep, setProcessingStep] = useState(0);
  const [textInput, setTextInput] = useState(
    'Asian elephant habitat loss and corridor fragmentation in Similipal National Park and Keonjhar district of Odisha due to open-cast iron ore mining activities and heavy railway infrastructure expansion.'
  );
  const [docTitle, setDocTitle] = useState('Odisha Elephant Corridor Field Report 2026');
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pdfTitle, setPdfTitle] = useState('');
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const validatePdf = (f: File): string | null => {
    if (!f.name.toLowerCase().endsWith('.pdf')) return 'Only PDF documents are supported.';
    if (f.size === 0) return 'The selected file is empty.';
    if (f.size > MAX_PDF_MB * 1024 * 1024) return `PDF exceeds the ${MAX_PDF_MB} MB limit.`;
    return null;
  };
  const handleFileSelect = (f: File) => {
    const err = validatePdf(f);
    if (err) { setPdfError(err); setPdfFile(null); }
    else { setPdfError(null); setPdfFile(f); if (!pdfTitle) setPdfTitle(f.name.replace(/\.pdf$/i, '')); }
  };
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragOver(false);
    const f = e.dataTransfer.files[0]; if (f) handleFileSelect(f);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pdfTitle]);
  const clearPdf = () => {
    setPdfFile(null); setPdfTitle(''); setPdfError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleCancelAnalysis = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setLoading(false);
    setProcessingStep(0);
    setError('Analysis cancelled by user.');
  };

  const handleAnalyzeText = async () => {
    if (!textInput.trim()) {
      setError('Please enter document text to analyze.');
      return;
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true); setError(null); setNlpResult(null); setProcessingStep(0);
    try {
      const res = await nlpService.analyzeText(textInput, docTitle, controller.signal);
      setNlpResult(res); setShowAllThreats(false);
    } catch (err: any) {
      if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') {
        setError('Analysis cancelled.');
      } else {
        console.error('NLP Analysis failed:', err);
        const detail = err?.response?.data?.detail || err?.message || 'NLP pipeline request failed. Check network or parameters and try again.';
        setError(detail);
      }
    } finally {
      abortControllerRef.current = null;
      setLoading(false);
    }
  };

  const handleAnalyzePdf = async () => {
    if (!pdfFile) { setPdfError('Please select a PDF file before analysing.'); return; }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true); setError(null); setNlpResult(null); setPdfError(null); setShowAllThreats(false);
    let stepIdx = 0;
    const stepTimer = setInterval(() => {
      stepIdx = Math.min(stepIdx + 1, PDF_PROCESSING_STEPS.length - 1);
      setProcessingStep(stepIdx);
    }, 900);
    try {
      const res = await nlpService.analyzePdf(pdfFile, pdfTitle || undefined, controller.signal);
      setNlpResult(res);
    } catch (err: any) {
      if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') {
        setError('PDF analysis cancelled.');
      } else {
        const detail = err?.response?.data?.detail || err?.message;
        setError(detail || 'NLP processing failed. Please try again.');
      }
    } finally {
      clearInterval(stepTimer);
      abortControllerRef.current = null;
      setProcessingStep(0);
      setLoading(false);
    }
  };

  const tabs: { id: MainTab; label: string; icon: React.ReactNode }[] = [
    { id: 'analysis', label: 'Document Analysis', icon: <FileText className="w-3.5 h-3.5" /> },
    { id: 'brief',    label: 'Conservation Brief', icon: <BookOpen className="w-3.5 h-3.5" /> },
    { id: 'ask',      label: 'Ask the Corpus',     icon: <HelpCircle className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="space-y-6">
      <DemoBanner />
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-2">
        <div>
          <p className="font-mono text-[10px] tracking-widest uppercase font-semibold mb-1 text-emerald-700">INTELLIGENCE DESK</p>
          <h1 className="font-serif text-3xl font-bold leading-tight flex items-center gap-2 text-[#1a1916]">
            <FileText className="w-6 h-6 text-emerald-700" /> Document Pipeline
          </h1>
          <p className="text-sm mt-1 text-[#77746c]">
            NLP pipeline \u00b7 Multi-document synthesis \u00b7 Evidence-grounded question answering.
          </p>
        </div>
      </div>

      {/* Main tab strip */}
      <div className="flex border border-[#e5e0d8] rounded-sm overflow-hidden">
        {tabs.map(tab => (
          <button key={tab.id} id={`main-tab-${tab.id}`} onClick={() => setMainTab(tab.id)}
            className={`flex-1 py-2.5 text-[10px] font-mono font-semibold tracking-wider uppercase flex items-center justify-center gap-1.5 transition-colors ${
              mainTab === tab.id ? 'bg-[#1a1916] text-white' : 'bg-[#fdfaf5] text-[#77746c] hover:bg-[#f0ebe2]'
            }`}>
            {tab.icon}{tab.label}
          </button>
        ))}
      </div>

      {/* DOCUMENT ANALYSIS tab */}
      {mainTab === 'analysis' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white border border-[#e5e0d8] p-5 rounded-sm space-y-4">
            <div className="flex border border-[#e5e0d8] rounded-sm overflow-hidden">
              <button id="tab-paste-text" onClick={() => { setActiveTab('text'); setError(null); }}
                className={`flex-1 py-2 text-[10px] font-mono font-semibold tracking-wider uppercase flex items-center justify-center gap-1.5 transition-colors ${
                  activeTab === 'text' ? 'bg-[#1a1916] text-white' : 'bg-[#fdfaf5] text-[#77746c] hover:bg-[#f0ebe2]'}`}>
                <FileText className="w-3.5 h-3.5" /> Paste Text
              </button>
              <button id="tab-upload-pdf" onClick={() => { setActiveTab('pdf'); setError(null); }}
                className={`flex-1 py-2 text-[10px] font-mono font-semibold tracking-wider uppercase flex items-center justify-center gap-1.5 transition-colors ${
                  activeTab === 'pdf' ? 'bg-[#1a1916] text-white' : 'bg-[#fdfaf5] text-[#77746c] hover:bg-[#f0ebe2]'}`}>
                <Upload className="w-3.5 h-3.5" /> Upload PDF
              </button>
            </div>
            {activeTab === 'text' && (
              <>
                <h3 className="text-sm font-semibold text-[#1a1916]">Submit Document for Real-time NLP Processing</h3>
                <div>
                  <label className="block text-[10px] font-mono text-[#94918a] uppercase tracking-wider mb-1">Document Title</label>
                  <input id="doc-title-input" type="text" value={docTitle} onChange={e => setDocTitle(e.target.value)}
                    className="w-full px-3 py-2 bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm text-sm text-[#1a1916] focus:outline-none focus:border-emerald-700 font-serif" />
                </div>
                <div>
                  <label className="block text-[10px] font-mono text-[#94918a] uppercase tracking-wider mb-1">Conservation Document Text</label>
                  <textarea id="doc-text-input" rows={6} value={textInput} onChange={e => setTextInput(e.target.value)}
                    className="w-full p-3 bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm text-sm text-[#1a1916] focus:outline-none focus:border-emerald-700 font-sans leading-relaxed" />
                </div>
                <div className="flex gap-2">
                  <button id="btn-run-text-analysis" onClick={handleAnalyzeText} disabled={loading}
                    className="flex-1 py-2.5 bg-[#1a1916] hover:bg-[#2c2b26] disabled:opacity-50 text-white font-mono tracking-wide text-xs rounded-sm flex items-center justify-center gap-2 transition-all">
                    <Sparkles className="w-4 h-4" />
                    <span>{loading ? 'PROCESSING NLP EMBEDDINGS...' : 'RUN PIPELINE ANALYSIS'}</span>
                  </button>
                  {loading && (
                    <button id="btn-cancel-text-analysis" onClick={handleCancelAnalysis}
                      className="px-4 py-2.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-300 font-mono text-xs rounded-sm transition-colors">
                      Cancel
                    </button>
                  )}
                </div>
              </>
            )}
            {activeTab === 'pdf' && (
              <>
                <h3 className="text-sm font-semibold text-[#1a1916]">Upload a Conservation PDF</h3>
                <p className="text-[11px] text-[#77746c]">Text-based PDFs only. Scanned / image-only PDFs are not supported. Max {MAX_PDF_MB}&nbsp;MB.</p>
                <div id="pdf-drop-zone" onDragOver={e => { e.preventDefault(); setDragOver(true); }} onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop} onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-sm p-6 flex flex-col items-center justify-center gap-2 cursor-pointer transition-colors ${
                    dragOver ? 'border-emerald-600 bg-emerald-50' : pdfFile ? 'border-emerald-400 bg-emerald-50' : 'border-[#e5e0d8] bg-[#fdfaf5] hover:border-emerald-400 hover:bg-emerald-50'}`}>
                  <input ref={fileInputRef} id="pdf-file-input" type="file" accept=".pdf,application/pdf" className="hidden"
                    onChange={e => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }} />
                  {pdfFile ? (
                    <><CheckCircle2 className="w-8 h-8 text-emerald-600" />
                      <span className="text-sm font-semibold text-emerald-800 text-center break-all">{pdfFile.name}</span>
                      <span className="text-[10px] font-mono text-emerald-600">{formatBytes(pdfFile.size)}</span></>
                  ) : (
                    <><Upload className="w-8 h-8 text-[#94918a]" />
                      <span className="text-sm text-[#77746c]">Drag &amp; drop or click to choose a PDF</span>
                      <span className="text-[10px] font-mono text-[#94918a] uppercase tracking-wider">Supported: PDF &middot; Max {MAX_PDF_MB}&nbsp;MB</span></>
                  )}
                </div>
                {pdfFile && (
                  <div className="flex items-center gap-2 bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm px-3 py-2">
                    <FileIcon className="w-4 h-4 text-emerald-700 shrink-0" />
                    <span className="text-xs text-[#1a1916] flex-1 truncate">{pdfFile.name}</span>
                    <span className="text-[10px] font-mono text-[#94918a] shrink-0">{formatBytes(pdfFile.size)}</span>
                    <button onClick={e => { e.stopPropagation(); clearPdf(); }} className="p-0.5 rounded hover:bg-rose-50 text-[#94918a] hover:text-rose-600" title="Remove file">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
                {pdfFile && (
                  <div>
                    <label className="block text-[10px] font-mono text-[#94918a] uppercase tracking-wider mb-1">Document Title (optional)</label>
                    <input id="pdf-title-input" type="text" value={pdfTitle} onChange={e => setPdfTitle(e.target.value)}
                      placeholder={pdfFile.name.replace(/\.pdf$/i, '')}
                      className="w-full px-3 py-2 bg-[#fdfaf5] border border-[#e5e0d8] rounded-sm text-sm text-[#1a1916] focus:outline-none focus:border-emerald-700 font-serif" />
                  </div>
                )}
                {pdfError && (
                  <div className="flex items-center gap-2 bg-rose-50 border border-rose-200 rounded-sm px-3 py-2 text-xs text-rose-700">
                    <AlertCircle className="w-4 h-4 shrink-0" />{pdfError}
                  </div>
                )}
                <div className="flex gap-2">
                  <button id="btn-analyze-pdf" onClick={handleAnalyzePdf} disabled={loading || !pdfFile}
                    className="flex-1 py-2.5 bg-[#1a1916] hover:bg-[#2c2b26] disabled:opacity-40 text-white font-mono tracking-wide text-xs rounded-sm flex items-center justify-center gap-2 transition-all">
                    <Sparkles className="w-4 h-4" />
                    <span>{loading ? 'PROCESSING PDF...' : 'ANALYSE PDF'}</span>
                  </button>
                  {loading && (
                    <button id="btn-cancel-pdf-analysis" onClick={handleCancelAnalysis}
                      className="px-4 py-2.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-300 font-mono text-xs rounded-sm transition-colors">
                      Cancel
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
          <div className="space-y-4">
            {error && (
              <EmptyState variant="error" icon={ShieldAlert} title="Analysis failed" description={error}
                actionLabel="Retry" onAction={activeTab === 'pdf' ? handleAnalyzePdf : handleAnalyzeText} />
            )}
            {loading && (
              <div className="bg-[#fdfaf5] border border-[#e5e0d8] p-6 rounded-sm space-y-3">
                {activeTab === 'pdf' ? (
                  <div className="space-y-2">
                    {PDF_PROCESSING_STEPS.map((step, i) => (
                      <div key={step} className={`flex items-center gap-2 text-xs transition-opacity ${i <= processingStep ? 'opacity-100' : 'opacity-25'}`}>
                        {i < processingStep ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                          : i === processingStep ? <div className="w-3.5 h-3.5 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin shrink-0" />
                          : <div className="w-3.5 h-3.5 rounded-full border border-[#e5e0d8] shrink-0" />}
                        <span className={i === processingStep ? 'text-[#1a1916] font-semibold' : 'text-[#77746c]'}>{step}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <>
                    <div className="flex items-center justify-between pb-2 border-b border-[#e5e0d8]">
                      <div className="flex items-center gap-2">
                        <div className="w-3.5 h-3.5 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin shrink-0" />
                        <span className="text-xs font-semibold text-[#1a1916]">Extracting entities &amp; generating embeddings...</span>
                      </div>
                      <button onClick={handleCancelAnalysis} className="text-[10px] font-mono text-rose-600 hover:text-rose-700 underline">
                        Cancel
                      </button>
                    </div>
                    <div className="animate-skeleton h-4 w-2/3 bg-[#e5e0d8] rounded-sm" />
                    <div className="animate-skeleton h-3 w-full bg-[#e5e0d8] rounded-sm" />
                    <div className="animate-skeleton h-3 w-5/6 bg-[#e5e0d8] rounded-sm" />
                    <div className="animate-skeleton h-20 w-full bg-[#e5e0d8] rounded-sm mt-2" />
                  </>
                )}
              </div>
            )}
            {!loading && !error && nlpResult ? (
              <div className="space-y-4 animate-fade-slide-in">
                <NLPSummaryBox summary={nlpResult.summary} sentenceCount={nlpResult.sentence_count} />
                <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm space-y-3">
                  <h4 className="text-[10px] font-mono font-bold text-[#94918a] uppercase tracking-wider">Extracted Domain Entities</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    <div className="bg-[#fdfaf5] p-2.5 rounded-sm border border-[#e5e0d8]">
                      <span className="text-[10px] text-emerald-700 flex items-center gap-1 font-mono mb-1.5 font-semibold"><Layers className="w-3 h-3" /> SPECIES</span>
                      <div className="flex flex-wrap gap-1.5">
                        {nlpResult.entities.species.length > 0 ? nlpResult.entities.species.map((s, i) => (
                          <EntityChip key={i} label={entityLabel(s)} colorClass="bg-emerald-50 text-emerald-700 border-emerald-200" />
                        )) : <span className="text-[#94918a]">None detected</span>}
                      </div>
                    </div>
                    <div className="bg-[#fdfaf5] p-2.5 rounded-sm border border-[#e5e0d8]">
                      <span className="text-[10px] text-emerald-700 flex items-center gap-1 font-mono mb-1.5 font-semibold"><MapPin className="w-3 h-3" /> LOCATIONS</span>
                      <div className="flex flex-wrap gap-1.5">
                        {nlpResult.entities.locations.length > 0 ? nlpResult.entities.locations.map((l, i) => (
                          <EntityChip key={i} label={entityLabel(l)} colorClass="bg-emerald-50 text-emerald-700 border-emerald-200" />
                        )) : <span className="text-[#94918a]">None detected</span>}
                      </div>
                    </div>
                    <div className="bg-[#fdfaf5] p-2.5 rounded-sm border border-[#e5e0d8]">
                      <span className="text-[10px] text-emerald-700 flex items-center gap-1 font-mono mb-1.5 font-semibold"><Shield className="w-3 h-3" /> PROTECTED AREAS</span>
                      <div className="flex flex-wrap gap-1.5">
                        {nlpResult.entities.protected_areas.length > 0 ? nlpResult.entities.protected_areas.map((p, i) => (
                          <EntityChip key={i} label={entityLabel(p)} colorClass="bg-emerald-50 text-emerald-700 border-emerald-200" />
                        )) : <span className="text-[#94918a]">None detected</span>}
                      </div>
                    </div>
                    <div className="bg-[#fdfaf5] p-2.5 rounded-sm border border-[#e5e0d8]">
                      <span className="text-[10px] text-amber-600 flex items-center gap-1 font-mono mb-1.5 font-semibold"><Building2 className="w-3 h-3" /> ORGANIZATIONS</span>
                      <div className="flex flex-wrap gap-1.5">
                        {nlpResult.entities.organizations.length > 0 ? nlpResult.entities.organizations.map((o, i) => (
                          <EntityChip key={i} label={entityLabel(o)} colorClass="bg-amber-50 text-amber-700 border-amber-200" />
                        )) : <span className="text-[#94918a]">None detected</span>}
                      </div>
                    </div>
                    <div className="bg-[#fdfaf5] p-2.5 rounded-sm border border-[#e5e0d8] sm:col-span-2">
                      <span className="text-[10px] text-amber-600 flex items-center gap-1 font-mono mb-1.5 font-semibold"><CalendarDays className="w-3 h-3" /> DATES</span>
                      <div className="flex flex-wrap gap-1.5">
                        {nlpResult.entities.dates.length > 0 ? nlpResult.entities.dates.map((d, i) => (
                          <EntityChip key={i} label={entityLabel(d)} colorClass="bg-amber-50 text-amber-700 border-amber-200" />
                        )) : <span className="text-[#94918a]">None detected</span>}
                      </div>
                    </div>
                    {nlpResult.entities.people && nlpResult.entities.people.length > 0 && (
                      <div className="bg-[#fdfaf5] p-2.5 rounded-sm border border-[#e5e0d8] sm:col-span-2">
                        <span className="text-[10px] text-blue-700 flex items-center gap-1 font-mono mb-1.5 font-semibold"><Building2 className="w-3 h-3" /> AUTHORS / PERSONNEL</span>
                        <div className="flex flex-wrap gap-1.5">
                          {nlpResult.entities.people.map((p, i) => (
                            <EntityChip key={i} label={entityLabel(p)} colorClass="bg-blue-50 text-blue-700 border-blue-200" />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Document Type Badge & Context */}
                {nlpResult.document_type && (
                  <div className="bg-[#fdfaf5] border border-[#e5e0d8] px-3.5 py-2.5 rounded-sm flex items-center justify-between">
                    <span className="text-[10px] font-mono text-[#94918a] uppercase tracking-wider">Document Classification</span>
                    <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded-sm bg-[#1a1916] text-white">
                      {nlpResult.document_type.replace(/_/g, ' ')}
                    </span>
                  </div>
                )}

                {nlpResult.threats.length > 0 && (
                  <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm space-y-2.5">
                    <h4 className="text-[10px] font-mono font-bold text-[#94918a] uppercase flex items-center gap-1.5 tracking-wider">
                      <ShieldAlert className="w-3.5 h-3.5 text-rose-600" /> Classified Threats ({nlpResult.threats.length})
                    </h4>
                    {(showAllThreats ? nlpResult.threats : nlpResult.threats.slice(0, 3)).map((th, i) => (
                      <div key={i} className="bg-[#fdfaf5] p-2.5 rounded-sm border border-[#e5e0d8] space-y-1.5">
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-[#1a1916]">{th.threat_name}</span>
                            {th.evidence_status && (
                              <span className={`text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded-sm ${
                                th.evidence_status === 'DIRECTLY_OBSERVED' ? 'bg-rose-100 text-rose-800 border border-rose-300' :
                                th.evidence_status === 'PROPOSED_OR_CAPABILITY' ? 'bg-purple-100 text-purple-800 border border-purple-300' :
                                th.evidence_status === 'CITED_LITERATURE' ? 'bg-slate-100 text-slate-700 border border-slate-300' :
                                'bg-amber-100 text-amber-800 border border-amber-300'
                              }`}>
                                {th.evidence_status.replace(/_/g, ' ')}
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] font-mono text-[#94918a] shrink-0">
                            {(th.confidence * 100).toFixed(0)}% calibrated
                          </span>
                        </div>
                        {th.supporting_passage && (
                          <p className="text-[11px] text-[#77746c] italic bg-white p-2 rounded-sm border border-[#e5e0d8] line-clamp-2">
                            "{th.supporting_passage}"
                          </p>
                        )}
                        {th.explanation && (
                          <p className="text-[10px] font-mono text-[#94918a]">
                            {th.explanation}
                          </p>
                        )}
                      </div>
                    ))}
                    {nlpResult.threats.length > 3 && (
                      <button onClick={() => setShowAllThreats(v => !v)}
                        className="w-full flex items-center justify-center gap-1 text-[10px] font-mono text-emerald-700 hover:text-emerald-800 py-1.5 transition-all font-semibold">
                        <span>{showAllThreats ? 'SHOW FEWER' : `SHOW ALL ${nlpResult.threats.length}`}</span>
                        <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showAllThreats ? 'rotate-180' : ''}`} />
                      </button>
                    )}
                  </div>
                )}
                {nlpResult.topics.length > 0 && (
                  <div className="bg-white border border-[#e5e0d8] p-4 rounded-sm space-y-2">
                    <h4 className="text-[10px] font-mono font-bold text-[#94918a] uppercase flex items-center gap-1.5 tracking-wider">
                      <Layers className="w-3.5 h-3.5 text-emerald-700" /> Topics &amp; Domains ({nlpResult.topics.length})
                    </h4>
                    <div className="flex flex-wrap gap-1.5">
                      {nlpResult.topics.map((tp, i) => (
                        <EntityChip key={i} label={`${tp.topic_name} \u2022 ${(tp.score * 100).toFixed(0)}%`} colorClass="bg-emerald-50 text-emerald-700 border-emerald-200" />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : !loading && !error && (
              <div className="bg-[#fdfaf5] border border-[#e5e0d8] p-8 rounded-sm text-center text-[10px] font-mono text-[#94918a] uppercase tracking-wider">
                {activeTab === 'pdf'
                  ? 'Upload a PDF and click \u201cAnalyse PDF\u201d to extract conservation intelligence.'
                  : 'Enter document text and click \u201cRun Pipeline Analysis\u201d to extract intelligence entities and embeddings.'}
              </div>
            )}
          </div>
        </div>
      )}

      {mainTab === 'brief' && <ConservationBriefTab />}
      {mainTab === 'ask'   && <AskTheCorpusTab />}
    </div>
  );
};
