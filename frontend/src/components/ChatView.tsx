import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  ChatMessage,
  HomeworkProblem,
  UserProfile,
  TunsayState,
  ChatSession,
  WorksheetQueue,
  StepItem,
} from '../types';
import { HintSheet } from './HintSheet';
import { ExplanationCard } from './ExplanationCard';
import { AllStepsDrawer } from './AllStepsDrawer';
import { MathKeypad } from './MathKeypad';
import { askTunsayTutor } from '../services/geminiService';
import { tutorApi } from '../api';
import { fastValidateStepAnswer } from '../services/answerValidationService';
import { updateActivity, findActiveActivity } from '../utils/reportUtils';
import {
  mapWidgetToStepItems,
  extractStepWidgetFromMessage,
  localizeStepsForKhmer,
  thinkingTextsEng,
  thinkingTextsKhmer,
} from './chat/chatUtils';
import { ChatHeader } from './chat/ChatHeader';
import { ChatSidebar } from './chat/ChatSidebar';
import { ChatMessageList } from './chat/ChatMessageList';
import { ChatInputBar } from './chat/ChatInputBar';

interface ChatViewProps {
  profile: UserProfile;
  initialProblem?: HomeworkProblem | undefined;
  initialQuery?: string | undefined;
  onClearInitialQuery?: () => void;
  sessions: ChatSession[];
  activeSessionId: string;
  activeSession?: ChatSession | undefined;
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
  activeSession: activeSessionProp,
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
  const activeSession = activeSessionProp ?? sessions.find((s) => s.id === activeSessionId);
  const messages = activeSession?.messages ?? [];
  const latestMessagesRef = useRef<ChatMessage[]>(messages);
  useEffect(() => {
    latestMessagesRef.current = messages;
  }, [messages]);

  const [activeProblem, setActiveProblem] = useState<HomeworkProblem | undefined>(initialProblem);

  // When the UI is Khmer, translate dynamic step content via /api/translate.
  // Text that is already Khmer (or an unavailable endpoint) is left untouched.
  useEffect(() => {
    if (profile.language !== 'km') return;
    const steps = activeProblem?.steps;
    if (!steps || steps.length === 0) return;
    let cancelled = false;
    localizeStepsForKhmer(steps).then((localized) => {
      if (cancelled || localized === steps) return;
      setActiveProblem((prev) => (prev ? { ...prev, steps: localized } : prev));
    });
    return () => {
      cancelled = true;
    };
  }, [profile.language, activeProblem?.id, activeProblem?.steps?.length]);

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
  const [problemStepProgress, setProblemStepProgress] = useState<
    Record<
      string,
      {
        currentStepIndex: number;
        maxUnlockedStepIndex: number;
        completedStepIndices: number[];
      }
    >
  >(() => activeSession?.problemStepProgress || {});

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
  const [isMathKeypadOpen, setIsMathKeypadOpen] = useState(false);
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
      setActiveProblem(initialProblem);
      setCelebratingProblemId(null);

      const progressSource = isNewSession
        ? activeSession?.problemStepProgress
        : problemStepProgress;

      if (initialProblem?.id && progressSource?.[initialProblem.id]) {
        const saved = progressSource[initialProblem.id];
        setCurrentStepIndex(saved.currentStepIndex ?? 0);
        setMaxUnlockedStepIndex(saved.maxUnlockedStepIndex ?? 0);
        setCompletedStepIndices(saved.completedStepIndices ?? []);
      } else {
        setCurrentStepIndex(0);
        setMaxUnlockedStepIndex(0);
        setCompletedStepIndices([]);
      }
    }
  }, [activeSessionId, initialProblem, activeSession?.problemStepProgress, problemStepProgress]);

  // Initial load check & exercise switch handler
  useEffect(() => {
    if (!initialProblem) {
      if (worksheetQueue && worksheetQueue.problems.length > 1) {
        setSidebarMode('worksheet');
      } else {
        setSidebarMode('chats');
      }
      return;
    }

    const enriched = initialProblem;
    setActiveProblem(enriched);

    const hasProblemMessages = messages.some(
      (m) => m.problemId === enriched.id || m.problem?.id === enriched.id
    );

    // If this problem has no messages yet and no initialQuery is pending, dispatch to tutor automatically
    if (!hasProblemMessages && !initialQuery) {
      const promptText = (enriched.problemStatementEng || enriched.problemStatementKhmer || enriched.titleEng || '').trim();
      if (promptText) {
        const userMsg: ChatMessage = {
          id: Date.now().toString(),
          sender: 'user',
          textEng: promptText,
          problemId: enriched.id,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        const updatedWithUser = [...messages, userMsg];
        onUpdateMessages(updatedWithUser);
        setIsSayoThinking(true);
        lastInteractionRef.current = Date.now();

        askTunsayTutor(promptText, enriched, profile.language, activeSessionId).then((res) => {
          if (!isMountedRef.current) return;
          setIsSayoThinking(false);

          if (res.stepWidget && Array.isArray(res.stepWidget.steps) && res.stepWidget.steps.length > 0) {
            const dynSteps = mapWidgetToStepItems(res.stepWidget);
            if (dynSteps.length > 0) {
              setActiveProblem((prev) => (prev ? {
                ...prev,
                steps: dynSteps,
                has_steps: true,
                visualData: res.stepWidget.visual_data || res.stepWidget.visualData || dynSteps[0]?.visualData || prev.visualData
              } : prev));
            }
          }

          const tutorMsg: ChatMessage = {
            id: (Date.now() + 1).toString(),
            sender: 'sayo',
            textKhmer: res.textKhmer,
            textEng: res.textEng,
            problemId: enriched.id,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            isSafetyRefusal: res.isSafetyRefusal ?? false,
            stepWidget: res.stepWidget,
          };
          onUpdateMessages([...updatedWithUser, tutorMsg]);

          const nextState = determineMascotStateFromResponse(tutorMsg.textEng || '');
          if (
            nextState === 'celebrating' ||
            nextState === 'jumping' ||
            nextState === 'encouraging' ||
            nextState === 'happy'
          ) {
            transitionMascotState(nextState, 3000);
          } else {
            setSayoStatus(nextState);
          }
        }).catch(() => {
          if (isMountedRef.current) setIsSayoThinking(false);
        });
      }
    }

    if (worksheetQueue && worksheetQueue.problems.length > 1) {
      setSidebarMode('worksheet');
    } else {
      setSidebarMode('chats');
    }
  }, [activeSessionId, initialProblem?.id, profile.grade, worksheetQueue]);

  // Cycle through thinking texts
  useEffect(() => {
    if (sayoStatus === 'thinking') {
      const interval = setInterval(() => {
        setThinkingTextIdx((prev) => (prev + 1) % 4);
      }, 1800);
      return () => clearInterval(interval);
    } else {
      setThinkingTextIdx(0);
    }
  }, [sayoStatus]);

  const updateMessages = (newMsgs: ChatMessage[], progressMap?: Record<string, any>) => {
    latestMessagesRef.current = newMsgs;
    onUpdateMessages(newMsgs, progressMap || problemStepProgress);
  };

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
    if (
      lower.includes('not quite') ||
      lower.includes('not exactly') ||
      lower.includes('try again') ||
      lower.includes('not quite right') ||
      lower.includes('oops')
    ) {
      return 'encouraging';
    }
    if (
      lower.includes('great') ||
      lower.includes('excellent') ||
      lower.includes('well done') ||
      lower.includes('perfect') ||
      lower.includes('amazing') ||
      lower.includes('awesome')
    ) {
      return 'celebrating';
    }
    if (lower.includes('think') || lower.includes('let me') || lower.includes("let's see")) {
      return 'thinking';
    }
    return 'explaining';
  };

  const getMascotContextText = (state: TunsayState): string => {
    switch (state) {
      case 'idle':
        return isKhmer ? 'ReanMore រង់ចាំជួយ!' : 'Ready to help!';
      case 'waving':
        return isKhmer ? 'សួស្ដី! រៀបចំរៀនហើយឬ?' : 'Hi! Ready to learn?';
      case 'thinking':
        return isKhmer ? thinkingTextsKhmer[thinkingTextIdx] : thinkingTextsEng[thinkingTextIdx];
      case 'listening':
        return isKhmer ? 'ខ្ញុំកំពុងស្ដាប់អ្នក...' : "I'm listening...";
      case 'explaining':
        return isKhmer ? 'នេះជារបៀបគិតអំពីវា...' : "Here's how to think about it...";
      case 'encouraging':
        return isKhmer ? 'មិនអីទេ! តោះមើលវាតាមរបៀបផ្សេង' : "That's okay! Let's look at it another way.";
      case 'happy':
        return isKhmer ? 'អ្នកធ្វើបានល្អ!' : "You're doing great!";
      case 'celebrating':
        return isKhmer ? 'រួចរាល់ហើយ!' : 'Aha! Got it!';
      case 'jumping':
        return isKhmer ? 'អស្ចារ្យណាស់!' : 'Woohoo! Amazing!';
      case 'sleeping':
        return isKhmer ? 'ខ្ញុំសម្រាកខណៈអ្នកគិត...' : 'Resting while you think...';
      default:
        return '';
    }
  };

  // Greeting wave on first load
  useEffect(() => {
    if (!hasWavedRef.current && messages.length <= 1) {
      hasWavedRef.current = true;
      transitionMascotState('waving', 2500);
    }
  }, [messages.length, transitionMascotState]);

  // Inactivity sleeping
  useEffect(() => {
    if (sayoStatus !== 'idle') return;
    const timer = setTimeout(() => {
      setSayoStatus('sleeping');
    }, 30000);
    return () => clearTimeout(timer);
  }, [sayoStatus]);

  // Sayo thinking state sync
  useEffect(() => {
    if (isSayoThinking) {
      setSayoStatus('thinking');
    }
  }, [isSayoThinking]);

  const [isHintOpen, setIsHintOpen] = useState(false);
  const [isExplainOpen, setIsExplainOpen] = useState(false);
  const [activeModalStep, setActiveModalStep] = useState<StepItem | null>(null);

  const [isAllStepsDrawerOpen, setIsAllStepsDrawerOpen] = useState(false);
  const [activeDrawerSteps, setActiveDrawerSteps] = useState<StepItem[]>([]);
  const [activeDrawerStepIdx, setActiveDrawerStepIdx] = useState(0);
  const [activeDrawerMsgId, setActiveDrawerMsgId] = useState<string | null>(null);

  const handleStepHint = (msgId: string) => {
    const currentMsgs = latestMessagesRef.current;
    const idx = currentMsgs.findIndex((m) => m.id === msgId);
    if (idx === -1) return;
    const targetMsg = currentMsgs[idx];
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
      const updated = [...currentMsgs];
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
    const currentMsgs = latestMessagesRef.current;
    const idx = currentMsgs.findIndex((m) => m.id === msgId);
    if (idx === -1) return;
    const targetMsg = currentMsgs[idx];
    const parsed = extractStepWidgetFromMessage(targetMsg);
    if (!parsed) return;

    const widget = targetMsg.stepWidget || parsed.widget;
    if (!widget.steps || targetIdx < 0 || targetIdx >= widget.steps.length) return;

    const newWidget = {
      ...widget,
      current_step_index: targetIdx,
    };
    const targetStep = newWidget.steps[targetIdx];
    if (targetStep) {
      setActiveModalStep(targetStep);
    }
    const newMsg: ChatMessage = {
      ...targetMsg,
      stepWidget: newWidget,
    };
    const updated = [...currentMsgs];
    updated[idx] = newMsg;
    updateMessages(updated);

    try {
      if (activeSessionId) {
        await tutorApi.navigateStep({
          session_id: activeSessionId,
          target_step_index: targetIdx,
        });
      }
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
    const currentMsgs = latestMessagesRef.current;
    const idx = currentMsgs.findIndex((m) => m.id === msgId);
    if (idx === -1) return;
    const targetMsg = currentMsgs[idx];
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

    const updated = [...currentMsgs];
    updated[idx] = newMsg;
    updateMessages(updated);

    if (isCorrect && stepIndex + 1 < (widget.total_steps || widget.steps.length)) {
      const nextStep = newWidget.steps[stepIndex + 1];
      if (nextStep) {
        setActiveModalStep(nextStep);
      }
    }

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
    } else {
      transitionMascotState('encouraging', 2000);
    }

    try {
      if (activeSessionId) {
        const idempKey = `ans_${activeSessionId}_${stepIndex + 1}_${Date.now()}`;
        await tutorApi.submitStepAnswer(
          {
            session_id: activeSessionId,
            step_number: stepIndex + 1,
            student_answer: studentAnswer,
            is_correct: isCorrect,
          },
          idempKey
        );
      }
    } catch {
      // offline fallback
    }
  };

  const chatEndRef = useRef<HTMLDivElement>(null);
  const isMountedRef = useRef(true);
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Handle initialQuery if passed
  useEffect(() => {
    if (!initialQuery?.trim()) return;
    const queryText = initialQuery.trim();
    onClearInitialQuery?.();

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      textEng: queryText,
      problemId: activeProblem?.id,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const updatedWithUser = [...messages, userMsg];
    updateMessages(updatedWithUser);
    setIsSayoThinking(true);
    lastInteractionRef.current = Date.now();

    askTunsayTutor(queryText, activeProblem, profile.language, activeSessionId).then((sayoRes) => {
      if (!isMountedRef.current) return;
      setIsSayoThinking(false);

      if (
        sayoRes.stepWidget &&
        Array.isArray(sayoRes.stepWidget.steps) &&
        sayoRes.stepWidget.steps.length > 0
      ) {
        const dynSteps = mapWidgetToStepItems(sayoRes.stepWidget);
        if (dynSteps.length > 0) {
          setActiveProblem((prev) => (prev ? {
            ...prev,
            steps: dynSteps,
            has_steps: true,
            visualData: sayoRes.stepWidget.visual_data || sayoRes.stepWidget.visualData || dynSteps[0]?.visualData || prev.visualData
          } : prev));
        }
      }

      const sayoMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'sayo',
        textKhmer: sayoRes.textKhmer,
        textEng: sayoRes.textEng,
        problemId: activeProblem?.id,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isSafetyRefusal: sayoRes.isSafetyRefusal ?? false,
        stepWidget: sayoRes.stepWidget,
      };
      updateMessages([...updatedWithUser, sayoMsg]);

      if (sayoMsg.isSafetyRefusal) {
        transitionMascotState('encouraging', 3000);
      } else {
        const nextState = determineMascotStateFromResponse(sayoMsg.textEng || '');
        if (
          nextState === 'celebrating' ||
          nextState === 'jumping' ||
          nextState === 'encouraging' ||
          nextState === 'happy'
        ) {
          transitionMascotState(nextState, 3000);
        } else {
          setSayoStatus(nextState);
        }
      }
    });
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
    setCurrentStepIndex(0);
    setMaxUnlockedStepIndex(0);
    setCompletedStepIndices([]);
    setProblemStepProgress({});
    setCelebratingProblemId(null);
    celebrationShownRef.current.clear();
    onNewSession();
  };

  const isAdvancingStepRef = useRef(false);

  const handleStepAnswer = async (studentAnswer: string): Promise<boolean> => {
    if (!currentStep || isAdvancingStepRef.current) return false;

    const stepNum = currentStep.stepNumber || currentStepIndex + 1;
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      textEng: studentAnswer,
      textKhmer: studentAnswer,
      stepNumber: stepNum,
      stepTotal: activeProblem?.steps?.length,
      problemId: activeProblem?.id,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const updatedWithUser = [...messages, userMsg];
    updateMessages(updatedWithUser);
    setIsSayoThinking(true);
    lastInteractionRef.current = Date.now();

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
      setIsSayoThinking(false);
    } else {
      const evalPrompt = `[Student Answer Evaluation for Step ${stepNum}: "${
        currentStep.questionEng || currentStep.questionKhmer
      }"]. The student answered: "${studentAnswer}". The target expected concept is: "${
        currentStep.correctAnswer
      }". Please determine if this answer is conceptually correct, nearly correct, or needs rethinking. Explain encouragingly in child-friendly words.`;

      try {
        const sayoRes = await askTunsayTutor(
          evalPrompt,
          activeProblem,
          profile.language,
          activeSessionId
        );
        setIsSayoThinking(false);

        if (sayoRes?.textKhmer || sayoRes?.textEng) {
          tutorReplyKhmer = sayoRes.textKhmer || '';
          tutorReplyEng = sayoRes.textEng || '';
          const combined = (tutorReplyEng + ' ' + tutorReplyKhmer).toLowerCase();
          const isAffirmative =
            combined.includes('correct') ||
            combined.includes('spot on') ||
            combined.includes('great job');
          const isNegative =
            combined.includes('not quite') ||
            combined.includes('incorrect') ||
            combined.includes('try again');

          if (isAffirmative && !isNegative) {
            isCorrect = true;
          }
        }
      } catch {
        setIsSayoThinking(false);
      }
    }

    if (activeSessionId) {
      const idempKey = `ans_chat_${activeSessionId}_${stepNum}_${Date.now()}`;
      tutorApi
        .submitStepAnswer(
          {
            session_id: activeSessionId,
            step_number: stepNum,
            student_answer: studentAnswer,
          },
          idempKey
        )
        .catch(() => {});
    }

    const tutorMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      sender: 'sayo',
      textKhmer: tutorReplyKhmer,
      textEng: tutorReplyEng,
      problemId: activeProblem?.id,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
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

      const updatedProgress = activeProblem?.id
        ? {
            ...problemStepProgress,
            ...(activeSession?.problemStepProgress || {}),
            [activeProblem.id]: {
              currentStepIndex: nextIdx,
              maxUnlockedStepIndex: updatedMax,
              completedStepIndices: updatedCompleted,
            },
          }
        : problemStepProgress;

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
    } else {
      updateMessages(updated);
      transitionMascotState('encouraging', 2500);
    }

    return isCorrect;
  };

  const handleSendMessage = async () => {
    if (!inputQuery.trim()) return;

    const userText = inputQuery.trim();
    setInputQuery('');
    shouldAutoScrollToBottomRef.current = true;

    // Accept conversational wrappers like "what 2+2" / "what's 8 + 6?" so
    // simple questions are treated as a fresh arithmetic problem.
    const bareMath = userText
      .replace(
        /^(?:please\s+)?(?:what(?:'s|’s|\s+is|\s+are)?|whats|how\s+much\s+is|how\s+many\s+is|solve|calculate|compute)\s*/i,
        ''
      )
      .replace(/[?=.\s]+$/, '')
      .trim();
    const isBinaryMath = /^\d+(?:\.\d+)?\s*[\+\-\*\/xX×÷]\s*\d+(?:\.\d+)?$/.test(
      bareMath
    );
    const isNewProblemPhrase =
      /^(?:solve|calculate|compute|what(?:'s|’s|\s+is|\s+are)?(?=\s*\d)|whats(?=\s*\d)|how\s+much\s+is\s+\d+|how\s+many\s+is\s+\d+|find\s+the\s+sum|find\s+the\s+difference|new\s+problem|another\s+problem)\b/i.test(
        userText
      );
    const expectedAns = String(
      currentStep?.correctAnswer || currentStep?.expectedAnswer || ''
    ).trim();
    const isExpectedAnsMatch =
      expectedAns.length > 0 && userText.toLowerCase() === expectedAns.toLowerCase();

    const isExplicitNewProblem =
      (isBinaryMath && !isExpectedAnsMatch) || isNewProblemPhrase;

    let currentProblem = activeProblem;

    if (isExplicitNewProblem) {
      currentProblem = undefined;
      setActiveProblem(undefined);
      setCurrentStepIndex(0);
      setMaxUnlockedStepIndex(0);
      setCompletedStepIndices([]);
    } else if (
      currentProblem &&
      currentStep &&
      !completedStepIndices.includes(currentStepIndex)
    ) {
      const isQuestionOrHelp = /(?:help|hint|explain|why|how|what|confused|stuck|\?)/i.test(
        userText
      );
      const isShortAnswer = userText.length <= 40;
      if (!isQuestionOrHelp && isShortAnswer) {
        await handleStepAnswer(userText);
        return;
      }
    }

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      textEng: userText,
      problemId: currentProblem?.id,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const updatedWithUser = [...messages, userMsg];
    updateMessages(updatedWithUser);
    setIsSayoThinking(true);
    lastInteractionRef.current = Date.now();

    const sayoRes = await askTunsayTutor(
      userText,
      currentProblem,
      profile.language,
      activeSessionId
    );
    if (!isMountedRef.current) return;

    setIsSayoThinking(false);

    // If backend returned a structured step widget and this was a fresh problem, save it
    if (
      sayoRes.stepWidget &&
      Array.isArray(sayoRes.stepWidget.steps) &&
      sayoRes.stepWidget.steps.length > 0
    ) {
      if (!currentProblem || !currentProblem.steps || currentProblem.steps.length <= 1) {
        const dynSteps = mapWidgetToStepItems(sayoRes.stepWidget);
        if (dynSteps.length > 0) {
          const vData = sayoRes.stepWidget.visual_data || sayoRes.stepWidget.visualData || dynSteps[0]?.visualData;
          const updatedProblem: HomeworkProblem = currentProblem
            ? { ...currentProblem, steps: dynSteps, visualData: vData || currentProblem.visualData }
            : {
                id: `dyn-p-${Date.now()}`,
                titleKhmer: sayoRes.stepWidget.steps[0]?.title || 'លំហាត់ថ្មី',
                titleEng: sayoRes.stepWidget.steps[0]?.title || 'Homework Problem',
                grade: profile.grade,
                subject: profile.subject,
                problemStatementKhmer: userText,
                problemStatementEng: userText,
                steps: dynSteps,
                visualData: vData,
              };
          currentProblem = updatedProblem;
          setActiveProblem(updatedProblem);
        }
      }
    }

    const sayoMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      sender: 'sayo',
      textKhmer: sayoRes.textKhmer,
      textEng: sayoRes.textEng,
      problemId: currentProblem?.id,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isSafetyRefusal: sayoRes.isSafetyRefusal ?? false,
      stepWidget: sayoRes.stepWidget,
      suggestedChips: sayoRes.suggestedChips,
      degradeToTapFirst: sayoRes.degradeToTapFirst,
    };

    updateMessages([...updatedWithUser, sayoMsg]);

    if (sayoMsg.isSafetyRefusal) {
      transitionMascotState('encouraging', 3000);
    } else {
      const nextState = determineMascotStateFromResponse(sayoMsg.textEng || '');
      if (
        nextState === 'celebrating' ||
        nextState === 'jumping' ||
        nextState === 'encouraging' ||
        nextState === 'happy'
      ) {
        transitionMascotState(nextState, 3000);
      } else {
        setSayoStatus(nextState);
      }
    }
  };

  const handleInputChange = (value: string) => {
    setInputQuery(value);
    lastInteractionRef.current = Date.now();
    if (value.trim().length > 0 && sayoStatus !== 'thinking') {
      setSayoStatus('listening');
    }
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => {
      setSayoStatus((prev) => (prev === 'listening' ? 'idle' : prev));
    }, 1500);
  };

  const handleChipClick = (chip: string) => {
    if (
      chip.toLowerCase().includes('hint') ||
      chip.toLowerCase().includes('clue') ||
      chip.includes('តម្រុយ')
    ) {
      setActiveModalStep(currentStep || null);
      setIsHintOpen(true);
    } else {
      setInputQuery(chip);
    }
  };

  const lastMsg = messages[messages.length - 1];

  return (
    <div className="w-full h-full flex-1 flex flex-row items-stretch gap-2.5 sm:gap-4 lg:gap-5 overflow-hidden">
      {/* Sidebar: Mascot status & Session History */}
      <ChatSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={onSelectSession}
        onDeleteSession={onDeleteSession}
        onNewChat={handleNewChat}
        profile={profile}
        sayoStatus={sayoStatus}
        getMascotContextText={getMascotContextText}
        sidebarMode={sidebarMode}
        setSidebarMode={setSidebarMode}
        worksheetQueue={worksheetQueue}
        onSelectExercise={onSelectExercise}
        isMobileSidebarOpen={isMobileSidebarOpen}
        setIsMobileSidebarOpen={setIsMobileSidebarOpen}
      />

      {/* Main Chat Frame */}
      <div className="flex-1 min-w-0 h-full flex flex-col bg-[#E8F5E9] rounded-xl sm:rounded-3xl border-2 sm:border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] sm:shadow-[6px_6px_0px_#1B4332] overflow-hidden relative">
        {/* Top Header */}
        <ChatHeader
          profile={profile}
          isSayoThinking={isSayoThinking}
          onOpenMobileSidebar={() => setIsMobileSidebarOpen(true)}
          onNewChat={handleNewChat}
          onBackToHome={onBackToHome}
          worksheetQueue={worksheetQueue}
          onSelectExercise={onSelectExercise}
          onViewAllChats={() => setSidebarMode('chats')}
        />

        {/* Scrollable Conversation Stream */}
        <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-2.5 sm:p-4 lg:p-6 space-y-3 sm:space-y-4 lg:space-y-5">
          <ChatMessageList
            messages={messages}
            profile={profile}
            activeProblem={activeProblem}
            celebratingProblemId={celebratingProblemId}
            worksheetQueue={worksheetQueue}
            setCelebratingProblemId={setCelebratingProblemId}
            onSelectExercise={onSelectExercise}
            isSayoThinking={isSayoThinking}
            thinkingTextIdx={thinkingTextIdx}
            onOpenScanner={onOpenScanner}
            onStepHint={handleStepHint}
            onStepNavigate={handleStepNavigate}
            onOpenAllSteps={handleOpenAllSteps}
            onInlineStepAnswer={handleInlineStepAnswer}
            setActiveModalStep={setActiveModalStep}
            setIsHintOpen={setIsHintOpen}
            setIsExplainOpen={setIsExplainOpen}
          />

          <div ref={chatEndRef} />
        </div>

        {/* Interactive Math Keypad & Problem Builder */}
        <MathKeypad
          isOpen={isMathKeypadOpen}
          onClose={() => setIsMathKeypadOpen(false)}
          onInsert={(char) => {
            setInputQuery((prev) => prev + char);
            lastInteractionRef.current = Date.now();
          }}
          onBackspace={() => {
            setInputQuery((prev) => prev.slice(0, -1));
            lastInteractionRef.current = Date.now();
          }}
          onClear={() => {
            setInputQuery('');
            lastInteractionRef.current = Date.now();
          }}
          onSelectStarter={(prob) => {
            setInputQuery(prob);
            lastInteractionRef.current = Date.now();
            setIsMathKeypadOpen(false);
          }}
        />

        {/* Bottom Chat Input Bar */}
        <ChatInputBar
          inputQuery={inputQuery}
          isSayoThinking={isSayoThinking}
          isMathKeypadOpen={isMathKeypadOpen}
          setIsMathKeypadOpen={setIsMathKeypadOpen}
          suggestedChips={lastMsg?.suggestedChips}
          onOpenScanner={onOpenScanner}
          onSendMessage={handleSendMessage}
          onChipClick={handleChipClick}
          onInputChange={handleInputChange}
        />
      </div>

      {/* Sheets & Drawer Modals */}
      {(activeModalStep || currentStep) && (
        <>
          <HintSheet
            step={activeModalStep || currentStep!}
            isOpen={isHintOpen}
            language={profile.language}
            grade={profile.grade}
            onClose={() => {
              setIsHintOpen(false);
              setActiveModalStep(null);
            }}
          />
          <ExplanationCard
            step={activeModalStep || currentStep!}
            isOpen={isExplainOpen}
            language={profile.language}
            grade={profile.grade}
            onClose={() => {
              setIsExplainOpen(false);
              setActiveModalStep(null);
            }}
          />
        </>
      )}

      {isAllStepsDrawerOpen && (
        <AllStepsDrawer
          isOpen={isAllStepsDrawerOpen}
          steps={activeDrawerSteps}
          currentStepIndex={activeDrawerStepIdx}
          language={profile.language}
          onClose={() => {
            setIsAllStepsDrawerOpen(false);
            setActiveDrawerMsgId(null);
          }}
          onSelectStep={(targetIdx) => {
            if (activeDrawerMsgId) {
              handleStepNavigate(activeDrawerMsgId, targetIdx);
            }
            setActiveDrawerStepIdx(targetIdx);
          }}
        />
      )}
    </div>
  );
};
