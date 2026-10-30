/**
 * MultipleChoiceWidget.tsx
 * Multiple choice for science exercises (single and multi-select).
 * Answers are hidden — student picks, then validation is server-side.
 */
import { useState } from 'react';
import { ListChecks } from 'lucide-react';
import { OptionIcon } from '../OptionIcon';
import { stripEmojis } from '../chat/chatUtils';

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

interface ParsedOption {
  key: string;
  name: string;
}

function parseOption(opt: Option | string, idx: number): ParsedOption {
  const fallbackLetter = String.fromCharCode(65 + idx);

  if (typeof opt === 'string') {
    const clean = stripEmojis(opt).replace(/\s+/g, ' ').trim();
    const match = clean.match(/^([A-D])[\s\).:-]+(.+)$/);
    const name = match ? match[2].trim() : clean;
    return { key: name || fallbackLetter, name: name || fallbackLetter };
  }

  const name = stripEmojis(opt.name || opt.label || '')
    .replace(/\s+/g, ' ')
    .trim();
  return { key: name || fallbackLetter, name: name || fallbackLetter };
}

export function MultipleChoiceWidget({ options, multiSelect, onSelect }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const parsed = options.map(parseOption);

  const toggle = (key: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (multiSelect) {
        next.has(key) ? next.delete(key) : next.add(key);
      } else {
        next.clear();
        next.add(key);
      }
      onSelect?.([...next]);
      return next;
    });
  };

  return (
    <div className="w-full bg-white/70 rounded-2xl border-2 border-orange-200 p-4 mb-3">
      <div className="text-xs font-bold text-orange-700 mb-3 uppercase tracking-wider flex items-center gap-1.5">
        <ListChecks className="w-4 h-4" aria-hidden="true" />
        {multiSelect ? 'Select ALL that apply' : 'Choose the best answer'}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {parsed.map(opt => {
          const isSel = selected.has(opt.key);
          return (
            <button
              key={opt.key}
              type="button"
              onClick={() => toggle(opt.key)}
              className={[
                'flex items-center gap-2.5 p-3 rounded-xl border-2 text-left transition-all font-semibold text-sm cursor-pointer',
                isSel
                  ? 'bg-orange-500 border-orange-700 text-white scale-[0.98] shadow-sm'
                  : 'bg-white border-gray-200 hover:border-orange-300 text-gray-800',
              ].join(' ')}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 border-2 ${
                  isSel
                    ? 'bg-white text-orange-800 border-white'
                    : 'bg-orange-50 text-orange-900 border-orange-200'
                }`}
              >
                <OptionIcon label={opt.name} className="w-4 h-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="font-bold text-xs sm:text-sm break-words whitespace-normal">
                  {opt.name}
                </div>
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
