/**
 * AnimalFeatureCard.tsx
 * Shows an animal with a checklist of features — checkboxes are interactive
 * with bilingual Khmer & English support.
 */
import { useState } from 'react';

interface Props {
  animal: string;
  emoji: string;
  features: string[];
  onSelect?: (value: string) => void;
}

const ANIMAL_NAMES_KM: Record<string, string> = {
  flamingo: 'សត្វផ្លាមីងហ្គោ (Flamingo)',
  lobster: 'សត្វបង្កង (Lobster)',
  camel: 'សត្វអូដ្ឋ (Camel)',
  giraffe: 'សត្វហ្ស៊ីរ៉ាហ្វ (Giraffe)',
  slug: 'សត្វខ្យងឥតសំបក (Slug)',
  moth: 'សត្វមេអំបៅយប់ (Moth)',
};

const FEATURE_LABELS: Record<string, { km: string; en: string }> = {
  vertebrate: {
    km: 'មានឆ្អឹងកង / ឆ្អឹងខ្នង (Vertebrate)?',
    en: 'Vertebrate (has backbone)?'
  },
  feathers: {
    km: 'មានរោមស្លាប (Has feathers)?',
    en: 'Has feathers?'
  },
  hump_on_back: {
    km: 'មានបូកនៅលើខ្នង (Has hump on back)?',
    en: 'Has hump on back?'
  },
  pincers: {
    km: 'មានដង្កៀប / ក្រញ៉ាំ (Has pincers)?',
    en: 'Has pincers?'
  },
  wings: {
    km: 'មានស្លាប (Has wings)?',
    en: 'Has wings?'
  },
};

export function AnimalFeatureCard({ animal, emoji, features, onSelect }: Props) {
  const [checked, setChecked] = useState<Record<string, boolean | null>>({});

  const toggle = (f: string) => {
    const nextVal = checked[f] === true ? false : checked[f] === false ? null : true;
    setChecked(prev => ({ ...prev, [f]: nextVal }));
    if (onSelect && nextVal !== null) {
      onSelect(nextVal === true ? 'Yes' : 'No');
    }
  };

  const displayName = ANIMAL_NAMES_KM[animal.toLowerCase()] || animal;

  return (
    <div className="w-full bg-white/80 rounded-2xl border-2 border-emerald-300 p-4 mb-3 shadow-xs">
      <div className="flex items-center gap-3 mb-3">
        <span className="text-4xl">{emoji}</span>
        <div>
          <div className="font-black text-emerald-900 capitalize text-base">{displayName}</div>
          <div className="text-xs text-emerald-700 font-bold">
            គូសសញ្ញាគ្រីស ✅ ឬខ្វែង ❌ សម្រាប់លក្ខណៈនីមួយៗ (Tick or cross)
          </div>
        </div>
      </div>
      <div className="flex flex-col gap-2">
        {features.map(f => {
          const label = FEATURE_LABELS[f];
          const displayLabel = label ? label.km : f;
          return (
            <div key={f} className="flex items-center gap-2.5">
              <button
                type="button"
                onClick={() => toggle(f)}
                className={[
                  'w-9 h-9 rounded-xl border-2 font-black text-base flex items-center justify-center transition-all cursor-pointer shadow-xs',
                  checked[f] === true ? 'bg-emerald-500 border-emerald-700 text-white scale-105' :
                  checked[f] === false ? 'bg-rose-500 border-rose-700 text-white scale-105' :
                  'bg-white border-slate-300 text-slate-400 hover:border-emerald-400',
                ].join(' ')}
              >
                {checked[f] === true ? '✓' : checked[f] === false ? '✗' : '?'}
              </button>
              <span 
                onClick={() => toggle(f)}
                className="text-xs sm:text-sm font-black text-slate-800 cursor-pointer hover:text-emerald-800 select-none"
              >
                {displayLabel}
              </span>
            </div>
          );
        })}
      </div>
      <p className="text-[11px] text-emerald-700 font-bold mt-2.5">
        👉 ចុចលើប៊ូតុងដើម្បីជ្រើសរើស ✅ ឬ ❌ (Tap button to choose ✓ or ✗)
      </p>
    </div>
  );
}

