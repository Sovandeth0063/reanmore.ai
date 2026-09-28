import React from 'react';
import { Grade, Language } from '../types';
import { BookOpen, GraduationCap, Sparkles, Calculator, Atom } from 'lucide-react';

interface GradeSubjectSelectorProps {
  currentGrade: Grade;
  language?: Language;
  onSelectGrade: (grade: Grade) => void;
}

export const GradeSubjectSelector: React.FC<GradeSubjectSelectorProps> = ({
  currentGrade,
  language = 'km',
  onSelectGrade
}) => {
  const isKhmer = language === 'km';
  const grades: Grade[] = [1, 2, 3, 4, 5, 6];

  const subjects = [
    {
      id: 'math',
      nameKhmer: 'គណិតវិទ្យា',
      nameEng: 'Mathematics',
      icon: Calculator,
      bgColor: 'bg-[#A7CDB4]',
    },
    {
      id: 'science',
      nameKhmer: 'វិទ្យាសាស្ត្រ',
      nameEng: 'Science',
      icon: Atom,
      bgColor: 'bg-[#2D6A4F]',
    }
  ];

  return (
    <div className="w-full bg-white rounded-3xl border-3 border-[#1B4332] shadow-[4px_4px_0px_#1B4332] p-5 sm:p-7 space-y-6">
      {/* Grade Selector (3x2 Grid of Chips) */}
      <div className="space-y-3.5">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <label className="text-sm sm:text-base font-black text-[#1B4332] font-heading flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-[#1B4332] shrink-0" />
            <span>{isKhmer ? 'ជ្រើសរើសថ្នាក់សិក្សា' : 'Select Grade'}</span>
          </label>
          <span className="text-[11px] sm:text-xs font-black text-white bg-[#40916C] px-2.5 sm:px-3 py-1 rounded-full border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] flex items-center gap-1">
            <GraduationCap className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
            {isKhmer ? `ថ្នាក់ទី ${currentGrade}` : `Grade ${currentGrade}`}
          </span>
        </div>

        {/* 3x2 Grid */}
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2.5 sm:gap-3.5">
          {grades.map((g) => {
            const isSelected = currentGrade === g;
            return (
              <button
                key={g}
                type="button"
                onClick={() => onSelectGrade(g)}
                aria-pressed={isSelected}
                className={`py-2.5 sm:py-3.5 px-2 sm:px-3 rounded-2xl font-black text-sm sm:text-base border-3 transition-all flex items-center justify-center cursor-pointer min-w-0 ${
                  isSelected
                    ? 'bg-[#2D6A4F] border-[#1B4332] text-white shadow-[2.5px_2.5px_0px_#1B4332] -translate-y-0.5'
                    : 'bg-[#E8F5E9] border-[#1B4332] text-[#1B4332] hover:bg-[#40916C] shadow-[2px_2px_0px_#1B4332]'
                }`}
              >
                <span className="truncate">{isKhmer ? `ថ្នាក់ទី ${g}` : `Grade ${g}`}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Non-selectable Display-Only Subject Cards */}
      <div className="space-y-3 pt-4 border-t-2 border-[#1B4332]/20">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <label className="text-sm sm:text-base font-black text-[#1B4332] font-heading flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[#1B4332] shrink-0" />
            <span>{isKhmer ? 'មុខវិជ្ជាសិក្សាដែលគាំទ្រ' : 'Supported Subjects'}</span>
          </label>
          <span className="text-[10px] sm:text-xs font-black text-[#1B4332] bg-[#A7CDB4] px-2.5 py-1 rounded-full border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-[#1B4332]" />
            {isKhmer ? 'ស្វ័យប្រវត្តិដោយ AI' : 'Auto-detected by AI'}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {subjects.map((sub) => {
            const Icon = sub.icon;
            return (
              <div
                key={sub.id}
                className={`p-3.5 sm:p-4 rounded-2xl border-3 border-[#1B4332] shadow-[2px_2px_0px_#1B4332] ${sub.bgColor} flex items-center select-none cursor-default`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="p-2 bg-white rounded-xl border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] shrink-0">
                    <Icon className="w-5 h-5 text-[#1B4332]" />
                  </div>
                  <span className="font-black text-sm sm:text-base text-[#1B4332] truncate">
                    {isKhmer ? sub.nameKhmer : sub.nameEng}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};


