import React, { useState } from 'react';
import { UserAccount, UserRole, Language } from '../types';
import { AuthService } from '../services/authService';
import { getDisplayName } from '../utils/language';
import { User, Shield, KeyRound, UserPlus, LogIn, X, Check, AlertCircle } from 'lucide-react';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (account: UserAccount) => void;
  language?: Language | undefined;
  requiredRole?: UserRole | undefined; // If opening specifically for Parent mode verification
  initialMode?: 'select' | 'login' | 'create' | undefined;
}

export const LoginModal: React.FC<LoginModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  language = 'en',
  requiredRole,
  initialMode = 'select',
}) => {
  const isKhmer = false;
  const accounts = AuthService.getAccounts();
  const current = AuthService.getCurrentUser();

  const [mode, setMode] = useState<'select' | 'login' | 'create'>(
    requiredRole === 'parent' ? 'login' : initialMode
  );
  const [selectedAccount, setSelectedAccount] = useState<UserAccount | null>(() => {
    if (requiredRole === 'parent') {
      return accounts.find((a) => a.role === 'parent') || null;
    }
    return null;
  });

  const [pinInput, setPinInput] = useState(() => {
    if (requiredRole === 'parent') {
      const parentAcc = accounts.find((a) => a.role === 'parent');
      return parentAcc?.pin || '9999';
    }
    return '';
  });
  const [usernameInput, setUsernameInput] = useState('');
  const [newName, setNewName] = useState('');
  const [newUsername, setNewUsername] = useState('');
  const [newRole, setNewRole] = useState<UserRole>(requiredRole || 'student');
  const [newGrade, setNewGrade] = useState<number>(4);
  const [newPin, setNewPin] = useState('');
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleAccountClick = async (acc: UserAccount, quickLogin = false) => {
    setError(null);
    setSelectedAccount(acc);
    setPinInput(acc.pin || '');

    if (quickLogin || !acc.pin) {
      const res = await AuthService.loginRemote('GRADE4A', acc.username, acc.pin || '1234');
      if (res.success && res.account) {
        onSuccess(res.account);
        onClose();
      }
    } else {
      setMode('login');
    }
  };

  const handlePinSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!selectedAccount) return;

    setError(null);
    const res = await AuthService.loginRemote('GRADE4A', selectedAccount.username, pinInput);
    if (res.success && res.account) {
      onSuccess(res.account);
      onClose();
    } else {
      setError(isKhmer ? res.errorKhmer || 'លេខ PIN មិនត្រឹមត្រូវទេ' : res.errorEng || 'Incorrect PIN');
    }
  };

  const handleCustomLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!usernameInput.trim()) {
      setError(isKhmer ? 'សូមបញ្ចូលឈ្មោះអ្នកប្រើ' : 'Please enter a username');
      return;
    }

    const res = await AuthService.loginRemote('GRADE4A', usernameInput, pinInput || '1234');
    if (res.success && res.account) {
      onSuccess(res.account);
      onClose();
    } else {
      setError(isKhmer ? res.errorKhmer || 'ការចូលបរាជ័យ' : res.errorEng || 'Login failed');
    }
  };

  const handleCreateAccount = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!newUsername.trim() || !newName.trim()) {
      setError(isKhmer ? 'សូមបំពេញព័ត៌មានទាំងអស់' : 'Please fill all required fields');
      return;
    }

    const res = AuthService.createAccount(
      newUsername,
      newRole,
      {
        name: newName.trim(),
        grade: (newRole === 'student' ? newGrade : 4) as any,
        subject: 'math',
        language,
        role: newRole,
      },
      newPin || undefined
    );

    if (res.success && res.account) {
      onSuccess(res.account);
      onClose();
    } else {
      setError(isKhmer ? res.errorKhmer || 'មិនអាចបង្កើតគណនីបានទេ' : res.errorEng || 'Failed to create account');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-md bg-white rounded-3xl border-3 border-[#1B4332] shadow-[6px_6px_0px_#1B4332] overflow-hidden">
        {/* Header Banner */}
        <div className="bg-[#1B4332] text-white px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-[#40916C] border-2 border-white/30 flex items-center justify-center">
              {requiredRole === 'parent' ? (
                <Shield className="w-5 h-5 text-white" />
              ) : (
                <User className="w-5 h-5 text-white" />
              )}
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-black tracking-wide leading-tight">
                {requiredRole === 'parent'
                  ? isKhmer
                    ? 'ការផ្ទៀងផ្ទាត់អាណាព្យាបាល'
                    : 'Parent Verification'
                  : mode === 'create'
                  ? isKhmer
                    ? 'បង្កើតគណនីថ្មី'
                    : 'Create New Account'
                  : mode === 'login'
                  ? isKhmer
                    ? 'ចូលគណនី'
                    : 'Log In'
                  : isKhmer
                  ? 'ជ្រើសរើស ឬចូលគណនី'
                  : 'Select or Log In'}
              </h2>
              <p className="text-xs text-white/80 font-medium">
                {requiredRole === 'parent'
                  ? isKhmer
                    ? 'សូមបញ្ចូលកូដ PIN អាណាព្យាបាល (PIN: 9999)'
                    : 'Enter Parent PIN code (PIN: 9999)'
                  : isKhmer
                  ? 'ReanMore AI Homework Tutor'
                  : 'ReanMore AI Homework Tutor'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-colors cursor-pointer"
            title={isKhmer ? 'បិទ' : 'Close'}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="mx-5 mt-4 p-3 bg-red-50 border-2 border-red-300 rounded-xl flex items-center gap-2 text-red-700 text-xs sm:text-sm font-bold animate-shake">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-500" />
            <span>{error}</span>
          </div>
        )}

        <div className="p-5">
          {/* MODE 1: SELECT EXISTING ACCOUNT */}
          {mode === 'select' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-xs sm:text-sm font-black text-gray-800">
                  {isKhmer ? 'ជ្រើសរើសគណនីរបស់អ្នក៖' : 'Choose your account:'}
                </p>
                <span className="text-[11px] font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full border border-emerald-300">
                  {isKhmer ? 'គណនីគំរូសាកល្បង' : 'Demo Accounts'}
                </span>
              </div>

              <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                {accounts.map((acc) => {
                  const isCurrent = current?.id === acc.id;
                  const isParent = acc.role === 'parent';

                  return (
                    <div
                      key={acc.id}
                      className={`w-full flex items-center justify-between p-3 rounded-2xl border-2 transition-all ${
                        isCurrent
                          ? 'bg-[#E8F5E9] border-[#2D6A4F] shadow-[3px_3px_0px_#2D6A4F]'
                          : 'bg-white border-[#1B4332]/30 hover:border-[#1B4332] shadow-[2px_2px_0px_rgba(0,0,0,0.08)]'
                      }`}
                    >
                      {/* Account Info Clickable */}
                      <button
                        type="button"
                        onClick={() => handleAccountClick(acc, false)}
                        className="flex items-center gap-3 flex-1 text-left cursor-pointer min-w-0"
                      >
                        <div
                          className={`w-10 h-10 rounded-xl border-2 flex items-center justify-center font-black text-base shrink-0 ${
                            isParent
                              ? 'bg-amber-100 border-amber-500 text-amber-800'
                              : 'bg-emerald-100 border-emerald-500 text-emerald-800'
                          }`}
                        >
                          {isParent ? <Shield className="w-5 h-5" /> : <User className="w-5 h-5" />}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="font-black text-sm text-gray-900 truncate">
                              {getDisplayName(acc.profile.name, false)}
                            </span>
                            {isCurrent && (
                              <span className="px-1.5 py-0.5 rounded-full bg-[#2D6A4F] text-white text-[10px] font-bold shrink-0">
                                Active
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                            <span className="text-xs text-gray-500 font-medium">
                              {isParent
                                ? isKhmer
                                  ? 'អាណាព្យាបាល'
                                  : 'Parent'
                                : isKhmer
                                ? `ថ្នាក់ទី ${acc.profile.grade}`
                                : `Grade ${acc.profile.grade}`}
                            </span>
                            {acc.pin && (
                              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-amber-100 border border-amber-300 text-amber-900 font-mono text-[11px] font-black">
                                <KeyRound className="w-3 h-3 text-amber-700" />
                                PIN: {acc.pin}
                              </span>
                            )}
                          </div>
                        </div>
                      </button>

                      {/* Quick Login Button */}
                      <div className="shrink-0 pl-2">
                        <button
                          type="button"
                          onClick={() => handleAccountClick(acc, true)}
                          title={isKhmer ? 'ចូលភ្លាមៗដោយមិនបាច់វាយ PIN' : 'Instant Login without typing PIN'}
                          className="py-1.5 px-3 rounded-xl bg-[#2D6A4F] hover:bg-[#1B4332] text-white font-black text-xs border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] transition-transform active:scale-95 cursor-pointer flex items-center gap-1"
                        >
                          <LogIn className="w-3.5 h-3.5" />
                          <span>{isKhmer ? 'ចូលភ្លាមៗ' : 'Login'}</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex flex-col gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setError(null);
                    setMode('create');
                  }}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-[#2D6A4F] hover:bg-[#1B4332] text-white font-black text-xs sm:text-sm border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] transition-all cursor-pointer"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>{isKhmer ? 'បង្កើតគណនីថ្មី' : 'Create New Account'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setError(null);
                    setSelectedAccount(null);
                    setMode('login');
                  }}
                  className="w-full flex items-center justify-center gap-1.5 py-2 px-4 text-xs font-bold text-gray-600 hover:text-gray-900 hover:underline cursor-pointer"
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span>{isKhmer ? 'ចូលដោយវាយឈ្មោះ និងលេខកូដ PIN' : 'Log in by typing username & PIN'}</span>
                </button>
              </div>
            </div>
          )}

          {/* MODE 2: ENTER PIN OR LOGIN CREDENTIALS */}
          {mode === 'login' && (
            <div className="space-y-4">
              {selectedAccount ? (
                <div>
                  <div className="flex items-center gap-3 p-3 bg-emerald-50 border-2 border-emerald-200 rounded-2xl mb-3">
                    <div className="w-9 h-9 rounded-xl bg-white border border-emerald-300 flex items-center justify-center">
                      {selectedAccount.role === 'parent' ? <Shield className="w-5 h-5 text-amber-800" /> : <User className="w-5 h-5 text-emerald-800" />}
                    </div>
                    <div className="flex-1">
                      <div className="font-black text-sm text-gray-900">{selectedAccount.profile.name}</div>
                      <div className="text-xs text-gray-500 font-medium">
                        {selectedAccount.role === 'parent'
                          ? isKhmer
                            ? 'គណនីអាណាព្យាបាល'
                            : 'Parent Account'
                          : isKhmer
                          ? `សិស្ស ថ្នាក់ទី ${selectedAccount.profile.grade}`
                          : `Student Grade ${selectedAccount.profile.grade}`}
                      </div>
                    </div>
                  </div>

                  {/* Prominent Hardcoded PIN Display & Auto-fill */}
                  {selectedAccount.pin && (
                    <div className="flex items-center justify-between p-3 bg-amber-50 border-2 border-amber-300 rounded-2xl mb-3">
                      <div className="flex items-center gap-2">
                        <KeyRound className="w-4 h-4 text-amber-700 shrink-0" />
                        <div>
                          <div className="text-xs font-black text-amber-900">
                            {isKhmer ? 'លេខ PIN គំរូសាកល្បង៖' : 'Demo PIN Code:'}
                          </div>
                          <div className="text-[10px] text-amber-700">
                            {isKhmer ? 'លេខកូដសម្ងាត់ដែលបានកំណត់' : 'Preset mock PIN'}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="px-2.5 py-1 bg-white border-2 border-amber-400 rounded-xl font-mono text-sm font-black text-amber-900 shadow-sm">
                          {selectedAccount.pin}
                        </span>
                        <button
                          type="button"
                          onClick={() => setPinInput(selectedAccount.pin || '')}
                          className="px-2.5 py-1 text-xs font-black text-white bg-[#2D6A4F] hover:bg-[#1B4332] rounded-xl border border-[#1B4332] cursor-pointer shadow-[1px_1px_0px_#1B4332]"
                        >
                          {isKhmer ? 'បំពេញ PIN' : 'Auto-Fill'}
                        </button>
                      </div>
                    </div>
                  )}

                  <form onSubmit={handlePinSubmit} className="space-y-4">
                    <div>
                      <label className="block text-xs font-black text-gray-700 uppercase tracking-wider mb-1.5">
                        {isKhmer ? 'លេខកូដសម្ងាត់ (PIN ៤ ខ្ទង់)' : '4-Digit PIN Code'}
                      </label>
                      <div className="relative">
                        <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                          type="password"
                          maxLength={6}
                          autoFocus
                          value={pinInput}
                          onChange={(e) => setPinInput(e.target.value)}
                          placeholder="••••"
                          className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border-2 border-[#1B4332] rounded-xl text-center text-lg font-black tracking-widest text-gray-900 focus:outline-none focus:bg-white focus:ring-2 focus:ring-[#40916C]"
                        />
                      </div>
                    </div>

                    <div className="flex gap-2 pt-2">
                      <button
                        type="button"
                        onClick={() => {
                          setError(null);
                          setMode('select');
                        }}
                        className="flex-1 py-2.5 px-4 rounded-xl border-2 border-gray-300 hover:bg-gray-100 text-gray-700 font-bold text-xs sm:text-sm cursor-pointer"
                      >
                        {isKhmer ? 'ត្រឡប់ក្រោយ' : 'Back'}
                      </button>
                      <button
                        type="submit"
                        className="flex-[2] py-2.5 px-4 rounded-xl bg-[#40916C] hover:bg-[#2D6A4F] text-white font-black text-xs sm:text-sm border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] cursor-pointer flex items-center justify-center gap-1.5"
                      >
                        <Check className="w-4 h-4" />
                        <span>{isKhmer ? 'ចូលគណនី' : 'Confirm Log In'}</span>
                      </button>
                    </div>
                  </form>
                </div>
              ) : (
                <form onSubmit={handleCustomLogin} className="space-y-3.5">
                  {/* Demo account click chips */}
                  <div className="p-3 bg-emerald-50 border-2 border-emerald-300 rounded-2xl space-y-2">
                    <div className="text-xs font-black text-emerald-900">
                      {isKhmer ? 'ចុចលើគណនីគំរូដើម្បីបំពេញស្វ័យប្រវត្តិ៖' : 'Click a demo account to auto-fill:'}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setUsernameInput('sochea');
                          setPinInput('1234');
                        }}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white hover:bg-emerald-100 rounded-xl border-2 border-emerald-500 font-black text-xs text-emerald-900 shadow-[1px_1px_0px_#2D6A4F] cursor-pointer"
                      >
                        <User className="w-3.5 h-3.5 text-emerald-700" />
                        <span>sochea</span>
                        <span className="font-mono text-[10px] bg-emerald-100 px-1 py-0.5 rounded text-emerald-800">PIN: 1234</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setUsernameInput('parent');
                          setPinInput('9999');
                        }}
                        className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white hover:bg-amber-100 rounded-xl border-2 border-amber-500 font-black text-xs text-amber-900 shadow-[1px_1px_0px_#78350F] cursor-pointer"
                      >
                        <Shield className="w-3.5 h-3.5 text-amber-700" />
                        <span>parent</span>
                        <span className="font-mono text-[10px] bg-amber-100 px-1 py-0.5 rounded text-amber-800">PIN: 9999</span>
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-black text-gray-700 uppercase tracking-wider mb-1">
                      {isKhmer ? 'ឈ្មោះអ្នកប្រើ (Username)' : 'Username'}
                    </label>
                    <input
                      type="text"
                      autoFocus
                      value={usernameInput}
                      onChange={(e) => setUsernameInput(e.target.value)}
                      placeholder="sochea / parent"
                      className="w-full px-3.5 py-2.5 bg-gray-50 border-2 border-[#1B4332] rounded-xl text-sm font-bold text-gray-900 focus:outline-none focus:bg-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-black text-gray-700 uppercase tracking-wider mb-1">
                      {isKhmer ? 'លេខកូដសម្ងាត់ (PIN ៤ ខ្ទង់)' : 'PIN Code (4 digits)'}
                    </label>
                    <input
                      type="password"
                      value={pinInput}
                      onChange={(e) => setPinInput(e.target.value)}
                      placeholder="1234 / 9999"
                      className="w-full px-3.5 py-2.5 bg-gray-50 border-2 border-[#1B4332] rounded-xl text-sm font-bold text-gray-900 focus:outline-none focus:bg-white"
                    />
                  </div>

                  <div className="flex gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => {
                        setError(null);
                        setMode('select');
                      }}
                      className="flex-1 py-2.5 px-4 rounded-xl border-2 border-gray-300 hover:bg-gray-100 text-gray-700 font-bold text-xs sm:text-sm cursor-pointer"
                    >
                      {isKhmer ? 'ត្រឡប់ក្រោយ' : 'Back'}
                    </button>
                    <button
                      type="submit"
                      className="flex-[2] py-2.5 px-4 rounded-xl bg-[#2D6A4F] hover:bg-[#1B4332] text-white font-black text-xs sm:text-sm border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] cursor-pointer flex items-center justify-center gap-1.5"
                    >
                      <LogIn className="w-4 h-4" />
                      <span>{isKhmer ? 'ចូលគណនី' : 'Log In'}</span>
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}

          {/* MODE 3: CREATE NEW ACCOUNT */}
          {mode === 'create' && (
            <form onSubmit={handleCreateAccount} className="space-y-3.5">
              {/* Role Selector */}
              <div>
                <label className="block text-xs font-black text-gray-700 uppercase tracking-wider mb-1">
                  {isKhmer ? 'តួនាទីគណនី' : 'Account Role'}
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setNewRole('student')}
                    className={`py-2 px-3 rounded-xl border-2 font-black text-xs sm:text-sm flex items-center justify-center gap-1.5 cursor-pointer transition-all ${
                      newRole === 'student'
                        ? 'bg-emerald-100 border-[#2D6A4F] text-[#1B4332] shadow-[2px_2px_0px_#2D6A4F]'
                        : 'bg-white border-gray-300 text-gray-600'
                    }`}
                  >
                    <User className="w-4 h-4" />
                    <span>{isKhmer ? 'សិស្ស' : 'Student'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setNewRole('parent')}
                    className={`py-2 px-3 rounded-xl border-2 font-black text-xs sm:text-sm flex items-center justify-center gap-1.5 cursor-pointer transition-all ${
                      newRole === 'parent'
                        ? 'bg-amber-100 border-amber-600 text-amber-900 shadow-[2px_2px_0px_#B45309]'
                        : 'bg-white border-gray-300 text-gray-600'
                    }`}
                  >
                    <Shield className="w-4 h-4" />
                    <span>{isKhmer ? 'អាណាព្យាបាល' : 'Parent'}</span>
                  </button>
                </div>
              </div>

              {/* Display Name */}
              <div>
                <label className="block text-xs font-black text-gray-700 uppercase tracking-wider mb-1">
                  {isKhmer ? 'ឈ្មោះបង្ហាញ' : 'Display Name'}
                </label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder={newRole === 'student' ? 'វុឌ្ឍី (Vuthy)' : 'អ្នកម្តាយ (Mom)'}
                  className="w-full px-3.5 py-2.5 bg-gray-50 border-2 border-[#1B4332] rounded-xl text-sm font-bold text-gray-900 focus:outline-none focus:bg-white"
                />
              </div>

              {/* Username */}
              <div>
                <label className="block text-xs font-black text-gray-700 uppercase tracking-wider mb-1">
                  {isKhmer ? 'ឈ្មោះអ្នកប្រើ (Login Username)' : 'Username'}
                </label>
                <input
                  type="text"
                  required
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  placeholder="vuthy123"
                  className="w-full px-3.5 py-2.5 bg-gray-50 border-2 border-[#1B4332] rounded-xl text-sm font-bold text-gray-900 focus:outline-none focus:bg-white"
                />
              </div>

              {/* Grade (if student) */}
              {newRole === 'student' && (
                <div>
                  <label className="block text-xs font-black text-gray-700 uppercase tracking-wider mb-1">
                    {isKhmer ? 'កម្រិតថ្នាក់' : 'Grade Level'}
                  </label>
                  <select
                    value={newGrade}
                    onChange={(e) => setNewGrade(Number(e.target.value))}
                    className="w-full px-3.5 py-2.5 bg-gray-50 border-2 border-[#1B4332] rounded-xl text-sm font-bold text-gray-900 focus:outline-none focus:bg-white"
                  >
                    <option value={1}>{isKhmer ? 'ថ្នាក់ទី ១' : 'Grade 1'}</option>
                    <option value={2}>{isKhmer ? 'ថ្នាក់ទី ២' : 'Grade 2'}</option>
                    <option value={3}>{isKhmer ? 'ថ្នាក់ទី ៣' : 'Grade 3'}</option>
                    <option value={4}>{isKhmer ? 'ថ្នាក់ទី ៤' : 'Grade 4'}</option>
                    <option value={5}>{isKhmer ? 'ថ្នាក់ទី ៥' : 'Grade 5'}</option>
                    <option value={6}>{isKhmer ? 'ថ្នាក់ទី ៦' : 'Grade 6'}</option>
                  </select>
                </div>
              )}

              {/* Optional PIN */}
              <div>
                <label className="block text-xs font-black text-gray-700 uppercase tracking-wider mb-1">
                  {isKhmer ? 'លេខកូដសម្ងាត់ PIN (៤ ខ្ទង់ - ស្រេចចិត្ត)' : 'PIN Code (4 digits - optional)'}
                </label>
                <input
                  type="password"
                  maxLength={6}
                  value={newPin}
                  onChange={(e) => setNewPin(e.target.value)}
                  placeholder="1234"
                  className="w-full px-3.5 py-2.5 bg-gray-50 border-2 border-[#1B4332] rounded-xl text-sm font-bold text-gray-900 focus:outline-none focus:bg-white"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setError(null);
                    setMode('select');
                  }}
                  className="flex-1 py-2.5 px-4 rounded-xl border-2 border-gray-300 hover:bg-gray-100 text-gray-700 font-bold text-xs sm:text-sm cursor-pointer"
                >
                  {isKhmer ? 'ត្រឡប់ក្រោយ' : 'Back'}
                </button>
                <button
                  type="submit"
                  className="flex-[2] py-2.5 px-4 rounded-xl bg-[#40916C] hover:bg-[#2D6A4F] text-white font-black text-xs sm:text-sm border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>{isKhmer ? 'បង្កើតគណនី' : 'Save & Log In'}</span>
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
