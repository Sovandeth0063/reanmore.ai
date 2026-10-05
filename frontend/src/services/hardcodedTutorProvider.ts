import { HomeworkProblem, TutorSession, TutorStep, TutorStepStatus, VisualData, Grade, Subject } from '../types';
import {
  ALL_HARDCODED_CASES,
  getWorksheetImageForCase,
  RawHardcodedCase,
  MATH_QUEUES,
  SCIENCE_QUEUES,
  WORKSHEET_IMAGES,
} from '../data/hardcodedCases';

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
    .replace(/\+/g, ' plus ')
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

export function answersMatch(studentRaw: string, expectedRaw: string, acceptableAnswers?: string[]): boolean {
  const s = normalizeWithKhmer(studentRaw).toLowerCase().trim();
  const e = normalizeWithKhmer(expectedRaw).toLowerCase().trim();
  if (!s || !e) return false;
  if (s === e) return true;

  // 0. Acceptable answers array check if provided
  if (acceptableAnswers && acceptableAnswers.length > 0) {
    for (const acc of acceptableAnswers) {
      const a = normalizeWithKhmer(acc).toLowerCase().trim();
      if (s === a) return true;
      if (answersMatch(studentRaw, acc)) return true;
    }
  }

  // 1. Khmer & English Affirmative / Negative Cross-Language Matching
  const affirmative = new Set([
    'yes', 'true', 'correct', 'y', 't', 'has', 'tick', '✓', 'check',
    'បាទ', 'ចាស', 'មាន', 'ពិតជាមាន', 'ត្រូវ', 'ពិតមែន', 'បាទ/ចាស', 'បាទមាន', 'ចាសមាន', 'ពិត', 'គ្រីស',
    '✓ មាន', 'មានរោមស្លាប', 'មានស្លាប', 'មានដង្កៀប', 'មានបូក'
  ]);
  const negative = new Set([
    'no', 'false', 'incorrect', 'n', 'f', 'none', 'cross', '✗', 'x',
    'ទេ', 'គ្មាន', 'មិនមាន', 'អត់', 'ខុស', 'មិនពិត', 'អត់ទេ', 'អត់មាន', 'មិនមែន', 'ខ្វែង',
    '✗ គ្មាន', 'គ្មានទេ'
  ]);

  if ((affirmative.has(s) || [...affirmative].some(w => s.startsWith(w))) && 
      (affirmative.has(e) || [...affirmative].some(w => e.startsWith(w)))) {
    return true;
  }

  if ((negative.has(s) || [...negative].some(w => s.startsWith(w))) && 
      (negative.has(e) || [...negative].some(w => e.startsWith(w)))) {
    return true;
  }

  // 1b. Feature Presence Cross-Matching (Worksheet Table Classification)
  // When an animal has the feature, answering affirmative (Yes / ✓ / មាន)
  // or answering the feature name (Feathers / Wings / etc.) are equivalent.
  const featureAffirmatives: Record<string, string[]> = {
    vertebrate: ['vertebrate', 'vertebrates', 'backbone', 'has backbone', 'ឆ្អឹងកង', 'ឆ្អឹងខ្នង', 'សត្វមានឆ្អឹងកង'],
    feathers: ['feathers', 'feather', 'has feathers', 'រោម', 'រោមស្លាប', 'មានរោមស្លាប'],
    wings: ['wings', 'wing', 'has wings', 'ស្លាប', 'មានស្លាប'],
    pincers: ['pincers', 'pincer', 'claws', 'claw', 'has pincers', 'ដង្កៀប', 'ក្រញ៉ាំ', 'មានដង្កៀប'],
    hump: ['hump', 'hump on back', 'has hump on back', 'បូក', 'បូកនៅលើខ្នង', 'បូកខ្នង', 'មានបូក'],
  };

  for (const feats of Object.values(featureAffirmatives)) {
    const eIsFeat = feats.some(f => e === f || e.includes(f));
    const sIsFeat = feats.some(f => s === f || s.includes(f));
    const sIsAffirm = affirmative.has(s) || [...affirmative].some(w => s.startsWith(w));
    const eIsAffirm = affirmative.has(e) || [...affirmative].some(w => e.startsWith(w));

    if ((eIsFeat && sIsAffirm) || (sIsFeat && eIsAffirm) || (eIsFeat && sIsFeat)) {
      return true;
    }
  }

  // 2. Multiple Choice Khmer Letters mapping (ក -> a, ខ -> b, គ -> c, ឃ -> d)
  const khmerLetters: Record<string, string> = { 'ក': 'a', 'ខ': 'b', 'គ': 'c', 'ឃ': 'd' };
  const sMapped = khmerLetters[s] || s;
  const eMapped = khmerLetters[e] || e;
  if (sMapped === eMapped) return true;

  // 2b. Option Letter Prefix matching (e.g. student selected "C (ទន្សាយ / Rabbit)" or "គ. សត្វទន្សាយ", expected is "C")
  const sLetterMatch = s.match(/^([a-d]|[ក-ឃ])(?:\.|\s|\)|\()/i);
  if (sLetterMatch) {
    const sCleanLetter = khmerLetters[sLetterMatch[1].toLowerCase()] || sLetterMatch[1].toLowerCase();
    if (sCleanLetter === eMapped || sCleanLetter === e) return true;
  }
  const eLetterMatch = e.match(/^([a-d]|[ក-ឃ])(?:\.|\s|\)|\()/i);
  if (eLetterMatch) {
    const eCleanLetter = khmerLetters[eLetterMatch[1].toLowerCase()] || eLetterMatch[1].toLowerCase();
    if (sMapped === eCleanLetter || s === eCleanLetter) return true;
  }

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
    ['producer', 'producers', 'makes own food', 'makes its own food', 'បង្កើតអាហារដោយខ្លួនឯង', 'អ្នកផលិត', 'រុក្ខជាតិ'],
    ['consumer', 'consumers', 'eats others', 'eats other organisms', 'ស៊ីសារពាង្គកាយដទៃ', 'អ្នកស៊ី', 'អ្នកប្រើប្រាស់', 'សត្វ'],
    ['leaves', 'leaf', 'ស្លឹក', 'ស្លឹកឈើ'],
    ['rabbit', 'ទន្សាយ'],
    ['cabbage', 'ស្ពៃ', 'ស្ពៃក្តោប'],
    ['b, d', 'b and d', 'owl and eagle', 'owl & eagle', 'a and d', 'a & d', 'b, c', 'b and c', 'ខ និង ឃ', 'ខ, ឃ', 'ទីទុយ និងឥន្ទ្រី', 'a និង d', 'a, d'],
    ['a, c and d', 'a, c & d', 'a, c, d', 'a c d', 'a c និង d', 'consumers', 'អ្នកស៊ី'],
    ['in water', 'water', 'ក្នុងទឹក', 'ទឹក'],
    ['gills', 'gill', 'ស្រកី', 'ស្រកីត្រី'],
    ['moist skin', 'smooth skin', 'ស្បែកសើម', 'ស្បែករលោងសើម', 'ស្បែករលោង'],
    ['frog', 'កង្កែប'],
    ['snake', 'ពស់'],
    ['scales', 'scale', 'ស្រកា'],
    ['mammal', 'mammals', 'ថនិកសត្វ'],
    ['hair or fur', 'hair', 'fur', 'រោមសត្វ', 'រោម'],
    ['a plant', 'plant', 'plants', 'រុក្ខជាតិ'],
    ['eyes', 'eye', 'ភ្នែក'],
    ['sight', 'see', 'ការមើលឃើញ', 'មើលឃើញ'],
    ['ears', 'ear', 'ត្រចៀក'],
    ['hearing', 'hear', 'ការស្តាប់', 'ការស្តាប់ឮ', 'ស្តាប់'],
    ['nose', 'ច្រមុះ'],
    ['smell', 'ការហិតក្លិន', 'ហិតក្លិន'],
    ['tongue', 'អណ្តាត'],
    ['taste', 'ការភ្លក្ស', 'ការភ្លក្សរសជាតិ', 'ភ្លក្ស'],
    ['skin', 'ស្បែក'],
    ['touch', 'ការប៉ះ', 'ការប៉ះដឹង', 'ប៉ះដឹង'],
    ['kitten', 'cat', 'កូនឆ្មា', 'ឆ្មា'],
    ['stone', 'rock', 'ដុំថ្ម', 'ថ្ម'],
    ['solid', 'solids', 'សភាពរឹង', 'រឹង'],
    ['liquid', 'liquids', 'សភាពរាវ', 'រាវ'],
    ['gas', 'gases', 'សភាពឧស្ម័ន', 'ឧស្ម័ន'],
    ['melting', 'melt', 'melts', 'ការរលាយ', 'រលាយ'],
    ['roots', 'root', 'ឫស', 'ឬស'],
    ['stem', 'stems', 'ដើម', 'ដើមឈើ'],
    ['herbivores', 'herbivore', 'plant eater', 'plant eaters', 'សត្វស៊ីរុក្ខជាតិ', 'ស៊ីរុក្ខជាតិ'],
    ['tens', 'ten', 'the tens', 'tens digit', 'the tens digit', 'tens place', 'the tens place', 'increases by 1', 'tens increases by 1', 'the tens place increases by 1', 'ខ្ទង់ដប់', 'ដប់'],
    ['ones', 'one', 'the ones', 'ones digit', 'the ones digit', 'ones place', 'the ones place', 'ខ្ទង់រាយ', 'រាយ'],
    ['hundreds', 'hundred', 'the hundreds', 'hundreds digit', 'the hundreds digit', 'hundreds place', 'the hundreds place', 'ខ្ទង់រយ', 'រយ'],
    ['february', 'february has an extra day', 'because february has an extra day', 'extra day in february', 'leap year', 'leap years', 'because of leap years', 'ខែកុម្ភៈ', 'ឆ្នាំបង្គ្រប់'],
    ['31', '31 days', 'student selects 31', '៣១', '៣១ ថ្ងៃ'],
    ['30', '30 days', 'student selects 30', '៣០', '៣០ ថ្ងៃ'],
    ['28', '28 days', '២៨', '២៨ ថ្ងៃ'],
    ['29', '29 days', '២៩', '២៩ ថ្ងៃ'],
    ['row 2', 'second row', 'the second row', 'the row containing 9 to 15', 'row containing 9 to 15', '9 to 15', 'ជួរទី២', 'ជួរទី 2'],
    ['add', 'plus', 'addition', 'បូក', 'បន្ថែម'],
    ['subtract', 'minus', 'subtraction', 'ដក'],
  ];

  for (const group of synonymGroups) {
    const sMatches = group.some(g => s === g || s.includes(g));
    const eMatches = group.some(g => e === g || e.includes(g));
    if (sMatches && eMatches) {
      return true;
    }
  }

  // 6. Action targets (e.g. "add 6" or "បូក ៦")
  if (eTokens.length === 2 && (eTokens.includes('add') || eTokens.includes('subtract') || eTokens.includes('multiply') || eTokens.includes('divide') || eTokens.includes('plus') || eTokens.includes('minus') || eTokens.includes('បូក') || eTokens.includes('ដក'))) {
    const actionTarget = eTokens.find(t => !['add', 'subtract', 'multiply', 'divide', 'plus', 'minus', 'បូក', 'ដក'].includes(t));
    if (actionTarget && (s === actionTarget || sTokens.includes(actionTarget))) {
      return true;
    }
  }

  // 6b. Action verb matching (e.g. question asks "add or subtract?", expected is "add 6", student answers "add" or "plus")
  const verbSynonyms: Record<string, string[]> = {
    add: ['add', 'plus', 'addition', 'បូក', 'បន្ថែម'],
    subtract: ['subtract', 'minus', 'subtraction', 'ដក'],
    multiply: ['multiply', 'times', 'multiplication', 'គុណ'],
    divide: ['divide', 'division', 'ចែក'],
  };
  for (const syns of Object.values(verbSynonyms)) {
    const sHas = syns.some(v => sTokens.includes(v) || s === v);
    const eHas = syns.some(v => eTokens.includes(v) || e === v);
    if (sHas && eHas && (sTokens.length === 1 || eTokens.length <= 2)) {
      return true;
    }
  }

  // 7. Whole word / phrase containment in either direction
  if (s.length > e.length && s.includes(e)) {
    const escaped = e.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(?:^|\\b|\\s)${escaped}(?:\\b|\\s|$)`, 'i');
    if (regex.test(s)) return true;
  }
  if (e.length > s.length && s.length >= 3 && e.includes(s)) {
    const escaped = s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(?:^|\\b|\\s)${escaped}(?:\\b|\\s|$)`, 'i');
    if (regex.test(e)) return true;
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
  const engCase = getEnglishCaseData(caseId);
  const acceptable = engCase?.steps?.[stepIndex]?.acceptableAnswers;
  const correct = answersMatch(studentAnswer, step.expected_student_answer, acceptable);
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
  const engCase = getEnglishCaseData(caseId);
  const steps: TutorStep[] = hcase.steps.map((s, idx) => ({
    step: s.step,
    tutor_question: engCase?.steps?.[idx]?.questionEng || s.tutor_question,
    expected_student_answer: s.expected_student_answer,
  }));
  return {
    case_id: caseId,
    source: 'hardcoded',
    subject: hcase.subject,
    original_question: engCase?.statementEng || hcase.original_question,
    tutor_intro: hcase.tutor_intro,
    steps,
    hints: engCase?.hintsEng || hcase.hints,
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

export function isAnswerCorrect(studentRaw: string, expectedRaw: string, acceptableAnswers?: string[]): boolean {
  return answersMatch(studentRaw, expectedRaw, acceptableAnswers);
}

import { matchCaseFromProblem, matchCaseId } from './caseMatcher';
import { getKhmerCaseData } from './translationService';
import { getEnglishCaseData } from '../data/englishPedagogicalData';

export const P8_ANIMAL_ANSWERS: Record<string, Record<string, boolean>> = {
  flamingo: { vertebrate: true, feathers: true, hump_on_back: false, pincers: false, wings: true },
  lobster:  { vertebrate: false, feathers: false, hump_on_back: false, pincers: true, wings: false },
  camel:    { vertebrate: true, feathers: false, hump_on_back: true, pincers: false, wings: false },
  giraffe:  { vertebrate: true, feathers: false, hump_on_back: false, pincers: false, wings: false },
  slug:     { vertebrate: false, feathers: false, hump_on_back: false, pincers: false, wings: false },
  moth:     { vertebrate: false, feathers: false, hump_on_back: false, pincers: false, wings: true },
};

export const SCIENCE_STEP_OPTIONS: Record<string, Record<number, string[]>> = {
  science_p6_bird: {
    1: ['រោមស្លាប (Feathers)', 'រោមសត្វ (Fur)', 'ស្រកា (Scales)'],
    2: ['បាទ/ចាស ពិតមែន (Yes)', 'ទេ មិនមែនទេ (No)'],
  },
  science_p6_mammal: {
    1: ['ថនិកសត្វ (Mammal)', 'សត្វស្លាប (Bird)', 'សត្វល្មូន (Reptile)', 'សត្វឥតឆ្អឹងកង (Invertebrate)'],
    2: ['រោមសត្វ (Hair or fur)', 'រោមស្លាប (Feathers)', 'ស្រកា (Scales)'],
  },
  science_p6_amphibian: {
    1: ['កង្កែប (Frog)', 'ពស់ (Snake)', 'ត្រី (Fish)', 'បក្សី (Bird)'],
    2: ['ស្បែករលោងសើម (Moist skin)', 'រោមស្លាប (Feathers)', 'ស្រកា (Scales)'],
    3: ['ស្បែករលោងសើម (Moist skin)', 'រោមសត្វ (Fur)', 'ស្លាប (Wings)'],
  },
  science_p6_reptile: {
    1: ['ពស់ (Snake)', 'កង្កែប (Frog)', 'សត្វស្លាប (Bird)', 'ថនិកសត្វ (Mammal)'],
    2: ['ស្រកា (Scales)', 'រោមស្លាប (Feathers)', 'រោមសត្វ (Fur)'],
  },
  science_p6_fish: {
    1: ['ក្នុងទឹក (In water)', 'លើគោក (On land)', 'លើដើមឈើ (In trees)'],
    2: ['ស្រកី (Gills)', 'សួត (Lungs)', 'ច្រមុះ (Nose)'],
  },
  science_p6_invertebrate: {
    1: ['សត្វមានឆ្អឹងកង (Vertebrates)', 'សត្វឥតឆ្អឹងកង (Invertebrates)', 'រុក្ខជាតិ (Plants)'],
    2: ['ទេ មិនមែនទេ (No)', 'បាទ/ចាស (Yes)'],
    3: ['សត្វឥតឆ្អឹងកង (Invertebrates)', 'សត្វមានឆ្អឹងកង (Vertebrates)', 'ថនិកសត្វ (Mammals)'],
  },
  science_p44_a_plant_part: {
    1: ['ស្លឹក (Leaf)', 'ឫស (Roots)', 'ដើម (Stem)', 'ផ្កា (Flower)'],
    2: ['ស្លឹក (Leaf)', 'ឫស (Roots)', 'ដើម (Stem)'],
    3: ['ស្លឹក (Leaf)', 'ឫស (Roots)', 'ដើម (Stem)', 'ផ្កា (Flower)'],
  },
  science_p44_b_plant_eater: {
    1: ['ទីទុយ ទន្សាយ ឥន្ទ្រី (Owl, rabbit, eagle)', 'ស្ពៃក្តោបប៉ុណ្ណោះ (Only cabbage)', 'ទន្សាយតែមួយ (Only rabbit)'],
    2: ['សត្វទន្សាយ (Rabbit)', 'សត្វទីទុយ (Owl)', 'សត្វឥន្ទ្រី (Eagle)', 'ស្ពៃក្តោប (Cabbage)'],
    3: ['C (ទន្សាយ / Rabbit)', 'A (ទីទុយ / Owl)', 'B (ស្ពៃក្តោប / Cabbage)', 'D (ឥន្ទ្រី / Eagle)'],
  },
  science_p44_c_i_producer: {
    1: ['B (ស្ពៃក្តោប / Cabbage)', 'A (ទីទុយ / Owl)', 'C (ទន្សាយ / Rabbit)', 'D (ឥន្ទ្រី / Eagle)'],
    2: ['បាទ/ចាស (Yes)', 'ទេ (No)'],
    3: ['B', 'A', 'C', 'D'],
  },
  science_p44_c_ii_eat_animals: {
    1: ['ទីទុយ និងឥន្ទ្រី (Owl and eagle)', 'ទន្សាយ និងស្ពៃក្តោប (Rabbit and cabbage)', 'ស្ពៃក្តោបប៉ុណ្ណោះ (Only cabbage)'],
    2: ['ទេ មិនមែនទេ (No)', 'បាទ/ចាស (Yes)'],
    3: ['A និង D (Owl and eagle)', 'B និង C', 'A និង B', 'C និង D'],
  },
  science_p44_c_iii_consumers: {
    1: ['B (ស្ពៃក្តោប / Cabbage)', 'A (ទីទុយ / Owl)', 'C (ទន្សាយ / Rabbit)', 'D (ឥន្ទ្រី / Eagle)'],
    2: ['បង្កើតអាហារដោយខ្លួនឯង (Makes own food)', 'ស៊ីសារពាង្គកាយដទៃ (Eats others)'],
    3: ['ទីទុយ ទន្សាយ ឥន្ទ្រី (Owl, rabbit, eagle)', 'ស្ពៃក្តោបប៉ុណ្ណោះ (Cabbage only)', 'ទន្សាយប៉ុណ្ណោះ (Rabbit only)'],
    4: ['A, C និង D (A, C and D)', 'A និង B', 'តែ B ប៉ុណ្ណោះ', 'ទាំងអស់'],
  },
  science_p44_d_producer_word: {
    1: ['រុក្ខជាតិ (A plant)', 'សត្វ (An animal)', 'ផ្សិត (Fungi)'],
    2: ['អ្នកផលិត (Producer)', 'អ្នកស៊ី (Consumer)', 'អ្នកបរបាញ់ (Predator)'],
    3: ['អ្នកផលិត (Producers)', 'អ្នកស៊ី (Consumers)', 'សត្វស៊ីរុក្ខជាតិ (Herbivores)'],
  },
  science_g1_eyes: {
    1: ['ភ្នែក (Eyes)', 'ត្រចៀក (Ears)', 'ច្រមុះ (Nose)'],
    2: ['ការមើលឃើញ (Sight)', 'ការស្តាប់ (Hearing)', 'ការហិតក្លិន (Smell)'],
  },
  science_g1_ears: {
    1: ['ត្រចៀក (Ears)', 'ភ្នែក (Eyes)', 'មាត់ (Mouth)'],
    2: ['បាទ/ចាស (Yes)', 'ទេ (No)'],
  },
  science_g1_nose: {
    1: ['ច្រមុះ (Nose)', 'អណ្តាត (Tongue)', 'ត្រចៀក (Ears)'],
    2: ['បាទ/ចាស (Yes)', 'ទេ (No)'],
  },
  science_g1_tongue: {
    1: ['អណ្តាត (Tongue)', 'ធ្មេញ (Teeth)', 'បបូរមាត់ (Lips)'],
    2: ['បាទ/ចាស (Yes)', 'ទេ (No)'],
  },
  science_g1_hands: {
    1: ['ស្បែក (Skin)', 'សក់ (Hair)', 'ក្រចក (Nails)'],
    2: ['បាទ/ចាស (Yes)', 'ទេ (No)'],
  },
  science_g1_living: {
    1: ['បាទ/ចាស (Yes)', 'ទេ (No)'],
    2: ['ទេ (No)', 'បាទ/ចាស (Yes)'],
    3: ['កូនឆ្មា (Kitten)', 'ដុំថ្ម (Stone)'],
  },
  science_g2_plant_needs: {
    1: ['បាទ/ចាស (Yes)', 'ទេ (No)'],
    2: ['ទឹក (Water)', 'ប្រេង (Oil)', 'ទឹកផ្លែឈើ (Juice)'],
  },
  science_g2_plant_parts: {
    1: ['ឫស (Roots)', 'ស្លឹក (Leaves)', 'ផ្កា (Flower)'],
    2: ['ដើម (Stem)', 'ឫស (Roots)', 'ផ្លែ (Fruit)'],
  },
  science_g2_habitats: {
    1: ['ទេ (No)', 'បាទ/ចាស (Yes)'],
    2: ['ក្នុងទឹក (In water)', 'លើដើមឈើ (In trees)', 'វាលខ្សាច់ (In desert)'],
  },
  science_g3_matter_ice: {
    1: ['សភាពរឹង (Solid)', 'សភាពរាវ (Liquid)', 'សភាពឧស្ម័ន (Gas)'],
    2: ['បាទ/ចាស (Yes)', 'ទេ (No)'],
    3: ['ការរលាយ (Melting)', 'ការកក (Freezing)', 'ការរំហួត (Evaporation)'],
  },
  science_g3_matter_states: {
    1: ['បាទ/ចាស (Yes)', 'ទេ (No)'],
    2: ['សភាពរាវ (Liquid)', 'សភាពរឹង (Solid)', 'សភាពឧស្ម័ន (Gas)'],
  },
  science_g3_animal_diet: {
    1: ['បាទ/ចាស (Yes)', 'ទេ (No)'],
    2: ['សត្វស៊ីរុក្ខជាតិ (Herbivores)', 'សត្វស៊ីសាច់ (Carnivores)', 'អ្នកផលិត (Producers)'],
  },
};

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
  const engCase = getEnglishCaseData(targetCaseId);

  const steps = hcase.steps.map((s, idx) => {
    const kStep = khmerCase?.steps?.[idx];
    const eStep = engCase?.steps?.[idx];
    const qKhmer = kStep?.questionKhmer || s.tutor_question;
    const qEng = eStep?.questionEng || s.tutor_question;
    const socraticKhmer = kStep?.socraticPromptKhmer || qKhmer;
    const socraticEng = eStep?.socraticPromptEng || qEng;
    const isEngText = (str?: string) => Boolean(str && /^[A-Za-z0-9\s.,!?:;'"()\-_/+%=]+$/.test(str.trim()));

    const defaultH1 = hcase.subject === 'science'
      ? 'ពិនិត្យមើលលក្ខណៈពិសេសរបស់សត្វ ឬរុក្ខជាតិក្នុងសំណួរដោយយកចិត្តទុកដាក់។'
      : 'ចាប់ផ្ដើមដោយពិនិត្យមើលសំណួរក្នុងជំហាននេះដោយយកចិត្តទុកដាក់។';
    const defaultH2 = hcase.subject === 'science'
      ? 'គិតអំពីលក្ខណៈជីវវិទ្យា និងប្រៀបធៀបជាមួយក្រុមសត្វដទៃទៀត។'
      : 'រាប់ ឬគណនាជាជំហានៗដោយផ្អែកលើតម្រុយដំបូង។';
    const defaultH3 = gradeAdaptation
      ? `ការណែនាំ៖ ${gradeAdaptation}`
      : (hcase.subject === 'science' ? 'ពិចារណាលើរូបរាង និងលក្ខណៈសម្គាល់ចម្បង!' : 'ព្យាយាមគិតម្តងមួយជំហានៗ!');

    const h1Khmer = (kStep?.hint1Khmer && !isEngText(kStep.hint1Khmer) ? kStep.hint1Khmer : null)
      || (khmerCase?.hintsKhmer?.[0] && !isEngText(khmerCase.hintsKhmer[0]) ? khmerCase.hintsKhmer[0] : null)
      || defaultH1;

    const h2Khmer = (kStep?.hint2Khmer && !isEngText(kStep.hint2Khmer) ? kStep.hint2Khmer : null)
      || (khmerCase?.hintsKhmer?.[1] && !isEngText(khmerCase.hintsKhmer[1]) ? khmerCase.hintsKhmer[1] : null)
      || defaultH2;

    const h3Khmer = (kStep?.hint3Khmer && !isEngText(kStep.hint3Khmer) ? kStep.hint3Khmer : null)
      || (khmerCase?.hintsKhmer?.[2] && !isEngText(khmerCase.hintsKhmer[2]) ? khmerCase.hintsKhmer[2] : null)
      || defaultH3;

    const expKhmer = (kStep?.explainKhmer && !isEngText(kStep.explainKhmer) ? kStep.explainKhmer : null)
      || (khmerCase?.explainKhmer?.messageKhmer && !isEngText(khmerCase.explainKhmer.messageKhmer) ? khmerCase.explainKhmer.messageKhmer : null)
      || qKhmer;

    const h1Eng = eStep?.hint1Eng || hcase.hints[0] || 'Read the question carefully.';
    const h2Eng = eStep?.hint2Eng || hcase.hints[1] || 'Look for keywords or numbers in the step.';
    const h3Eng = eStep?.hint3Eng || hcase.hints[2] || (gradeAdaptation ? `Tip: ${gradeAdaptation}` : 'Try thinking step by step!');
    const expEng = eStep?.explainEng || engCase?.explainEng?.messageEng || hcase.explain_another_way?.message || s.tutor_question;
    const analogyEng = eStep?.analogyEng || engCase?.explainEng?.questionEng || hcase.explain_another_way?.question || '';
    const analogyTitle = engCase?.titleEng || hcase.concept || 'Helpful Explanation';

    // Option & answer resolution for science & interactive cases
    let stepOptions: string[] | undefined = undefined;
    let stepInputFormat: 'mcq' | 'number' | 'text' = 'text';
    let stepCorrectAnswer = s.expected_student_answer;

    if (hcase.subject === 'science') {
      const p8Match = targetCaseId.match(/science_p8_([a-z]+)/);
      if (p8Match) {
        const p8Animal = p8Match[1];
        const p8Features = ['vertebrate', 'feathers', 'hump_on_back', 'pincers', 'wings'];
        const feat = p8Features[idx];
        const hasFeat = P8_ANIMAL_ANSWERS[p8Animal]?.[feat] ?? (s.expected_student_answer.toLowerCase() === 'yes');
        stepCorrectAnswer = hasFeat ? 'Yes' : 'No';
        stepOptions = ['✓ មាន (Yes)', '✗ គ្មាន (No)'];
        stepInputFormat = 'mcq';
      } else if (SCIENCE_STEP_OPTIONS[targetCaseId]?.[s.step]) {
        stepOptions = SCIENCE_STEP_OPTIONS[targetCaseId][s.step];
        stepInputFormat = 'mcq';
      }
    }

    // Step options from English pedagogy if not set yet (e.g. multiple choice math steps)
    if (!stepOptions && eStep?.options && eStep.options.length > 0) {
      stepOptions = eStep.options;
      stepInputFormat = 'mcq';
    }

    return {
      id: `${targetCaseId}-step-${s.step}`,
      stepNumber: s.step,
      totalSteps: totalSteps,
      questionKhmer: qKhmer,
      questionEng: qEng,
      inputFormat: stepInputFormat,
      ...(stepOptions ? { options: stepOptions } : {}),
      correctAnswer: stepCorrectAnswer,
      ...(eStep?.acceptableAnswers ? { acceptableAnswers: eStep.acceptableAnswers } : {}),
      socraticPromptKhmer: socraticKhmer,
      socraticPromptEng: socraticEng,
      hint1: {
        khmer: h1Khmer,
        eng: h1Eng,
      },
      hint2: {
        khmer: h2Khmer,
        eng: h2Eng,
      },
      hint3: {
        titleKhmer: 'ឧទាហរណ៍ជំនួយ',
        titleEng: 'Helpful Example',
        exampleKhmer: h3Khmer,
        exampleEng: h3Eng,
      },
      explainDifferently: {
        simpleKhmer: expKhmer,
        simpleEng: expEng,
        analogyTitle: analogyTitle,
        analogyKhmer: khmerCase?.explainKhmer?.questionKhmer || hcase.explain_another_way?.question || '',
        analogyEng: analogyEng,
        analogyType: 'apples' as const,
      },
    };
  });

  const finalImage = worksheetImage || problem.imageUri;

  return {
    ...problem,
    id: targetCaseId,
    problemStatementKhmer: khmerCase?.statementKhmer || hcase.original_question,
    problemStatementEng: engCase?.statementEng || hcase.original_question,
    visualData: hcase.visual_data,
    ...(finalImage ? { imageUri: finalImage } : {}),
    steps,
  };
}

/**
 * Returns the complete list of hardcoded exercises for Math or Science,
 * strictly focused on early primary (Grade 1 - 3).
 * Prevents loading any exercises higher than Grade 3.
 */
export function getHardcodedProblemsBySubject(
  subject: 'math' | 'science',
  grade: number = 2
): { problems: HomeworkProblem[]; imageUri: string } {
  // Strictly clamp grade between Grade 1 and Grade 3
  const targetGrade = Math.min(Math.max(grade || 2, 1), 3);
  let queueKey = 'page_1_homework_1';

  if (subject === 'math') {
    if (targetGrade <= 2) {
      queueKey = 'page_1_homework_1';
    } else {
      queueKey = 'page_8_homework_8';
    }
  } else {
    // Science queue selection: Grade 1-2 (senses & living) or Grade 3 (plants, habitats & matter)
    if (targetGrade <= 2) {
      queueKey = 'grade_1_senses_and_body';
    } else {
      queueKey = 'grade_2_3_plants_and_matter';
    }
  }

  const queueMeta = subject === 'math' ? MATH_QUEUES[queueKey] : SCIENCE_QUEUES[queueKey];
  const imageUri = WORKSHEET_IMAGES[queueKey] || '';

  if (!queueMeta || !queueMeta.exercise_ids) {
    return { problems: [], imageUri };
  }

  const problems: HomeworkProblem[] = queueMeta.exercise_ids
    .map((caseId, idx) => {
      const hcase = ALL_HARDCODED_CASES[caseId];
      if (!hcase) return null;
      const khmerData = getKhmerCaseData(caseId);
      const engCase = getEnglishCaseData(caseId);

      let titleEng = engCase?.titleEng || `Exercise ${idx + 1}`;
      let titleKhmer = `លំហាត់ទី ${idx + 1}`;

      if (subject === 'math') {
        const expr = hcase.original_question || hcase.ocr_style_input?.normalized_text || '';
        titleEng = engCase?.titleEng || `${idx + 1}. ${expr}`;
        titleKhmer = `លំហាត់ ${idx + 1}៖ ${khmerData?.statementKhmer || expr}`;
      } else {
        const scienceTitleMap: Record<string, { en: string; km: string }> = {
          science_g1_eyes: { en: 'Eyes & Sight', km: 'ភ្នែក និងការមើលឃើញ' },
          science_g1_ears: { en: 'Ears & Hearing', km: 'ត្រចៀក និងការស្តាប់ឮ' },
          science_g1_nose: { en: 'Nose & Smell', km: 'ច្រមុះ និងការហិតក្លិន' },
          science_g1_tongue: { en: 'Tongue & Taste', km: 'អណ្តាត និងការភ្លក្សរសជាតិ' },
          science_g1_hands: { en: 'Skin & Touch', km: 'ស្បែក និងការប៉ះដឹង' },
          science_g1_living: { en: 'Living vs Non-Living', km: 'ភាវៈរស់ និងភាវៈឥតជីវិត' },
          science_g2_plant_needs: { en: 'What Plants Need', km: 'តម្រូវការរបស់រុក្ខជាតិ' },
          science_g2_plant_parts: { en: 'Plant Parts', km: 'ផ្នែកសំខាន់ៗនៃរុក្ខជាតិ' },
          science_g2_habitats: { en: 'Animal Habitats', km: 'ជម្រកធម្មជាតិរបស់សត្វ' },
          science_g3_matter_ice: { en: 'Ice & Melting', km: 'ទឹកកក និងការរលាយ' },
          science_g3_matter_states: { en: 'States of Matter', km: 'សភាពនៃរូបធាតុ' },
          science_g3_animal_diet: { en: 'Animal Diets', km: 'របបអាហារសត្វ' },
        };

        const animalMatch = caseId.match(/science_p8_([a-z]+)/);
        const animalName = animalMatch ? animalMatch[1] : '';
        const animalMap: Record<string, { en: string; km: string }> = {
          flamingo: { en: 'Flamingo', km: 'សត្វផ្លាមីងហ្គោ' },
          lobster: { en: 'Lobster', km: 'សត្វបង្កង' },
          camel: { en: 'Camel', km: 'សត្វអូដ្ឋ' },
          giraffe: { en: 'Giraffe', km: 'សត្វហ្ស៊ីរ៉ាហ្វ' },
          slug: { en: 'Slug', km: 'ខ្យងដង្កូវឥតសម្បក' },
          moth: { en: 'Moth', km: 'មេអំបៅរាត្រី' },
        };

        if (scienceTitleMap[caseId]) {
          titleEng = `${idx + 1}. ${scienceTitleMap[caseId].en}`;
          titleKhmer = `លំហាត់ ${idx + 1}៖ ${scienceTitleMap[caseId].km}`;
        } else if (animalName && animalMap[animalName]) {
          titleEng = animalMap[animalName].en;
          titleKhmer = animalMap[animalName].km;
        } else {
          titleEng = hcase.concept || `Exercise ${idx + 1}`;
          titleKhmer = khmerData?.statementKhmer?.slice(0, 25) || `លំហាត់ទី ${idx + 1}`;
        }
      }

      // Strictly map problem grade to Grade 1 - 3
      let resolvedGrade: Grade = 2;
      if (caseId.startsWith('science_g1_')) resolvedGrade = 1;
      else if (caseId.startsWith('science_g2_')) resolvedGrade = 2;
      else if (caseId.startsWith('science_g3_')) resolvedGrade = 3;
      else if (caseId.startsWith('math_p1_')) resolvedGrade = (targetGrade <= 2 ? (targetGrade as Grade) : 2);
      else if (caseId.startsWith('math_p8_')) resolvedGrade = 3;
      else resolvedGrade = (targetGrade as Grade);

      const baseProblem: HomeworkProblem = {
        id: caseId,
        titleEng,
        titleKhmer,
        grade: resolvedGrade,
        subject: hcase.subject as Subject,
        problemStatementKhmer: khmerData?.statementKhmer || hcase.original_question,
        problemStatementEng: hcase.original_question,
        imageUri,
        visualData: hcase.visual_data,
        concept: hcase.concept,
        steps: [],
      };

      return enrichProblemFromCase(baseProblem, resolvedGrade);
    })
    .filter(Boolean) as HomeworkProblem[];

  return { problems, imageUri };
}



