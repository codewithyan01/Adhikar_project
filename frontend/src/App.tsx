import { useState } from 'react';
import { 
  ShieldCheck, 
  Layers, 
  FileText, 
  Scale,
  Send,
  Activity
} from 'lucide-react';
import { UserProfile, MatchedScheme, ViewMode } from './types';
import { ChatAssistant } from './components/ChatAssistant';
import { LanguageVoiceToggle } from './components/LanguageVoiceToggle';
import { ArchitectureInspectorModal } from './components/ArchitectureInspectorModal';
import { MatchedSchemesView } from './views/MatchedSchemesView';
import { DocumentGeneratorView } from './views/DocumentGeneratorView';
import { RTIDraftingView } from './views/RTIDraftingView';
import { YourRightsView } from './views/YourRightsView';

export default function App() {
  const [profile, setProfile] = useState<UserProfile>({});
  const [schemes, setSchemes] = useState<MatchedScheme[]>([]);
  const [isMatchingLoading, setIsMatchingLoading] = useState<boolean>(false);
  const [activeView, setActiveView] = useState<ViewMode>('schemes');
  const [selectedSchemeForApp, setSelectedSchemeForApp] = useState<MatchedScheme | null>(null);

  // Bhashini Multilingual & Voice State (ADR-011)
  const [selectedLanguage, setSelectedLanguage] = useState<string>('en');
  const [voiceEnabled, setVoiceEnabled] = useState<boolean>(false);

  // Architecture & Guardrail Inspector Modal for Judges
  const [isInspectorOpen, setIsInspectorOpen] = useState<boolean>(false);

  // Fetch matched schemes from FastAPI backend
  const fetchMatchedSchemes = async (currentProf?: UserProfile) => {
    const profToUse = currentProf || profile;
    setIsMatchingLoading(true);
    try {
      const res = await fetch('/api/schemes/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profile: profToUse,
          top_k: 5
        })
      });

      if (res.ok) {
        const data = await res.json();
        setSchemes(data);
      } else {
        console.error('Failed to match schemes:', res.statusText);
      }
    } catch (err) {
      console.error('Error fetching scheme matches:', err);
    } finally {
      setIsMatchingLoading(false);
    }
  };

  const handleProfileUpdate = (updatedProfile: UserProfile) => {
    setProfile(updatedProfile);
  };

  const handleSelectSchemeForApp = (scheme: MatchedScheme) => {
    setSelectedSchemeForApp(scheme);
    setActiveView('document');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* Top Navbar */}
      <header className="fixed top-0 left-0 right-0 h-16 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-between px-6">
        {/* Brand */}
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 via-indigo-500 to-emerald-500 flex items-center justify-center font-bold text-white shadow-lg shadow-sky-500/20 text-lg">
            अ
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-extrabold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-sky-400 via-indigo-300 to-emerald-400">
                Adhikar
              </h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30 uppercase tracking-wider">
                Full Suite
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-medium">
              AI for Civic & Legal Empowerment • Filter → Retrieve → Verify → Cite
            </p>
          </div>
        </div>

        {/* Center View Switcher Tabs (ADR-010) */}
        <div className="flex items-center bg-slate-900/90 p-1 rounded-xl border border-slate-800/80 space-x-1">
          <button
            onClick={() => setActiveView('schemes')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeView === 'schemes'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Matched Schemes (A)</span>
            {schemes.length > 0 && (
              <span className="w-4 h-4 rounded-full bg-white/20 text-[10px] flex items-center justify-center font-bold">
                {schemes.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveView('document')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeView === 'document'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Form Auto-Filler (B)</span>
            {selectedSchemeForApp && (
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            )}
          </button>

          <button
            onClick={() => setActiveView('rti')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeView === 'rti'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Send className="w-3.5 h-3.5" />
            <span>RTI Drafting (C)</span>
          </button>

          <button
            onClick={() => setActiveView('rights')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeView === 'rights'
                ? 'bg-sky-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Scale className="w-3.5 h-3.5" />
            <span>Your Rights (D)</span>
          </button>
        </div>

        {/* Right Controls: Architecture Inspector + Bhashini Multilingual Toggle */}
        <div className="flex items-center gap-2.5">
          {/* Architecture & AI Inspector Button (For Judges) */}
          <button
            onClick={() => setIsInspectorOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-sky-600/30 to-indigo-600/30 hover:from-sky-600/50 hover:to-indigo-600/50 text-sky-200 border border-sky-500/40 text-xs font-bold shadow-sm transition-all animate-pulse"
            title="Inspect Zero-Hallucination Pipeline & AI Engine Telemetry"
          >
            <Activity className="w-3.5 h-3.5 text-sky-400" />
            <span className="hidden xl:inline">AI & Guardrail Inspector</span>
            <span className="xl:hidden">Inspector</span>
          </button>

          {/* Gemini Native Language & Voice Selector (ADR-011) */}
          <LanguageVoiceToggle
            selectedLanguage={selectedLanguage}
            onLanguageChange={setSelectedLanguage}
            voiceEnabled={voiceEnabled}
            onToggleVoice={() => setVoiceEnabled(!voiceEnabled)}
          />

          {/* Guardrail Status Badge */}
          <div className="hidden md:flex items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] font-semibold">
              <ShieldCheck className="w-3.5 h-3.5" />
              Guardrail Active
            </span>
          </div>
        </div>
      </header>

      {/* Main Split Layout (ADR-010) */}
      <main className="flex w-full h-full pt-16">
        {/* Left Panel: Shared Conversational Assistant */}
        <section className="w-1/2 h-full">
          <ChatAssistant
            profile={profile}
            onProfileUpdate={handleProfileUpdate}
            onRequestMatchSchemes={() => fetchMatchedSchemes()}
            activeLanguage={selectedLanguage}
            voiceEnabled={voiceEnabled}
            onSwitchView={setActiveView}
          />
        </section>

        {/* Right Panel: Switchable Module View Panel */}
        <section className="w-1/2 h-full overflow-hidden">
          {activeView === 'schemes' && (
            <MatchedSchemesView
              schemes={schemes}
              profile={profile}
              isLoading={isMatchingLoading}
              onSelectSchemeForApplication={handleSelectSchemeForApp}
            />
          )}

          {activeView === 'document' && (
            <DocumentGeneratorView
              selectedScheme={selectedSchemeForApp}
              profile={profile}
              onBackToSchemes={() => setActiveView('schemes')}
            />
          )}

          {activeView === 'rti' && (
            <RTIDraftingView
              profile={profile}
            />
          )}

          {activeView === 'rights' && (
            <YourRightsView
              profile={profile}
            />
          )}
        </section>
      </main>

      {/* Architecture & AI Inspector Modal (For Judges & Evaluators) */}
      <ArchitectureInspectorModal
        isOpen={isInspectorOpen}
        onClose={() => setIsInspectorOpen(false)}
      />
    </div>
  );
}
