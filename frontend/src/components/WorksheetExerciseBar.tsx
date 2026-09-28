import React, { useRef } from 'react';
import { ChevronLeft, ChevronRight, CheckCircle, BookOpen, History } from 'lucide-react';
import { HomeworkProblem, Language } from '../types';

interface WorksheetExerciseBarProps {
  problems: HomeworkProblem[];
  activeIndex: number;
  completedIds: string[];
  language: Language;
  onSelectExercise: (index: number) => void;
  onViewAllChats?: () => void;
}

export const WorksheetExerciseBar: React.FC<WorksheetExerciseBarProps> = ({
  problems,
  activeIndex,
  completedIds,
  language,
  onSelectExercise,
  onViewAllChats,
}) => {
  const isKhmer = language === 'km';
  const scrollRef = useRef<HTMLDivElement>(null);

  if (problems.length <= 1) return null;

  const scroll = (dir: 'left' | 'right') => {
    scrollRef.current?.scrollBy({ left: dir === 'left' ? -200 : 200, behavior: 'smooth' });
  };

  const completedSet = new Set(completedIds);

  return (
    <div className="w-full shrink-0 bg-white border-b-2 border-[#1B4332]/15 px-1.5 sm:px-2.5 py-1.5 sm:py-2 flex items-center gap-1 sm:gap-1.5 relative z-10">
      {/* Left scroll */}
      <button
        type="button"
        onClick={() => scroll('left')}
        className="shrink-0 w-6 h-6 sm:w-7 sm:h-7 flex items-center justify-center bg-[#E8F5E9] hover:bg-[#A7CDB4] rounded-lg border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] sm:shadow-[1.5px_1.5px_0px_#1B4332] cursor-pointer transition-all hover:-translate-y-0.5 active:translate-y-0"
        aria-label="Scroll left"
      >
        <ChevronLeft className="w-3 h-3 sm:w-3.5 sm:h-3.5 stroke-[3] text-[#1B4332]" />
      </button>

      {/* Header label or All Chats button */}
      {onViewAllChats ? (
        <button
          type="button"
          onClick={onViewAllChats}
          className="shrink-0 flex items-center gap-1 px-1.5 sm:px-2 py-1 bg-[#E8F5E9] hover:bg-[#A7CDB4] rounded-lg border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] sm:shadow-[1.5px_1.5px_0px_#1B4332] cursor-pointer text-[#1B4332] transition-all hover:-translate-y-0.5 active:translate-y-0"
          title={isKhmer ? 'ត្រឡប់ទៅប្រវត្តិឆាតទាំងអស់' : 'Back to All Chat History'}
        >
          <History className="w-3 h-3 text-[#1B4332]" />
          <span className="text-[9px] font-black uppercase tracking-wider whitespace-nowrap">
            {isKhmer ? 'ប្រវត្តិ' : 'History'}
          </span>
        </button>
      ) : (
        <div className="shrink-0 flex items-center gap-1 px-1">
          <BookOpen className="w-3 h-3 text-[#1B4332]/60" />
          <span className="text-[9px] font-black text-[#1B4332]/60 uppercase tracking-wider whitespace-nowrap">
            {isKhmer ? 'លំហាត់' : 'Worksheet'}
          </span>
        </div>
      )}

      {/* Scrollable pills */}
      <div
        ref={scrollRef}
        className="flex-1 flex items-center gap-1 sm:gap-1.5 overflow-x-auto [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden scroll-smooth"
      >
        {problems.map((prob, idx) => {
          const isDone = completedSet.has(prob.id);
          const isActive = idx === activeIndex;
          const label = isKhmer ? `លំហាត់ ${idx + 1}` : `Ex ${idx + 1}`;

          let pillClass =
            'shrink-0 flex items-center gap-1 px-2 sm:px-2.5 py-0.5 sm:py-1 rounded-full text-[10px] font-black border-2 cursor-pointer transition-all select-none whitespace-nowrap ';

          if (isActive && !isDone) {
            pillClass +=
              'bg-[#1B4332] text-white border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] scale-105';
          } else if (isDone) {
            pillClass +=
              'bg-[#40916C] text-white border-[#2D6A4F] shadow-[1px_1px_0px_#1B4332] sm:shadow-[1.5px_1.5px_0px_#1B4332]';
          } else {
            pillClass +=
              'bg-[#E8F5E9] text-[#1B4332] border-[#1B4332]/40 hover:border-[#1B4332] hover:bg-[#A7CDB4]/40 hover:-translate-y-0.5 active:translate-y-0';
          }

          return (
            <button
              key={prob.id}
              type="button"
              onClick={() => onSelectExercise(idx)}
              className={pillClass}
              title={isKhmer ? prob.titleKhmer : prob.titleEng}
              aria-pressed={isActive}
            >
              {isDone ? (
                <CheckCircle className="w-2.5 h-2.5 sm:w-3 sm:h-3 shrink-0" />
              ) : isActive ? (
                <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-[#40916C] rounded-full border border-white shrink-0 animate-pulse" />
              ) : (
                <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-[#1B4332]/30 rounded-full shrink-0" />
              )}
              {label}
            </button>
          );
        })}
      </div>

      {/* Progress fraction */}
      <div className="shrink-0 px-1 text-[9px] font-black text-[#1B4332]/50 whitespace-nowrap">
        {completedIds.length}/{problems.length}
      </div>

      {/* Right scroll */}
      <button
        type="button"
        onClick={() => scroll('right')}
        className="shrink-0 w-6 h-6 sm:w-7 sm:h-7 flex items-center justify-center bg-[#E8F5E9] hover:bg-[#A7CDB4] rounded-lg border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] sm:shadow-[1.5px_1.5px_0px_#1B4332] cursor-pointer transition-all hover:-translate-y-0.5 active:translate-y-0"
        aria-label="Scroll right"
      >
        <ChevronRight className="w-3 h-3 sm:w-3.5 sm:h-3.5 stroke-[3] text-[#1B4332]" />
      </button>
    </div>
  );
};
