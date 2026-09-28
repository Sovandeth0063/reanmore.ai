/**
 * Typed loader for hardcoded Math and Science tutor cases.
 * Imports both JSONs and exports a unified lookup map.
 * SECURITY: correct_answer and expected_student_answer are typed here
 * but must NEVER be passed directly to JSX renders.
 */

import mathData from './math.json';
import scienceData from './science.json';

// ─── Raw JSON shape types ───────────────────────────────────────────────────

export interface RawStep {
  step: number;
  tutor_question: string;
  expected_student_answer: string;
}

export interface RawVisualData {
  type: string;
  [key: string]: unknown;
}

export interface RawHardcodedCase {
  case_id: string;
  subject: 'math' | 'science';
  grade_level: string;
  difficulty: 'easy' | 'medium' | 'hard';
  original_question: string;
  question_type: string;
  correct_answer: string | Record<string, unknown>;
  concept: string;
  ocr_style_input: {
    raw_text: string;
    normalized_text: string;
    confidence?: number;
  };
  tutor_intro: string;
  steps: RawStep[];
  hints: string[];
  explain_another_way: {
    message: string;
    question: string;
  };
  visual_data: RawVisualData;
  grade_adaptations: Record<string, string>;
  final_celebration: string;
}

export interface WorksheetQueueMeta {
  page: number;
  label?: string;
  title?: string;
  homework?: string;
  exercise_ids: string[];
  exercise_count?: number;
}

export interface CaseMatchingData {
  priority: string[];
  never_match_using_answer: boolean;
  patterns: Record<string, string[]>;
}

// ─── Merged data ────────────────────────────────────────────────────────────

/** All hardcoded cases from both math.json and science.json, keyed by case_id */
export const ALL_HARDCODED_CASES: Record<string, RawHardcodedCase> = {
  ...(mathData.cases as unknown as Record<string, RawHardcodedCase>),
  ...(scienceData.cases as unknown as Record<string, RawHardcodedCase>),
};

/** All worksheet queues from math.json */
export const MATH_QUEUES: Record<string, WorksheetQueueMeta> = mathData.worksheet_queues as unknown as Record<string, WorksheetQueueMeta>;

/** All worksheet queues from science.json */
export const SCIENCE_QUEUES: Record<string, WorksheetQueueMeta> = scienceData.worksheet_queues as unknown as Record<string, WorksheetQueueMeta>;

/** Combined matching patterns from both JSONs */
export const MATH_CASE_PATTERNS: CaseMatchingData = mathData.case_matching as unknown as CaseMatchingData;
export const SCIENCE_CASE_PATTERNS: CaseMatchingData = scienceData.case_matching as unknown as CaseMatchingData;

/** Worksheet image map: queue key → public image path */
export const WORKSHEET_IMAGES: Record<string, string> = {
  page_1_homework_1:           '/worksheets/Screenshot 2026-09-24 195728.png',
  page_8_homework_8:           '/worksheets/Screenshot 2026-09-24 200057.png',
  page_16_homework_16:         '/worksheets/Screenshot 2026-09-24 200149.png',
  page_8_identifying_animals:  '/worksheets/Screenshot 2026-09-24 200600.png',
  page_6_grouping_animals:     '/worksheets/Screenshot 2026-09-24 201646.png',
  page_44_producers_consumers:  '/worksheets/Screenshot 2026-09-24 201805.png',
};

/** Map a case_id to its worksheet image path */
export function getWorksheetImageForCase(caseId: string): string | undefined {
  for (const [queueKey, queue] of Object.entries({ ...MATH_QUEUES, ...SCIENCE_QUEUES })) {
    if (queue.exercise_ids.includes(caseId)) {
      return WORKSHEET_IMAGES[queueKey];
    }
  }
  return undefined;
}

/** Get the queue that contains a given case_id */
export function getQueueForCase(caseId: string): WorksheetQueueMeta | undefined {
  for (const queue of Object.values({ ...MATH_QUEUES, ...SCIENCE_QUEUES })) {
    if (queue.exercise_ids.includes(caseId)) return queue;
  }
  return undefined;
}

/** All exercise IDs that are hardcoded (for quick lookup) */
export const ALL_HARDCODED_IDS = new Set(Object.keys(ALL_HARDCODED_CASES));
