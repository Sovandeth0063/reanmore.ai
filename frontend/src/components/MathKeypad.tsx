import React from 'react';
import { Delete, Sparkles, X, Plus, Minus, PieChart, Calculator } from 'lucide-react';

interface MathKeypadProps {
  isOpen: boolean;
  onClose: () => void;
  onInsert: (char: string) => void;
  onBackspace: () => void;
  onClear: () => void;
  onSelectStarter: (problemText: string) => void;
}

const STARTER_PROBLEMS = [
  { label: '15 + 27', desc: 'Add with regrouping', icon: Plus },
  { label: '52 - 18', desc: 'Borrow from tens', icon: Minus },
  { label: '6 × 7', desc: 'Multiplication table', icon: X },
  { label: '2/4 = ?', desc: 'Equivalent fractions', icon: PieChart },
  { label: '12 - 4 = ?', desc: 'Subtract within 20', icon: Calculator },
];

const KEYPAD_BUTTONS = [
  ['1', '2', '3', '+', '½'],
  ['4', '5', '6', '-', '¼'],
  ['7', '8', '9', '×', '¾'],
  ['0', '.', '=', '÷', '⌫'],
];

export const MathKeypad: React.FC<MathKeypadProps> = ({
  isOpen,
  onClose,
  onInsert,
  onBackspace,
  onClear,
  onSelectStarter,
}) => {
  if (!isOpen) return null;

  return (
    <div className="bg-[#E8F5E9] border-t-2 sm:border-t-3 border-[#1B4332] p-3 sm:p-4 animate-fadeIn">
      <div className="max-w-xl mx-auto space-y-3">
        {/* Header & Close */}
        <div className="flex items-center justify-between pb-1">
          <div className="flex items-center gap-1.5 text-xs sm:text-sm font-black text-[#1B4332]">
            <Sparkles className="w-4 h-4 text-emerald-600" />
            <span>Math Problem Builder (Grades 1-6)</span>
          </div>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={onClear}
              className="px-2 py-0.5 text-xs font-bold text-[#1B4332] hover:bg-[#D8F3DC] rounded-lg transition-colors cursor-pointer"
              title="Clear input"
            >
              Clear
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-1 hover:bg-[#D8F3DC] rounded-lg text-[#1B4332] transition-colors cursor-pointer"
              title="Close keypad"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tap-to-Build Quick Problem Starter Chips */}
        <div>
          <div className="text-[10px] sm:text-xs font-bold text-[#1B4332]/70 uppercase tracking-wider mb-1.5">
            Quick Practice Problems:
          </div>
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
            {STARTER_PROBLEMS.map((starter, idx) => {
              const Icon = starter.icon;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onSelectStarter(starter.label)}
                  className="px-2.5 py-1.5 bg-white hover:bg-emerald-50 text-[#1B4332] rounded-xl border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] active:translate-y-0.5 transition-all text-xs font-black flex items-center gap-1.5 shrink-0 cursor-pointer"
                >
                  <Icon className="w-3.5 h-3.5 text-[#2D6A4F]" />
                  <span>{starter.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Tactile Kid Keypad Grid */}
        <div className="grid grid-cols-5 gap-1.5 sm:gap-2">
          {KEYPAD_BUTTONS.flat().map((key, idx) => {
            const isBackspace = key === '⌫';
            const isOperator = ['+', '-', '×', '÷', '='].includes(key);
            const isFraction = ['½', '¼', '¾'].includes(key);

            let bgStyle = 'bg-white text-[#1B4332] hover:bg-emerald-50';
            if (isOperator) {
              bgStyle = 'bg-[#2D6A4F] text-white hover:bg-[#1B4332]';
            } else if (isFraction) {
              bgStyle = 'bg-[#D8F3DC] text-[#1B4332] hover:bg-[#B7E4C7] font-serif';
            } else if (isBackspace) {
              bgStyle = 'bg-amber-100 text-amber-900 hover:bg-amber-200';
            }

            return (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  if (isBackspace) {
                    onBackspace();
                  } else {
                    onInsert(key);
                  }
                }}
                className={`h-10 sm:h-12 rounded-xl border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] active:shadow-none active:translate-y-0.5 text-sm sm:text-base font-black flex items-center justify-center transition-all cursor-pointer ${bgStyle}`}
              >
                {isBackspace ? <Delete className="w-4 h-4 sm:w-5 sm:h-5" /> : key}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
