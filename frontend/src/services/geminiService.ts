import { HomeworkProblem, Language } from "../types";
import { tutorApi } from "../api";

// ──────────────────────────────────────────────
// 1. Grade & Age Adapted Socratic System Prompts (Following promt.md)
// ──────────────────────────────────────────────
export function getGradeAdaptedSystemPrompt(
  grade: number = 4,
  language: Language = "km",
): string {
  const isKm = language === "km";
  if (grade <= 2) {
    // Grade 1-2 (Ages 6-7): Early Elementary
    return isKm
      ? `អ្នកគឺ ReanMore គ្រូបង្រៀន AI សម្រាប់កុមារថ្នាក់ទី ១–២ (អាយុ ៦–៧ ឆ្នាំ)។ ច្បាប់គំរូ៖
1. ប្រើប្រយោគខ្លីបំផុត (ក្រោម ១២ ពាក្យ) និងពាក្យសាមញ្ញបំផុត
2. ប្រើរូបតំណាងសត្វ 🦁 ផ្លែប៉ោម 🍎 ស្ករគ្រាប់ 🍬 ក្នុងការរាប់
3. កុំប្រាប់ចម្លើយផ្ទាល់ — សួរសំណួរម្តងមួយៗ
4. លើកទឹកចិត្តជានិច្ច និងពោរពេញដោយភាពកក់ក្តៅ`
      : `You are ReanMore, an AI tutor for Grade 1-2 elementary students (Ages 6-7). Core rules:
1. Use ultra-short sentences (< 12 words) and simple vocabulary
2. Use concrete object counting (apples 🍎, animals 🦁, blocks 🧱)
3. Never give the answer directly — ask one simple question at a time
4. Be enthusiastic, warm, and encourage the child at every step`;
  }

  if (grade <= 4) {
    // Grade 3-4 (Ages 8-9): Mid Elementary
    return isKm
      ? `អ្នកគឺ ReanMore គ្រូបង្រៀន AI សម្រាប់កុមារថ្នាក់ទី ៣–៤ (អាយុ ៨–៩ ឆ្នាំ)។ ច្បាប់គំរូ៖
1. ជួយកុមារគិតជាជំហានៗតាមវិធីសាស្រ្តសូក្រាត (Socratic Method)
2. ប្រើគំរូរូបភាព (បន្ទាត់ចំនួន ដ្យាក្រាមប្រអប់ លក្ខណៈសត្វ)
3. ផ្តល់តម្រុយជាដំណាក់កាលៗ មិនប្រាប់ចម្លើយចុងក្រោយ
4. ពន្យល់ដោយភាពរួសរាយ និងងាយយល់`
      : `You are ReanMore, a Socratic STEM tutor for Grade 3-4 elementary students (Ages 8-9). Core rules:
1. Guide step-by-step using Socratic questioning without leaking answers
2. Refer to visual scaffolds (number lines, bar models, animal feature charts)
3. Provide incremental progressive clues
4. Keep explanations conversational, friendly, and empowering`;
  }

  // Grade 5-6 (Ages 10-12): Upper Elementary
  return isKm
    ? `អ្នកគឺ ReanMore គ្រូបង្រៀន AI សម្រាប់កុមារថ្នាក់ទី ៥–៦ (អាយុ ១០–១២ ឆ្នាំ)។ ច្បាប់គំរូ៖
1. បណ្តុះការគិតវិភាគស៊ីជម្រៅ និងការបំបែកបញ្ហាជាជំហានៗ
2. ពន្យល់គោលគំនិតគណិតវិទ្យា និងវិទ្យាសាស្ត្រ (សភាពសារធាតុ ប្រភាគ ចំណោទស្មុគស្មាញ)
3. ណែនាំដោយសំណួរឆ្លាតវៃ ដោយមិនប្រាប់ចម្លើយផ្ទាល់
4. លើកទឹកចិត្តឲ្យកុមារពន្យល់ហេតុផលនៃការគិតរបស់ខ្លួន`
    : `You are ReanMore, an inspiring Socratic tutor for Grade 5-6 students (Ages 10-12). Core rules:
1. Foster analytical thinking and multi-step problem decomposition
2. Explain mathematical reasoning and scientific concepts (states of matter, fractions, classification)
3. Guide with thoughtful sub-questions without giving away the solution
4. Encourage the student to explain their own reasoning`;
}

// ──────────────────────────────────────────────
// 3. Expanded Safety Guardrails
// ──────────────────────────────────────────────
const UNSAFE_KEYWORDS = [
  // Violence / Danger
  "cheat",
  "hack",
  "fight",
  "kill",
  "die",
  "gun",
  "weapon",
  "bomb",
  "hurt",
  // Inappropriate for children
  "boyfriend",
  "girlfriend",
  "dating",
  "kiss",
  "sexy",
  "naked",
  // Academic dishonesty
  "write essay for me",
  "do my homework",
  "give me answer",
  "answer this",
  "solve this for me",
  "just tell me",
  "copy",
  "plagiar",
  // Off-topic
  "who is your father",
  "who made you",
  "are you real",
  "marry me",
];

function isUnsafePrompt(prompt: string): boolean {
  const lower = prompt.toLowerCase();
  return UNSAFE_KEYWORDS.some((kw) => lower.includes(kw));
}

// ──────────────────────────────────────────────
// 5. Inline Math Formatting Helper
// ──────────────────────────────────────────────
function formatMathInline(text: string): string {
  // Replace common patterns with visually friendly versions
  return (
    text
      // Fractions: 1/2, 3/4 etc.
      .replace(/(\d+)\/(\d+)(?!\d)/g, "$1⁄$2")
      // Multiplication: 2x3 or 2*3 → 2 × 3
      .replace(/(\d+)\s*\*\s*(\d+)/g, "$1 × $2")
      .replace(/(\d+)\s*x\s*(\d+)/gi, "$1 × $2")
      // Division: 10÷2 → 10 ÷ 2
      .replace(/(\d+)\s*÷\s*(\d+)/g, "$1 ÷ $2")
      // Square root: sqrt(9) → √9
      .replace(/sqrt\((\d+)\)/gi, "√$1")
      // Equals with spaces for readability
      .replace(/(\S+)=(\S+)/g, "$1 = $2")
  );
}

// ──────────────────────────────────────────────
// 2. Parse Numbered Steps from Backend Response
// ──────────────────────────────────────────────
export function parseSteps(text: string): string[] {
  // Try to find "Step 1:", "Step 2:" etc. patterns
  const stepRegex = /(?:Step|ជំហាន)\s*(\d+)[:.\s]/gi;
  const steps: string[] = [];
  let lastIndex = 0;
  let match;

  while ((match = stepRegex.exec(text)) !== null) {
    if (lastIndex > 0 && match.index > lastIndex) {
      steps.push(text.slice(lastIndex, match.index).trim());
    }
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex > 0 && lastIndex < text.length) {
    steps.push(text.slice(lastIndex).trim());
  }

  // If no steps found, return the whole text as one item
  return steps.length > 0 ? steps : [text];
}

// ──────────────────────────────────────────────
// 4. Better Fallback Messages (Socratic Redirect)
// ──────────────────────────────────────────────
function getSocraticFallback(
  _language: Language,
  prompt: string,
): { textKhmer: string; textEng: string } {
  const promptLower = prompt.toLowerCase();

  // Math-related fallback
  const mathKeywords = [
    "plus",
    "add",
    "minus",
    "subtract",
    "times",
    "multiply",
    "divide",
    "fraction",
    "+",
    "-",
    "×",
    "÷",
    "=",
    "?",
  ];
  const isMath = mathKeywords.some((kw) => promptLower.includes(kw));

  if (isMath) {
    return {
      textKhmer: `តោះយើងមើលសំណួរនេះជាមួយគ្នា! ជំហានទី ១៖ តើអ្នកឃើញលេខអ្វីខ្លះក្នុងសំណួរនេះ? ចុចលើរូបភាពឬវាយប្រាប់ខ្ញុំពីលេខទាំងនោះណា!`,
      textEng: `Let's look at this together! Step 1: What numbers do you see in the question? Tap or tell me what they are!`,
    };
  }

  // Science-related fallback
  const scienceKeywords = [
    "plant",
    "water",
    "animal",
    "earth",
    "sun",
    "moon",
    "weather",
    "body",
    "food",
  ];
  const isScience = scienceKeywords.some((kw) => promptLower.includes(kw));

  if (isScience) {
    return {
      textKhmer: `ចំណង់ចំណូលចិត្តណាស់! តោះយើងស្វែងយល់ពីវិទ្យាសាស្ត្រនេះជាមួយគ្នា។ ជំហានទី ១៖ តើអ្នកដឹងអ្វីខ្លះអំពីប្រធានបទនេះរួចហើយ?`,
      textEng: `Great curiosity! Let's explore this science topic together. Step 1: What do you already know about this?`,
    };
  }

  // Generic Socratic fallback
  return {
    textKhmer: `សួស្តី! ខ្ញុំគឺ ReanMore។ តើយើងរៀនមុខវិជ្ជាអ្វីថ្ងៃនេះ? អ្នកអាចសួរខ្ញុំអំពីគណិតវិទ្យា វិទ្យាសាស្ត្រ ឬភាសាអង់គ្លេស!`,
    textEng: `Hi! I'm ReanMore. What subject shall we learn today? You can ask me about Math, Science, or English!`,
  };
}

// ──────────────────────────────────────────────
// Main API Function
// ──────────────────────────────────────────────
export interface TutorResponse {
  textKhmer: string;
  textEng: string;
  isSafetyRefusal?: boolean | undefined;
  stepWidget?: any;
  suggestedChips?: string[] | undefined;
  degradeToTapFirst?: boolean | undefined;
}

export async function askReanMoreTutor(
  userPrompt: string,
  problemContext?: HomeworkProblem,
  language: Language = "km",
  sessionId?: string,
): Promise<TutorResponse> {
  // ── Safety Check FIRST ──
  if (isUnsafePrompt(userPrompt)) {
    return {
      textKhmer: `ខ្ញុំនៅទីនេះដើម្បីជួយសិក្សា និងធ្វើលំហាត់ដោយសុវត្ថិភាព។ តោះត្រឡប់ទៅមើលលំហាត់វិញណា! តើអ្នកមានសំណួរគណិតវិទ្យា ឬវិទ្យាសាស្ត្រចង់សួរទេ?`,
      textEng: `I'm here to help with safe, educational topics only. Let's get back to your homework! Do you have a Math or Science question?`,
      isSafetyRefusal: true,
    };
  }

  try {
    const activeIdx = problemContext?.activeStepIndex ?? 0;
    const activeStepObj = problemContext?.steps?.[activeIdx];
    const grade = problemContext?.grade ?? 4;
    const gradeLevel =
      grade <= 2 ? "grade_1_2" : grade <= 4 ? "grade_3_4" : "grade_5_6";
    const isEnglishExercise =
      problemContext?.subject === "english" ||
      Boolean(problemContext?.titleEng && /english/i.test(problemContext.titleEng));
    const effectiveLanguage = isEnglishExercise ? "en" : (language === "km" ? "km" : "en");

    const turn = await tutorApi.query({
      query: userPrompt,
      session_id: sessionId,
      grade_level: problemContext?.grade ? gradeLevel : "grade_1_3",
      language: effectiveLanguage,
      problem_context: problemContext
        ? {
            id: problemContext.id,
            subject: problemContext.subject,
            titleEng: problemContext.titleEng,
            titleKhmer: problemContext.titleKhmer,
            statementEng: problemContext.problemStatementEng,
            statementKhmer: problemContext.problemStatementKhmer,
            concept: problemContext.concept,
            totalSteps: problemContext.steps?.length,
            activeStepIndex: activeIdx,
            currentStepQuestion: activeStepObj?.questionEng,
            currentStepQuestionKhmer: activeStepObj?.questionKhmer,
            visualData: problemContext.visualData,
          }
        : null,
      active_step: activeStepObj || null,
      exercise_id: problemContext?.id,
    });

    let textEng = formatMathInline(turn.textEng || turn.textKhmer || "");
    let textKhmer = isEnglishExercise ? textEng : (turn.textKhmer || turn.textEng || "");

    return {
      textKhmer,
      textEng,
      isSafetyRefusal: turn.outcome === 'safety_tier1_deflected' || turn.outcome === 'safety_tier2_escalated',
      stepWidget: turn.stepWidget,
      suggestedChips: turn.suggestedChips,
      degradeToTapFirst: turn.degraded,
    };
  } catch (err) {
    console.error("tutorApi query error:", err);
  }

  // ── Fallback: Socratic redirect ──
  const fallback = getSocraticFallback(language, userPrompt);
  return {
    ...fallback,
    isSafetyRefusal: false,
  };
}

export const askTunsayTutor = askReanMoreTutor;
export const askSayoTutor = askReanMoreTutor;
