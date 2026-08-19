import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  Printer, 
  ArrowLeft, 
  CheckSquare, 
  Square, 
  ShieldCheck, 
  ExternalLink,
  Building,
  UserCheck
} from 'lucide-react';
import { MatchedScheme, UserProfile } from '../types';

interface Props {
  selectedScheme: MatchedScheme | null;
  profile: UserProfile;
  onBackToSchemes: () => void;
}

interface ApplicationPreviewData {
  scheme_name: string;
  source_url: string;
  applicant_details: Record<string, string>;
  submission_steps: string[];
  required_documents: Array<{ doc: string; status: string; reason: string }>;
  declaration_text: string;
}

export const DocumentGeneratorView: React.FC<Props> = ({
  selectedScheme,
  profile,
  onBackToSchemes
}) => {
  const [previewData, setPreviewData] = useState<ApplicationPreviewData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [checkedDocs, setCheckedDocs] = useState<Record<number, boolean>>({});

  useEffect(() => {
    if (!selectedScheme) return;

    const fetchPreview = async () => {
      setIsLoading(true);
      try {
        const res = await fetch('/api/application/preview', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            scheme_name: selectedScheme.name,
            application_process: selectedScheme.application_process,
            profile: profile,
            source_url: selectedScheme.source_url
          })
        });

        if (res.ok) {
          const data = await res.json();
          setPreviewData(data);
        }
      } catch (err) {
        console.error('Error loading application preview:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPreview();
  }, [selectedScheme, profile]);

  const toggleDocCheck = (index: number) => {
    setCheckedDocs(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const handleDownloadPdf = async () => {
    if (!selectedScheme) return;
    setIsDownloading(true);
    try {
      const res = await fetch('/api/application/pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scheme_name: selectedScheme.name,
          application_process: selectedScheme.application_process,
          profile: profile,
          source_url: selectedScheme.source_url
        })
      });

      if (!res.ok) throw new Error('PDF download failed');

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Adhikar_${selectedScheme.name.replace(/\s+/g, '_').substring(0, 25)}_Application.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('PDF download error:', err);
      alert('Could not generate PDF download. Please try again.');
    } finally {
      setIsDownloading(false);
    }
  };

  if (!selectedScheme) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-slate-900/30">
        <div className="w-14 h-14 rounded-2xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-400 mb-4 shadow-xl">
          <FileText className="w-7 h-7 text-sky-400" />
        </div>
        <h3 className="text-base font-bold text-slate-200">No Scheme Selected for Application</h3>
        <p className="text-xs text-slate-400 max-w-sm mt-1 mb-6">
          Please select any verified scheme from the "Matched Schemes" panel to auto-generate a government application form.
        </p>
        <button
          onClick={onBackToSchemes}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white shadow-lg shadow-sky-900/30 transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
          View Matched Schemes
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden bg-slate-900/50">
      {/* Top Header Controls */}
      <div className="p-4 border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToSchemes}
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Back to Schemes"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-400" />
              Application Form Auto-Filler
            </h2>
            <p className="text-[11px] text-slate-400">
              Auto-populated from official government template (Module B)
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            Print
          </button>
          <button
            onClick={handleDownloadPdf}
            disabled={isDownloading}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-950/40 disabled:opacity-50 transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            {isDownloading ? 'Generating PDF...' : 'Download Official PDF'}
          </button>
        </div>
      </div>

      {/* Main Document Content Area */}
      <div className="flex-1 overflow-y-auto p-6 flex justify-center bg-slate-950/40">
        {isLoading ? (
          <div className="h-64 flex flex-col items-center justify-center space-y-3">
            <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-xs text-slate-400">Populating official application fields...</p>
          </div>
        ) : previewData ? (
          <div className="w-full max-w-2xl bg-white text-slate-900 rounded-2xl shadow-2xl p-8 border border-slate-200 text-xs font-sans space-y-6 print:p-0 print:shadow-none">
            {/* Government Dossier Top Banner */}
            <div className="text-center border-b-2 border-sky-700 pb-4">
              <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-sky-100 text-sky-800 font-bold mb-1">
                अ
              </div>
              <p className="text-[10px] font-bold text-slate-500 tracking-widest uppercase">
                GOVERNMENT WELFARE & CIVIC ENTITLEMENT APPLICATION DOSSIER
              </p>
              <h1 className="text-base font-extrabold text-slate-900 mt-1">
                {previewData.scheme_name}
              </h1>
              <p className="text-[10px] text-slate-500 mt-0.5">
                Prepared via Adhikar Civic Translation Platform • Verified Form Format
              </p>
            </div>

            {/* Section 1: Verified Applicant Demographics */}
            <div>
              <h3 className="text-xs font-bold text-sky-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <UserCheck className="w-4 h-4 text-sky-700" />
                1. Verified Applicant Particulars
              </h3>
              <div className="grid grid-cols-2 gap-2 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                {Object.entries(previewData.applicant_details).map(([key, val]) => (
                  <div key={key} className="space-y-0.5">
                    <span className="text-[10px] text-slate-500 font-medium block">{key}</span>
                    <span className="text-xs font-semibold text-slate-800">{val}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Section 2: Required Documents Checklist */}
            <div>
              <h3 className="text-xs font-bold text-sky-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                2. Mandatory Enclosures & Enclosure Checklist
              </h3>
              <p className="text-[10px] text-slate-500 mb-2">
                Ensure self-attested copies of the following documents are attached:
              </p>
              <div className="space-y-1.5">
                {previewData.required_documents.map((item, idx) => {
                  const isChecked = !!checkedDocs[idx];
                  return (
                    <div
                      key={idx}
                      onClick={() => toggleDocCheck(idx)}
                      className="flex items-start gap-2.5 p-2.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors cursor-pointer"
                    >
                      <div className="mt-0.5 text-sky-700">
                        {isChecked ? (
                          <CheckSquare className="w-4 h-4 text-emerald-600" />
                        ) : (
                          <Square className="w-4 h-4 text-slate-400" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className={`text-xs font-semibold ${isChecked ? 'line-through text-slate-400' : 'text-slate-800'}`}>
                            {item.doc}
                          </span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-sky-100 text-sky-800">
                            {item.status}
                          </span>
                        </div>
                        <p className="text-[10px] text-slate-500 mt-0.5">{item.reason}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Section 3: Official Submission Steps */}
            <div>
              <h3 className="text-xs font-bold text-sky-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Building className="w-4 h-4 text-indigo-700" />
                3. Step-by-Step Submission Procedure
              </h3>
              <div className="space-y-2 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                {previewData.submission_steps.map((step, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs">
                    <span className="w-5 h-5 rounded-full bg-sky-800 text-white text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <p className="text-slate-700 leading-relaxed">{step}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Section 4: Self-Declaration & Signatures */}
            <div className="pt-2 border-t border-slate-200">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-1.5">
                4. Statutory Applicant Declaration
              </h3>
              <p className="text-[11px] text-slate-600 italic leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-200">
                "{previewData.declaration_text}"
              </p>

              <div className="mt-8 grid grid-cols-2 gap-8 text-[11px] text-slate-600">
                <div>
                  <p><strong>Date:</strong> {new Date().toLocaleDateString()}</p>
                  <p><strong>Place:</strong> {profile.state || 'India'}</p>
                </div>
                <div className="text-right">
                  <div className="border-b border-slate-400 w-48 ml-auto mb-1"></div>
                  <p className="font-semibold text-slate-800">Signature / Thumb Impression of Applicant</p>
                </div>
              </div>
            </div>

            {/* Official Portal Reference Link */}
            {selectedScheme.source_url && (
              <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
                <span>Direct portal: {selectedScheme.source_url}</span>
                <a
                  href={selectedScheme.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sky-600 font-semibold hover:underline inline-flex items-center gap-1"
                >
                  Visit Portal <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
};
