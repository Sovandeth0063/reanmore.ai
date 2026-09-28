/**
 * caseMatcher.ts
 * Matches OCR-extracted exercise text to a hardcoded case ID.
 * Priority: exact case_id match > normalized question text > OCR pattern substring.
 * Returns null if no match found (triggers Gemini fallback).
 */

import {
  ALL_HARDCODED_CASES,
  MATH_CASE_PATTERNS,
  SCIENCE_CASE_PATTERNS,
  RawHardcodedCase,
} from '../data/hardcodedCases';

/** Normalize text for fuzzy matching: lowercase, trim, collapse spaces, remove punctuation noise */
function normalize(text: string): string {
  return text
    .toLowerCase()
    .replace(/[_＿]{2,}/g, '___')    // standardize blanks
    .replace(/\[[\s]*\]/g, '[ ]')    // standardize brackets
    .replace(/\s+/g, ' ')
    .trim();
}

/** All patterns merged from both JSONs */
const ALL_PATTERNS: Record<string, string[]> = {
  ...MATH_CASE_PATTERNS.patterns,
  ...SCIENCE_CASE_PATTERNS.patterns,
};

/**
 * Match an OCR text string to a hardcoded case_id.
 * Returns the matched case_id, or null if no match.
 */
export function matchCaseId(ocrText: string): string | null {
  if (!ocrText || ocrText.trim().length < 2) return null;

  const norm = normalize(ocrText);

  // Priority 1: Direct case_id match (e.g., if OCR somehow returns the id)
  if (ALL_HARDCODED_CASES[ocrText.trim()]) return ocrText.trim();

  // Priority 2: Pattern substring matching
  for (const [caseId, patterns] of Object.entries(ALL_PATTERNS)) {
    for (const pattern of patterns) {
      const normPattern = normalize(pattern);
      if (norm.includes(normPattern) || normPattern.includes(norm)) {
        return caseId;
      }
    }
  }

  // Priority 3: Match against ocr_style_input.normalized_text in cases
  for (const [caseId, c] of Object.entries(ALL_HARDCODED_CASES)) {
    const caseNorm = normalize(c.ocr_style_input.normalized_text);
    if (norm.includes(caseNorm) || caseNorm.includes(norm)) {
      return caseId;
    }
    // Also try matching original_question
    const qNorm = normalize(c.original_question);
    if (norm.includes(qNorm) || qNorm.includes(norm)) {
      return caseId;
    }
  }

  return null;
}

/**
 * Given a HomeworkProblem (from OCR), find matching hardcoded case.
 * Tries multiple text fields in the problem.
 */
export function matchCaseFromProblem(problem: {
  id?: string;
  problemStatementEng?: string;
  titleEng?: string;
}): string | null {
  // Try problem id first (if already a hardcoded id)
  if (problem.id && ALL_HARDCODED_CASES[problem.id]) return problem.id;

  // Try problem statement
  if (problem.problemStatementEng) {
    const match = matchCaseId(problem.problemStatementEng);
    if (match) return match;
  }

  // Try title
  if (problem.titleEng) {
    const match = matchCaseId(problem.titleEng);
    if (match) return match;
  }

  return null;
}

/**
 * Get a case by ID (safe lookup).
 */
export function getCase(caseId: string): RawHardcodedCase | null {
  return ALL_HARDCODED_CASES[caseId] ?? null;
}

/**
 * Check if a given text likely belongs to a hardcoded exercise set.
 */
export function isHardcodedExercise(ocrText: string): boolean {
  return matchCaseId(ocrText) !== null;
}
