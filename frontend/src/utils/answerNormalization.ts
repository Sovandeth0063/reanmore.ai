/**
 * Answer normalization utilities for student input evaluation.
 * Performs character, numeral, and token normalization across Khmer and English.
 * Pure normalizer: does NOT contain canned answers or exercise-specific mocks.
 */

const KHMER_DIGITS: Record<string, string> = {
  '០': '0', '១': '1', '២': '2', '៣': '3', '៤': '4',
  '៥': '5', '៦': '6', '៧': '7', '៨': '8', '៩': '9'
};

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

export function normalizeAnswer(raw: string): string {
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

export function replaceNumberWords(text: string): string {
  let result = text;
  for (const [word, digit] of Object.entries(NUMBER_WORDS)) {
    const re = new RegExp('(?:^|\\b)' + word + '(?:\\b|$)', 'gi');
    result = result.replace(re, digit);
  }
  return result;
}

export function normalizeWithKhmer(raw: string): string {
  if (!raw) return '';
  const converted = raw.replace(/[០-៩]/g, d => KHMER_DIGITS[d] || d);
  return replaceNumberWords(normalizeAnswer(converted));
}

/**
 * Compares a student answer against an expected answer or acceptable answers list.
 * Evaluates exact match, case insensitivity, numerals, affirmative/negative,
 * MCQ letters, and basic token sets.
 */
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

  // 2b. Option Letter Prefix matching (e.g. "C (ទន្សាយ)" or "គ. សត្វទន្សាយ" vs "C")
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

  // 5. Whole word / phrase containment in either direction
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

export function isAnswerCorrect(studentRaw: string, expectedRaw: string, acceptableAnswers?: string[]): boolean {
  return answersMatch(studentRaw, expectedRaw, acceptableAnswers);
}
