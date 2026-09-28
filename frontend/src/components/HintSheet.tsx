import React, { useState, useEffect } from 'react';
import { StepItem, Language } from '../types';
import { Lightbulb, Sparkles, HelpCircle, X, ChevronRight } from 'lucide-react';
import { TunsayAvatar } from './TunsayAvatar';

interface HintSheetProps {
  step: StepItem;
  isOpen: boolean;
  language?: Language;
  onClose: () => void;
}

export const HintSheet: React.FC<HintSheetProps> = ({
  step,
  isOpen,
  language = 'km',
  onClose
}) => {
  const [hintLevel, setHintLevel] = useState<1 | 2 | 3>(1);
  const isKhmer = language === 'km';

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
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-[#1B4332]/60 backdrop-blur-xs p-0 sm:p-4 animate-fadeIn text-[#1B4332]">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="hint-sheet-title"
        className="w-full max-w-lg bg-white rounded-t-3xl sm:rounded-3xl border-3 border-[#1B4332] shadow-[6px_6px_0px_#1B4332] overflow-hidden flex flex-col max-h-[85vh] animate-slideUp"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Sheet Header */}
        <div className="p-4 bg-[#1B4332] border-b-3 border-[#1B4332] flex items-center justify-between text-white">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-[#40916C] rounded-2xl border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] flex items-center justify-center">
              <TunsayAvatar size="sm" state="thinking" showBadge={false} />
            </div>
            <div>
              <h3 id="hint-sheet-title" className="text-base sm:text-lg font-black text-white font-heading flex items-center gap-1.5 drop-shadow-[1px_1px_0px_#1B4332]">
                <Lightbulb className="w-5 h-5 text-white fill-white" />
                {isKhmer ? 'តម្រុយពី ReanMore' : "Tunsay's Hints"}
              </h3>
              <p className="text-xs text-white font-bold">
                {isKhmer 
                  ? `ជំហានទី ${step.stepNumber} នៃ ${step.totalSteps}` 
                  : `Step ${step.stepNumber} of ${step.totalSteps}`}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-2xl bg-[#2D6A4F] border-2 border-[#1B4332] text-white hover:bg-[#40916C] hover:text-[#1B4332] transition-colors cursor-pointer"
            title="Close hints"
          >
            <X className="w-5 h-5 stroke-[3]" />
          </button>
        </div>

        {/* Hint Level Selector Tabs */}
        <div className="flex border-b-3 border-[#1B4332] bg-[#E8F5E9] p-2 gap-2">
          <button
            type="button"
            onClick={() => setHintLevel(1)}
            className={`flex-1 py-2 px-3 rounded-2xl text-xs sm:text-sm font-black flex items-center justify-center gap-1.5 transition-all cursor-pointer border-2 border-[#1B4332] ${
              hintLevel === 1 
                ? 'bg-[#40916C] text-white shadow-[2px_2px_0px_#1B4332] -translate-y-0.5' 
                : 'bg-white text-[#1B4332]/80 hover:bg-[#40916C]/50'
            }`}
          >
            <Lightbulb className="w-3.5 h-3.5 stroke-[2.5]" />
            {isKhmer ? 'តម្រុយ ១' : 'Hint 1'}
          </button>

          <button
            type="button"
            onClick={() => setHintLevel(2)}
            className={`flex-1 py-2 px-3 rounded-2xl text-xs sm:text-sm font-black flex items-center justify-center gap-1.5 transition-all cursor-pointer border-2 border-[#1B4332] ${
              hintLevel === 2 
                ? 'bg-[#A7CDB4] text-[#1B4332] shadow-[2px_2px_0px_#1B4332] -translate-y-0.5' 
                : 'bg-white text-[#1B4332]/80 hover:bg-[#A7CDB4]/50'
            }`}
          >
            <HelpCircle className="w-3.5 h-3.5 stroke-[2.5]" />
            {isKhmer ? 'តម្រុយ ២' : 'Hint 2'}
          </button>

          <button
            type="button"
            onClick={() => setHintLevel(3)}
            className={`flex-1 py-2 px-3 rounded-2xl text-xs sm:text-sm font-black flex items-center justify-center gap-1.5 transition-all cursor-pointer border-2 border-[#1B4332] ${
              hintLevel === 3 
                ? 'bg-[#2D6A4F] text-white shadow-[2px_2px_0px_#1B4332] -translate-y-0.5' 
                : 'bg-white text-[#1B4332]/80 hover:bg-[#2D6A4F]/50'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 stroke-[2.5]" />
            {isKhmer ? 'ឧទាហរណ៍' : 'Example'}
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto space-y-4">
          {hintLevel === 1 && (
            <div className="bg-[#E8F5E9] p-4 rounded-2xl border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] space-y-2 animate-fadeIn">
              <div className="flex items-center gap-2 text-[#1B4332] font-black text-sm">
                <Sparkles className="w-4 h-4 text-[#2D6A4F]" />
                {isKhmer ? 'តម្រុយតូច៖' : 'Small hint:'}
              </div>
              <p className="text-sm sm:text-base text-[#1B4332] font-black leading-relaxed">
                {isKhmer ? step.hint1.khmer : step.hint1.eng}
              </p>
            </div>
          )}

          {hintLevel === 2 && (
            <div className="bg-[#E8F5E9] p-4 rounded-2xl border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] space-y-2 animate-fadeIn">
              <div className="flex items-center gap-2 text-[#1B4332] font-black text-sm">
                <HelpCircle className="w-4 h-4 text-[#2D6A4F]" />
                {isKhmer ? 'តម្រុយធំជាង៖' : 'Bigger hint:'}
              </div>
              <p className="text-sm sm:text-base text-[#1B4332] font-black leading-relaxed">
                {isKhmer ? step.hint2.khmer : step.hint2.eng}
              </p>
            </div>
          )}

          {hintLevel === 3 && (
            <div className="bg-[#40916C] p-4 rounded-2xl border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] space-y-3 animate-fadeIn">
              <div className="flex items-center gap-2 text-white font-black text-sm">
                <Sparkles className="w-4 h-4 text-white" />
                {isKhmer ? step.hint3.titleKhmer : step.hint3.titleEng}
              </div>
              <p className="text-sm sm:text-base text-[#1B4332] font-black leading-relaxed bg-white p-3 rounded-xl border-2 border-[#1B4332]">
                {isKhmer ? step.hint3.exampleKhmer : step.hint3.exampleEng}
              </p>
            </div>
          )}

          {/* Sayo Encouragement Note */}
          <div className="flex items-center gap-3 p-3.5 bg-[#2D6A4F] rounded-2xl border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332]">
            <Sparkles className="w-5 h-5 text-white" />
            <p className="text-xs sm:text-sm text-white font-black">
              {isKhmer 
                ? "អ្នកអាចធ្វើវាបាន! ព្យាយាមម្តងទៀតជាមួយចម្លើយរបស់អ្នក។" 
                : "You can do it! Give it a try now with your answer."}
            </p>
          </div>
        </div>

        {/* Bottom Actions */}
        <div className="p-4 bg-white border-t-3 border-[#1B4332] flex items-center justify-between">
          {hintLevel < 3 ? (
            <button
              type="button"
              onClick={() => setHintLevel((prev) => (prev + 1) as 1 | 2 | 3)}
              className="text-xs sm:text-sm font-black text-[#1B4332] hover:underline flex items-center gap-1 cursor-pointer"
            >
              {isKhmer ? 'មើលតម្រុយបន្ទាប់' : 'See next hint'} <ChevronRight className="w-4 h-4 stroke-[3]" />
            </button>
          ) : (
            <span className="text-xs font-black text-[#1B4332]">
              {isKhmer ? 'ត្រៀមខ្លួនសាកល្បងចម្លើយ!' : 'Ready to try your answer!'}
            </span>
          )}

          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 bg-[#2D6A4F] hover:bg-[#40916C] text-white hover:text-white font-black text-xs sm:text-sm rounded-2xl border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] transition-all cursor-pointer"
          >
            {isKhmer ? 'យល់ហើយ!' : 'Got it!'}
          </button>
        </div>
      </div>
    </div>
  );
};
