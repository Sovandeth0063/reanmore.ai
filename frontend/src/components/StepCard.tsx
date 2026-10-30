import React, { useState, useEffect } from 'react';
import { StepItem, Language } from '../types';
import { Lightbulb, RefreshCw, CheckCircle, AlertCircle, ArrowRight, Volume2 } from 'lucide-react';
import { cleanBilingualOption } from '../utils/language';
import { VisualWidget } from './VisualWidget';
import { OptionIcon } from './OptionIcon';
import { fastValidateStepAnswer } from '../services/answerValidationService';
import { expectsNumericAnswer } from '../utils/answerNormalization';

interface StepCardProps {
  step: StepItem;
  isCompleted?: boolean | undefined;
  onNextStep?: (() => void) | undefined;
  language?: Language | undefined;
  visualData?: any;
  onAnswerSubmit: (answer: string) => boolean | Promise<boolean>;
  onOpenHints: () => void;
  onOpenExplainDifferently: () => void;
}

export const StepCard: React.FC<StepCardProps> = ({
  step,
  isCompleted = false,
  onNextStep,
  language = 'en',
  visualData,
  onAnswerSubmit,
  onOpenHints,
  onOpenExplainDifferently,
}) => {
  const isKhmer = language === 'km';
  const showNumberPad = expectsNumericAnswer(step);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<'none' | 'correct' | 'incorrect' | 'near_miss'>('none');
  const [typedAnswer, setTypedAnswer] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Sync state when step changes or when reviewing a completed step
  useEffect(() => {
    if (isCompleted) {
      setFeedback('correct');
      setTypedAnswer(step.student_answer || step.correctAnswer || '');
      setSelectedOption(step.student_answer || step.correctAnswer || null);
    } else {
      setSelectedOption(null);
      setFeedback('none');
      setTypedAnswer('');
    }
    setIsSubmitting(false);
  }, [step.stepNumber, step.id, isCompleted]);

  const handleSpeakPrompt = () => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    if (isSpeaking) {
      setIsSpeaking(false);
      return;
    }
    const promptText = isKhmer ? step.socraticPromptKhmer : step.socraticPromptEng;
    const textToSpeak = `${promptText}. ${step.clue || ''}`;
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.rate = 0.9;
    utterance.pitch = 1.05;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  };

  const handleOptionClick = async (rawOption: string) => {
    if (isSubmitting || feedback === 'correct') return;
    const cleaned = cleanBilingualOption(rawOption, language);
    setSelectedOption(cleaned);
    setIsSubmitting(true);

    // Fast deterministic check (< 1ms)
    const fast = fastValidateStepAnswer(cleaned, step, language);
    if (fast.isDeterministic) {
      setFeedback(fast.isCorrect ? 'correct' : fast.feedbackType);
    }

    const res = onAnswerSubmit(cleaned);
    const isCorrect = typeof res === 'boolean' ? res : await res;
    setFeedback(isCorrect ? 'correct' : (fast.feedbackType || 'incorrect'));
    if (!isCorrect) {
      setIsSubmitting(false);
    }
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!typedAnswer.trim() || isSubmitting || feedback === 'correct') return;
    setIsSubmitting(true);

    // Fast deterministic check (< 1ms)
    const fast = fastValidateStepAnswer(typedAnswer.trim(), step, language);
    if (fast.isDeterministic) {
      setFeedback(fast.isCorrect ? 'correct' : fast.feedbackType);
    }

    const res = onAnswerSubmit(typedAnswer.trim());
    const isCorrect = typeof res === 'boolean' ? res : await res;
    setFeedback(isCorrect ? 'correct' : (fast.feedbackType || 'incorrect'));
    if (!isCorrect) {
      setIsSubmitting(false);
    }
  };

  const handleHintClick = () => {
    onOpenHints?.();
  };

  return (
    <div className="w-full bg-white rounded-2xl sm:rounded-3xl border-2 sm:border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] sm:shadow-[4px_4px_0px_#1B4332] p-3.5 sm:p-5 lg:p-6 space-y-3.5 sm:space-y-4 animate-fadeIn">
      {/* Top Banner: Step Indicator */}
      <div className="flex items-center justify-between flex-wrap gap-2 pb-2.5 sm:pb-3 border-b-2 border-[#1B4332]/20">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="px-2.5 py-0.5 bg-[#2D6A4F] text-white text-[10px] sm:text-xs font-black rounded-full border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] inline-block shrink-0">
            {isKhmer 
              ? `ជំហានទី ${step.stepNumber} នៃ ${step.totalSteps}` 
              : `Step ${step.stepNumber} of ${step.totalSteps}`}
          </span>
          <h4 className="text-sm sm:text-base lg:text-lg font-black text-[#1B4332] font-heading min-w-0 line-clamp-2 break-words">
            {isKhmer ? step.questionKhmer : step.questionEng}
          </h4>
        </div>
      </div>

      {/* ReanMore Socratic Guiding Prompt with Embedded Visual Support */}
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
            {isKhmer ? step.socraticPromptKhmer : step.socraticPromptEng}
          </p>
        </div>

        {/* Kid-Friendly Helpful Tip / Clue Banner */}
        {step.clue && (
          <div className="p-2 sm:p-2.5 bg-white/90 rounded-lg sm:rounded-xl border border-[#2D6A4F]/30 text-xs sm:text-sm text-[#1B4332] font-semibold flex items-start gap-2 shadow-[1px_1px_0px_#1B4332]">
            <Lightbulb className="w-4 h-4 text-[#2D6A4F] shrink-0 mt-0.5" />
            <div className="leading-snug">
              <span className="font-black text-[#2D6A4F] uppercase text-[10px] sm:text-xs block mb-0.5">
                {isKhmer ? 'តម្រុយជំនួយ៖' : 'Helpful Tip:'}
              </span>
              <span>{step.clue}</span>
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
                setTypedAnswer(singleVal);
                handleOptionClick(singleVal);
              }}
            />
          </div>
        )}
      </div>



      {/* Answer Options or Input Area */}
      {step.options ? (
        <div className="space-y-2 sm:space-y-3">
          <p className="text-[11px] sm:text-xs font-black text-[#1B4332] uppercase">
            {isKhmer ? 'ជ្រើសរើសចម្លើយរបស់អ្នក៖' : 'Choose your answer:'}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3">
            {step.options.map((opt, idx) => {
              const displayOpt = cleanBilingualOption(opt, language);
              const isSelected = selectedOption === displayOpt;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleOptionClick(opt)}
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
          {/* Quick Number Tap Chips for Young Learners — numeric steps only */}
          {showNumberPad && (
            <div className="flex items-center gap-1.5 overflow-x-auto py-1 scrollbar-none">
              {['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'].map((digit) => (
                <button
                  key={digit}
                  type="button"
                  onClick={() => setTypedAnswer((prev) => prev + digit)}
                  disabled={isSubmitting || feedback === 'correct'}
                  className="w-8 h-8 sm:w-9 sm:h-9 bg-white hover:bg-[#A7CDB4] text-[#1B4332] font-black rounded-lg border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] flex items-center justify-center text-xs sm:text-sm active:translate-y-0.5 shrink-0 cursor-pointer"
                >
                  {digit}
                </button>
              ))}
              <button
                type="button"
                onClick={() => setTypedAnswer((prev) => prev.slice(0, -1))}
                disabled={isSubmitting || feedback === 'correct' || !typedAnswer}
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
              value={typedAnswer}
              onChange={(e) => setTypedAnswer(e.target.value)}
              placeholder={
                showNumberPad
                  ? (isKhmer ? 'វាយចម្លើយ ឬចុចលេខខាងលើ...' : 'Type or tap numbers above...')
                  : (isKhmer ? 'វាយចម្លើយរបស់អ្នក...' : 'Type your answer...')
              }
              className="flex-1 p-2.5 sm:p-3.5 bg-[#E8F5E9] rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] font-black text-xs sm:text-sm md:text-base text-[#1B4332] focus:outline-none focus:bg-white"
            />
            <button
              type="submit"
              className="px-4 py-2.5 sm:px-5 sm:py-3.5 bg-[#1B4332] text-white font-black rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 transition-transform cursor-pointer shrink-0"
            >
              <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5 stroke-[3]" />
            </button>
          </div>
        </form>
      )}

      {/* Feedback Banner */}
      {feedback === 'correct' && (
        <div className="p-2.5 sm:p-3.5 bg-[#2D6A4F] text-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] flex items-center justify-between flex-wrap gap-2 font-black text-xs sm:text-sm animate-fadeIn">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 stroke-[3] shrink-0" />
            <span>{isKhmer ? 'ត្រឹមត្រូវហើយ! ពូកែណាស់!' : 'Correct! Awesome job!'}</span>
          </div>
          {onNextStep && (
            <button
              type="button"
              onClick={onNextStep}
              className="px-3 py-1.5 bg-white text-[#1B4332] hover:bg-[#A7CDB4] rounded-lg sm:rounded-xl border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] text-xs font-black flex items-center gap-1.5 cursor-pointer transition-all active:scale-95 shrink-0"
            >
              <span>{isKhmer ? 'ទៅកាន់ជំហានបន្ទាប់' : 'Go to Next Step'}</span>
              <ArrowRight className="w-3.5 h-3.5 stroke-[3]" />
            </button>
          )}
        </div>
      )}

      {(feedback === 'incorrect' || feedback === 'near_miss') && (
        <div className="p-2.5 sm:p-3.5 bg-[#2D6A4F] text-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] flex items-center justify-between gap-2 font-black text-xs sm:text-sm animate-fadeIn">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 stroke-[3] shrink-0" />
            <span>
              {feedback === 'near_miss'
                ? (isKhmer ? 'ជិតត្រូវហើយ! មើលតម្រុយខាងក្រោម' : 'So close! Check the hint below')
                : (isKhmer ? 'ព្យាយាមម្តងទៀត! មើលតម្រុយខាងក្រោម' : 'Try again! Check the hint below')}
            </span>
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

      {/* Scaffolding Action Buttons (Hint & Explain Differently) */}
      <div className="flex flex-wrap items-center justify-between gap-2 sm:gap-3 pt-2 border-t-2 border-[#1B4332]/20">
        <button
          type="button"
          onClick={handleHintClick}
          className="px-3 py-1.5 sm:px-4 sm:py-2 bg-[#40916C] text-white hover:bg-[#40916C]/80 rounded-xl sm:rounded-2xl font-black text-xs sm:text-sm md:text-base border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] flex items-center gap-1.5 sm:gap-2 transition-all cursor-pointer"
        >
          <Lightbulb className="w-3.5 h-3.5 sm:w-4 sm:h-4 fill-[#1B4332] stroke-[2.5]" />
          <span>{isKhmer ? 'តម្រុយ' : 'Hint'}</span>
        </button>

        <button
          type="button"
          onClick={onOpenExplainDifferently}
          className="px-3 py-1.5 sm:px-4 sm:py-2 bg-[#A7CDB4] text-[#1B4332] hover:bg-[#A7CDB4]/80 rounded-xl sm:rounded-2xl font-black text-xs sm:text-sm md:text-base border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] flex items-center gap-1.5 sm:gap-2 transition-all cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[2.5]" />
          <span>{isKhmer ? 'ពន្យល់តាមរបៀបផ្សេង' : 'Explain Differently'}</span>
        </button>
      </div>
    </div>
  );
};
