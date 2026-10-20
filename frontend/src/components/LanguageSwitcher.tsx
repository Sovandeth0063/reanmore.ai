import React from 'react';
import { Language } from '../types';

interface LanguageSwitcherProps {
  language?: Language;
  onSelectLanguage?: (lang: Language) => void;
  compact?: boolean;
}

export const LanguageSwitcher: React.FC<LanguageSwitcherProps> = () => {
  return (
    <div className="inline-flex items-center bg-[#40916C] border-3 border-[#1B4332] rounded-2xl p-1 shadow-[3px_3px_0px_#1B4332] text-xs">
      <div
        className="px-3 py-1 rounded-xl font-black bg-[#1B4332] text-white border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332]"
        title="English"
      >
        EN
      </div>
    </div>
  );
};

