import React, { useEffect, useState } from 'react';
import { StepItem, Language } from '../types';
import { RefreshCw, X, Sparkles, Eye, ChevronDown, ChevronUp } from 'lucide-react';
import { TunsayAvatar } from './TunsayAvatar';
import { resolveStepHints } from '../utils/hintHelper';

interface ExplanationCardProps {
  step: StepItem;
  isOpen: boolean;
  language?: Language;
  grade?: number;
  onClose: () => void;
}

export const ExplanationCard: React.FC<ExplanationCardProps> = ({
  step,
  isOpen,
  language = 'en',
  grade = 2,
  onClose
}) => {
  const isKhmer = language === 'km';
  const resolved = resolveStepHints(step, language, grade);
  const rawStep = step as any;
  const stepNumber = step?.stepNumber || rawStep?.step_number || 1;

  const [showAnalogy, setShowAnalogy] = useState(false);

  // Reset analogy toggle whenever modal opens or step changes
  useEffect(() => {
    setShowAnalogy(false);
  }, [step?.id, isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1B4332]/60 backdrop-blur-xs p-4 animate-fadeIn text-[#1B4332]">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="explain-sheet-title"
        className="w-full max-w-md bg-white rounded-3xl border-3 border-[#1B4332] shadow-[6px_6px_0px_#1B4332] overflow-hidden flex flex-col max-h-[85vh] animate-slideUp"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 bg-[#A7CDB4] border-b-3 border-[#1B4332] flex items-center justify-between text-[#1B4332]">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-white rounded-2xl border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] flex items-center justify-center shrink-0">
              <TunsayAvatar size="sm" state="explaining" showBadge={false} />
            </div>
            <div>
              <h3 id="explain-sheet-title" className="text-base sm:text-lg font-black font-heading flex items-center gap-1.5 drop-shadow-[1px_1px_0px_white]">
                <RefreshCw className="w-5 h-5 text-[#1B4332] stroke-[2.5]" />
                {isKhmer ? 'ពន្យល់តាមរបៀបផ្សេង' : 'Explain Differently'}
              </h3>
              <p className="text-xs font-bold text-[#1B4332]">
                {isKhmer 
                  ? `ជំហានទី ${stepNumber} • តោះធ្វើឱ្យវាកាន់តែងាយ!` 
                  : `Step ${stepNumber} • Let's make it easier!`}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-2xl bg-[#2D6A4F] border-2 border-[#1B4332] text-white hover:bg-[#40916C] hover:text-[#1B4332] transition-colors cursor-pointer"
            title={isKhmer ? 'បិទ' : 'Close explanation'}
          >
            <X className="w-5 h-5 stroke-[3]" />
          </button>
        </div>

        {/* Content Body: Kept Short & Grade-Appropriate */}
        <div className="p-5 overflow-y-auto space-y-4">
          {/* Single Main Explanation Box */}
          <div className="bg-[#E8F5E9] p-4 sm:p-5 rounded-2xl border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] space-y-3 animate-fadeIn">
            {/* Simpler words (1-2 short sentences) */}
            <p className="text-base sm:text-lg font-black text-[#1B4332] leading-snug">
              {resolved.simpleExplanation}
            </p>

            {/* Existing visual reference on the card */}
            {resolved.visualReference && (
              <p className="text-xs sm:text-sm font-bold text-[#2D6A4F] flex items-center gap-2 pt-2.5 border-t-2 border-[#1B4332]/10">
                <Eye className="w-4 h-4 text-[#2D6A4F] shrink-0" />
                <span>{resolved.visualReference}</span>
              </p>
            )}
          </div>

          {/* Optional Analogy: Only when requested / needed */}
          {resolved.analogyExplanation && (
            <div className="pt-1">
              {!showAnalogy ? (
                <button
                  type="button"
                  onClick={() => setShowAnalogy(true)}
                  className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-black text-[#2D6A4F] hover:text-[#1B4332] transition-colors cursor-pointer group"
                >
                  <Sparkles className="w-4 h-4 text-[#D97706] group-hover:scale-110 transition-transform" />
                  <span className="underline underline-offset-4 decoration-[#2D6A4F]/40 group-hover:decoration-[#1B4332]">
                    {isKhmer ? 'ចង់បានឧទាហរណ៍បន្ថែម? (ជំនួយបន្ថែម)' : 'Need an everyday example? (Optional extra help)'}
                  </span>
                  <ChevronDown className="w-3.5 h-3.5 text-[#2D6A4F]" />
                </button>
              ) : (
                <div className="bg-[#FFFDE7] p-3.5 rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] space-y-1.5 animate-fadeIn">
                  <div className="flex items-center justify-between text-[#D97706] font-black text-xs sm:text-sm">
                    <div className="flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-[#D97706] shrink-0" />
                      <span>{resolved.analogyTitle ? `${resolved.analogyTitle}:` : (isKhmer ? 'ឧទាហរណ៍ជីវិតពិត៖' : 'Everyday example:')}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowAnalogy(false)}
                      className="text-[11px] font-bold text-[#1B4332]/70 hover:text-[#1B4332] flex items-center gap-0.5 cursor-pointer"
                    >
                      <span>{isKhmer ? 'លាក់' : 'Hide'}</span>
                      <ChevronUp className="w-3 h-3" />
                    </button>
                  </div>
                  <p className="text-xs sm:text-sm font-bold text-[#1B4332] leading-relaxed">
                    {resolved.analogyExplanation}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-white border-t-3 border-[#1B4332] flex items-center justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-6 py-2.5 bg-[#2D6A4F] hover:bg-[#40916C] text-white hover:text-white font-black text-sm rounded-2xl border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] transition-all cursor-pointer"
          >
            {isKhmer ? 'យល់ហើយ!' : 'Got it!'}
          </button>
        </div>
      </div>
    </div>
  );
};
