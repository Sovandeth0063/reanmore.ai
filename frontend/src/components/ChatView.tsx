import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ChatMessage, HomeworkProblem, UserProfile, TunsayState, ChatSession, WorksheetQueue } from '../types';
import { TunsayAvatar } from './TunsayAvatar';
import { StepTrail } from './StepTrail';
import { StepCard } from './StepCard';
import { HintSheet } from './HintSheet';
import { ExplanationCard } from './ExplanationCard';
import { StepChatBubble } from './StepChatBubble';
import { AllStepsDrawer } from './AllStepsDrawer';
import { WorksheetExerciseBar } from './WorksheetExerciseBar';
import { WorksheetProgressPanel } from './WorksheetProgressPanel';
import { ExerciseCelebrationBanner } from './ExerciseCelebrationBanner';
import { StepItem } from '../types';
import { askTunsayTutor } from '../services/geminiService';
import { enrichProblemFromCase } from '../services/hardcodedTutorProvider';
import { fastValidateStepAnswer } from '../services/answerValidationService';
import { Send, Camera, User, GraduationCap, ArrowLeft, Plus, Trash2, MessageSquare, Sparkles, Layers, Menu, X, RotateCcw } from 'lucide-react';
import { ALL_HARDCODED_CASES } from '../data/hardcodedCases';
import { matchCaseId } from '../services/caseMatcher';
import {
  updateActivity,
  findActiveActivity,
} from '../utils/reportUtils';

// Helper: Render inline markdown (bold, italic, code) and newlines
function renderFormattedInline(text: string): React.ReactNode {
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

// Helper: Render numbered steps and formatted paragraphs with visual badges
function formatMessageText(text: string): React.ReactNode[] {
  if (!text) return [];
  const paragraphs = text.split(/\n\s*\n/);
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

interface ExtractedStepWidget {
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
function extractStepWidgetFromMessage(msg: ChatMessage): ExtractedStepWidget | null {
  if (msg.stepWidget && msg.stepWidget.steps && msg.stepWidget.steps.length > 0) {
    const w = msg.stepWidget;
    const activeIdx = Math.max(0, Math.min(w.current_step_index ?? 0, w.steps.length - 1));
    const activeStep = w.steps[activeIdx];
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
  const missionRegex = /(?:🎯\s*)?\*{0,2}(?:Our Mission|បេសកកម្មរបស់យើង)\*{0,2}:?\s*([\s\S]*?)(?=(?:🔍\s*)?\*{0,2}(?:Clue|តម្រុយ)\*{0,2}:|$)/i;
  const clueRegex = /(?:🔍\s*)?\*{0,2}(?:Clue|តម្រុយ)\*{0,2}:?\s*([\s\S]*?)(?=(?:💡\s*)?\*{0,2}(?:Helpful (?:Picture \/ )?Example|រូបភាព \/ ឧទាហរណ៍ជំនួយ)\*{0,2}:|$)/i;
  const exampleRegex = /(?:💡\s*)?\*{0,2}(?:Helpful (?:Picture \/ )?Example|រូបភាព \/ ឧទាហរណ៍ជំនួយ)\*{0,2}:?\s*([\s\S]*?)(?=(?:✏️\s*)?\*{0,2}(?:Your Turn|វេនរបស់អ្នក)\*{0,2}:|$)/i;
  const yourTurnRegex = /(?:✏️\s*)?\*{0,2}(?:Your Turn|វេនរបស់អ្នក)\*{0,2}:?\s*([\s\S]*?)$/i;

  const missionMatch = rawText.match(missionRegex);
  const yourTurnMatch = rawText.match(yourTurnRegex);

  if (missionMatch && yourTurnMatch) {
    const firstSectionIdx = rawText.search(/(?:🎯\s*)?\*{0,2}(?:Our Mission|បេសកកម្មរបស់យើង)\*{0,2}:/i);
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

    const synthesizedWidget = {
      total_steps: Math.max(stepNum, 3),
      current_step_index: stepNum - 1,
      completed_steps: [],
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

interface ChatViewProps {
  profile: UserProfile;
  initialProblem?: HomeworkProblem | undefined;
  initialQuery?: string | undefined;
  onClearInitialQuery?: () => void;
  sessions: ChatSession[];
  activeSessionId: string;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
  onUpdateMessages: (messages: ChatMessage[], progressMap?: Record<string, any>) => void;
  onOpenScanner: () => void;
  onBackToHome?: () => void;
  worksheetQueue?: WorksheetQueue | undefined;
  onSelectExercise?: (index: number) => void;
  onExerciseComplete?: (problemId: string) => void;
}

export const ChatView: React.FC<ChatViewProps> = ({
  profile,
  initialProblem,
  initialQuery,
  onClearInitialQuery,
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onUpdateMessages,
  onOpenScanner,
  onBackToHome,
  worksheetQueue,
  onSelectExercise,
  onExerciseComplete,
}) => {
  const isKhmer = profile.language === 'km';
  const activeSession = sessions.find(s => s.id === activeSessionId);
  const messages = activeSession?.messages ?? [];

  const [activeProblem, setActiveProblem] = useState<HomeworkProblem | undefined>(() => {
    return initialProblem ? enrichProblemFromCase(initialProblem, profile.grade) : undefined;
  });
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(() => {
    if (initialProblem?.id && activeSession?.problemStepProgress?.[initialProblem.id]) {
      return activeSession.problemStepProgress[initialProblem.id].currentStepIndex ?? 0;
    }
    return 0;
  });
  const [maxUnlockedStepIndex, setMaxUnlockedStepIndex] = useState<number>(() => {
    if (initialProblem?.id && activeSession?.problemStepProgress?.[initialProblem.id]) {
      return activeSession.problemStepProgress[initialProblem.id].maxUnlockedStepIndex ?? 0;
    }
    return 0;
  });
  const [completedStepIndices, setCompletedStepIndices] = useState<number[]>(() => {
    if (initialProblem?.id && activeSession?.problemStepProgress?.[initialProblem.id]) {
      return activeSession.problemStepProgress[initialProblem.id].completedStepIndices ?? [];
    }
    return [];
  });
  const [problemStepProgress, setProblemStepProgress] = useState<Record<string, {
    currentStepIndex: number;
    maxUnlockedStepIndex: number;
    completedStepIndices: number[];
  }>>(() => activeSession?.problemStepProgress || {});
  const [celebratingProblemId, setCelebratingProblemId] = useState<string | null>(null);
  const celebrationShownRef = useRef<Set<string>>(new Set());

  // Sync problemStepProgress whenever session changes or loads from storage
  useEffect(() => {
    if (activeSession?.problemStepProgress) {
      setProblemStepProgress(activeSession.problemStepProgress);
      if (activeProblem?.id && activeSession.problemStepProgress[activeProblem.id]) {
        const saved = activeSession.problemStepProgress[activeProblem.id];
        setCurrentStepIndex(saved.currentStepIndex ?? 0);
        setMaxUnlockedStepIndex(saved.maxUnlockedStepIndex ?? 0);
        setCompletedStepIndices(saved.completedStepIndices ?? []);
      }
    }
  }, [activeSessionId, activeSession?.problemStepProgress, activeProblem?.id]);

  const [sidebarMode, setSidebarMode] = useState<'worksheet' | 'chats'>('worksheet');
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [inputQuery, setInputQuery] = useState('');
  const [isSayoThinking, setIsSayoThinking] = useState(false);
  const [sayoStatus, setSayoStatus] = useState<TunsayState>('idle');
  const [thinkingTextIdx, setThinkingTextIdx] = useState(0);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mascotTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const hasWavedRef = useRef(false);
  const lastInteractionRef = useRef<number>(Date.now());
  const currentActivityRef = useRef<string | null>(null);
  const prevProblemIdRef = useRef<string | undefined>(initialProblem?.id);
  const prevSessionIdRef = useRef<string | undefined>(activeSessionId);

  // Sync active problem only when problem ID or session ID changes
  useEffect(() => {
    const isNewSession = prevSessionIdRef.current !== activeSessionId;
    const isNewProblem = prevProblemIdRef.current !== initialProblem?.id;

    if (isNewSession || isNewProblem) {
      prevSessionIdRef.current = activeSessionId;
      prevProblemIdRef.current = initialProblem?.id;

      hasWavedRef.current = false;
      setSayoStatus('idle');
      const enriched = initialProblem ? enrichProblemFromCase(initialProblem, profile.grade) : undefined;
      setActiveProblem(enriched);
      setCelebratingProblemId(null);

      const progressSource = isNewSession
        ? (activeSession?.problemStepProgress || {})  // New session: only use saved session data, never stale local state
        : (activeSession?.problemStepProgress || problemStepProgress);
      if (enriched && enriched.id && progressSource[enriched.id]) {
        setCurrentStepIndex(progressSource[enriched.id].currentStepIndex ?? 0);
        setMaxUnlockedStepIndex(progressSource[enriched.id].maxUnlockedStepIndex ?? 0);
        setCompletedStepIndices(progressSource[enriched.id].completedStepIndices || []);
      } else {
        setCurrentStepIndex(0);
        setMaxUnlockedStepIndex(0);
        setCompletedStepIndices([]);
      }
      // Always sync the local progress state to the active session when switching sessions
      if (isNewSession) {
        setProblemStepProgress(activeSession?.problemStepProgress || {});
        celebrationShownRef.current.clear();
      }
    }

    if (worksheetQueue && worksheetQueue.problems.length > 1) {
      setSidebarMode('worksheet');
    } else {
      setSidebarMode('chats');
    }
    if (mascotTimeoutRef.current) {
      clearTimeout(mascotTimeoutRef.current);
      mascotTimeoutRef.current = null;
    }
  }, [activeSessionId, initialProblem?.id, profile.grade, worksheetQueue]);

  // Cycle through Socratic thinking messages while AI is processing
  useEffect(() => {
    if (sayoStatus === 'thinking') {
      const interval = setInterval(() => {
        setThinkingTextIdx((prev: number) => (prev + 1) % 4);
      }, 1800);
      return () => clearInterval(interval);
    } else {
      setThinkingTextIdx(0);
    }
  }, [sayoStatus]);

  const updateMessages = (newMsgs: ChatMessage[], progressMap?: Record<string, any>) => {
    onUpdateMessages(newMsgs, progressMap || problemStepProgress);
  };

  // 💬 Mascot state helpers 💬
  const transitionMascotState = useCallback((state: TunsayState, autoReturnToIdleMs?: number) => {
    if (mascotTimeoutRef.current) {
      clearTimeout(mascotTimeoutRef.current);
      mascotTimeoutRef.current = null;
    }
    setSayoStatus(state);
    if (autoReturnToIdleMs && autoReturnToIdleMs > 0) {
      mascotTimeoutRef.current = setTimeout(() => {
        setSayoStatus('idle');
      }, autoReturnToIdleMs);
    }
  }, []);

  const determineMascotStateFromResponse = (textEng: string): TunsayState => {
    const lower = textEng.toLowerCase();
    if (lower.includes('not quite') || lower.includes('not exactly') || lower.includes('try again') || lower.includes('not quite right') || lower.includes('oops') || lower.includes('that\'s not')) {
      return 'encouraging';
    }
    if (lower.includes('great') || lower.includes('excellent') || lower.includes('well done') || lower.includes('perfect') || lower.includes('amazing') || lower.includes('awesome') || lower.includes('brilliant')) {
      return 'celebrating';
    }
    if (lower.includes('think') || lower.includes('let me') || lower.includes('hmm') || lower.includes("let's see")) {
      return 'thinking';
    }
    if (lower.includes('?') && (lower.includes('what') || lower.includes('how') || lower.includes('why') || lower.includes('can you') || lower.includes('do you think'))) {
      return 'explaining';
    }
    return 'explaining';
  };

  const getMascotContextText = (state: TunsayState): string => {
    switch (state) {
      case 'idle': return isKhmer ? idleTextKhmer : idleTextEng;
      case 'waving': return isKhmer ? 'សួស្ដី! រៀបចំរៀនហើយឬ?' : 'Hi! Ready to learn?';
      case 'thinking': return isKhmer ? thinkingTextsKhmer[thinkingTextIdx] : thinkingTextsEng[thinkingTextIdx];
      case 'listening': return isKhmer ? 'ខ្ញុំកំពុងស្ដាប់អ្នក...' : "I'm listening...";
      case 'explaining': return isKhmer ? 'នេះជារបៀបគិតអំពីវា...' : "Here's how to think about it...";
      case 'encouraging': return isKhmer ? 'មិនអីទេ! តោះមើលវាតាមរបៀបផ្សេង' : "That's okay! Let's look at it another way.";
      case 'happy': return isKhmer ? 'អ្នកធ្វើបានល្អ!' : "You're doing great!";
      case 'celebrating': return isKhmer ? celebratoryTextKhmer : celebratoryTextEng;
      case 'jumping': return isKhmer ? 'អស្ចារ្យណាស់!' : 'Woohoo! Amazing!';
      case 'confused': return isKhmer ? 'ហ៊ឹម... តោះមើលទាំងអស់គ្នា' : "Hmm... let's look closer together";
      case 'sleeping': return isKhmer ? 'ខ្ញុំសម្រាកខណៈអ្នកគិត...' : 'Resting while you think...';
      default: return '';
    }
  };

  // Greeting wave on first load of a session
  useEffect(() => {
    if (!hasWavedRef.current && messages.length <= 1) {
      hasWavedRef.current = true;
      transitionMascotState('waving', 2500);
    }
  }, [messages.length, transitionMascotState]);

  // Inactivity → sleeping
  useEffect(() => {
    if (sayoStatus !== 'idle') return;
    const timer = setTimeout(() => {
      setSayoStatus('sleeping');
    }, 30000);
    return () => clearTimeout(timer);
  }, [sayoStatus]);

  // AI processing
  useEffect(() => {
    if (isSayoThinking) {
      setSayoStatus('thinking');
    }
  }, [isSayoThinking]);

  // 6. Socratic "Think Aloud" messages while processing
  const thinkingTextsKhmer = [
    'តើយើងដឹងអ្វីខ្លះជាដំបូងនៅក្នុងសំណួរនេះ?',
    'តើសំណួរនេះសុំឡ្យយើងរកអ្វី?',
    'តើយើងអាចបែងចែកវាជាជំហានតូចៗបានទេ?',
    'ជិតរួចរាល់ហើយ! ខ្ញុំកំពុងរៀបចំពន្យល់'
  ];
  const thinkingTextsEng = [
    'What do we know first in this question?',
    'What is the question asking us to find?',
    'Can we break this into smaller steps?',
    'Almost ready! Preparing a helpful explanation'
  ];
  const celebratoryTextKhmer = 'រួចរាល់ហើយ!';
  const celebratoryTextEng = 'Aha! Got it!';
  const idleTextKhmer = 'ReanMore រង់ចាំជួយ!';
  const idleTextEng = 'Ready to help!';

  const [isHintOpen, setIsHintOpen] = useState(false);
  const [isExplainOpen, setIsExplainOpen] = useState(false);
  const [activeModalStep, setActiveModalStep] = useState<StepItem | null>(null);

  // 💬 Socratic Stepper Solution Journey Drawer state 💬
  const [isAllStepsDrawerOpen, setIsAllStepsDrawerOpen] = useState(false);
  const [activeDrawerSteps, setActiveDrawerSteps] = useState<StepItem[]>([]);
  const [activeDrawerStepIdx, setActiveDrawerStepIdx] = useState(0);
  const [activeDrawerMsgId, setActiveDrawerMsgId] = useState<string | null>(null);

  const handleStepHint = (msgId: string) => {
    const idx = messages.findIndex((m) => m.id === msgId);
    if (idx === -1) return;
    const targetMsg = messages[idx];
    const parsed = extractStepWidgetFromMessage(targetMsg);
    if (!parsed) return;

    const widget = targetMsg.stepWidget || parsed.widget;
    const activeIdx = widget.current_step_index ?? 0;
    const step = widget.steps?.[activeIdx];
    if (!step) return;

    const curLevel = step.currentHintLevel ?? step.current_hint_level ?? 0;
    if (curLevel < 3) {
      const nextLevel = curLevel + 1;
      const newSteps = [...widget.steps];
      newSteps[activeIdx] = {
        ...step,
        currentHintLevel: nextLevel,
        current_hint_level: nextLevel,
      };
      const newWidget = {
        ...widget,
        steps: newSteps,
      };
      const newMsg: ChatMessage = {
        ...targetMsg,
        stepWidget: newWidget,
      };
      const updated = [...messages];
      updated[idx] = newMsg;

      if (currentActivityRef.current) {
        const act = findActiveActivity(activeSessionId);
        if (act) {
          updateActivity(currentActivityRef.current, {
            hintsUsed: act.hintsUsed + 1,
          });
        }
      }

      updateMessages(updated);
    }
  };

  const handleStepNavigate = async (msgId: string, targetIdx: number) => {
    const idx = messages.findIndex((m) => m.id === msgId);
    if (idx === -1) return;
    const targetMsg = messages[idx];
    const parsed = extractStepWidgetFromMessage(targetMsg);
    if (!parsed) return;

    const widget = targetMsg.stepWidget || parsed.widget;
    if (!widget.steps || targetIdx < 0 || targetIdx >= widget.steps.length) return;

    const newWidget = {
      ...widget,
      current_step_index: targetIdx,
    };
    const newMsg: ChatMessage = {
      ...targetMsg,
      stepWidget: newWidget,
    };
    const updated = [...messages];
    updated[idx] = newMsg;
    updateMessages(updated);

    try {
      await fetch('/api/step/navigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSessionId,
          target_step_index: targetIdx,
        }),
      });
    } catch (err) {
      console.error('Failed to sync step navigation with backend:', err);
    }
  };

  const handleOpenAllSteps = (msgId: string, widget: any) => {
    if (!widget || !widget.steps) return;
    setActiveDrawerSteps(widget.steps);
    setActiveDrawerStepIdx(widget.current_step_index ?? 0);
    setActiveDrawerMsgId(msgId);
    setIsAllStepsDrawerOpen(true);
  };

  const handleInlineStepAnswer = async (
    msgId: string,
    stepIndex: number,
    studentAnswer: string,
    isCorrect: boolean
  ) => {
    const idx = messages.findIndex((m) => m.id === msgId);
    if (idx === -1) return;
    const targetMsg = messages[idx];
    const parsed = extractStepWidgetFromMessage(targetMsg);
    if (!parsed) return;

    const widget = targetMsg.stepWidget || parsed.widget;
    if (!widget.steps || stepIndex < 0 || stepIndex >= widget.steps.length) return;

    const currentStepObj = widget.steps[stepIndex];
    const updatedStep = {
      ...currentStepObj,
      status: isCorrect ? 'completed' : 'in_progress',
      student_answer: studentAnswer,
      studentAnswer: studentAnswer,
    };

    const newSteps = [...widget.steps];
    newSteps[stepIndex] = updatedStep;

    const existingCompleted: number[] = widget.completed_steps || [];
    const newCompleted =
      isCorrect && !existingCompleted.includes(stepIndex)
        ? [...existingCompleted, stepIndex]
        : existingCompleted;

    const newWidget = {
      ...widget,
      steps: newSteps,
      completed_steps: newCompleted,
    };

    const newMsg: ChatMessage = {
      ...targetMsg,
      stepWidget: newWidget,
    };

    const updated = [...messages];
    updated[idx] = newMsg;
    updateMessages(updated);

    if (isCorrect) {
      const isDone = newCompleted.length >= (widget.total_steps || widget.steps.length);
      if (isDone && activeProblem && worksheetQueue) {
        if (!celebrationShownRef.current.has(activeProblem.id)) {
          celebrationShownRef.current.add(activeProblem.id);
          setCelebratingProblemId(activeProblem.id);
          transitionMascotState('celebrating', 4000);
          onExerciseComplete?.(activeProblem.id);
        }
      } else {
        transitionMascotState('jumping', 2000);
      }
      /* Track activity */
      if (currentActivityRef.current) {
        const act = findActiveActivity(activeSessionId);
        if (act) {
          const nextSteps = (act.stepsCompleted || 0) + 1;
          updateActivity(currentActivityRef.current, {
            stepsCompleted: nextSteps,
            status: isDone ? 'completed' : 'in_progress',
          });
          if (isDone) currentActivityRef.current = null;
        }
      }
    } else {
      transitionMascotState('encouraging', 2000);
    }

    // Inform backend of step answer to keep session synchronized
    try {
      await fetch('/api/step/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSessionId,
          step_number: stepIndex + 1,
          student_answer: studentAnswer,
          is_correct: isCorrect,
        }),
      });
    } catch (err) {
      // Graceful offline fallback
    }
  };

  const chatEndRef = useRef<HTMLDivElement>(null);
  const isMountedRef = useRef(true);
  useEffect(() => {
    isMountedRef.current = true;
    return () => { isMountedRef.current = false; };
  }, []);



  useEffect(() => {
    if (!initialQuery?.trim()) return;
    const queryText = initialQuery.trim();
    onClearInitialQuery?.();

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      textEng: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const updatedWithUser = [...messages, userMsg];
    updateMessages(updatedWithUser);
    setIsSayoThinking(true);
    lastInteractionRef.current = Date.now();

    askTunsayTutor(queryText, activeProblem, profile.language, activeSessionId).then((sayoRes) => {
      if (!isMountedRef.current) return;
      setIsSayoThinking(false);

      const sayoMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'sayo',
        textKhmer: sayoRes.textKhmer,
        textEng: sayoRes.textEng,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isSafetyRefusal: sayoRes.isSafetyRefusal ?? false,
        stepWidget: sayoRes.stepWidget,
      };
      updateMessages([...updatedWithUser, sayoMsg]);

      if (sayoMsg.isSafetyRefusal) {
        transitionMascotState('encouraging', 3000);
      } else {
        const nextState = determineMascotStateFromResponse(sayoMsg.textEng || '');
        if (nextState === 'celebrating' || nextState === 'jumping' || nextState === 'encouraging' || nextState === 'happy') {
          transitionMascotState(nextState, 3000);
        } else {
          setSayoStatus(nextState);
        }
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  const shouldAutoScrollToBottomRef = useRef(false);

  useEffect(() => {
    if (shouldAutoScrollToBottomRef.current) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      shouldAutoScrollToBottomRef.current = false;
    }
  }, [messages, isSayoThinking]);

  const currentStep = activeProblem?.steps?.[currentStepIndex];

  const handleNewChat = () => {
    setActiveProblem(undefined);
    // Reset ALL step-related state so every new session starts at Step 1
    setCurrentStepIndex(0);
    setMaxUnlockedStepIndex(0);
    setCompletedStepIndices([]);
    setProblemStepProgress({});
    setCelebratingProblemId(null);
    celebrationShownRef.current.clear();
    onNewSession();
  };

  const handleResetProgress = () => {
    if (!activeProblem?.id) return;
    // Reset all step state back to Step 1
    setCurrentStepIndex(0);
    setMaxUnlockedStepIndex(0);
    setCompletedStepIndices([]);
    setCelebratingProblemId(null);
    celebrationShownRef.current.delete(activeProblem.id);
    // Remove saved progress for this exercise from session
    const updatedProgress = { ...problemStepProgress };
    delete updatedProgress[activeProblem.id];
    setProblemStepProgress(updatedProgress);
    updateMessages(messages, updatedProgress);
  };


  const isAdvancingStepRef = useRef(false);

  const handleStepAnswer = async (studentAnswer: string): Promise<boolean> => {
    if (!currentStep || isAdvancingStepRef.current) return false;

    const stepNum = currentStep.stepNumber || currentStepIndex + 1;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      textEng: `[Step ${stepNum}]: ${studentAnswer}`,
      textKhmer: `[ជំហានទី ${stepNum}]: ${studentAnswer}`,
      problemId: activeProblem?.id,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const updatedWithUser = [...messages, userMsg];
    updateMessages(updatedWithUser);
    setIsSayoThinking(true);
    lastInteractionRef.current = Date.now();

    // Fast deterministic validation (< 1ms)
    const fastResult = fastValidateStepAnswer(
      studentAnswer,
      currentStep,
      profile.language,
      activeProblem,
      currentStepIndex
    );

    let isCorrect = fastResult.isCorrect;
    let tutorReplyKhmer = fastResult.tutorReplyKhmer;
    let tutorReplyEng = fastResult.tutorReplyEng;

    if (fastResult.isDeterministic) {
      // Numbers, arithmetic, MCQs, and binary choices are verified in 0ms!
      setIsSayoThinking(false);
    } else {
      // Only for open-ended conceptual explanations: evaluate with LLM
      const evalPrompt = `[Student Answer Evaluation for Step ${stepNum}: "${currentStep.questionEng || currentStep.questionKhmer}"]. The student answered: "${studentAnswer}". The target expected concept is: "${currentStep.correctAnswer}". Please determine if this answer is conceptually correct, nearly correct, or needs rethinking. Explain encouragingly in child-friendly words.`;
      
      try {
        const sayoRes = await askTunsayTutor(evalPrompt, activeProblem, profile.language, activeSessionId);
        setIsSayoThinking(false);

        if (sayoRes?.textKhmer || sayoRes?.textEng) {
          tutorReplyKhmer = sayoRes.textKhmer || '';
          tutorReplyEng = sayoRes.textEng || '';

          const combined = (tutorReplyEng + ' ' + tutorReplyKhmer).toLowerCase();
          const isAffirmative = combined.includes('correct') ||
            combined.includes('spot on') ||
            combined.includes('great job') ||
            combined.includes('ត្រឹមត្រូវ') ||
            combined.includes('ល្អណាស់') ||
            combined.includes('ពូកែណាស់');
          const isNegative = combined.includes('not quite') ||
            combined.includes('incorrect') ||
            combined.includes('try again') ||
            combined.includes('មិនទាន់ត្រឹមត្រូវ') ||
            combined.includes('ព្យាយាមម្តងទៀត');

          if (isAffirmative && !isNegative) {
            isCorrect = true;
          }
        }
      } catch {
        setIsSayoThinking(false);
      }
    }

    // Sync answer to backend in background
    if (activeSessionId) {
      fetch('/api/step/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSessionId,
          step_number: stepNum,
          student_answer: studentAnswer,
        })
      }).catch(() => {});
    }

    const tutorMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      sender: 'sayo',
      textKhmer: tutorReplyKhmer,
      textEng: tutorReplyEng,
      problemId: activeProblem?.id,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const updated = [...updatedWithUser, tutorMsg];

    if (isCorrect) {
      isAdvancingStepRef.current = true;
      const nextIdx = currentStepIndex + 1;
      const updatedCompleted = completedStepIndices.includes(currentStepIndex)
        ? completedStepIndices
        : [...completedStepIndices, currentStepIndex];
      const updatedMax = Math.max(maxUnlockedStepIndex, nextIdx);

      setCompletedStepIndices(updatedCompleted);
      setMaxUnlockedStepIndex(updatedMax);

      const updatedProgress = activeProblem?.id ? {
        ...problemStepProgress,
        ...(activeSession?.problemStepProgress || {}),
        [activeProblem.id]: {
          currentStepIndex: nextIdx,
          maxUnlockedStepIndex: updatedMax,
          completedStepIndices: updatedCompleted,
        }
      } : problemStepProgress;

      setProblemStepProgress(updatedProgress);
      updateMessages(updated, updatedProgress);
      lastInteractionRef.current = Date.now();

      if (activeProblem && nextIdx < activeProblem.steps.length) {
        setTimeout(() => {
          setCurrentStepIndex(nextIdx);
          isAdvancingStepRef.current = false;
        }, 900);
      } else if (activeProblem && nextIdx >= activeProblem.steps.length) {
        setTimeout(() => {
          if (!celebrationShownRef.current.has(activeProblem.id)) {
            celebrationShownRef.current.add(activeProblem.id);
            setCelebratingProblemId(activeProblem.id);
            transitionMascotState('celebrating', 4000);
            onExerciseComplete?.(activeProblem.id);
          }
          isAdvancingStepRef.current = false;
        }, 800);
      }
      transitionMascotState('jumping', 2000);

      /* Track: correct step */
      if (currentActivityRef.current) {
        const act = findActiveActivity(activeSessionId);
        if (act) {
          const nextSteps = act.stepsCompleted + 1;
          const isDone = activeProblem ? nextSteps >= activeProblem.steps.length : false;
          updateActivity(currentActivityRef.current, {
            stepsCompleted: nextSteps,
            status: isDone ? 'completed' : 'in_progress',
          });
          if (isDone) currentActivityRef.current = null;
        }
      }
    } else {
      updateMessages(updated);
      transitionMascotState('encouraging', 2500);

      /* Track: wrong attempt */
      if (currentActivityRef.current) {
        const act = findActiveActivity(activeSessionId);
        if (act) {
          updateActivity(currentActivityRef.current, {
            wrongAttempts: act.wrongAttempts + 1,
          });
        }
      }
    }

    return isCorrect;
  };

  const handleSendMessage = async () => {
    if (!inputQuery.trim()) return;

    const userText = inputQuery.trim();
    setInputQuery('');
    shouldAutoScrollToBottomRef.current = true;

    // Always try to match the typed text to a known exercise case.
    // If a DIFFERENT case is matched, reset progress and switch to the new problem.
    let currentProblem = activeProblem;
    const matchedId = matchCaseId(userText);
    if (matchedId && matchedId !== activeProblem?.id) {
      // User typed a new problem — switch to it
      const newProblem = enrichProblemFromCase(
        {
          id: matchedId,
          titleKhmer: `លំហាត់ ${matchedId}`,
          titleEng: `Exercise ${matchedId}`,
          grade: profile.grade,
          subject: profile.subject,
          problemStatementKhmer: '',
          problemStatementEng: userText,
          steps: [],
        },
        profile.grade
      );
      if (newProblem) {
        currentProblem = newProblem;
        setActiveProblem(newProblem);
        // Reset step progress for the new problem
        setCurrentStepIndex(0);
        setMaxUnlockedStepIndex(0);
        setCompletedStepIndices([]);
        setCelebratingProblemId(null);
      }
    } else if (!currentProblem && matchedId) {
      // No active problem yet — set one from the match
      const newProblem = enrichProblemFromCase(
        {
          id: matchedId,
          titleKhmer: `លំហាត់ ${matchedId}`,
          titleEng: `Exercise ${matchedId}`,
          grade: profile.grade,
          subject: profile.subject,
          problemStatementKhmer: '',
          problemStatementEng: userText,
          steps: [],
        },
        profile.grade
      );
      if (newProblem) {
        currentProblem = newProblem;
        setActiveProblem(newProblem);
      }
    }

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      textEng: userText,
      problemId: currentProblem?.id,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const updatedWithUser = [...messages, userMsg];
    updateMessages(updatedWithUser);
    setIsSayoThinking(true);
    lastInteractionRef.current = Date.now();

    const sayoRes = await askTunsayTutor(userText, currentProblem, profile.language, activeSessionId);
    if (!isMountedRef.current) return;

    setIsSayoThinking(false);

    const sayoMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      sender: 'sayo',
      textKhmer: sayoRes.textKhmer,
      textEng: sayoRes.textEng,
      problemId: currentProblem?.id,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isSafetyRefusal: sayoRes.isSafetyRefusal ?? false,
      stepWidget: sayoRes.stepWidget,
    };

    updateMessages([...updatedWithUser, sayoMsg]);

    if (sayoMsg.isSafetyRefusal) {
      transitionMascotState('encouraging', 3000);
    } else {
      const nextState = determineMascotStateFromResponse(sayoMsg.textEng || '');
      if (nextState === 'celebrating' || nextState === 'jumping' || nextState === 'encouraging' || nextState === 'happy') {
        transitionMascotState(nextState, 3000);
      } else {
        setSayoStatus(nextState);
      }
    }
  };

  // 💬 Session list helpers 💬
  const getSessionPreview = (session: ChatSession): string => {
    const lastMsg = session.messages[session.messages.length - 1];
    if (!lastMsg) return '';
    const text = lastMsg.sender === 'user'
      ? (isKhmer ? lastMsg.textKhmer : lastMsg.textEng)
      : (isKhmer ? lastMsg.textKhmer : lastMsg.textEng);
    return (text || '').slice(0, 40) + ((text || '').length > 40 ? '...' : '');
  };

  const formatSessionTime = (iso: string): string => {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    } catch { return ''; }
  };

  const renderSidebarPanel = (isMobile = false) => (
    <div className="flex-1 flex flex-col h-full overflow-hidden select-none relative">
      {/* Decorative blobs */}
      <div className="absolute -top-10 -left-10 w-28 h-28 bg-[#40916C]/20 rounded-full blur-sm pointer-events-none" />
      <div className="absolute -bottom-10 -right-10 w-28 h-28 bg-[#2D6A4F]/20 rounded-full blur-sm pointer-events-none" />

      {/* Mascot area */}
      <div className="flex flex-col items-center gap-2 pt-3 pb-2.5 px-3 relative z-10 shrink-0 border-b-2 border-[#1B4332]/15">
        <div className="w-full max-w-[220px]">
          {(() => {
            const badges: Record<TunsayState, { text: string; style: string; icon: 'ping' | 'sparkle' | 'dot' | 'none' }> = {
              thinking:    { text: isKhmer ? 'កំពុងគិត...' : 'Thinking...', style: 'bg-[#2D6A4F] text-white animate-pulse', icon: 'ping' },
              celebrating: { text: isKhmer ? 'រួចរាល់!' : 'Done!', style: 'bg-[#2D6A4F] text-white animate-bounce', icon: 'sparkle' },
              jumping:     { text: isKhmer ? 'អស្ចារ្យ!' : 'Amazing!', style: 'bg-[#2D6A4F] text-white animate-bounce', icon: 'sparkle' },
              encouraging: { text: isKhmer ? 'កុំបារំរ!' : 'No worries!', style: 'bg-[#A7CDB4] text-[#1B4332]', icon: 'dot' },
              listening:   { text: isKhmer ? 'ស្ដាប់...' : 'Listening...', style: 'bg-[#A7CDB4] text-[#1B4332] animate-pulse', icon: 'dot' },
              explaining:  { text: isKhmer ? 'ពន្យល់...' : 'Explaining...', style: 'bg-[#A7CDB4] text-[#1B4332]', icon: 'dot' },
              waving:      { text: isKhmer ? 'សួស្ដី!' : 'Hello!', style: 'bg-[#A7CDB4] text-[#1B4332] animate-bounce', icon: 'dot' },
              happy:       { text: isKhmer ? 'ល្អ!' : 'Yay!', style: 'bg-[#2D6A4F] text-white animate-bounce', icon: 'sparkle' },
              confused:    { text: isKhmer ? 'ហ៊ឹម...' : 'Hmm...', style: 'bg-[#A7CDB4] text-[#1B4332]', icon: 'dot' },
              sleeping:    { text: isKhmer ? 'សម្រាក...' : 'Resting...', style: 'bg-gray-200 text-gray-700', icon: 'none' },
              idle:        { text: isKhmer ? 'ReanMore AI Tutor' : 'ReanMore AI Tutor', style: 'bg-[#A7CDB4] text-[#1B4332]', icon: 'dot' },
            };
            const b = badges[sayoStatus];
            return (
              <span className={`px-2.5 py-1 text-[11px] font-black rounded-full border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] inline-flex items-center justify-center gap-1.5 uppercase tracking-wider w-full ${b.style}`}>
                {b.icon === 'ping' && <span className="w-2 h-2 bg-white rounded-full animate-ping shrink-0" />}
                {b.icon === 'sparkle' && <Sparkles className="w-3 h-3 text-white" />}
                {b.icon === 'dot' && <span className="w-2 h-2 bg-[#2D6A4F] rounded-full border border-[#1B4332] shrink-0" />}
                <span className="truncate">{b.text}</span>
              </span>
            );
          })()}
        </div>

        <div className="flex flex-col items-center justify-center transition-all duration-300 transform w-full">
          <div className={`transition-all duration-300 ${
            sayoStatus === 'thinking' ? 'scale-105' : sayoStatus === 'celebrating' || sayoStatus === 'jumping' || sayoStatus === 'happy' ? 'scale-110 animate-bounce' : 'scale-100 hover:scale-105'
          }`}>
            <TunsayAvatar size={isMobile ? 'md' : 'lg'} state={sayoStatus} showBadge={false} />
          </div>

          <div className="mt-1.5 px-2.5 w-full max-w-[240px] bg-white rounded-xl p-2 border-2 sm:border-2.5 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] relative">
            <div className="w-2.5 h-2.5 bg-white border-t-2 border-l-2 sm:border-t-2.5 sm:border-l-2.5 border-[#1B4332] rotate-45 absolute -top-1.5 left-1/2 -translate-x-1/2" />
            <p className="font-heading font-black text-xs text-[#1B4332] leading-snug text-center transition-all duration-300 line-clamp-2">
              {getMascotContextText(sayoStatus)}
            </p>
          </div>
        </div>
      </div>

      {/* Session History List / Worksheet Progress Panel */}
      {sidebarMode === 'worksheet' && worksheetQueue && worksheetQueue.problems.length > 1 ? (
        <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
          <WorksheetProgressPanel
            problems={worksheetQueue.problems}
            activeIndex={worksheetQueue.activeIndex}
            completedIds={worksheetQueue.completedIds}
            language={profile.language}
            {...(worksheetQueue.worksheetTitle ? { worksheetTitle: worksheetQueue.worksheetTitle } : {})}
            onSelectExercise={(idx) => {
              onSelectExercise?.(idx);
              if (isMobile) setIsMobileSidebarOpen(false);
            }}
            onViewAllChats={() => setSidebarMode('chats')}
          />
        </div>
      ) : (
        <div className="flex-1 min-h-0 overflow-y-auto px-2.5 sm:px-3 py-2.5 sm:py-3 space-y-2 relative z-10 overscroll-contain">
          {/* Active Worksheet Quick Return Banner */}
          {worksheetQueue && worksheetQueue.problems.length > 1 && (
            <button
              type="button"
              onClick={() => setSidebarMode('worksheet')}
              className="w-full mb-2 px-2.5 py-1.5 bg-[#40916C]/15 hover:bg-[#40916C]/25 border-2 border-[#1B4332] rounded-xl flex items-center justify-between text-left transition-all shadow-[1.5px_1.5px_0px_#1B4332] cursor-pointer"
            >
              <div className="flex items-center gap-1.5 min-w-0">
                <Layers className="w-3.5 h-3.5 text-[#1B4332] shrink-0" />
                <span className="text-[10px] sm:text-xs font-black text-[#1B4332] truncate">
                  {isKhmer ? `ទំព័រលំហាត់ (${worksheetQueue.problems.length} លំហាត់)` : `Worksheet (${worksheetQueue.problems.length} Exercises)`}
                </span>
              </div>
              <span className="text-[9px] font-black text-[#2D6A4F] bg-white px-1.5 py-0.5 rounded-md shrink-0 border border-[#1B4332]/20">
                {isKhmer ? 'មើលលំហាត់ →' : 'View Page →'}
              </span>
            </button>
          )}

          <div className="flex items-center justify-between mb-1.5 px-0.5">
            <p className="text-xs sm:text-sm font-black text-[#1B4332] uppercase tracking-wider flex items-center gap-1.5">
              <span>{isKhmer ? 'ប្រវត្តិជជែក' : 'Recent Chats'}</span>
              <span className="text-[10px] px-1.5 py-0.5 bg-[#40916C]/20 text-[#1B4332] rounded-full font-bold">
                {sessions.length}
              </span>
            </p>
            <button
              onClick={() => {
                handleNewChat();
                if (isMobile) setIsMobileSidebarOpen(false);
              }}
              className="text-xs font-black text-[#1B4332] bg-white hover:bg-[#A7CDB4] border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] active:translate-y-0.5 px-2.5 py-1 rounded-lg flex items-center gap-1 cursor-pointer transition-all"
              title={isKhmer ? 'ចាប់ផ្តើមជជែកថ្មី' : 'New Chat'}
            >
              <Plus className="w-3.5 h-3.5 stroke-[3]" />
              <span>{isKhmer ? 'ថ្មី' : 'New'}</span>
            </button>
          </div>

          {sessions.map((session) => {
            const isActive = session.id === activeSessionId;
            const hasWorksheet = Boolean(session.worksheetQueue && session.worksheetQueue.problems && session.worksheetQueue.problems.length > 1);
            const wsTotal = session.worksheetQueue?.problems?.length || 0;
            const wsDone = session.worksheetQueue?.completedIds?.length || 0;

            return (
              <div
                key={session.id}
                role="button"
                tabIndex={0}
                onClick={() => {
                  onSelectSession(session.id);
                  if (hasWorksheet) {
                    setSidebarMode('worksheet');
                  }
                  if (isMobile) setIsMobileSidebarOpen(false);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    onSelectSession(session.id);
                    if (hasWorksheet) setSidebarMode('worksheet');
                    if (isMobile) setIsMobileSidebarOpen(false);
                  }
                }}
                className={`w-full text-left rounded-xl border-2 sm:border-2.5 p-2.5 sm:p-3 transition-all cursor-pointer group ${
                  isActive
                    ? 'bg-white border-[#1B4332] shadow-[2.5px_2.5px_0px_#1B4332] translate-x-0.5'
                    : 'bg-white/80 hover:bg-white border-[#1B4332]/30 hover:border-[#1B4332] shadow-[1.5px_1.5px_0px_rgba(27,67,50,0.12)] hover:shadow-[2.5px_2.5px_0px_#1B4332]'
                }`}
              >
                <div className="flex items-start gap-2 sm:gap-2.5">
                  <div className={`p-1.5 rounded-lg border-2 shrink-0 mt-0.5 ${
                    hasWorksheet
                      ? 'bg-[#40916C] text-white border-[#1B4332]'
                      : isActive
                      ? 'bg-[#A7CDB4] text-[#1B4332] border-[#1B4332]'
                      : 'bg-[#E8F5E9] text-[#1B4332] border-[#1B4332]/40 group-hover:border-[#1B4332]'
                  }`}>
                    {hasWorksheet ? (
                      <Layers className="w-3.5 h-3.5 stroke-[2.5]" />
                    ) : (
                      <MessageSquare className="w-3.5 h-3.5 stroke-[2.5]" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <p className="text-xs sm:text-sm font-black text-[#1B4332] truncate leading-tight">
                        {isKhmer ? session.titleKhmer : session.title}
                      </p>
                      {hasWorksheet && (
                        <span className="text-[9px] font-black bg-[#A7CDB4]/40 text-[#1B4332] px-1.5 py-0.5 rounded border border-[#1B4332]/30 shrink-0">
                          {wsTotal} {isKhmer ? 'លំហាត់' : 'Ex'}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] sm:text-xs font-bold text-[#1B4332]/75 truncate mt-0.5 leading-snug">
                      {hasWorksheet && wsDone > 0 ? (
                        <span className="text-[#2D6A4F] font-bold">
                          ✓ {wsDone}/{wsTotal} {isKhmer ? 'រួចរាល់' : 'done'} • {getSessionPreview(session)}
                        </span>
                      ) : (
                        getSessionPreview(session)
                      )}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <span className="text-[9px] sm:text-[10px] font-black text-[#1B4332]/70 bg-[#A7CDB4]/30 px-1.5 py-0.5 rounded-md">
                      {formatSessionTime(session.updatedAt)}
                    </span>
                    {sessions.length > 1 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteSession(session.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 transition-opacity text-[#1B4332]/40 hover:text-red-600 hover:scale-110 p-0.5 cursor-pointer"
                        title={isKhmer ? 'លុប' : 'Delete'}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="w-full pt-2.5 pb-2.5 px-3 border-t-2 border-[#1B4332]/20 relative z-10 shrink-0 bg-white/40">
        <p className="text-[11px] sm:text-xs font-black text-[#1B4332] uppercase tracking-widest truncate text-center">
          ReanMore WEG
        </p>
      </div>
    </div>
  );

  return (
    <div className="w-full h-full flex-1 flex flex-row items-stretch gap-2.5 sm:gap-4 lg:gap-5 overflow-hidden">
      {/* Desktop Left Panel: Mascot + Session History */}
      <div
        className="hidden lg:flex lg:w-[28%] lg:min-w-[260px] lg:max-w-[340px] shrink-0 h-full max-h-full bg-[#E8F5E9] rounded-2xl lg:rounded-3xl border-2 sm:border-3 border-[#1B4332] shadow-[4px_4px_0px_#1B4332] lg:shadow-[6px_6px_0px_#1B4332] flex-col select-none z-10 relative overflow-hidden min-h-0"
      >
        {renderSidebarPanel(false)}
      </div>

      {/* Mobile Slide-Over Drawer (ChatGPT Mobile Inspired) */}
      {isMobileSidebarOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden animate-fadeIn">
          {/* Backdrop overlay */}
          <div
            className="fixed inset-0 bg-[#1B4332]/60 backdrop-blur-xs transition-opacity cursor-pointer"
            onClick={() => setIsMobileSidebarOpen(false)}
          />
          {/* Drawer container */}
          <div className="relative w-[85%] max-w-[320px] h-full bg-[#E8F5E9] shadow-2xl flex flex-col border-r-3 border-[#1B4332] z-10 animate-slideInLeft overflow-hidden">
            <div className="flex items-center justify-between p-3 bg-[#1B4332] text-white border-b-2 border-[#1B4332] shrink-0">
              <div className="flex items-center gap-2">
                <TunsayAvatar size="sm" state={sayoStatus} showBadge={false} />
                <span className="font-black text-sm">{isKhmer ? 'ប្រវត្តិជជែក' : 'Recent Chats'}</span>
              </div>
              <button
                type="button"
                onClick={() => setIsMobileSidebarOpen(false)}
                className="p-1.5 rounded-lg bg-[#40916C] hover:bg-white hover:text-[#1B4332] text-white transition-colors cursor-pointer border border-[#1B4332]"
                title="Close"
              >
                <X className="w-4 h-4 stroke-[3]" />
              </button>
            </div>
            {renderSidebarPanel(true)}
          </div>
        </div>
      )}

      {/* Main Chat Frame */}
      <div className="flex-1 min-w-0 h-full flex flex-col bg-[#E8F5E9] rounded-xl sm:rounded-3xl border-2 sm:border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] sm:shadow-[6px_6px_0px_#1B4332] overflow-hidden relative">
        {/* Top Navigation Bar */}
        <div className="shrink-0 z-20 px-2.5 sm:px-5 py-2 sm:py-2.5 bg-[#1B4332] border-b-2 sm:border-b-3 border-[#1B4332] flex items-center justify-between gap-1.5 sm:gap-3 shadow-[0_2px_0px_#1B4332] sm:shadow-[0_3px_0px_#1B4332]">
          <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
            {/* Mobile History / Menu Toggle Button */}
            <button
              type="button"
              onClick={() => setIsMobileSidebarOpen(true)}
              className="lg:hidden p-1.5 sm:p-2 bg-[#40916C] text-white hover:bg-white hover:text-[#1B4332] rounded-lg sm:rounded-xl border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] flex items-center justify-center cursor-pointer transition-all active:translate-y-0.5 shrink-0"
              title={isKhmer ? 'ប្រវត្តិជជែក' : 'Chat History'}
            >
              <Menu className="w-4 h-4 stroke-[2.5]" />
            </button>

            <div className="relative">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-[#40916C] rounded-lg sm:rounded-2xl flex items-center justify-center border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332]">
                <TunsayAvatar size="sm" state={isSayoThinking ? 'thinking' : 'idle'} showBadge={false} />
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 sm:w-3 sm:h-3 bg-[#2D6A4F] border-2 border-[#1B4332] rounded-full" title="Online" />
            </div>

            <div>
              <h3 className="font-black text-xs sm:text-sm md:text-base text-white flex items-center gap-1 font-heading leading-tight drop-shadow-[1px_1px_0px_#1B4332]">
                {isKhmer ? 'ReanMore' : 'ReanMore AI'}
              </h3>
              <p className="text-[10px] sm:text-xs text-white font-black flex items-center gap-1 drop-shadow-[1px_1px_0px_#1B4332]">
                <GraduationCap className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-white" />
                {isKhmer ? `ថ្នាក់ទី ${profile.grade}` : `Grade ${profile.grade}`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            <button
              type="button"
              onClick={handleNewChat}
              className="w-8 h-8 sm:w-10 sm:h-10 bg-[#40916C] text-white hover:bg-white hover:text-[#1B4332] rounded-lg sm:rounded-2xl flex items-center justify-center transition-all cursor-pointer border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] active:translate-x-0.5 active:translate-y-0.5 shrink-0"
              title={isKhmer ? 'ចាប់ផ្តើមជជែកថ្មី' : 'New Chat'}
            >
              <Plus className="w-4 h-4 sm:w-5 sm:h-5 stroke-[3]" />
            </button>

            {onBackToHome && (
              <button
                type="button"
                onClick={onBackToHome}
                className="px-2.5 sm:px-3.5 py-1.5 bg-[#40916C] text-white hover:bg-white hover:text-[#1B4332] rounded-lg sm:rounded-2xl text-xs sm:text-sm font-black transition-all flex items-center gap-1 cursor-pointer border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] active:translate-x-0.5 active:translate-y-0.5 shrink-0"
              >
                <ArrowLeft className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[3]" />
                <span className="hidden min-[380px]:inline">{isKhmer ? 'ទំព័រដើម' : 'Home'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Worksheet Exercise Bar — shown above scrollable area when multi-exercise queue active */}
        {worksheetQueue && worksheetQueue.problems.length > 1 && (
          <WorksheetExerciseBar
            problems={worksheetQueue.problems}
            activeIndex={worksheetQueue.activeIndex}
            completedIds={worksheetQueue.completedIds}
            language={profile.language}
            onSelectExercise={(idx) => onSelectExercise?.(idx)}
            onViewAllChats={() => setSidebarMode('chats')}
          />
        )}

        {/* Scrollable Conversation Area */}
        <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-2.5 sm:p-4 lg:p-6 space-y-3 sm:space-y-4 lg:space-y-5">
          {/* Celebration banner — shown inline after exercise completion */}
          {activeProblem && celebratingProblemId === activeProblem.id && worksheetQueue && (() => {
            const exIdx = worksheetQueue.problems.findIndex(p => p.id === celebratingProblemId);
            const hasNext = worksheetQueue.problems.some(
              (p, i) => i > exIdx && !worksheetQueue.completedIds.includes(p.id)
            );
            return (
              <ExerciseCelebrationBanner
                exerciseNumber={exIdx + 1}
                totalExercises={worksheetQueue.problems.length}
                exerciseTitleKhmer={activeProblem.titleKhmer}
                exerciseTitleEng={activeProblem.titleEng}
                language={profile.language}
                hasNext={hasNext}
                onNext={() => {
                  setCelebratingProblemId(null);
                  const nextIdx = worksheetQueue.problems.findIndex(
                    (p, i) => i > exIdx && !worksheetQueue.completedIds.includes(p.id)
                  );
                  if (nextIdx !== -1) onSelectExercise?.(nextIdx);
                }}
                onReview={() => setCelebratingProblemId(null)}
              />
            );
          })()}


          {(() => {
            const displayedMessages = messages.filter((msg) => {
              // Always show messages with no problemId (welcome messages, general chat)
              if (!msg.problemId && !msg.problem?.id) return true;
              // If there's an active problem, show only its messages
              if (activeProblem) {
                if (msg.problemId) return msg.problemId === activeProblem.id;
                if (msg.problem?.id) return msg.problem.id === activeProblem.id;
              }
              // No active problem — show everything
              return true;
            });

            return displayedMessages.map((msg) => {
              const isUser = msg.sender === 'user';
              let displayText = '';
              if (isUser) {
                displayText = msg.textEng || msg.textKhmer || '';
              } else {
                displayText = isKhmer ? (msg.textKhmer || msg.textEng || '') : (msg.textEng || msg.textKhmer || '');
              }

              const stepCardData = !isUser ? extractStepWidgetFromMessage(msg) : null;

              return (
                <div
                  key={msg.id}
                  className={`flex items-start gap-2 sm:gap-3 w-full ${isUser ? 'flex-row-reverse' : 'flex-row'} animate-fadeIn`}
                >
                {!isUser ? (
                  <div className="w-8 h-8 sm:w-10 sm:h-10 bg-[#40916C] rounded-lg sm:rounded-2xl shrink-0 border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] flex items-center justify-center p-0.5">
                    <TunsayAvatar size="sm" state={msg.isSafetyRefusal ? 'encouraging' : 'explaining'} showBadge={false} />
                  </div>
                ) : (
                  <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-2xl bg-[#A7CDB4] text-[#1B4332] border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] font-black flex items-center justify-center shrink-0 overflow-hidden">
                    {profile.avatarUrl ? (
                      <img src={profile.avatarUrl} alt="You" className="w-full h-full object-cover" />
                    ) : (
                      <User className="w-4 h-4 sm:w-5 sm:h-5" />
                    )}
                  </div>
                )}

                {stepCardData ? (
                  <div className="w-full max-w-[94%] sm:max-w-[85%] flex flex-col gap-2 min-w-0">
                    {stepCardData.introText && (
                      <div className="p-2.5 sm:p-4 rounded-xl sm:rounded-2xl bg-white text-[#1B4332] border-2 sm:border-2.5 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[2.5px_2.5px_0px_#1B4332] speech-tail-left text-xs sm:text-sm font-black leading-relaxed">
                        {stepCardData.introText}
                      </div>
                    )}
                    <StepChatBubble
                      step={stepCardData.activeStep}
                      stepIndex={stepCardData.activeIdx}
                      totalSteps={stepCardData.totalSteps}
                      language={profile.language}
                      visualData={activeProblem?.visualData || (activeProblem?.id ? ALL_HARDCODED_CASES[activeProblem.id]?.visual_data : null) || (stepCardData.widget as any)?.visualData}
                      completedStepIndices={stepCardData.completedSteps}
                      isLatest={msg.id === messages[messages.length - 1]?.id}
                      onOpenHints={() => {
                        setActiveModalStep(stepCardData.activeStep);
                        setIsHintOpen(true);
                        handleStepHint(msg.id);
                      }}
                      onOpenExplainDifferently={() => {
                        setActiveModalStep(stepCardData.activeStep);
                        setIsExplainOpen(true);
                      }}
                      onOpenAllSteps={() => handleOpenAllSteps(msg.id, stepCardData.widget)}
                      onNavigateStep={(targetIdx) => handleStepNavigate(msg.id, targetIdx)}
                      onStepAnswerSubmit={(stepIdx, ans, isCorrect) =>
                        handleInlineStepAnswer(msg.id, stepIdx, ans, isCorrect)
                      }
                    />
                    <span className="text-[10px] block font-black opacity-60 ml-2">
                      {msg.timestamp}
                    </span>
                  </div>
                ) : (
                  <div
                    className={`max-w-[88%] sm:max-w-[80%] min-w-0 p-2.5 sm:p-4 md:p-5 rounded-xl sm:rounded-3xl border-2 sm:border-3 border-[#1B4332] text-xs sm:text-sm md:text-base leading-relaxed break-words overflow-hidden ${
                      isUser
                        ? 'bg-[#1B4332] text-white shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] speech-tail-right'
                        : msg.isSafetyRefusal
                        ? 'bg-[#2D6A4F] text-white shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] speech-tail-left'
                        : 'bg-white text-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] speech-tail-left'
                    }`}
                  >
                    <div className="font-black text-xs sm:text-sm md:text-base leading-relaxed break-words whitespace-pre-wrap">
                      {formatMessageText(displayText)}
                    </div>
                    <span className="text-[9px] sm:text-[10px] mt-1.5 block text-right font-black opacity-80">
                      {msg.timestamp}
                    </span>
                  </div>
                )}
              </div>
            );
          });
        })()}

          {/* Socratic Loading / Thinking Message Bubble */}
          {isSayoThinking && (
            <div className="flex items-start gap-2 sm:gap-3 w-full flex-row animate-fadeIn">
              <div className="w-8 h-8 sm:w-10 sm:h-10 bg-[#40916C] rounded-lg sm:rounded-2xl shrink-0 border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] sm:shadow-[2px_2px_0px_#1B4332] flex items-center justify-center p-0.5 animate-pulse">
                <TunsayAvatar size="sm" state="thinking" showBadge={false} />
              </div>
              <div className="max-w-[88%] sm:max-w-[80%] min-w-0 p-2.5 sm:p-4 rounded-xl sm:rounded-3xl border-2 sm:border-3 border-[#1B4332] bg-white text-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] speech-tail-left flex flex-col gap-1 sm:gap-1.5">
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 bg-[#E8F5E9] px-1.5 py-0.5 sm:px-2 sm:py-1 rounded-lg border border-[#A7CDB4]">
                    <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-[#40916C] rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                    <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-[#2D6A4F] rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                    <span className="w-1.5 h-1.5 sm:w-2 sm:h-2 bg-[#1B4332] rounded-full animate-bounce"></span>
                  </div>
                  <span className="text-xs sm:text-sm font-black text-[#1B4332]">
                    {isKhmer ? 'ReanMore កំពុងគិត...' : 'ReanMore is thinking...'}
                  </span>
                </div>
                <div className="text-[11px] sm:text-xs md:text-sm font-bold text-[#1B4332]/75 italic pl-0.5">
                  💭 {isKhmer ? thinkingTextsKhmer[thinkingTextIdx] : thinkingTextsEng[thinkingTextIdx]}
                </div>
              </div>
            </div>
          )}

          {/* Fresh Start: Scan Button */}
          {!activeProblem && messages.length <= 1 && (
            <div className="space-y-3 pt-1 pl-1 sm:pl-12 animate-fadeIn">
              <div className="flex flex-wrap gap-2.5">
                <button
                  type="button"
                  onClick={onOpenScanner}
                  className="px-3.5 py-2 sm:px-4 sm:py-2.5 bg-[#2D6A4F] text-white hover:bg-[#40916C] hover:text-white rounded-xl sm:rounded-2xl text-xs sm:text-sm font-black border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] flex items-center gap-1.5 sm:gap-2 transition-all cursor-pointer"
                >
                  <Camera className="w-4 h-4 stroke-[2.5]" />
                  <span>{isKhmer ? 'ស្កែនរូបថតលំហាត់' : 'Scan Homework Photo'}</span>
                </button>
              </div>
            </div>
          )}

          {activeProblem && (
            <div className="space-y-3 sm:space-y-4">
              {/* Scanned Problem Header Card */}
              {(activeProblem.problemStatementKhmer || activeProblem.problemStatementEng) && (
                <div className="p-3 sm:p-4 bg-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-[10px] font-black text-[#2D6A4F] uppercase tracking-wider">
                      {isKhmer 
                        ? `លំហាត់ស្កែនបាន ${worksheetQueue ? worksheetQueue.activeIndex + 1 : 1}` 
                        : `SCANNED PROBLEM ${worksheetQueue ? worksheetQueue.activeIndex + 1 : 1}`}
                    </p>
                    {completedStepIndices.length > 0 && (
                      <button
                        type="button"
                        onClick={handleResetProgress}
                        title={isKhmer ? 'ចាប់ផ្ដើមពីដើម' : 'Reset to Step 1'}
                        className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-black text-[#2D6A4F] border border-[#2D6A4F]/40 rounded-lg hover:bg-[#E8F5E9] hover:border-[#1B4332] transition-all cursor-pointer shrink-0"
                      >
                        <RotateCcw className="w-3 h-3" />
                        <span>{isKhmer ? 'ចាប់ផ្ដើមពីដើម' : 'Start fresh'}</span>
                      </button>
                    )}
                  </div>
                  <p className="text-sm sm:text-base md:text-lg font-black text-[#1B4332]">
                    {isKhmer 
                      ? (activeProblem.problemStatementKhmer || activeProblem.problemStatementEng)
                      : (activeProblem.problemStatementEng || activeProblem.problemStatementKhmer)}
                  </p>
                </div>
              )}

              {/* Step Trail */}
              {activeProblem.steps && activeProblem.steps.length > 0 && (
                <StepTrail
                  currentStep={currentStepIndex + 1}
                  totalSteps={activeProblem.steps.length}
                  completedSteps={completedStepIndices}
                  maxUnlockedStep={maxUnlockedStepIndex + 1}
                  language={profile.language}
                  onSelectStep={(stepIdx) => {
                    if (stepIdx <= maxUnlockedStepIndex || completedStepIndices.includes(stepIdx)) {
                      setCurrentStepIndex(stepIdx);
                    }
                  }}
                />
              )}

              {/* Step Card with Embedded Visual Manipulative */}
              {currentStep && (
                <StepCard
                  step={currentStep}
                  isCompleted={completedStepIndices.includes(currentStepIndex)}
                  language={profile.language}
                  visualData={activeProblem.visualData || (activeProblem.id ? ALL_HARDCODED_CASES[activeProblem.id]?.visual_data : null)}
                  onAnswerSubmit={handleStepAnswer}
                  onNextStep={
                    currentStepIndex < maxUnlockedStepIndex && currentStepIndex + 1 < (activeProblem?.steps?.length || 0)
                      ? () => setCurrentStepIndex(currentStepIndex + 1)
                      : undefined
                  }
                  onOpenHints={() => {
                    setActiveModalStep(currentStep || null);
                    setIsHintOpen(true);
                    if (currentActivityRef.current) {
                      const act = findActiveActivity(activeSessionId);
                      if (act) {
                        updateActivity(currentActivityRef.current, {
                          hintsUsed: act.hintsUsed + 1,
                        });
                      }
                    }
                  }}
                  onOpenExplainDifferently={() => {
                    setActiveModalStep(currentStep || null);
                    setIsExplainOpen(true);
                    if (currentActivityRef.current) {
                      const act = findActiveActivity(activeSessionId);
                      if (act) {
                        updateActivity(currentActivityRef.current, {
                          explainUsed: act.explainUsed + 1,
                        });
                      }
                    }
                  }}
                />
              )}
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Bottom Chat Input Bar */}
        <div className="px-2.5 sm:px-5 py-2 sm:py-3 bg-white border-t-2 sm:border-t-3 border-[#1B4332] shrink-0 pb-[max(0.5rem,env(safe-area-inset-bottom))]">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="w-full flex items-center gap-1.5 sm:gap-2.5"
          >
            <button
              type="button"
              onClick={onOpenScanner}
              className="w-10 h-10 sm:w-12 sm:h-12 bg-[#2D6A4F] text-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] flex items-center justify-center hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] transition-all cursor-pointer shrink-0"
              title={isKhmer ? 'ស្កែនរូបថតលំហាត់' : 'Scan Homework Photo'}
            >
              <Camera className="w-5 h-5 sm:w-6 sm:h-6 stroke-[2.5]" />
            </button>

            <div className="flex-1 bg-[#E8F5E9] rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] px-3 sm:px-4 flex items-center">
              <input
                type="text"
                value={inputQuery}
                disabled={isSayoThinking}
                onChange={(e) => {
                  const value = e.target.value;
                  setInputQuery(value);
                  lastInteractionRef.current = Date.now();
                  if (value.trim().length > 0 && sayoStatus !== 'thinking') {
                    setSayoStatus('listening');
                  }
                  if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
                  typingTimeoutRef.current = setTimeout(() => {
                    setSayoStatus(prev => prev === 'listening' ? 'idle' : prev);
                  }, 1500);
                }}
                placeholder={
                  isSayoThinking
                    ? (isKhmer ? 'ReanMore កំពុងគិត...' : 'ReanMore is thinking...')
                    : (isKhmer ? 'សួរអ្វីបន្ថែម ឬ "ខ្ញុំមិនយល់ទេ"...' : 'Ask for help or "I\'m stuck"...')
                }
                className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 text-xs sm:text-sm md:text-base py-2 sm:py-2.5 font-bold text-[#1B4332] placeholder:text-[#1B4332]/50 disabled:opacity-60"
              />
            </div>

            <button
              type="submit"
              disabled={!inputQuery.trim() || isSayoThinking}
              className="w-10 h-10 sm:w-12 sm:h-12 bg-[#1B4332] disabled:bg-gray-200 disabled:border-gray-400 text-white rounded-xl sm:rounded-2xl border-2 sm:border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] sm:shadow-[3px_3px_0px_#1B4332] font-black hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] transition-all flex items-center justify-center cursor-pointer shrink-0"
            >
              <Send className="w-4 h-4 sm:w-5 sm:h-5 stroke-[2.5]" />
            </button>
          </form>
        </div>
      </div>

      {/* Sheets Modals */}
      {(activeModalStep || currentStep) && (
        <>
          <HintSheet
            step={activeModalStep || currentStep!}
            isOpen={isHintOpen}
            language={profile.language}
            onClose={() => {
              setIsHintOpen(false);
              setActiveModalStep(null);
            }}
          />
          <ExplanationCard
            step={activeModalStep || currentStep!}
            isOpen={isExplainOpen}
            language={profile.language}
            onClose={() => {
              setIsExplainOpen(false);
              setActiveModalStep(null);
            }}
          />
        </>
      )}

      {/* Socratic Stepper Solution Journey Drawer */}
      <AllStepsDrawer
        steps={activeDrawerSteps}
        currentStepIndex={activeDrawerStepIdx}
        isOpen={isAllStepsDrawerOpen}
        language={profile.language}
        onSelectStep={(idx) => {
          if (activeDrawerMsgId) {
            handleStepNavigate(activeDrawerMsgId, idx);
          }
          setIsAllStepsDrawerOpen(false);
        }}
        onClose={() => setIsAllStepsDrawerOpen(false)}
      />
    </div>
  );
};

