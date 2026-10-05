import React from 'react';
import { UserProfile, UserAccount, UserRole } from '../types';
import { Home, BookOpen, User, Award, LogIn, LogOut, ChevronDown, Cpu } from 'lucide-react';
import logoWhiteImg from '../assets/logo_white.png';

export type TabType = 'home' | 'chat' | 'profile' | 'report';

interface HeaderProps {
  profile: UserProfile;
  currentUser?: UserAccount | null;
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
  onOpenAuth?: (requiredRole?: UserRole) => void;
  onLogout?: () => void;
  onOpenLLMController?: () => void;
}

const NAV_ITEMS = [
  { key: 'home' as const, labelKhmer: 'ទំព័រដើម', labelEng: 'Home', icon: Home },
  { key: 'chat' as const, labelKhmer: 'លំហាត់', labelEng: 'Homework', icon: BookOpen },
  { key: 'report' as const, labelKhmer: 'របាយការណ៍', labelEng: 'Report', icon: Award },
  { key: 'profile' as const, labelKhmer: 'ប្រូហ្វាល', labelEng: 'Profile', icon: User },
];

export const Header: React.FC<HeaderProps> = ({
  profile,
  currentUser,
  activeTab,
  onSelectTab,
  onOpenAuth,
  onLogout,
  onOpenLLMController,
}) => {
  const isKhmer = profile.language === 'km';
  const role = currentUser?.role || profile.role || 'student';
  const isParent = role === 'parent';

  return (
    <header className="sticky top-0 z-40 bg-[#1B4332] border-b-2 sm:border-b-[3px] border-[#1B4332] shadow-[0_3px_0px_#2D6A4F] sm:shadow-[0_4px_0px_#2D6A4F] select-none">
      <div className="max-w-7xl mx-auto px-2 sm:px-4 md:px-6 py-2 sm:py-2.5">
        <div className="flex items-center justify-between gap-1.5 sm:gap-3">
          {/* Logo */}
          <div
            className="flex items-center gap-2 shrink-0 cursor-pointer"
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
                      // If clicking Parent Report while in student mode, prompt parent authentication
                      if (item.key === 'report' && role === 'student' && onOpenAuth) {
                        onOpenAuth('parent');
                        return;
                      }
                      onSelectTab(item.key);
                    }}
                    aria-current={isActive ? 'page' : undefined}
                    title={label}
                    className={`relative flex items-center gap-1 sm:gap-1.5 px-2 py-1.5 sm:px-3 sm:py-2 md:px-3.5 md:py-2 rounded-lg sm:rounded-xl font-black text-xs sm:text-sm transition-all cursor-pointer border-2 ${
                      isActive
                        ? 'bg-[#40916C] text-white border-[#A7CDB4] shadow-[1.5px_1.5px_0px_#A7CDB4] sm:shadow-[2px_2px_0px_#A7CDB4]'
                        : 'bg-[#2D6A4F] text-white border-[#1B4332] hover:bg-[#40916C]'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0 ${isActive ? 'text-white' : 'text-white/90'}`} />
                    <span className={`truncate ${isActive ? 'inline min-[400px]:inline' : 'hidden min-[480px]:inline'}`}>
                      {label}
                    </span>
                    {isActive && (
                      <span className="absolute -bottom-[3px] left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-[#A7CDB4] rounded-full" />
                    )}
                  </button>
                );
              })}
            </nav>

            {/* AI Engine Controller Button */}
            {onOpenLLMController && (
              <button
                type="button"
                onClick={onOpenLLMController}
                title={isKhmer ? 'ប្តូរម៉ូដែល AI (LLM Controller)' : 'AI Engine Switcher'}
                className="flex items-center gap-1 sm:gap-1.5 px-2 py-1.5 sm:px-2.5 sm:py-2 rounded-lg sm:rounded-xl bg-[#2D6A4F] hover:bg-[#40916C] text-[#D8F3DC] hover:text-white border-2 border-[#1B4332] font-black text-xs sm:text-sm transition-all cursor-pointer shadow-[1.5px_1.5px_0px_rgba(0,0,0,0.2)] active:scale-95"
              >
                <Cpu className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[#74C69D] shrink-0" />
                <span className="hidden min-[560px]:inline text-xs font-bold tracking-tight">AI Engine</span>
              </button>
            )}

            {/* Auth Account / Switcher / Logout */}
            <div className="flex items-center gap-1 sm:gap-2 pl-1.5 sm:pl-2.5 ml-0.5 sm:ml-1 border-l-2 border-white/20">
              {currentUser ? (
                <div className="flex items-center gap-1 sm:gap-2">
                  {/* Account Badge / Switcher Button */}
                  <button
                    type="button"
                    onClick={() => onOpenAuth?.()}
                    title={isKhmer ? 'ប្តូរគណនី' : 'Switch Account'}
                    className="flex items-center gap-1 sm:gap-1.5 px-2 py-1.5 sm:px-3 sm:py-2 md:px-3.5 md:py-2 rounded-lg sm:rounded-xl bg-[#2D6A4F] hover:bg-[#40916C] text-white border-2 border-[#1B4332] font-black text-xs sm:text-sm transition-all cursor-pointer shadow-[1.5px_1.5px_0px_rgba(0,0,0,0.2)]"
                  >
                    <span className="text-xs sm:text-sm">{isParent ? '👩‍👧' : '👦'}</span>
                    <span className="inline max-w-[80px] sm:max-w-[110px] truncate text-white">
                      {currentUser.profile.name.split(' ')[0]}
                    </span>
                    <ChevronDown className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white/70 shrink-0" />
                  </button>

                  {/* Log Out Button */}
                  <button
                    type="button"
                    onClick={() => onLogout?.()}
                    title={isKhmer ? 'ចាកចេញពីគណនី' : 'Log Out'}
                    className="flex items-center gap-1 sm:gap-1.5 px-2 py-1.5 sm:px-3 sm:py-2 md:px-3.5 md:py-2 rounded-lg sm:rounded-xl bg-red-700 hover:bg-red-600 text-white border-2 border-red-900 font-black text-xs sm:text-sm transition-all cursor-pointer shadow-[1.5px_1.5px_0px_rgba(0,0,0,0.2)] active:scale-95"
                  >
                    <LogOut className="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0" />
                    <span className="hidden sm:inline">{isKhmer ? 'ចាកចេញ' : 'Log Out'}</span>
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => onOpenAuth?.()}
                  title={isKhmer ? 'ចូលគណនី' : 'Log In'}
                  className="flex items-center gap-1.5 px-2 py-1.5 sm:px-3 sm:py-2 md:px-3.5 md:py-2 rounded-lg sm:rounded-xl bg-amber-400 hover:bg-amber-300 text-[#1B4332] border-2 border-amber-600 font-black text-xs sm:text-sm transition-all cursor-pointer shadow-[2px_2px_0px_#78350F] active:scale-95"
                >
                  <LogIn className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[#1B4332] shrink-0" />
                  <span className="inline">{isKhmer ? 'ចូលគណនី' : 'Log In'}</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
