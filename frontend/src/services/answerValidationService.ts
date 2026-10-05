import { StepItem, Language, HomeworkProblem } from '../types';
import { answersMatch, normalizeWithKhmer, isAnswerCorrect } from './hardcodedTutorProvider';
import { cleanBilingualOption } from '../utils/language';

export interface StepValidationResult {
  isCorrect: boolean;
  isDeterministic: boolean;
  feedbackType: 'correct' | 'near_miss' | 'incorrect';
  tutorReplyKhmer: string;
  tutorReplyEng: string;
  hintSuggestion?: {
    level: 1 | 2 | 3;
    textKhmer: string;
    textEng: string;
  } | undefined;
}

/**
 * Fast, deterministic validation and follow-up generator for step answers.
 * Evaluates calculations, numbers, multiple-choice, boolean (yes/no), and synonyms
 * in < 1ms to eliminate slow LLM wait times on wrong answers.
 */
export function fastValidateStepAnswer(
  studentAnswer: string,
  currentStep: StepItem,
  language: Language = 'km',
  activeProblem?: HomeworkProblem,
  currentStepIndex: number = 0
): StepValidationResult {
  const stepNum = currentStep.stepNumber || currentStepIndex + 1;
  const total = activeProblem?.steps?.length || currentStep.totalSteps || 3;
  const nextStep = activeProblem?.steps?.[currentStepIndex + 1];

  const trimmed = studentAnswer.trim();
  const rawStep = currentStep as any;
  const targetExpected = currentStep.correctAnswer || rawStep.expectedAnswer || rawStep.expected_answer || '';
  const cleanedOption = cleanBilingualOption(trimmed, language);
  const expectedClean = cleanBilingualOption(targetExpected, language);

  // 1. Direct match check (answersMatch + bilingual option equality + acceptableAnswers)
  const isDirect = (targetExpected && (
    isAnswerCorrect(trimmed, targetExpected, currentStep.acceptableAnswers) ||
    cleanedOption.toLowerCase() === expectedClean.toLowerCase() ||
    answersMatch(cleanedOption, expectedClean, currentStep.acceptableAnswers) ||
    (currentStep.acceptableAnswers && currentStep.acceptableAnswers.some(acc =>
      answersMatch(trimmed, acc) || answersMatch(cleanedOption, acc)
    ))
  )) || (!targetExpected && trimmed.length > 0 && activeProblem?.steps?.length === 1);

  if (isDirect) {
    let replyKhmer = '';
    let replyEng = '';

    if (nextStep) {
      replyKhmer = `🎉 **ជំហានទី ${stepNum} នៃ ${total} ត្រឹមត្រូវហើយ!**\n\nចម្លើយរបស់អ្នកគឺ **"${trimmed}"** ពិតជាត្រឹមត្រូវល្អណាស់!\n\n👉 **ជំហានទី ${nextStep.stepNumber || currentStepIndex + 2} បន្ទាប់**៖ ${nextStep.questionKhmer || nextStep.questionEng}`;
      replyEng = `🎉 **Step ${stepNum} of ${total} is Correct!**\n\nYour answer **"${trimmed}"** is spot on!\n\n👉 **Next Step ${nextStep.stepNumber || currentStepIndex + 2}**: ${nextStep.questionEng || nextStep.questionKhmer}`;
    } else {
      replyKhmer = `🏆 **អបអរសាទរ! អ្នកបានបញ្ចប់ជំហានទី ${stepNum} នៃ ${total} ទាំងអស់ហើយ!**\n\nចម្លើយចុងក្រោយគឺ **"${trimmed}"** ត្រឹមត្រូវល្អណាស់! ពូកែខ្លាំងណាស់!`;
      replyEng = `🏆 **Congratulations! You completed all ${total} steps!**\n\nYour final answer **"${trimmed}"** is correct! Excellent work!`;
    }

    return {
      isCorrect: true,
      isDeterministic: true,
      feedbackType: 'correct',
      tutorReplyKhmer: replyKhmer,
      tutorReplyEng: replyEng,
    };
  }

  // 2. Numeric / Arithmetic Check (Fast near-miss & off-by-one detection)
  const sNorm = normalizeWithKhmer(trimmed).trim();
  const eNorm = normalizeWithKhmer(targetExpected).trim();
  const numS = parseFloat(sNorm);
  const numE = parseFloat(eNorm);

  const isNumericComparison = !isNaN(numS) && !isNaN(numE);

  if (isNumericComparison) {
    const diff = Math.abs(numS - numE);
    const hint1Kh = currentStep.hint1?.khmer || '';
    const hint1En = currentStep.hint1?.eng || '';

    // Near-miss: off by 1 (e.g. student typed 14 for 9+6=15)
    if (diff === 1) {
      const isUnder = numS < numE;
      const khmerDetail = isUnder
        ? `💡 **ជិតត្រូវហើយ!** ចម្លើយ **"${trimmed}"** គឺខ្វះតែ **១** ទៀតប៉ុណ្ណោះ!`
        : `💡 **ជិតត្រូវហើយ!** ចម្លើយ **"${trimmed}"** គឺលើសតែ **១** ប៉ុណ្ណោះ!`;
      const engDetail = isUnder
        ? `💡 **So close!** Your answer **"${trimmed}"** is just **1** away!`
        : `💡 **So close!** Your answer **"${trimmed}"** is just **1** over!`;

      const actionKh = isUnder
        ? 'សាកល្បងរាប់បន្ថែម ១ ទៀត ឬចុចមើល «តម្រុយ» ខាងក្រោមណា៎! 🍎'
        : 'សាកល្បងដក ១ ចេញ ឬរាប់ឡើងវិញណា៎! 🍎';
      const actionEn = isUnder
        ? 'Try counting on 1 more or tap "Hint" below! 🍎'
        : 'Try taking 1 away or recount carefully! 🍎';

      const replyKhmer = `${khmerDetail}\n\n${hint1Kh ? `👉 **តម្រុយជំនួយ៖** ${hint1Kh}\n\n` : ''}${actionKh}`;
      const replyEng = `${engDetail}\n\n${hint1En ? `👉 **Helpful Clue:** ${hint1En}\n\n` : ''}${actionEn}`;

      return {
        isCorrect: false,
        isDeterministic: true,
        feedbackType: 'near_miss',
        tutorReplyKhmer: replyKhmer,
        tutorReplyEng: replyEng,
        hintSuggestion: hint1Kh ? { level: 1, textKhmer: hint1Kh, textEng: hint1En } : undefined,
      };
    }

    // Near-miss: off by 2
    if (diff === 2) {
      const replyKhmer = `💡 **ជិតដល់ហើយ!** ចម្លើយ **"${trimmed}"** គឺជិតត្រូវណាស់ (ខ្វះតែ ២ ទៀត)!\n\n${hint1Kh ? `👉 **តម្រុយជំនួយ៖** ${hint1Kh}\n\n` : ''}សាកល្បងពិនិត្យមើលរូបភាព ឬរាប់ម្តងទៀតណា៎! 🍎`;
      const replyEng = `💡 **Almost there!** Your answer **"${trimmed}"** is very close (just 2 away)!\n\n${hint1En ? `👉 **Helpful Clue:** ${hint1En}\n\n` : ''}Take another look at the picture and count again! 🍎`;

      return {
        isCorrect: false,
        isDeterministic: true,
        feedbackType: 'near_miss',
        tutorReplyKhmer: replyKhmer,
        tutorReplyEng: replyEng,
        hintSuggestion: hint1Kh ? { level: 1, textKhmer: hint1Kh, textEng: hint1En } : undefined,
      };
    }

    // Off by > 2
    const replyKhmer = `🤔 **ព្យាយាមម្តងទៀតណា៎!** ចម្លើយ **"${trimmed}"** មិនទាន់ត្រឹមត្រូវឡើយ។\n\n${hint1Kh ? `💡 **តម្រុយជួយអ្នក៖** ${hint1Kh}\n\n` : ''}ចុចមើលប៊ូតុង **«តម្រុយ»** ខាងក្រោម ឬសាកល្បងរាប់ម្តងទៀតដោយប្រុងប្រយ័ត្ន!`;
    const replyEng = `🤔 **Try again!** **"${trimmed}"** isn't quite right.\n\n${hint1En ? `💡 **Helpful Clue:** ${hint1En}\n\n` : ''}Tap the **"Hint"** button below or try counting again carefully!`;

    return {
      isCorrect: false,
      isDeterministic: true,
      feedbackType: 'incorrect',
      tutorReplyKhmer: replyKhmer,
      tutorReplyEng: replyEng,
      hintSuggestion: hint1Kh ? { level: 1, textKhmer: hint1Kh, textEng: hint1En } : undefined,
    };
  }

  // 3. Multiple Choice & Preset Options Check
  const isMCQ = Boolean((currentStep.options && currentStep.options.length > 0) || currentStep.inputFormat === 'mcq');
  if (isMCQ) {
    const hint1Kh = currentStep.hint1?.khmer || '';
    const hint1En = currentStep.hint1?.eng || '';

    const replyKhmer = `🤔 **មិនទាន់ត្រឹមត្រូវទេ!** ជម្រើស **"${cleanedOption}"** មិនទាន់ជាចម្លើយត្រឹមត្រូវឡើយ។\n\n${hint1Kh ? `💡 **តម្រុយជំនួយ៖** ${hint1Kh}\n\n` : ''}សូមពិនិត្យមើលជម្រើសដទៃទៀត ឬចុចមើល «តម្រុយ» ដើម្បីជួយអ្នក!`;
    const replyEng = `🤔 **Not quite!** **"${cleanedOption}"** isn't the right choice.\n\n${hint1En ? `💡 **Helpful Clue:** ${hint1En}\n\n` : ''}Take another look at the other options or tap "Hint" to help you!`;

    return {
      isCorrect: false,
      isDeterministic: true,
      feedbackType: 'incorrect',
      tutorReplyKhmer: replyKhmer,
      tutorReplyEng: replyEng,
      hintSuggestion: hint1Kh ? { level: 1, textKhmer: hint1Kh, textEng: hint1En } : undefined,
    };
  }

  // 4. Affirmative / Negative (Yes/No, មាន/គ្មាន) Check
  const affirmative = new Set([
    'yes', 'true', 'correct', 'y', 't', 'has', '✓', 'check',
    'បាទ', 'ចាស', 'មាន', 'ពិតជាមាន', 'ត្រូវ', 'ពិតមែន', 'បាទ/ចាស', '✓ មាន'
  ]);
  const negative = new Set([
    'no', 'false', 'incorrect', 'n', 'f', 'none', '✗', 'x',
    'ទេ', 'គ្មាន', 'មិនមាន', 'អត់', 'ខុស', 'មិនពិត', '✗ គ្មាន'
  ]);

  const sLower = sNorm.toLowerCase();
  const eLower = eNorm.toLowerCase();
  const isBinaryAffirmative = (affirmative.has(sLower) || negative.has(sLower)) &&
                              (affirmative.has(eLower) || negative.has(eLower));

  if (isBinaryAffirmative) {
    const hint1Kh = currentStep.hint1?.khmer || '';
    const hint1En = currentStep.hint1?.eng || '';

    const replyKhmer = `🤔 **មិនទាន់ត្រឹមត្រូវទេ!** ចម្លើយ **"${trimmed}"** មិនទាន់ត្រឹមត្រូវទេ។\n\n${hint1Kh ? `💡 **តម្រុយ៖** ${hint1Kh}\n\n` : ''}សាកល្បងពិនិត្យមើលលក្ខណៈម្តងទៀតណា៎!`;
    const replyEng = `🤔 **Not quite!** **"${trimmed}"** is not correct.\n\n${hint1En ? `💡 **Clue:** ${hint1En}\n\n` : ''}Check the details once more and try again!`;

    return {
      isCorrect: false,
      isDeterministic: true,
      feedbackType: 'incorrect',
      tutorReplyKhmer: replyKhmer,
      tutorReplyEng: replyEng,
      hintSuggestion: hint1Kh ? { level: 1, textKhmer: hint1Kh, textEng: hint1En } : undefined,
    };
  }

  // 5. Open-ended Free Text (fallback to non-deterministic)
  const hint1Kh = currentStep.hint1?.khmer || '';
  const hint1En = currentStep.hint1?.eng || '';

  return {
    isCorrect: false,
    isDeterministic: false,
    feedbackType: 'incorrect',
    tutorReplyKhmer: `🤔 **សាកល្បងគិតម្តងទៀតណា៎!** ចម្លើយ **"${trimmed}"** មិនទាន់ចំគោលដៅឡើយ។\n\n${hint1Kh ? `💡 **តម្រុយ៖** ${hint1Kh}\n\n` : ''}សាកល្បងពន្យល់ម្តងទៀត ឬចុចមើល «តម្រុយ» ខាងក្រោម!`,
    tutorReplyEng: `🤔 **Let's rethink this together!** **"${trimmed}"** isn't quite right.\n\n${hint1En ? `💡 **Clue:** ${hint1En}\n\n` : ''}Try explaining again or check the hints below!`,
    hintSuggestion: hint1Kh ? { level: 1, textKhmer: hint1Kh, textEng: hint1En } : undefined,
  };
}
