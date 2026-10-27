import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Play,
  Server,
  Zap,
  HardDrive,
  X,
  Shield,
} from 'lucide-react';
import {
  LLMControllerService,
  LLMStatusResponse,
  LLMModelsResponse,
  TestGenerationResult,
} from '../services/llmControllerService';

interface LLMControllerModalProps {
  isOpen: boolean;
  onClose: () => void;
  language?: 'km' | 'en';
}

export const LLMControllerModal: React.FC<LLMControllerModalProps> = ({
  isOpen,
  onClose,
  language = 'km',
}) => {
  const isKm = language === 'km';
  const [status, setStatus] = useState<LLMStatusResponse | null>(null);
  const [modelsData, setModelsData] = useState<LLMModelsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [testResult, setTestResult] = useState<TestGenerationResult | null>(null);
  const [testing, setTesting] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  const fetchStatusAndModels = async () => {
    setLoading(true);
    const [s, m] = await Promise.all([
      LLMControllerService.getStatus(),
      LLMControllerService.getModels(),
    ]);
    setStatus(s);
    setModelsData(m);
    setLoading(false);
  };

  useEffect(() => {
    if (isOpen) {
      fetchStatusAndModels();
      setTestResult(null);
      setNotification(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSwitchProvider = async (provider: string, model?: string) => {
    setSwitching(true);
    setNotification(null);
    const res = await LLMControllerService.switchProvider(provider, model);
    if (res.success) {
      setNotification(res.message);
      await fetchStatusAndModels();
    } else {
      setNotification(`Error: ${res.message}`);
    }
    setSwitching(false);
  };

  const handleTestConnection = async (provider?: string, model?: string) => {
    setTesting(true);
    setTestResult(null);
    const res = await LLMControllerService.testGeneration(
      'Hello from ReanMore Tutor! Confirm system status.',
      provider,
      model
    );
    setTestResult(res);
    setTesting(false);
  };

  const activeProvider = status?.primary_provider || 'gemini';
  const activeModel = status?.active_model || 'default';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl border-2 border-[#2D6A4F] overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-[#1B4332] text-white px-5 py-4 flex items-center justify-between shadow-md">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-[#2D6A4F] rounded-xl text-[#74C69D]">
              <Cpu className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-black tracking-wide flex items-center gap-2">
                {isKm ? 'ឧបករណ៍គ្រប់គ្រង LLM (LLM Controller)' : 'LLM Engine Controller'}
                <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 bg-[#40916C] text-white rounded-full">
                  Zero-Code Swap
                </span>
              </h2>
              <p className="text-xs text-[#D8F3DC]">
                {isKm
                  ? 'ប្តូរម៉ូដែល AI ដោយសេរី ដោយមិនប៉ះពាល់ដល់ប្រព័ន្ធស្នូល'
                  : 'Seamlessly switch models & providers without touching core systems'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-4 sm:p-5 overflow-y-auto space-y-4 flex-1 text-slate-800">
          {/* Active Model Banner */}
          <div className="bg-gradient-to-r from-[#D8F3DC] to-[#B7E4C7] p-3.5 sm:p-4 rounded-xl border border-[#74C69D] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#2D6A4F] text-white flex items-center justify-center font-black shadow-inner">
                {activeProvider === 'ollama' ? (
                  <HardDrive className="w-5 h-5" />
                ) : activeProvider === 'gemini' ? (
                  <Sparkles className="w-5 h-5 text-amber-300" />
                ) : (
                  <Server className="w-5 h-5" />
                )}
              </div>
              <div>
                <div className="text-[11px] font-bold text-[#1B4332] uppercase tracking-wider">
                  {isKm ? 'ម៉ាស៊ីនកំពុងដំណើរការ (Active Engine)' : 'Active Engine'}
                </div>
                <div className="text-base font-extrabold text-[#1B4332] flex items-center gap-1.5">
                  <span className="capitalize">{activeProvider}</span>
                  <span className="text-xs font-semibold text-[#2D6A4F]">({activeModel})</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => handleTestConnection(activeProvider, activeModel)}
              disabled={testing || switching}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1B4332] hover:bg-[#2D6A4F] text-white text-xs font-black rounded-lg transition-all shadow-sm active:scale-95 disabled:opacity-50"
            >
              {testing ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5 fill-current" />
              )}
              <span>{isKm ? 'សាកល្បង (Ping)' : 'Test Ping'}</span>
            </button>
          </div>

          {notification && (
            <div className="px-3.5 py-2.5 bg-emerald-50 border border-emerald-300 rounded-lg text-xs font-semibold text-emerald-800 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{notification}</span>
            </div>
          )}

          {/* Test Ping Result Card */}
          {testResult && (
            <div
              className={`p-3 rounded-xl border text-xs font-mono transition-all ${
                testResult.success
                  ? 'bg-emerald-50/70 border-emerald-300 text-emerald-900'
                  : 'bg-rose-50 border-rose-300 text-rose-900'
              }`}
            >
              <div className="flex items-center justify-between font-bold mb-1">
                <span className="flex items-center gap-1.5">
                  {testResult.success ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  ) : (
                    <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                  )}
                  {testResult.success ? 'Engine Responded Successfully' : 'Test Failed'}
                </span>
                {testResult.latency_ms !== undefined && (
                  <span className="text-[10px] px-1.5 py-0.5 bg-white rounded border border-emerald-200">
                    ⏱️ {testResult.latency_ms.toFixed(0)}ms
                  </span>
                )}
              </div>
              {testResult.response_text && (
                <p className="mt-1 text-slate-700 bg-white/80 p-2 rounded border border-slate-200 break-words font-sans">
                  "{testResult.response_text}"
                </p>
              )}
              {testResult.error && <p className="mt-1 text-rose-700">{testResult.error}</p>}
            </div>
          )}

          {/* Available Engine Selection */}
          <div className="space-y-2.5">
            <div className="text-xs font-black uppercase text-slate-500 tracking-wider">
              {isKm ? 'ជ្រើសរើសម៉ូដែល AI (Select AI Model)' : 'Available LLM Providers & Models'}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {/* Option 1: Local Ollama Qwen3.5:4b */}
              <div
                onClick={() => handleSwitchProvider('ollama', 'qwen3.5:4b')}
                className={`p-3 rounded-xl border-2 transition-all cursor-pointer relative ${
                  activeProvider === 'ollama' && activeModel === 'qwen3.5:4b'
                    ? 'border-[#2D6A4F] bg-emerald-50/60 shadow-md ring-2 ring-[#40916C]/20'
                    : 'border-slate-200 hover:border-[#74C69D] hover:bg-slate-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-blue-100 text-blue-700 rounded-lg">
                      <HardDrive className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-extrabold text-sm text-slate-800">Qwen 3.5 4B</div>
                      <div className="text-[10px] text-blue-700 font-bold">Local Ollama • 3.4GB</div>
                    </div>
                  </div>
                  {activeProvider === 'ollama' && activeModel === 'qwen3.5:4b' && (
                    <CheckCircle2 className="w-4 h-4 text-[#2D6A4F]" />
                  )}
                </div>
                <p className="text-[11px] text-slate-600 mt-2">
                  {isKm
                    ? 'ដំណើរការក្នុងម៉ាស៊ីនផ្ទាល់ (Offline 100%) សមត្ថភាពហេតុផលខ្ពស់'
                    : '100% Offline inference, lightweight, great reasoning on CPU/GPU'}
                </p>
              </div>

              {/* Option 2: Local Ollama Gemma4:e4b */}
              <div
                onClick={() => handleSwitchProvider('ollama', 'gemma4:e4b')}
                className={`p-3 rounded-xl border-2 transition-all cursor-pointer relative ${
                  activeProvider === 'ollama' && activeModel === 'gemma4:e4b'
                    ? 'border-[#2D6A4F] bg-emerald-50/60 shadow-md ring-2 ring-[#40916C]/20'
                    : 'border-slate-200 hover:border-[#74C69D] hover:bg-slate-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-purple-100 text-purple-700 rounded-lg">
                      <Cpu className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-extrabold text-sm text-slate-800">Gemma 4 e4b</div>
                      <div className="text-[10px] text-purple-700 font-bold">Local Ollama • 6.6GB</div>
                    </div>
                  </div>
                  {activeProvider === 'ollama' && activeModel === 'gemma4:e4b' && (
                    <CheckCircle2 className="w-4 h-4 text-[#2D6A4F]" />
                  )}
                </div>
                <p className="text-[11px] text-slate-600 mt-2">
                  {isKm
                    ? 'ម៉ូដែលធំកម្រិតខ្ពស់ ជំនាញគណិតវិទ្យា និងវិទ្យាសាស្ត្រស៊ីជម្រៅ'
                    : 'High capacity 7.5B model for deep math & science reasoning'}
                </p>
              </div>

              {/* Option 3: Google Gemini Cloud */}
              <div
                onClick={() => handleSwitchProvider('gemini', 'gemini-3.6-flash')}
                className={`p-3 rounded-xl border-2 transition-all cursor-pointer relative ${
                  activeProvider === 'gemini'
                    ? 'border-[#2D6A4F] bg-emerald-50/60 shadow-md ring-2 ring-[#40916C]/20'
                    : 'border-slate-200 hover:border-[#74C69D] hover:bg-slate-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-amber-100 text-amber-700 rounded-lg">
                      <Sparkles className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-extrabold text-sm text-slate-800">Gemini 3.6 Flash</div>
                      <div className="text-[10px] text-amber-700 font-bold">Google Cloud API</div>
                    </div>
                  </div>
                  {activeProvider === 'gemini' && (
                    <CheckCircle2 className="w-4 h-4 text-[#2D6A4F]" />
                  )}
                </div>
                <p className="text-[11px] text-slate-600 mt-2">
                  {isKm
                    ? 'ល្បឿនលឿនបំផុត និងឆ្លើយតបភាសាខ្មែរ-អង់គ្លេសបានច្បាស់លាស់'
                    : 'Ultra-low latency cloud, highest quota, multimodal vision'}
                </p>
              </div>

              {/* Option 4: Mock Provider */}
              <div
                onClick={() => handleSwitchProvider('mock')}
                className={`p-3 rounded-xl border-2 transition-all cursor-pointer relative ${
                  activeProvider === 'mock'
                    ? 'border-[#2D6A4F] bg-emerald-50/60 shadow-md ring-2 ring-[#40916C]/20'
                    : 'border-slate-200 hover:border-[#74C69D] hover:bg-slate-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-slate-100 text-slate-700 rounded-lg">
                      <Zap className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-extrabold text-sm text-slate-800">Mock Tutor (Offline)</div>
                      <div className="text-[10px] text-slate-500 font-bold">Zero-Cost Testing</div>
                    </div>
                  </div>
                  {activeProvider === 'mock' && (
                    <CheckCircle2 className="w-4 h-4 text-[#2D6A4F]" />
                  )}
                </div>
                <p className="text-[11px] text-slate-600 mt-2">
                  {isKm
                    ? 'សម្រាប់ធ្វើតេស្តសាកល្បងដោយគ្មានការចំណាយ និងគ្មានអ៊ីនធឺណិត'
                    : 'Deterministic instant mock for UI tests, debugging, and demo safety net'}
                </p>
              </div>
            </div>
          </div>

          {/* Invariant Safety Note */}
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-[11px] text-slate-600 flex items-start gap-2">
            <Shield className="w-4 h-4 text-slate-700 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-slate-800">
                {isKm ? 'គោលការណ៍សុវត្ថិភាពអចិន្ត្រៃយ៍៖' : 'Decoupled Core Architecture:'}
              </span>{' '}
              {isKm
                ? 'តម្រងសុវត្ថិភាពកុមារ ការពារការបែកធ្លាយចម្លើយ (Leak Defense) និងការត្រួតពិនិត្យគណិតវិទ្យា (AST Math Grader) នៅតែដំណើរការជាស្វ័យប្រវត្តិដោយឯករាជ្យ ទោះបីជាប្តូរម៉ូដែល AI ណាក៏ដោយ។'
                : 'Pedagogical Socratic state machine, regex leak defense, and AST math grading operate strictly independent of whichever LLM is chosen.'}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-5 py-3.5 bg-slate-100 border-t border-slate-200 flex items-center justify-between">
          <div className="text-[11px] text-slate-500 flex items-center gap-2">
            <span>{loading ? 'Refreshing status...' : `Fallback: ${status?.fallback_provider || 'mock'}`}</span>
            {modelsData?.models?.ollama && modelsData.models.ollama.length > 0 && (
              <span className="text-[10px] bg-slate-200/80 text-slate-600 px-1.5 py-0.5 rounded font-mono font-medium">
                {modelsData.models.ollama.length} Ollama models detected
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-[#1B4332] hover:bg-[#2D6A4F] text-white text-xs font-bold rounded-lg transition-colors cursor-pointer"
          >
            {isKm ? 'រួចរាល់' : 'Done'}
          </button>
        </div>
      </div>
    </div>
  );
};
