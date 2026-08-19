import React, { useState } from 'react';
import { 
  FileText, 
  Download, 
  Building2, 
  AlertCircle, 
  CheckCircle2, 
  Send, 
  Copy, 
  Check, 
  Sparkles, 
  Scale
} from 'lucide-react';
import { UserProfile, RTIDepartment, RTIRoutingResult, RTIDraftResult } from '../types';

interface Props {
  profile: UserProfile;
}

const SAMPLE_GRIEVANCES = [
  "Ration card application submitted 5 months ago in Pune, but no status or card issued.",
  "Deep potholes on municipal road causing accidents, multiple complaints to ward office ignored.",
  "PF withdrawal claim rejected by EPFO without explaining discrepancy in employer records.",
  "Post-matric SC scholarship fee reimbursement pending for over 8 months from Social Welfare Dept."
];

export const RTIDraftingView: React.FC<Props> = ({ profile }) => {
  const [grievanceText, setGrievanceText] = useState(profile.grievance || '');
  const [isRouting, setIsRouting] = useState(false);
  const [isDrafting, setIsDrafting] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [copied, setCopied] = useState(false);

  const [routingResult, setRoutingResult] = useState<RTIRoutingResult | null>(null);
  const [selectedDeptId, setSelectedDeptId] = useState<string | null>(null);
  const [draftResult, setDraftResult] = useState<RTIDraftResult | null>(null);

  // Trigger routing when user submits grievance
  const handleRouteGrievance = async (overrideText?: string) => {
    const text = overrideText || grievanceText;
    if (!text.trim()) return;

    setIsRouting(true);
    setDraftResult(null);
    try {
      const res = await fetch('/api/rti/route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grievance: text,
          state: profile.state || 'All'
        })
      });

      if (res.ok) {
        const data: RTIRoutingResult = await res.json();
        setRoutingResult(data);
        setSelectedDeptId(data.primary_department.id);

        // Auto draft if confidence >= 0.75
        if (!data.requires_confirmation) {
          handleGenerateDraft(text, data.primary_department.id);
        }
      }
    } catch (err) {
      console.error('Error routing RTI grievance:', err);
    } finally {
      setIsRouting(false);
    }
  };

  const handleGenerateDraft = async (grievance: string, deptId: string) => {
    setIsDrafting(true);
    try {
      const res = await fetch('/api/rti/draft', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grievance: grievance,
          department_id: deptId,
          profile: profile
        })
      });

      if (res.ok) {
        const data: RTIDraftResult = await res.json();
        setDraftResult(data);
      }
    } catch (err) {
      console.error('Error drafting RTI application:', err);
    } finally {
      setIsDrafting(false);
    }
  };

  const handleSelectCandidateDept = (dept: RTIDepartment) => {
    setSelectedDeptId(dept.id);
    handleGenerateDraft(grievanceText, dept.id);
  };

  const handleDownloadPdf = async () => {
    if (!draftResult || !selectedDeptId) return;
    setIsDownloading(true);
    try {
      const res = await fetch('/api/rti/pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grievance: grievanceText,
          department_id: selectedDeptId,
          profile: profile
        })
      });

      if (!res.ok) throw new Error('PDF download failed');

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Adhikar_RTI_Form_A_${selectedDeptId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('PDF error:', err);
      alert('Could not download RTI PDF.');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleCopyText = () => {
    if (!draftResult) return;
    const textToCopy = `
FORM 'A' - RTI APPLICATION UNDER SECTION 6(1) OF THE RTI ACT, 2005
TO: ${draftResult.department.designation_pio}, ${draftResult.department.name}
SUBJECT: ${draftResult.subject_line}

PARTICULARS OF INFORMATION SOUGHT:
${draftResult.framed_questions.map((q, idx) => `(${idx + 1}) ${q}`).join('\n')}

STATUTORY DECLARATION:
${draftResult.statutory_declaration}
    `.trim();

    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="h-full flex flex-col overflow-hidden bg-slate-900/40">
      {/* Top Header */}
      <div className="p-4 border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <Scale className="w-5 h-5 text-indigo-400" />
              RTI Drafting Agent
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              Module C (Stretch)
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Human-in-the-loop department routing and legally framed RTI Form-A applications under RTI Act 2005.
          </p>
        </div>

        {draftResult && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyText}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Copied' : 'Copy Text'}
            </button>
            <button
              onClick={handleDownloadPdf}
              disabled={isDownloading}
              className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-indigo-600 to-sky-600 hover:from-indigo-500 hover:to-sky-500 text-white shadow-lg shadow-indigo-950/40 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              {isDownloading ? 'Generating...' : 'Download Official RTI PDF'}
            </button>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {/* Grievance Input Card */}
        <div className="p-4 rounded-2xl border border-slate-800 bg-slate-950/70 shadow-lg space-y-3">
          <label className="text-xs font-bold text-slate-300 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-sky-400" />
            Describe your Civic Issue or Unanswered Government Grievance:
          </label>
          <div className="flex items-start gap-2">
            <textarea
              rows={2}
              value={grievanceText}
              onChange={(e) => setGrievanceText(e.target.value)}
              placeholder="e.g., 'My ration card application was submitted 6 months ago in Pune but no ration card or reason has been provided...'"
              className="flex-1 px-3.5 py-2 text-xs rounded-xl bg-slate-900 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-all resize-none"
            />
            <button
              onClick={() => handleRouteGrievance()}
              disabled={!grievanceText.trim() || isRouting}
              className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-xs font-bold transition-all shadow-md shrink-0 flex items-center gap-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              {isRouting ? 'Routing...' : 'Route RTI'}
            </button>
          </div>

          {/* Quick Examples */}
          <div className="flex items-center gap-1.5 flex-wrap pt-1 text-[11px]">
            <span className="text-slate-500 font-semibold uppercase text-[10px]">Examples:</span>
            {SAMPLE_GRIEVANCES.map((ex, i) => (
              <button
                key={i}
                onClick={() => {
                  setGrievanceText(ex);
                  handleRouteGrievance(ex);
                }}
                className="px-2.5 py-0.5 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-sky-300 border border-slate-800 text-[11px] transition-colors"
              >
                {ex.substring(0, 45)}...
              </button>
            ))}
          </div>
        </div>

        {/* Human-in-the-Loop Routing Results Card */}
        {routingResult && (
          <div className="p-4 rounded-2xl border border-indigo-900/60 bg-indigo-950/20 shadow-lg space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-indigo-400" />
                <h3 className="text-sm font-bold text-slate-200">Public Authority Classification</h3>
              </div>
              <div className="flex items-center gap-2 text-xs font-semibold">
                <span>Confidence:</span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-mono font-bold ${
                  routingResult.confidence_score >= 0.75 
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                    : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                }`}>
                  {intPercent(routingResult.confidence_score)}%
                </span>
              </div>
            </div>

            {/* Human-in-the-loop warning if confidence < 0.75 */}
            {routingResult.requires_confirmation && (
              <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-700/50 flex items-start gap-2.5 text-xs text-amber-300">
                <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Human-in-the-Loop Confirmation Required (ADR-008): </span>
                  Multiple public authorities have jurisdiction over related issues. Please confirm or select the target department below.
                </div>
              </div>
            )}

            {/* Candidate Department Selection Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
              {routingResult.candidate_departments.map((dept) => {
                const isSelected = selectedDeptId === dept.id;
                return (
                  <div
                    key={dept.id}
                    onClick={() => handleSelectCandidateDept(dept)}
                    className={`p-3 rounded-xl border transition-all cursor-pointer space-y-1.5 ${
                      isSelected
                        ? 'bg-indigo-600/20 border-indigo-500 shadow-md shadow-indigo-900/30'
                        : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 uppercase">
                        {dept.jurisdiction}
                      </span>
                      {isSelected && <CheckCircle2 className="w-4 h-4 text-indigo-400" />}
                    </div>
                    <h4 className="text-xs font-bold text-slate-100">{dept.name}</h4>
                    <p className="text-[10px] text-slate-400 line-clamp-2">
                      PIO: {dept.designation_pio}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Drafted RTI Application Sheet */}
        {isDrafting ? (
          <div className="h-64 flex flex-col items-center justify-center space-y-3">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-xs text-slate-400">Framing legal RTI questions under Section 6(1)...</p>
          </div>
        ) : draftResult ? (
          <div className="w-full bg-white text-slate-900 rounded-2xl shadow-2xl p-8 border border-slate-200 text-xs font-sans space-y-6">
            {/* RTI Form Header */}
            <div className="text-center border-b-2 border-indigo-900 pb-4">
              <p className="text-[10px] font-bold text-slate-500 tracking-widest uppercase">
                FORM 'A' — APPLICATION FOR OBTAINING INFORMATION
              </p>
              <h1 className="text-sm font-extrabold text-slate-900 mt-0.5">
                UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005
              </h1>
              <p className="text-[10px] text-slate-500 mt-0.5">
                Drafted via Adhikar Civic Empowerment Platform • Citizen Legal Translation Layer
              </p>
            </div>

            {/* To Section */}
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
              <span className="text-[10px] font-bold uppercase text-slate-500">Addressed To:</span>
              <p className="text-xs font-bold text-slate-800">{draftResult.department.designation_pio}</p>
              <p className="text-xs text-slate-700">{draftResult.department.name}</p>
              <p className="text-[11px] text-slate-500">Jurisdiction: {profile.state || 'India'}</p>
            </div>

            {/* Subject */}
            <div>
              <span className="text-[10px] font-bold uppercase text-slate-500 block mb-0.5">Subject:</span>
              <p className="text-xs font-bold text-slate-900 bg-indigo-50/70 p-2.5 rounded-lg border border-indigo-100">
                {draftResult.subject_line}
              </p>
            </div>

            {/* Questions Sought */}
            <div>
              <h3 className="text-xs font-bold text-indigo-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-indigo-700" />
                Particulars of Information Sought (Section 6(1)):
              </h3>
              <div className="space-y-2">
                {draftResult.framed_questions.map((q, idx) => (
                  <div key={idx} className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-50 border border-slate-200">
                    <span className="w-5 h-5 rounded-full bg-indigo-800 text-white text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                      2.{idx + 1}
                    </span>
                    <p className="text-xs text-slate-800 leading-relaxed font-mono">{q}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Statutory Declaration */}
            <div className="pt-2 border-t border-slate-200 space-y-2">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Statutory Declaration:
              </h3>
              <p className="text-[11px] text-slate-600 italic bg-slate-50 p-3 rounded-lg border border-slate-200">
                "{draftResult.statutory_declaration}"
              </p>
              <p className="text-[10px] text-slate-500">
                <strong>Prescribed RTI Fee:</strong> {draftResult.fee_guidance}
              </p>
            </div>

            {/* Filing Instructions Guide */}
            <div className="bg-sky-50/70 p-3.5 rounded-xl border border-sky-200 space-y-1.5">
              <h4 className="text-[11px] font-bold text-sky-900 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-sky-700" />
                How to File this RTI Application:
              </h4>
              <ul className="text-[10px] text-sky-800 space-y-1 list-disc pl-4">
                {draftResult.filing_instructions.map((inst, i) => (
                  <li key={i}>{inst}</li>
                ))}
              </ul>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};

function intPercent(score: number): number {
  return Math.round(score * 100);
}
