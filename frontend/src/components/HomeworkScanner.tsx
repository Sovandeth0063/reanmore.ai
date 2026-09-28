import React, { useState, useRef, useEffect } from 'react';
import { Camera, Upload, RefreshCw, CheckCircle, ArrowLeft, Sparkles, BookOpen, AlertCircle } from 'lucide-react';
import { TunsayAvatar } from './TunsayAvatar';
import { HomeworkProblem, Language } from '../types';
import { MOCK_PROBLEMS } from '../data/mockProblems';
import { processHomeworkImage } from '../services/ocrService';

interface HomeworkScannerProps {
  language?: Language;
  onHomeworkConfirmed: (problems: HomeworkProblem[], initialIndex?: number, imageUri?: string) => void;
  onCancel: () => void;
}

export const HomeworkScanner: React.FC<HomeworkScannerProps> = ({
  language = 'km',
  onHomeworkConfirmed,
  onCancel
}) => {
  const isKhmer = language === 'km';
  const [stage, setStage] = useState<'capture' | 'preview' | 'analyzing' | 'confirm'>('capture');
  const [imageUri, setImageUri] = useState<string>('');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [detectedProblems, setDetectedProblems] = useState<HomeworkProblem[]>([]);
  const [selectedProblem, setSelectedProblem] = useState<HomeworkProblem>(MOCK_PROBLEMS[0]);
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
    const subjectProblems = MOCK_PROBLEMS.filter(p => p.subject === subject);
    const chosenProblems = subjectProblems.length > 0 ? subjectProblems : [MOCK_PROBLEMS[0]];
    const mainProblem = chosenProblems[0];

    setDetectedProblems(chosenProblems);
    setSelectedProblem(mainProblem);
    setAnalysisError(null);
    setImageUri(mainProblem.imageUri || 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600&auto=format&fit=crop&q=80');
    setStage('preview');
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
          setDetectedProblems(result.problems);
          setSelectedProblem(result.problems[0]);
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
    setStage('confirm');
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={isKhmer ? 'ស្កែនលំហាត់' : 'Homework Scanner'}
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
          <Camera className="w-4 h-4 stroke-[2.5]" /> {isKhmer ? 'ស្កែនលំហាត់' : 'Homework Scanner'}
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
                  ? 'ដាក់ក្រដាសលំហាត់របស់អ្នកឲ្យចំកណ្តាលស៊ុម' 
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
                    <div className="w-10 h-10 rounded-xl bg-[#2D6A4F] text-white group-hover:bg-white group-hover:text-[#1B4332] border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] flex items-center justify-center font-black text-lg transition-colors">
                      🔢
                    </div>
                    <span className="text-[10px] font-black text-[#1B4332] bg-white group-hover:bg-[#1B4332] group-hover:text-white px-2.5 py-0.5 rounded-full border-2 border-[#1B4332] transition-colors">
                      {isKhmer ? 'ថ្នាក់ទី ៤ • គណិត' : 'Grade 4 • Math'}
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
                    <div className="w-10 h-10 rounded-xl bg-[#40916C] text-white group-hover:bg-white group-hover:text-[#1B4332] border-2 border-[#1B4332] shadow-[1.5px_1.5px_0px_#1B4332] flex items-center justify-center font-black text-lg transition-colors">
                      🧪
                    </div>
                    <span className="text-[10px] font-black text-[#1B4332] bg-white group-hover:bg-[#1B4332] group-hover:text-white px-2.5 py-0.5 rounded-full border-2 border-[#1B4332] transition-colors">
                      {isKhmer ? 'ថ្នាក់ទី ៤ • វិទ្យាសាស្ត្រ' : 'Grade 4 • Science'}
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
          <div className="p-6 space-y-4">
            <div className="flex items-center gap-3 p-3 bg-[#40916C] rounded-2xl border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332]">
              <TunsayAvatar size="sm" state="explaining" showBadge={false} />
              <div>
                <p className="font-black text-sm text-white">
                  {isKhmer 
                    ? `ខ្ញុំឃើញ ${detectedProblems.length > 1 ? `${detectedProblems.length} លំហាត់` : 'លំហាត់'} របស់អ្នកហើយ! តោះដោះស្រាយវាជាមួយគ្នា!` 
                    : `I found ${detectedProblems.length > 1 ? `${detectedProblems.length} exercises` : 'your exercise'}! Let's solve it together!`}
                </p>
              </div>
            </div>

            {analysisError && (
              <div className="p-3 bg-amber-50 border-2 border-amber-400 rounded-xl text-xs font-bold text-amber-900 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-amber-600" />
                <span>{analysisError}</span>
              </div>
            )}

            {/* Multiple Exercise Selector if > 1 exercises detected */}
            {detectedProblems.length > 1 && (
              <div className="space-y-1.5">
                <p className="text-xs font-black text-[#1B4332] uppercase tracking-wider">
                  {isKhmer ? 'ជ្រើសរើសលំហាត់ដែលចង់ដោះស្រាយមុន៖' : 'Select Exercise to Solve:'}
                </p>
                <div className="flex gap-2 overflow-x-auto pb-1.5 pt-0.5 no-scrollbar">
                  {detectedProblems.map((prob, idx) => {
                    const isSelected = selectedProblem.id === prob.id;
                    const label = prob.titleKhmer || prob.titleEng || `Problem ${idx + 1}`;
                    return (
                      <button
                        key={prob.id || idx}
                        type="button"
                        onClick={() => setSelectedProblem(prob)}
                        className={`px-3 py-1.5 rounded-xl border-2 font-black text-xs shrink-0 cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-[#1B4332] text-white border-[#1B4332] shadow-[2px_2px_0px_#2D6A4F] scale-[1.02]'
                            : 'bg-white text-[#1B4332] border-[#1B4332] hover:bg-[#E8F5E9]'
                        }`}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Detected Question Box */}
            <div className="p-4 bg-[#E8F5E9] rounded-2xl border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] space-y-2 max-h-48 overflow-y-auto">
              <div className="flex items-center justify-between">
                <p className="text-xs font-black text-[#1B4332] uppercase">
                  {isKhmer ? 'សំណួរដែលស្កែនបាន៖' : 'Detected Question:'}
                </p>
                {selectedProblem.grade && (
                  <span className="text-[10px] font-black bg-white px-2 py-0.5 rounded-full border border-[#1B4332]">
                    {isKhmer ? `ថ្នាក់ទី ${selectedProblem.grade}` : `Grade ${selectedProblem.grade}`}
                  </span>
                )}
              </div>
              <p className="font-bold text-sm text-[#1B4332] whitespace-pre-line leading-relaxed">
                {selectedProblem.problemStatementKhmer || selectedProblem.problemStatementEng}
              </p>
            </div>

            <p className="text-center font-black text-xs sm:text-sm text-[#1B4332]">
              {isKhmer ? 'តើសំណួរនេះត្រឹមត្រូវទេ?' : 'Does this look correct?'}
            </p>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStage('capture')}
                className="flex-1 py-3 px-4 rounded-2xl border-3 border-[#1B4332] bg-white text-[#1B4332] font-black text-xs sm:text-sm shadow-[3px_3px_0px_#1B4332] flex items-center justify-center gap-1 transition-all cursor-pointer hover:bg-gray-50"
              >
                <RefreshCw className="w-4 h-4 stroke-[2.5]" /> {isKhmer ? 'ថតឡើងវិញ' : 'Retake Photo'}
              </button>
              <button
                type="button"
                onClick={() => {
                  const allProbs = detectedProblems.length > 0 ? detectedProblems : [selectedProblem];
                  const initialIdx = allProbs.findIndex(p => p.id === selectedProblem.id);
                  onHomeworkConfirmed(allProbs, initialIdx >= 0 ? initialIdx : 0, imageUri || selectedProblem.imageUri);
                }}
                className="flex-1 py-3 px-4 rounded-2xl bg-[#2D6A4F] text-white font-black text-xs sm:text-sm border-3 border-[#1B4332] shadow-[3px_3px_0px_#1B4332] flex items-center justify-center gap-1 transition-all cursor-pointer hover:-translate-y-0.5 active:translate-y-0.5 hover:bg-[#40916C]"
              >
                <span>{isKhmer ? 'តោះចាប់ផ្តើម!' : 'Yes, let\'s start!'}</span>
                <CheckCircle className="w-4 h-4 stroke-[2.5]" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
