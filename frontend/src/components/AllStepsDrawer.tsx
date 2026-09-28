import React, { useEffect } from 'react';
import { StepItem, Language } from '../types';
import { X, CheckCircle2, CircleDot, Circle, ArrowRight, ArrowLeft, BookOpen, Edit3, Lock } from 'lucide-react';

interface AllStepsDrawerProps {
  steps: StepItem[];
  currentStepIndex: number;
  isOpen: boolean;
  language?: Language;
  onSelectStep: (index: number) => void;
  onClose: () => void;
}

export const AllStepsDrawer: React.FC<AllStepsDrawerProps> = ({
  steps,
  currentStepIndex,
  isOpen,
  language = 'km',
  onSelectStep,
  onClose,
}) => {
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div 
        role="dialog"
        aria-modal="true"
        aria-labelledby="all-steps-title"
        className="w-full max-w-lg max-h-[85vh] bg-white rounded-3xl border-3 border-[#1B4332] shadow-[6px_6px_0px_#1B4332] flex flex-col overflow-hidden animate-scaleUp"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 sm:p-5 bg-[#1B4332] text-white flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-2xl bg-[#40916C] border-2 border-white flex items-center justify-center shadow-[1px_1px_0px_white]">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 id="all-steps-title" className="font-heading font-black text-sm sm:text-base leading-tight">
                {isKhmer ? '📋 ផែនទីដំណើរការដោះស្រាយ' : '📋 Solution Journey Roadmap'}
              </h3>
              <p className="text-[11px] font-bold text-white/80">
                {isKhmer
                  ? `ជំហានសរុប៖ ${steps.length} • កំពុងនៅជំហានទី ${currentStepIndex + 1}`
                  : `Total: ${steps.length} steps • Currently on Step ${currentStepIndex + 1}`}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 text-white hover:bg-white/20 rounded-xl transition-all cursor-pointer border border-white/20"
            title={isKhmer ? 'បិទ' : 'Close'}
          >
            <X className="w-5 h-5 stroke-[2.5]" />
          </button>
        </div>

        {/* Spec §5 Clean Roadmap (No "Your Turn" Questions) */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-3.5 bg-[#F9FBF9]">
          {steps.map((s, idx) => {
            const isCompleted = idx < currentStepIndex || s.status === 'completed';
            const isCurrent = idx === currentStepIndex;
            const isLocked = idx > currentStepIndex && s.status !== 'completed';

            const missionText = s.mission || (isKhmer ? s.questionKhmer : s.questionEng);
            const ruleText = s.clue || (isKhmer ? s.hint1?.khmer : s.hint1?.eng);

            return (
              <div
                key={s.id || idx}
                className={`p-4 rounded-2xl border-3 transition-all flex flex-col gap-2.5 relative ${
                  isCurrent
                    ? 'bg-[#E8F5E9] border-[#1B4332] shadow-[3px_3px_0px_#1B4332]'
                    : isCompleted
                    ? 'bg-white border-[#2D6A4F] shadow-[2px_2px_0px_#2D6A4F]'
                    : 'bg-white/70 border-[#1B4332]/25 opacity-75'
                }`}
              >
                {/* Step Header */}
                <div className="flex items-center justify-between gap-2 border-b border-[#1B4332]/10 pb-2">
                  <div className="flex items-center gap-2">
                    <div className="shrink-0">
                      {isCompleted ? (
                        <div className="w-6 h-6 rounded-lg bg-[#2D6A4F] text-white flex items-center justify-center border border-[#1B4332]">
                          <CheckCircle2 className="w-4 h-4 stroke-[3]" />
                        </div>
                      ) : isCurrent ? (
                        <div className="w-6 h-6 rounded-lg bg-[#1B4332] text-white flex items-center justify-center border border-[#1B4332] animate-pulse">
                          <CircleDot className="w-4 h-4 stroke-[3]" />
                        </div>
                      ) : (
                        <div className="w-6 h-6 rounded-lg bg-gray-100 text-gray-400 flex items-center justify-center border border-gray-300">
                          <Circle className="w-3.5 h-3.5 stroke-[2]" />
                        </div>
                      )}
                    </div>
                    <span className="text-xs font-black uppercase tracking-wider text-[#1B4332]">
                      {isKhmer ? `ជំហានទី ${idx + 1}` : `Step ${idx + 1}`}:&nbsp;
                      <span className="text-[#2D6A4F]">
                        {s.title || missionText}
                      </span>
                    </span>
                  </div>

                  {isCurrent && (
                    <span className="px-2 py-0.5 bg-[#1B4332] text-white text-[10px] font-black rounded-full uppercase">
                      {isKhmer ? 'សកម្ម' : 'Active'}
                    </span>
                  )}
                  {isCompleted && (
                    <span className="px-2 py-0.5 bg-[#A7CDB4] text-[#1B4332] text-[10px] font-black rounded-full uppercase">
                      {isKhmer ? 'រួចរាល់' : 'Done'}
                    </span>
                  )}
                  {isLocked && (
                    <span className="px-2 py-0.5 bg-gray-200 text-gray-600 text-[10px] font-black rounded-full flex items-center gap-1">
                      <Lock className="w-2.5 h-2.5" />
                      {isKhmer ? 'ចាក់សោ' : 'Locked'}
                    </span>
                  )}
                </div>

                {/* Mission & Rule (Spec §5 Roadmap Items) */}
                <div className="space-y-1.5 text-xs">
                  {missionText && (
                    <p className="font-bold text-[#1B4332] flex items-start gap-1.5">
                      <span className="shrink-0 text-[#2D6A4F]">🌟</span>
                      <span>
                        <strong className="text-[#2D6A4F]">{isKhmer ? 'បេសកកម្ម៖' : 'Mission:'}</strong>{' '}
                        {missionText}
                      </span>
                    </p>
                  )}
                  {ruleText && (
                    <p className="font-bold text-[#78350F] flex items-start gap-1.5">
                      <span className="shrink-0 text-[#D97706]">💡</span>
                      <span>
                        <strong className="text-[#B45309]">{isKhmer ? 'វិធាន/គន្លឹះ៖' : 'Rule:'}</strong>{' '}
                        {ruleText}
                      </span>
                    </p>
                  )}
                </div>

                {/* Spec §5 Status Line & Action */}
                <div className="pt-2 border-t border-[#1B4332]/10 flex items-center justify-between gap-2 flex-wrap">
                  {isCompleted && (
                    <div className="flex items-center justify-between w-full">
                      <p className="text-[11px] font-black text-[#2D6A4F] flex items-center gap-1">
                        <span>✅ {isKhmer ? 'បានដោះស្រាយ' : 'Solved'}</span>
                        <span className="text-[#1B4332]/80 font-bold">
                          ({isKhmer ? 'កត់ត្រាទុក៖' : 'Recorded:'} "{s.studentAnswer || (isKhmer ? 'រួចរាល់' : 'Done')}")
                        </span>
                      </p>
                      <button
                        type="button"
                        onClick={() => {
                          onSelectStep(idx);
                          onClose();
                        }}
                        className="px-2.5 py-1 bg-[#E8F5E9] hover:bg-[#D8F3DC] text-[#1B4332] text-[10px] font-black rounded-lg border border-[#2D6A4F] flex items-center gap-1 cursor-pointer transition-all"
                      >
                        <span>{isKhmer ? 'មើលឡើងវិញ' : 'Review'}</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>
                  )}

                  {isCurrent && (
                    <div className="flex items-center justify-between w-full">
                      <p className="text-[11px] font-black text-[#1B4332] flex items-center gap-1">
                        <span>🔄 {isKhmer ? 'កំពុងដំណើរការ' : 'In Progress'}</span>
                      </p>
                      <button
                        type="button"
                        onClick={() => {
                          onSelectStep(idx);
                          onClose();
                        }}
                        className="px-3 py-1.5 bg-[#1B4332] hover:bg-[#2D6A4F] text-white text-xs font-black rounded-xl border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] hover:-translate-y-0.5 flex items-center gap-1.5 cursor-pointer transition-all"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>{isKhmer ? `ទៅដោះស្រាយជំហានទី ${idx + 1}` : `Go to Step ${idx + 1} to Solve`}</span>
                      </button>
                    </div>
                  )}

                  {isLocked && (
                    <p className="text-[11px] font-bold text-gray-500 flex items-center gap-1">
                      <span>⏳ {isKhmer ? 'បន្ទាប់ទៀត 🔒' : 'Up Next 🔒'}</span>
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Spec §5 Footer Navigation Actions */}
        <div className="p-3.5 sm:p-4 bg-[#E8F5E9] border-t-2 border-[#1B4332]/20 flex items-center justify-between gap-3 shrink-0">
          <button
            type="button"
            onClick={() => {
              onSelectStep(currentStepIndex);
              onClose();
            }}
            className="px-3 sm:px-4 py-2 bg-white hover:bg-[#F4FBF7] text-[#1B4332] font-black text-xs rounded-xl border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] hover:-translate-y-0.5 cursor-pointer transition-all flex items-center gap-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>{isKhmer ? 'ត្រឡប់ទៅកាតសកម្ម' : 'Return to Active Card'}</span>
          </button>

          <button
            type="button"
            onClick={() => {
              onSelectStep(currentStepIndex);
              onClose();
            }}
            className="px-3.5 sm:px-4 py-2 bg-[#2D6A4F] hover:bg-[#1B4332] text-white font-black text-xs rounded-xl border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] hover:-translate-y-0.5 cursor-pointer transition-all flex items-center gap-1.5"
          >
            <Edit3 className="w-3.5 h-3.5" />
            <span>{isKhmer ? `ទៅដោះស្រាយជំហានទី ${currentStepIndex + 1}` : `Go to Step ${currentStepIndex + 1}`}</span>
          </button>
        </div>
      </div>
    </div>
  );
};


