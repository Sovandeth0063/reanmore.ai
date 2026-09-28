import { StepItem, Language } from '../types';

export interface ResolvedStepHints {
  hint1: string;
  hint2: string;
  hint3Title: string;
  hint3Example: string;
  simpleExplanation: string;
  analogyTitle: string;
  analogyExplanation: string;
  allHints: string[];
}

/**
 * Strips markdown asterisks, backticks, blockquotes, and header symbols.
 */
function cleanMd(val: any): string {
  if (!val) return '';
  if (typeof val !== 'string') return String(val);
  const text = val
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/^>\s?/gm, '')
    .replace(/^#+\s?/gm, '')
    .replace(/`([^`]+)`/g, '$1')
    .trim();

  // Filter out any mock LLM testing artifacts or placeholder strings
  if (
    /mock\s*llm/i.test(text) ||
    text === 'Mock LLM generated response.' ||
    /mock\s+response/i.test(text)
  ) {
    return '';
  }
  return text;
}

/**
 * Robustly extracts and normalizes hints and explanations for ANY StepItem,
 * whether it originates from:
 * 1. Hardcoded mock cases (with rich hint1, hint2, hint3, explainDifferently objects)
 * 2. Backend Orchestrator Socratic steppers (with hints array, clue, helpful_example, your_turn)
 * 3. Scanned VLM / OCR exercises (with prompt, sub_questions, mission)
 * 4. Synthesized fallback steps (regex parsed from conversational LLM output)
 */
export function resolveStepHints(step?: StepItem | any, language: Language = 'km'): ResolvedStepHints {
  const isKhmer = language === 'km';
  if (!step) {
    return {
      hint1: isKhmer ? 'សូមអានសំណួរដោយប្រុងប្រយ័ត្ន។' : 'Read the question carefully.',
      hint2: isKhmer ? 'គិតអំពីលេខ ឬពាក្យគន្លឹះក្នុងសំណួរ។' : 'Look at key numbers and words in the question.',
      hint3Title: isKhmer ? 'វិធីដោះស្រាយ' : 'Guided Solution',
      hint3Example: isKhmer ? 'បំបែកលំហាត់ជាជំហានតូចៗដើម្បីគណនា។' : 'Break down the problem into smaller steps.',
      simpleExplanation: isKhmer ? 'តោះដោះស្រាយជាមួយគ្នា មួយជំហានម្តងៗ!' : "Let's solve this together step by step!",
      analogyTitle: isKhmer ? 'ជំនួយការគិត' : 'Thinking Helper',
      analogyExplanation: isKhmer ? 'ស្រមៃមើលរូបភាពជាក់ស្តែងដើម្បីងាយយល់។' : 'Visualize concrete examples to make it easy to grasp.',
      allHints: [],
    };
  }

  const raw = step as any;

  // Extract raw strings from hints array if available
  const rawHintsList: string[] = [];
  if (Array.isArray(raw.hints)) {
    raw.hints.forEach((h: any) => {
      if (typeof h === 'string' && h.trim()) {
        rawHintsList.push(cleanMd(h));
      } else if (h && typeof h === 'object') {
        const text = isKhmer ? (h.khmer || h.textKhmer || h.text) : (h.eng || h.textEng || h.text);
        if (text) rawHintsList.push(cleanMd(text));
      }
    });
  }

  // --- Hint 1 (Small Clue / Focus) ---
  let h1 = '';
  if (raw.hint1) {
    if (typeof raw.hint1 === 'string') {
      h1 = cleanMd(raw.hint1);
    } else if (typeof raw.hint1 === 'object') {
      h1 = cleanMd(isKhmer ? (raw.hint1.khmer || raw.hint1.eng) : (raw.hint1.eng || raw.hint1.khmer));
    }
  }
  if (!h1 && rawHintsList.length > 0) {
    h1 = rawHintsList[0];
  }
  if (!h1 && (raw.clue || raw.clueKhmer || raw.clue_khmer)) {
    h1 = cleanMd(isKhmer ? (raw.clueKhmer || raw.clue_khmer || raw.clue) : (raw.clue || raw.clueEng));
  }
  if (!h1) {
    const focusContext = cleanMd(raw.mission || raw.questionKhmer || raw.questionEng || '');
    h1 = isKhmer
      ? (focusContext ? `សូមពិនិត្យមើលចំណុចនេះ៖ ${focusContext}` : 'ចាប់ផ្ដើមដោយពិនិត្យមើលសំណួរក្នុងជំហាននេះដោយយកចិត្តទុកដាក់។')
      : (focusContext ? `Focus on this key part: ${focusContext}` : 'Start by reading the question carefully and finding the keywords.');
  }

  // --- Hint 2 (Bigger Hint / Guided Strategy) ---
  let h2 = '';
  if (raw.hint2) {
    if (typeof raw.hint2 === 'string') {
      h2 = cleanMd(raw.hint2);
    } else if (typeof raw.hint2 === 'object') {
      h2 = cleanMd(isKhmer ? (raw.hint2.khmer || raw.hint2.eng) : (raw.hint2.eng || raw.hint2.khmer));
    }
  }
  if (!h2 && rawHintsList.length > 1) {
    h2 = rawHintsList[1];
  }
  if (!h2 && (raw.helpfulExample || raw.helpful_example || raw.helpfulExampleKhmer)) {
    h2 = cleanMd(isKhmer ? (raw.helpfulExampleKhmer || raw.helpfulExample || raw.helpful_example) : (raw.helpfulExample || raw.helpful_example));
  }
  if (!h2 && (raw.yourTurn || raw.your_turn)) {
    const yt = cleanMd(raw.yourTurn || raw.your_turn);
    h2 = isKhmer ? `គិតអំពីសំណួរនេះ៖ ${yt}` : `Think about this: ${yt}`;
  }
  if (!h2) {
    h2 = isKhmer
      ? 'បំបែកលំហាត់ជាជំហានតូចៗ ឬសាកល្បងគណនាម្តងមួយលេខ។'
      : 'Break the problem down into smaller parts or calculate step by step.';
  }

  // --- Hint 3 (Example / Concrete Analogy) ---
  let h3Title = isKhmer ? 'ឧទាហរណ៍ និងវិធីដោះស្រាយ' : 'Example & Guidance';
  let h3Example = '';
  if (raw.hint3) {
    if (typeof raw.hint3 === 'string') {
      h3Example = cleanMd(raw.hint3);
    } else if (typeof raw.hint3 === 'object') {
      const title = isKhmer ? (raw.hint3.titleKhmer || raw.hint3.titleEng) : (raw.hint3.titleEng || raw.hint3.titleKhmer);
      if (title) h3Title = cleanMd(title);
      h3Example = cleanMd(isKhmer ? (raw.hint3.exampleKhmer || raw.hint3.exampleEng) : (raw.hint3.exampleEng || raw.hint3.exampleKhmer));
    }
  }
  if (!h3Example && rawHintsList.length > 2) {
    h3Example = rawHintsList[2];
  }
  if (!h3Example && (raw.helpfulExample || raw.helpful_example)) {
    h3Example = cleanMd(raw.helpfulExample || raw.helpful_example);
  }
  if (!h3Example) {
    const qText = cleanMd(raw.questionKhmer || raw.questionEng || raw.prompt || '');
    h3Example = isKhmer
      ? (qText ? `សាកល្បងគិត៖ ប្រសិនបើយើងពិនិត្យលើ ${qText} តើយើងអាចធ្វើតាមវិធីណាខ្លះ?` : 'សាកល្បងសរសេរលេខ ឬរូបមន្តនៅលើក្រដាសព្រាងដើម្បីងាយស្រួលផ្ទៀងផ្ទាត់!')
      : (qText ? `Try thinking: If we look at "${qText}", what pattern or operation can we apply?` : 'Write down the steps or numbers on scratch paper to clearly see the solution!');
  }

  // --- Simple Explanation ---
  let simpleExp = '';
  if (raw.explainDifferently) {
    if (typeof raw.explainDifferently === 'string') {
      simpleExp = cleanMd(raw.explainDifferently);
    } else if (typeof raw.explainDifferently === 'object') {
      simpleExp = cleanMd(isKhmer ? (raw.explainDifferently.simpleKhmer || raw.explainDifferently.simpleEng) : (raw.explainDifferently.simpleEng || raw.explainDifferently.simpleKhmer));
    }
  }
  if (!simpleExp && (raw.clue || raw.helpfulExample || raw.helpful_example)) {
    const parts = [raw.clue, raw.helpfulExample || raw.helpful_example].filter(Boolean).map(cleanMd);
    simpleExp = parts.join(' ');
  }
  if (!simpleExp && (raw.mission || raw.questionKhmer || raw.questionEng)) {
    const m = cleanMd(raw.mission || raw.questionKhmer || raw.questionEng);
    simpleExp = isKhmer ? `គោលដៅនៃជំហាននេះគឺ៖ ${m}` : `The goal of this step is: ${m}`;
  }
  if (!simpleExp) {
    simpleExp = isKhmer
      ? 'តោះចាប់ផ្តើមដោះស្រាយជាមួយគ្នា មួយជំហានម្តងៗដោយភាពជឿជាក់!'
      : "Let's solve this together, one step at a time with confidence!";
  }

  // --- Analogy & Visual ---
  let anTitle = isKhmer ? 'ឧទាហរណ៍រូបភាព' : 'Visual Analogy';
  let anExp = '';
  if (raw.explainDifferently && typeof raw.explainDifferently === 'object') {
    const t = raw.explainDifferently.analogyTitle;
    if (t) anTitle = cleanMd(t);
    anExp = cleanMd(isKhmer ? (raw.explainDifferently.analogyKhmer || raw.explainDifferently.analogyEng) : (raw.explainDifferently.analogyEng || raw.explainDifferently.analogyKhmer));
  }
  if (!anExp && (raw.helpfulExample || raw.helpful_example)) {
    anExp = cleanMd(raw.helpfulExample || raw.helpful_example);
  }
  if (!anExp) {
    anExp = isKhmer
      ? 'ស្រមៃមើលចំនួន ឬរូបភាពជាក់ស្តែង (ដូចជាផ្លែឈើ ឬដុំគ្រួស) ដើម្បីជួយឱ្យការគិតកាន់តែច្បាស់លាស់។'
      : 'Picture real objects (like apples or blocks) in your mind to make the concept clear and intuitive.';
  }

  const allHints = [h1, h2, h3Example].filter(Boolean);

  return {
    hint1: h1,
    hint2: h2,
    hint3Title: h3Title,
    hint3Example: h3Example,
    simpleExplanation: simpleExp,
    analogyTitle: anTitle,
    analogyExplanation: anExp,
    allHints,
  };
}
