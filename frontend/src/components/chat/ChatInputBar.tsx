import React from 'react';
import { Camera, Calculator, Send, Sparkles } from 'lucide-react';

interface ChatInputBarProps {
  inputQuery: string;
  isSayoThinking: boolean;
  isMathKeypadOpen: boolean;
  setIsMathKeypadOpen: React.Dispatch<React.SetStateAction<boolean>>;
  suggestedChips?: string[] | undefined;
  onOpenScanner: () => void;
  onSendMessage: () => void;
  onChipClick: (chip: string) => void;
  onInputChange: (value: string) => void;
}

export const ChatInputBar: React.FC<ChatInputBarProps> = ({
  inputQuery,
  isSayoThinking,
  isMathKeypadOpen,
  setIsMathKeypadOpen,
  suggestedChips,
  onOpenScanner,
  onSendMessage,
  onChipClick,
  onInputChange,
}) => {
  const isKhmer = false;

  return (
    <div className="px-2.5 sm:px-5 py-2 sm:py-3 bg-white border-t-2 sm:border-t-3 border-[#1B4332] shrink-0 pb-[max(0.5rem,env(safe-area-inset-bottom))]">
      {/* Queue Status Notification Banner */}
      {isSayoThinking && (
        <div className="mb-2 px-3 py-2 bg-emerald-50 border-2 border-emerald-400 rounded-xl flex items-center gap-2 animate-pulse">
          <Sparkles className="w-4 h-4 text-[#2D6A4F] shrink-0" />
          <span className="text-xs sm:text-sm font-black text-[#1B4332]">
            {isKhmer
              ? 'អ្នកស្ថិតក្នុងជួរបន្ទាប់! ReanMore កំពុងគិត...'
              : "You're next in line! ReanMore is preparing your step-by-step guidance..."}
          </span>
        </div>
      )}

      {/* Tap-First Degraded Suggested Chips (Sprint 0.3) */}
      {suggestedChips && suggestedChips.length > 0 && (
        <div className="mb-2 flex items-center gap-1.5 overflow-x-auto pb-1 animate-fadeIn no-scrollbar">
          {suggestedChips.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => onChipClick(chip)}
              className="px-2.5 py-1 text-xs sm:text-sm font-bold bg-[#E8F5E9] hover:bg-[#D8F3DC] text-[#1B4332] rounded-xl border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] active:translate-y-0.5 transition-all whitespace-nowrap cursor-pointer shrink-0"
            >
              {chip}
            </button>
          ))}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSendMessage();
        }}
        className="w-full flex items-center gap-1.5 sm:gap-2.5"
      >
        <button
          type="button"
          onClick={onOpenScanner}
          className="w-10 h-10 sm:w-12 sm:h-12 bg-[#2D6A4F] text-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] flex items-center justify-center hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] transition-all cursor-pointer shrink-0"
          title={isKhmer ? 'ស្កែនរូបថតលំហាត់' : 'Scan Homework Photo'}
        >
          <Camera className="w-5 h-5 sm:w-6 sm:h-6 stroke-[2.5]" />
        </button>

        <button
          type="button"
          onClick={() => setIsMathKeypadOpen((prev) => !prev)}
          className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] flex items-center justify-center hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] transition-all cursor-pointer shrink-0 ${
            isMathKeypadOpen ? 'bg-emerald-700 text-white' : 'bg-[#E8F5E9] text-[#1B4332]'
          }`}
          title="Math Keypad & Problem Builder (Grades 1-6)"
        >
          <Calculator className="w-5 h-5 sm:w-6 sm:h-6 stroke-[2.5]" />
        </button>

        <div className="flex-1 bg-[#E8F5E9] rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] px-3 sm:px-4 flex items-center">
          <input
            type="text"
            value={inputQuery}
            disabled={isSayoThinking}
            onChange={(e) => onInputChange(e.target.value)}
            placeholder={
              isSayoThinking
                ? isKhmer
                  ? 'ReanMore កំពុងគិត...'
                  : 'ReanMore is thinking...'
                : isKhmer
                ? 'សួរអ្វីបន្ថែម ឬ "ខ្ញុំមិនយល់ទេ"...'
                : 'Ask for help or "I\'m stuck"...'
            }
            className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 text-xs sm:text-sm md:text-base py-2 sm:py-2.5 font-bold text-[#1B4332] placeholder:text-[#1B4332]/50 disabled:opacity-60"
          />
        </div>

        <button
          type="submit"
          disabled={!inputQuery.trim() || isSayoThinking}
          className="w-10 h-10 sm:w-12 sm:h-12 bg-[#1B4332] disabled:bg-gray-200 disabled:border-gray-400 text-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] font-black hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] transition-all flex items-center justify-center cursor-pointer shrink-0"
        >
          <Send className="w-4 h-4 sm:w-5 sm:h-5 stroke-[2.5]" />
        </button>
      </form>
    </div>
  );
};
