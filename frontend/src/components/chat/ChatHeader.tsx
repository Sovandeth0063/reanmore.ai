import React from 'react';
import { UserProfile, WorksheetQueue } from '../../types';
import { TunsayAvatar } from '../TunsayAvatar';
import { WorksheetExerciseBar } from '../WorksheetExerciseBar';
import { Menu, Plus, ArrowLeft, GraduationCap } from 'lucide-react';

interface ChatHeaderProps {
  profile: UserProfile;
  isSayoThinking: boolean;
  onOpenMobileSidebar: () => void;
  onNewChat: () => void;
  onBackToHome?: (() => void) | undefined;
  worksheetQueue?: WorksheetQueue | undefined;
  onSelectExercise?: ((index: number) => void) | undefined;
  onViewAllChats?: (() => void) | undefined;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  profile,
  isSayoThinking,
  onOpenMobileSidebar,
  onNewChat,
  onBackToHome,
  worksheetQueue,
  onSelectExercise,
  onViewAllChats,
}) => {
  const isKhmer = false;

  return (
    <>
      <div className="p-2 sm:p-4 bg-[#1B4332] border-b-2 sm:border-b-3 border-[#1B4332] flex items-center justify-between gap-2 shrink-0">
        <div className="flex items-center gap-2 sm:gap-3 min-w-0">
          <button
            type="button"
            onClick={onOpenMobileSidebar}
            className="lg:hidden p-1.5 sm:p-2 bg-[#40916C] text-white hover:bg-white hover:text-[#1B4332] rounded-lg sm:rounded-xl border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] flex items-center justify-center cursor-pointer transition-all active:translate-y-0.5 shrink-0"
            title={isKhmer ? 'ប្រវត្តិជជែក' : 'Chat History'}
          >
            <Menu className="w-4 h-4 stroke-[2.5]" />
          </button>

          <div className="relative">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-[#40916C] rounded-lg sm:rounded-2xl flex items-center justify-center border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332]">
              <TunsayAvatar size="sm" state={isSayoThinking ? 'thinking' : 'idle'} showBadge={false} />
            </div>
            <span
              className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 sm:w-3 sm:h-3 bg-[#2D6A4F] border-2 border-[#1B4332] rounded-full"
              title="Online"
            />
          </div>

          <div>
            <h3 className="font-black text-xs sm:text-sm md:text-base text-white flex items-center gap-1 font-heading leading-tight drop-shadow-[1px_1px_0px_#1B4332]">
              {isKhmer ? 'ReanMore' : 'ReanMore AI'}
            </h3>
            <p className="text-[10px] sm:text-xs text-white font-black flex items-center gap-1 drop-shadow-[1px_1px_0px_#1B4332]">
              <GraduationCap className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-white" />
              {isKhmer ? `ថ្នាក់ទី ${profile.grade}` : `Grade ${profile.grade}`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
          <button
            type="button"
            onClick={onNewChat}
            className="w-8 h-8 sm:w-10 sm:h-10 bg-[#40916C] text-white hover:bg-white hover:text-[#1B4332] rounded-lg sm:rounded-2xl flex items-center justify-center transition-all cursor-pointer border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] active:translate-x-0.5 active:translate-y-0.5 shrink-0"
            title={isKhmer ? 'ចាប់ផ្តើមជជែកថ្មី' : 'New Chat'}
          >
            <Plus className="w-4 h-4 sm:w-5 sm:h-5 stroke-[3]" />
          </button>

          {onBackToHome && (
            <button
              type="button"
              onClick={onBackToHome}
              className="px-2.5 sm:px-3.5 py-1.5 bg-[#40916C] text-white hover:bg-white hover:text-[#1B4332] rounded-lg sm:rounded-2xl text-xs sm:text-sm font-black transition-all flex items-center gap-1 cursor-pointer border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] active:translate-x-0.5 active:translate-y-0.5 shrink-0"
            >
              <ArrowLeft className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[3]" />
              <span className="hidden min-[380px]:inline">{isKhmer ? 'ទំព័រដើម' : 'Home'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Worksheet Exercise Bar — shown when multi-exercise queue is active */}
      {worksheetQueue && worksheetQueue.problems.length > 1 && (
        <WorksheetExerciseBar
          problems={worksheetQueue.problems}
          activeIndex={worksheetQueue.activeIndex}
          completedIds={worksheetQueue.completedIds}
          language={profile.language}
          onSelectExercise={(idx) => onSelectExercise?.(idx)}
          onViewAllChats={onViewAllChats || (() => {})}
        />
      )}
    </>
  );
};
