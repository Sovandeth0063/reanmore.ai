import React from 'react';
import { Language } from '../types';

interface LanguageSwitcherProps {
  language: Language;
  onSelectLanguage: (lang: Language) => void;
  compact?: boolean;
}

export const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({
  language,
  onSelectLanguage,
}) => {
  return (
    <div className="inline-flex items-center bg-[#40916C] border-3 border-[#1B4332] rounded-2xl p-1 shadow-[3px_3px_0px_#1B4332] text-xs">
      <button
        type="button"
        onClick={() => onSelectLanguage('km')}
        className={`px-2.5 py-1 rounded-xl font-black transition-all cursor-pointer ${
          language === 'km'
            ? 'bg-[#1B4332] text-white border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] -translate-y-0.5'
            : 'text-[#1B4332] hover:bg-black/10'
        }`}
        title="ភាសាខ្មែរ (Khmer)"
        aria-pressed={language === 'km'}
      >
        KM
      </button>

      <button
        type="button"
        onClick={() => onSelectLanguage('en')}
        className={`px-2.5 py-1 rounded-xl font-black transition-all cursor-pointer ${
          language === 'en'
            ? 'bg-[#1B4332] text-white border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] -translate-y-0.5'
            : 'text-[#1B4332] hover:bg-black/10'
        }`}
        title="English"
        aria-pressed={language === 'en'}
      >
        EN
      </button>
    </div>
  );
};
