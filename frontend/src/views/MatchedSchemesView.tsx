import React, { useState } from 'react';
import { 
  CheckCircle2, 
  HelpCircle, 
  XCircle, 
  ExternalLink, 
  ChevronDown, 
  ChevronUp, 
  ShieldCheck, 
  AlertTriangle,
  FileText,
  Sparkles,
  Search
} from 'lucide-react';
import { MatchedScheme, UserProfile } from '../types';

interface Props {
  schemes: MatchedScheme[];
  profile: UserProfile;
  isLoading: boolean;
  onSelectSchemeForApplication?: (scheme: MatchedScheme) => void;
}

export const MatchedSchemesView: React.FC<Props> = ({
  schemes,
  profile,
  isLoading,
  onSelectSchemeForApplication
}) => {
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});

  const toggleExpand = (id: string) => {
    setExpandedCards(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const getVerdictBadge = (verdict: string) => {
    switch (verdict) {
      case 'ELIGIBLE':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" />
            ELIGIBLE
          </span>
        );
      case 'UNSURE':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <HelpCircle className="w-3.5 h-3.5" />
            REQUIRES VERIFICATION
          </span>
        );
      case 'NOT_ELIGIBLE':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <XCircle className="w-3.5 h-3.5" />
            NOT ELIGIBLE
          </span>
        );
    }
  };

  return (
    <div className="h-full flex flex-col overflow-hidden bg-slate-900/40">
      {/* View Header */}
      <div className="p-6 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-sky-400" />
              Verified Scheme Matches
            </h2>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-sky-500/20 text-sky-300 border border-sky-500/30">
              {schemes.length} Found
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Grounded against official government eligibility criteria with verifiable citations.
          </p>
        </div>

        {/* Profile Attributes Capsule */}
        <div className="hidden lg:flex items-center gap-2 text-xs text-slate-400">
          {profile.state && (
            <span className="px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/60">
              📍 {profile.state}
            </span>
          )}
          {profile.occupation && (
            <span className="px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/60 capitalize">
              💼 {profile.occupation}
            </span>
          )}
          {profile.age && (
            <span className="px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/60">
              🎂 {profile.age} yrs
            </span>
          )}
        </div>
      </div>

      {/* Schemes Card List */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {isLoading ? (
          <div className="h-64 flex flex-col items-center justify-center text-center space-y-3">
            <div className="w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-sm text-slate-400">
              Evaluating your profile against statutory rules & scheme clauses...
            </p>
          </div>
        ) : schemes.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center text-center p-8 rounded-2xl border border-slate-800 bg-slate-900/20">
            <div className="w-12 h-12 rounded-2xl bg-slate-800/80 flex items-center justify-center text-slate-400 mb-3">
              <Search className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-slate-300">No Matched Schemes Yet</h3>
            <p className="text-xs text-slate-500 max-w-sm mt-1">
              Start chatting with the assistant on the left. Once you share your occupation, state, or age, verified schemes will appear here.
            </p>
          </div>
        ) : (
          schemes.map((scheme) => {
            const isExpanded = !!expandedCards[scheme.id];

            return (
              <div
                key={scheme.id}
                className="group rounded-xl border border-slate-800/90 bg-slate-950/70 hover:border-slate-700/80 transition-all duration-200 overflow-hidden shadow-lg shadow-black/20"
              >
                <div className="p-5">
                  {/* Top Bar: Title & Verdict */}
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-base font-bold text-slate-100 group-hover:text-sky-300 transition-colors">
                        {scheme.name}
                      </h3>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                        {scheme.reasoning}
                      </p>
                    </div>
                    <div>{getVerdictBadge(scheme.verdict)}</div>
                  </div>

                  {/* Caveat Alert Banner if present */}
                  {scheme.caveat && (
                    <div className="mt-3.5 p-3 rounded-lg bg-amber-950/30 border border-amber-700/40 flex items-start gap-2.5 text-xs text-amber-300">
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-amber-200">Statutory Caveat: </span>
                        {scheme.caveat}
                      </div>
                    </div>
                  )}

                  {/* Key Benefits */}
                  <div className="mt-4 p-3 rounded-lg bg-slate-900/60 border border-slate-800/60">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-400 block mb-1">
                      Benefits & Entitlement
                    </span>
                    <p className="text-xs text-slate-300 leading-relaxed">
                      {scheme.benefits}
                    </p>
                  </div>

                  {/* Verifiable Source Citation Accordion (Trust Anchor) */}
                  <div className="mt-3 border-t border-slate-800/50 pt-3">
                    <button
                      onClick={() => toggleExpand(scheme.id)}
                      className="w-full flex items-center justify-between text-xs font-semibold text-sky-400/90 hover:text-sky-300 transition-colors"
                    >
                      <span className="flex items-center gap-1.5">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" />
                        Verifiable Official Clause Citation
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      )}
                    </button>

                    {isExpanded && (
                      <div className="mt-2.5 p-3.5 rounded-lg bg-slate-900 border border-emerald-950/60 text-xs text-slate-300 font-mono leading-relaxed space-y-2">
                        <p className="text-[11px] font-semibold text-emerald-400 font-sans uppercase tracking-wider">
                          Cited Legal / Scheme Text:
                        </p>
                        <blockquote className="border-l-2 border-emerald-500 pl-3 italic text-slate-300">
                          "{scheme.cited_clause}"
                        </blockquote>
                        <div className="pt-2 text-[10px] text-slate-500 flex items-center justify-between">
                          <span>Verified via Adhikar Guardrail RAG</span>
                          <span>Chroma Collection: scheme_eligibility</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Actions Footer */}
                  <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between">
                    <a
                      href={scheme.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-200 transition-colors"
                    >
                      Official Portal <ExternalLink className="w-3.5 h-3.5" />
                    </a>

                    {onSelectSchemeForApplication && scheme.verdict === 'ELIGIBLE' && (
                      <button
                        onClick={() => onSelectSchemeForApplication(scheme)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white shadow-md shadow-sky-900/30 transition-all duration-200"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        Prepare Application Form
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
