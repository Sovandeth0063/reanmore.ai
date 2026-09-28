import { LearningActivity, WeeklyReportData, Subject, ActivityStatus, Grade } from '../types';

const STORAGE_KEY = 'reanmore_activity_v1';

/* ── Storage Helpers ── */

export function loadActivities(): LearningActivity[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as LearningActivity[];
      if (Array.isArray(parsed)) return parsed;
    }
  } catch { /* ignore corrupt storage */ }
  return [];
}

export function saveActivities(activities: LearningActivity[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(activities));
  } catch { /* ignore quota errors */ }
}

export function createActivity(
  sessionId: string,
  problemId: string,
  titleKhmer: string,
  titleEng: string,
  subject: Subject,
  grade: Grade,
  totalSteps: number
): LearningActivity {
  const activity: LearningActivity = {
    id: `${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
    sessionId,
    problemId,
    problemTitleKhmer: titleKhmer,
    problemTitleEng: titleEng,
    subject,
    grade,
    startedAt: new Date().toISOString(),
    stepsCompleted: 0,
    totalSteps,
    wrongAttempts: 0,
    hintsUsed: 0,
    explainUsed: 0,
    status: 'in_progress',
  };
  const existing = loadActivities();
  saveActivities([activity, ...existing]);
  return activity;
}

export function updateActivity(activityId: string, patch: Partial<Omit<LearningActivity, 'id'>>) {
  const existing = loadActivities();
  const updated = existing.map(a => {
    if (a.id !== activityId) return a;
    const next = { ...a, ...patch };
    /* Auto-set completedAt when status flips to completed */
    if (patch.status === 'completed' && a.status !== 'completed') {
      next.completedAt = new Date().toISOString();
    }
    return next;
  });
  saveActivities(updated);
}

export function findActiveActivity(sessionId: string): LearningActivity | undefined {
  return loadActivities().find(a => a.sessionId === sessionId && a.status === 'in_progress');
}

export function markSessionAbandoned(sessionId: string) {
  const existing = loadActivities();
  const updated = existing.map(a => {
    if (a.sessionId === sessionId && a.status === 'in_progress') {
      return { ...a, status: 'abandoned' as ActivityStatus };
    }
    return a;
  });
  saveActivities(updated);
}

/* ── Report Generator ── */

function getWeekBounds(date = new Date()) {
  const d = new Date(date);
  const day = d.getDay(); /* 0=Sun, 1=Mon ... */
  const diffToMonday = day === 0 ? -6 : 1 - day;
  const monday = new Date(d);
  monday.setDate(d.getDate() + diffToMonday);
  monday.setHours(0, 0, 0, 0);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  sunday.setHours(23, 59, 59, 999);
  return {
    monday: monday.toISOString().split('T')[0],
    sunday: sunday.toISOString().split('T')[0],
    mondayDate: monday,
    sundayDate: sunday,
  };
}

function isInWeek(dateStr: string, weekStart: string, weekEnd: string) {
  const d = dateStr.split('T')[0];
  return d >= weekStart && d <= weekEnd;
}

export function generateWeeklyReport(
  activities: LearningActivity[] = loadActivities()
): WeeklyReportData {
  const { monday, sunday, mondayDate } = getWeekBounds();

  const weekActivities = activities.filter(a =>
    isInWeek(a.startedAt, monday, sunday)
  );

  const totalProblems = weekActivities.length;
  const completedProblems = weekActivities.filter(a => a.status === 'completed').length;
  const completionRate = totalProblems > 0 ? Math.round((completedProblems / totalProblems) * 100) : 0;

  const totalWrongAttempts = weekActivities.reduce((s, a) => s + a.wrongAttempts, 0);
  const totalHintsUsed = weekActivities.reduce((s, a) => s + a.hintsUsed, 0);

  /* Estimate time: ~3 min per step attempted */
  const totalTimeMinutes = weekActivities.reduce(
    (s, a) => s + (a.stepsCompleted + a.wrongAttempts) * 3,
    0
  );

  /* Subject breakdown */
  const subjects: Subject[] = ['math', 'science', 'english'];
  const subjectBreakdown: WeeklyReportData['subjectBreakdown'] = {
    math: { solved: 0, attempted: 0, wrongRate: 0 },
    science: { solved: 0, attempted: 0, wrongRate: 0 },
    english: { solved: 0, attempted: 0, wrongRate: 0 },
  };

  for (const sub of subjects) {
    const subActs = weekActivities.filter(a => a.subject === sub);
    const attempted = subActs.length;
    const solved = subActs.filter(a => a.status === 'completed').length;
    const totalWrong = subActs.reduce((s, a) => s + a.wrongAttempts, 0);
    const totalStepsDone = subActs.reduce((s, a) => s + a.stepsCompleted + a.wrongAttempts, 0);
    const wrongRate = totalStepsDone > 0 ? Math.round((totalWrong / totalStepsDone) * 100) : 0;
    subjectBreakdown[sub] = { solved, attempted, wrongRate };
  }

  /* Struggle areas: wrongRate > 40% OR hintsUsed >= 2 */
  const struggleAreas = weekActivities
    .filter(a => {
      const totalAttempts = a.stepsCompleted + a.wrongAttempts;
      const wrongRate = totalAttempts > 0 ? (a.wrongAttempts / totalAttempts) * 100 : 0;
      return wrongRate > 40 || a.hintsUsed >= 2;
    })
    .map(a => {
      const totalAttempts = a.stepsCompleted + a.wrongAttempts;
      const wrongRate = totalAttempts > 0 ? Math.round((a.wrongAttempts / totalAttempts) * 100) : 0;
      return {
        titleKhmer: a.problemTitleKhmer,
        titleEng: a.problemTitleEng,
        subject: a.subject,
        wrongRate,
        hintsNeeded: a.hintsUsed,
      };
    })
    .sort((a, b) => b.wrongRate - a.wrongRate)
    .slice(0, 5);

  /* Strongest areas: completed with wrongRate <= 20% */
  const strongestAreas = weekActivities
    .filter(a => a.status === 'completed')
    .filter(a => {
      const totalAttempts = a.stepsCompleted + a.wrongAttempts;
      const wrongRate = totalAttempts > 0 ? (a.wrongAttempts / totalAttempts) * 100 : 0;
      return wrongRate <= 20;
    })
    .map(a => {
      const totalAttempts = a.stepsCompleted + a.wrongAttempts;
      const wrongRate = totalAttempts > 0 ? Math.round((a.wrongAttempts / totalAttempts) * 100) : 0;
      return {
        titleKhmer: a.problemTitleKhmer,
        titleEng: a.problemTitleEng,
        subject: a.subject,
        correctRate: 100 - wrongRate,
      };
    })
    .sort((a, b) => b.correctRate - a.correctRate)
    .slice(0, 5);

  /* Daily breakdown (Mon-Sun) */
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const dayLabelsKhmer = ['ច', 'អ', 'ព', 'ព្រ', 'ស', 'សៅ', 'អា'];
  const dailyBreakdown: WeeklyReportData['dailyBreakdown'] = [];

  for (let i = 0; i < 7; i++) {
    const d = new Date(mondayDate);
    d.setDate(mondayDate.getDate() + i);
    const dateStr = d.toISOString().split('T')[0];
    const dayActs = weekActivities.filter(a => a.startedAt.split('T')[0] === dateStr);
    const solved = dayActs.filter(a => a.status === 'completed').length;
    const attempted = dayActs.length;
    dailyBreakdown.push({
      day: days[i],
      label: dayLabelsKhmer[i],
      solved,
      attempted,
    });
  }

  return {
    weekStart: monday,
    weekEnd: sunday,
    totalProblems,
    completedProblems,
    completionRate,
    totalWrongAttempts,
    totalHintsUsed,
    totalTimeMinutes,
    subjectBreakdown,
    struggleAreas,
    strongestAreas,
    dailyBreakdown,
  };
}

/* ── Historical weeks list ── */
export function getAvailableWeeks(activities: LearningActivity[] = loadActivities()): string[] {
  const weeks = new Set<string>();
  for (const a of activities) {
    const { monday } = getWeekBounds(new Date(a.startedAt));
    weeks.add(monday);
  }
  return Array.from(weeks).sort().reverse();
}

export function generateReportForWeek(mondayStr: string): WeeklyReportData {
  const monday = new Date(mondayStr);
  const { sunday } = getWeekBounds(monday);
  const all = loadActivities().filter(a => {
    const d = a.startedAt.split('T')[0];
    return d >= mondayStr && d <= sunday;
  });
  return generateWeeklyReport(all);
}
