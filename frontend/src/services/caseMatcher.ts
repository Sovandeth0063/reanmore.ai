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

  // If text is very short (< 6 chars), only allow exact match against caseId or full patterns
  const isShort = norm.length < 6;

  // Priority 2: Pattern matching
  for (const [caseId, patterns] of Object.entries(ALL_PATTERNS)) {
    for (const pattern of patterns) {
      const normPattern = normalize(pattern);
      if (norm === normPattern) {
        return caseId;
      }
      if (!isShort) {
        // OCR text contains the full known pattern
        if (normPattern.length >= 10 && norm.includes(normPattern)) {
          return caseId;
        }
        // Known pattern contains OCR text, but only if OCR text is long enough and covers a significant portion
        if (norm.length >= 16 && normPattern.length >= 16 && normPattern.includes(norm) && norm.length >= normPattern.length * 0.7) {
          return caseId;
        }
      }
    }
  }

  // Priority 3: Match against ocr_style_input.normalized_text and original_question
  if (!isShort) {
    for (const [caseId, c] of Object.entries(ALL_HARDCODED_CASES)) {
      const caseNorm = normalize(c.ocr_style_input.normalized_text);
      if (norm === caseNorm) {
        return caseId;
      }
      if (caseNorm.length >= 15 && norm.includes(caseNorm)) {
        return caseId;
      }
      if (norm.length >= 20 && caseNorm.length >= 20 && caseNorm.includes(norm) && norm.length >= caseNorm.length * 0.75) {
        return caseId;
      }

      // Also try matching original_question
      const qNorm = normalize(c.original_question);
      if (norm === qNorm) {
        return caseId;
      }
      if (qNorm.length >= 15 && norm.includes(qNorm)) {
        return caseId;
      }
      if (norm.length >= 20 && qNorm.length >= 20 && qNorm.includes(norm) && norm.length >= qNorm.length * 0.75) {
        return caseId;
      }
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
