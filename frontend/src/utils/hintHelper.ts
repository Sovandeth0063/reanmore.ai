import { StepItem, Language } from '../types';

export interface ResolvedStepHints {
  hint1: string;
  hint2: string;
  hint3Title?: string;
  hint3Example?: string;
  simpleExplanation: string;
  analogyTitle: string;
  analogyExplanation: string;
  visualReference?: string;
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
 * Robustly extracts and normalizes hints and explanations for ANY StepItem.
 * - Hint: Provides a short, grade-appropriate clue that guides students toward the answer without revealing it.
 * - Explain Differently: Rephrases and explains the current step's guiding question in simpler language,
 *   refers to the existing visual on the card when helpful, and provides a familiar analogy only when
 *   it genuinely improves understanding.
 */
export function resolveStepHints(
  step?: StepItem | any,
  language: Language = 'en',
  _grade: number = 2
): ResolvedStepHints {
  const isKhmer = language === 'km';
  if (!step) {
    return {
      hint1: isKhmer ? 'សូមអានសំណួរដោយប្រុងប្រយ័ត្ន។' : 'Read the question carefully.',
      hint2: isKhmer ? 'គិតអំពីលេខ ឬពាក្យគន្លឹះក្នុងសំណួរ។' : 'Look at key numbers and words in the question.',
      hint3Title: '',
      hint3Example: '',
      simpleExplanation: isKhmer ? 'តោះដោះស្រាយជាមួយគ្នា មួយជំហានម្តងៗ!' : "Let's solve this together step by step!",
      analogyTitle: '',
      analogyExplanation: '',
      visualReference: '',
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

  // --- Hint 1 (Small Clue / Focus: guides student without revealing answer) ---
  let h1 = '';
  if (rawHintsList.length > 0) {
    h1 = rawHintsList[0];
  } else if (raw.hint1) {
    if (typeof raw.hint1 === 'string') {
      h1 = cleanMd(raw.hint1);
    } else if (typeof raw.hint1 === 'object') {
      h1 = cleanMd(isKhmer ? (raw.hint1.khmer || raw.hint1.eng) : (raw.hint1.eng || raw.hint1.khmer));
    }
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

  // --- Hint 2 (Stepping-Stone Clue / Strategy: guides toward answer without revealing it) ---
  let h2 = '';
  if (rawHintsList.length > 1) {
    h2 = rawHintsList[1];
  } else if (raw.hint2) {
    if (typeof raw.hint2 === 'string') {
      h2 = cleanMd(raw.hint2);
    } else if (typeof raw.hint2 === 'object') {
      h2 = cleanMd(isKhmer ? (raw.hint2.khmer || raw.hint2.eng) : (raw.hint2.eng || raw.hint2.khmer));
    }
  }
  if (!h2 && (raw.clue || raw.clueKhmer)) {
    const cl = cleanMd(raw.clue || raw.clueKhmer);
    if (cl && cl !== h1) h2 = cl;
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

  // Pure answer-safe hints array (no worked examples)
  const allHints = [h1, h2].filter(Boolean);

  // --- Explain Differently: Rephrase and explain the current step's guiding question ---
  const guidingQuestion = cleanMd(
    raw.yourTurn ||
    raw.your_turn ||
    (isKhmer ? raw.socraticPromptKhmer : raw.socraticPromptEng) ||
    raw.socraticPromptEng ||
    (isKhmer ? raw.questionKhmer : raw.questionEng) ||
    raw.questionEng ||
    raw.mission ||
    ''
  );

  const stepMission = cleanMd(
    (isKhmer ? raw.questionKhmer : raw.questionEng) ||
    raw.mission ||
    raw.title ||
    ''
  );

  const qLower = `${guidingQuestion} ${stepMission}`.toLowerCase();
  const visual = raw.visualData || raw.visual_data || raw.visual;
  const vType = visual ? String(visual.type || '').toLowerCase() : '';
  const onLinePhrase = vType === 'number_line' ? ' on the number line' : '';

  let simpleExp = '';
  // Check if explicit custom explainDifferently is already provided and not generic
  if (raw.explainDifferently) {
    if (typeof raw.explainDifferently === 'string' && raw.explainDifferently.trim().length > 20) {
      simpleExp = cleanMd(raw.explainDifferently);
    } else if (typeof raw.explainDifferently === 'object') {
      const exp = isKhmer 
        ? (raw.explainDifferently.simpleKhmer || raw.explainDifferently.simpleEng) 
        : (raw.explainDifferently.simpleEng || raw.explainDifferently.simpleKhmer);
      if (exp && exp.trim().length > 20 && exp !== raw.mission && exp !== raw.questionEng) {
        simpleExp = cleanMd(exp);
      }
    }
  }

  // Synthesize concise, grade-appropriate rephrasing (1-2 short sentences)
  if (!simpleExp) {
    const nums = (guidingQuestion.match(/\b\d+\b/g) || []).map(Number);

    if (qLower.includes('subtract') || qLower.includes('minus') || qLower.includes('-') || qLower.includes('take away') || qLower.includes('backward')) {
      if (nums.length >= 2) {
        simpleExp = isKhmer
          ? `ចាប់ផ្ដើមពី ${nums[0]} ហើយរាប់ថយក្រោយ ${nums[1]} ជំហាន${vType === 'number_line' ? ' លើបន្ទាត់លេខ' : ''}។ តើអ្នកទៅដល់លេខណា?`
          : `Start at ${nums[0]} and count backward ${nums[1]} steps${onLinePhrase}. Where do you land?`;
      } else if (nums.length === 1) {
        simpleExp = isKhmer
          ? `រាប់ថយក្រោយ ${nums[0]} ជំហាន${vType === 'number_line' ? ' លើបន្ទាត់លេខ' : ''}។ តើនៅសល់ប៉ុន្មាន?`
          : `Count backward ${nums[0]} steps${onLinePhrase}. How many are left?`;
      } else {
        simpleExp = isKhmer
          ? 'រាប់ថយក្រោយដើម្បីដឹងថានៅសល់ប៉ុន្មាន!'
          : 'Count backward to see what is left!';
      }
    } else if (qLower.includes('put together') || qLower.includes('what two numbers') || qLower.includes('which two numbers') || qLower.includes('first two')) {
      if (nums.length >= 2) {
        simpleExp = isKhmer
          ? `មើលលេខពីរដំបូង (${nums[0]} និង ${nums[1]})។ តើបូកបញ្ចូលគ្នាបានប៉ុន្មាន?`
          : `Look at the first two numbers, ${nums[0]} and ${nums[1]}. What do you get when you put them together?`;
      } else {
        simpleExp = isKhmer
          ? 'រកមើលលេខពីរដែលនៅសងខាងសញ្ញាបូក ➕!'
          : 'Look at the numbers on either side of the plus sign ➕ to see what to combine.';
      }
    } else if (qLower.includes('add') || qLower.includes('plus') || qLower.includes('+') || qLower.includes('more') || qLower.includes('forward')) {
      if (nums.length >= 2) {
        simpleExp = isKhmer
          ? `ចាប់ផ្ដើមពី ${nums[0]} ហើយរាប់ទៅមុខ ${nums[1]} ជំហាន${vType === 'number_line' ? ' លើបន្ទាត់លេខ' : ''}។ តើអ្នកទៅដល់លេខណា?`
          : `Start at ${nums[0]} and count forward ${nums[1]} steps${onLinePhrase}. Where do you land?`;
      } else if (nums.length === 1) {
        simpleExp = isKhmer
          ? `រាប់ទៅមុខ ${nums[0]} ជំហាន${vType === 'number_line' ? ' លើបន្ទាត់លេខ' : ''}។ តើទទួលបានប៉ុន្មាន?`
          : `Count forward ${nums[0]} steps${onLinePhrase}. Where do you land?`;
      } else {
        simpleExp = isKhmer
          ? 'បូកចំនួនទាំងពីរនេះបញ្ចូលគ្នាដើម្បីរកចំនួនសរុប!'
          : 'Add these amounts together to find the total!';
      }
    } else if (qLower.includes('ones') || qLower.includes('tens') || qLower.includes('regroup') || qLower.includes('trade')) {
      if (qLower.includes('ones')) {
        simpleExp = isKhmer
          ? 'រាប់ដុំរាយនៅខាងស្ដាំ។ តើយើងមានដុំរាយប៉ុន្មាន?'
          : 'Look at the ones column on the right. How many single blocks do we have?';
      } else {
        simpleExp = isKhmer
          ? 'តើដុំរាយមានដល់ ១០ ឬច្រើនជាងនេះដើម្បីបង្កើតជាខ្ទង់ដប់ទេ?'
          : 'Do we have 10 or more loose pieces to make a new ten?';
      }
    } else if (qLower.includes('multiply') || qLower.includes('times') || qLower.includes('×') || (qLower.includes('group') && !qLower.includes('put together'))) {
      if (nums.length >= 2) {
        simpleExp = isKhmer
          ? `រាប់លោត ${nums[0]} ក្រុម ដែលក្រុមនីមួយៗមាន ${nums[1]}។`
          : `Skip-count ${nums[0]} equal groups of ${nums[1]}. Where do you land?`;
      } else {
        simpleExp = isKhmer
          ? 'រាប់លោតតាមក្រុមនីមួយៗដើម្បីរកចំនួនសរុប!'
          : 'Skip-count each equal group to find the total!';
      }
    } else if (qLower.includes('fraction') || qLower.includes('slice') || qLower.includes('shaded') || qLower.includes('/')) {
      simpleExp = isKhmer
        ? 'រាប់ចំនួនចំណែកដែលផាត់ពណ៌ ធៀបនឹងចំណែកស្មើៗគ្នាទាំងអស់។'
        : 'Count how many parts are colored out of all the equal parts.';
    } else if (qLower.includes('solid') || qLower.includes('liquid') || qLower.includes('gas') || qLower.includes('matter')) {
      simpleExp = isKhmer
        ? 'គិតមើលថាតើវាមានរាងរឹងមាំដូចទឹកកក ឬអាចហូរដូចទឹក?'
        : 'Think about whether it stays firm like ice, or pours like water.';
    } else if (guidingQuestion) {
      simpleExp = guidingQuestion;
    } else {
      simpleExp = isKhmer
        ? 'តោះធ្វើឱ្យវាកាន់តែងាយ! ឆ្លើយមួយជំហានម្តងៗ។'
        : "Let's make it easier! Take it one step at a time.";
    }
  }

  // --- Visual Reference: Short single-line cue referring to the existing visual on the card ---
  let visualRef = '';
  if (visual && typeof visual === 'object') {
    if (vType === 'number_line') {
      visualRef = isKhmer
        ? 'ប្រើបន្ទាត់លេខនៅលើកាតរបស់អ្នកដើម្បីជួយរាប់។'
        : 'Use the number line on your card to help you.';
    } else if (vType === 'ten_frame') {
      visualRef = isKhmer
        ? 'ប្រើរូបក្រឡា ១០ នៅលើកាតរបស់អ្នកដើម្បីជួយរាប់។'
        : 'Use the ten-frame on your card to help you.';
    } else if (vType === 'place_value_blocks' || vType === 'base_ten_blocks') {
      visualRef = isKhmer
        ? 'ប្រើដុំប្លុកនៅលើកាតរបស់អ្នកដើម្បីជួយរាប់។'
        : 'Use the blocks on your card to help you.';
    } else if (vType === 'objects') {
      visualRef = isKhmer
        ? 'ប្រើរូបភាពនៅលើកាតរបស់អ្នកដើម្បីជួយរាប់។'
        : 'Use the pictures on your card to help you.';
    } else if (vType === 'bar_model' || vType === 'fraction_bar') {
      visualRef = isKhmer
        ? 'ប្រើរបារនៅលើកាតរបស់អ្នកដើម្បីជួយមើល។'
        : 'Use the bar diagram on your card to help you.';
    } else if (vType === 'array_grid') {
      visualRef = isKhmer
        ? 'ប្រើក្រឡាចត្រង្គនៅលើកាតរបស់អ្នកដើម្បីជួយរាប់។'
        : 'Use the grid on your card to help you.';
    } else {
      visualRef = isKhmer
        ? 'ប្រើរូបភាពនៅលើកាតរបស់អ្នកដើម្បីជួយអ្នក។'
        : 'Use the picture on your card to help you.';
    }
  }

  // --- Familiar Analogy: Only when it genuinely improves understanding (optional extra help) ---
  let anTitle = '';
  let anExp = '';

  if (raw.explainDifferently && typeof raw.explainDifferently === 'object') {
    anTitle = cleanMd(isKhmer ? (raw.explainDifferently.analogyKhmerTitle || raw.explainDifferently.analogyTitle) : (raw.explainDifferently.analogyTitle || raw.explainDifferently.analogyEngTitle));
    anExp = cleanMd(isKhmer ? (raw.explainDifferently.analogyKhmer || raw.explainDifferently.analogyEng) : (raw.explainDifferently.analogyEng || raw.explainDifferently.analogyKhmer));
  }

  if (!anExp) {
    if (qLower.includes('ones') || qLower.includes('tens') || qLower.includes('regroup') || qLower.includes('trade')) {
      anTitle = isKhmer ? 'ប្រអប់នំឃុកឃី' : 'Cookie Box';
      anExp = isKhmer
        ? 'ស្រមៃមើលនំ ១០ ដុំ រៀបចូលពេញប្រអប់ ១ ហើយនំដែលនៅសល់ក្រៅប្រអប់ជាដុំរាយ!'
        : 'Imagine 10 cookies fill 1 full box, and any leftover cookies stay out as loose ones!';
    } else if (qLower.includes('put together') || qLower.includes('add') || qLower.includes('plus') || qLower.includes('combine')) {
      anTitle = isKhmer ? 'កន្ត្រកប្រដាប់ក្មេងលេង' : 'Toy Basket';
      anExp = isKhmer
        ? 'ស្រមៃមើលការប្រមូលប្រដាប់ក្មេងលេងពីគំនរពីរ ដាក់ចូលទៅក្នុងកន្ត្រកតែមួយ!'
        : 'Imagine gathering toys from two separate piles together into one big basket!';
    } else if (qLower.includes('multiply') || qLower.includes('times') || qLower.includes('×') || (qLower.includes('group') && !qLower.includes('put together'))) {
      anTitle = isKhmer ? 'កង់កង់' : 'Bicycle Wheels';
      anExp = isKhmer
        ? 'គិតអំពីកង់កង់៖ កង់នីមួយៗមានកង់ ២ ដូច្នេះការរាប់កង់ ៣ គឺរាប់លោត ២, ៤, ៦!'
        : 'Think of bicycles: each bike has 2 wheels, so counting 3 bikes is skip-counting: 2, 4, 6!';
    } else if (qLower.includes('subtract') || qLower.includes('minus') || qLower.includes('take away')) {
      anTitle = isKhmer ? 'ការចែករំលែកផ្លែឈើ' : 'Snack Sharing';
      anExp = isKhmer
        ? 'ស្រមៃមើលថាអ្នកមានផ្លែឈើមួយចាន ហើយចែកខ្លះទៅមិត្តភក្តិ—តើនៅសល់ប៉ុន្មានសម្រាប់អ្នក?'
        : 'Imagine having a bowl of cherries and sharing some with a friend—how many are left for you?';
    } else if (qLower.includes('fraction') || qLower.includes('slice')) {
      anTitle = isKhmer ? 'ចំណែកភីហ្សា' : 'Pizza Slices';
      anExp = isKhmer
        ? 'ស្រមៃមើលការកាត់នំភីហ្សាជាចំណែកស្មើៗគ្នា ដើម្បីឱ្យអ្នកគ្រប់គ្នាទទួលបានចំណែកស្មើគ្នា!'
        : 'Imagine cutting a pizza into equal slices so each slice has the exact same amount!';
    } else if (qLower.includes('solid') || qLower.includes('liquid') || qLower.includes('gas')) {
      anTitle = isKhmer ? 'ដំណើរនៃទឹកកក' : 'Ice, Water & Steam';
      anExp = isKhmer
        ? 'ដុំទឹកកកមានរាងរឹង កាលណាក្ដៅរលាយជាទឹក ហើយពេលដាំពុះហុយឡើងលើជាចំហាយ!'
        : 'An ice cube stays firm (solid), in the sun it melts to water (liquid), and when boiled it turns to steam (gas)!';
    }
  }

  return {
    hint1: h1,
    hint2: h2,
    hint3Title: '',
    hint3Example: '',
    simpleExplanation: simpleExp,
    analogyTitle: anTitle,
    analogyExplanation: anExp,
    visualReference: visualRef,
    allHints,
  };
}
