import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen,
  Shield,
  AlertTriangle,
  PawPrint,
  Search,
  Filter,
  ArrowRight,
  ExternalLink,
  Info,
  CheckCircle2,
  HelpCircle,
  FileText,
  MapPin,
  HeartHandshake
} from 'lucide-react';
import { DemoBanner } from '../components/DemoBanner';

interface ArticleItem {
  id: string;
  category: 'SPECIES' | 'THREATS' | 'LAW' | 'COMMUNITY' | 'SAFETY';
  title: string;
  subtitle: string;
  readTime: string;
  summary: string;
  keyPoints: string[];
  actionLink?: { text: string; to: string };
  tag: string;
}

const ARTICLES: ArticleItem[] = [
  {
    id: 'art-1',
    category: 'SPECIES',
    title: "India's Keystone Species: The Bengal Tiger & Asian Elephant",
    subtitle: 'Ecological Guardians of Forest Canopies and River Basins',
    readTime: '4 min read',
    summary: 'Tigers and elephants act as umbrella species in Indian forest biomes. Conserving contiguous elephant corridors directly protects hundreds of sympatric floral and faunal species while ensuring hydrological stability in downstream rivers.',
    keyPoints: [
      'Project Tiger (1973) and Project Elephant (1992) unite over 54 Dedicated Reserves.',
      'Linear infrastructure fragmentation remains the #1 threat to elephant herds.',
      'Camera-trap AI surveillance helps identify individuals by unique stripe and ear patterns.'
    ],
    actionLink: { text: 'Explore Monitored Species', to: '/species' },
    tag: 'Keystone Ecology'
  },
  {
    id: 'art-2',
    category: 'THREATS',
    title: 'Mitigating Anthropogenic Threats: Snaring, Electrocution & Poisoning',
    subtitle: 'Understanding the Drivers Behind Human-Wildlife Interface Incidents',
    readTime: '5 min read',
    summary: 'Poaching with wire snares, illegal electrical fence tapping, and retaliatory poisoning create severe mortality sinks near agricultural fringes. Rapid forest department response teams and community early warning sensors provide proven mitigation.',
    keyPoints: [
      'Solar-powered early warning buzzers reduce elephant crop encounters by 78%.',
      'Community eco-development committees (EDCs) ensure rapid ex-gratia compensation.',
      'Isolation Forest anomaly detection flags sudden absence of wildlife telemetry.'
    ],
    actionLink: { text: 'View ML Threat Analytics', to: '/threats' },
    tag: 'Threat Reduction'
  },
  {
    id: 'art-3',
    category: 'LAW',
    title: 'Wildlife Protection Act (1972) & The 2022 Amendment Guidelines',
    subtitle: 'Legal Framework Governing Wildlife Protection and Protected Areas',
    readTime: '6 min read',
    summary: 'The Wild Life (Protection) Amendment Act, 2022 rationalised protection schedules into four tiers and implemented CITES compliance for international trade. Offenses concerning Schedule I species attract stringent non-bailable penal provisions.',
    keyPoints: [
      'Schedule I: Highest statutory protection (Tigers, Elephants, Great Indian Bustards, Gharials).',
      'Standing committees empower local forest range officers to take immediate custody of seized contraband.',
      'Citizen reporting of illegal trade or snares is legally protected and rewarded.'
    ],
    tag: 'Statutory Law'
  },
  {
    id: 'art-4',
    category: 'SAFETY',
    title: 'Field Safety & Responsible Wildlife Observation Protocols',
    subtitle: 'Best Practices for Citizen Observers, Students, and Ecotourists',
    readTime: '3 min read',
    summary: 'Maintaining safe stand-off distances (minimum 50 meters from large herbivores and carnivores) is essential for personal safety and animal welfare. Never use artificial food bait or intrusive flash photography.',
    keyPoints: [
      'Always travel with authorized certified local guides in designated tourism zones.',
      'Respect vehicle retreat protocols: do not cut off wildlife crossing corridors.',
      'Report any distressed, injured, or trapped animal directly to the nearest Range Forest Office.'
    ],
    actionLink: { text: 'Report Field Observation', to: '/submit' },
    tag: 'Field Safety'
  },
  {
    id: 'art-5',
    category: 'COMMUNITY',
    title: 'Coexistence Over Conflict: Community-Led Forest Stewardship',
    subtitle: 'How Fringe Villages Drive Conservation Success Across India',
    readTime: '4 min read',
    summary: 'Long-term conservation succeeds only with local communities as primary stakeholders. Joint Forest Management (JFM) and indigenous patrol initiatives have restored critical habitats in Similipal, Kaziranga, and Periyar reserves.',
    keyPoints: [
      'Community anti-poaching watchers earn dignified livelihoods protecting native biodiversity.',
      'Grain banks and crop insurance schemes cushion agricultural families from wildlife damage.',
      'Traditional ecological knowledge (TEK) provides invaluable input for scientific monitoring.'
    ],
    tag: 'Community Stewardship'
  }
];

const CATEGORIES = [
  { id: 'ALL', label: 'ALL SUBJECTS' },
  { id: 'SPECIES', label: 'SPECIES ECOLOGY' },
  { id: 'THREATS', label: 'THREAT MITIGATION' },
  { id: 'LAW', label: 'WILDLIFE LAWS' },
  { id: 'SAFETY', label: 'SAFETY & PROTOCOLS' },
  { id: 'COMMUNITY', label: 'COMMUNITY ACTION' },
];

export const AwarenessHubPage: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredArticles = ARTICLES.filter((art) => {
    const matchesCategory = selectedCategory === 'ALL' || art.category === selectedCategory;
    const matchesSearch =
      art.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      art.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      art.tag.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="space-y-8 animate-fade-slide-in">
      <DemoBanner />

      {/* Header */}
      <div className="border-b border-[#e5e0d8] pb-6">
        <p className="font-mono text-[10px] tracking-widest uppercase font-semibold mb-1" style={{ color: '#11682f' }}>
          NATIONAL WILDLIFE CONSERVATION INTELLIGENCE PLATFORM
        </p>
        <h1
          className="font-serif text-3xl font-bold leading-tight"
          style={{ color: '#1a1916', fontFamily: "'Newsreader', Georgia, serif" }}
        >
          Conservation Awareness & Education Hub
        </h1>
        <p className="text-sm mt-1" style={{ color: '#77746c' }}>
          Authoritative intelligence on Indian wildlife biodiversity, statutory conservation mandates, threat mitigation, and responsible field protocols.
        </p>
      </div>

      {/* Search and Category Filter Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
        <div className="flex flex-wrap gap-1.5">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className="px-3 py-1 font-mono text-[10px] font-semibold tracking-wider transition-all"
              style={{
                borderRadius: '3px',
                border: `1px solid ${selectedCategory === cat.id ? '#11682f' : '#e5e0d8'}`,
                backgroundColor: selectedCategory === cat.id ? '#11682f' : '#ffffff',
                color: selectedCategory === cat.id ? '#ffffff' : '#5e5b54',
              }}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-2.5 w-3.5 h-3.5" style={{ color: '#94918a' }} />
          <input
            type="text"
            placeholder="Search awareness guides..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-[#e5e0d8] rounded-xs focus:outline-none focus:border-[#11682f]"
          />
        </div>
      </div>

      {/* Educational Article Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredArticles.map((art) => (
          <div
            key={art.id}
            className="bg-white border border-[#e5e0d8] p-6 rounded-sm shadow-sm flex flex-col justify-between hover:border-[#11682f] transition-colors"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-3">
                <span className="font-mono text-[10px] tracking-widest uppercase font-semibold text-[#11682f] bg-[#11682f12] px-2 py-0.5 rounded-xs">
                  {art.tag}
                </span>
                <span className="font-mono text-[10px] text-[#94918a]">{art.readTime}</span>
              </div>

              <h2 className="font-serif text-xl font-bold text-[#1a1916] mb-1 leading-snug">
                {art.title}
              </h2>
              <p className="text-xs text-[#94918a] font-mono mb-3">{art.subtitle}</p>

              <p className="text-xs text-[#5e5b54] leading-relaxed mb-4">
                {art.summary}
              </p>

              <div className="bg-[#faf8f4] p-3 rounded-xs border border-[#eee9df] mb-4 space-y-1.5">
                <p className="font-mono text-[9px] uppercase font-bold text-[#11682f] tracking-wider">
                  Key Directives & Insights
                </p>
                {art.keyPoints.map((pt, idx) => (
                  <div key={idx} className="flex items-start gap-1.5 text-[11px] text-[#4a4740]">
                    <span className="text-[#11682f] font-bold">•</span>
                    <span>{pt}</span>
                  </div>
                ))}
              </div>
            </div>

            {art.actionLink ? (
              <div className="pt-2 border-t border-[#f0ede6]">
                <Link
                  to={art.actionLink.to}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#11682f] hover:underline"
                >
                  {art.actionLink.text}
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            ) : (
              <div className="pt-2 border-t border-[#f0ede6] text-[10px] font-mono text-[#94918a]">
                Statutory Conservation Documentation
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredArticles.length === 0 && (
        <div className="bg-white border border-[#e5e0d8] p-12 text-center rounded-sm">
          <BookOpen className="w-8 h-8 text-[#94918a] mx-auto mb-3" />
          <h3 className="font-serif text-lg font-bold text-[#1a1916] mb-1">No guides found</h3>
          <p className="text-xs text-[#94918a]">Try searching for other topics like elephants, tiger, laws, or safety.</p>
        </div>
      )}
    </div>
  );
};
