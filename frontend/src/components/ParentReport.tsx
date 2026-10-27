import React, { useState, useMemo } from 'react';
import { UserProfile, WeeklyReportData } from '../types';
import {
  generateWeeklyReport,
  generateReportForWeek,
  getAvailableWeeks,
  loadActivities,
} from '../utils/reportUtils';
import {
  TrendingUp,
  AlertTriangle,
  Award,
  Clock,
  CheckCircle,
  BookOpen,
  ChevronDown,
  ChevronUp,
  CalendarDays,
  Lightbulb,
  Target,
  Zap,
} from 'lucide-react';

interface ParentReportProps {
  profile: UserProfile;
}

const SUBJECT_META: Record<string, { labelKhmer: string; labelEng: string; color: string }> = {
  math:    { labelKhmer: 'គណិតវិទ្យា', labelEng: 'Math',    color: '#40916C' },
  science: { labelKhmer: 'វិទ្យាសាស្ត្រ', labelEng: 'Science', color: '#2D6A4F' },
  english: { labelKhmer: 'ភាសាអង់គ្លេស', labelEng: 'English', color: '#1B4332' },
};

export const ParentReport: React.FC<ParentReportProps> = ({ profile }) => {
  const isKhmer = profile.language === 'km';
  const [showDetail, setShowDetail] = useState(false);

  /* Week selector */
  const availableWeeks = useMemo(() => getAvailableWeeks(), []);
  const [selectedWeek, setSelectedWeek] = useState<string | 'current'>(
    availableWeeks.length > 0 ? availableWeeks[0] : 'current'
  );

  const report: WeeklyReportData = useMemo(() => {
    if (selectedWeek === 'current') return generateWeeklyReport();
    return generateReportForWeek(selectedWeek);
  }, [selectedWeek]);

  const activities = useMemo(() => loadActivities(), []);

  const hasData = report.totalProblems > 0;

  /* Format week display */
  const formatWeekLabel = (mondayStr: string) => {
    const d = new Date(mondayStr);
    const end = new Date(d);
    end.setDate(d.getDate() + 6);
    const opts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
    return `${d.toLocaleDateString(undefined, opts)} – ${end.toLocaleDateString(undefined, opts)}`;
  };

  return (
    <div className="space-y-4 sm:space-y-5 animate-fadeIn w-full">
      {/* ── Report Header ── */}
      <div className="bg-white rounded-2xl sm:rounded-3xl border-3 border-[#1B4332] shadow-[4px_4px_0px_#1B4332] p-4 sm:p-6 space-y-4">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6 text-[#40916C]" />
            <h3 className="text-base sm:text-lg font-black text-[#1B4332] font-heading">
              {isKhmer ? 'របាយការណ៍ប្រចាំសប្តាហ៍' : 'Weekly Parent Report'}
            </h3>
          </div>

          {availableWeeks.length > 0 && (
            <select
              value={selectedWeek}
              onChange={(e) => setSelectedWeek(e.target.value)}
              className="px-3 py-1.5 bg-[#E8F5E9] border-2 border-[#1B4332] rounded-xl text-xs sm:text-sm font-black text-[#1B4332] focus:outline-none cursor-pointer shadow-[2px_2px_0px_#1B4332]"
            >
              <option value="current">{isKhmer ? 'សប្តាហ៍នេះ' : 'This Week'}</option>
              {availableWeeks.map((w) => (
                <option key={w} value={w}>{formatWeekLabel(w)}</option>
              ))}
            </select>
          )}
        </div>

        {/* Date range */}
        <p className="text-xs sm:text-sm font-bold text-[#1B4332]/60 flex items-center gap-1.5">
          <CalendarDays className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          <span>
            {formatWeekLabel(report.weekStart)}
          </span>
        </p>

        {!hasData ? (
          <div className="p-4 sm:p-6 bg-[#E8F5E9] rounded-xl border-2 border-[#A7CDB4] text-center">
            <BookOpen className="w-8 h-8 sm:w-10 sm:h-10 text-[#40916C] mx-auto mb-2" />
            <p className="text-sm sm:text-base font-black text-[#1B4332]/60">
              {isKhmer
                ? 'មិនទាន់មានទិន្នន័យសម្រាប់សប្តាហ៍នេះទេ។ កូនអ្នកនឹងចាប់ផ្តើមលេងលំហាត់ឆាប់ៗនេះ!'
                : 'No data for this week yet. Your child will start solving homework soon!'}
            </p>
          </div>
        ) : (
          <>
            {/* Summary stat cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3">
              <StatCard
                icon={<CheckCircle className="w-4 h-4 sm:w-5 sm:h-5 text-white" />}
                label={isKhmer ? 'បានបញ្ចប់' : 'Completed'}
                value={`${report.completedProblems}`}
                sub={`/ ${report.totalProblems}`}
                bg="bg-[#40916C]"
              />
              <StatCard
                icon={<Target className="w-4 h-4 sm:w-5 sm:h-5 text-white" />}
                label={isKhmer ? 'អត្រាបញ្ចប់' : 'Completion'}
                value={`${report.completionRate}%`}
                bg="bg-[#2D6A4F]"
              />
              <StatCard
                icon={<Clock className="w-4 h-4 sm:w-5 sm:h-5 text-white" />}
                label={isKhmer ? 'ពេលវេលា' : 'Time'}
                value={`${report.totalTimeMinutes}`}
                sub={isKhmer ? 'នាទី' : 'min'}
                bg="bg-[#1B4332]"
              />
              <StatCard
                icon={<Lightbulb className="w-4 h-4 sm:w-5 sm:h-5 text-white" />}
                label={isKhmer ? 'តម្រុយបានប្រើ' : 'Hints Used'}
                value={`${report.totalHintsUsed}`}
                bg="bg-[#52B788]"
              />
            </div>

            {/* Subject Breakdown */}
            <div className="space-y-2.5">
              <h4 className="text-xs sm:text-sm font-black text-[#1B4332] uppercase tracking-wider flex items-center gap-1.5">
                <BookOpen className="w-4 h-4 sm:w-5 sm:h-5" />
                {isKhmer ? 'លទ្ធផលតាមមុខវិជ្ជា' : 'Subject Breakdown'}
              </h4>
              <div className="space-y-2">
                {(Object.entries(report.subjectBreakdown) as [string, { solved: number; attempted: number; wrongRate: number }][])
                  .filter(([_, v]) => v.attempted > 0)
                  .map(([subject, data]) => {
                    const meta = SUBJECT_META[subject];
                    const pct = data.attempted > 0
                      ? Math.round((data.solved / data.attempted) * 100)
                      : 0;
                    return (
                      <div key={subject} className="bg-[#E8F5E9] rounded-xl p-2.5 sm:p-3 border-2 border-[#1B4332]/15">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs sm:text-sm font-black text-[#1B4332]">
                            {isKhmer ? meta.labelKhmer : meta.labelEng}
                          </span>
                          <span className="text-[10px] sm:text-xs font-black text-[#1B4332]/70">
                            {data.solved} / {data.attempted} {isKhmer ? 'បានបញ្ចប់' : 'done'}
                          </span>
                        </div>
                        <div className="h-2.5 sm:h-3 bg-white rounded-full border border-[#1B4332]/20 overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-700"
                            style={{
                              width: `${pct}%`,
                              backgroundColor: meta.color,
                            }}
                          />
                        </div>
                        {data.wrongRate > 0 && (
                          <p className="text-[9px] sm:text-[10px] font-bold text-[#1B4332]/50 mt-1">
                            {isKhmer ? `ចម្លើយខុស៖ ${data.wrongRate}%` : `Wrong answers: ${data.wrongRate}%`}
                          </p>
                        )}
                      </div>
                    );
                  })}
              </div>
            </div>

            {/* Daily Activity Strip */}
            <div className="space-y-2.5">
              <h4 className="text-xs sm:text-sm font-black text-[#1B4332] uppercase tracking-wider flex items-center gap-1.5">
                <CalendarDays className="w-4 h-4 sm:w-5 sm:h-5" />
                {isKhmer ? 'សកម្មភាពប្រចាំថ្ងៃ' : 'Daily Activity'}
              </h4>
              <div className="grid grid-cols-7 gap-1.5 sm:gap-2">
                {report.dailyBreakdown.map((d: { day: string; label: string; solved: number; attempted: number }) => {
                  const isActive = d.attempted > 0;
                  const isComplete = d.solved > 0 && d.solved >= d.attempted;
                  return (
                    <div
                      key={d.day}
                      className={`
                        flex flex-col items-center gap-1 p-1.5 sm:p-2 rounded-xl border-2 transition-all
                        ${isComplete
                          ? 'bg-[#40916C] border-[#1B4332] text-white shadow-[2px_2px_0px_#1B4332]'
                          : isActive
                            ? 'bg-[#ffd768] border-[#1B4332] text-[#1B4332] shadow-[2px_2px_0px_#1B4332]'
                            : 'bg-white border-[#A7CDB4]/40 text-[#1B4332]/40'
                        }
                      `}
                    >
                      <span className="text-[9px] sm:text-[10px] font-black opacity-80">
                        {isKhmer ? d.label : d.day}
                      </span>
                      <div className="w-5 h-5 sm:w-6 sm:h-6 flex items-center justify-center">
                        {isComplete ? (
                          <CheckCircle className="w-4 h-4 sm:w-5 sm:h-5" />
                        ) : isActive ? (
                          <Zap className="w-4 h-4 sm:w-5 sm:h-5" />
                        ) : (
                          <span className="text-xs">–</span>
                        )}
                      </div>
                      <span className="text-[8px] sm:text-[9px] font-black">
                        {isActive ? `${d.solved}/${d.attempted}` : ''}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Struggle Areas */}
            {report.struggleAreas.length > 0 && (
              <div className="bg-[#fff8e1] rounded-2xl p-3 sm:p-4 border-2 border-[#ffd768] shadow-[3px_3px_0px_#1B4332]">
                <div className="flex items-center gap-2 mb-2.5">
                  <div className="w-8 h-8 sm:w-9 sm:h-9 bg-[#ffd768] rounded-full border-2 border-[#1B4332] flex items-center justify-center shrink-0">
                    <AlertTriangle className="w-4 h-4 sm:w-5 sm:h-5 text-[#1B4332]" />
                  </div>
                  <h4 className="text-sm sm:text-base font-black text-[#1B4332] font-heading">
                    {isKhmer ? 'ត្រូវហ្វឹកហាត់បន្ថែម' : 'Needs More Practice'}
                  </h4>
                </div>
                <div className="space-y-1.5">
                  {report.struggleAreas.map((area: WeeklyReportData['struggleAreas'][number], i: number) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-2 sm:p-2.5 bg-white rounded-xl border-2 border-[#1B4332]/15"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-xs sm:text-sm font-black text-[#1B4332] truncate">
                          {isKhmer ? area.titleKhmer : area.titleEng}
                        </p>
                        <p className="text-[9px] sm:text-[10px] font-bold text-[#1B4332]/50">
                          {isKhmer
                            ? `${SUBJECT_META[area.subject].labelKhmer} · ចម្លើយខុស ${area.wrongRate}%`
                            : `${SUBJECT_META[area.subject].labelEng} · ${area.wrongRate}% wrong`}
                        </p>
                      </div>
                      {area.hintsNeeded > 0 && (
                        <span className="shrink-0 ml-2 px-2 py-0.5 bg-[#ffd768] text-[#1B4332] rounded-full text-[9px] sm:text-[10px] font-black border border-[#1B4332]">
                          {area.hintsNeeded} {isKhmer ? 'តម្រុយ' : 'hints'}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Strongest Areas */}
            {report.strongestAreas.length > 0 && (
              <div className="bg-[#E8F5E9] rounded-2xl p-3 sm:p-4 border-2 border-[#40916C] shadow-[3px_3px_0px_#1B4332]">
                <div className="flex items-center gap-2 mb-2.5">
                  <div className="w-8 h-8 sm:w-9 sm:h-9 bg-[#40916C] rounded-full border-2 border-[#1B4332] flex items-center justify-center shrink-0">
                    <Award className="w-4 h-4 sm:w-5 sm:h-5 text-white" />
                  </div>
                  <h4 className="text-sm sm:text-base font-black text-[#1B4332] font-heading">
                    {isKhmer ? 'ធ្វើបានល្អ!' : 'Doing Great!'}
                  </h4>
                </div>
                <div className="space-y-1.5">
                  {report.strongestAreas.map((area: WeeklyReportData['strongestAreas'][number], i: number) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-2 sm:p-2.5 bg-white rounded-xl border-2 border-[#1B4332]/15"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-xs sm:text-sm font-black text-[#1B4332] truncate">
                          {isKhmer ? area.titleKhmer : area.titleEng}
                        </p>
                        <p className="text-[9px] sm:text-[10px] font-bold text-[#1B4332]/50">
                          {isKhmer
                            ? `${SUBJECT_META[area.subject].labelKhmer} · ត្រឹមត្រូវ ${area.correctRate}%`
                            : `${SUBJECT_META[area.subject].labelEng} · ${area.correctRate}% correct`}
                        </p>
                      </div>
                      <span className="shrink-0 ml-2 px-2 py-0.5 bg-[#40916C] text-white rounded-full text-[9px] sm:text-[10px] font-black border border-[#1B4332]">
                        {area.correctRate}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Detail Toggle */}
            <button
              type="button"
              onClick={() => setShowDetail(!showDetail)}
              className="w-full py-2.5 bg-[#A7CDB4] hover:bg-[#40916C] text-[#1B4332] hover:text-white text-xs sm:text-sm font-black rounded-xl border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] transition-all cursor-pointer flex items-center justify-center gap-2"
            >
              {showDetail ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  <span>{isKhmer ? 'លាក់លម្អិត' : 'Hide Details'}</span>
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  <span>{isKhmer ? 'មើលលម្អិតបន្ថែម' : 'View Full Details'}</span>
                </>
              )}
            </button>

            {/* Detail Table */}
            {showDetail && (
              <div className="overflow-x-auto rounded-2xl border-2 border-[#1B4332] shadow-[3px_3px_0px_#1B4332]">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-[#A7CDB4] text-[#1B4332]">
                      <th className="px-3 py-2 text-[10px] sm:text-xs font-black border-b-2 border-[#1B4332]">{isKhmer ? 'លំហាត់' : 'Problem'}</th>
                      <th className="px-3 py-2 text-[10px] sm:text-xs font-black border-b-2 border-[#1B4332] text-center">{isKhmer ? 'មុខវិជ្ជា' : 'Subject'}</th>
                      <th className="px-3 py-2 text-[10px] sm:text-xs font-black border-b-2 border-[#1B4332] text-center">{isKhmer ? 'ជំហាន' : 'Steps'}</th>
                      <th className="px-3 py-2 text-[10px] sm:text-xs font-black border-b-2 border-[#1B4332] text-center">{isKhmer ? 'ខុស' : 'Wrong'}</th>
                      <th className="px-3 py-2 text-[10px] sm:text-xs font-black border-b-2 border-[#1B4332] text-center">{isKhmer ? 'តម្រុយ' : 'Hints'}</th>
                      <th className="px-3 py-2 text-[10px] sm:text-xs font-black border-b-2 border-[#1B4332] text-center">{isKhmer ? 'ស្ថានភាព' : 'Status'}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activities
                      .filter(a => {
                        const d = a.startedAt.split('T')[0];
                        return d >= report.weekStart && d <= report.weekEnd;
                      })
                      .map((a) => (
                        <tr key={a.id} className="bg-white hover:bg-[#E8F5E9] transition-colors">
                          <td className="px-3 py-2 text-[10px] sm:text-xs font-bold text-[#1B4332] border-b border-[#A7CDB4]/30 max-w-[140px] truncate">
                            {isKhmer ? a.problemTitleKhmer : a.problemTitleEng}
                          </td>
                          <td className="px-3 py-2 text-[10px] sm:text-xs font-bold text-center border-b border-[#A7CDB4]/30">
                            {isKhmer ? SUBJECT_META[a.subject].labelKhmer : SUBJECT_META[a.subject].labelEng}
                          </td>
                          <td className="px-3 py-2 text-[10px] sm:text-xs font-bold text-center border-b border-[#A7CDB4]/30">
                            {a.stepsCompleted}/{a.totalSteps}
                          </td>
                          <td className="px-3 py-2 text-[10px] sm:text-xs font-bold text-center border-b border-[#A7CDB4]/30">
                            {a.wrongAttempts}
                          </td>
                          <td className="px-3 py-2 text-[10px] sm:text-xs font-bold text-center border-b border-[#A7CDB4]/30">
                            {a.hintsUsed}
                          </td>
                          <td className="px-3 py-2 text-[10px] sm:text-xs font-black text-center border-b border-[#A7CDB4]/30">
                            <span
                              className={`
                                inline-block px-2 py-0.5 rounded-full text-[9px] sm:text-[10px] border
                                ${a.status === 'completed'
                                  ? 'bg-[#40916C] text-white border-[#1B4332]'
                                  : a.status === 'in_progress'
                                    ? 'bg-[#ffd768] text-[#1B4332] border-[#1B4332]'
                                    : 'bg-gray-200 text-gray-600 border-gray-400'
                                }
                              `}
                            >
                              {a.status === 'completed'
                                ? (isKhmer ? 'បានបញ្ចប់' : 'Done')
                                : a.status === 'in_progress'
                                  ? (isKhmer ? 'កំពុងធ្វើ' : 'In Progress')
                                  : (isKhmer ? 'មិនបានបន្ត' : 'Abandoned')}
                            </span>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

/* ── Sub-component: Stat Card ── */

function StatCard({
  icon,
  label,
  value,
  sub,
  bg,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  bg: string;
}) {
  return (
    <div className={`${bg} rounded-xl p-2.5 sm:p-3 border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] text-white flex flex-col items-center gap-1`}>
      <div className="flex items-center gap-1.5">
        {icon}
        <span className="text-[9px] sm:text-[10px] font-black opacity-90 leading-none">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-lg sm:text-xl font-black leading-none">{value}</span>
        {sub && (
          <span className="text-[9px] sm:text-xs font-bold opacity-75">{sub}</span>
        )}
      </div>
    </div>
  );
}
