import React from 'react';
import { ChatSession, TunsayState, UserProfile, WorksheetQueue } from '../../types';
import { TunsayAvatar } from '../TunsayAvatar';
import { WorksheetProgressPanel } from '../WorksheetProgressPanel';
import { Layers, MessageSquare, Plus, Trash2, Sparkles, X } from 'lucide-react';
import { stripEmojis } from './chatUtils';

interface ChatSidebarProps {
  sessions: ChatSession[];
  activeSessionId: string;
  onSelectSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onNewChat: () => void;
  profile: UserProfile;
  sayoStatus: TunsayState;
  getMascotContextText: (state: TunsayState) => string;
  sidebarMode: 'worksheet' | 'chats';
  setSidebarMode: (mode: 'worksheet' | 'chats') => void;
  worksheetQueue?: WorksheetQueue | undefined;
  onSelectExercise?: ((index: number) => void) | undefined;
  isMobileSidebarOpen: boolean;
  setIsMobileSidebarOpen: (open: boolean) => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onDeleteSession,
  onNewChat,
  profile,
  sayoStatus,
  getMascotContextText,
  sidebarMode,
  setSidebarMode,
  worksheetQueue,
  onSelectExercise,
  isMobileSidebarOpen,
  setIsMobileSidebarOpen,
}) => {
  const isKhmer = profile.language === 'km';

  const getSessionPreview = (session: ChatSession): string => {
    const lastMsg = session.messages[session.messages.length - 1];
    if (!lastMsg) return '';
    const rawText = (isKhmer ? lastMsg.textKhmer : lastMsg.textEng) || lastMsg.textEng || lastMsg.textKhmer || '';
    const text = stripEmojis(rawText).replace(/[*#`_~]/g, '').replace(/\s+/g, ' ').trim();
    return text.slice(0, 42) + (text.length > 42 ? '...' : '');
  };

  const formatSessionTime = (iso: string): string => {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    } catch {
      return '';
    }
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
              thinking: { text: isKhmer ? 'កំពុងគិត...' : 'Thinking...', style: 'bg-[#2D6A4F] text-white animate-pulse', icon: 'ping' },
              celebrating: { text: isKhmer ? 'រួចរាល់!' : 'Done!', style: 'bg-[#2D6A4F] text-white animate-bounce', icon: 'sparkle' },
              jumping: { text: isKhmer ? 'អស្ចារ្យ!' : 'Amazing!', style: 'bg-[#2D6A4F] text-white animate-bounce', icon: 'sparkle' },
              encouraging: { text: isKhmer ? 'កុំបារម្ភ!' : 'No worries!', style: 'bg-[#A7CDB4] text-[#1B4332]', icon: 'dot' },
              listening: { text: isKhmer ? 'ស្ដាប់...' : 'Listening...', style: 'bg-[#A7CDB4] text-[#1B4332] animate-pulse', icon: 'dot' },
              explaining: { text: isKhmer ? 'ពន្យល់...' : 'Explaining...', style: 'bg-[#A7CDB4] text-[#1B4332]', icon: 'dot' },
              waving: { text: isKhmer ? 'សួស្ដី!' : 'Hello!', style: 'bg-[#A7CDB4] text-[#1B4332] animate-bounce', icon: 'dot' },
              happy: { text: isKhmer ? 'ល្អ!' : 'Yay!', style: 'bg-[#2D6A4F] text-white animate-bounce', icon: 'sparkle' },
              confused: { text: isKhmer ? 'ហ៊ឹម...' : 'Hmm...', style: 'bg-[#A7CDB4] text-[#1B4332]', icon: 'dot' },
              sleeping: { text: isKhmer ? 'សម្រាក...' : 'Resting...', style: 'bg-gray-200 text-gray-700', icon: 'none' },
              idle: { text: 'ReanMore AI Tutor', style: 'bg-[#A7CDB4] text-[#1B4332]', icon: 'dot' },
            };
            const b = badges[sayoStatus] || badges.idle;
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
                onNewChat();
                if (isMobile) setIsMobileSidebarOpen(false);
              }}
              className="text-xs font-black text-[#1B4332] bg-white hover:bg-[#A7CDB4] border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] active:translate-y-0.5 px-2.5 py-1 rounded-lg flex items-center gap-1 cursor-pointer transition-all"
              title={isKhmer ? 'ចាប់ផ្តើមជជែកថ្មី' : 'New Chat'}
            >
              <Plus className="w-3.5 h-3.5 stroke-[3]" />
              <span>{isKhmer ? 'ថ្មី' : 'New'}</span>
            </button>
          </div>

          {sessions.length === 0 && (
            <div className="py-8 px-3 text-center rounded-2xl bg-white/40 border-2 border-dashed border-[#1B4332]/20 my-2">
              <MessageSquare className="w-6 h-6 text-[#1B4332]/40 mx-auto mb-2" />
              <p className="text-xs font-black text-[#1B4332]/70">
                {isKhmer ? 'មិនទាន់មានប្រវត្តិជជែកទេ' : 'No saved chats yet'}
              </p>
              <p className="text-[10px] font-semibold text-[#1B4332]/50 mt-1">
                {isKhmer ? 'ផ្ញើសារដើម្បីរក្សាទុកប្រវត្តិជជែក' : 'Start chatting to save your conversation'}
              </p>
            </div>
          )}

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
                className={`w-full h-[72px] min-h-[72px] max-h-[72px] text-left rounded-xl border-2 sm:border-2.5 px-2.5 sm:px-3 py-2 transition-all cursor-pointer group flex items-center gap-2.5 relative select-none ${
                  isActive
                    ? 'bg-[#F0FDF4] border-[#1B4332] shadow-[2.5px_2.5px_0px_#1B4332] translate-x-0.5'
                    : 'bg-white hover:bg-[#F9FCF9] border-[#1B4332]/35 hover:border-[#1B4332] shadow-[1.5px_1.5px_0px_rgba(27,67,50,0.12)] hover:shadow-[2px_2px_0px_#1B4332]'
                }`}
              >
                {/* Session Type Icon */}
                <div className={`w-8 h-8 rounded-lg border-2 shrink-0 flex items-center justify-center transition-colors ${
                  hasWorksheet
                    ? 'bg-[#40916C] text-white border-[#1B4332]'
                    : isActive
                    ? 'bg-[#2D6A4F] text-white border-[#1B4332]'
                    : 'bg-[#E8F5E9] text-[#1B4332] border-[#1B4332]/40 group-hover:border-[#1B4332]'
                }`}>
                  {hasWorksheet ? (
                    <Layers className="w-4 h-4 stroke-[2.5]" />
                  ) : (
                    <MessageSquare className="w-4 h-4 stroke-[2.5]" />
                  )}
                </div>

                {/* Session Title & Preview (2 consistent rows) */}
                <div className="min-w-0 flex-1 flex flex-col justify-center">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <p className="text-xs sm:text-sm font-black text-[#1B4332] truncate leading-tight flex-1 min-w-0">
                      {stripEmojis(isKhmer ? session.titleKhmer : session.title)}
                    </p>
                    {hasWorksheet && (
                      <span className="text-[9px] font-black bg-[#A7CDB4]/50 text-[#1B4332] px-1.5 py-0.5 rounded border border-[#1B4332]/30 shrink-0">
                        {wsTotal} {isKhmer ? 'លំហាត់' : 'Ex'}
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] sm:text-xs font-semibold text-[#1B4332]/75 truncate mt-1 leading-snug">
                    {hasWorksheet && wsDone > 0 ? (
                      <span className="text-[#2D6A4F] font-bold">
                        {wsDone}/{wsTotal} {isKhmer ? 'រួចរាល់' : 'done'} • {getSessionPreview(session)}
                      </span>
                    ) : (
                      getSessionPreview(session) || (isKhmer ? 'ចាប់ផ្តើមជជែក' : 'No messages yet')
                    )}
                  </div>
                </div>

                {/* Right Column: Active status badge / Date / Delete */}
                <div className="flex flex-col items-end justify-between h-full py-0.5 shrink-0 pl-1">
                  <div className="flex items-center gap-1">
                    {isActive && (
                      <span className="text-[8.5px] font-black uppercase tracking-wider bg-[#2D6A4F] text-white px-1.5 py-0.5 rounded shadow-xs">
                        {isKhmer ? 'បើក' : 'Active'}
                      </span>
                    )}
                    <span className="text-[9px] font-bold text-[#1B4332]/70 bg-[#A7CDB4]/30 px-1.5 py-0.5 rounded-md">
                      {formatSessionTime(session.updatedAt)}
                    </span>
                  </div>
                  {onDeleteSession && (
                    <button
                      type="button"
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
    <>
      {/* Desktop Left Panel */}
      <div className="hidden lg:flex lg:w-[28%] lg:min-w-[260px] lg:max-w-[340px] shrink-0 h-full max-h-full bg-[#E8F5E9] rounded-2xl lg:rounded-3xl border-2 sm:border-3 border-[#1B4332] shadow-[4px_4px_0px_#1B4332] lg:shadow-[6px_6px_0px_#1B4332] flex-col select-none z-10 relative overflow-hidden min-h-0">
        {renderSidebarPanel(false)}
      </div>

      {/* Mobile Slide-Over Drawer */}
      {isMobileSidebarOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden animate-fadeIn">
          <div
            className="fixed inset-0 bg-[#1B4332]/60 backdrop-blur-xs transition-opacity cursor-pointer"
            onClick={() => setIsMobileSidebarOpen(false)}
          />
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
    </>
  );
};
