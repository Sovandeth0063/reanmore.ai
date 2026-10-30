import React from 'react';
import { ChatMessage, StepItem } from '../../types';
import { extractStepNumbers } from '../VisualWidget';
import { translateApi } from '../../api';

const KHMER_RANGE = /[\u1780-\u17FF]/;

/**
 * Fills the Khmer fields of mapped step items using the backend /api/translate
 * endpoint. If translation is unavailable (or returns English), the original
 * text is kept, so the UI degrades gracefully.
 */
export async function localizeStepsForKhmer(steps: StepItem[]): Promise<StepItem[]> {
  const pending: string[] = [];
  const add = (value?: string) => {
    const text = (value || '').trim();
    if (text && !KHMER_RANGE.test(text)) pending.push(text);
  };

  for (const step of steps) {
    add(step.mission);
    add(step.clue);
    add(step.helpfulExample);
    add(step.yourTurn);
    add(step.title);
    (step.hints || []).forEach(add);
  }

  const unique = Array.from(new Set(pending));
  if (unique.length === 0) return steps;

  const translated = await translateApi.translateBatch(unique, 'km');
  const lookup = new Map(unique.map((text, i) => [text, translated[i] || text]));
  const t = (value?: string) => lookup.get((value || '').trim()) || value || '';

  return steps.map((step) => ({
    ...step,
    questionKhmer: t(step.mission),
    socraticPromptKhmer: t(step.yourTurn),
    hint1: { ...step.hint1, khmer: t(step.hints?.[0]) },
    hint2: { ...step.hint2, khmer: t(step.hints?.[1]) },
    hint3: {
      ...step.hint3,
      titleKhmer: t(step.hint3?.titleEng),
      exampleKhmer: t(step.hints?.[2]),
    },
    explainDifferently: {
      ...step.explainDifferently,
      simpleKhmer: t(step.mission),
      analogyTitle: t(step.title),
      analogyKhmer: t(step.helpfulExample),
    },
  }));
}

// Helper: Render inline markdown (bold, italic, code) and newlines
export function renderFormattedInline(text: string): React.ReactNode {
  if (!text) return null;

  // Split by **bold**, *italic*, or `code` tokens
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);

  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
      return (
        <strong key={idx} className="font-black text-inherit">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith('*') && part.endsWith('*') && part.length >= 2) {
      return (
        <em key={idx} className="italic font-bold">
          {part.slice(1, -1)}
        </em>
      );
    }
    if (part.startsWith('`') && part.endsWith('`') && part.length >= 2) {
      return (
        <code key={idx} className="px-1.5 py-0.5 bg-emerald-100 text-[#1B4332] rounded font-mono text-xs font-black border border-emerald-300">
          {part.slice(1, -1)}
        </code>
      );
    }

    // Handle line breaks within text
    if (part.includes('\n')) {
      const subLines = part.split('\n');
      return (
        <React.Fragment key={idx}>
          {subLines.map((sub, sIdx) => (
            <React.Fragment key={sIdx}>
              {sIdx > 0 && <br />}
              {sub}
            </React.Fragment>
          ))}
        </React.Fragment>
      );
    }

    return part;
  });
}

export const EMOJI_STRIP_REGEX = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{26FF}\u{1F1E0}-\u{1F1FF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{1F900}-\u{1F9FF}\u{2700}-\u{2712}\u{2714}-\u{2716}\u{2718}-\u{27BF}]/gu;

export function stripEmojis(str: string): string {
  if (!str) return '';
  return str.replace(EMOJI_STRIP_REGEX, '').replace(/\s{2,}/g, ' ');
}

// Helper: Render numbered steps and formatted paragraphs with visual badges
export function formatMessageText(text: string): React.ReactNode[] {
  if (!text) return [];
  const cleanText = stripEmojis(text);
  const paragraphs = cleanText.split(/\n\s*\n/);
  return paragraphs.map((para, i) => {
    const trimmed = para.trim();
    if (!trimmed) return null;

    const stepMatch = trimmed.match(/^(\d+)\.\s*/);
    if (stepMatch) {
      const num = stepMatch[1];
      const content = trimmed.slice(stepMatch[0].length);
      return (
        <div key={i} className="flex items-start gap-2 mb-2.5 last:mb-0">
          <span className="inline-flex items-center justify-center w-6 h-6 sm:w-7 sm:h-7 bg-[#1B4332] text-white rounded-lg text-xs font-black shrink-0 mt-0.5 shadow-[1px_1px_0px_#1B4332]">
            {num}
          </span>
          <span className="leading-relaxed">{renderFormattedInline(content)}</span>
        </div>
      );
    }
    return (
      <div key={i} className="mb-2 last:mb-0 leading-relaxed">
        {renderFormattedInline(trimmed)}
      </div>
    );
  }).filter(Boolean) as React.ReactNode[];
}

export interface ExtractedStepWidget {
  widget: any;
  activeStep: StepItem;
  activeIdx: number;
  totalSteps: number;
  completedSteps: number[];
  introText?: string;
}

/**
 * Extracts structured StepWidgetPayload from a ChatMessage.
 * Supports both direct `msg.stepWidget` payload and regex fallback parsing
 * for messages containing the 4-part Socratic card pattern.
 */
export function extractStepWidgetFromMessage(msg: ChatMessage): ExtractedStepWidget | null {
  if (msg.stepWidget && msg.stepWidget.steps && msg.stepWidget.steps.length > 0) {
    const w = msg.stepWidget;
    const activeIdx = Math.max(0, Math.min(w.current_step_index ?? 0, w.steps.length - 1));
    const rawActiveStep = w.steps[activeIdx];
    const activeStep = rawActiveStep
      ? {
          ...rawActiveStep,
          options: rawActiveStep.options || (rawActiveStep as any).options || (w as any).options,
          visualData:
            rawActiveStep.visualData ||
            (rawActiveStep as any).visual_data ||
            // A widget-level visual belongs to the first step; don't show it later.
            (activeIdx === 0
              ? (w as any).visual_data || (w as any).visualData
              : undefined),
        }
      : rawActiveStep;
    const totalSteps = w.total_steps || w.steps.length;
    const completedSteps = w.completed_steps || [];
    return {
      widget: w,
      activeStep,
      activeIdx,
      totalSteps,
      completedSteps,
    };
  }

  const rawText = msg.textEng || msg.textKhmer || '';
  const missionRegex = /(?:(?:\u{1F3AF})\s*)?\*{0,2}(?:Our Mission|បេសកកម្មរបស់យើង)\*{0,2}:?\s*([\s\S]*?)(?=(?:(?:\u{1F50D})\s*)?\*{0,2}(?:Clue|តម្រុយ)\*{0,2}:|$)/iu;
  const clueRegex = /(?:(?:\u{1F50D})\s*)?\*{0,2}(?:Clue|តម្រុយ)\*{0,2}:?\s*([\s\S]*?)(?=(?:(?:\u{1F4A1})\s*)?\*{0,2}(?:Helpful (?:Picture \/ )?Example|រូបភាព \/ ឧទាហរណ៍ជំនួយ)\*{0,2}:|$)/iu;
  const exampleRegex = /(?:(?:\u{1F4A1})\s*)?\*{0,2}(?:Helpful (?:Picture \/ )?Example|រូបភាព \/ ឧទាហរណ៍ជំនួយ)\*{0,2}:?\s*([\s\S]*?)(?=(?:(?:\u{270F}\u{FE0F}?)\s*)?\*{0,2}(?:Your Turn|វេនរបស់អ្នក)\*{0,2}:|$)/iu;
  const yourTurnRegex = /(?:(?:\u{270F}\u{FE0F}?)\s*)?\*{0,2}(?:Your Turn|វេនរបស់អ្នក)\*{0,2}:?\s*([\s\S]*?)$/iu;

  const missionMatch = rawText.match(missionRegex);
  const yourTurnMatch = rawText.match(yourTurnRegex);

  if (missionMatch && yourTurnMatch) {
    const firstSectionIdx = rawText.search(/(?:(?:\u{1F3AF})\s*)?\*{0,2}(?:Our Mission|បេសកកម្មរបស់យើង)\*{0,2}:/iu);
    let intro = '';
    if (firstSectionIdx > 0) {
      intro = rawText.slice(0, firstSectionIdx).replace(/---\s*$/g, '').trim();
    }

    const clueMatch = rawText.match(clueRegex);
    const exampleMatch = rawText.match(exampleRegex);

    const clean = (s?: string) => {
      if (!s) return '';
      return s
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/\*(.*?)\*/g, '$1')
        .replace(/^>\s?/gm, '')
        .replace(/^#+\s?/gm, '')
        .replace(/`([^`]+)`/g, '$1')
        .trim();
    };

    const mission = clean(missionMatch[1]);
    const clue = clean(clueMatch?.[1]);
    const helpfulExample = clean(exampleMatch?.[1]);
    const yourTurn = clean(yourTurnMatch[1]);

    let stepNum = 1;
    const numMatch = (intro || rawText).match(/(?:Step|ជំហាន)\s*(\d+)/i);
    if (numMatch) {
      stepNum = parseInt(numMatch[1], 10);
    }

    const synthesizedStep: StepItem = {
      id: `step-${stepNum}`,
      stepNumber: stepNum,
      title: `Step ${stepNum}`,
      status: 'in_progress',
      mission,
      clue,
      helpfulExample,
      yourTurn,
      currentHintLevel: 0,
      hints: [
        clue,
        helpfulExample,
        `Think about: ${yourTurn}`
      ],
      questionEng: mission,
      questionKhmer: mission,
      inputFormat: 'text',
      correctAnswer: '',
      hint1: { khmer: clue, eng: clue },
      hint2: { khmer: helpfulExample, eng: helpfulExample },
      hint3: { titleKhmer: 'Example', titleEng: 'Example', exampleKhmer: helpfulExample, exampleEng: helpfulExample },
      socraticPromptEng: yourTurn,
      socraticPromptKhmer: yourTurn,
      explainDifferently: { simpleKhmer: clue, simpleEng: clue, analogyTitle: '', analogyKhmer: '', analogyEng: '', analogyType: 'plants' },
      totalSteps: Math.max(stepNum, 3)
    };

    const activeGroups = extractStepNumbers(synthesizedStep);
    if (activeGroups && activeGroups.length > 0) {
      synthesizedStep.visualData = {
        type: 'objects',
        groups: activeGroups,
        item_type: 'apple'
      };
    }

    const synthesizedWidget = {
      total_steps: Math.max(stepNum, 3),
      current_step_index: stepNum - 1,
      completed_steps: [],
      visual_data: synthesizedStep.visualData,
      steps: [synthesizedStep]
    };

    return {
      widget: synthesizedWidget,
      activeStep: synthesizedStep,
      activeIdx: 0,
      totalSteps: Math.max(stepNum, 3),
      completedSteps: [],
      introText: intro
    };
  }

  return null;
}

export function mapWidgetToStepItems(widget: any): StepItem[] {
  if (!widget || !Array.isArray(widget.steps)) return [];
  const total = widget.total_steps || widget.steps.length;
  return widget.steps.map((s: any, idx: number) => {
    const stepNum = s.step_number || idx + 1;
    const mission = s.mission || s.title || `Step ${stepNum}`;
    const yourTurn = s.your_turn || mission;
    const expectedAns = String(s.expected_answer || s.expectedAnswer || '').trim();
    const isNum = /^-?\d+(\.\d+)?$/.test(expectedAns);
    const options = s.options && Array.isArray(s.options) && s.options.length > 0 ? s.options : undefined;
    const inputFormat = options ? 'mcq' : (isNum ? 'number' : 'text');
    const hints = Array.isArray(s.hints) ? s.hints : [];
    const clue = s.clue || hints[0] || 'Please review the question and hints carefully.';
    const example = s.helpful_example || hints[1] || 'Try thinking one step at a time!';
    const acceptableAnswers = Array.isArray(s.acceptable_answers)
      ? s.acceptable_answers
      : Array.isArray(s.acceptableAnswers)
      ? s.acceptableAnswers
      : undefined;
    return {
      id: `step-${stepNum}`,
      stepNumber: stepNum,
      totalSteps: total,
      questionKhmer: mission,
      questionEng: mission,
      socraticPromptKhmer: yourTurn,
      socraticPromptEng: yourTurn,
      inputFormat,
      options,
      correctAnswer: expectedAns,
      acceptableAnswers,
      expectedAnswer: expectedAns,
      expected_answer: expectedAns,
      mission,
      title: s.title || `Step ${stepNum}`,
      clue,
      helpfulExample: example,
      yourTurn,
      hints: [hints[0] || clue, hints[1] || example, hints[2] || ''],
      // Each step owns its visual; the widget-level visual belongs to step 1 only.
      visualData:
        s.visual_data ||
        s.visualData ||
        (idx === 0 ? widget?.visual_data || widget?.visualData : undefined),
      status: idx === 0 ? 'in_progress' : 'locked',
      hint1: { khmer: hints[0] || clue, eng: hints[0] || clue },
      hint2: { khmer: hints[1] || example, eng: hints[1] || example },
      hint3: { titleKhmer: 'Help', titleEng: 'Help', exampleKhmer: hints[2] || '', exampleEng: hints[2] || '' },
      explainDifferently: {
        simpleKhmer: mission,
        simpleEng: mission,
        analogyTitle: s.title || 'Guidance',
        analogyKhmer: example,
        analogyEng: example,
        analogyType: 'apples',
      },
    };
  });
}

export const thinkingTextsEng = [
  'Reading your homework problem carefully...',
  'Thinking of a fun, simple way to explain this...',
  'Checking the math steps one by one...',
  'Preparing a helpful clue just for you...',
];

export const thinkingTextsKhmer = [
  'កំពុងអានលំហាត់របស់អ្នកយ៉ាងយកចិត្តទុកដាក់...',
  'កំពុងគិតពីវិធីងាយៗ និងសប្បាយៗដើម្បីពន្យល់...',
  'កំពុងពិនិត្យជំហានគណិតវិទ្យាម្តងមួយៗ...',
  'កំពុងរៀបចំតម្រុយជំនួយសម្រាប់អ្នក...',
];
