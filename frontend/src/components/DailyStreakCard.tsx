import React, { useState, useEffect } from 'react';
import { Flame, Sparkles, Trophy, Zap, ShieldCheck, Award, Star, Gem, Crown, Check } from 'lucide-react';
import { UserProfile, HomeworkProblem } from '../types';
import { loadActivities } from '../utils/reportUtils';

interface DailyStreakCardProps {
  profile: UserProfile;
  onStartPractice?: (problem?: HomeworkProblem) => void;
}

const STORAGE_KEY = 'reanmore_continuous_streak_v2';

interface StreakMilestone {
  days: number;
  labelKhmer: string;
  labelEng: string;
  icon: React.ComponentType<{ className?: string }>;
  iconColor: string;
  rewardXP: number;
}

const STREAK_MILESTONES: StreakMilestone[] = [
  { days: 3, labelKhmer: 'ពន្លកភ្លើង', labelEng: 'Spark Starter', icon: Zap, iconColor: 'text-amber-400', rewardXP: 50 },
  { days: 7, labelKhmer: 'ភ្លើងឆេះសន្ធោសន្ធៅ', labelEng: 'Flame Master', icon: Flame, iconColor: 'text-orange-500', rewardXP: 100 },
  { days: 14, labelKhmer: 'អគ្គីមាស', labelEng: 'Golden Blaze', icon: Star, iconColor: 'text-yellow-400', rewardXP: 200 },
  { days: 30, labelKhmer: 'ពេជ្រមិនរលត់', labelEng: 'Diamond Spark', icon: Gem, iconColor: 'text-cyan-400', rewardXP: 500 },
  { days: 50, labelKhmer: 'ស្ដេចភ្លើង', labelEng: 'Fire King', icon: Crown, iconColor: 'text-amber-300', rewardXP: 1000 },
  { days: 100, labelKhmer: 'ជើងឯកអមតៈ', labelEng: 'Immortal Streak', icon: Trophy, iconColor: 'text-yellow-500', rewardXP: 2500 },
];

function getTodayString(): string {
  return new Date().toISOString().split('T')[0];
}


export const DailyStreakCard: React.FC<DailyStreakCardProps> = ({ profile, onStartPractice: _onStartPractice }) => {
  const isKhmer = profile.language === 'km';
  const today = getTodayString();

  const [streakState, setStreakState] = useState<{
    currentStreak: number;
    bestStreak: number;
    lastActiveDate: string;
    totalXP: number;
    hasStudiedToday: boolean;
    totalSessions?: number;
    totalTurns?: number;
    dbSource?: string;
  }>(() => {
    // Initial compute from local storage or activities
    const activities = loadActivities();
    const completedActivities = activities.filter(a => a.status === 'completed');
    const uniqueDays = new Set(activities.map(a => a.startedAt.split('T')[0]));
    const calcXP = (completedActivities.length * 50) + (activities.reduce((acc, a) => acc + (a.stepsCompleted || 0), 0) * 15);
    const hasToday = uniqueDays.has(today);

    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        return {
          currentStreak: parsed.currentStreak ?? (uniqueDays.size || (activities.length > 0 ? 1 : 0)),
          bestStreak: Math.max(parsed.bestStreak ?? 0, uniqueDays.size || 0),
          lastActiveDate: parsed.lastActiveDate || today,
          totalXP: parsed.totalXP ?? calcXP,
          hasStudiedToday: parsed.hasStudiedToday ?? (hasToday || activities.length > 0),
          dbSource: parsed.dbSource || 'local',
        };
      }
    } catch { /* ignore */ }

    return {
      currentStreak: uniqueDays.size || (activities.length > 0 ? 1 : 0),
      bestStreak: Math.max(uniqueDays.size || 0, activities.length > 0 ? 1 : 0),
      lastActiveDate: today,
      totalXP: calcXP,
      hasStudiedToday: hasToday || activities.length > 0,
      dbSource: 'local',
    };
  });

  // Fetch live metrics from Database backend & subscribe to activity changes
  useEffect(() => {
    let isMounted = true;

    async function fetchStats() {
      try {
        const res = await fetch('/api/stats');
        if (res.ok) {
          const data = await res.json();
          if (isMounted && data && !data.error) {
            const updated = {
              currentStreak: Number(data.current_streak ?? 0),
              bestStreak: Number(data.best_streak ?? 0),
              lastActiveDate: today,
              totalXP: Number(data.total_xp ?? 0),
              hasStudiedToday: Boolean(data.has_studied_today),
              totalSessions: Number(data.total_sessions ?? 0),
              totalTurns: Number(data.total_turns ?? 0),
              dbSource: data.source || 'db',
            };
            setStreakState(updated);
            try {
              localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
            } catch { /* ignore */ }
            return;
          }
        }
      } catch (err) {
        console.debug('Using local activity streak calculation:', err);
      }

      // Local activity recalculation fallback
      const activities = loadActivities();
      const completedActivities = activities.filter(a => a.status === 'completed');
      const uniqueDays = new Set(activities.map(a => a.startedAt.split('T')[0]));
      const calcXP = (completedActivities.length * 50) + (activities.reduce((acc, a) => acc + (a.stepsCompleted || 0), 0) * 15);
      const isTodayActive = uniqueDays.has(today);

      if (isMounted) {
        const fallback = {
          currentStreak: uniqueDays.size > 0 ? (isTodayActive ? uniqueDays.size : 1) : (activities.length > 0 ? 1 : 0),
          bestStreak: Math.max(uniqueDays.size, activities.length > 0 ? 1 : 0),
          lastActiveDate: today,
          totalXP: calcXP,
          hasStudiedToday: isTodayActive || activities.length > 0,
          dbSource: 'local',
        };
        setStreakState(fallback);
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(fallback));
        } catch { /* ignore */ }
      }
    }

    fetchStats();

    // Listen to storage or custom activity update events
    const handleStorageChange = () => fetchStats();
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('reanmore_activity_updated', handleStorageChange);

    return () => {
      isMounted = false;
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('reanmore_activity_updated', handleStorageChange);
    };
  }, [today]);

  // Find next milestone
  const nextMilestone = STREAK_MILESTONES.find(m => m.days > streakState.currentStreak) || STREAK_MILESTONES[STREAK_MILESTONES.length - 1];
  const prevMilestoneDays = STREAK_MILESTONES.filter(m => m.days <= streakState.currentStreak).slice(-1)[0]?.days || 0;
  
  const milestoneProgress = Math.min(
    100,
    Math.round(((streakState.currentStreak - prevMilestoneDays) / (nextMilestone.days - prevMilestoneDays)) * 100)
  );

  const daysUntilNext = Math.max(0, nextMilestone.days - streakState.currentStreak);
  const NextIcon = nextMilestone.icon;

  return (
    <div className="bg-gradient-to-b from-[#1B4332] to-[#143326] rounded-2xl sm:rounded-3xl border-3 border-[#1B4332] shadow-[5px_5px_0px_#1B4332] p-4 sm:p-6 text-white relative overflow-hidden select-none">
      
      {/* Background ambient glowing fire gradients */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-[#FF6B6B]/20 via-[#FF9F1C]/15 to-transparent rounded-full blur-2xl pointer-events-none" />
      <div className="absolute -bottom-10 -left-10 w-48 h-48 bg-[#40916C]/20 rounded-full blur-2xl pointer-events-none" />

      {/* ── Main TikTok Streak Row ── */}
      <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-5">
        
        {/* Left: Giant Fire Counter */}
        <div className="flex items-center gap-4">
          
          {/* Pulsing Flame Box */}
          <div className="relative shrink-0">
            <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-b from-[#FF4D4D] via-[#FF851B] to-[#FFDC00] rounded-2xl sm:rounded-3xl border-3 border-white/90 shadow-[0_6px_0px_rgba(0,0,0,0.35),0_10px_20px_rgba(255,107,107,0.4)] flex items-center justify-center transform hover:scale-105 transition-transform">
              <Flame className="w-10 h-10 sm:w-12 sm:h-12 text-white fill-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)] animate-pulse" />
            </div>
            
            {/* Active Spark Ring */}
            <span className="absolute -inset-1 rounded-2xl sm:rounded-3xl border-2 border-[#FFD166] animate-ping opacity-30 pointer-events-none" />
          </div>

          {/* Continuous Days Text */}
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-3xl sm:text-4xl font-black font-heading tracking-tight text-white drop-shadow-[2px_2px_0px_rgba(0,0,0,0.4)] flex items-center gap-1.5">
                {streakState.currentStreak}
                <span className="text-lg sm:text-2xl text-[#FFD166] font-extrabold uppercase">
                  {isKhmer ? 'ថ្ងៃបន្តគ្នា' : 'Days Streak'}
                </span>
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#FF6B6B]/25 text-[#FFD166] text-[10px] sm:text-xs font-black border border-[#FF6B6B]/40">
                <Zap className="w-3 h-3 text-[#FFD166] fill-[#FFD166]" />
                {isKhmer ? 'កំពុងឆេះសន្ធោសន្ធៅ!' : "You're on Fire!"}
              </span>
              
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/10 text-white text-[10px] sm:text-xs font-bold border border-white/15">
                <ShieldCheck className="w-3 h-3 text-white" />
                {isKhmer ? 'បានរៀនថ្ងៃនេះ' : 'Active Today'}
              </span>
            </div>
          </div>
        </div>

        {/* Right: Quick Stats & Highscore */}
        <div className="flex items-center gap-3 self-start md:self-auto bg-black/25 px-3.5 py-2 rounded-2xl border border-white/15">
          <div className="text-left pr-3 border-r border-white/15">
            <p className="text-[10px] uppercase font-black tracking-wider text-white">
              {isKhmer ? 'កំណត់ត្រាខ្ពស់បំផុត' : 'Best Streak'}
            </p>
            <p className="text-sm sm:text-base font-black text-[#FFD166] flex items-center gap-1">
              <Trophy className="w-3.5 h-3.5 text-[#FFD166]" />
              {streakState.bestStreak} {isKhmer ? 'ថ្ងៃ' : 'Days'}
            </p>
          </div>

          <div className="text-left">
            <p className="text-[10px] uppercase font-black tracking-wider text-white">
              {isKhmer ? 'ពិន្ទុសរុប' : 'Total XP'}
            </p>
            <p className="text-sm sm:text-base font-black text-white flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-white" />
              {streakState.totalXP} XP
            </p>
          </div>
        </div>
      </div>

      {/* ── Continuous Milestone Track Bar ── */}
      <div className="mt-5 pt-4 border-t-2 border-white/15 relative z-10 space-y-2.5">
        
        {/* Milestone Header */}
        <div className="flex flex-col min-[440px]:flex-row min-[440px]:items-center justify-between gap-1 text-xs font-black">
          <span className="text-white flex items-center gap-1.5 flex-wrap">
            <Award className="w-4 h-4 text-[#FFD166] shrink-0" />
            <span>{isKhmer ? 'គោលដៅបន្ទាប់៖' : 'Next Milestone:'}</span>
            <span className="text-white font-black underline decoration-[#FFD166] inline-flex items-center gap-1">
              <NextIcon className={`w-3.5 h-3.5 ${nextMilestone.iconColor}`} /> {nextMilestone.days} {isKhmer ? 'ថ្ងៃ' : 'Days'} ({isKhmer ? nextMilestone.labelKhmer : nextMilestone.labelEng})
            </span>
          </span>
          <span className="text-[#FFD166] font-bold text-[10px] sm:text-xs shrink-0">
            {daysUntilNext > 0
              ? (isKhmer ? `នៅសល់ ${daysUntilNext} ថ្ងៃទៀត!` : `${daysUntilNext} days to unlock!`)
              : (isKhmer ? 'សម្រេចបានហើយ!' : 'Milestone Unlocked!')}
          </span>
        </div>

        {/* Milestone Continuous Progress Bar */}
        <div className="h-3 sm:h-3.5 bg-black/40 rounded-full border-2 border-white/30 overflow-hidden relative shadow-inner">
          <div
            className="h-full bg-gradient-to-r from-[#FF851B] via-[#FF4D4D] to-[#FFDC00] rounded-full transition-all duration-700 ease-out shadow-[0_0_10px_rgba(255,133,27,0.8)]"
            style={{ width: `${milestoneProgress}%` }}
          />
        </div>

        {/* Milestone Badges Strip */}
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5 sm:gap-2 pt-1.5 sm:pt-2">
          {STREAK_MILESTONES.map((milestone) => {
            const isUnlocked = streakState.currentStreak >= milestone.days;
            const isNext = nextMilestone.days === milestone.days && !isUnlocked;
            const MIcon = milestone.icon;

            return (
              <div
                key={milestone.days}
                className={`
                  flex flex-col items-center p-1.5 sm:p-2 rounded-xl sm:rounded-2xl transition-all border
                  ${isUnlocked
                    ? 'bg-gradient-to-b from-[#2D6A4F] to-[#1B4332] border-[#52B788] shadow-[0_2px_4px_rgba(0,0,0,0.3)]'
                    : isNext
                    ? 'bg-white/10 border-[#FFD166] ring-1 ring-[#FFD166]/50 animate-pulse'
                    : 'bg-black/20 border-white/10 opacity-50'
                  }
                `}
                title={`${milestone.labelEng} (${milestone.days} Days) - +${milestone.rewardXP} XP`}
              >
                <div className="h-4 sm:h-5 flex items-center justify-center">
                  <MIcon className={`w-3.5 h-3.5 sm:w-5 sm:h-5 ${isUnlocked ? milestone.iconColor : 'text-white/70'}`} />
                </div>
                <span className={`text-[9px] sm:text-[10px] font-black mt-1 leading-none ${isUnlocked ? 'text-[#FFD166]' : 'text-white/80'}`}>
                  {milestone.days}d
                </span>
                {isUnlocked && (
                  <Check className="w-2.5 h-2.5 mt-0.5 text-[#FFD166] stroke-[3]" />
                )}
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
};
