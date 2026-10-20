import { useState, useCallback, useEffect } from 'react';
import { UserProfile, HomeworkProblem, Grade, ChatSession, WorksheetQueue, UserAccount, UserRole } from './types';
import { Header } from './components/Header';
import { HomeView } from './components/HomeView';
import { ChatView } from './components/ChatView';
import { ProfileView } from './components/ProfileView';
import { HomeworkScanner } from './components/HomeworkScanner';
import { LoginModal } from './components/LoginModal';
import { ForestBackground } from './components/ForestBackground';
import { markSessionAbandoned } from './utils/reportUtils';
import { AuthService } from './services/authService';
import { sessionApi } from './api';

const STORAGE_KEY = 'reanmore_sessions_v2';

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

function isCorruptText(text?: string): boolean {
  if (!text) return false;
  return text.includes('áž') || text.includes('áŸ') || text.includes('\ufffd');
}

function sanitizeMessage(msg: any): any {
  if (!msg) return msg;
  const isKhmerCorrupt = isCorruptText(msg.textKhmer);
  const isEngCorrupt = isCorruptText(msg.textEng);
  return {
    ...msg,
    textKhmer: isKhmerCorrupt
      ? (msg.textEng && !isCorruptText(msg.textEng) ? msg.textEng : 'សួស្តី! តោះដោះស្រាយលំហាត់ជាមួយគ្នា។')
      : msg.textKhmer,
    textEng: isEngCorrupt ? 'Hello! Let us solve homework together.' : msg.textEng,
  };
}

function sanitizeSession(s: ChatSession): ChatSession {
  return {
    ...s,
    titleKhmer: isCorruptText(s.titleKhmer) ? (s.title || 'ជជែកថ្មី') : s.titleKhmer,
    messages: (s.messages || []).map(sanitizeMessage),
  };
}

function getInitialSessions(profileName: string): ChatSession[] {
  return [
    {
      id: generateId(),
      title: 'New Chat',
      titleKhmer: 'ជជែកថ្មី',
      messages: [
        {
          id: 'init-msg',
          sender: 'sayo',
          textKhmer: `សួស្តី ${profileName}! ខ្ញុំគឺ ReanMore គ្រូបង្រៀន AI។ តើអ្នកមានលំហាត់អ្វីចង់ឱ្យខ្ញុំជួយទេ? អ្នកអាចថតរូបស្កែនលំហាត់ ឬវាយបញ្ចូលសំណួរនៅខាងក្រោម!`,
          textEng: `Hi ${profileName}! I am ReanMore, your AI Tutor. What homework would you like help with? You can scan a photo or type your question below!`,
          timestamp: 'Just now'
        }
      ],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
  ];
}

import { ParentReport } from './components/ParentReport';
import { MOCK_PROBLEMS } from './data/mockProblems';

export type TabType = 'home' | 'chat' | 'profile' | 'report';

export default function App() {
  const [currentUser, setCurrentUser] = useState<UserAccount | null>(() => AuthService.getCurrentUser());
  const [profile, setProfile] = useState<UserProfile>(() => {
    const acc = AuthService.getCurrentUser();
    return acc ? acc.profile : {
      name: 'Sochea',
      grade: 4,
      subject: 'math',
      language: 'en',
      role: 'student',
    };
  });

  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authRequiredRole, setAuthRequiredRole] = useState<UserRole | undefined>(undefined);

  useEffect(() => {
    const unsubscribe = AuthService.subscribe((account) => {
      setCurrentUser(account);
      if (account) {
        setProfile({ ...account.profile, language: 'en' });
      }
    });
    return unsubscribe;
  }, []);

  const [activeTab, setActiveTab] = useState<TabType>('home');
  const [worksheetQueue, setWorksheetQueue] = useState<WorksheetQueue | null>(() => {
    try {
      const pathname = window.location.pathname.replace(/\/$/, '') || '/';
      const parts = pathname.split('/').filter(Boolean);
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as ChatSession[];
        const targetId = (parts[0] === 'chat' && parts[1]) ? parts[1] : parsed[0]?.id;
        const target = parsed.find(s => s.id === targetId);
        if (target?.worksheetQueue && target.worksheetQueue.problems && target.worksheetQueue.problems.length > 0) {
          return target.worksheetQueue;
        }
      }
    } catch {}
    return null;
  });

  const [activeProblem, setActiveProblem] = useState<HomeworkProblem | undefined>(() => {
    try {
      const pathname = window.location.pathname.replace(/\/$/, '') || '/';
      const parts = pathname.split('/').filter(Boolean);
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as ChatSession[];
        const targetId = (parts[0] === 'chat' && parts[1]) ? parts[1] : parsed[0]?.id;
        const target = parsed.find(s => s.id === targetId);
        if (target?.worksheetQueue?.problems?.length) {
          const activeIdx = target.worksheetQueue.activeIndex || 0;
          const prob = target.worksheetQueue.problems[activeIdx] || target.problem || target.worksheetQueue.problems[0];
          if (prob) return prob;
        } else if (target?.problem) {
          return target.problem;
        }
      }
    } catch {}
    return undefined;
  });

  const [initialChatQuery, setInitialChatQuery] = useState<string | undefined>(undefined);
  const [isScannerOpen, setIsScannerOpen] = useState(false);

  // ── Session state with localStorage persistence ──
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY) || localStorage.getItem('reanmore_sessions_v1') || localStorage.getItem('tunsay_sessions_v1');
      if (raw) {
        const parsed = JSON.parse(raw) as ChatSession[];
        if (Array.isArray(parsed) && parsed.length > 0) {
          const cleaned = parsed.map(sanitizeSession).filter(s => s.messages && s.messages.length > 0);
          // Keep genuine sessions that have user messages, a problem, a worksheet, or an image
          const genuineSessions = cleaned.filter(s =>
            s.messages.some(m => m.sender === 'user') ||
            Boolean(s.problem) ||
            Boolean(s.worksheetQueue?.problems && s.worksheetQueue.problems.length > 0) ||
            Boolean(s.imageUri)
          );
          if (genuineSessions.length > 0) {
            return genuineSessions;
          }
          // If all saved sessions were empty duplicates, keep only the first one
          if (cleaned.length > 0) {
            return [cleaned[0]];
          }
        }
      }
    } catch { /* ignore corrupt storage */ }
    return getInitialSessions('សុជា (Sochea)');
  });

  const [activeSessionId, setActiveSessionId] = useState<string>(() => {
    try {
      const pathname = window.location.pathname.replace(/\/$/, '') || '/';
      const parts = pathname.split('/').filter(Boolean);
      if (parts[0] === 'chat' && parts[1]) {
        return parts[1];
      }
    } catch {}
    return (sessions[0] && sessions[0].id) ? sessions[0].id : '';
  });

  // ── URL Path Router Synchronization ──
  const navigateTo = useCallback((tab: TabType, sessionId?: string, exerciseId?: string) => {
    setActiveTab(tab);
    let path = `/${tab}`;
    if (tab === 'home') path = '/home';
    else if (tab === 'chat') {
      if (exerciseId) path = `/exercise/${exerciseId}`;
      else if (sessionId) path = `/chat/${sessionId}`;
      else path = '/chat';
    } else if (tab === 'profile') path = '/profile';
    else if (tab === 'report') path = '/report';

    if (window.location.pathname !== path) {
      window.history.pushState({ tab, sessionId, exerciseId }, '', path);
    }
  }, []);

  // Parse initial route from window.location.pathname on load and back/forward navigation
  useEffect(() => {
    const handleLocationChange = () => {
      const pathname = window.location.pathname.replace(/\/$/, '') || '/';
      const parts = pathname.split('/').filter(Boolean);

      if (parts.length === 0 || parts[0] === 'home') {
        setActiveTab('home');
      } else if (parts[0] === 'profile') {
        setActiveTab('profile');
      } else if (parts[0] === 'report') {
        setActiveTab('report');
      } else if (parts[0] === 'scan') {
        setIsScannerOpen(true);
      } else if (parts[0] === 'chat') {
        setActiveTab('chat');
        const targetId = parts[1] || activeSessionId || sessions[0]?.id;
        if (targetId) {
          const targetSession = sessions.find(s => s.id === targetId) || sessions[0];
          if (targetSession) {
            setActiveSessionId(targetSession.id);
            if (targetSession.worksheetQueue && targetSession.worksheetQueue.problems && targetSession.worksheetQueue.problems.length > 0) {
              setWorksheetQueue(targetSession.worksheetQueue);
              const activeIdx = targetSession.worksheetQueue.activeIndex || 0;
              const activeProb = targetSession.worksheetQueue.problems[activeIdx] || targetSession.problem || targetSession.worksheetQueue.problems[0];
              setActiveProblem(activeProb);
            } else if (targetSession.problem) {
              setWorksheetQueue(null);
              setActiveProblem(targetSession.problem);
            } else {
              setWorksheetQueue(null);
              setActiveProblem(undefined);
            }
          }
        }
      } else if (parts[0] === 'exercise' && parts[1]) {
        const exId = parts[1];
        const rawProblem = MOCK_PROBLEMS.find(p => p.id === exId) || {
          id: exId,
          titleKhmer: `លំហាត់ ${exId}`,
          titleEng: `Exercise ${exId}`,
          grade: profile.grade,
          subject: profile.subject,
          problemStatementKhmer: '',
          problemStatementEng: exId,
          steps: [],
        };
        setActiveProblem(rawProblem);
        setActiveTab('chat');
      }
    };

    handleLocationChange();
    window.addEventListener('popstate', handleLocationChange);
    return () => window.removeEventListener('popstate', handleLocationChange);
  }, [sessions, profile.grade, profile.subject, activeSessionId]);

  // Persist sessions to localStorage (always sanitize to prevent duplicates)
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    } catch { /* ignore quota errors */ }
  }, [sessions]);

  // Mark in-progress activities as abandoned when leaving chat tab
  useEffect(() => {
    if (activeTab !== 'chat') {
      markSessionAbandoned(activeSessionId);
    }
  }, [activeTab, activeSessionId]);

  // Sync session state to PostgreSQL DB in the background
  const syncSessionToBackend = useCallback((session: ChatSession, userProfile: UserProfile) => {
    // Only persist to DB if there is actual user interaction (texted a message, scanned image, or loaded problem)
    const hasUserMsgs = session.messages?.some(m => m.sender === 'user');
    const hasWorksheet = Boolean(session.worksheetQueue?.problems && session.worksheetQueue.problems.length > 0);
    const hasProblem = Boolean(session.problem);
    const hasImage = Boolean(session.imageUri);
    if (!hasUserMsgs && !hasWorksheet && !hasProblem && !hasImage) {
      return; // Skip saving blank new chat with 0 user messages
    }

    try {
      const problemProgress = session.problem?.id && session.problemStepProgress ? session.problemStepProgress[session.problem.id] : undefined;
      sessionApi.syncSession({
        session_id: session.id,
        user_id: userProfile.name,
        student_name: userProfile.name,
        subject: userProfile.subject,
        grade: userProfile.grade,
        language: userProfile.language,
        messages: session.messages,
        current_problem: session.problem,
        active_step_index: problemProgress?.currentStepIndex,
        completed_step_indices: problemProgress?.completedStepIndices,
        timestamp: Date.now(),
      }).catch(err => console.debug('sessionApi sync offline/fallback:', err));
    } catch { /* ignore network error in offline mode */ }
  }, []);

  const activeSession = sessions.find(s => s.id === activeSessionId) ?? sessions[0];

  const handleUpdateProfile = (updated: Partial<UserProfile>) => {
    const sanitized = { ...updated, language: 'en' as const };
    AuthService.updateProfile(sanitized);
    setProfile((prev: UserProfile) => ({ ...prev, ...sanitized }));
  };

  const handleOpenAuth = (requiredRole?: UserRole) => {
    setAuthRequiredRole(requiredRole);
    setIsAuthModalOpen(true);
  };

  const handleLogout = () => {
    AuthService.logout();
    setCurrentUser(null);
    setProfile({
      name: 'Guest',
      grade: 4,
      subject: 'math',
      language: 'en',
      role: 'student',
    });
    if (activeTab === 'report') {
      navigateTo('home');
    }
  };

  const createNewSession = useCallback((problem?: HomeworkProblem, wsQueue?: WorksheetQueue, imageUri?: string) => {
    // If starting a blank chat and an empty chat already exists, reuse it
    if (!problem && !wsQueue && !imageUri) {
      const existingEmpty = sessions.find(s =>
        !s.problem &&
        (!s.worksheetQueue?.problems || s.worksheetQueue.problems.length === 0) &&
        !s.imageUri &&
        !s.messages?.some(m => m.sender === 'user')
      );
      if (existingEmpty) {
        setActiveSessionId(existingEmpty.id);
        return existingEmpty.id;
      }
    }

    const isWs = Boolean(wsQueue && wsQueue.problems && wsQueue.problems.length > 1);
    const exCount = wsQueue?.problems?.length || 1;
    const title = isWs ? `Worksheet (${exCount} Exercises)` : (problem?.titleEng ?? 'New Chat');
    const titleKhmer = isWs ? `ទំព័រលំហាត់ (${exCount} លំហាត់)` : (problem?.titleKhmer ?? 'ជជែកថ្មី');

    const newSession: ChatSession = {
      id: generateId(),
      title,
      titleKhmer,
      messages: [
        {
          id: 'init-msg',
          sender: 'sayo',
          textKhmer: `សួស្តី ${profile.name}! ខ្ញុំគឺ ReanMore គ្រូបង្រៀន AI។ តើអ្នកមានលំហាត់អ្វីចង់ឱ្យខ្ញុំជួយទេ? អ្នកអាចថតរូបស្កែនលំហាត់ ឬវាយបញ្ចូលសំណួរនៅខាងក្រោម!`,
          textEng: `Hi ${profile.name}! I am ReanMore, your AI Tutor. What homework would you like help with? You can scan a photo or type your question below!`,
          timestamp: 'Just now'
        }
      ],
      problem,
      worksheetQueue: wsQueue,
      imageUri,
      isWorksheet: isWs,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    setSessions(prev => {
      // Filter out any other duplicate blank unused sessions
      const filtered = prev.filter(s =>
        s.messages?.some(m => m.sender === 'user') ||
        Boolean(s.problem) ||
        Boolean(s.worksheetQueue?.problems && s.worksheetQueue.problems.length > 0) ||
        Boolean(s.imageUri)
      );
      return [newSession, ...filtered];
    });

    setActiveSessionId(newSession.id);
    // Navigate to the new session URL immediately so the user sees the blank chat
    navigateTo('chat', newSession.id);
    if (problem || wsQueue || imageUri) {
      syncSessionToBackend(newSession, profile);
    }
    return newSession.id;
  }, [profile, sessions, syncSessionToBackend, navigateTo]);

  const updateSessionMessages = useCallback((sessionId: string, messages: ChatSession['messages'], progressMap?: Record<string, any>) => {
    setSessions(prev => prev.map(s => {
      if (s.id !== sessionId) return s;
      const firstUserMsg = messages.find(m => m.sender === 'user');
      let title = s.title;
      let titleKhmer = s.titleKhmer;
      if (firstUserMsg && (s.title === 'New Chat' || s.title === 'ជជែកថ្មី')) {
        const preview = firstUserMsg.textEng.slice(0, 30);
        title = preview + (firstUserMsg.textEng.length > 30 ? '...' : '');
        const khmerPreview = firstUserMsg.textKhmer?.slice(0, 30) ?? '';
        titleKhmer = khmerPreview + ((firstUserMsg.textKhmer?.length ?? 0) > 30 ? '...' : '');
      }
      const updated: ChatSession = {
        ...s,
        messages,
        problemStepProgress: progressMap || s.problemStepProgress,
        title,
        titleKhmer,
        updatedAt: new Date().toISOString(),
      };
      syncSessionToBackend(updated, profile);
      return updated;
    }));
  }, [profile, syncSessionToBackend]);

  const handleStartChatWithProblem = (problem?: HomeworkProblem, initialQuery?: string) => {
    // Only route to curriculum practice queue if problem is an empty subject placeholder
    const isSubjectOnlyPlaceholder = problem && !problem.problemStatementEng && !problem.problemStatementKhmer && (!problem.steps || problem.steps.length === 0);
    if (isSubjectOnlyPlaceholder && (problem.subject === 'math' || problem.subject === 'science')) {
      const sampleProblems = MOCK_PROBLEMS.filter(p => p.subject === problem.subject);
      if (sampleProblems.length > 0) {
        handleHomeworkScanned(sampleProblems, 0, sampleProblems[0]?.imageUri);
        return;
      }
    }
    const enriched = problem;
    setActiveProblem(enriched);
    setInitialChatQuery(initialQuery);
    setWorksheetQueue(null);
    const sessionId = createNewSession(enriched);
    setActiveSessionId(sessionId);
    navigateTo('chat', sessionId, enriched?.id);
  };

  const handleHomeworkScanned = (problems: HomeworkProblem[], initialIndex: number = 0, imageUri?: string) => {
    if (problems.length === 0) return;

    // Auto-detect grade from scanned homework and sync to profile
    const detectedGrade = problems.find(p => p.grade && p.grade >= 1 && p.grade <= 6)?.grade;
    if (detectedGrade && detectedGrade !== profile.grade) {
      setProfile(prev => ({ ...prev, grade: detectedGrade as Grade }));
    }

    const enrichedProblems = problems;
    const initialProblem = enrichedProblems[initialIndex] || enrichedProblems[0];
    setActiveProblem(initialProblem);
    setInitialChatQuery(undefined);
    setIsScannerOpen(false);

    // Initialize worksheet queue with all exercises on the scanned page
    const subjectTitle = initialProblem.subject === 'math'
      ? (profile.language === 'km' ? 'កិច្ចការផ្ទះគណិតវិទ្យា' : 'Math Homework')
      : initialProblem.subject === 'science'
      ? (profile.language === 'km' ? 'កិច្ចការផ្ទះវិទ្យាសាស្ត្រ' : 'Science Homework')
      : (profile.language === 'km' ? 'ទំព័រលំហាត់' : 'Worksheet');

    const queue: WorksheetQueue = {
      problems: enrichedProblems,
      activeIndex: initialIndex,
      completedIds: [],
      worksheetTitle: enrichedProblems.length > 1
        ? `${subjectTitle} (${enrichedProblems.length} ${profile.language === 'km' ? 'លំហាត់' : 'Exercises'})`
        : undefined,
    };
    setWorksheetQueue(queue);
    const sessionId = createNewSession(initialProblem, queue, imageUri);
    setActiveSessionId(sessionId);
    navigateTo('chat', sessionId, initialProblem.id);
  };

  const handleSelectExercise = (index: number) => {
    setWorksheetQueue(prev => {
      if (!prev) return prev;
      const rawProblem = prev.problems[index];
      if (!rawProblem) return prev;
      const problem = rawProblem;
      setActiveProblem(problem);
      navigateTo('chat', activeSessionId, problem.id);

      const updatedQueue: WorksheetQueue = { ...prev, activeIndex: index };
      // Save updated active index to session state
      setSessions(sList => sList.map(s => {
        if (s.id !== activeSessionId) return s;
        const updated = {
          ...s,
          problem,
          worksheetQueue: updatedQueue,
          updatedAt: new Date().toISOString()
        };
        syncSessionToBackend(updated, profile);
        return updated;
      }));

      return updatedQueue;
    });
  };

  const handleExerciseComplete = (problemId: string) => {
    setWorksheetQueue(prev => {
      if (!prev) return prev;
      if (prev.completedIds.includes(problemId)) return prev;
      const newCompleted = [...prev.completedIds, problemId];
      const nextIndex = prev.problems.findIndex(
        (p, i) => i > prev.activeIndex && !newCompleted.includes(p.id)
      );
      const newIndex = nextIndex !== -1 ? nextIndex : prev.activeIndex;
      if (nextIndex !== -1) {
        const rawNext = prev.problems[nextIndex];
        const nextProb = rawNext;
        setActiveProblem(nextProb);
        navigateTo('chat', activeSessionId, nextProb.id);
      }

      const updatedQueue: WorksheetQueue = { ...prev, completedIds: newCompleted, activeIndex: newIndex };
      // Update session in sessions list and persist
      setSessions(sList => sList.map(s => {
        if (s.id !== activeSessionId) return s;
        const updated = {
          ...s,
          worksheetQueue: updatedQueue,
          updatedAt: new Date().toISOString()
        };
        syncSessionToBackend(updated, profile);
        return updated;
      }));

      return updatedQueue;
    });
  };

  const handleSelectSession = (sessionId: string) => {
    setActiveSessionId(sessionId);
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
      if (session.worksheetQueue && session.worksheetQueue.problems.length > 0) {
        setWorksheetQueue(session.worksheetQueue);
        const activeProb = session.worksheetQueue.problems[session.worksheetQueue.activeIndex] || session.problem || session.worksheetQueue.problems[0];
        setActiveProblem(activeProb);
      } else if (session.problem) {
        setWorksheetQueue(null);
        setActiveProblem(session.problem);
      } else {
        setWorksheetQueue(null);
        setActiveProblem(undefined);
      }
    }
    navigateTo('chat', sessionId);
  };

  const handleDeleteSession = (sessionId: string) => {
    setSessions(prev => {
      const filtered = prev.filter(s => s.id !== sessionId);
      if (filtered.length === 0) {
        const fresh = getInitialSessions(profile.name);
        setActiveSessionId(fresh[0].id);
        navigateTo('chat', fresh[0].id);
        return fresh;
      }
      if (activeSessionId === sessionId) {
        setActiveSessionId(filtered[0].id);
        navigateTo('chat', filtered[0].id);
      }
      return filtered;
    });

    // Delete in background from backend
    try {
      sessionApi.deleteSession(sessionId).catch(() => {});
    } catch { /* ignore */ }
  };

  return (
    <div className={`relative bg-[#EDF7EE] text-[#1B4332] flex flex-col font-sans w-full overflow-x-hidden ${activeTab === 'chat' ? 'h-screen h-[100dvh] overflow-hidden' : 'min-h-screen'}`}>
      <ForestBackground activeTab={activeTab} />

      <Header
        profile={profile}
        currentUser={currentUser}
        activeTab={activeTab}
        onSelectTab={(tab) => navigateTo(tab)}
        onOpenAuth={handleOpenAuth}
        onLogout={handleLogout}
      />

      <main className={`relative z-10 flex-1 min-h-0 w-full mx-auto ${activeTab === 'chat' ? 'w-full px-1.5 sm:px-4 lg:px-6 py-1.5 sm:py-3 lg:py-4 h-full overflow-hidden flex flex-col' : 'max-w-7xl px-3 py-3 sm:px-6 sm:py-6 lg:px-8'}`}>
        {activeTab === 'home' && (
          <HomeView
            profile={profile}
            onStartScan={() => setIsScannerOpen(true)}
            onStartChat={handleStartChatWithProblem}
            onSelectGrade={(grade: Grade) => handleUpdateProfile({ grade })}
          />
        )}

        {activeTab === 'chat' && activeSession && (
          <ChatView
            profile={profile}
            initialProblem={activeProblem}
            initialQuery={initialChatQuery}
            onClearInitialQuery={() => setInitialChatQuery(undefined)}
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSelectSession={handleSelectSession}
            onNewSession={() => {
              const newId = createNewSession();
              setWorksheetQueue(null);
              setActiveProblem(undefined);
              if (newId) navigateTo('chat', newId);
            }}
            onDeleteSession={handleDeleteSession}
            onUpdateMessages={(msgs, progressMap) => updateSessionMessages(activeSessionId, msgs, progressMap)}
            onOpenScanner={() => setIsScannerOpen(true)}
            onBackToHome={() => navigateTo('home')}
            worksheetQueue={worksheetQueue ?? undefined}
            onSelectExercise={handleSelectExercise}
            onExerciseComplete={handleExerciseComplete}
          />
        )}

        {activeTab === 'report' && (
          <ParentReport profile={profile} />
        )}

        {activeTab === 'profile' && (
          <ProfileView
            profile={profile}
            currentUser={currentUser}
            onUpdateProfile={handleUpdateProfile}
            onOpenAuth={handleOpenAuth}
            onLogout={handleLogout}
          />
        )}
      </main>

      {isScannerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#1B4332]/60 backdrop-blur-sm p-4 animate-fadeIn">
          <HomeworkScanner
            language={profile.language}
            grade={profile.grade}
            onHomeworkConfirmed={handleHomeworkScanned}
            onCancel={() => setIsScannerOpen(false)}
          />
        </div>
      )}

      {/* Login & Account Switcher Modal */}
      <LoginModal
        isOpen={isAuthModalOpen}
        onClose={() => {
          setIsAuthModalOpen(false);
          setAuthRequiredRole(undefined);
        }}
        onSuccess={(account) => {
          setCurrentUser(account);
          setProfile(account.profile);
          if (authRequiredRole === 'parent') {
            navigateTo('report');
          }
        }}
        language={profile.language}
        requiredRole={authRequiredRole}
      />
    </div>
  );
}


