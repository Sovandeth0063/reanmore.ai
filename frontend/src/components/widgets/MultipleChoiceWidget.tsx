/**
 * MultipleChoiceWidget.tsx
 * Multiple choice for science exercises (single and multi-select).
 * Answers are hidden — student picks, then validation is server-side.
 */
import { useState } from 'react';

interface Option {
  label: string;
  emoji?: string;
  name?: string;
}

interface Props {
  options: Option[] | string[];
  multiSelect?: boolean;
  onSelect?: ((selected: string[]) => void) | undefined;
}

function parseOption(opt: Option | string): Option {
  if (typeof opt === 'string') {
    const match = opt.match(/^([A-D])\s+(.+)$/);
    return match ? { label: match[1], name: match[2] } : { label: opt, name: opt };
  }
  return opt;
}

export function MultipleChoiceWidget({ options, multiSelect, onSelect }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const parsed = options.map(parseOption);

  const toggle = (label: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (multiSelect) {
        next.has(label) ? next.delete(label) : next.add(label);
      } else {
        next.clear();
        next.add(label);
      }
      onSelect?.([...next]);
      return next;
    });
  };

  return (
    <div className="w-full bg-white/70 rounded-2xl border-2 border-orange-200 p-4 mb-3">
      <div className="text-xs font-bold text-orange-700 mb-3 uppercase tracking-wider">
        {multiSelect ? 'Select ALL that apply' : 'Choose the best answer'}
      </div>
      <div className="grid grid-cols-2 gap-2">
        {parsed.map(opt => {
          const isSel = selected.has(opt.label);
          return (
            <button
              key={opt.label}
              onClick={() => toggle(opt.label)}
              className={[
                'flex items-center gap-2.5 p-3 rounded-xl border-2 text-left transition-all font-semibold text-sm cursor-pointer',
                isSel ? 'bg-orange-500 border-orange-700 text-white scale-[0.98] shadow-sm' : 'bg-white border-gray-200 hover:border-orange-300 text-gray-800',
              ].join(' ')}
            >
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-black text-xs shrink-0 border-2 ${
                isSel ? 'bg-white text-orange-800 border-white' : 'bg-orange-50 text-orange-900 border-orange-200'
              }`}>
                {opt.label}
              </div>
              <div className="min-w-0">
                <div className="font-bold text-xs sm:text-sm truncate">{opt.name}</div>
              </div>
            </button>
          );
        })}
      </div>
      <p className="text-xs text-orange-600 mt-2 text-center">
        {multiSelect ? 'Select all correct options.' : 'Select the correct option.'}
      </p>
    </div>
  );
}

