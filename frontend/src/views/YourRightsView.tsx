import React, { useState, useEffect } from 'react';
import { 
  Scale, 
  Search, 
  ShieldAlert, 
  CheckCircle2, 
  HelpCircle, 
  ExternalLink, 
  ChevronDown, 
  ChevronUp, 
  ShoppingBag, 
  Home, 
  Briefcase, 
  PhoneCall, 
  Sparkles,
  BookOpen
} from 'lucide-react';
import { UserProfile, RightsExplainerResult } from '../types';

interface Props {
  profile: UserProfile;
}

const SAMPLE_QUERIES = [
  { label: "Tenant Deposit Cap", text: "My landlord in Pune is demanding 6 months rent as security deposit before moving in.", cat: "tenant" },
  { label: "E-Commerce Refund", text: "E-commerce app delivered a broken television and is refusing refund or return.", cat: "consumer" },
  { label: "Unpaid Salary", text: "Employer has delayed salary payment by over 45 days and made arbitrary deductions.", cat: "workplace" },
  { label: "Arbitrary Rent Hike", text: "Landlord gave 3 days notice to increase rent by 35% or vacate immediately.", cat: "tenant" }
];

export const YourRightsView: React.FC<Props> = ({ profile }) => {
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [results, setResults] = useState<RightsExplainerResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});

  // Initial fetch of rights
  useEffect(() => {
    fetchRights("What are my statutory rights regarding consumer issues, tenancy, and workplace wages?", 'all');
  }, []);

  const fetchRights = async (query: string, category: string) => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/rights/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dispute: query || "statutory rights in India",
          state: profile.state || "All India",
          category: category,
          top_k: 4
        })
      });

      if (res.ok) {
        const data = await res.json();
        setResults(data);
      }
    } catch (err) {
      console.error('Failed to fetch rights:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    fetchRights(searchQuery || "statutory legal rights", activeCategory);
  };

  const handleCategoryChange = (cat: string) => {
    setActiveCategory(cat);
    fetchRights(searchQuery || "statutory legal rights", cat);
  };

  const toggleExpand = (id: string) => {
    setExpandedCards(prev => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="h-full flex flex-col overflow-hidden bg-slate-900/40">
      {/* Top Header */}
      <div className="p-4 border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                <Scale className="w-5 h-5 text-sky-400" />
                Your Rights Navigator
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                Module D
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Grounded legal guidance across Consumer Protection, Tenant Disputes, and Workplace Wages.
            </p>
          </div>

          {/* National Legal Aid Helpline Quick Badge */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <PhoneCall className="w-3.5 h-3.5 text-emerald-400" />
            <div>
              <span className="text-[10px] text-slate-400 block">Free Legal Aid (NALSA):</span>
              <span className="font-bold text-emerald-400 font-mono">15100 (Toll-Free)</span>
            </div>
          </div>
        </div>

        {/* Search Input Bar */}
        <form onSubmit={handleSearchSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Describe your dispute (e.g., landlord withholding deposit, damaged e-commerce goods)..."
              className="w-full pl-9 pr-3.5 py-2 text-xs rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold transition-all shadow-md shrink-0 flex items-center gap-1.5"
          >
            {isLoading ? 'Checking...' : 'Check Rights'}
          </button>
        </form>

        {/* Category Filters & Quick Scenarios */}
        <div className="flex items-center justify-between gap-2 mt-3 flex-wrap">
          {/* Category Chips */}
          <div className="flex items-center gap-1.5">
            {[
              { id: 'all', label: 'All Rights', icon: BookOpen },
              { id: 'consumer', label: 'Consumer', icon: ShoppingBag },
              { id: 'tenant', label: 'Tenant', icon: Home },
              { id: 'workplace', label: 'Workplace', icon: Briefcase }
            ].map(tab => {
              const Icon = tab.icon;
              const isSelected = activeCategory === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleCategoryChange(tab.id)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    isSelected
                      ? 'bg-sky-600 text-white shadow-sm'
                      : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 border border-slate-800'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {tab.label}
                </button>
              );
            })}
          </div>

          {/* Quick Starter Chips */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {SAMPLE_QUERIES.map((q, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setSearchQuery(q.text);
                  fetchRights(q.text, q.cat);
                }}
                className="text-[10px] px-2 py-0.5 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-sky-300 border border-slate-800 transition-colors"
              >
                {q.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Results Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {isLoading ? (
          <div className="h-64 flex flex-col items-center justify-center space-y-3">
            <div className="w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-xs text-slate-400">Retrieving official gazetted rights & verifying clauses...</p>
          </div>
        ) : results.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center p-6 text-center">
            <HelpCircle className="w-10 h-10 text-slate-600 mb-2" />
            <h3 className="text-sm font-bold text-slate-300">No matching rights explainer found</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm">
              Try searching with keywords like 'deposit', 'refund', 'unpaid salary', or 'eviction'.
            </p>
          </div>
        ) : (
          results.map((item) => {
            const isExpanded = !!expandedCards[item.rights_id];
            const isApplicable = item.verdict === 'APPLICABLE' || item.verdict === 'ELIGIBLE';
            const isUnsure = item.verdict === 'UNSURE';

            return (
              <div
                key={item.rights_id}
                className={`rounded-2xl border transition-all shadow-lg overflow-hidden ${
                  isApplicable
                    ? 'border-slate-800 bg-slate-950/70 hover:border-slate-700'
                    : isUnsure
                    ? 'border-amber-900/60 bg-amber-950/20'
                    : 'border-slate-800/80 bg-slate-950/50'
                }`}
              >
                {/* Card Header */}
                <div className="p-5 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-slate-800 text-sky-400 border border-slate-700">
                          {item.category}
                        </span>
                        <span className="text-[11px] font-medium text-slate-400">
                          {item.act_reference}
                        </span>
                      </div>
                      <h3 className="text-sm font-bold text-slate-100">{item.title}</h3>
                    </div>

                    {/* Verdict Badge */}
                    <div className="shrink-0">
                      {isApplicable ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Applicable Right
                        </span>
                      ) : isUnsure ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          <HelpCircle className="w-3.5 h-3.5" />
                          Check Details
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                          <ShieldAlert className="w-3.5 h-3.5" />
                          Not Applicable
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Plain Language Explanation */}
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {item.explanation}
                  </p>

                  {/* Statutory Caveat Alert Banner */}
                  {item.caveat && (
                    <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-700/50 flex items-start gap-2 text-xs text-amber-300">
                      <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <div className="space-y-0.5">
                        <span className="font-bold text-[11px] uppercase tracking-wider block">
                          Statutory State Adoption Caveat (ADR-005 / ADR-009):
                        </span>
                        <p className="text-[11px] leading-relaxed text-amber-200">{item.caveat}</p>
                      </div>
                    </div>
                  )}

                  {/* Actionable Remedies Block */}
                  <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-sky-400" />
                      Actionable Legal Remedies & Nodal Portal:
                    </span>
                    <p className="text-xs font-medium text-slate-200">{item.key_remedies}</p>
                  </div>

                  {/* Referral to NALSA if UNSURE */}
                  {item.legal_aid_referral && (
                    <div className="p-3 rounded-xl bg-sky-950/30 border border-sky-800/60 text-xs text-sky-300 flex items-start gap-2">
                      <PhoneCall className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold">Free Legal Representation Referral: </span>
                        {item.legal_aid_referral}
                      </div>
                    </div>
                  )}

                  {/* Card Bottom Controls */}
                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                    <button
                      onClick={() => toggleExpand(item.rights_id)}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-sky-400 hover:text-sky-300 transition-colors"
                    >
                      {isExpanded ? (
                        <>Hide Verifiable Statutory Citation <ChevronUp className="w-3.5 h-3.5" /></>
                      ) : (
                        <>Expand Verifiable Statutory Citation <ChevronDown className="w-3.5 h-3.5" /></>
                      )}
                    </button>

                    {item.source_url && (
                      <a
                        href={item.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-slate-200 transition-colors"
                      >
                        Official Portal <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>

                {/* Expandable Verifiable Citation Accordion */}
                {isExpanded && (
                  <div className="p-4 bg-slate-950 border-t border-slate-800 space-y-2 text-xs">
                    <div className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      <span>Verbatim Official Text from Knowledge Base:</span>
                      <span className="font-mono text-emerald-400">Source: {item.authority}</span>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 font-mono text-[11px] text-slate-300 leading-relaxed whitespace-pre-wrap">
                      "{item.cited_clause}"
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
