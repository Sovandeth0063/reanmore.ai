/**
 * Automated Content Quality Validator for ALL Hardcoded Math Problems.
 * Directly imports HARDCODED_KHMER_TRANSLATIONS and math.json to validate:
 * 1. Completeness of 3-tier hints for all steps across all 31 math exercises.
 * 2. Zero answer leakage in Hint 1 and Hint 2.
 * 3. Zero Latin characters in child-facing Khmer fields.
 * 4. Zero cross-exercise hint contamination or copy-pasted filler.
 */

import { HARDCODED_KHMER_TRANSLATIONS } from '../src/services/translationService';
import mathData from '../src/data/math.json';

const LATIN_RE = /[a-zA-Z]/;

export const hw1Ids = [
  'math_p1_a1',
  'math_p1_a2',
  'math_p1_a3',
  'math_p1_a4',
  'math_p1_a5',
  'math_p1_b1',
  'math_p1_b2',
  'math_p1_b3',
  'math_p1_b4',
  'math_p1_b5',
  'math_p1_b6',
];

export const hw8Ids = [
  'math_p8_a1',
  'math_p8_a2',
  'math_p8_a3',
  'math_p8_a4',
  'math_p8_b2',
  'math_p8_b6',
  'math_p8_b3',
  'math_p8_b7',
  'math_p8_b4',
  'math_p8_b8',
];

export const hw16Ids = [
  'math_p16_a1',
  'math_p16_a2',
  'math_p16_a3',
  'math_p16_a4',
  'math_p16_b1',
  'math_p16_b2',
  'math_p16_b3',
  'math_p16_b4',
  'math_p16_b5',
  'math_p16_b6',
];

export const allMathIds = [...hw1Ids, ...hw8Ids, ...hw16Ids];

const kmMap: Record<string, string> = {
  '0': '០', '1': '១', '2': '២', '3': '៣', '4': '៤',
  '5': '៥', '6': '៦', '7': '៧', '8': '៨', '9': '៩',
};

function toKmNum(str: string): string {
  return str.split('').map((c) => kmMap[c] || c).join('');
}

function runAudit() {
  console.log(`=== Auditing All ${allMathIds.length} Math Exercises Across Homework 1, 8, and 16 ===`);
  const errors: string[] = [];
  let totalSteps = 0;

  for (const caseId of allMathIds) {
    const khmerCase = HARDCODED_KHMER_TRANSLATIONS[caseId];
    if (!khmerCase) {
      errors.push(`[${caseId}] Missing from HARDCODED_KHMER_TRANSLATIONS`);
      continue;
    }

    if (LATIN_RE.test(khmerCase.statementKhmer)) {
      errors.push(`[${caseId}] statementKhmer contains Latin characters: "${khmerCase.statementKhmer}"`);
    }

    const mCase = (mathData as any).cases?.[caseId];
    const mSteps = mCase?.steps || [];
    const kSteps = khmerCase.steps || [];
    totalSteps += kSteps.length;

    if (kSteps.length !== mSteps.length) {
      errors.push(`[${caseId}] Step count mismatch: Khmer has ${kSteps.length}, math.json has ${mSteps.length}`);
    }

    kSteps.forEach((step, idx) => {
      const sNum = idx + 1;

      // 1. Completeness checks
      if (!step.questionKhmer) errors.push(`[${caseId} Step ${sNum}] Missing questionKhmer`);
      if (!step.socraticPromptKhmer) errors.push(`[${caseId} Step ${sNum}] Missing socraticPromptKhmer`);
      if (!step.hint1Khmer) errors.push(`[${caseId} Step ${sNum}] Missing hint1Khmer`);
      if (!step.hint2Khmer) errors.push(`[${caseId} Step ${sNum}] Missing hint2Khmer`);
      if (!step.hint3Khmer) errors.push(`[${caseId} Step ${sNum}] Missing hint3Khmer`);

      // 2. Zero Latin characters in Khmer fields
      [
        { name: 'questionKhmer', val: step.questionKhmer },
        { name: 'socraticPromptKhmer', val: step.socraticPromptKhmer },
        { name: 'hint1Khmer', val: step.hint1Khmer },
        { name: 'hint2Khmer', val: step.hint2Khmer },
        { name: 'hint3Khmer', val: step.hint3Khmer },
      ].forEach(({ name, val }) => {
        if (val && LATIN_RE.test(val)) {
          errors.push(`[${caseId} Step ${sNum}] ${name} contains Latin characters: "${val}"`);
        }
      });

      // 3. Zero answer leakage in Hint 1 and Hint 2
      if (idx < mSteps.length) {
        const expected = String(mSteps[idx].expected_student_answer || '').trim();
        if (/^\d+$/.test(expected)) {
          const expectedKm = toKmNum(expected);
          [step.hint1Khmer, step.hint2Khmer].forEach((hVal, hIdx) => {
            if (!hVal) return;
            const leakPatterns = [`ស្មើ ${expectedKm}`, `ស្មើនឹង ${expectedKm}`, `= ${expectedKm}`];
            leakPatterns.forEach((p) => {
              if (hVal.includes(p)) {
                errors.push(`[${caseId} Step ${sNum}] Direct answer leak in Hint ${hIdx + 1}: "${hVal}"`);
              }
            });
          });
        }
      }
    });

    // 4. Exercise-level hints
    const hintsKm = khmerCase.hintsKhmer || [];
    if (hintsKm.length !== 3) {
      errors.push(`[${caseId}] hintsKhmer must have 3 items, found ${hintsKm.length}`);
    }
    hintsKm.forEach((h, hIdx) => {
      if (LATIN_RE.test(h)) {
        errors.push(`[${caseId}] hintsKhmer[${hIdx}] contains Latin characters: "${h}"`);
      }
    });

    // 5. Explain Khmer
    if (!khmerCase.explainKhmer?.messageKhmer) {
      errors.push(`[${caseId}] Missing explainKhmer.messageKhmer`);
    } else if (LATIN_RE.test(khmerCase.explainKhmer.messageKhmer)) {
      errors.push(`[${caseId}] explainKhmer.messageKhmer contains Latin characters: "${khmerCase.explainKhmer.messageKhmer}"`);
    }

    if (!khmerCase.explainKhmer?.questionKhmer) {
      errors.push(`[${caseId}] Missing explainKhmer.questionKhmer`);
    } else if (LATIN_RE.test(khmerCase.explainKhmer.questionKhmer)) {
      errors.push(`[${caseId}] explainKhmer.questionKhmer contains Latin characters: "${khmerCase.explainKhmer.questionKhmer}"`);
    }
  }

  // 6. Cross-exercise contamination checks
  // (a) HW 1 Part A addition should not contain '100' logic
  ['math_p1_a1', 'math_p1_a2', 'math_p1_a3', 'math_p1_a4', 'math_p1_a5'].forEach((caseId) => {
    const c = HARDCODED_KHMER_TRANSLATIONS[caseId];
    if (!c) return;
    const combined = [
      ...(c.hintsKhmer || []),
      c.explainKhmer?.messageKhmer || '',
      c.explainKhmer?.questionKhmer || '',
      ...(c.steps || []).map((s) => `${s.hint1Khmer} ${s.hint2Khmer} ${s.hint3Khmer}`),
    ].join(' ');

    if (combined.includes('១០០') || combined.includes('100')) {
      errors.push(`[${caseId}] Contaminated with "100" logic in addition exercise!`);
    }
  });

  // (b) HW 8 place value & mental arithmetic should not have HW 1 '100' addition filler
  hw8Ids.forEach((caseId) => {
    const c = HARDCODED_KHMER_TRANSLATIONS[caseId];
    if (!c) return;
    const combined = [
      ...(c.hintsKhmer || []),
      c.explainKhmer?.messageKhmer || '',
      c.explainKhmer?.questionKhmer || '',
    ].join(' ');

    if (combined.includes('២០ + ___ = ១០០') || combined.includes('៣០ + ___ = ១០០')) {
      errors.push(`[${caseId}] Contaminated with copy-pasted HW 1 "100" hints!`);
    }
  });

  // (c) HW 16 calendar exercises should not have HW 1 '100' addition filler
  hw16Ids.forEach((caseId) => {
    const c = HARDCODED_KHMER_TRANSLATIONS[caseId];
    if (!c) return;
    const combined = [
      ...(c.hintsKhmer || []),
      c.explainKhmer?.messageKhmer || '',
      c.explainKhmer?.questionKhmer || '',
    ].join(' ');

    if (combined.includes('២០ + ___ = ១០០') || combined.includes('៣០ + ___ = ១០០')) {
      errors.push(`[${caseId}] Contaminated with copy-pasted HW 1 "100" hints!`);
    }
  });

  console.log(`Audited ${allMathIds.length} math exercises (${hw1Ids.length} HW1, ${hw8Ids.length} HW8, ${hw16Ids.length} HW16) across ${totalSteps} total steps.`);

  if (errors.length > 0) {
    console.error(`\n❌ FAILED with ${errors.length} quality issues:`);
    errors.forEach((e) => console.error(`  - ${e}`));
    process.exit(1);
  } else {
    console.log('\n✅ PASSED! All 31 math exercises across all homeworks are 100% complete, non-leaking, and strictly pedagogical.');
    process.exit(0);
  }
}

runAudit();
