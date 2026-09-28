import React, { useEffect, useRef } from 'react';
import { Star, ChevronRight, RotateCcw, Sparkles } from 'lucide-react';
import { TunsayAvatar } from './TunsayAvatar';
import { Language } from '../types';

interface ExerciseCelebrationBannerProps {
  exerciseNumber: number;           // 1-based
  totalExercises: number;
  exerciseTitleKhmer?: string;
  exerciseTitleEng?: string;
  language: Language;
  hasNext: boolean;
  onNext: () => void;
  onReview: () => void;
}

const STAR_POSITIONS = [
  { top: '8%',  left: '5%',  size: 20, delay: 0 },
  { top: '15%', left: '92%', size: 16, delay: 0.15 },
  { top: '70%', left: '8%',  size: 14, delay: 0.1 },
  { top: '75%', left: '88%', size: 18, delay: 0.2 },
  { top: '30%', left: '50%', size: 12, delay: 0.05 },
  { top: '5%',  left: '55%', size: 15, delay: 0.25 },
];

export const ExerciseCelebrationBanner: React.FC<ExerciseCelebrationBannerProps> = ({
  exerciseNumber,
  totalExercises,
  exerciseTitleKhmer,
  exerciseTitleEng,
  language,
  hasNext,
  onNext,
  onReview,
}) => {
  const isKhmer = language === 'km';
  const bannerRef = useRef<HTMLDivElement>(null);

  // Scroll into view when shown
  useEffect(() => {
    bannerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, []);

  const title = isKhmer
    ? (exerciseTitleKhmer || `លំហាត់ ${exerciseNumber}`)
    : (exerciseTitleEng || `Exercise ${exerciseNumber}`);

  const doneText = isKhmer
    ? `អ្នកបានបញ្ចប់ ${title} ហើយ! 🎉`
    : `You completed ${title}! 🎉`;

  const allDone = !hasNext;

  const bigText = allDone
    ? (isKhmer ? 'អ្នកបញ្ចប់ទំព័រលំហាត់ទាំងអស់ហើយ! 🌟' : 'You finished the whole worksheet! 🌟')
    : doneText;

  const subText = allDone
    ? (isKhmer ? 'អ្នកពូកែណាស់! រៀនបានគ្រប់ប្រភេទ' : 'Amazing work! You tackled every exercise.')
    : (isKhmer
        ? `${exerciseNumber} / ${totalExercises} ☑`
        : `${exerciseNumber} of ${totalExercises} done ☑`);

  return (
    <div
      ref={bannerRef}
      className="relative w-full rounded-2xl sm:rounded-3xl border-3 border-[#1B4332] shadow-[4px_4px_0px_#1B4332] overflow-hidden my-4"
      style={{ background: 'linear-gradient(135deg, #1B4332 0%, #2D6A4F 60%, #40916C 100%)' }}
    >
      {/* Floating stars */}
      {STAR_POSITIONS.map((s, i) => (
        <Star
          key={i}
          className="absolute fill-yellow-300 text-yellow-300 animate-bounce"
          style={{
            top: s.top,
            left: s.left,
            width: s.size,
            height: s.size,
            animationDelay: `${s.delay}s`,
            animationDuration: '1.2s',
            opacity: 0.75,
          }}
        />
      ))}

      {/* Sparkles overlay */}
      <Sparkles className="absolute top-3 right-12 w-5 h-5 text-yellow-300/60 animate-spin" style={{ animationDuration: '3s' }} />

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center gap-4 px-6 py-6 sm:py-8 text-center">
        {/* Mascot */}
        <div className="animate-bounce" style={{ animationDuration: '0.8s' }}>
          <TunsayAvatar size="lg" state="celebrating" showBadge={false} className="drop-shadow-lg" />
        </div>

        {/* Main text */}
        <div className="space-y-1.5">
          <h2 className="font-black text-xl sm:text-2xl text-white drop-shadow-[2px_2px_0px_#1B4332] leading-tight">
            {bigText}
          </h2>
          <p className="text-sm font-bold text-[#A7CDB4]">{subText}</p>
        </div>

        {/* Progress dots (one per exercise) */}
        {totalExercises > 1 && (
          <div className="flex items-center gap-2">
            {Array.from({ length: totalExercises }).map((_, i) => (
              <div
                key={i}
                className={`rounded-full border-2 border-white/60 transition-all ${
                  i < exerciseNumber
                    ? 'w-4 h-4 bg-yellow-300 border-yellow-400 shadow-[0_0_6px_rgba(253,224,71,0.8)]'
                    : 'w-3 h-3 bg-white/20'
                }`}
              />
            ))}
          </div>
        )}

        {/* CTA buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full max-w-xs">
          {hasNext && (
            <button
              type="button"
              onClick={onNext}
              className="flex-1 py-3 px-5 rounded-2xl bg-yellow-300 hover:bg-yellow-200 text-[#1B4332] font-black text-sm border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] flex items-center justify-center gap-2 cursor-pointer transition-all hover:-translate-y-0.5 active:translate-y-0 active:shadow-[1px_1px_0px_#1B4332]"
            >
              {isKhmer ? 'លំហាត់បន្ទាប់' : 'Next Exercise'}
              <ChevronRight className="w-4 h-4 stroke-[3]" />
            </button>
          )}
          <button
            type="button"
            onClick={onReview}
            className={`${hasNext ? 'flex-none' : 'flex-1'} py-3 px-5 rounded-2xl bg-white/20 hover:bg-white/30 text-white font-black text-sm border-3 border-white/40 flex items-center justify-center gap-2 cursor-pointer transition-all hover:-translate-y-0.5 active:translate-y-0 backdrop-blur-sm`}
          >
            <RotateCcw className="w-3.5 h-3.5 stroke-[2.5]" />
            {isKhmer ? (allDone ? 'ត្រលប់ទៅផ្ទះ' : 'មើលឡើងវិញ') : (allDone ? 'Back to Home' : 'Review')}
          </button>
        </div>
      </div>
    </div>
  );
};
