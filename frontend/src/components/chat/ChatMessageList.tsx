import React from 'react';
import { ChatMessage, HomeworkProblem, StepItem, UserProfile, WorksheetQueue } from '../../types';
import { TunsayAvatar } from '../TunsayAvatar';
import { StepChatBubble } from '../StepChatBubble';
import { ExerciseCelebrationBanner } from '../ExerciseCelebrationBanner';
import { extractStepWidgetFromMessage, formatMessageText, thinkingTextsEng, thinkingTextsKhmer } from './chatUtils';
import { Camera, User, Sparkles } from 'lucide-react';

interface ChatMessageListProps {
  messages: ChatMessage[];
  profile: UserProfile;
  activeProblem?: HomeworkProblem | undefined;
  celebratingProblemId: string | null;
  worksheetQueue?: WorksheetQueue | undefined;
  setCelebratingProblemId: (id: string | null) => void;
  onSelectExercise?: ((index: number) => void) | undefined;
  isSayoThinking: boolean;
  thinkingTextIdx: number;
  onOpenScanner: () => void;
  onStepHint: (msgId: string) => void;
  onStepNavigate: (msgId: string, targetIdx: number) => void;
  onOpenAllSteps: (msgId: string, widget: any) => void;
  onInlineStepAnswer: (msgId: string, stepIdx: number, ans: string, isCorrect: boolean) => void;
  setActiveModalStep: (step: StepItem | null) => void;
  setIsHintOpen: (open: boolean) => void;
  setIsExplainOpen: (open: boolean) => void;
}

export const ChatMessageList: React.FC<ChatMessageListProps> = ({
  messages,
  profile,
  activeProblem,
  celebratingProblemId,
  worksheetQueue,
  setCelebratingProblemId,
  onSelectExercise,
  isSayoThinking,
  thinkingTextIdx,
  onOpenScanner,
  onStepHint,
  onStepNavigate,
  onOpenAllSteps,
  onInlineStepAnswer,
  setActiveModalStep,
  setIsHintOpen,
  setIsExplainOpen,
}) => {
  const isKhmer = false;

  const displayedMessages = messages.filter((msg) => {
    // Always show messages with no problemId (welcome messages, general chat)
    if (!msg.problemId && !msg.problem?.id) return true;
    // If there's an active problem, show only its messages
    if (activeProblem) {
      if (msg.problemId) return msg.problemId === activeProblem.id;
      if (msg.problem?.id) return msg.problem.id === activeProblem.id;
    }
    return true;
  });

  return (
    <>
      {/* Celebration banner — shown inline after exercise completion */}
      {activeProblem && celebratingProblemId === activeProblem.id && worksheetQueue && (() => {
        const exIdx = worksheetQueue.problems.findIndex((p) => p.id === celebratingProblemId);
        const hasNext = worksheetQueue.problems.some(
          (p, i) => i > exIdx && !worksheetQueue.completedIds.includes(p.id)
        );
        return (
          <ExerciseCelebrationBanner
            exerciseNumber={exIdx + 1}
            totalExercises={worksheetQueue.problems.length}
            exerciseTitleKhmer={activeProblem.titleKhmer}
            exerciseTitleEng={activeProblem.titleEng}
            language={profile.language}
            hasNext={hasNext}
            onNext={() => {
              setCelebratingProblemId(null);
              const nextIdx = worksheetQueue.problems.findIndex(
                (p, i) => i > exIdx && !worksheetQueue.completedIds.includes(p.id)
              );
              if (nextIdx !== -1) onSelectExercise?.(nextIdx);
            }}
            onReview={() => setCelebratingProblemId(null)}
          />
        );
      })()}

      {displayedMessages.map((msg) => {
        const isUser = msg.sender === 'user';
        const displayText = isUser
          ? msg.textEng || msg.textKhmer || ''
          : isKhmer
          ? msg.textKhmer || msg.textEng || ''
          : msg.textEng || msg.textKhmer || '';

        const stepCardData = !isUser ? extractStepWidgetFromMessage(msg) : null;

        return (
          <div
            key={msg.id}
            className={`flex items-start gap-2 sm:gap-3 w-full ${isUser ? 'flex-row-reverse' : 'flex-row'} animate-fadeIn`}
          >
            {!isUser ? (
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-[#40916C] rounded-lg sm:rounded-2xl shrink-0 border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] flex items-center justify-center p-0.5">
                <TunsayAvatar
                  size="sm"
                  state={msg.isSafetyRefusal ? 'encouraging' : 'explaining'}
                  showBadge={false}
                />
              </div>
            ) : (
              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-2xl bg-[#A7CDB4] text-[#1B4332] border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] font-black flex items-center justify-center shrink-0 overflow-hidden">
                {profile.avatarUrl ? (
                  <img src={profile.avatarUrl} alt="You" className="w-full h-full object-cover" />
                ) : (
                  <User className="w-4 h-4 sm:w-5 sm:h-5" />
                )}
              </div>
            )}

            {stepCardData ? (
              <div className="w-full max-w-[94%] sm:max-w-[85%] flex flex-col gap-2 min-w-0">
                {stepCardData.introText && (
                  <div className="p-2.5 sm:p-4 rounded-xl sm:rounded-2xl bg-white text-[#1B4332] border-2 sm:border-2.5 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[2.5px_2.5px_0px_#1B4332] speech-tail-left text-xs sm:text-sm font-black leading-relaxed">
                    {stepCardData.introText}
                  </div>
                )}
                <StepChatBubble
                  step={stepCardData.activeStep}
                  stepIndex={stepCardData.activeIdx}
                  totalSteps={stepCardData.totalSteps}
                  language={profile.language}
                  completedStepIndices={stepCardData.completedSteps}
                  visualData={
                    stepCardData.activeStep?.visualData ||
                    (stepCardData.activeStep as any)?.visual_data ||
                    (stepCardData.widget as any)?.visual_data ||
                    (stepCardData.widget as any)?.visualData ||
                    activeProblem?.visualData ||
                    (activeProblem as any)?.visual_data
                  }
                  isLatest={msg.id === messages[messages.length - 1]?.id}
                  onOpenHints={() => {
                    setActiveModalStep(stepCardData.activeStep);
                    setIsHintOpen(true);
                    onStepHint(msg.id);
                  }}
                  onOpenExplainDifferently={() => {
                    setActiveModalStep(stepCardData.activeStep);
                    setIsExplainOpen(true);
                  }}
                  onOpenAllSteps={() => onOpenAllSteps(msg.id, stepCardData.widget)}
                  onNavigateStep={(targetIdx) => onStepNavigate(msg.id, targetIdx)}
                  onStepAnswerSubmit={(stepIdx, ans, isCorrect) =>
                    onInlineStepAnswer(msg.id, stepIdx, ans, isCorrect)
                  }
                />
                <span className="text-[10px] block font-black opacity-60 ml-2">
                  {msg.timestamp}
                </span>
              </div>
            ) : (
              <div
                className={`max-w-[88%] sm:max-w-[80%] min-w-0 p-2.5 sm:p-4 md:p-5 rounded-xl sm:rounded-3xl border-2 sm:border-3 border-[#1B4332] text-xs sm:text-sm md:text-base leading-relaxed break-words overflow-hidden ${
                  isUser
                    ? 'bg-[#1B4332] text-white shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] speech-tail-right'
                    : msg.isSafetyRefusal
                    ? 'bg-[#2D6A4F] text-white shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] speech-tail-left'
                    : 'bg-white text-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] speech-tail-left'
                }`}
              >
                <div className="font-black text-xs sm:text-sm md:text-base leading-relaxed break-words whitespace-pre-wrap">
                  {formatMessageText(displayText)}
                </div>
                <span className="text-[9px] sm:text-[10px] mt-1.5 block text-right font-black opacity-80">
                  {msg.timestamp}
                </span>
              </div>
            )}
          </div>
        );
      })}

      {/* Socratic Loading / Thinking Message Bubble */}
      {isSayoThinking && (
        <div className="flex items-start gap-2 sm:gap-3 w-full flex-row animate-fadeIn">
          <div className="w-8 h-8 sm:w-10 sm:h-10 bg-[#40916C] rounded-lg sm:rounded-2xl shrink-0 border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] flex items-center justify-center p-0.5 animate-pulse">
            <TunsayAvatar size="sm" state="thinking" showBadge={false} />
          </div>
          <div className="max-w-[88%] sm:max-w-[80%] min-w-0 p-2.5 sm:p-4 rounded-xl sm:rounded-3xl border-2 sm:border-3 border-[#1B4332] bg-white text-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] speech-tail-left flex flex-col gap-1 sm:gap-1.5">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 bg-[#E8F5E9] px-1.5 py-0.5 sm:px-2 sm:py-1 rounded-lg border border-[#A7CDB4]">
                <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-[#40916C] rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-[#2D6A4F] rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-[#1B4332] rounded-full animate-bounce"></span>
              </div>
              <span className="text-xs sm:text-sm font-black text-[#1B4332]">
                {isKhmer ? 'ReanMore កំពុងគិត...' : 'ReanMore is thinking...'}
              </span>
            </div>
            <div className="text-[11px] sm:text-xs md:text-sm font-bold text-[#1B4332]/75 italic pl-0.5 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#2D6A4F] shrink-0" />
              <span>{isKhmer ? thinkingTextsKhmer[thinkingTextIdx] : thinkingTextsEng[thinkingTextIdx]}</span>
            </div>
          </div>
        </div>
      )}

      {/* Fresh Start: Scan Button */}
      {!activeProblem && messages.length <= 1 && (
        <div className="space-y-3 pt-1 pl-1 sm:pl-12 animate-fadeIn">
          <div className="flex flex-wrap gap-2.5">
            <button
              type="button"
              onClick={onOpenScanner}
              className="px-3.5 py-2 sm:px-4 sm:py-2.5 bg-[#2D6A4F] text-white hover:bg-[#40916C] hover:text-white rounded-xl sm:rounded-2xl text-xs sm:text-sm font-black border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] flex items-center gap-1.5 sm:gap-2 transition-all cursor-pointer"
            >
              <Camera className="w-4 h-4 stroke-[2.5]" />
              <span>{isKhmer ? 'ស្កែនរូបថតលំហាត់' : 'Scan Homework Photo'}</span>
            </button>
          </div>
        </div>
      )}
    </>
  );
};
