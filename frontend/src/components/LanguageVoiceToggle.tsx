import React from 'react';
import { Globe, Volume2, VolumeX, Sparkles } from 'lucide-react';

export interface LanguageOption {
  code: string;
  name: string;
  native: string;
}

export const INDIAN_LANGUAGES: LanguageOption[] = [
  { code: 'en', name: 'English', native: 'English' },
  { code: 'hi', name: 'Hindi', native: 'हिन्दी' },
  { code: 'mr', name: 'Marathi', native: 'मराठी' },
  { code: 'ta', name: 'Tamil', native: 'தமிழ்' },
  { code: 'te', name: 'Telugu', native: 'తెలుగు' },
  { code: 'bn', name: 'Bengali', native: 'বাংলা' },
  { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ' },
  { code: 'gu', name: 'Gujarati', native: 'ગુજરાતી' },
  { code: 'pa', name: 'Punjabi', native: 'ਪੰਜਾਬੀ' }
];

interface Props {
  selectedLanguage: string;
  onLanguageChange: (langCode: string) => void;
  voiceEnabled: boolean;
  onToggleVoice: () => void;
}

export const LanguageVoiceToggle: React.FC<Props> = ({
  selectedLanguage,
  onLanguageChange,
  voiceEnabled,
  onToggleVoice
}) => {
  const isIndic = selectedLanguage !== 'en';

  return (
    <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-800 rounded-xl px-2.5 py-1 shadow-sm">
      {/* Gemini Native Language Badge */}
      <div className="flex items-center gap-1.5 pr-2 border-r border-slate-800">
        <Globe className="w-3.5 h-3.5 text-sky-400" />
        <span className="text-[10px] font-extrabold uppercase tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-sky-400 to-indigo-400 flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-sky-400" />
          Native Language
        </span>
      </div>

      {/* Language Selector Dropdown */}
      <select
        value={selectedLanguage}
        onChange={(e) => onLanguageChange(e.target.value)}
        className="bg-transparent text-xs font-semibold text-slate-200 focus:outline-none cursor-pointer pr-1"
      >
        {INDIAN_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code} className="bg-slate-900 text-slate-100 text-xs">
            {lang.native} ({lang.name})
          </option>
        ))}
      </select>

      {/* Voice Toggle Button */}
      <button
        type="button"
        onClick={onToggleVoice}
        className={`p-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1 ${
          voiceEnabled
            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
            : 'text-slate-400 hover:text-slate-200'
        }`}
        title={voiceEnabled ? "Gemini Native Voice Output Active" : "Enable Voice Output"}
      >
        {voiceEnabled ? (
          <>
            <Volume2 className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            <span className="text-[10px] font-bold hidden xl:inline">Voice ON</span>
          </>
        ) : (
          <>
            <VolumeX className="w-3.5 h-3.5" />
            <span className="text-[10px] hidden xl:inline">Voice OFF</span>
          </>
        )}
      </button>

      {/* Native Multilingual Indicator */}
      {isIndic && (
        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 hidden md:inline">
          Gemini Native (ADR-011)
        </span>
      )}
    </div>
  );
};
