import React from 'react';
import { CheckCircle, Circle, BookOpen, Star, ArrowLeft } from 'lucide-react';
import { HomeworkProblem, Language } from '../types';

interface WorksheetProgressPanelProps {
  problems: HomeworkProblem[];
  activeIndex: number;
  completedIds: string[];
  language: Language;
  worksheetTitle?: string;
  onSelectExercise: (index: number) => void;
  onViewAllChats?: () => void;
}

export const WorksheetProgressPanel: React.FC<WorksheetProgressPanelProps> = ({
  problems,
  activeIndex,
  completedIds,
  language,
  worksheetTitle,
  onSelectExercise,
  onViewAllChats,
}) => {
  const isKhmer = language === 'km';
  const completedSet = new Set(completedIds);
  const doneCount = completedIds.length;
  const total = problems.length;
  const pct = total > 0 ? Math.round((doneCount / total) * 100) : 0;
  const allDone = doneCount >= total;

  return (
    <div className="flex flex-col h-full min-h-0 flex-1 overflow-hidden">
      {/* Header */}
      <div className="px-3 pt-3 pb-2 shrink-0">
        <div className="flex items-center justify-between gap-1.5 mb-2">
          <div className="flex items-center gap-1.5 min-w-0">
            <BookOpen className="w-3.5 h-3.5 text-[#1B4332] shrink-0" />
            <span className="text-[10px] font-black text-[#1B4332] uppercase tracking-wider truncate">
              {worksheetTitle || (isKhmer ? 'ទំព័រលំហាត់' : 'Worksheet')}
            </span>
          </div>
          {onViewAllChats && (
            <button
              type="button"
              onClick={onViewAllChats}
              className="text-[9px] font-black text-[#1B4332] bg-white hover:bg-[#A7CDB4] px-2 py-1 rounded-lg border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] shrink-0 cursor-pointer transition-all active:translate-y-0.5 flex items-center gap-1"
              title={isKhmer ? 'មើលប្រវត្តិជជែកទាំងអស់' : 'View All Recent Chats'}
            >
              <ArrowLeft className="w-3 h-3 stroke-[3]" />
              <span>{isKhmer ? 'ប្រវត្តិឆាត' : 'All Chats'}</span>
            </button>
          )}
        </div>

        {/* Progress bar */}
        <div className="h-3 w-full bg-[#E8F5E9] rounded-full border-2 border-[#1B4332] overflow-hidden shadow-[1px_1px_0px_#1B4332]">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${pct}%`,
              background: allDone
                ? 'linear-gradient(90deg, #40916C, #2D6A4F)'
                : 'linear-gradient(90deg, #A7CDB4, #40916C)',
            }}
          />
        </div>

        {/* Fraction */}
        <div className="flex items-center justify-between mt-1.5">
          <span className="text-[9px] font-black text-[#1B4332]/60 uppercase tracking-wider">
            {isKhmer ? 'ដំណើរការ' : 'Progress'}
          </span>
          <span className={`text-[10px] font-black ${allDone ? 'text-[#2D6A4F]' : 'text-[#1B4332]/70'}`}>
            {allDone ? (isKhmer ? '✓ រួចរាល់!' : '✓ All done!') : `${doneCount} / ${total}`}
          </span>
        </div>
      </div>

      {/* Exercise list */}
      <div className="flex-1 min-h-0 overflow-y-auto px-2 pb-3 space-y-1 overscroll-contain">
        {problems.map((prob, idx) => {
          const isDone = completedSet.has(prob.id);
          const isActive = idx === activeIndex;
          const label = isKhmer ? `លំហាត់ ${idx + 1}` : `Exercise ${idx + 1}`;
          const title = isKhmer ? prob.titleKhmer : prob.titleEng;

          return (
            <button
              key={prob.id}
              type="button"
              onClick={() => onSelectExercise(idx)}
              className={`w-full text-left px-2.5 py-2 rounded-xl border-2 transition-all cursor-pointer group flex items-center gap-2 ${
                isActive
                  ? 'bg-white border-[#1B4332] shadow-[2px_2px_0px_#1B4332]'
                  : isDone
                  ? 'bg-[#40916C]/10 border-[#40916C]/30 hover:border-[#40916C]'
                  : 'bg-transparent border-transparent hover:bg-[#E8F5E9] hover:border-[#1B4332]/20'
              }`}
            >
              {/* Status icon */}
              <div className="shrink-0">
                {isDone ? (
                  <CheckCircle className="w-4 h-4 text-[#40916C]" />
                ) : isActive ? (
                  <div className="w-4 h-4 rounded-full bg-[#1B4332] flex items-center justify-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#40916C] animate-pulse" />
                  </div>
                ) : (
                  <Circle className="w-4 h-4 text-[#1B4332]/25" />
                )}
              </div>

              {/* Text */}
              <div className="min-w-0 flex-1">
                <p className={`text-[10px] font-black truncate ${
                  isActive ? 'text-[#1B4332]' : isDone ? 'text-[#2D6A4F]' : 'text-[#1B4332]/50'
                }`}>
                  {label}
                </p>
                {title && (
                  <p className="text-[9px] text-[#1B4332]/40 font-bold truncate leading-tight">
                    {title}
                  </p>
                )}
              </div>

              {/* Step dots (show completed steps if problem has steps) */}
              {prob.steps.length > 0 && (
                <div className="shrink-0 flex items-center gap-0.5">
                  {prob.steps.slice(0, 5).map((_, si) => (
                    <span
                      key={si}
                      className={`w-1.5 h-1.5 rounded-full ${
                        isDone
                          ? 'bg-[#40916C]'
                          : isActive && si < (prob.steps.length ?? 0)
                          ? 'bg-[#1B4332]/40'
                          : 'bg-[#1B4332]/15'
                      }`}
                    />
                  ))}
                  {prob.steps.length > 5 && (
                    <span className="text-[8px] text-[#1B4332]/30 font-black">+{prob.steps.length - 5}</span>
                  )}
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Completion star badge (shown when all done) */}
      {allDone && (
        <div className="mx-3 mb-3 p-2 bg-[#40916C] rounded-xl border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] flex items-center gap-2 shrink-0">
          <Star className="w-4 h-4 text-yellow-300 fill-yellow-300 shrink-0" />
          <p className="text-[10px] font-black text-white leading-tight">
            {isKhmer ? 'អ្នកបានបញ្ចប់ទំព័រលំហាត់ទាំងអស់!' : 'All exercises complete!'}
          </p>
        </div>
      )}
    </div>
  );
};
