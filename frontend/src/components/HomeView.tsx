import React, { useState } from 'react';
import { UserProfile, HomeworkProblem, Subject } from '../types';
import { Camera, MessageSquare, BookOpen, Send, TrendingUp, Zap, Calculator, Atom } from 'lucide-react';
import { getDisplayName } from '../utils/language';
import { TunsayAvatar } from './TunsayAvatar';
import { DailyStreakCard } from './DailyStreakCard';
import { MOCK_PROBLEMS } from '../data/mockProblems';

interface HomeViewProps {
  profile: UserProfile;
  onStartScan: () => void;
  onStartChat: (problem?: HomeworkProblem, initialQuery?: string) => void;
  onSelectGrade?: (grade: UserProfile['grade']) => void;
}

const SUBJECT_META: Record<Subject, { labelKhmer: string; labelEng: string; color: string; icon: typeof Calculator }> = {
  math:    { labelKhmer: 'គណិតវិទ្យា', labelEng: 'Math',    color: 'bg-[#40916C]', icon: Calculator },
  science: { labelKhmer: 'វិទ្យាសាស្ត្រ', labelEng: 'Science', color: 'bg-[#2D6A4F]', icon: Atom },
  english: { labelKhmer: 'ភាសាអង់គ្លេស', labelEng: 'English', color: 'bg-[#1B4332]', icon: BookOpen },
};

export const HomeView: React.FC<HomeViewProps> = ({
  profile,
  onStartScan,
  onStartChat,
}) => {
  const isKhmer = profile.language === 'km';
  const [heroChatInput, setHeroChatInput] = useState('');

  const handleHeroChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (heroChatInput.trim()) {
      onStartChat(undefined, heroChatInput.trim());
      setHeroChatInput('');
    } else {
      onStartChat();
    }
  };

  // Unique subjects from mock problems (filter out english for now)
  const subjects = Array.from(new Set(MOCK_PROBLEMS.map(p => p.subject))).filter(s => s !== 'english');
  // Pick one example problem per subject for quick-start
  const subjectProblems = subjects.map(sub =>
    MOCK_PROBLEMS.find(p => p.subject === sub)
  ).filter(Boolean) as HomeworkProblem[];

  return (
    <div className="space-y-4 sm:space-y-6 animate-fadeIn pb-10 w-full">
      {/* Hero Section with Mascot + Chat Input */}
      <div className="bg-[#A7CDB4] rounded-2xl sm:rounded-3xl border-2 sm:border-3 border-[#1B4332] p-3.5 sm:p-5 lg:p-6 shadow-[3px_3px_0px_#1B4332] sm:shadow-[6px_6px_0px_#1B4332] relative transition-all">
        {/* Decorative dots */}
        <div className="absolute top-3 right-6 w-6 h-6 bg-[#2D6A4F] rounded-full border-2 border-[#1B4332] opacity-30 pointer-events-none" />
        <div className="absolute bottom-3 left-6 w-4 h-4 bg-[#40916C] rounded-full border-2 border-[#1B4332] opacity-30 pointer-events-none" />
        <div className="absolute top-6 left-10 w-3 h-3 bg-white rounded-full border-2 border-[#1B4332] opacity-40 pointer-events-none" />

        <div className="relative z-10 flex flex-col sm:flex-row items-center gap-3 sm:gap-6">
          {/* Text + Input Column */}
          <div className="flex-1 text-[#1B4332] min-w-0 w-full flex flex-col items-center sm:items-start text-center sm:text-left">
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-1.5 sm:gap-2 mb-1.5 sm:mb-2">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 sm:px-3 sm:py-1 rounded-full bg-[#1B4332] text-white text-[11px] sm:text-xs md:text-sm font-black border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332]">
                <span className="truncate">{isKhmer ? 'គ្រូបង្រៀន AI កិច្ចការផ្ទះ' : 'AI Homework Companion'}</span>
              </div>
              <span className="px-2 py-0.5 sm:px-2.5 sm:py-1 bg-white text-[#1B4332] rounded-full border-2 border-[#1B4332] text-[11px] sm:text-xs md:text-sm font-black shadow-[1px_1px_0px_#1B4332]">
                {isKhmer ? `ថ្នាក់ទី ${profile.grade}` : `Grade ${profile.grade}`}
              </span>
            </div>

            <h2 className="text-lg min-[400px]:text-xl sm:text-2xl lg:text-3xl font-black font-heading leading-snug text-[#1B4332] drop-shadow-[1px_1px_0px_#FFFFFF] break-words">
              {isKhmer
                ? `សួស្តី ${getDisplayName(profile.name, true)}! តោះដោះស្រាយលំហាត់ជាមួយគ្នា!`
                : `Hello ${getDisplayName(profile.name, false)}! Ready to solve homework together?`}
            </h2>
            <p className="text-xs sm:text-sm md:text-base font-black text-[#1B4332]/80 leading-relaxed mt-1 sm:mt-2">
              {isKhmer
                ? "ReanMore នឹងជួយណែនាំអ្នកជាជំហានៗយ៉ាងងាយស្រួល!"
                : "ReanMore will guide you step-by-step with ease!"}
            </p>

            {/* Chat Input Box */}
            <form onSubmit={handleHeroChatSubmit} className="pt-2 sm:pt-3 w-full max-w-lg">
              <div className="flex items-center gap-1.5 sm:gap-2 p-1 sm:p-1.5 bg-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2.5px_2.5px_0px_#1B4332] sm:shadow-[4px_4px_0px_#1B4332] focus-within:shadow-[4px_4px_0px_#1B4332] focus-within:-translate-y-0.5 transition-all">
                <input
                  type="text"
                  value={heroChatInput}
                  onChange={(e) => setHeroChatInput(e.target.value)}
                  placeholder={
                    isKhmer
                      ? "វាយសំណួរ ឬលំហាត់របស់អ្នកនៅទីនេះ..."
                      : "Type your homework question here..."
                  }
                  className="flex-1 min-w-0 px-2.5 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-black text-[#1B4332] placeholder-[#1B4332]/45 bg-transparent border-none outline-none focus:ring-0"
                />
                <button
                  type="submit"
                  className="px-3 sm:px-5 py-1.5 sm:py-2 bg-[#40916C] hover:bg-[#ffd768] text-white hover:text-[#1B4332] rounded-lg sm:rounded-xl font-black text-xs sm:text-sm border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer flex items-center gap-1.5 shrink-0"
                >
                  <span>{isKhmer ? 'ផ្ញើ' : 'Send'}</span>
                  <Send className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[3]" />
                </button>
              </div>
            </form>
          </div>

          {/* Mascot Column */}
          <div className="shrink-0 hidden sm:flex flex-col items-center justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-white/40 rounded-full blur-md scale-90" />
              <TunsayAvatar size="lg" state="waving" showBadge={false} />
            </div>
          </div>
        </div>
      </div>

      {/* Action Grid: Photo Scan / Chat */}
      <div className="space-y-2.5 sm:space-y-4">
        <h3 className="text-sm sm:text-lg font-black text-[#1B4332] font-heading flex items-center gap-2">
          <BookOpen className="w-4 h-4 sm:w-5 sm:h-5 text-[#1B4332] shrink-0" />
          <span>{isKhmer ? 'តើអ្នកចង់ធ្វើអ្វីថ្ងៃនេះ?' : 'What would you like to do today?'}</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 sm:gap-4">
          {/* Scan Homework Photo */}
          <button
            type="button"
            onClick={onStartScan}
            className="p-3 sm:p-4 bg-white text-[#1B4332] rounded-xl sm:rounded-3xl border-2 sm:border-3 border-[#1B4332] shadow-[2.5px_2.5px_0px_#1B4332] sm:shadow-[4px_4px_0px_#1B4332] hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[4px_4px_0px_#1B4332] active:translate-x-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] text-left transition-all flex items-center gap-3 sm:gap-4 group cursor-pointer relative"
          >
            <div className="p-2 sm:p-2.5 bg-[#A7CDB4] rounded-xl border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] shrink-0 text-[#1B4332] group-hover:scale-110 transition-transform">
              <Camera className="w-5 h-5 sm:w-7 sm:h-7 text-[#1B4332]" />
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="text-sm sm:text-base lg:text-lg font-black font-heading leading-tight">
                {isKhmer ? 'ស្កែនរូបថតលំហាត់' : 'Scan Homework Photo'}
              </h4>
              <p className="text-[11px] sm:text-xs md:text-sm font-bold text-[#1B4332]/60 mt-0.5 truncate">
                {isKhmer ? 'ថតរូបលំហាត់ហើយ ReanMore នឹងជួយដោះស្រាយ' : 'Snap a photo and ReanMore will help solve it'}
              </p>
            </div>
          </button>

          {/* Ask via Chat */}
          <button
            type="button"
            onClick={() => onStartChat()}
            className="p-3 sm:p-4 bg-white text-[#1B4332] rounded-xl sm:rounded-3xl border-2 sm:border-3 border-[#1B4332] shadow-[2.5px_2.5px_0px_#1B4332] sm:shadow-[4px_4px_0px_#1B4332] hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[4px_4px_0px_#1B4332] active:translate-x-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] text-left transition-all flex items-center gap-3 sm:gap-4 group cursor-pointer relative"
          >
            <div className="p-2 sm:p-2.5 bg-[#A7CDB4] rounded-xl border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] shrink-0 text-[#1B4332] group-hover:scale-110 transition-transform">
              <MessageSquare className="w-5 h-5 sm:w-7 sm:h-7 text-[#1B4332]" />
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="text-sm sm:text-base lg:text-lg font-black font-heading leading-tight">
                {isKhmer ? 'វាយសួរ ReanMore' : 'Ask ReanMore via Chat'}
              </h4>
              <p className="text-[11px] sm:text-xs md:text-sm font-bold text-[#1B4332]/60 mt-0.5 truncate">
                {isKhmer ? 'វាយសំណួរហើយទទួលចម្លើយភ្លាមៗ' : 'Type a question and get instant guidance'}
              </p>
            </div>
          </button>
        </div>
      </div>

      {/* Quick Subject Chips */}
      <div className="space-y-2 sm:space-y-3">
        <h3 className="text-sm sm:text-lg font-black text-[#1B4332] font-heading flex items-center gap-2">
          <Zap className="w-4 h-4 sm:w-5 sm:h-5 text-[#1B4332] shrink-0" />
          <span>{isKhmer ? 'មុខវិជ្ជាពេញនិយម' : 'Popular Subjects'}</span>
        </h3>
        <div className="flex flex-wrap gap-1.5 sm:gap-2.5">
          {subjectProblems.map((prob) => {
            const meta = SUBJECT_META[prob.subject];
            const Icon = meta.icon;
            return (
              <button
                key={prob.id}
                type="button"
                onClick={() => onStartChat(prob)}
                className={`px-2.5 py-1.5 sm:px-4 sm:py-2.5 ${meta.color} text-white rounded-lg sm:rounded-xl border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2.5px_2.5px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] transition-all cursor-pointer flex items-center gap-1.5 sm:gap-2`}
              >
                <Icon className="w-3.5 h-3.5 sm:w-5 sm:h-5 shrink-0" />
                <span className="font-black text-xs sm:text-sm md:text-base">
                  {isKhmer ? meta.labelKhmer : meta.labelEng}
                </span>
              </button>
            );
          })}
          <button
            type="button"
            onClick={() => onStartChat()}
            className="px-2.5 py-1.5 sm:px-4 sm:py-2.5 bg-white text-[#1B4332] rounded-lg sm:rounded-xl border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2.5px_2.5px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] transition-all cursor-pointer flex items-center gap-1.5 sm:gap-2"
          >
            <TrendingUp className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            <span className="font-black text-xs sm:text-sm md:text-base">
              {isKhmer ? 'ផ្សេងៗ' : 'More Topics'}
            </span>
          </button>
        </div>
      </div>

      {/* Daily Streak & Progress Tracker */}
      <DailyStreakCard profile={profile} />
    </div>
  );
};
