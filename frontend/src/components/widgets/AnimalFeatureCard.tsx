/**
 * AnimalFeatureCard.tsx
 * Shows an animal with a checklist of features — step-aware table where
 * previous steps show verified answers, the active step is highlighted with
 * instant-answer action buttons, and upcoming steps are shown as pending.
 */
import { StepItem } from '../../types';
import { Sparkles } from 'lucide-react';

interface Props {
  animal: string;
  emoji?: string;
  features: string[];
  step?: StepItem | undefined;
  onSelect?: ((value: string) => void) | undefined;
}

const ANIMAL_NAMES_KM: Record<string, string> = {
  flamingo: 'សត្វហ្វ្លាមីងហ្គោ (Flamingo)',
  lobster: 'សត្វបង្កង (Lobster)',
  camel: 'សត្វអូដ្ឋ (Camel)',
  giraffe: 'សត្វហ្ស៊ីរ៉ាហ្វ (Giraffe)',
  slug: 'សត្វខ្យងឥតសំបក (Slug)',
  moth: 'សត្វមេអំបៅរាត្រី (Moth)',
};

const FEATURE_LABELS: Record<string, { km: string; en: string }> = {
  vertebrate: {
    km: 'មានឆ្អឹងកង / ឆ្អឹងខ្នង',
    en: 'Vertebrate (has backbone)'
  },
  feathers: {
    km: 'មានរោមស្លាប',
    en: 'Has feathers'
  },
  hump_on_back: {
    km: 'មានបូកនៅលើខ្នង',
    en: 'Has hump on back'
  },
  pincers: {
    km: 'មានដង្កៀប / ក្រញ៉ាំ',
    en: 'Has pincers'
  },
  wings: {
    km: 'មានស្លាប',
    en: 'Has wings'
  },
};

const P8_ANIMAL_ANSWERS: Record<string, Record<string, boolean>> = {
  flamingo: { vertebrate: true, feathers: true, hump_on_back: false, pincers: false, wings: true },
  lobster:  { vertebrate: false, feathers: false, hump_on_back: false, pincers: true, wings: false },
  camel:    { vertebrate: true, feathers: false, hump_on_back: true, pincers: false, wings: false },
  giraffe:  { vertebrate: true, feathers: false, hump_on_back: false, pincers: false, wings: false },
  slug:     { vertebrate: false, feathers: false, hump_on_back: false, pincers: false, wings: false },
  moth:     { vertebrate: false, feathers: false, hump_on_back: false, pincers: false, wings: true },
};

export function AnimalFeatureCard({ animal, emoji, features, step, onSelect }: Props) {
  const normAnimal = animal.toLowerCase().trim();
  const displayName = ANIMAL_NAMES_KM[normAnimal] || animal;
  const answers = P8_ANIMAL_ANSWERS[normAnimal] || {};

  // Determine current active step (0-indexed)
  const activeStepIdx = typeof step?.stepNumber === 'number' ? step.stepNumber - 1 : 0;
  const isAllComplete = activeStepIdx >= features.length;

  return (
    <div className="w-full bg-white/95 rounded-2xl border-2 sm:border-3 border-[#1B4332] p-3 sm:p-4 shadow-[2px_2px_0px_#1B4332] space-y-2.5">
      {/* Animal Header */}
      <div className="flex items-center justify-between gap-2 pb-2 border-b border-[#1B4332]/15">
        <div className="flex items-center gap-2.5 min-w-0">
          {emoji ? (
            <span className="text-3xl sm:text-4xl shrink-0">{emoji}</span>
          ) : (
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-[#E8F5E9] border-2 border-[#1B4332] shadow-[1px_1px_0px_#1B4332] flex items-center justify-center shrink-0">
              <Sparkles className="w-5 h-5 text-[#2D6A4F]" />
            </div>
          )}
          <div className="min-w-0">
            <h4 className="font-black text-[#1B4332] capitalize text-sm sm:text-base truncate">
              {displayName}
            </h4>
            <p className="text-[11px] sm:text-xs text-[#2D6A4F] font-bold">
              តារាងផ្ទៀងផ្ទាត់លក្ខណៈសត្វ (Feature Checklist)
            </p>
          </div>
        </div>
        <span className="text-[10px] sm:text-xs font-black bg-[#E8F5E9] text-[#1B4332] border border-[#2D6A4F] px-2 py-0.5 rounded-full shrink-0">
          {isAllComplete ? '✓ រួចរាល់' : `ជំហានទី ${Math.min(activeStepIdx + 1, features.length)} / ${features.length}`}
        </span>
      </div>

      {/* Feature Rows */}
      <div className="flex flex-col gap-1.5 sm:gap-2">
        {features.map((f, idx) => {
          const label = FEATURE_LABELS[f];
          const displayLabel = label ? label.km : f;
          const isPast = idx < activeStepIdx;
          const isCurrent = idx === activeStepIdx;
          const isFuture = idx > activeStepIdx;
          const isPresent = answers[f] === true;

          return (
            <div
              key={f}
              className={`flex items-center justify-between gap-2 p-2 sm:p-2.5 rounded-xl border-2 transition-all ${
                isCurrent
                  ? 'bg-[#E8F5E9] border-[#2D6A4F] shadow-[1.5px_1.5px_0px_#1B4332] ring-2 ring-[#40916C]/40'
                  : isPast
                  ? 'bg-white border-[#1B4332]/30 opacity-90'
                  : 'bg-slate-50/80 border-slate-200 opacity-60'
              }`}
            >
              {/* Feature label with numbering */}
              <div className="flex items-center gap-2 min-w-0">
                <span className={`w-5 h-5 rounded-md text-[11px] font-black flex items-center justify-center shrink-0 ${
                  isCurrent ? 'bg-[#2D6A4F] text-white' : isPast ? 'bg-[#1B4332]/10 text-[#1B4332]' : 'bg-slate-200 text-slate-500'
                }`}>
                  {idx + 1}
                </span>
                <span className={`text-xs sm:text-sm font-black truncate ${
                  isCurrent ? 'text-[#1B4332]' : isPast ? 'text-slate-700' : 'text-slate-400'
                }`}>
                  {displayLabel}?
                </span>
              </div>

              {/* Status or Interactive Action Buttons */}
              <div className="shrink-0 flex items-center gap-1.5">
                {isPast && (
                  <span className={`px-2 py-0.5 rounded-lg text-xs font-black border flex items-center gap-1 ${
                    isPresent
                      ? 'bg-emerald-100 text-emerald-800 border-emerald-400'
                      : 'bg-rose-100 text-rose-800 border-rose-300'
                  }`}>
                    {isPresent ? '✓ មាន (Tick)' : '✗ គ្មាន (Cross)'}
                  </span>
                )}

                {isCurrent && (
                  <div className="flex items-center gap-1.5 animate-fadeIn">
                    <button
                      type="button"
                      onClick={() => onSelect?.('✓ មាន (Yes)')}
                      className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-black rounded-lg border border-emerald-800 shadow-[1px_1px_0px_#1B4332] transition-transform active:scale-95 cursor-pointer flex items-center gap-1"
                    >
                      <span>✓ មាន</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => onSelect?.('✗ គ្មាន (No)')}
                      className="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-black rounded-lg border border-rose-800 shadow-[1px_1px_0px_#1B4332] transition-transform active:scale-95 cursor-pointer flex items-center gap-1"
                    >
                      <span>✗ គ្មាន</span>
                    </button>
                  </div>
                )}

                {isFuture && (
                  <span className="px-2 py-0.5 rounded-lg text-[11px] font-bold bg-slate-100 text-slate-400 border border-slate-200">
                    ? រង់ចាំ
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {isAllComplete ? (
        <div className="p-2 bg-[#2D6A4F] text-white text-xs font-black rounded-xl text-center shadow-xs">
          តារាងលក្ខណៈសត្វត្រូវបានបំពេញរួចរាល់ទាំងស្រុង!
        </div>
      ) : (
        <p className="text-[11px] text-[#2D6A4F] font-bold text-center">
          ចុចជ្រើសរើស «✓ មាន» ឬ «✗ គ្មាន» សម្រាប់លក្ខណៈក្នុងជំហាននេះ
        </p>
      )}
    </div>
  );
}

