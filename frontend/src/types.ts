/**
 * Core type definitions for ReanMore AI Homework Tutor — MVP Scope
 * Must-haves: OCR, NLU, Socratic Guidance, Safety Guardrails
 */

export type Grade = 1 | 2 | 3 | 4 | 5 | 6;

export type Subject = 'math' | 'science' | 'english';

export type Language = 'km' | 'en';

export type ReanMoreState =
  | 'idle'
  | 'waving'
  | 'thinking'
  | 'listening'
  | 'explaining'
  | 'encouraging'
  | 'happy'
  | 'celebrating'
  | 'jumping'
  | 'confused'
  | 'sleeping';

export type TunsayState = ReanMoreState;

export interface StepItem {
  id: string;
  stepNumber: number;
  totalSteps: number;
  questionKhmer: string;
  questionEng: string;
  inputFormat: 'mcq' | 'number' | 'text';
  options?: string[];
  correctAnswer: string;
  hint1: {
    khmer: string;
    eng: string;
  };
  hint2: {
    khmer: string;
    eng: string;
  };
  hint3: {
    titleKhmer: string;
    titleEng: string;
    exampleKhmer: string;
    exampleEng: string;
  };
  socraticPromptKhmer: string;
  socraticPromptEng: string;
  explainDifferently: {
    simpleKhmer: string;
    simpleEng: string;
    analogyTitle: string;
    analogyKhmer: string;
    analogyEng: string;
    analogyType: 'apples' | 'pizza' | 'water' | 'plants';
  };

  // ── Socratic Stepper Widget fields (added by sovandeth_frontend) ──
  /** Step title shown in the header and roadmap */
  title?: string;
  /** Step status driven by the backend stepper state machine */
  status?: 'pending' | 'active' | 'completed' | 'skipped' | 'locked' | 'up_next' | 'in_progress';
  /** Primary mission / question text (maps from backend card schema) */
  mission?: string;
  /** Guiding clue shown in the card body (Tier 1 hint equivalent) */
  clue?: string;
  /** Friendly analogy or visual example for Tier 2 */
  helpfulExample?: string;
  /** Socratic "Your Turn" prompt shown at the bottom of the card */
  yourTurn?: string;
  /** Flat array of 3 progressive hint strings from the backend */
  hints?: [string?, string?, string?];
  /** Currently unlocked hint tier (0 = no hint shown, 1–3 = tier unlocked) */
  currentHintLevel?: number;
  /** Student's recorded answer after solving the step */
  studentAnswer?: string;
  student_answer?: string;
  /** Ground truth or normalized target answer for evaluation */
  expectedAnswer?: string;
  expected_answer?: string;
}

export interface HomeworkProblem {
  id: string;
  titleKhmer: string;
  titleEng: string;
  grade: Grade;
  subject: Subject;
  problemStatementKhmer: string;
  problemStatementEng: string;
  imageUri?: string;
  visualData?: any;
  concept?: string;
  activeStepIndex?: number;
  steps: StepItem[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'sayo' | 'system';
  textKhmer?: string | undefined;
  textEng: string;
  timestamp: string;
  problemId?: string | undefined;
  imageUri?: string | undefined;
  problem?: HomeworkProblem | undefined;
  activeStepIndex?: number | undefined;
  isSafetyRefusal?: boolean | undefined;
  stepWidget?: any;
}

export interface ChatSession {
  id: string;
  title: string;
  titleKhmer: string;
  messages: ChatMessage[];
  problem?: HomeworkProblem | undefined;
  worksheetQueue?: WorksheetQueue | undefined;
  problemStepProgress?: Record<string, {
    currentStepIndex: number;
    maxUnlockedStepIndex: number;
    completedStepIndices: number[];
  }> | undefined;
  imageUri?: string | undefined;
  isWorksheet?: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface WorksheetQueue {
  problems: HomeworkProblem[];
  activeIndex: number;
  completedIds: string[];
  worksheetTitle?: string | undefined;
}

export type UserRole = 'student' | 'parent';

export interface UserAccount {
  id: string;
  username: string;
  role: UserRole;
  pin?: string | undefined;
  profile: UserProfile;
}

export interface AuthState {
  currentUser: UserAccount | null;
  isAuthenticated: boolean;
}

export interface UserProfile {
  name: string;
  grade: Grade;
  subject: Subject;
  language: Language;
  avatarUrl?: string | undefined;
  role?: UserRole | undefined;
}

/* ── Parent Weekly Report types ── */

export type ActivityStatus = 'in_progress' | 'completed' | 'abandoned';

export interface LearningActivity {
  id: string;
  sessionId: string;
  problemId: string;
  problemTitleKhmer: string;
  problemTitleEng: string;
  subject: Subject;
  grade: Grade;
  startedAt: string;       
  completedAt?: string | undefined;    
  stepsCompleted: number;
  totalSteps: number;
  wrongAttempts: number;
  hintsUsed: number;
  explainUsed: number;
  status: ActivityStatus;
}

export interface WeeklyReportData {
  weekStart: string;       /* Monday ISO date */
  weekEnd: string;         /* Sunday ISO date */
  totalProblems: number;
  completedProblems: number;
  completionRate: number;  /* 0-100 */
  totalWrongAttempts: number;
  totalHintsUsed: number;
  totalTimeMinutes: number;
  subjectBreakdown: Record<Subject, { solved: number; attempted: number; wrongRate: number }>;
  struggleAreas: Array<{ titleKhmer: string; titleEng: string; subject: Subject; wrongRate: number; hintsNeeded: number }>;
  strongestAreas: Array<{ titleKhmer: string; titleEng: string; subject: Subject; correctRate: number }>;
  dailyBreakdown: Array<{ day: string; label: string; solved: number; attempted: number }>;
}

// ─────────────────────────────────────────────────────────────────────────────
// Unified Tutor Session types (shared by hardcoded + Gemini providers)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * A single step in a tutor session.
 * NOTE: expected_student_answer must NEVER be sent to JSX renders.
 */
export interface TutorStep {
  step: number;
  tutor_question: string;
  /** Backend-only. Validated in provider, never exposed to UI directly. */
  expected_student_answer: string;
}

export interface VisualData {
  type:
    | 'number_line'
    | 'place_value_blocks'
    | 'objects'
    | 'number_groups'
    | 'number_grouping'
    | 'base_ten_blocks'
    | 'calendar'
    | 'interactive_calendar'
    | 'calendar_blocks'
    | 'calendar_month'
    | 'year_comparison'
    | 'weekday_row'
    | 'fact_cards'
    | 'month_list'
    | 'animal_feature_card'
    | 'animal_group_card'
    | 'multiple_choice_images'
    | 'multiple_choice_multi_select'
    | 'classification_split'
    | 'producer_consumer_sort'
    | 'food_chain'
    | 'plant_diagram'
    | 'circuit'
    | 'circuit_simulator'
    | 'equation_balance'
    | 'balance_scale'
    | 'tape_diagram'
    | 'bar_model'
    | 'geometry_angle'
    | 'string';
  [key: string]: unknown;
}

/**
 * Unified tutor session. Works for both hardcoded and Gemini-sourced sessions.
 * Correct answers and expected answers are held ONLY in the provider, not here.
 */
export interface TutorSession {
  case_id: string;
  source: 'hardcoded' | 'gemini';
  subject: 'math' | 'science' | 'english';
  original_question: string;
  tutor_intro: string;
  steps: TutorStep[];
  hints: string[];
  explain_another_way: {
    message: string;
    question: string;
  };
  visual_data: VisualData | null;
  grade_adaptation: string;
  final_celebration: string;
  worksheet_image?: string;
}

export type TutorStepStatus = 'pending' | 'correct' | 'wrong' | 'skipped';

export interface TutorSessionState {
  session: TutorSession;
  currentStep: number;       // 0-indexed into session.steps
  wrongAttempts: number;     // resets per step
  hintsUsed: number;         // 0–3 across the current step
  stepStatuses: TutorStepStatus[];
  isComplete: boolean;
  showExplainAnotherWay: boolean;
}
