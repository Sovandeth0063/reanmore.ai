import { HomeworkProblem, TutorSession, TutorStep, TutorStepStatus, VisualData } from '../types';
import { ALL_HARDCODED_CASES, getWorksheetImageForCase, RawHardcodedCase } from '../data/hardcodedCases';

function gradeToKey(grade: number): string {
  if (grade <= 2) return 'grade_1_2';
  if (grade <= 4) return 'grade_3_4';
  return 'grade_5_6';
}

function normalizeAnswer(raw: string): string {
  let text = raw.toLowerCase().trim();
  for (const [kWord, eWord] of Object.entries(KHMER_WORDS)) {
    text = text.replace(new RegExp(kWord, 'g'), ` ${eWord} `);
  }
  return text
    .replace(/[,]/g, ' and ')
    .replace(/\s+/g, ' ')
    .replace(/[^\w\s\u1780-\u17FF]/g, '')
    .trim();
}

const NUMBER_WORDS: Record<string, string> = {
  zero: '0', one: '1', two: '2', three: '3', four: '4',
  five: '5', six: '6', seven: '7', eight: '8', nine: '9',
  ten: '10', eleven: '11', twelve: '12', thirteen: '13',
  fourteen: '14', fifteen: '15', sixteen: '16', seventeen: '17',
  eighteen: '18', nineteen: '19', twenty: '20',
  thirty: '30', forty: '40', fifty: '50', sixty: '60',
  seventy: '70', eighty: '80', ninety: '90', hundred: '100',
};

const KHMER_WORDS: Record<string, string> = {
  'បូក': 'add',
  'បន្ថែម': 'add',
  'ដក': 'subtract',
  'គុណ': 'multiply',
  'ចែក': 'divide',
  'និង': 'and',
  'ឬ': 'or',
  'ដប់': '10',
  'សិប': 'tens',
  'រយ': '100',
};

function replaceNumberWords(text: string): string {
  let result = text;
  for (const [word, digit] of Object.entries(NUMBER_WORDS)) {
    const re = new RegExp('(?:^|\\b)' + word + '(?:\\b|$)', 'gi');
    result = result.replace(re, digit);
  }
  return result;
}

const KHMER_DIGITS: Record<string, string> = {
  '០': '0', '១': '1', '២': '2', '៣': '3', '៤': '4',
  '៥': '5', '៦': '6', '៧': '7', '៨': '8', '៩': '9'
};

export function normalizeWithKhmer(raw: string): string {
  if (!raw) return '';
  const converted = raw.replace(/[០-៩]/g, d => KHMER_DIGITS[d] || d);
  return replaceNumberWords(normalizeAnswer(converted));
}

export function answersMatch(studentRaw: string, expectedRaw: string): boolean {
  const s = normalizeWithKhmer(studentRaw).toLowerCase().trim();
  const e = normalizeWithKhmer(expectedRaw).toLowerCase().trim();
  if (!s || !e) return false;
  if (s === e) return true;

  // 1. Khmer & English Affirmative / Negative Cross-Language Matching
  const affirmative = new Set([
    'yes', 'true', 'correct', 'y', 't', 'has', 'tick', '✓', 'check',
    'បាទ', 'ចាស', 'មាន', 'ពិតជាមាន', 'ត្រូវ', 'ពិតមែន', 'បាទ/ចាស', 'បាទមាន', 'ចាសមាន', 'ពិត', 'គ្រីស'
  ]);
  const negative = new Set([
    'no', 'false', 'incorrect', 'n', 'f', 'none', 'cross', '✗', 'x',
    'ទេ', 'គ្មាន', 'មិនមាន', 'អត់', 'ខុស', 'មិនពិត', 'អត់ទេ', 'អត់មាន', 'មិនមែន', 'ខ្វែង'
  ]);

  if ((affirmative.has(s) || [...affirmative].some(w => s.startsWith(w))) && 
      (affirmative.has(e) || [...affirmative].some(w => e.startsWith(w)))) {
    return true;
  }

  if ((negative.has(s) || [...negative].some(w => s.startsWith(w))) && 
      (negative.has(e) || [...negative].some(w => e.startsWith(w)))) {
    return true;
  }

  // 2. Multiple Choice Khmer Letters mapping (ក -> a, ខ -> b, គ -> c, ឃ -> d)
  const khmerLetters: Record<string, string> = { 'ក': 'a', 'ខ': 'b', 'គ': 'c', 'ឃ': 'd' };
  const sMapped = khmerLetters[s] || s;
  const eMapped = khmerLetters[e] || e;
  if (sMapped === eMapped) return true;

  // 3. Numerical equality (e.g. "9" === "9" or "09" === "9")
  const numS = Number(s);
  const numE = Number(e);
  if (!isNaN(numS) && !isNaN(numE)) {
    return numS === numE;
  }

  // 3b. Multi-Number Set Equality (e.g., student typed "4 6", expected was "4 and 6", "4+6", "4, 6", "6 4")
  const sDigits = s.match(/\d+/g);
  const eDigits = e.match(/\d+/g);
  if (sDigits && eDigits && sDigits.length === eDigits.length && sDigits.length > 1) {
    const sSet = new Set(sDigits);
    const eSet = new Set(eDigits);
    if (sSet.size === eSet.size && [...sSet].every(d => eSet.has(d))) {
      return true;
    }
  }

  // 4. Token set equality (e.g. "7 and 3" vs "3 and 7" or "7, 3" vs "៧ និង ៣")
  const splitRe = /\s+(?:and|or|និង|ឬ)\s+|\s*,\s*|\s+/i;
  const sTokens = s.split(splitRe).map(t => khmerLetters[t] || t).filter(Boolean);
  const eTokens = e.split(splitRe).map(t => khmerLetters[t] || t).filter(Boolean);
  if (sTokens.length > 0 && sTokens.length === eTokens.length) {
    const sSet = new Set(sTokens);
    const eSet = new Set(eTokens);
    if (sSet.size === eSet.size && [...sSet].every(t => eSet.has(t))) {
      return true;
    }
  }

  // 5. Bilingual Science & Math Concept Synonyms
  const synonymGroups: string[][] = [
    ['vertebrate', 'vertebrates', 'backbone', 'has backbone', 'ឆ្អឹងកង', 'ឆ្អឹងខ្នង', 'សត្វមានឆ្អឹងកង'],
    ['invertebrate', 'invertebrates', 'no backbone', 'without backbone', 'ឥតឆ្អឹងកង', 'សត្វឥតឆ្អឹងកង', 'គ្មានឆ្អឹងខ្នង'],
    ['feathers', 'feather', 'has feathers', 'រោម', 'រោមស្លាប'],
    ['wings', 'wing', 'has wings', 'ស្លាប', 'មានស្លាប'],
    ['pincers', 'pincer', 'claws', 'claw', 'has pincers', 'ដង្កៀប', 'ក្រញ៉ាំ', 'មានដង្កៀប'],
    ['hump', 'hump on back', 'has hump on back', 'បូក', 'បូកនៅលើខ្នង', 'បូកខ្នង'],
    ['producer', 'producers', 'makes own food', 'អ្នកផលិត', 'រុក្ខជាតិ'],
    ['consumer', 'consumers', 'eats others', 'អ្នកស៊ី', 'អ្នកប្រើប្រាស់', 'សត្វ'],
    ['leaves', 'leaf', 'ស្លឹក', 'ស្លឹកឈើ'],
    ['rabbit', 'ទន្សាយ'],
    ['cabbage', 'ស្ពៃ', 'ស្ពៃក្តោប'],
    ['b, d', 'b and d', 'owl and eagle', 'b, c', 'b and c', 'ខ និង ឃ', 'ខ, ឃ']
  ];

  for (const group of synonymGroups) {
    const sMatches = group.some(g => s === g || s.includes(g));
    const eMatches = group.some(g => e === g || e.includes(g));
    if (sMatches && eMatches) {
      return true;
    }
  }

  // 6. Action targets (e.g. "add 6" or "បូក ៦")
  if (eTokens.length === 2 && (eTokens.includes('add') || eTokens.includes('subtract') || eTokens.includes('multiply') || eTokens.includes('divide') || eTokens.includes('បូក') || eTokens.includes('ដក'))) {
    const actionTarget = eTokens.find(t => t !== 'add' && t !== 'subtract' && t !== 'multiply' && t !== 'divide' && t !== 'បូក' && t !== 'ដក');
    if (actionTarget && (s === actionTarget || sTokens.includes(actionTarget))) {
      return true;
    }
  }

  // 7. Whole word / phrase containment
  if (s.length > e.length && s.includes(e)) {
    const escaped = e.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(?:^|\\b|\\s)${escaped}(?:\\b|\\s|$)`, 'i');
    if (regex.test(s)) return true;
  }

  return false;
}

export function validateStepAnswer(
  caseId: string,
  stepIndex: number,
  studentAnswer: string,
): { correct: boolean; feedback: string } {
  const hcase = ALL_HARDCODED_CASES[caseId];
  if (!hcase) return { correct: false, feedback: 'Exercise not found.' };
  const step = hcase.steps[stepIndex];
  if (!step) return { correct: false, feedback: 'Step not found.' };
  const correct = answersMatch(studentAnswer, step.expected_student_answer);
  return { correct, feedback: correct ? 'Correct!' : 'Not quite. Try again!' };
}

export function validateFinalAnswer(caseId: string, studentAnswer: string): boolean {
  const hcase = ALL_HARDCODED_CASES[caseId];
  if (!hcase) return false;
  const expected = typeof hcase.correct_answer === 'string'
    ? hcase.correct_answer
    : JSON.stringify(hcase.correct_answer);
  return answersMatch(studentAnswer, expected);
}

export function createHardcodedSession(caseId: string, grade: number = 4): TutorSession | null {
  const hcase: RawHardcodedCase | undefined = ALL_HARDCODED_CASES[caseId];
  if (!hcase) return null;
  const gradeKey = gradeToKey(grade);
  const gradeAdaptation = hcase.grade_adaptations?.[gradeKey] ?? '';
  const worksheetImage = getWorksheetImageForCase(caseId);
  const steps: TutorStep[] = hcase.steps.map(s => ({
    step: s.step,
    tutor_question: s.tutor_question,
    expected_student_answer: s.expected_student_answer,
  }));
  return {
    case_id: caseId,
    source: 'hardcoded',
    subject: hcase.subject,
    original_question: hcase.original_question,
    tutor_intro: hcase.tutor_intro,
    steps,
    hints: hcase.hints,
    explain_another_way: hcase.explain_another_way,
    visual_data: hcase.visual_data as VisualData,
    grade_adaptation: gradeAdaptation,
    final_celebration: hcase.final_celebration,
    ...(worksheetImage !== undefined ? { worksheet_image: worksheetImage } : {}),
  };
}

export function createInitialSessionState(session: TutorSession) {
  return {
    session,
    currentStep: 0,
    wrongAttempts: 0,
    hintsUsed: 0,
    stepStatuses: session.steps.map((): TutorStepStatus => 'pending'),
    isComplete: false,
    showExplainAnotherWay: false,
  };
}

export function isAnswerCorrect(studentRaw: string, expectedRaw: string): boolean {
  return answersMatch(studentRaw, expectedRaw);
}

import { matchCaseFromProblem, matchCaseId } from './caseMatcher';

import { getKhmerCaseData } from './translationService';

export function enrichProblemFromCase(problem: HomeworkProblem, grade: number = 4): HomeworkProblem {
  if (!problem) return problem;
  
  const matchedId = matchCaseFromProblem(problem) ||
    (problem.problemStatementEng ? matchCaseId(problem.problemStatementEng) : null) ||
    (problem.titleEng ? matchCaseId(problem.titleEng) : null) ||
    (problem.problemStatementKhmer ? matchCaseId(problem.problemStatementKhmer) : null);

  const targetCaseId = matchedId || (problem.id && ALL_HARDCODED_CASES[problem.id] ? problem.id : null);

  if (!targetCaseId) return problem;
  const hcase = ALL_HARDCODED_CASES[targetCaseId];
  if (!hcase) return problem;

  const totalSteps = hcase.steps.length;
  const gradeKey = gradeToKey(grade);
  const gradeAdaptation = hcase.grade_adaptations?.[gradeKey] ?? '';
  const worksheetImage = getWorksheetImageForCase(targetCaseId);
  const khmerCase = getKhmerCaseData(targetCaseId);

  const steps = hcase.steps.map((s, idx) => {
    const kStep = khmerCase?.steps?.[idx];
    const qKhmer = kStep?.questionKhmer || s.tutor_question;
    const socraticKhmer = kStep?.socraticPromptKhmer || qKhmer;
    const h1Khmer = kStep?.hint1Khmer || (idx === 0 ? khmerCase?.hintsKhmer?.[0] : undefined) || hcase.hints?.[0] || 'ចាប់ផ្ដើមដោយពិនិត្យមើលសំណួរក្នុងជំហាននេះដោយយកចិត្តទុកដាក់។';
    const h2Khmer = kStep?.hint2Khmer || (idx === 0 ? khmerCase?.hintsKhmer?.[1] : undefined) || hcase.hints?.[1] || 'រាប់ ឬគណនាជាជំហានៗដោយផ្អែកលើតម្រុយដំបូង។';
    const h3Khmer = kStep?.hint3Khmer || (idx === 0 ? khmerCase?.hintsKhmer?.[2] : undefined) || hcase.hints?.[2] || (gradeAdaptation ? `ការណែនាំ៖ ${gradeAdaptation}` : 'ព្យាយាមគិតម្តងមួយជំហានៗ!');
    const expKhmer = kStep?.explainKhmer || khmerCase?.explainKhmer?.messageKhmer || hcase.explain_another_way?.message || s.tutor_question;

    return {
      id: `${targetCaseId}-step-${s.step}`,
      stepNumber: s.step,
      totalSteps: totalSteps,
      questionKhmer: qKhmer,
      questionEng: s.tutor_question,
      inputFormat: 'text' as const,
      correctAnswer: s.expected_student_answer,
      socraticPromptKhmer: socraticKhmer,
      socraticPromptEng: s.tutor_question,
      hint1: {
        khmer: h1Khmer,
        eng: hcase.hints[0] || 'Read the question carefully.',
      },
      hint2: {
        khmer: h2Khmer,
        eng: hcase.hints[1] || 'Look for keywords or numbers in the step.',
      },
      hint3: {
        titleKhmer: 'ឧទាហរណ៍ជំនួយ',
        titleEng: 'Helpful Example',
        exampleKhmer: h3Khmer,
        exampleEng: hcase.hints[2] || (gradeAdaptation ? `Tip: ${gradeAdaptation}` : 'Try thinking step by step!'),
      },
      explainDifferently: {
        simpleKhmer: expKhmer,
        simpleEng: hcase.explain_another_way?.message || s.tutor_question,
        analogyTitle: hcase.concept || 'ការពន្យល់ងាយយល់',
        analogyKhmer: khmerCase?.explainKhmer?.questionKhmer || hcase.explain_another_way?.question || '',
        analogyEng: hcase.explain_another_way?.question || '',
        analogyType: 'apples' as const,
      },
    };
  });

  const finalImage = worksheetImage || problem.imageUri;

  return {
    ...problem,
    id: targetCaseId,
    problemStatementKhmer: khmerCase?.statementKhmer || hcase.original_question,
    problemStatementEng: hcase.original_question,
    visualData: hcase.visual_data,
    ...(finalImage ? { imageUri: finalImage } : {}),
    steps,
  };
}


