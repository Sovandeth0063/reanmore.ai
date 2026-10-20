import React, { useState, useEffect, useCallback } from 'react';
import { UserAccount, UserRole, Language } from '../types';
import { AuthService } from '../services/authService';
import { getDisplayName } from '../utils/language';
import {
  CreditCard,
  User,
  LogIn,
  X,
  AlertCircle,
  ArrowLeft,
  ChevronRight,
  Check,
  Delete,
  Sparkles,
  Award,
  ShieldCheck,
  QrCode,
  ArrowRight,
} from 'lucide-react';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (account: UserAccount) => void;
  language?: Language | undefined;
  requiredRole?: UserRole | undefined;
  initialMode?: 'select' | 'login' | 'create' | undefined;
}

const AVATAR_OPTIONS = ['👦', '👧', '🦁', '🐰', '🦊', '🐼', '🚀', '🌟', '🎨', '🔬'];

export const LoginModal: React.FC<LoginModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  language = 'en',
  requiredRole,
  initialMode,
}) => {
  const accounts = AuthService.getAccounts();
  const current = AuthService.getCurrentUser();

  // Navigation tab: 'register' vs 'login'
  const [activeTab, setActiveTab] = useState<'register' | 'login'>(() => {
    if (requiredRole === 'parent') return 'login';
    if (initialMode === 'create') return 'register';
    if (accounts.length === 0) return 'register';
    return 'login';
  });

  // Newly issued Student ID Card screen (shown right after registration)
  const [newlyIssuedCard, setNewlyIssuedCard] = useState<UserAccount | null>(null);

  // Selected profile for tactile PIN pad mode
  const [selectedAccount, setSelectedAccount] = useState<UserAccount | null>(null);

  // Manual typing mode on Login tab
  const [isTypingLogin, setIsTypingLogin] = useState(false);

  // Form states
  const [pinInput, setPinInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Manual Login fields
  const [loginIdentifier, setLoginIdentifier] = useState('');
  const [manualPin, setManualPin] = useState('');

  // Register fields
  const [regName, setRegName] = useState('');
  const [regAvatar, setRegAvatar] = useState('🦁');
  const [regGrade, setRegGrade] = useState<number>(4);
  const [regCustomId, setRegCustomId] = useState('');
  const [regPin, setRegPin] = useState('');

  // Reset state on open/close
  useEffect(() => {
    if (isOpen) {
      setError(null);
      setPinInput('');
      setManualPin('');
      setNewlyIssuedCard(null);
      const currentAccounts = AuthService.getAccounts();

      if (requiredRole === 'parent') {
        const parentAcc = currentAccounts.find((a) => a.role === 'parent');
        setSelectedAccount(parentAcc || null);
        setActiveTab('login');
      } else {
        setSelectedAccount(null);
        setIsTypingLogin(false);
        if (initialMode === 'create' || currentAccounts.length === 0) {
          setActiveTab('register');
        } else {
          setActiveTab('login');
        }
      }
    }
  }, [isOpen, requiredRole, initialMode]);

  // Execute PIN Login for selected account
  const executePinLogin = useCallback(
    async (pinToTest: string) => {
      if (!selectedAccount) return;
      setIsLoading(true);
      setError(null);

      try {
        const identifierToUse = selectedAccount.idCard || selectedAccount.id || selectedAccount.username;
        const res = await AuthService.loginRemote(identifierToUse, pinToTest);
        if (res.success && res.account) {
          onSuccess(res.account);
          onClose();
        } else {
          setError(res.errorEng || 'PIN មិនត្រឹមត្រូវឡើយ (Incorrect PIN. Please try again).');
          setPinInput('');
        }
      } catch {
        setError('Connection error. Please try again.');
        setPinInput('');
      } finally {
        setIsLoading(false);
      }
    },
    [selectedAccount, onSuccess, onClose]
  );

  // Keypad handlers
  const handleDigitPress = (digit: string) => {
    if (pinInput.length >= 4) return;
    const nextPin = pinInput + digit;
    setPinInput(nextPin);
    setError(null);

    if (nextPin.length === 4) {
      executePinLogin(nextPin);
    }
  };

  const handleBackspace = () => {
    setPinInput((prev) => prev.slice(0, -1));
    setError(null);
  };

  const handleClearPin = () => {
    setPinInput('');
    setError(null);
  };

  // Physical keyboard listener for PIN pad
  useEffect(() => {
    if (!isOpen || !selectedAccount) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key >= '0' && e.key <= '9') {
        handleDigitPress(e.key);
      } else if (e.key === 'Backspace') {
        handleBackspace();
      } else if (e.key === 'Escape') {
        setSelectedAccount(null);
        setPinInput('');
        setError(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedAccount, pinInput]);

  // Handle Manual Login with Student ID Card or Name
  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginIdentifier.trim()) {
      setError('Please enter your Student ID Card Number or Name.');
      return;
    }
    if (!manualPin.trim() || manualPin.trim().length < 4) {
      setError('Please enter your 4-digit PIN.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const res = await AuthService.loginRemote(loginIdentifier.trim(), manualPin.trim());
      if (res.success && res.account) {
        onSuccess(res.account);
        onClose();
      } else {
        setError(res.errorEng || 'Student ID Card not found or incorrect PIN.');
      }
    } catch {
      setError('Network error. Logging into offline profile.');
      const localRes = AuthService.login(loginIdentifier.trim(), manualPin.trim());
      if (localRes.success && localRes.account) {
        onSuccess(localRes.account);
        onClose();
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Register Student ID Card
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regName.trim()) {
      setError('Please enter learner full name.');
      return;
    }
    if (!regPin.trim() || regPin.trim().length < 4) {
      setError('Please choose a 4-digit secret PIN.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const res = await AuthService.registerRemote(
        regName.trim(),
        regPin.trim(),
        regGrade,
        requiredRole === 'parent' ? 'parent' : 'student',
        language,
        regAvatar,
        regCustomId.trim() || undefined
      );

      if (res.success && res.account) {
        // Show the Digital Student ID Card!
        setNewlyIssuedCard(res.account);
      } else {
        setError(res.errorEng || 'Registration failed. Please try a different name or ID.');
      }
    } catch {
      setError('Could not connect to database. Card generated locally.');
      const randomId = `RM-${Math.floor(10000 + Math.random() * 90000)}`;
      const localRes = AuthService.createAccount(
        regName.trim().toLowerCase().replace(/\s+/g, '_'),
        'student',
        {
          name: regName.trim(),
          grade: regGrade as any,
          subject: 'math',
          language,
          role: 'student',
          avatarUrl: regAvatar,
          idCard: randomId,
        },
        regPin.trim()
      );
      if (localRes.success && localRes.account) {
        setNewlyIssuedCard(localRes.account);
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-[#0B1E16]/75 backdrop-blur-sm animate-fadeIn">
      {/* Outer Card Styled with Forest Theme: 3px dark green border & offset tactile shadow */}
      <div className="relative w-full max-w-md bg-[#F4FAF5] rounded-3xl border-3 border-[#1B4332] shadow-[6px_6px_0px_#1B4332] overflow-hidden flex flex-col max-h-[92vh]">
        {/* ========================================================================= */}
        {/* TOP HEADER: Deep Forest Green matching the Navigation Bar                 */}
        {/* ========================================================================= */}
        <div className="bg-[#1B4332] text-white px-5 py-4 border-b-3 border-[#1B4332] flex items-center justify-between select-none">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#2D6A4F] border-2 border-[#52B788] flex items-center justify-center text-xl shadow-[1.5px_1.5px_0px_#0B1E16]">
              {requiredRole === 'parent' ? '🛡️' : '🦁'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-black tracking-tight text-white leading-tight">
                  {newlyIssuedCard
                    ? 'Student ID Card Issued!'
                    : requiredRole === 'parent'
                    ? 'Parent Verification'
                    : selectedAccount
                    ? 'Student ID Sign-In'
                    : 'ReanMore Student Portal'}
                </h2>
              </div>
              <p className="text-[11px] text-[#A3E635] font-bold">
                {newlyIssuedCard
                  ? 'Your official digital identity card'
                  : 'Elementary Math & Science Companion'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-xl bg-[#2D6A4F] hover:bg-[#40916C] border-2 border-[#52B788] text-white flex items-center justify-center transition-all cursor-pointer shadow-[1.5px_1.5px_0px_#0B1E16] active:scale-95"
            title="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="mx-5 mt-3 p-3 bg-red-100 border-2 border-red-800 rounded-2xl flex items-center gap-2 text-red-900 text-xs font-black animate-shake shadow-[2px_2px_0px_#991B1B]">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-700" />
            <span>{error}</span>
          </div>
        )}

        {/* Modal Scrollable Content */}
        <div className="p-5 overflow-y-auto">
          {/* ========================================================================= */}
          {/* VIEW 1: NEWLY ISSUED DIGITAL STUDENT ID CARD SHOWCASE                     */}
          {/* ========================================================================= */}
          {newlyIssuedCard && (
            <div className="flex flex-col items-center space-y-4 animate-fadeIn">
              <div className="w-full bg-white rounded-3xl border-3 border-[#1B4332] shadow-[4px_4px_0px_#1B4332] overflow-hidden">
                {/* ID Card Top Ribbon */}
                <div className="bg-[#1B4332] px-4 py-2.5 flex items-center justify-between text-white border-b-2 border-[#1B4332]">
                  <div className="flex items-center gap-1.5">
                    <span className="text-base">🎓</span>
                    <span className="text-xs font-black tracking-wider uppercase">ReanMore Academy</span>
                  </div>
                  <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded-full bg-[#52B788] text-[#0B1E16] border border-[#1B4332]">
                    Official Student ID
                  </span>
                </div>

                {/* ID Card Body */}
                <div className="p-4 bg-[#EDF7EE] flex items-center gap-4">
                  {/* Photo Avatar Frame */}
                  <div className="w-20 h-20 rounded-2xl bg-white border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] flex flex-col items-center justify-center text-4xl shrink-0 relative overflow-hidden">
                    <span>{newlyIssuedCard.profile.avatarUrl || '🦁'}</span>
                    <div className="absolute bottom-0 inset-x-0 bg-[#1B4332] text-white text-[8px] font-black text-center py-0.5 uppercase tracking-tighter">
                      PHOTO
                    </div>
                  </div>

                  {/* Student Credentials */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-black text-[#1B4332] leading-snug truncate">
                      {getDisplayName(newlyIssuedCard.profile.name, false)}
                    </h3>
                    <div className="inline-block mt-1 px-2.5 py-1 rounded-xl bg-white border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332]">
                      <span className="text-xs font-black text-[#2D6A4F] tracking-wide font-mono">
                        {newlyIssuedCard.idCard || newlyIssuedCard.id}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1.5 text-[11px] font-bold text-[#1B4332]">
                      <span>Grade {newlyIssuedCard.profile.grade}</span>
                      <span>•</span>
                      <span>Academic Year 2026</span>
                    </div>
                  </div>
                </div>

                {/* ID Card Bottom Barcode Decorative Strip */}
                <div className="bg-white px-4 py-2 border-t-2 border-[#1B4332] flex items-center justify-between">
                  <div className="flex items-center gap-1 font-mono tracking-widest text-[#1B4332] text-xs font-black">
                    <QrCode className="w-4 h-4 text-[#1B4332]" />
                    <span>||| | | |||| || | |||</span>
                  </div>
                  <span className="text-[10px] font-bold text-[#52796F]">
                    PIN Protected
                  </span>
                </div>
              </div>

              <div className="text-center px-2">
                <p className="text-xs font-bold text-[#1B4332]">
                  🎉 Welcome to ReanMore, <strong>{newlyIssuedCard.profile.name}</strong>! Your Student ID is{' '}
                  <span className="text-[#2D6A4F] font-black underline">{newlyIssuedCard.idCard || newlyIssuedCard.id}</span>.
                </p>
                <p className="text-[11px] text-[#52796F] font-semibold mt-0.5">
                  Use this ID and your 4-digit PIN to log in anytime.
                </p>
              </div>

              <button
                type="button"
                onClick={() => {
                  onSuccess(newlyIssuedCard);
                  onClose();
                }}
                className="w-full py-3.5 px-5 rounded-2xl bg-[#2D6A4F] hover:bg-[#1B4332] text-white font-black text-sm border-2 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer flex items-center justify-center gap-2"
              >
                <span>Enter Homework Classroom</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* ========================================================================= */}
          {/* VIEW 2: TACTILE 4-DIGIT PIN KEYPAD (When a Student ID Card is selected)   */}
          {/* ========================================================================= */}
          {!newlyIssuedCard && selectedAccount && (
            <div className="flex flex-col items-center space-y-4 animate-fadeIn">
              {/* Selected ID Card Badge */}
              <div className="w-full bg-white rounded-2xl border-2 border-[#1B4332] p-3 shadow-[3px_3px_0px_#1B4332] flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-[#D8EEDF] border-2 border-[#1B4332] flex items-center justify-center text-2xl shrink-0">
                  {selectedAccount.profile.avatarUrl || '🦁'}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-black text-[#1B4332] text-sm truncate">
                      {getDisplayName(selectedAccount.profile.name, false)}
                    </h3>
                    <span className="px-2 py-0.5 rounded-full bg-[#D8EEDF] border border-[#1B4332] text-[10px] font-black text-[#1B4332]">
                      Grade {selectedAccount.profile.grade}
                    </span>
                  </div>
                  <span className="text-xs font-mono font-bold text-[#2D6A4F]">
                    {selectedAccount.idCard || selectedAccount.id}
                  </span>
                </div>
              </div>

              {/* 4 Glowing Dot Indicators */}
              <div className="flex items-center justify-center gap-3.5 py-1">
                {[0, 1, 2, 3].map((index) => {
                  const isFilled = pinInput.length > index;
                  return (
                    <div
                      key={index}
                      className={`w-4 h-4 rounded-full transition-all duration-200 border-2 border-[#1B4332] ${
                        isFilled
                          ? 'bg-[#2D6A4F] scale-125 shadow-[1.5px_1.5px_0px_#1B4332]'
                          : 'bg-white'
                      }`}
                    />
                  );
                })}
              </div>

              {/* 3x4 Tactile Keypad matching the forest theme */}
              <div className="w-full max-w-[270px] grid grid-cols-3 gap-2">
                {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map((digit) => (
                  <button
                    key={digit}
                    type="button"
                    onClick={() => handleDigitPress(digit)}
                    disabled={isLoading}
                    className="h-12 rounded-2xl bg-white hover:bg-[#D8EEDF] active:bg-[#B7E4C7] border-2 border-[#1B4332] text-[#1B4332] font-black text-xl flex items-center justify-center shadow-[2px_2px_0px_#1B4332] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer disabled:opacity-50 select-none"
                  >
                    {digit}
                  </button>
                ))}

                <button
                  type="button"
                  onClick={handleClearPin}
                  disabled={isLoading || pinInput.length === 0}
                  className="h-12 rounded-2xl bg-white hover:bg-rose-50 border-2 border-[#1B4332] text-rose-700 font-bold text-xs flex items-center justify-center shadow-[2px_2px_0px_#1B4332] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer disabled:opacity-40 select-none"
                >
                  Clear
                </button>

                <button
                  type="button"
                  onClick={() => handleDigitPress('0')}
                  disabled={isLoading}
                  className="h-12 rounded-2xl bg-white hover:bg-[#D8EEDF] active:bg-[#B7E4C7] border-2 border-[#1B4332] text-[#1B4332] font-black text-xl flex items-center justify-center shadow-[2px_2px_0px_#1B4332] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer disabled:opacity-50 select-none"
                >
                  0
                </button>

                <button
                  type="button"
                  onClick={handleBackspace}
                  disabled={isLoading || pinInput.length === 0}
                  className="h-12 rounded-2xl bg-white hover:bg-amber-50 border-2 border-[#1B4332] text-[#1B4332] font-bold flex items-center justify-center shadow-[2px_2px_0px_#1B4332] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer disabled:opacity-40 select-none"
                  title="Backspace"
                >
                  <Delete className="w-5 h-5" />
                </button>
              </div>

              {/* Back to ID Card List */}
              <div className="w-full flex items-center justify-between pt-1">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedAccount(null);
                    setPinInput('');
                    setError(null);
                  }}
                  className="flex items-center gap-1.5 text-xs font-black text-[#1B4332] hover:underline cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Choose Another Card</span>
                </button>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* VIEW 3: MAIN TABS (Register Student ID vs Log In with Student ID)         */}
          {/* ========================================================================= */}
          {!newlyIssuedCard && !selectedAccount && (
            <div className="space-y-4 animate-fadeIn">
              {/* Segmented Tab Pill Control */}
              <div className="flex bg-[#D8EEDF] p-1 rounded-2xl border-2 border-[#1B4332]">
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('register');
                    setError(null);
                  }}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl font-black text-xs sm:text-sm transition-all cursor-pointer ${
                    activeTab === 'register'
                      ? 'bg-[#1B4332] text-white shadow-[2px_2px_0px_#0B1E16]'
                      : 'text-[#1B4332] hover:bg-white/50'
                  }`}
                >
                  <CreditCard className="w-4 h-4" />
                  <span>Register ID Card</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('login');
                    setError(null);
                  }}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl font-black text-xs sm:text-sm transition-all cursor-pointer ${
                    activeTab === 'login'
                      ? 'bg-[#1B4332] text-white shadow-[2px_2px_0px_#0B1E16]'
                      : 'text-[#1B4332] hover:bg-white/50'
                  }`}
                >
                  <LogIn className="w-4 h-4" />
                  <span>Log In</span>
                </button>
              </div>

              {/* ───────────────────────────────────────────────────────────── */}
              {/* TAB A: REGISTER OFFICIAL STUDENT ID CARD                      */}
              {/* ───────────────────────────────────────────────────────────── */}
              {activeTab === 'register' && (
                <form onSubmit={handleRegister} className="space-y-3.5">
                  {/* Name Input */}
                  <div>
                    <label className="block text-xs font-black text-[#1B4332] uppercase tracking-wider mb-1">
                      Learner Full Name (ឈ្មោះសិស្ស)
                    </label>
                    <input
                      type="text"
                      required
                      value={regName}
                      onChange={(e) => setRegName(e.target.value)}
                      placeholder="e.g. Dara Pich, Sophea, Borey"
                      className="w-full px-3.5 py-2.5 bg-white border-2 border-[#1B4332] rounded-2xl text-sm font-black text-[#1B4332] placeholder-[#52796F] focus:outline-none focus:ring-2 focus:ring-[#40916C] shadow-[2px_2px_0px_#1B4332]"
                    />
                  </div>

                  {/* Character Avatar Picker */}
                  <div>
                    <label className="block text-xs font-black text-[#1B4332] uppercase tracking-wider mb-1.5">
                      Choose Your ID Photo Mascot
                    </label>
                    <div className="grid grid-cols-5 gap-2">
                      {AVATAR_OPTIONS.map((emoji) => {
                        const isSelected = regAvatar === emoji;
                        return (
                          <button
                            key={emoji}
                            type="button"
                            onClick={() => setRegAvatar(emoji)}
                            className={`h-11 rounded-2xl flex items-center justify-center text-2xl transition-all cursor-pointer border-2 border-[#1B4332] ${
                              isSelected
                                ? 'bg-[#D8EEDF] shadow-[2px_2px_0px_#1B4332] scale-105 ring-2 ring-[#2D6A4F]'
                                : 'bg-white hover:bg-[#F0FDF4]'
                            }`}
                          >
                            <span>{emoji}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Grade Level Selector */}
                  <div>
                    <label className="block text-xs font-black text-[#1B4332] uppercase tracking-wider mb-1.5">
                      Select Grade Level
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {[1, 2, 3, 4, 5, 6].map((grade) => {
                        const isSelected = regGrade === grade;
                        return (
                          <button
                            key={grade}
                            type="button"
                            onClick={() => setRegGrade(grade)}
                            className={`py-1.5 px-2 rounded-xl font-black text-xs transition-all cursor-pointer border-2 border-[#1B4332] ${
                              isSelected
                                ? 'bg-[#2D6A4F] text-white shadow-[2px_2px_0px_#1B4332]'
                                : 'bg-white text-[#1B4332] hover:bg-[#D8EEDF]'
                            }`}
                          >
                            Grade {grade}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Optional Custom ID Card Number */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-xs font-black text-[#1B4332] uppercase tracking-wider">
                        Student ID Card No. (លេខកាត)
                      </label>
                      <span className="text-[10px] font-bold text-[#52796F]">
                        Leave blank to auto-generate
                      </span>
                    </div>
                    <input
                      type="text"
                      value={regCustomId}
                      onChange={(e) => setRegCustomId(e.target.value.toUpperCase())}
                      placeholder="e.g. RM-88291 (Optional)"
                      className="w-full px-3.5 py-2.5 bg-white border-2 border-[#1B4332] rounded-2xl text-sm font-black text-[#1B4332] placeholder-[#52796F] font-mono focus:outline-none focus:ring-2 focus:ring-[#40916C] shadow-[2px_2px_0px_#1B4332]"
                    />
                  </div>

                  {/* 4-digit PIN */}
                  <div>
                    <label className="block text-xs font-black text-[#1B4332] uppercase tracking-wider mb-0.5">
                      Create 4-Digit Security PIN (លេខសម្ងាត់)
                    </label>
                    <p className="text-[10px] text-[#52796F] font-semibold mb-1">
                      You will use this PIN together with your Student ID Card to log in.
                    </p>
                    <input
                      type="password"
                      maxLength={6}
                      required
                      value={regPin}
                      onChange={(e) => setRegPin(e.target.value.replace(/\D/g, ''))}
                      placeholder="••••"
                      className="w-full px-3.5 py-2.5 bg-white border-2 border-[#1B4332] rounded-2xl text-center text-lg font-black tracking-widest text-[#1B4332] placeholder-[#52796F] focus:outline-none focus:ring-2 focus:ring-[#40916C] shadow-[2px_2px_0px_#1B4332]"
                    />
                  </div>

                  {/* Submit Button */}
                  <div className="pt-1">
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full py-3.5 px-5 rounded-2xl bg-[#2D6A4F] hover:bg-[#1B4332] text-white font-black text-sm border-2 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      <CreditCard className="w-4 h-4" />
                      <span>{isLoading ? 'Issuing Card...' : 'Issue Student ID & Start Learning 🚀'}</span>
                    </button>
                  </div>
                </form>
              )}

              {/* ───────────────────────────────────────────────────────────── */}
              {/* TAB B: LOG IN WITH STUDENT ID CARD                            */}
              {/* ───────────────────────────────────────────────────────────── */}
              {activeTab === 'login' && (
                <div className="space-y-3.5">
                  {/* Saved Student ID Cards on this device */}
                  {accounts.length > 0 && !isTypingLogin ? (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-black text-[#1B4332] uppercase tracking-wider">
                          Select Your Student ID Card
                        </p>
                        <span className="text-[10px] font-black text-[#1B4332] bg-[#D8EEDF] px-2 py-0.5 rounded-full border border-[#1B4332]">
                          Tap to enter PIN
                        </span>
                      </div>

                      {/* ID Card Badges */}
                      <div className="space-y-2.5 max-h-60 overflow-y-auto pr-1">
                        {accounts.map((acc) => {
                          const isCurrent = current?.id === acc.id;
                          return (
                            <div
                              key={acc.id}
                              onClick={() => {
                                setSelectedAccount(acc);
                                setPinInput('');
                                setError(null);
                              }}
                              className={`w-full flex items-center justify-between p-3 rounded-2xl border-2 border-[#1B4332] transition-all cursor-pointer group select-none ${
                                isCurrent
                                  ? 'bg-[#D8EEDF] shadow-[3px_3px_0px_#1B4332] ring-2 ring-[#2D6A4F]'
                                  : 'bg-white hover:bg-[#EDF7EE] shadow-[2px_2px_0px_#1B4332]'
                              }`}
                            >
                              <div className="flex items-center gap-3 min-w-0">
                                <div className="w-11 h-11 rounded-xl bg-[#EDF7EE] border-2 border-[#1B4332] flex items-center justify-center text-2xl shrink-0 group-hover:scale-105 transition-transform shadow-[1px_1px_0px_#1B4332]">
                                  {acc.profile.avatarUrl || '🦁'}
                                </div>
                                <div className="min-w-0">
                                  <div className="flex items-center gap-1.5">
                                    <span className="font-black text-[#1B4332] text-sm truncate">
                                      {getDisplayName(acc.profile.name, false)}
                                    </span>
                                    {isCurrent && (
                                      <span className="px-1.5 py-0.2 rounded-full bg-[#1B4332] text-white text-[9px] font-bold">
                                        Active
                                      </span>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-2 mt-0.5">
                                    <span className="text-[11px] font-mono font-black text-[#2D6A4F]">
                                      {acc.idCard || acc.id}
                                    </span>
                                    <span className="text-[10px] font-bold text-[#52796F]">
                                      • Grade {acc.profile.grade}
                                    </span>
                                  </div>
                                </div>
                              </div>

                              <div className="flex items-center gap-1 text-[#1B4332] shrink-0 font-black text-xs">
                                <span>PIN</span>
                                <ChevronRight className="w-4 h-4" />
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Manual ID Card Input Toggle */}
                      <button
                        type="button"
                        onClick={() => {
                          setIsTypingLogin(true);
                          setError(null);
                        }}
                        className="w-full py-2.5 px-3 rounded-xl bg-white hover:bg-[#EDF7EE] text-[#1B4332] font-black text-xs border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] transition-colors cursor-pointer text-center"
                      >
                        Sign in with another Student ID Card No.
                      </button>
                    </div>
                  ) : (
                    /* Manual Student ID Card Login Form */
                    <form onSubmit={handleManualLogin} className="space-y-3.5">
                      {accounts.length > 0 && (
                        <button
                          type="button"
                          onClick={() => {
                            setIsTypingLogin(false);
                            setError(null);
                          }}
                          className="flex items-center gap-1.5 text-xs font-black text-[#1B4332] hover:underline cursor-pointer mb-1"
                        >
                          <ArrowLeft className="w-4 h-4" />
                          <span>Back to saved ID cards</span>
                        </button>
                      )}

                      <div>
                        <label className="block text-xs font-black text-[#1B4332] uppercase tracking-wider mb-1">
                          Student ID Card No. or Name (លេខកាតសិស្ស ឬឈ្មោះ)
                        </label>
                        <input
                          type="text"
                          required
                          value={loginIdentifier}
                          onChange={(e) => setLoginIdentifier(e.target.value)}
                          placeholder="e.g. RM-96960 or Piseth"
                          className="w-full px-3.5 py-2.5 bg-white border-2 border-[#1B4332] rounded-2xl text-sm font-black text-[#1B4332] placeholder-[#52796F] font-mono focus:outline-none focus:ring-2 focus:ring-[#40916C] shadow-[2px_2px_0px_#1B4332]"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-black text-[#1B4332] uppercase tracking-wider mb-1">
                          4-Digit Security PIN (លេខសម្ងាត់)
                        </label>
                        <input
                          type="password"
                          maxLength={6}
                          required
                          value={manualPin}
                          onChange={(e) => setManualPin(e.target.value.replace(/\D/g, ''))}
                          placeholder="••••"
                          className="w-full px-3.5 py-2.5 bg-white border-2 border-[#1B4332] rounded-2xl text-center text-lg font-black tracking-widest text-[#1B4332] placeholder-[#52796F] focus:outline-none focus:ring-2 focus:ring-[#40916C] shadow-[2px_2px_0px_#1B4332]"
                        />
                      </div>

                      <div className="pt-1">
                        <button
                          type="submit"
                          disabled={isLoading}
                          className="w-full py-3.5 px-5 rounded-2xl bg-[#2D6A4F] hover:bg-[#1B4332] text-white font-black text-sm border-2 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] active:translate-x-0.5 active:translate-y-0.5 transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                          <LogIn className="w-4 h-4" />
                          <span>{isLoading ? 'Verifying Card...' : 'Sign In with Student ID 🚀'}</span>
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
