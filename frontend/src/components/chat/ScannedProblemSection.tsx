import React from 'react';
import { HomeworkProblem, StepItem, UserProfile, WorksheetQueue } from '../../types';
import { StepTrail } from '../StepTrail';
import { StepCard } from '../StepCard';
import { TunsayAvatar } from '../TunsayAvatar';
import { RotateCcw } from 'lucide-react';

interface ScannedProblemSectionProps {
  activeProblem: HomeworkProblem;
  worksheetQueue?: WorksheetQueue | undefined;
  completedStepIndices: number[];
  currentStepIndex: number;
  maxUnlockedStepIndex: number;
  currentStep?: StepItem | undefined;
  profile: UserProfile;
  onResetProgress: () => void;
  onSelectStep: (stepIdx: number) => void;
  onStepAnswer: (answer: string) => boolean | Promise<boolean>;
  onNextStep?: (() => void) | undefined;
  onOpenHints: () => void;
  onOpenExplainDifferently: () => void;
}

export const ScannedProblemSection: React.FC<ScannedProblemSectionProps> = ({
  activeProblem,
  worksheetQueue,
  completedStepIndices,
  currentStepIndex,
  maxUnlockedStepIndex,
  currentStep,
  profile,
  onResetProgress,
  onSelectStep,
  onStepAnswer,
  onNextStep,
  onOpenHints,
  onOpenExplainDifferently,
}) => {
  const isKhmer = false;

  const isScannedWorksheet =
    Boolean(worksheetQueue) ||
    Boolean(activeProblem.imageUri) ||
    Boolean((activeProblem as any).isScanned);

  if (!isScannedWorksheet) {
    return null;
  }

  return (
    <div className="space-y-3 sm:space-y-4 w-full">
      {/* Scanned Problem Header Card — aligned with mascot box column */}
      {(activeProblem.problemStatementKhmer || activeProblem.problemStatementEng) && (
        <div className="flex items-start gap-2 sm:gap-3 w-full flex-row animate-fadeIn">
          {/* Aligned Mascot Box */}
          <div className="w-8 h-8 sm:w-10 sm:h-10 bg-[#40916C] rounded-lg sm:rounded-2xl shrink-0 border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] flex items-center justify-center p-0.5">
            <TunsayAvatar size="sm" state="explaining" showBadge={false} />
          </div>

          <div className="w-full max-w-[94%] sm:max-w-[85%] min-w-0 p-3 sm:p-4 bg-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] space-y-1">
            <div className="flex items-center justify-between gap-2">
              <p className="text-[10px] font-black text-[#2D6A4F] uppercase tracking-wider">
                {isKhmer
                  ? `លំហាត់ស្កែនបាន ${worksheetQueue ? worksheetQueue.activeIndex + 1 : 1}`
                  : `SCANNED PROBLEM ${worksheetQueue ? worksheetQueue.activeIndex + 1 : 1}`}
              </p>
              {completedStepIndices.length > 0 && (
                <button
                  type="button"
                  onClick={onResetProgress}
                  title={isKhmer ? 'ចាប់ផ្ដើមពីដើម' : 'Reset to Step 1'}
                  className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-black text-[#2D6A4F] border border-[#2D6A4F]/40 rounded-lg hover:bg-[#E8F5E9] hover:border-[#1B4332] transition-all cursor-pointer shrink-0"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>{isKhmer ? 'ចាប់ផ្ដើមពីដើម' : 'Start fresh'}</span>
                </button>
              )}
            </div>
            <p className="text-sm sm:text-base md:text-lg font-black text-[#1B4332] leading-relaxed">
              {isKhmer
                ? activeProblem.problemStatementKhmer || activeProblem.problemStatementEng
                : activeProblem.problemStatementEng || activeProblem.problemStatementKhmer}
            </p>
          </div>
        </div>
      )}

      {/* Step Trail — aligned with the card body column */}
      {activeProblem.steps && activeProblem.steps.length > 0 && (
        <div className="flex items-center gap-2 sm:gap-3 w-full flex-row">
          <div className="w-8 h-8 sm:w-10 sm:h-10 shrink-0 opacity-0 pointer-events-none" />
          <div className="w-full max-w-[94%] sm:max-w-[85%] min-w-0 flex justify-center">
            <StepTrail
              currentStep={currentStepIndex + 1}
              totalSteps={activeProblem.steps.length}
              completedSteps={completedStepIndices}
              maxUnlockedStep={maxUnlockedStepIndex + 1}
              language={profile.language}
              onSelectStep={(stepIdx) => {
                if (stepIdx <= maxUnlockedStepIndex || completedStepIndices.includes(stepIdx)) {
                  onSelectStep(stepIdx);
                }
              }}
            />
          </div>
        </div>
      )}

      {/* Step Card — aligned with mascot box column */}
      {currentStep && (
        <div className="flex items-start gap-2 sm:gap-3 w-full flex-row animate-fadeIn">
          {/* Aligned Mascot Box for Step Card */}
          <div className="w-8 h-8 sm:w-10 sm:h-10 bg-[#40916C] rounded-lg sm:rounded-2xl shrink-0 border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] flex items-center justify-center p-0.5">
            <TunsayAvatar
              size="sm"
              state={
                completedStepIndices.includes(currentStepIndex)
                  ? 'celebrating'
                  : 'explaining'
              }
              showBadge={false}
            />
          </div>

          <div className="w-full max-w-[94%] sm:max-w-[85%] min-w-0">
            <StepCard
              step={currentStep}
              isCompleted={completedStepIndices.includes(currentStepIndex)}
              language={profile.language}
              visualData={activeProblem.visualData}
              onAnswerSubmit={onStepAnswer}
              onNextStep={onNextStep}
              onOpenHints={onOpenHints}
              onOpenExplainDifferently={onOpenExplainDifferently}
            />
          </div>
        </div>
      )}
    </div>
  );
};
