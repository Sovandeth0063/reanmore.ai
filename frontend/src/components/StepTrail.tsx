import React from 'react';
import { Language } from '../types';
import { Footprints, Check } from 'lucide-react';

interface StepTrailProps {
  currentStep: number;
  totalSteps: number;
  completedSteps?: number[];
  maxUnlockedStep?: number;
  language?: Language;
  onSelectStep?: (stepIndex: number) => void;
}

export const StepTrail: React.FC<StepTrailProps> = ({
  currentStep,
  totalSteps,
  completedSteps = [],
  maxUnlockedStep,
  language = 'km',
  onSelectStep
}) => {
  const isKhmer = language === 'km';
  const effectiveMaxUnlocked = maxUnlockedStep ?? currentStep;

  return (
    <div className="w-full flex justify-center items-center my-2 sm:my-3">
      <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3 px-3 sm:px-6 py-1.5 sm:py-2.5 bg-white rounded-full border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] max-w-full">
        <div className="flex items-center gap-1 sm:gap-1.5 text-[11px] sm:text-xs font-black text-[#1B4332] shrink-0">
          <Footprints className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[#1B4332]" />
          <span>
            {isKhmer 
              ? `ជំហានទី ${currentStep} នៃ ${totalSteps}` 
              : `Step ${currentStep} of ${totalSteps}`}
          </span>
        </div>

        <div className="flex items-center gap-1 sm:gap-2 ml-1 sm:ml-2">
          {Array.from({ length: totalSteps }).map((_, idx) => {
            const stepNum = idx + 1;
            const isCompleted = completedSteps.includes(idx);
            const isCurrent = stepNum === currentStep;
            const isUnlocked = stepNum <= effectiveMaxUnlocked || isCompleted || isCurrent;

            return (
              <React.Fragment key={idx}>
                {idx > 0 && (
                  <div 
                    className={`w-3 sm:w-6 h-[2.5px] sm:h-[3px] rounded-full transition-colors ${
                      stepNum <= effectiveMaxUnlocked ? 'bg-[#1B4332]' : 'bg-[#1B4332]/30'
                    }`}
                  />
                )}
                <button
                  type="button"
                  disabled={!isUnlocked}
                  onClick={() => isUnlocked && onSelectStep && onSelectStep(idx)}
                  className={`flex items-center justify-center transition-all ${
                    isUnlocked ? 'cursor-pointer hover:scale-110 active:scale-95' : 'cursor-not-allowed opacity-40'
                  }`}
                  title={
                    isUnlocked 
                      ? (isKhmer ? `ទៅកាន់ជំហានទី ${stepNum}` : `Go to step ${stepNum}`)
                      : (isKhmer ? `ត្រូវដោះស្រាយជំហានមុនសិន` : `Must solve previous steps first`)
                  }
                >
                  {isCompleted && !isCurrent ? (
                    <div className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-[#2D6A4F] border-2 border-[#1B4332] text-white flex items-center justify-center shadow-[1px_1px_0px_#1B4332]">
                      <Check className="w-3 h-3 sm:w-3.5 sm:h-3.5 stroke-[3]" />
                    </div>
                  ) : isCurrent ? (
                    <div className={`w-6 h-6 sm:w-7 sm:h-7 rounded-full border-2 sm:border-2.5 border-[#1B4332] text-white flex items-center justify-center text-[10px] sm:text-xs font-black shadow-[1.5px_1.5px_0px_#1B4332] ring-2 ring-[#40916C]/50 ${
                      isCompleted ? 'bg-[#2D6A4F]' : 'bg-[#1B4332]'
                    }`}>
                      {isCompleted ? (
                        <Check className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[3]" />
                      ) : (
                        stepNum
                      )}
                    </div>
                  ) : (
                    <div className="w-4 h-4 sm:w-5 sm:h-5 rounded-full border border-[#1B4332]/40 bg-[#E8F5E9]/60 flex items-center justify-center text-[9px] sm:text-[10px] font-black text-[#1B4332]/60">
                      {stepNum}
                    </div>
                  )}
                </button>
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
};
