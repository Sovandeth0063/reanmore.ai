import React, { useState, useEffect, useRef } from 'react';
import { UserProfile, Grade, Language, UserAccount, UserRole } from '../types';
import { GradeSubjectSelector } from './GradeSubjectSelector';
import { LanguageSwitcher } from './LanguageSwitcher';
import {
  Sparkles,
  Globe,
  GraduationCap,
  Save,
  CheckCircle2,
  Edit3,
  User,
  Camera,
  X,
  Shield,
  KeyRound,
  LogOut,
  LogIn,
  Users,
} from 'lucide-react';
import { getDisplayName } from '../utils/language';
import { ParentReport } from './ParentReport';

interface ProfileViewProps {
  profile: UserProfile;
  currentUser?: UserAccount | null;
  onUpdateProfile: (updated: Partial<UserProfile>) => void;
  onOpenAuth?: (requiredRole?: UserRole) => void;
  onLogout?: () => void;
}

export const ProfileView: React.FC<ProfileViewProps> = ({
  profile,
  currentUser,
  onUpdateProfile,
  onOpenAuth,
  onLogout,
}) => {
  const [draftName, setDraftName] = useState(profile.name);
  const [draftGrade, setDraftGrade] = useState<Grade>(profile.grade);
  const [draftLanguage, setDraftLanguage] = useState<Language>(profile.language);
  const [draftAvatarUrl, setDraftAvatarUrl] = useState<string | undefined>(profile.avatarUrl);
  const [isSaved, setIsSaved] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setDraftName(profile.name);
    setDraftGrade(profile.grade);
    setDraftLanguage(profile.language);
    setDraftAvatarUrl(profile.avatarUrl);
  }, [profile]);

  const isKhmer = draftLanguage === 'km';
  const role = currentUser?.role || profile.role || 'student';
  const isParent = role === 'parent';

  const hasChanges =
    draftName !== profile.name ||
    draftGrade !== profile.grade ||
    draftLanguage !== profile.language ||
    draftAvatarUrl !== profile.avatarUrl;

  const handleSave = () => {
    onUpdateProfile({
      name: draftName,
      grade: draftGrade,
      language: draftLanguage,
      avatarUrl: draftAvatarUrl,
    });
    setIsSaved(true);
    setTimeout(() => {
      setIsSaved(false);
    }, 3000);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) return;
    if (file.size > 2 * 1024 * 1024) return; // 2MB max

    const reader = new FileReader();
    reader.onloadend = () => {
      setDraftAvatarUrl(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveAvatar = () => {
    setDraftAvatarUrl(undefined);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-5 sm:space-y-7 animate-fadeIn w-full pb-12">
      {/* Profile Hero Card */}
      <div className="bg-[#40916C] rounded-2xl sm:rounded-3xl border-3 border-[#1B4332] p-4 sm:p-6 shadow-[4px_4px_0px_#1B4332] sm:shadow-[6px_6px_0px_#1B4332] flex flex-col sm:flex-row items-center gap-4 sm:gap-6 text-center sm:text-left relative">
        <div className="absolute -top-4 -right-4 w-12 sm:w-16 h-12 sm:h-16 bg-[#2D6A4F] rounded-full border-2 border-[#1B4332] opacity-30" />
        <div className="absolute -bottom-4 -left-4 w-12 sm:w-16 h-12 sm:h-16 bg-[#A7CDB4] rounded-full border-2 border-[#1B4332] opacity-30" />

        {/* Avatar Upload Area */}
        <div className="shrink-0 relative group">
          <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-3xl border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] bg-white overflow-hidden flex items-center justify-center relative">
            {draftAvatarUrl ? (
              <img
                src={draftAvatarUrl}
                alt="Profile"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-[#E8F5E9] flex items-center justify-center">
                {isParent ? (
                  <span className="text-4xl">👩‍👧</span>
                ) : (
                  <User className="w-12 h-12 sm:w-14 sm:h-14 text-[#40916C]" strokeWidth={2} />
                )}
              </div>
            )}

            {/* Hover overlay */}
            <button
              type="button"
              onClick={triggerFileInput}
              className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center text-white cursor-pointer"
            >
              <Camera className="w-6 h-6 mb-1" />
              <span className="text-[10px] font-black uppercase tracking-wider">
                {isKhmer ? 'ប្តូររូប' : 'Change'}
              </span>
            </button>
          </div>

          {draftAvatarUrl && (
            <button
              type="button"
              onClick={handleRemoveAvatar}
              className="absolute -top-2 -right-2 w-7 h-7 bg-red-500 hover:bg-red-600 text-white rounded-full border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] flex items-center justify-center cursor-pointer transition-all"
              title={isKhmer ? 'លុបរូបភាព' : 'Remove image'}
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>

        <div className="space-y-2 sm:space-y-3 flex-1 relative z-10 w-full min-w-0">
          <div className="inline-flex items-center gap-1.5 px-3 sm:px-3.5 py-1 rounded-full bg-[#1B4332] text-white text-[11px] sm:text-xs font-black border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332]">
            {isParent ? (
              <>
                <Shield className="w-3.5 h-3.5 text-amber-300 shrink-0" />
                <span className="truncate">{isKhmer ? 'គណនីអាណាព្យាបាល' : 'Parent Account'}</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-white shrink-0" />
                <span className="truncate">{isKhmer ? 'សិស្សរៀនជាមួយ ReanMore' : 'ReanMore Student'}</span>
              </>
            )}
          </div>

          <h2 className="text-xl sm:text-3xl font-black text-[#1B4332] font-heading drop-shadow-[1px_1px_0px_white] break-words">
            {getDisplayName(profile.name, isKhmer)}
          </h2>

          <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 pt-1">
            {!isParent && (
              <span className="px-3 py-1 sm:px-3.5 sm:py-1.5 bg-white text-[#1B4332] rounded-full border-2 border-[#1B4332] text-xs font-black flex items-center gap-1.5 shadow-[2px_2px_0px_#1B4332]">
                <GraduationCap className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-[#1B4332]" />
                {isKhmer ? `ថ្នាក់ទី ${profile.grade}` : `Grade ${profile.grade}`}
              </span>
            )}
            <span className="px-3 py-1 sm:px-3.5 sm:py-1.5 bg-[#A7CDB4] text-[#1B4332] rounded-full border-2 border-[#1B4332] text-xs font-black flex items-center gap-1.5 shadow-[2px_2px_0px_#1B4332]">
              <Sparkles className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
              {isKhmer ? 'រៀនគ្រប់មុខវិជ្ជា' : 'All Subjects AI'}
            </span>
          </div>
        </div>
      </div>

      {/* Account & Authentication Card */}
      <div className="bg-white rounded-2xl sm:rounded-3xl border-3 border-[#1B4332] shadow-[4px_4px_0px_#1B4332] p-4 sm:p-6 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 border-2 border-[#1B4332] flex items-center justify-center text-lg">
              {isParent ? '👩‍👧' : '👦'}
            </div>
            <div>
              <h3 className="font-black text-base sm:text-lg text-[#1B4332] font-heading leading-tight">
                {isKhmer ? 'ព័ត៌មានគណនី និងការចូលប្រើ' : 'Account & Authentication'}
              </h3>
              <p className="text-xs font-bold text-gray-500">
                {currentUser
                  ? isKhmer
                    ? `ចូលជា៖ @${currentUser.username} (${isParent ? 'អាណាព្យាបាល' : 'សិស្ស'})`
                    : `Logged in as: @${currentUser.username} (${isParent ? 'Parent' : 'Student'})`
                  : isKhmer
                  ? 'មិនទាន់បានចូលគណនី'
                  : 'Not logged in'}
              </p>
            </div>
          </div>

          {/* Quick Switch / Log In / Log Out Buttons */}
          <div className="flex items-center gap-2">
            {currentUser ? (
              <>
                <button
                  type="button"
                  onClick={() => onOpenAuth?.()}
                  className="flex items-center gap-1.5 py-2 px-3 sm:px-4 rounded-xl bg-[#2D6A4F] hover:bg-[#1B4332] text-white border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] font-black text-xs sm:text-sm cursor-pointer transition-all"
                >
                  <Users className="w-4 h-4" />
                  <span>{isKhmer ? 'ប្តូរគណនី' : 'Switch Account'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => onLogout?.()}
                  className="flex items-center gap-1.5 py-2 px-3 sm:px-4 rounded-xl bg-red-100 hover:bg-red-200 text-red-800 border-2 border-red-800 shadow-[2px_2px_0px_#991B1B] font-black text-xs sm:text-sm cursor-pointer transition-all"
                >
                  <LogOut className="w-4 h-4" />
                  <span>{isKhmer ? 'ចាកចេញ' : 'Log Out'}</span>
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => onOpenAuth?.()}
                className="flex items-center gap-1.5 py-2 px-4 rounded-xl bg-amber-400 hover:bg-amber-300 text-[#1B4332] border-2 border-amber-600 shadow-[2px_2px_0px_#78350F] font-black text-xs sm:text-sm cursor-pointer transition-all"
              >
                <LogIn className="w-4 h-4 text-[#1B4332]" />
                <span>{isKhmer ? 'ចូលគណនី' : 'Log In'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Security / Hardcoded Demo PIN Info */}
        <div className="p-3 bg-[#E8F5E9] border-2 border-[#A7CDB4] rounded-2xl space-y-2 text-xs font-bold text-[#1B4332]">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <KeyRound className="w-4 h-4 text-[#2D6A4F] shrink-0" />
              <span className="font-black">
                {isKhmer ? 'លេខកូដ PIN គំរូក្នុងប្រព័ន្ធ (Demo PINs)៖' : 'System Demo PIN Codes:'}
              </span>
            </div>
            <span className="text-[11px] font-bold text-[#2D6A4F] bg-white px-2 py-0.5 rounded-lg border border-[#A7CDB4]">
              {isKhmer ? 'កំណត់ស្រេចសម្រាប់សាកល្បង' : 'Hardcoded for demo'}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
            <div className="flex items-center justify-between p-2 bg-white rounded-xl border border-[#A7CDB4]">
              <span className="font-bold text-[#1B4332]">👦 សិស្ស (sochea)</span>
              <span className="font-mono font-black text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded border border-emerald-300">
                PIN: 1234
              </span>
            </div>
            <div className="flex items-center justify-between p-2 bg-white rounded-xl border border-[#A7CDB4]">
              <span className="font-bold text-[#1B4332]">👩‍👧 អាណាព្យាបាល (parent)</span>
              <span className="font-mono font-black text-amber-800 bg-amber-100 px-2 py-0.5 rounded border border-amber-300">
                PIN: 9999
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Save Changes Button */}
      <div className="bg-white p-4 sm:p-5 rounded-2xl sm:rounded-3xl border-3 border-[#1B4332] shadow-[4px_4px_0px_#1B4332] sm:shadow-[5px_5px_0px_#1B4332] flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="space-y-1 text-center sm:text-left">
          <h4 className="font-black text-base sm:text-lg text-[#1B4332] font-heading flex items-center justify-center sm:justify-start gap-2">
            <Save className="w-5 h-5 text-[#1B4332]" />
            <span>{isKhmer ? 'រក្សាទុកការកំណត់' : 'Save Profile Settings'}</span>
          </h4>
          <p className="text-xs font-bold text-[#1B4332]/70">
            {hasChanges
              ? isKhmer
                ? 'អ្នកមានការផ្លាស់ប្តូរដែលមិនទាន់បានរក្សាទុក!'
                : 'You have unsaved changes!'
              : isKhmer
              ? 'ការកំណត់ទាំងអស់ទាន់សម័យ'
              : 'All settings are up to date'}
          </p>
        </div>

        <button
          type="button"
          onClick={handleSave}
          className={`w-full sm:w-auto px-6 py-3 rounded-xl sm:rounded-2xl font-black text-sm sm:text-base border-3 border-[#1B4332] transition-all flex items-center justify-center gap-2.5 cursor-pointer ${
            isSaved
              ? 'bg-[#2D6A4F] text-white shadow-[3px_3px_0px_#1B4332]'
              : hasChanges
              ? 'bg-[#2D6A4F] text-white shadow-[4px_4px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332]'
              : 'bg-[#E8F5E9] text-[#1B4332] shadow-[3px_3px_0px_#1B4332] hover:opacity-95'
          }`}
        >
          {isSaved ? (
            <>
              <CheckCircle2 className="w-5 h-5" />
              <span>{isKhmer ? 'បានរក្សាទុក!' : 'Saved!'}</span>
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              <span>{isKhmer ? 'រក្សាទុក' : 'Save Changes'}</span>
            </>
          )}
        </button>
      </div>

      {/* Profile Form Field */}
      <div className="bg-white rounded-2xl sm:rounded-3xl border-3 border-[#1B4332] shadow-[4px_4px_0px_#1B4332] p-4 sm:p-6 space-y-2">
        <label className="font-black text-sm text-[#1B4332] flex items-center gap-2">
          <Edit3 className="w-4 h-4 text-[#1B4332]" />
          <span>{isKhmer ? 'ឈ្មោះបង្ហាញ' : 'Display Name'}</span>
        </label>
        <input
          type="text"
          value={draftName}
          onChange={(e) => setDraftName(e.target.value)}
          placeholder={isKhmer ? 'បញ្ចូលឈ្មោះរបស់អ្នក...' : 'Enter your name...'}
          className="w-full px-4 py-3 bg-[#E8F5E9] border-3 border-[#1B4332] rounded-2xl font-black text-sm sm:text-base text-[#1B4332] focus:outline-none focus:ring-4 focus:ring-[#A7CDB4]/40 shadow-[2px_2px_0px_#1B4332]"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        {/* Language Switcher Card */}
        <div className="bg-white rounded-2xl sm:rounded-3xl border-3 border-[#1B4332] shadow-[4px_4px_0px_#1B4332] p-4 sm:p-6 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h3 className="font-black text-base sm:text-lg text-[#1B4332] flex items-center gap-2 font-heading">
              <Globe className="w-5 h-5 text-[#1B4332] shrink-0" />
              <span>{isKhmer ? 'ភាសាកម្មវិធី' : 'Language'}</span>
            </h3>
            <LanguageSwitcher
              language={draftLanguage}
              onSelectLanguage={(lang: Language) => setDraftLanguage(lang)}
            />
          </div>
          <p className="text-xs font-bold text-[#1B4332]/80">
            {isKhmer
              ? 'ជ្រើសរើសភាសាដែលអ្នកចង់ប្រើប្រាស់នៅក្នុងកម្មវិធី'
              : 'Select your preferred application display language'}
          </p>
        </div>

        {/* Grade Info Card (read-only display) */}
        <div className="bg-white rounded-2xl sm:rounded-3xl border-3 border-[#1B4332] shadow-[4px_4px_0px_#1B4332] p-4 sm:p-6 space-y-3">
          <div className="flex items-center gap-2">
            <GraduationCap className="w-5 h-5 text-[#2D6A4F] shrink-0" />
            <h3 className="font-black text-base sm:text-lg text-[#1B4332] font-heading">
              {isKhmer ? 'ថ្នាក់រៀន' : 'Grade Level'}
            </h3>
          </div>
          <span className="inline-block px-3 py-1.5 bg-[#A7CDB4] text-[#1B4332] rounded-xl text-xs font-black border-2 border-[#1B4332] shadow-[2px_2px_0px_#1B4332]">
            {isKhmer ? `ថ្នាក់ទី ${draftGrade}` : `Grade ${draftGrade}`}
          </span>
        </div>
      </div>

      {/* Grade Selector */}
      <GradeSubjectSelector
        currentGrade={draftGrade}
        language={draftLanguage}
        onSelectGrade={(grade: Grade) => setDraftGrade(grade)}
      />

      {/* Parent Weekly Report */}
      <ParentReport profile={profile} />
    </div>
  );
};
