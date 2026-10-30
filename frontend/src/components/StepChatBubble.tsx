import React, { useState, useEffect } from 'react';
import { StepItem, Language } from '../types';
import { Lightbulb, RefreshCw, CheckCircle, AlertCircle, ArrowRight, ListOrdered, ChevronLeft, ChevronRight, Volume2 } from 'lucide-react';
import { cleanBilingualOption } from '../utils/language';
import { VisualWidget } from './VisualWidget';
import { OptionIcon } from './OptionIcon';
import { answersMatch, expectsNumericAnswer, normalizeWithKhmer } from '../utils/answerNormalization';

interface StepChatBubbleProps {
  step: StepItem;
  stepIndex: number;
  totalSteps: number;
  language: Language;
  completedStepIndices: number[];
  visualData?: any;
  /** True if this is the currently active step the student is solving */
  isLatest: boolean;
  onOpenHints: () => void;
  onOpenAllSteps?: () => void;
  onOpenExplainDifferently?: () => void;
  onNavigateStep: (idx: number) => void;
  /** Callback fired when student submits an answer via the inline input */
  onStepAnswerSubmit?: (stepIndex: number, studentAnswer: string, isCorrect: boolean) => void;
}

export const StepChatBubble: React.FC<StepChatBubbleProps> = ({
  step,
  stepIndex,
  totalSteps,
  language = 'en',
  completedStepIndices,
  visualData,
  isLatest: _isLatest,
  onOpenHints,
  onOpenAllSteps,
  onOpenExplainDifferently,
  onNavigateStep,
  onStepAnswerSubmit,
}) => {
  const isKhmer = language === 'km';
  const rawStep = step as any;
  const stepNum = step.stepNumber || rawStep.step_number || stepIndex + 1;

  const isCompleted =
    completedStepIndices.includes(stepIndex) ||
    step.status === 'completed' ||
    rawStep.status === 'completed';

  const [inputAnswer, setInputAnswer] = useState('');
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<'none' | 'correct' | 'incorrect'>('none');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Sync state when navigating between steps or when step updates
  useEffect(() => {
    if (isCompleted) {
      setFeedback('correct');
      const ans = step.student_answer || rawStep.student_answer || step.correctAnswer || '';
      setInputAnswer(ans);
      setSelectedOption(ans || null);
    } else {
      setInputAnswer('');
      setSelectedOption(null);
      setFeedback('none');
    }
    setIsSubmitting(false);
  }, [stepIndex, step.stepNumber, isCompleted, rawStep.student_answer]);

  const handleSpeakPrompt = () => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    if (isSpeaking) {
      setIsSpeaking(false);
      return;
    }
    const textToSpeak = `${promptText}. ${clueText || ''}`;
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.rate = 0.9;
    utterance.pitch = 1.05;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  };

  // Clean helper: strips markdown tokens so strings render cleanly into UI components
  const stripMd = (str?: string): string => {
    if (!str) return '';
    return str
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/^>\s?/gm, '')
      .replace(/^#+\s?/gm, '')
      .replace(/`([^`]+)`/g, '$1')
      .trim();
  };

  const questionTitle = stripMd(
    (isKhmer ? step.questionKhmer : step.questionEng) ||
    step.mission ||
    rawStep.mission ||
    step.title ||
    rawStep.title ||
    (isKhmer ? `ជំហានទី ${stepNum}` : `Step ${stepNum}`)
  );

  const promptText = stripMd(
    (isKhmer ? step.socraticPromptKhmer : step.socraticPromptEng) ||
    step.yourTurn ||
    rawStep.your_turn ||
    (isKhmer ? step.questionKhmer : step.questionEng) ||
    ''
  );

  const expectedAnswer = step.correctAnswer || rawStep.expectedAnswer || rawStep.expected_answer;
  const acceptableAnswers: string[] = Array.isArray(rawStep.acceptable_answers)
    ? rawStep.acceptable_answers
    : Array.isArray(rawStep.acceptableAnswers)
    ? rawStep.acceptableAnswers
    : Array.isArray(step.acceptableAnswers)
    ? step.acceptableAnswers
    : [];
  const showNumberPad = expectsNumericAnswer(step);

  const checkIsCorrect = (studentAns: string): boolean => {
    if (!studentAns.trim()) return false;
    if (!expectedAnswer || !expectedAnswer.trim()) return true;

    if (answersMatch(studentAns, expectedAnswer, acceptableAnswers)) return true;

    // Mathematical problem verification for dynamic prompts:
    // e.g. "which two numbers add together to make 10?" -> student typed "4 6", "6 4", "៤ ៦"
    const promptCombined = `${questionTitle} ${promptText}`.toLowerCase();
    if (promptCombined.includes('10') || promptCombined.includes('ដប់') || promptCombined.includes('ten')) {
      if (promptCombined.includes('add') || promptCombined.includes('make') || promptCombined.includes('បូក') || promptCombined.includes('បង្កើត')) {
        const normAns = normalizeWithKhmer(studentAns);
        const nums = normAns.match(/\d+/g)?.map(Number);
        if (nums && nums.length === 2 && nums[0] + nums[1] === 10) {
          return true;
        }
      }
    }

    return false;
  };

  const handleOptionClick = (rawOption: string) => {
    if (isSubmitting || feedback === 'correct') return;
    const cleaned = cleanBilingualOption(rawOption, language);
    setSelectedOption(cleaned);
    setInputAnswer(cleaned);
    setIsSubmitting(true);

    const isCorrect = checkIsCorrect(cleaned);
    setFeedback(isCorrect ? 'correct' : 'incorrect');
    onStepAnswerSubmit?.(stepIndex, cleaned, isCorrect);

    if (isCorrect) {
      setTimeout(() => {
        if (stepIndex + 1 < totalSteps) {
          onNavigateStep(stepIndex + 1);
        }
      }, 850);
    } else {
      setIsSubmitting(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputAnswer.trim();
    if (!trimmed || isSubmitting || feedback === 'correct') return;

    setIsSubmitting(true);
    const isCorrect = checkIsCorrect(trimmed);
    setFeedback(isCorrect ? 'correct' : 'incorrect');
    onStepAnswerSubmit?.(stepIndex, trimmed, isCorrect);

    if (isCorrect) {
      setTimeout(() => {
        if (stepIndex + 1 < totalSteps) {
          onNavigateStep(stepIndex + 1);
        }
      }, 850);
    } else {
      setIsSubmitting(false);
    }
  };

  const canGoBack = stepIndex > 0;
  const canGoNext = (isCompleted || stepIndex < Math.max(...completedStepIndices, -1)) && stepIndex + 1 < totalSteps;

  const handleHintClick = () => {
    onOpenHints?.();
  };

  const clueText = stripMd(
    step.clue ||
    rawStep.clue ||
    (Array.isArray(step.hints) && step.hints.length > 0 ? step.hints[0] : '') ||
    (Array.isArray(rawStep.hints) && rawStep.hints.length > 0 ? rawStep.hints[0] : '')
  );

  return (
    <div className="w-full bg-white rounded-2xl sm:rounded-3xl border-2 sm:border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] sm:shadow-[4px_4px_0px_#1B4332] p-3.5 sm:p-5 lg:p-6 space-y-3.5 sm:space-y-4 animate-fadeIn">
      {/* Top Banner: Step Indicator */}
      <div className="flex items-center justify-between flex-wrap gap-2 pb-2.5 sm:pb-3 border-b-2 border-[#1B4332]/20">
        <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
          <span className="px-2.5 py-0.5 bg-[#2D6A4F] text-white text-[10px] sm:text-xs font-black rounded-full border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] inline-block shrink-0">
            {isKhmer 
              ? `ជំហានទី ${stepNum} នៃ ${totalSteps}` 
              : `Step ${stepNum} of ${totalSteps}`}
          </span>
          <h4 className="text-sm sm:text-base lg:text-lg font-black text-[#1B4332] font-heading min-w-0 line-clamp-2 break-words">
            {questionTitle}
          </h4>
        </div>

        {onOpenAllSteps && (
          <button
            type="button"
            onClick={onOpenAllSteps}
            className="px-2.5 py-1 sm:px-3 sm:py-1.5 bg-[#2D6A4F] hover:bg-[#40916C] text-white text-[11px] sm:text-xs font-black rounded-lg sm:rounded-xl border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] flex items-center gap-1.5 transition-all cursor-pointer shrink-0"
          >
            <ListOrdered className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{isKhmer ? 'បញ្ជីជំហាន' : 'View all steps'}</span>
          </button>
        )}
      </div>

      {/* ReanMore Socratic Guiding Prompt with Embedded Visual Support & Helpful Tip */}
      <div className="p-3 sm:p-4 bg-[#E8F5E9] rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] space-y-2.5 sm:space-y-3">
        <div>
          <div className="flex items-center justify-between gap-2 mb-1">
            <p className="text-[10px] sm:text-xs font-black text-[#1B4332] uppercase tracking-wider">
              {isKhmer ? 'សំណួរណែនាំពី ReanMore៖' : "ReanMore's Guiding Prompt:"}
            </p>
            <button
              type="button"
              onClick={handleSpeakPrompt}
              title={isKhmer ? 'អានសំណួរឮៗ' : 'Listen to question'}
              className={`px-2 py-0.5 rounded-full border border-[#1B4332]/30 flex items-center gap-1 text-[10px] font-black transition-all cursor-pointer ${
                isSpeaking
                  ? 'bg-[#2D6A4F] text-white animate-pulse'
                  : 'bg-white/90 hover:bg-white text-[#1B4332] shadow-sm hover:scale-105 active:scale-95'
              }`}
            >
              <Volume2 className="w-3.5 h-3.5 stroke-[2.5]" />
              <span>{isSpeaking ? (isKhmer ? 'កំពុងអាន...' : 'Reading...') : (isKhmer ? 'ស្តាប់' : 'Listen')}</span>
            </button>
          </div>
          <p className="text-sm sm:text-base lg:text-lg font-black text-[#1B4332] leading-relaxed">
            {promptText}
          </p>
        </div>

        {/* Kid-Friendly Helpful Tip Banner */}
        {clueText && (
          <div className="p-2 sm:p-2.5 bg-white/95 rounded-lg sm:rounded-xl border border-[#2D6A4F]/30 text-xs sm:text-sm text-[#1B4332] font-semibold flex items-start gap-2 shadow-[1px_1px_0px_#1B4332]">
            <Lightbulb className="w-4 h-4 text-[#2D6A4F] shrink-0 mt-0.5" />
            <div className="leading-snug">
              <span className="font-black text-[#2D6A4F] uppercase text-[10px] sm:text-xs block mb-0.5">
                {isKhmer ? 'តម្រុយជំនួយ៖' : 'Helpful Tip:'}
              </span>
              <span>{clueText}</span>
            </div>
          </div>
        )}

        {/* Visual Widget directly inside the Guiding Prompt box */}
        {visualData && (
          <div className="pt-1.5 sm:pt-2 max-w-full overflow-x-auto">
            <VisualWidget
              visualData={visualData}
              step={step}
              language={language}
              onSelect={(val) => {
                const singleVal = Array.isArray(val) ? val[0] || '' : val;
                setInputAnswer(singleVal);
                handleOptionClick(singleVal);
              }}
            />
          </div>
        )}
      </div>



      {/* Answer Options or Input Area */}
      {((step.options && step.options.length > 0) || (rawStep.options && rawStep.options.length > 0)) ? (
        <div className="space-y-2 sm:space-y-3">
          <p className="text-[11px] sm:text-xs font-black text-[#1B4332] uppercase">
            {isKhmer ? 'ជ្រើសរើសចម្លើយរបស់អ្នក៖' : 'Choose your answer:'}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3">
            {((step.options && step.options.length > 0) ? step.options : rawStep.options).map((opt: string, idx: number) => {
              const displayOpt = cleanBilingualOption(opt, language);
              const isSelected = selectedOption === displayOpt || inputAnswer === displayOpt;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleOptionClick(opt)}
                  disabled={isSubmitting || feedback === 'correct'}
                  className={`p-2.5 sm:p-3.5 rounded-xl sm:rounded-2xl border-2 sm:border-3 font-black text-xs sm:text-sm md:text-base transition-all text-left flex items-center justify-between cursor-pointer ${
                    isSelected && feedback === 'correct'
                      ? 'bg-[#2D6A4F] border-[#1B4332] text-white shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332]'
                      : isSelected && feedback === 'incorrect'
                      ? 'bg-[#2D6A4F] border-[#1B4332] text-white shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332]'
                      : 'bg-white border-[#1B4332] text-[#1B4332] hover:bg-[#40916C] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332]'
                  }`}
                >
                  <span className="flex items-center gap-2 min-w-0 flex-1">
                    <OptionIcon label={displayOpt} />
                    <span className="break-words whitespace-normal">{displayOpt}</span>
                  </span>
                  {isSelected && feedback === 'correct' && (
                    <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-[#1B4332] stroke-[3] shrink-0" />
                  )}
                  {isSelected && feedback === 'incorrect' && (
                    <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 text-white stroke-[3] shrink-0" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      ) : (
        <form onSubmit={handleFormSubmit} className="space-y-2 sm:space-y-3">
          {/* Quick Number Tap Chips for Young Learners (Kill Typing Anxiety).
              Only shown for genuinely numeric answers — science steps answer with words. */}
          {showNumberPad && (
            <div className="flex items-center gap-1.5 overflow-x-auto py-1 scrollbar-none">
              {['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'].map((digit) => (
                <button
                  key={digit}
                  type="button"
                  onClick={() => setInputAnswer((prev) => prev + digit)}
                  disabled={isSubmitting || feedback === 'correct'}
                  className="w-8 h-8 sm:w-9 sm:h-9 bg-white hover:bg-[#A7CDB4] text-[#1B4332] font-black rounded-lg border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] flex items-center justify-center text-xs sm:text-sm active:translate-y-0.5 shrink-0 cursor-pointer"
                >
                  {digit}
                </button>
              ))}
              <button
                type="button"
                onClick={() => setInputAnswer((prev) => prev.slice(0, -1))}
                disabled={isSubmitting || feedback === 'correct' || !inputAnswer}
                className="px-2 h-8 sm:h-9 bg-white hover:bg-red-50 text-red-600 font-black rounded-lg border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] flex items-center justify-center text-xs shrink-0 cursor-pointer"
                title="Delete"
              >
                ⌫
              </button>
            </div>
          )}

          <div className="flex items-center gap-2">
            <input
              type="text"
              value={inputAnswer}
              onChange={(e) => {
                setInputAnswer(e.target.value);
                if (feedback === 'incorrect') setFeedback('none');
              }}
              disabled={isSubmitting || feedback === 'correct'}
              placeholder={
                showNumberPad
                  ? (isKhmer ? 'វាយចម្លើយ ឬចុចលេខខាងលើ...' : 'Type or tap numbers above...')
                  : (isKhmer ? 'វាយចម្លើយរបស់អ្នក...' : 'Type your answer...')
              }
              className="flex-1 p-2.5 sm:p-3.5 bg-[#E8F5E9] rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] font-black text-xs sm:text-sm md:text-base text-[#1B4332] focus:outline-none focus:bg-white focus:ring-2 focus:ring-[#2D6A4F] disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={!inputAnswer.trim() || isSubmitting || feedback === 'correct'}
              className="px-4 py-2.5 sm:px-5 sm:py-3.5 bg-[#1B4332] disabled:opacity-50 text-white font-black rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 transition-transform cursor-pointer shrink-0"
            >
              <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 stroke-[3]" />
            </button>
          </div>
        </form>
      )}

      {/* Feedback Banner: Correct */}
      {feedback === 'correct' && (
        <div className="p-2.5 sm:p-3.5 bg-[#2D6A4F] text-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] flex items-center justify-between flex-wrap gap-2 font-black text-xs sm:text-sm animate-fadeIn">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 stroke-[3] shrink-0" />
            <span>{isKhmer ? 'ត្រឹមត្រូវហើយ! ពូកែណាស់!' : 'Correct! Awesome job!'}</span>
          </div>
          {canGoNext && (
            <button
              type="button"
              onClick={() => onNavigateStep(stepIndex + 1)}
              className="px-3 py-1.5 bg-white text-[#1B4332] hover:bg-[#A7CDB4] rounded-lg sm:rounded-xl border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] text-xs font-black flex items-center gap-1.5 cursor-pointer transition-all active:scale-95 shrink-0"
            >
              <span>{isKhmer ? 'ទៅកាន់ជំហានបន្ទាប់' : 'Go to Next Step'}</span>
              <ArrowRight className="w-3.5 h-3.5 stroke-[3]" />
            </button>
          )}
        </div>
      )}

      {/* Feedback Banner: Incorrect */}
      {feedback === 'incorrect' && (
        <div className="p-2.5 sm:p-3.5 bg-[#2D6A4F] text-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] flex items-center justify-between gap-2 font-black text-xs sm:text-sm animate-fadeIn">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 stroke-[3] shrink-0" />
            <span>{isKhmer ? 'ព្យាយាមម្តងទៀត! មើលតម្រុយខាងក្រោម' : 'Try again! Check the hint below'}</span>
          </div>
          <button
            type="button"
            onClick={handleHintClick}
            className="px-2.5 py-1 bg-[#40916C] text-white rounded-lg sm:rounded-xl border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] text-xs font-black cursor-pointer shrink-0 hover:scale-105 active:scale-95 transition-transform"
          >
            {isKhmer ? 'តម្រុយ' : 'Hint'}
          </button>
        </div>
      )}

      {/* Scaffolding Action Buttons & Stepper Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-2 sm:gap-3 pt-2 border-t-2 border-[#1B4332]/20">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <button
            type="button"
            onClick={handleHintClick}
            className="px-3 py-1.5 sm:px-4 sm:py-2 bg-[#40916C] text-white hover:bg-[#40916C]/80 rounded-xl sm:rounded-2xl font-black text-xs sm:text-sm md:text-base border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] flex items-center gap-1.5 sm:gap-2 transition-all cursor-pointer"
          >
            <Lightbulb className="w-3.5 h-3.5 sm:w-4 sm:h-4 fill-[#1B4332] stroke-[2.5]" />
            <span>{isKhmer ? 'តម្រុយ' : 'Hint'}</span>
          </button>

          {onOpenExplainDifferently && (
            <button
              type="button"
              onClick={onOpenExplainDifferently}
              className="px-3 py-1.5 sm:px-4 sm:py-2 bg-[#A7CDB4] text-[#1B4332] hover:bg-[#A7CDB4]/80 rounded-xl sm:rounded-2xl font-black text-xs sm:text-sm md:text-base border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] flex items-center gap-1.5 sm:gap-2 transition-all cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[2.5]" />
              <span className="hidden sm:inline">{isKhmer ? 'ពន្យល់តាមរបៀបផ្សេង' : 'Explain Differently'}</span>
            </button>
          )}
        </div>

        {/* Stepper Navigation */}
        <div className="flex items-center gap-1 sm:gap-1.5">
          <button
            type="button"
            onClick={() => onNavigateStep(stepIndex - 1)}
            disabled={!canGoBack}
            className="p-1.5 sm:p-2 bg-white disabled:opacity-40 disabled:cursor-not-allowed rounded-lg sm:rounded-xl border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] sm:shadow-[1.5px_1.5px_0px_#1B4332] text-[#1B4332] font-black cursor-pointer hover:-translate-y-0.5 active:translate-y-0.5 shrink-0"
            title={isKhmer ? 'ថយក្រោយ' : 'Previous Step'}
          >
            <ChevronLeft className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[3]" />
          </button>

          <div className="flex items-center gap-1 px-0.5">
            {Array.from({ length: totalSteps }).map((_, idx) => {
              const isDone = completedStepIndices.includes(idx);
              const isCurrent = idx === stepIndex;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onNavigateStep(idx)}
                  className={`w-5 h-5 sm:w-6 sm:h-6 rounded-full text-[10px] sm:text-xs font-black flex items-center justify-center border-2 border-[#1B4332] transition-all cursor-pointer ${
                    isCurrent
                      ? 'bg-[#1B4332] text-white scale-110 shadow-[1px_1px_0px_#1B4332]'
                      : isDone
                      ? 'bg-[#2D6A4F] text-white'
                      : 'bg-white text-[#1B4332]/60'
                  }`}
                >
                  {isDone ? '✓' : idx + 1}
                </button>
              );
            })}
          </div>

          <button
            type="button"
            onClick={() => onNavigateStep(stepIndex + 1)}
            disabled={!canGoNext}
            className="p-1.5 sm:p-2 bg-white disabled:opacity-40 disabled:cursor-not-allowed rounded-lg sm:rounded-xl border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] sm:shadow-[1.5px_1.5px_0px_#1B4332] text-[#1B4332] font-black cursor-pointer hover:-translate-y-0.5 active:translate-y-0.5 shrink-0"
            title={isKhmer ? 'បន្ទាប់' : 'Next Step'}
          >
            <ChevronRight className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[3]" />
          </button>
        </div>
      </div>
    </div>
  );
};
