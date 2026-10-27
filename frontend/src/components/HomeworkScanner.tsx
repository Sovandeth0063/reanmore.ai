import React, { useState, useRef, useEffect } from 'react';
import { Camera, Upload, RefreshCw, CheckCircle, ArrowLeft, Sparkles, BookOpen, AlertCircle, Calculator, FlaskConical, ListChecks } from 'lucide-react';
import { TunsayAvatar } from './TunsayAvatar';
import { HomeworkProblem, Language, Grade } from '../types';
import { MOCK_PROBLEMS } from '../data/mockProblems';
import { processHomeworkImage, cleanOcrText } from '../services/ocrService';

interface HomeworkScannerProps {
  language?: Language;
  grade?: Grade;
  onHomeworkConfirmed: (problems: HomeworkProblem[], initialIndex?: number, imageUri?: string) => void;
  onCancel: () => void;
}

export const HomeworkScanner: React.FC<HomeworkScannerProps> = ({
  language = 'km',
  grade = 2,
  onHomeworkConfirmed,
  onCancel
}) => {
  const isKhmer = language === 'km';
  const effectiveGrade = Math.min(Math.max(grade || 2, 1), 3);
  const [stage, setStage] = useState<'capture' | 'preview' | 'analyzing' | 'confirm'>('capture');
  const [imageUri, setImageUri] = useState<string>('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [detectedProblems, setDetectedProblems] = useState<HomeworkProblem[]>([]);
  const [selectedProblem, setSelectedProblem] = useState<HomeworkProblem>(MOCK_PROBLEMS[0]);
  const [selectedProblemIds, setSelectedProblemIds] = useState<Set<string>>(new Set());
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const objectUrlRef = useRef<string | null>(null);

  useEffect(() => {
    return () => {
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCancel();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onCancel]);

  const handleSelectSubject = (subject: 'math' | 'science') => {
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
    setUploadedFile(null);

    // Route to curriculum exercises for this subject (Grade 1-3)
    const chosenProblems = MOCK_PROBLEMS.filter(p => p.subject === subject);
    const mainProblem = chosenProblems[0] || MOCK_PROBLEMS[0];

    setDetectedProblems(chosenProblems);
    setSelectedProblem(mainProblem);
    setSelectedProblemIds(new Set(chosenProblems.map(p => p.id)));
    setAnalysisError(null);
    setImageUri(mainProblem?.imageUri || '');
    // Directly open the exercise selector so the user can choose which exercise to proceed with!
    setStage('confirm');
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
      }
      const url = URL.createObjectURL(file);
      objectUrlRef.current = url;
      setUploadedFile(file);
      setImageUri(url);
      setAnalysisError(null);
      setStage('preview');
    }
  };

  const handleConfirmPhoto = async () => {
    setStage('analyzing');
    setAnalysisError(null);

    if (uploadedFile) {
      try {
        const result = await processHomeworkImage(uploadedFile);
        if (result.success && result.problems && result.problems.length > 0) {
          const cleanedProblems = result.problems.map((p, idx) => ({
            ...p,
            titleEng: cleanOcrText(p.titleEng || `Exercise ${idx + 1}`),
            problemStatementEng: cleanOcrText(p.problemStatementEng || p.problemStatementKhmer || ''),
            problemStatementKhmer: p.problemStatementKhmer ? cleanOcrText(p.problemStatementKhmer) : cleanOcrText(p.problemStatementEng || ''),
          }));

          setDetectedProblems(cleanedProblems);
          setSelectedProblem(cleanedProblems[0]);
          setSelectedProblemIds(new Set(cleanedProblems.map(p => p.id)));
          setStage('confirm');
          return;
        } else if (result.error) {
          setAnalysisError(result.error);
        }
      } catch (err: any) {
        console.error('Failed to process image via OCR:', err);
        setAnalysisError(err?.message || 'Error communicating with OCR service');
      }
    }

    // Fallback if sample was chosen or if processing returned empty
    setSelectedProblemIds(new Set(detectedProblems.map(p => p.id)));
    setStage('confirm');
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={isKhmer ? 'ស្កេនលំហាត់' : 'Homework Scanner'}
      className="w-full max-w-xl sm:max-w-2xl mx-auto bg-white rounded-2xl sm:rounded-3xl border-2 sm:border-3 border-[#1B4332] shadow-[4px_4px_0px_#1B4332] sm:shadow-[6px_6px_0px_#1B4332] overflow-hidden animate-fadeIn text-[#1B4332] max-h-[90dvh] flex flex-col"
    >
      {/* Header */}
      <div className="p-3 sm:p-4 bg-[#1B4332] border-b-2 sm:border-b-3 border-[#1B4332] flex items-center justify-between text-white shrink-0">
        <button
          type="button"
          onClick={onCancel}
          className="px-2.5 py-1 sm:px-3 sm:py-1.5 bg-[#40916C] text-white rounded-lg sm:rounded-xl border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] flex items-center gap-1 text-xs font-black cursor-pointer hover:-translate-y-0.5 transition-transform"
        >
          <ArrowLeft className="w-3.5 h-3.5 sm:w-4 sm:h-4 stroke-[3]" /> {isKhmer ? 'ត្រឡប់' : 'Back'}
        </button>
        <div className="flex items-center gap-1.5 font-black text-xs sm:text-sm text-white">
          <Camera className="w-4 h-4 stroke-[2.5]" /> {isKhmer ? 'ស្កេនលំហាត់' : 'Homework Scanner'}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto no-scrollbar">
        {/* Stage 1: Capture / Select Sample */}
        {stage === 'capture' && (
          <div className="p-3.5 sm:p-6 space-y-3.5 sm:space-y-5 text-center">
            {/* Camera Frame */}
            <div className="relative w-full aspect-4/3 max-h-56 bg-[#E8F5E9] rounded-2xl border-3 border-dashed border-[#1B4332] flex flex-col items-center justify-center p-4 text-center group hover:bg-[#40916C]/30 transition-colors">
              {/* Viewfinder Corners */}
              <div className="absolute top-3 left-3 w-5 h-5 border-t-4 border-l-4 border-[#1B4332] rounded-tl-lg" />
              <div className="absolute top-3 right-3 w-5 h-5 border-t-4 border-r-4 border-[#1B4332] rounded-tr-lg" />
              <div className="absolute bottom-3 left-3 w-5 h-5 border-b-4 border-l-4 border-[#1B4332] rounded-bl-lg" />
              <div className="absolute bottom-3 right-3 w-5 h-5 border-b-4 border-r-4 border-[#1B4332] rounded-br-lg" />

              <TunsayAvatar size="sm" state="idle" showBadge={false} className="mb-1" />
              <p className="text-sm sm:text-base font-black text-[#1B4332] font-heading flex items-center justify-center gap-1.5">
                <Camera className="w-4 h-4 sm:w-5 sm:h-5 text-[#1B4332]" />
                {isKhmer ? 'ថតរូបលំហាត់របស់អ្នក' : 'Scan your homework'}
              </p>
              <p className="text-xs font-bold text-[#1B4332]/80 mt-0.5 max-w-xs">
                {isKhmer 
                  ? 'ដាក់ក្រដាសលំហាត់របស់អ្នកឱ្យចំកណ្តាលស៊ុម' 
                  : 'Fit your homework page inside the frame'}
              </p>

              <input
                type="file"
                ref={fileInputRef}
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
              />

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="mt-3 px-5 py-2.5 bg-[#2D6A4F] hover:bg-[#40916C] text-white hover:text-white font-black rounded-2xl border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] transition-all flex items-center gap-2 cursor-pointer text-xs sm:text-sm"
              >
                <Upload className="w-4 h-4 stroke-[2.5]" />
                {isKhmer ? 'ជ្រើសរើសរូបថត' : 'Upload Photo'}
              </button>
            </div>

            {/* Choose Subject: Math or Science */}
            <div className="space-y-3 pt-2 text-left">
              <p className="text-xs font-black text-[#1B4332] uppercase tracking-wider flex items-center gap-1.5">
                <BookOpen className="w-4 h-4 text-[#2D6A4F]" />
                <span>
                  {isKhmer 
                    ? 'ឬ ជ្រើសរើសមុខវិជ្ជាដើម្បីអនុវត្ត៖' 
                    : 'Or choose a subject to practice:'}
                </span>
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Math Card */}
                <button
                  type="button"
                  onClick={() => handleSelectSubject('math')}
                  className="p-4 rounded-2xl border-3 border-[#1B4332] bg-[#E8F5E9] hover:bg-[#40916C] hover:text-white text-left transition-all shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] flex flex-col justify-between cursor-pointer group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="w-10 h-10 rounded-xl bg-[#2D6A4F] text-white group-hover:bg-white group-hover:text-[#1B4332] border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] flex items-center justify-center font-black transition-colors">
                      <Calculator className="w-5 h-5 stroke-[2.5]" />
                    </div>
                    <span className="text-[10px] font-black text-[#1B4332] bg-white group-hover:bg-[#1B4332] group-hover:text-white px-2.5 py-0.5 rounded-full border-2 border-[#1B4332] transition-colors">
                      {isKhmer ? `ថ្នាក់ទី ${effectiveGrade} • គណិត` : `Grade ${effectiveGrade} • Math`}
                    </span>
                  </div>

                  <div className="mt-3">
                    <h4 className="font-black text-sm sm:text-base text-[#1B4332] group-hover:text-white transition-colors">
                      {isKhmer ? 'គណិតវិទ្យា (Math)' : 'Mathematics (គណិតវិទ្យា)'}
                    </h4>
                    <p className="text-xs font-bold text-[#1B4332]/75 group-hover:text-white/90 mt-1 leading-snug transition-colors">
                      {isKhmer 
                        ? 'លំហាត់ប្រមាណវិធី វិធីគុណ វិធីចែក និងចំណោទ' 
                        : 'Arithmetic, multiplication, division & word problems'}
                    </p>
                  </div>

                  <div className="flex items-center justify-between mt-3 pt-2 border-t-2 border-[#1B4332]/20 group-hover:border-white/30 text-xs font-black text-[#2D6A4F] group-hover:text-white transition-colors">
                    <span>{isKhmer ? 'ជ្រើសរើស គណិត' : 'Select Math'}</span>
                    <Sparkles className="w-4 h-4" />
                  </div>
                </button>

                {/* Science Card */}
                <button
                  type="button"
                  onClick={() => handleSelectSubject('science')}
                  className="p-4 rounded-2xl border-3 border-[#1B4332] bg-[#E8F5E9] hover:bg-[#40916C] hover:text-white text-left transition-all shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-[1px_1px_0px_#1B4332] flex flex-col justify-between cursor-pointer group"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="w-10 h-10 rounded-xl bg-[#40916C] text-white group-hover:bg-white group-hover:text-[#1B4332] border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] flex items-center justify-center font-black transition-colors">
                      <FlaskConical className="w-5 h-5 stroke-[2.5]" />
                    </div>
                    <span className="text-[10px] font-black text-[#1B4332] bg-white group-hover:bg-[#1B4332] group-hover:text-white px-2.5 py-0.5 rounded-full border-2 border-[#1B4332] transition-colors">
                      {isKhmer ? `ថ្នាក់ទី ${effectiveGrade} • វិទ្យាសាស្ត្រ` : `Grade ${effectiveGrade} • Science`}
                    </span>
                  </div>

                  <div className="mt-3">
                    <h4 className="font-black text-sm sm:text-base text-[#1B4332] group-hover:text-white transition-colors">
                      {isKhmer ? 'វិទ្យាសាស្ត្រ (Science)' : 'Science (វិទ្យាសាស្ត្រ)'}
                    </h4>
                    <p className="text-xs font-bold text-[#1B4332]/75 group-hover:text-white/90 mt-1 leading-snug transition-colors">
                      {isKhmer 
                        ? 'លំហាត់សត្វ ជីវវិទ្យា រូបវិទ្យា និងធម្មជាតិ' 
                        : 'Animals, biology, states of matter & nature'}
                    </p>
                  </div>

                  <div className="flex items-center justify-between mt-3 pt-2 border-t-2 border-[#1B4332]/20 group-hover:border-white/30 text-xs font-black text-[#2D6A4F] group-hover:text-white transition-colors">
                    <span>{isKhmer ? 'ជ្រើសរើស វិទ្យាសាស្ត្រ' : 'Select Science'}</span>
                    <Sparkles className="w-4 h-4" />
                  </div>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Stage 2: Preview */}
        {stage === 'preview' && (
          <div className="p-4 sm:p-6 space-y-4 text-center flex flex-col">
            <div className="relative rounded-2xl overflow-hidden border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] bg-[#E8F5E9]/50 flex items-center justify-center max-h-[60vh] p-1.5">
              <img
                src={imageUri}
                alt="Homework preview"
                className="w-full h-auto max-h-[58vh] object-contain rounded-xl"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22300%22%3E%3Crect fill=%22%23E8F5E9%22 width=%22400%22 height=%22300%22/%3E%3Ctext fill=%22%231B4332%22 font-family=%22sans-serif%22 font-size=%2218%22 dy=%22.3em%22 text-anchor=%22middle%22 x=%22200%22 y=%22150%22%3EImage unavailable%3C/text%3E%3C/svg%3E';
                }}
              />
            </div>

            <div className="flex gap-3 pt-1">
              <button
                type="button"
                onClick={() => setStage('capture')}
                className="flex-1 py-3 px-4 rounded-2xl border-3 border-[#1B4332] bg-white text-[#1B4332] font-black text-sm flex items-center justify-center gap-1.5 shadow-[3px_3px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer hover:bg-gray-50"
              >
                <RefreshCw className="w-4 h-4 stroke-[2.5]" /> {isKhmer ? 'ថតសារថ្មី' : 'Retake'}
              </button>
              <button
                type="button"
                onClick={handleConfirmPhoto}
                className="flex-1 py-3 px-4 rounded-2xl bg-[#2D6A4F] text-white font-black text-sm border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] flex items-center justify-center gap-1.5 hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer hover:bg-[#40916C]"
              >
                <CheckCircle className="w-4 h-4 stroke-[2.5]" /> {isKhmer ? 'ប្រើរូបនេះ' : 'Use Photo'}
              </button>
            </div>
          </div>
        )}

        {/* Stage 3: Reading / Analyzing */}
        {stage === 'analyzing' && (
          <div className="p-10 text-center space-y-4">
            <TunsayAvatar size="lg" state="thinking" showBadge={false} className="mx-auto" />
            <div className="space-y-1">
              <h3 className="text-lg font-black text-[#1B4332] font-heading flex items-center justify-center gap-2">
                <Sparkles className="w-5 h-5 text-[#2D6A4F] animate-spin" />
                {isKhmer ? 'ReanMore កំពុងអានលំហាត់របស់អ្នក...' : 'ReanMore is reading your homework...'}
              </h3>
              <p className="text-xs text-[#1B4332]/70 font-bold">
                {isKhmer ? 'កំពុងបំបែកសំណួរ និងទិន្នន័យ (VLM Vision)...' : 'Extracting questions and exercises...'}
              </p>
            </div>
            <div className="w-48 h-3 bg-[#E8F5E9] border-2 border-[#1B4332] rounded-full mx-auto overflow-hidden">
              <div className="h-full bg-[#40916C] animate-pulse rounded-full w-3/4" />
            </div>
          </div>
        )}

        {/* Stage 4: Confirm Analyzed Question */}
        {stage === 'confirm' && (
          <div className="p-4 sm:p-6 space-y-3.5 sm:space-y-4 flex flex-col h-full">
            {/* Mascot Banner */}
            <div className="flex items-center gap-3 p-3 bg-[#40916C] rounded-2xl border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] shrink-0">
              <TunsayAvatar size="sm" state="happy" showBadge={false} />
              <div>
                <p className="font-black text-xs sm:text-sm text-white">
                  {isKhmer 
                    ? `ខ្ញុំឃើញ ${detectedProblems.length > 1 ? `${detectedProblems.length} លំហាត់` : 'លំហាត់'} របស់អ្នកហើយ! តោះដោះស្រាយវាទាំងអស់គ្នា!` 
                    : `I found ${detectedProblems.length > 1 ? `${detectedProblems.length} exercises` : 'your exercise'}! Let's solve them together!`}
                </p>
              </div>
            </div>

            {analysisError && (
              <div className="p-3 bg-amber-50 border-2 border-amber-400 rounded-xl text-xs font-bold text-amber-900 flex items-center gap-2 shrink-0">
                <AlertCircle className="w-4 h-4 shrink-0 text-amber-600" />
                <span>{analysisError}</span>
              </div>
            )}

            {/* Exercise Selector with Select All / Deselect All */}
            {detectedProblems.length > 0 && (
              <div className="space-y-2 flex-1 flex flex-col min-h-0">
                <div className="flex items-center justify-between shrink-0">
                  <div className="text-xs font-black text-[#1B4332] uppercase tracking-wider flex items-center gap-1.5">
                    <ListChecks className="w-4 h-4 text-[#1B4332] stroke-[2.5]" />
                    <span>{isKhmer ? 'ជ្រើសរើសលំហាត់ដើម្បីអនុវត្ត៖' : 'Select exercises to practice:'}</span>
                    <span className="text-[11px] font-black text-[#2D6A4F] bg-[#E8F5E9] px-2 py-0.5 rounded-full border border-[#1B4332]/20">
                      {selectedProblemIds.size} / {detectedProblems.length}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      if (selectedProblemIds.size === detectedProblems.length) {
                        setSelectedProblemIds(new Set());
                      } else {
                        setSelectedProblemIds(new Set(detectedProblems.map(p => p.id)));
                      }
                    }}
                    className="px-2.5 py-1 text-xs font-black text-[#1B4332] bg-[#E8F5E9] hover:bg-[#D8F3DC] rounded-xl border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] hover:-translate-y-0.5 active:translate-y-0.5 transition-all cursor-pointer"
                  >
                    {selectedProblemIds.size === detectedProblems.length
                      ? (isKhmer ? 'ដកការជ្រើសរើសទាំងអស់' : 'Deselect All')
                      : (isKhmer ? 'ជ្រើសរើសទាំងអស់' : 'Select All')}
                  </button>
                </div>

                {/* Scrollable list of exercises */}
                <div className="grid grid-cols-1 gap-2.5 max-h-[50vh] sm:max-h-[54vh] overflow-y-auto pr-1 no-scrollbar">
                  {detectedProblems.map((prob, idx) => {
                    const isSelected = selectedProblemIds.has(prob.id);
                    const titleKh = prob.titleKhmer || (isKhmer ? `លំហាត់ ${idx + 1}` : `Exercise ${idx + 1}`);
                    const titleEn = prob.titleEng || `Exercise ${idx + 1}`;
                    const displayTitle = isKhmer ? titleKh : titleEn;

                    const rawPreview = (prob.problemStatementKhmer || prob.problemStatementEng || '').trim();
                    const cleanTitleNorm = displayTitle.toLowerCase().replace(/^[q\d\.\:\s-]+/, '').trim();
                    const cleanPrevNorm = rawPreview.toLowerCase().replace(/^[q\d\.\:\s-]+/, '').trim();
                    const cleanPreview = rawPreview && cleanPrevNorm !== cleanTitleNorm && !cleanTitleNorm.includes(cleanPrevNorm)
                      ? rawPreview.slice(0, 90)
                      : '';

                    return (
                      <button
                        key={prob.id || idx}
                        type="button"
                        onClick={() => {
                          setSelectedProblemIds(prev => {
                            const next = new Set(prev);
                            if (next.has(prob.id)) {
                              next.delete(prob.id);
                            } else {
                              next.add(prob.id);
                            }
                            return next;
                          });
                          setSelectedProblem(prob);
                        }}
                        aria-pressed={isSelected}
                        className={`w-full text-left flex items-center gap-3 px-3.5 py-3 rounded-2xl border-3 cursor-pointer transition-all select-none ${
                          isSelected
                            ? 'bg-[#E8F5E9] text-[#1B4332] border-[#1B4332] shadow-[3px_3px_0px_#1B4332]'
                            : 'bg-white text-[#1B4332]/80 border-[#1B4332]/25 hover:border-[#1B4332]/50 shadow-[1.5px_1.5px_0px_#1B4332]/10 hover:shadow-[2px_2px_0px_#1B4332]/20'
                        }`}
                      >
                        {/* Number & subject icon badge */}
                        <div className={`shrink-0 w-11 h-11 rounded-2xl border-2 flex flex-col items-center justify-center font-black transition-colors ${
                          isSelected
                            ? 'bg-white border-[#1B4332]/30 text-[#1B4332]'
                            : 'bg-[#E8F5E9]/50 border-[#1B4332]/15 text-[#1B4332]/60'
                        }`}>
                          {prob.subject === 'science' ? (
                            <FlaskConical className="w-4 h-4 stroke-[2.5]" />
                          ) : prob.subject === 'english' ? (
                            <BookOpen className="w-4 h-4 stroke-[2.5]" />
                          ) : (
                            <Calculator className="w-4 h-4 stroke-[2.5]" />
                          )}
                          <span className="text-[10px] leading-tight mt-0.5">{idx + 1}</span>
                        </div>

                        {/* Text block */}
                        <div className="flex-1 min-w-0">
                          <p className="font-black text-sm leading-snug truncate text-[#1B4332]">
                            {displayTitle}
                          </p>
                          {cleanPreview && (
                            <p className="text-[11px] font-bold leading-snug mt-0.5 line-clamp-1 text-[#1B4332]/75">
                              {cleanPreview}
                            </p>
                          )}
                          {prob.grade && (
                            <span className={`mt-1 inline-block text-[10px] font-black px-1.5 py-0.5 rounded-full border ${
                              isSelected
                                ? 'bg-white border-[#1B4332]/25 text-[#2D6A4F]'
                                : 'bg-[#E8F5E9] border-[#1B4332]/20 text-[#2D6A4F]'
                            }`}>
                              {isKhmer ? `ថ្នាក់ ${prob.grade}` : `Gr. ${prob.grade}`}
                            </span>
                          )}
                        </div>

                        {/* Checkbox indicator */}
                        <div className={`shrink-0 w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all ${
                          isSelected
                            ? 'bg-[#2D6A4F] border-[#1B4332] text-white shadow-[1px_1px_0px_#1B4332]'
                            : 'bg-transparent border-[#1B4332]/30'
                        }`}>
                          {isSelected && (
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Bottom Actions */}
            <div className="flex gap-3 pt-2 shrink-0">
              <button
                type="button"
                onClick={() => setStage('capture')}
                className="flex-1 py-3 px-4 rounded-2xl border-3 border-[#1B4332] bg-white text-[#1B4332] font-black text-xs sm:text-sm shadow-[3px_3px_0px_#1B4332] flex items-center justify-center gap-1.5 transition-all cursor-pointer hover:bg-gray-50 active:translate-y-0.5"
              >
                <RefreshCw className="w-4 h-4 stroke-[2.5]" /> {isKhmer ? (uploadedFile ? 'ថតឡើងវិញ' : 'ត្រឡប់') : (uploadedFile ? 'Retake Photo' : 'Back')}
              </button>
              <button
                type="button"
                disabled={selectedProblemIds.size === 0}
                onClick={() => {
                  const chosenProbs = detectedProblems.filter(p => selectedProblemIds.has(p.id));
                  const finalProbs = chosenProbs.length > 0 ? chosenProbs : [detectedProblems[0] || selectedProblem];
                  onHomeworkConfirmed(finalProbs, 0, imageUri || finalProbs[0]?.imageUri);
                }}
                className={`flex-1 py-3 px-4 rounded-2xl text-white font-black text-xs sm:text-sm border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                  selectedProblemIds.size === 0
                    ? 'bg-gray-400 opacity-60 cursor-not-allowed shadow-none'
                    : 'bg-[#2D6A4F] hover:bg-[#40916C] hover:-translate-y-0.5 active:translate-y-0.5'
                }`}
              >
                <span>
                  {isKhmer 
                    ? `តោះចាប់ផ្តើម! (${selectedProblemIds.size})` 
                    : `Yes, let's start! (${selectedProblemIds.size})`}
                </span>
                <CheckCircle className="w-4 h-4 stroke-[2.5]" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
