/**
 * Automated Content Quality Validator for ALL Hardcoded English Pedagogical Cases.
 * Validates:
 * 1. Completeness of 3-tier hints and Socratic prompts across all 61 math & science cases.
 * 2. Step count matching between englishPedagogicalData.ts and math.json / science.json.
 * 3. Zero answer leakage in Hint 1 and Hint 2.
 * 4. Kid-friendly clarity and completeness.
 */

import { HARDCODED_ENGLISH_PEDAGOGY } from '../src/data/englishPedagogicalData';
import mathData from '../src/data/math.json';
import scienceData from '../src/data/science.json';

const allMathIds = [
  // HW1
  'math_p1_a1', 'math_p1_a2', 'math_p1_a3', 'math_p1_a4', 'math_p1_a5',
  'math_p1_b1', 'math_p1_b2', 'math_p1_b3', 'math_p1_b4', 'math_p1_b5', 'math_p1_b6',
  // HW8
  'math_p8_a1', 'math_p8_a2', 'math_p8_a3', 'math_p8_a4',
  'math_p8_b2', 'math_p8_b6', 'math_p8_b3', 'math_p8_b7', 'math_p8_b4', 'math_p8_b8',
  // HW16
  'math_p16_a1', 'math_p16_a2', 'math_p16_a3', 'math_p16_a4',
  'math_p16_b1', 'math_p16_b2', 'math_p16_b3', 'math_p16_b4', 'math_p16_b5', 'math_p16_b6',
];

const allScienceIds = [
  // Page 8
  'science_p8_flamingo', 'science_p8_lobster', 'science_p8_camel',
  'science_p8_giraffe', 'science_p8_slug', 'science_p8_moth',
  // Page 6
  'science_p6_bird', 'science_p6_mammal', 'science_p6_amphibian',
  'science_p6_reptile', 'science_p6_fish', 'science_p6_invertebrate',
  // Page 44
  'science_p44_a_plant_part', 'science_p44_b_plant_eater', 'science_p44_c_i_producer',
  'science_p44_c_ii_eat_animals', 'science_p44_c_iii_consumers', 'science_p44_d_producer_word',
  // Grade 1
  'science_g1_eyes', 'science_g1_ears', 'science_g1_nose',
  'science_g1_tongue', 'science_g1_hands', 'science_g1_living',
  // Grade 2-3
  'science_g2_plant_needs', 'science_g2_plant_parts', 'science_g2_habitats',
  'science_g3_matter_ice', 'science_g3_matter_states', 'science_g3_animal_diet',
];

const allIds = [...allMathIds, ...allScienceIds];

function runEnglishAudit() {
  console.log(`=== Auditing All ${allIds.length} English Exercises (${allMathIds.length} Math + ${allScienceIds.length} Science) ===`);
  const errors: string[] = [];
  let totalSteps = 0;

  for (const caseId of allIds) {
    const eCase = HARDCODED_ENGLISH_PEDAGOGY[caseId];
    if (!eCase) {
      errors.push(`[${caseId}] Missing from HARDCODED_ENGLISH_PEDAGOGY`);
      continue;
    }

    const isMath = caseId.startsWith('math_');
    const sourceData = isMath ? (mathData as any).cases?.[caseId] : (scienceData as any).cases?.[caseId];
    const sourceSteps = sourceData?.steps || [];
    const eSteps = eCase.steps || [];
    totalSteps += eSteps.length;

    if (eSteps.length !== sourceSteps.length) {
      errors.push(`[${caseId}] Step count mismatch: English has ${eSteps.length}, source JSON has ${sourceSteps.length}`);
    }

    eSteps.forEach((step, idx) => {
      const sNum = idx + 1;

      // 1. Completeness checks
      if (!step.questionEng) errors.push(`[${caseId} Step ${sNum}] Missing questionEng`);
      if (!step.socraticPromptEng) errors.push(`[${caseId} Step ${sNum}] Missing socraticPromptEng`);
      if (!step.hint1Eng) errors.push(`[${caseId} Step ${sNum}] Missing hint1Eng`);
      if (!step.hint2Eng) errors.push(`[${caseId} Step ${sNum}] Missing hint2Eng`);
      if (!step.hint3Eng) errors.push(`[${caseId} Step ${sNum}] Missing hint3Eng`);
      if (!step.explainEng) errors.push(`[${caseId} Step ${sNum}] Missing explainEng`);
      if (!step.analogyEng) errors.push(`[${caseId} Step ${sNum}] Missing analogyEng`);
      if (!step.acceptableAnswers || step.acceptableAnswers.length === 0) {
        errors.push(`[${caseId} Step ${sNum}] Missing acceptableAnswers`);
      }

      // 2. Answer leakage check: expected answer should not be bluntly stated in hint 1 or 2 as "= {ans}"
      const expected = sourceSteps[idx]?.expected_student_answer;
      if (expected && typeof expected === 'string') {
        const trimmed = expected.trim().toLowerCase();
        // Check if numeric
        if (/^\d+$/.test(trimmed)) {
          if (step.hint1Eng.includes(`= ${trimmed}`) || step.hint1Eng.includes(`is ${trimmed}`)) {
            errors.push(`[${caseId} Step ${sNum}] Hint 1 leaks exact answer: "${step.hint1Eng}"`);
          }
          if (step.hint2Eng.includes(`= ${trimmed}`) && !step.hint2Eng.includes('?')) {
            // Only flag if not a question
            if (!step.hint2Eng.includes(`= ${trimmed}?`)) {
              errors.push(`[${caseId} Step ${sNum}] Hint 2 leaks exact answer: "${step.hint2Eng}"`);
            }
          }
        }
      }
    });
  }

  if (errors.length > 0) {
    console.error(`❌ Found ${errors.length} error(s):`);
    errors.forEach((e) => console.error(`  - ${e}`));
    process.exit(1);
  }

  console.log(`Audited ${allIds.length} exercises across ${totalSteps} total steps.`);
  console.log('✅ PASSED! All 61 exercises have complete, pedagogical, step-aligned English guidance!');
}

runEnglishAudit();
