import React, { useState, useEffect, useCallback } from 'react';
import { UserAccount, UserRole, Language } from '../types';
import { AuthService } from '../services/authService';
import { getDisplayName } from '../utils/language';
import {
  User,
  UserPlus,
  LogIn,
  X,
  AlertCircle,
  ArrowLeft,
  ChevronRight,
  Sparkles,
  Check,
  Delete,
} from 'lucide-react';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (account: UserAccount) => void;
  language?: Language | undefined;
  requiredRole?: UserRole | undefined; // Used for Parent Report mode verification
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

  // Selected profile for PIN pad mode (when tapping a saved profile)
  const [selectedAccount, setSelectedAccount] = useState<UserAccount | null>(null);

  // Toggle for typing a username manually on the login tab
  const [isTypingLogin, setIsTypingLogin] = useState(false);

  // PIN entry states
  const [pinInput, setPinInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Manual Login fields
  const [loginUsername, setLoginUsername] = useState('');
  const [manualPin, setManualPin] = useState('');

  // Register fields
  const [regName, setRegName] = useState('');
  const [regAvatar, setRegAvatar] = useState('👦');
  const [regGrade, setRegGrade] = useState<number>(4);
  const [regPin, setRegPin] = useState('');

  // Reset state on open/close
  useEffect(() => {
    if (isOpen) {
      setError(null);
      setPinInput('');
      setManualPin('');
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
        const res = await AuthService.loginRemote(selectedAccount.username, pinToTest);
        if (res.success && res.account) {
          onSuccess(res.account);
          onClose();
        } else {
          setError(res.errorEng || 'Incorrect PIN. Please try again.');
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

  // Handle keypad digit tap
  const handleDigitPress = (digit: string) => {
    if (pinInput.length >= 4) return;
    const nextPin = pinInput + digit;
    setPinInput(nextPin);
    setError(null);

    // Auto-submit on 4th digit
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

  // Keyboard listener for PIN mode
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

  // Handle Manual Login Submit
  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginUsername.trim()) {
      setError('Please enter your name or username.');
      return;
    }
    if (!manualPin.trim() || manualPin.trim().length < 4) {
      setError('Please enter your 4-digit PIN.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const res = await AuthService.loginRemote(loginUsername.trim(), manualPin.trim());
      if (res.success && res.account) {
        onSuccess(res.account);
        onClose();
      } else {
        setError(res.errorEng || 'Account not found or incorrect PIN. Please try again.');
      }
    } catch {
      setError('Network error. Logging into offline profile.');
      const localRes = AuthService.login(loginUsername.trim(), manualPin.trim());
      if (localRes.success && localRes.account) {
        onSuccess(localRes.account);
        onClose();
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Register Submit
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regName.trim()) {
      setError('Please enter your name.');
      return;
    }
    if (!regPin.trim() || regPin.trim().length < 4) {
      setError('Please choose a 4-digit PIN to protect your profile.');
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
        regAvatar
      );

      if (res.success && res.account) {
        onSuccess(res.account);
        onClose();
      } else {
        setError(res.errorEng || 'Registration failed. Please try a different name.');
      }
    } catch {
      setError('Could not connect to database. Profile created locally.');
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
        },
        regPin.trim()
      );
      if (localRes.success && localRes.account) {
        onSuccess(localRes.account);
        onClose();
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl shadow-emerald-950/15 border border-slate-100 overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header Banner */}
        <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-sky-600 text-white px-6 py-5 relative select-none">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-2xl bg-white/20 backdrop-blur-md border border-white/30 flex items-center justify-center text-2xl shadow-inner">
                {requiredRole === 'parent' ? '🛡️' : '🎓'}
              </div>
              <div>
                <h2 className="text-lg sm:text-xl font-black tracking-tight leading-snug">
                  {requiredRole === 'parent'
                    ? 'Parent Verification'
                    : selectedAccount
                    ? 'Learner Sign-In'
                    : activeTab === 'register'
                    ? 'Create Learner Profile'
                    : 'Welcome Back!'}
                </h2>
                <p className="text-xs text-white/85 font-medium">
                  {requiredRole === 'parent'
                    ? 'Enter parent PIN code to access reports'
                    : selectedAccount
                    ? `Logging in as ${selectedAccount.profile.name}`
                    : activeTab === 'register'
                    ? 'Join ReanMore to explore Math & Science'
                    : 'Choose your profile or enter your PIN'}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-full text-white/80 hover:text-white hover:bg-white/20 transition-all cursor-pointer"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-2.5 text-red-700 text-xs sm:text-sm font-semibold animate-shake">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
            <span>{error}</span>
          </div>
        )}

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto">
          {/* ========================================================================= */}
          {/* SCREEN A: PIN ENTRY KEYPAD SCREEN (When a profile is selected)           */}
          {/* ========================================================================= */}
          {selectedAccount && (
            <div className="flex flex-col items-center space-y-5 animate-fadeIn">
              {/* Profile Card Header */}
              <div className="flex flex-col items-center text-center">
                <div className="w-16 h-16 rounded-full bg-emerald-50 border-2 border-emerald-400 flex items-center justify-center text-3xl shadow-sm mb-2">
                  {selectedAccount.profile.avatarUrl || '👦'}
                </div>
                <h3 className="font-black text-slate-800 text-lg">
                  {getDisplayName(selectedAccount.profile.name, false)}
                </h3>
                <span className="text-xs text-slate-500 font-medium">
                  Grade {selectedAccount.profile.grade} Learner
                </span>
              </div>

              {/* 4 Visual PIN Indicator Dots */}
              <div className="flex items-center justify-center gap-4 py-2">
                {[0, 1, 2, 3].map((index) => {
                  const isFilled = pinInput.length > index;
                  return (
                    <div
                      key={index}
                      className={`w-4 h-4 rounded-full transition-all duration-200 ${
                        isFilled
                          ? 'bg-emerald-500 border-2 border-emerald-500 scale-125 shadow-md shadow-emerald-500/30'
                          : 'bg-slate-100 border-2 border-slate-300'
                      }`}
                    />
                  );
                })}
              </div>

              {/* Tactile On-Screen Number Pad */}
              <div className="w-full max-w-[280px] grid grid-cols-3 gap-2.5 pt-1">
                {['1', '2', '3', '4', '5', '6', '7', '8', '9'].map((digit) => (
                  <button
                    key={digit}
                    type="button"
                    onClick={() => handleDigitPress(digit)}
                    disabled={isLoading}
                    className="h-13 sm:h-14 rounded-2xl bg-slate-50 hover:bg-emerald-50 active:bg-emerald-100 border border-slate-200 text-slate-800 font-black text-xl flex items-center justify-center transition-all active:scale-95 cursor-pointer shadow-sm disabled:opacity-50 select-none"
                  >
                    {digit}
                  </button>
                ))}

                <button
                  type="button"
                  onClick={handleClearPin}
                  disabled={isLoading || pinInput.length === 0}
                  className="h-13 sm:h-14 rounded-2xl bg-slate-50 hover:bg-rose-50 border border-slate-200 text-slate-500 font-bold text-xs flex items-center justify-center transition-all active:scale-95 cursor-pointer shadow-sm disabled:opacity-40 select-none"
                >
                  Clear
                </button>

                <button
                  type="button"
                  onClick={() => handleDigitPress('0')}
                  disabled={isLoading}
                  className="h-13 sm:h-14 rounded-2xl bg-slate-50 hover:bg-emerald-50 active:bg-emerald-100 border border-slate-200 text-slate-800 font-black text-xl flex items-center justify-center transition-all active:scale-95 cursor-pointer shadow-sm disabled:opacity-50 select-none"
                >
                  0
                </button>

                <button
                  type="button"
                  onClick={handleBackspace}
                  disabled={isLoading || pinInput.length === 0}
                  className="h-13 sm:h-14 rounded-2xl bg-slate-50 hover:bg-amber-50 border border-slate-200 text-slate-600 font-bold flex items-center justify-center transition-all active:scale-95 cursor-pointer shadow-sm disabled:opacity-40 select-none"
                  title="Backspace"
                >
                  <Delete className="w-5 h-5" />
                </button>
              </div>

              {/* Bottom Actions */}
              <div className="w-full flex items-center justify-between pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedAccount(null);
                    setPinInput('');
                    setError(null);
                  }}
                  className="flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Switch Profile</span>
                </button>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* SCREEN B: MAIN TABS (Register vs Log In)                                   */}
          {/* ========================================================================= */}
          {!selectedAccount && (
            <div className="space-y-5 animate-fadeIn">
              {/* Segmented Tab Control: Register vs Log In */}
              <div className="flex bg-slate-100 p-1 rounded-2xl border border-slate-200">
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('register');
                    setError(null);
                  }}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl font-bold text-xs sm:text-sm transition-all cursor-pointer ${
                    activeTab === 'register'
                      ? 'bg-white text-emerald-800 shadow-sm'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <Sparkles className="w-4 h-4 text-emerald-600" />
                  <span>Register</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setActiveTab('login');
                    setError(null);
                  }}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl font-bold text-xs sm:text-sm transition-all cursor-pointer ${
                    activeTab === 'login'
                      ? 'bg-white text-slate-800 shadow-sm'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <LogIn className="w-4 h-4" />
                  <span>Log In</span>
                </button>
              </div>

              {/* ───────────────────────────────────────────────────────────── */}
              {/* TAB 1: REGISTER NEW LEARNER                                  */}
              {/* ───────────────────────────────────────────────────────────── */}
              {activeTab === 'register' && (
                <form onSubmit={handleRegister} className="space-y-4">
                  {/* Name Input */}
                  <div>
                    <label className="block text-xs font-black text-slate-700 uppercase tracking-wider mb-1.5">
                      Learner Name
                    </label>
                    <input
                      type="text"
                      required
                      value={regName}
                      onChange={(e) => setRegName(e.target.value)}
                      placeholder="e.g. Dara, Sophea, Pich"
                      className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-bold text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all"
                    />
                  </div>

                  {/* Character Avatar Picker */}
                  <div>
                    <label className="block text-xs font-black text-slate-700 uppercase tracking-wider mb-2">
                      Choose Your Mascot
                    </label>
                    <div className="grid grid-cols-5 gap-2">
                      {AVATAR_OPTIONS.map((emoji) => {
                        const isSelected = regAvatar === emoji;
                        return (
                          <button
                            key={emoji}
                            type="button"
                            onClick={() => setRegAvatar(emoji)}
                            className={`h-12 rounded-2xl flex items-center justify-center text-2xl transition-all cursor-pointer relative ${
                              isSelected
                                ? 'bg-emerald-100/70 border-2 border-emerald-500 scale-105 shadow-sm'
                                : 'bg-slate-50 border border-slate-200 hover:bg-slate-100 hover:scale-102'
                            }`}
                          >
                            <span>{emoji}</span>
                            {isSelected && (
                              <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-600 text-white flex items-center justify-center">
                                <Check className="w-2.5 h-2.5 stroke-[3]" />
                              </div>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Grade Level Selector */}
                  <div>
                    <label className="block text-xs font-black text-slate-700 uppercase tracking-wider mb-2">
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
                            className={`py-2 px-3 rounded-xl font-bold text-xs transition-all cursor-pointer ${
                              isSelected
                                ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-600/30 ring-2 ring-emerald-600/20'
                                : 'bg-slate-50 border border-slate-200 text-slate-600 hover:bg-slate-100'
                            }`}
                          >
                            Grade {grade}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* 4-digit PIN */}
                  <div>
                    <label className="block text-xs font-black text-slate-700 uppercase tracking-wider mb-1">
                      Create 4-Digit PIN
                    </label>
                    <p className="text-[11px] text-slate-400 mb-1.5 font-medium">
                      Keep your progress safe. You'll use this to sign in later.
                    </p>
                    <input
                      type="password"
                      maxLength={6}
                      required
                      value={regPin}
                      onChange={(e) => setRegPin(e.target.value.replace(/\D/g, ''))}
                      placeholder="e.g. 1234"
                      className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl text-center text-lg font-black tracking-widest text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all"
                    />
                  </div>

                  {/* Register Submit Button */}
                  <div className="pt-2">
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full py-3.5 px-5 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-black text-sm shadow-lg shadow-emerald-600/25 active:scale-98 transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      <UserPlus className="w-4 h-4" />
                      <span>{isLoading ? 'Creating Account...' : 'Start Learning 🚀'}</span>
                    </button>
                  </div>
                </form>
              )}

              {/* ───────────────────────────────────────────────────────────── */}
              {/* TAB 2: LOG IN                                                 */}
              {/* ───────────────────────────────────────────────────────────── */}
              {activeTab === 'login' && (
                <div className="space-y-4">
                  {/* If user has saved profiles on this device AND is not typing manually */}
                  {accounts.length > 0 && !isTypingLogin ? (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <p className="text-xs font-black text-slate-600 uppercase tracking-wider">
                          Select Your Profile
                        </p>
                        <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                          Tap to enter PIN
                        </span>
                      </div>

                      <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
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
                              className={`w-full flex items-center justify-between p-3.5 rounded-2xl border transition-all cursor-pointer group select-none ${
                                isCurrent
                                  ? 'bg-emerald-50/60 border-emerald-300 ring-2 ring-emerald-500/20'
                                  : 'bg-white border-slate-200 hover:border-emerald-300 hover:bg-slate-50/70 shadow-sm'
                              }`}
                            >
                              <div className="flex items-center gap-3.5 min-w-0">
                                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-100 to-teal-50 border border-emerald-200 flex items-center justify-center text-2xl shrink-0 group-hover:scale-105 transition-transform shadow-xs">
                                  {acc.profile.avatarUrl || '👦'}
                                </div>
                                <div className="min-w-0">
                                  <div className="flex items-center gap-2">
                                    <span className="font-black text-slate-900 text-sm truncate">
                                      {getDisplayName(acc.profile.name, false)}
                                    </span>
                                    {isCurrent && (
                                      <span className="px-2 py-0.5 rounded-full bg-emerald-600 text-white text-[10px] font-bold shrink-0">
                                        Active
                                      </span>
                                    )}
                                  </div>
                                  <span className="text-xs text-slate-500 font-medium">
                                    Grade {acc.profile.grade} Learner
                                  </span>
                                </div>
                              </div>

                              <div className="flex items-center gap-1.5 text-slate-400 group-hover:text-emerald-600 transition-colors shrink-0">
                                <span className="text-xs font-bold hidden sm:inline">Enter PIN</span>
                                <ChevronRight className="w-4 h-4" />
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Manual Login Switcher */}
                      <button
                        type="button"
                        onClick={() => {
                          setIsTypingLogin(true);
                          setError(null);
                        }}
                        className="w-full py-2.5 px-3 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-600 font-bold text-xs border border-slate-200 transition-colors cursor-pointer text-center"
                      >
                        Log in by typing name & PIN
                      </button>
                    </div>
                  ) : (
                    /* Manual Name + PIN Login Form */
                    <form onSubmit={handleManualLogin} className="space-y-4">
                      {accounts.length > 0 && (
                        <button
                          type="button"
                          onClick={() => {
                            setIsTypingLogin(false);
                            setError(null);
                          }}
                          className="flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors cursor-pointer mb-2"
                        >
                          <ArrowLeft className="w-4 h-4" />
                          <span>Back to saved profiles</span>
                        </button>
                      )}

                      <div>
                        <label className="block text-xs font-black text-slate-700 uppercase tracking-wider mb-1.5">
                          Learner Name or Username
                        </label>
                        <input
                          type="text"
                          required
                          value={loginUsername}
                          onChange={(e) => setLoginUsername(e.target.value)}
                          placeholder="e.g. Dara"
                          className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl text-sm font-bold text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-black text-slate-700 uppercase tracking-wider mb-1.5">
                          4-Digit PIN
                        </label>
                        <input
                          type="password"
                          maxLength={6}
                          required
                          value={manualPin}
                          onChange={(e) => setManualPin(e.target.value.replace(/\D/g, ''))}
                          placeholder="••••"
                          className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-2xl text-center text-lg font-black tracking-widest text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all"
                        />
                      </div>

                      <div className="pt-2">
                        <button
                          type="submit"
                          disabled={isLoading}
                          className="w-full py-3.5 px-5 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-black text-sm shadow-lg shadow-emerald-600/25 active:scale-98 transition-all cursor-pointer flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                          <LogIn className="w-4 h-4" />
                          <span>{isLoading ? 'Signing In...' : 'Log In'}</span>
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
