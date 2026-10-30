import React from 'react';
import { UserProfile, UserAccount, UserRole, Language } from '../types';
import { Home, BookOpen, User, Award, Languages } from 'lucide-react';
import logoWhiteImg from '../assets/logo_white.png';

export type TabType = 'home' | 'chat' | 'profile' | 'report';

interface HeaderProps {
  profile: UserProfile;
  currentUser?: UserAccount | null;
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
  onOpenAuth?: (requiredRole?: UserRole) => void;
  onLogout?: () => void;
  language?: Language;
  onToggleLanguage?: () => void;
}

const NAV_ITEMS = [
  { key: 'home' as const, labelKhmer: 'ទំព័រដើម', labelEng: 'Home', icon: Home },
  { key: 'chat' as const, labelKhmer: 'លំហាត់', labelEng: 'Homework', icon: BookOpen },
  { key: 'report' as const, labelKhmer: 'របាយការណ៍', labelEng: 'Report', icon: Award },
  { key: 'profile' as const, labelKhmer: 'ប្រូហ្វាល', labelEng: 'Profile', icon: User },
];

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onSelectTab,
  language = 'en',
  onToggleLanguage,
}) => {
  const isKhmer = language === 'km';
  const isChat = activeTab === 'chat';

  return (
    <header className="sticky top-0 z-40 bg-[#1B4332] border-b-2 sm:border-b-[3px] border-[#1B4332] shadow-[0_3px_0px_#2D6A4F] sm:shadow-[0_4px_0px_#2D6A4F] select-none">
      <div className={`${isChat ? 'w-full px-1.5 sm:px-4 lg:px-6' : 'max-w-7xl mx-auto px-2 sm:px-4 md:px-6'} py-2 sm:py-2.5`}>
        <div className="flex items-center justify-between gap-1.5 sm:gap-3 w-full">
          {/* Logo: Centered over history sidebar on desktop chat */}
          <div
            className={`flex items-center shrink-0 cursor-pointer ${
              isChat ? 'lg:w-[28%] lg:min-w-[260px] lg:max-w-[340px] lg:justify-center' : ''
            }`}
            onClick={() => onSelectTab('home')}
            title="ReanMore AI Tutor"
          >
            <img
              src={logoWhiteImg}
              alt="ReanMore AI Tutor"
              className="h-7 sm:h-8 md:h-9 w-auto object-contain hover:scale-105 transition-transform drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)]"
            />
          </div>

          {/* Navigation & Auth */}
          <div className="flex items-center gap-1.5 sm:gap-2.5">
            {onToggleLanguage && (
              <button
                type="button"
                onClick={onToggleLanguage}
                title={isKhmer ? 'Switch to English' : 'ប្តូរទៅភាសាខ្មែរ'}
                aria-label={isKhmer ? 'Switch to English' : 'Switch to Khmer'}
                className="flex items-center gap-1 px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg sm:rounded-xl font-black text-[10px] sm:text-xs bg-[#2D6A4F] text-white border-2 border-[#1B4332] hover:bg-[#40916C] cursor-pointer"
              >
                <Languages className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                <span>{isKhmer ? 'EN' : 'ខ្មែរ'}</span>
              </button>
            )}
            <nav className="flex items-center gap-1 sm:gap-1.5 md:gap-2">
              {NAV_ITEMS.map((item) => {
                const isActive = activeTab === item.key;
                const Icon = item.icon;
                const label = isKhmer ? item.labelKhmer : item.labelEng;

                return (
                  <button
                    key={item.key}
                    type="button"
                    onClick={() => {
                      onSelectTab(item.key);
                    }}
                    aria-current={isActive ? 'page' : undefined}
                    title={label}
                    className={`relative flex items-center gap-1 sm:gap-1.5 px-2.5 py-1.5 sm:px-3.5 sm:py-2 md:px-4 md:py-2 rounded-lg sm:rounded-xl font-black text-xs sm:text-sm transition-all cursor-pointer border-2 ${
                      isActive
                        ? 'bg-[#40916C] text-white border-[#A7CDB4] shadow-[1.5px_1.5px_0px_#A7CDB4] sm:shadow-[2px_2px_0px_#A7CDB4]'
                        : 'bg-[#2D6A4F] text-white border-[#1B4332] hover:bg-[#40916C]'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0 ${isActive ? 'text-white' : 'text-white/90'}`} />
                    <span className="truncate">
                      {label}
                    </span>
                    {isActive && (
                      <span className="absolute -bottom-[3px] left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-[#A7CDB4] rounded-full" />
                    )}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>
      </div>
    </header>
  );
};
