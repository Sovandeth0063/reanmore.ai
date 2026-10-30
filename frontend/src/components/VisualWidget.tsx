/**
 * VisualWidget.tsx
 * Routes visual_data.type → the correct visual component.
 * All widgets HIDE answers before exercise completion.
 */
import { useState } from 'react';
import { VisualData, StepItem, Language } from '../types';
import { NumberLineWidget } from './widgets/NumberLineWidget';
import { PlaceValueWidget } from './widgets/PlaceValueWidget';
import { CalendarWidget } from './widgets/CalendarWidget';
import { MultipleChoiceWidget } from './widgets/MultipleChoiceWidget';
import { ObjectGroupsWidget } from './widgets/ObjectGroupsWidget';
import { VisualRenderer } from './visual/VisualRenderer';
import {
  Calendar as CalendarIcon,
  CalendarDays,
  Layers,
  Scale,
  Ruler,
  Triangle,
  Zap,
  BatteryMedium,
  Lightbulb,
  ToggleLeft,
  ToggleRight,
  Sprout,
  Activity,
  GitCompare,
  ArrowRight,
} from 'lucide-react';

interface Props {
  visualData: VisualData | null;
  step?: StepItem | undefined;
  language?: Language | undefined;
  onSelect?: ((selected: string | string[]) => void) | undefined;
}

// Convert Khmer numerals and extract active step numbers
export function extractStepNumbers(step?: StepItem, defaultGroups?: number[]): number[] {
  if (defaultGroups && defaultGroups.length > 0) {
    return defaultGroups;
  }
  if (!step) return [];
  const text = `${step.socraticPromptKhmer || ''} ${step.questionKhmer || ''} ${step.socraticPromptEng || ''} ${step.questionEng || ''} ${step.mission || ''} ${step.yourTurn || ''} ${step.helpfulExample || ''}`;
  
  const khmerToEng: Record<string, string> = {
    '០': '0', '១': '1', '២': '2', '៣': '3', '៤': '4',
    '៥': '5', '៦': '6', '៧': '7', '៨': '8', '៩': '9'
  };
  const normalized = text.replace(/[០-៩]/g, d => khmerToEng[d] || d);

  // Look for multiplication expression like "5 x 8" or "5 * 8" or "5 ដង 8"
  const multMatch = normalized.match(/(\d+)\s*(?:\*|x|×|times|ដង|គុណ)\s*(\d+)/i);
  if (multMatch) {
    const count = parseInt(multMatch[1], 10);
    const size = parseInt(multMatch[2], 10);
    if (!isNaN(count) && !isNaN(size) && count > 0 && count <= 12 && size > 0 && size <= 30) {
      return Array(count).fill(size);
    }
  }

  // Look for equal groups in text like "5 boxes with 8 apples"
  const groupWordMatch = normalized.match(/(\d+)\s*(?:boxes|box|baskets|basket|groups|group|bags|bag|ប្រអប់|កន្ត្រក|កញ្ចប់|ថង់|ក្រុម)[\s\S]{1,40}?(\d+)/i);
  if (groupWordMatch) {
    const count = parseInt(groupWordMatch[1], 10);
    const size = parseInt(groupWordMatch[2], 10);
    if (!isNaN(count) && !isNaN(size) && count > 0 && count <= 12 && size > 0 && size <= 30) {
      return Array(count).fill(size);
    }
  }
  
  // Look for addition expression like "4 + 5 + 6" or "7 + 3"
  const addMatch = normalized.match(/(\d+)\s*\+\s*(\d+)(?:\s*\+\s*(\d+))?(?:\s*\+\s*(\d+))?/);
  if (addMatch) {
    const nums = [parseInt(addMatch[1], 10), parseInt(addMatch[2], 10)];
    if (addMatch[3]) nums.push(parseInt(addMatch[3], 10));
    if (addMatch[4]) nums.push(parseInt(addMatch[4], 10));
    if (nums.every(n => !isNaN(n) && n > 0 && n <= 50)) {
      return nums;
    }
  }

  // Look for pair expressions like "7 and 3" or "7 និង 3"
  const pairMatch = normalized.match(/(\d+)\s*(?:and|និង)\s*(\d+)/i);
  if (pairMatch) {
    const nums = [parseInt(pairMatch[1], 10), parseInt(pairMatch[2], 10)];
    if (nums.every(n => !isNaN(n) && n > 0 && n <= 50)) {
      return nums;
    }
  }

  return [];
}

export function VisualWidget({ visualData, step, language, onSelect }: Props) {
  if (!visualData) return null;

  const v = visualData as Record<string, any>;
  const isKhmer = language === 'km';

  // Route deterministic VisualSpec models from Architecture v2.1 to pure SVG VisualRenderer
  if (
    v.schema_version === 1 ||
    ['ten_frame', 'fraction_bar', 'bar_model', 'array_grid'].includes(visualData.type) ||
    (visualData.type === 'number_line' && v.params) ||
    (visualData.type === 'base_ten_blocks' && v.params)
  ) {
    return <VisualRenderer spec={visualData as any} />;
  }

  switch (visualData.type) {
    case 'number_line':
      return (
        <NumberLineWidget
          start={v.start ?? 0}
          target={v.target}
          jumps={v.jumps}
          showJumps={v.show_jumps}
        />
      );

    case 'place_value_blocks':
      return <PlaceValueWidget number={v.number ?? 0} />;

    case 'objects':
    case 'number_groups':
    case 'number_grouping': {
      const activeGroups = extractStepNumbers(step, v.groups ?? v.numbers ?? []);
      return (
        <ObjectGroupsWidget
          groups={activeGroups}
          itemType={v.item_type || v.itemType || 'apple'}
          language={language}
          titleKhmer={v.title_khmer || v.titleKhmer}
          titleEng={v.title_eng || v.titleEng}
        />
      );
    }

    case 'base_ten_blocks':
      return (
        <div className="w-full bg-white/70 rounded-2xl border-2 border-indigo-200 p-4 mb-3">
          <div className="text-xs font-bold text-indigo-700 mb-2 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-indigo-600" />
            <span>Base-10 Blocks</span>
          </div>
          <p className="text-sm text-gray-700">
            Start with <strong>{v.start}</strong>.{' '}
            {v.add ? `Add ${v.add}.` : v.remove ? `Remove ${v.remove}.` : ''}
          </p>
          <p className="text-xs text-indigo-600 mt-2">What is the result?</p>
        </div>
      );

    case 'calendar':
    case 'interactive_calendar':
      return (
        <CalendarWidget

          startDate={v.start_date}
          allowCircle={v.allow_student_circle || visualData.type === 'interactive_calendar'}
        />
      );

    case 'calendar_blocks':
      return (
        <div className="w-full bg-white/70 rounded-2xl border-2 border-amber-200 p-4 mb-3">
          <div className="text-xs font-bold text-amber-700 mb-2 flex items-center gap-1.5">
            <CalendarIcon className="w-4 h-4 text-amber-600" />
            <span>Calendar Groups</span>
          </div>
          <div className="flex gap-2 justify-center">
            {Array.from({ length: v.groups ?? 2 }).map((_, i) => (
              <div key={i} className="border-2 border-amber-400 rounded-xl p-3 bg-amber-50">
                <div className="text-xs font-bold text-amber-700 text-center">Week {i + 1}</div>
                <div className="grid grid-cols-7 gap-0.5 mt-1">
                  {Array.from({ length: 7 }).map((_, d) => (
                    <div key={d} className="w-4 h-4 bg-amber-200 rounded" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      );

    case 'calendar_month':
      return (
        <div className="w-full bg-white/70 rounded-2xl border-2 border-amber-200 p-4 mb-3">
          <div className="text-xs font-bold text-amber-700 mb-2 flex items-center gap-1.5">
            <CalendarIcon className="w-4 h-4 text-amber-600" />
            <span>{v.month}</span>
          </div>
          <p className="text-sm text-gray-700">How many days are in <strong>{v.month}</strong>?</p>
        </div>
      );

    case 'year_comparison':
      return (
        <div className="w-full bg-white/70 rounded-2xl border-2 border-blue-200 p-4 mb-3">
          <div className="text-xs font-bold text-blue-700 mb-3 flex items-center gap-1.5">
            <CalendarDays className="w-4 h-4 text-blue-600" />
            <span>Year Types</span>
          </div>
          <div className="flex gap-3 justify-center">
            <div className="flex flex-col items-center p-3 bg-blue-50 rounded-xl border border-blue-200 min-w-[80px]">
              <CalendarIcon className="w-7 h-7 text-blue-600 mb-1" />
              <span className="text-xs font-bold text-blue-700 mt-1">Common Year</span>
              <span className="text-lg font-black text-blue-800">{v.common_year}</span>
              <span className="text-xs text-blue-600">days</span>
            </div>
            <div className="flex flex-col items-center p-3 bg-purple-50 rounded-xl border border-purple-200 min-w-[80px]">
              <CalendarDays className="w-7 h-7 text-purple-600 mb-1" />
              <span className="text-xs font-bold text-purple-700 mt-1">Leap Year</span>
              <span className="text-xl font-black text-purple-800">{v.show_answer_before_attempt ? v.leap_year : '?'}</span>
              <span className="text-xs text-purple-600">days</span>
            </div>
          </div>
        </div>
      );

    case 'weekday_row':
      return (
        <div className="w-full bg-white/70 rounded-2xl border-2 border-amber-200 p-3 mb-3">
          <div className="text-xs font-bold text-amber-700 mb-2 flex items-center gap-1.5">
            <CalendarIcon className="w-4 h-4 text-amber-600" />
            <span>Days of the Week</span>
          </div>
          <div className="flex gap-1 justify-center flex-wrap">
            {(v.days as string[]).map((d: string, i: number) => (
              <div key={i} className="px-2 py-1 bg-amber-100 border border-amber-300 rounded-lg text-xs font-bold text-amber-800">
                {d}
              </div>
            ))}
          </div>
        </div>
      );

    case 'fact_cards':
      return (
        <div className="w-full bg-white/70 rounded-2xl border-2 border-green-200 p-4 mb-3">
          <div className="text-xs font-bold text-green-700 mb-2 flex items-center gap-1.5">
            <CalendarIcon className="w-4 h-4 text-green-600" />
            <span>Calendar Facts</span>
          </div>
          <div className="flex gap-2 flex-wrap">
            {(v.cards as string[]).map((c: string, i: number) => (
              <div key={i} className="px-3 py-2 bg-green-50 border border-green-300 rounded-xl">
                <span className="text-sm font-bold text-green-800 capitalize">{c}</span>
                <span className="text-sm text-green-600 ml-2">= <span className="text-gray-400">?</span></span>
              </div>
            ))}
          </div>
        </div>
      );

    case 'month_list':
      return (
        <div className="w-full bg-white/70 rounded-2xl border-2 border-amber-200 p-3 mb-3">
          <div className="text-xs font-bold text-amber-700 mb-2 flex items-center gap-1.5">
            <CalendarIcon className="w-4 h-4 text-amber-600" />
            <span>Months of the Year</span>
          </div>
          <div className="grid grid-cols-3 gap-1">
            {(v.months as string[]).map((m: string, i: number) => (
              <div key={i} className="px-2 py-1 bg-amber-50 border border-amber-200 rounded-lg text-xs font-bold text-amber-700 text-center">
                {i + 1}. {m}
              </div>
            ))}
          </div>
        </div>
      );

    // Legacy hardcoded animal widgets are intentionally unsupported. The planner
    // must express animal questions as classification_split / multiple_choice data.
    case 'animal_feature_card':
    case 'animal_group_card':
      return null;

    case 'multiple_choice_images':
      return (
        <MultipleChoiceWidget
          options={v.options ?? []}
          multiSelect={false}
          onSelect={(val) => onSelect?.(val)}
        />
      );

    case 'multiple_choice_multi_select':
      return (
        <MultipleChoiceWidget
          options={v.options ?? []}
          multiSelect={v.allow_multiple_selection}
          onSelect={(val) => onSelect?.(val)}
        />
      );

    case 'producer_consumer_sort': {
      const pickBilingual = (text: string) => {
        const match = text.match(/^(.+?)\s*[\(\（]([^)\）]+)[\)\）]$/);
        if (!match) return text;
        return isKhmer ? match[1].trim() : match[2].trim();
      };
      // Items must come from the planner; there is no hardcoded example set.
      const rawItems: unknown = v.items;
      const items = (Array.isArray(rawItems) ? rawItems : [])
        .filter((item): item is string => typeof item === 'string' && item.trim().length > 0)
        .map(pickBilingual);
      if (items.length < 2) return null;
      return (
        <div className="w-full pt-1 select-none">
          <div className="text-xs sm:text-sm font-black text-[#1B4332] mb-2 flex items-center gap-1.5">
            <GitCompare className="w-4 h-4 text-[#2D6A4F]" />
            <span>
              {isKhmer
                ? 'ចាត់ថ្នាក់អ្នកផលិត និងអ្នកស៊ី៖'
                : 'Sort: Producers vs Consumers:'}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-3 mb-2">
            <div className="border-2 border-dashed border-emerald-500 bg-white/80 rounded-2xl p-3 min-h-[70px] flex flex-col items-center shadow-xs">
              <span className="text-xs font-black text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
                <Sprout className="w-3.5 h-3.5 text-emerald-700" />
                <span>{isKhmer ? 'អ្នកផលិត' : 'Producers'}</span>
              </span>
              <span className="text-[10px] text-emerald-700 font-bold mt-1 text-center">
                {isKhmer ? 'បង្កើតអាហារដោយខ្លួនឯង' : 'Makes own food'}
              </span>
            </div>
            <div className="border-2 border-dashed border-amber-500 bg-white/80 rounded-2xl p-3 min-h-[70px] flex flex-col items-center shadow-xs">
              <span className="text-xs font-black text-amber-800 bg-amber-100 px-2 py-0.5 rounded-full border border-amber-300 flex items-center gap-1">
                <Activity className="w-3.5 h-3.5 text-amber-700" />
                <span>{isKhmer ? 'អ្នកស៊ី' : 'Consumers'}</span>
              </span>
              <span className="text-[10px] text-amber-700 font-bold mt-1 text-center">
                {isKhmer ? 'ស៊ីសារពាង្គកាយដទៃ' : 'Eats other living things'}
              </span>
            </div>
          </div>
          <div className="flex gap-2 flex-wrap justify-center">
            {items.map((item: string, i: number) => (
              <span key={i} className="px-2.5 py-1 bg-white border border-emerald-300 rounded-xl text-xs font-black text-[#1B4332] shadow-xs cursor-pointer hover:bg-emerald-50">
                {item}
              </span>
            ))}
          </div>
        </div>
      );
    }

    case 'classification_split': {
      // Categories are always generated per question by the planner. There is
      // deliberately no fallback panel: a payload without categories renders
      // nothing rather than showing a hardcoded answer key.
      const categories: string[] = Array.isArray(v.categories)
        ? (v.categories as unknown[])
            .filter((c): c is string => typeof c === 'string' && c.trim().length > 0)
            .slice(0, 2)
        : [];
      if (categories.length < 2) return null;

      const heading = isKhmer ? 'ជ្រើសរើសក្រុមត្រឹមត្រូវ៖' : 'Choose the correct group:';
      const cardStyles = [
        {
          border: 'border-blue-200',
          badge: 'bg-blue-100 border-blue-300 text-blue-800',
          title: 'text-blue-900',
        },
        {
          border: 'border-rose-200',
          badge: 'bg-rose-100 border-rose-300 text-rose-800',
          title: 'text-rose-900',
        },
      ];

      // Cards are only answer choices when the backend could identify which
      // label matches the hidden answer. Otherwise they stay decorative so a
      // tap can never submit the wrong group.
      const stepOptions = Boolean(step?.options && step.options.length > 0);
      const knownAnswers =
        (step as any)?.acceptableAnswers || (step as any)?.acceptable_answers || [];
      const canTapCards =
        Boolean(onSelect) &&
        !stepOptions &&
        Array.isArray(knownAnswers) &&
        knownAnswers.length > 0;

      return (
        <div className="w-full pt-1 select-none">
          <div className="text-xs sm:text-sm font-black text-[#1B4332] mb-2 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-[#2D6A4F]" />
            <span>{heading}</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {categories.map((category: string, i: number) => {
              const style = cardStyles[i];
              const cardInner = (
                <>
                  <div
                    className={`w-9 h-9 rounded-xl border ${style.badge} font-black text-xs flex items-center justify-center mx-auto mb-1.5`}
                  >
                    {String.fromCharCode(65 + i)}
                  </div>
                  <div className={`text-xs sm:text-sm font-black ${style.title}`}>{category}</div>
                </>
              );
              return canTapCards ? (
                <button
                  key={i}
                  type="button"
                  onClick={() => onSelect?.(category)}
                  aria-label={`Choose group ${String.fromCharCode(65 + i)}: ${category}`}
                  className={`bg-white/90 border-2 ${style.border} rounded-2xl p-3 text-center shadow-xs cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-md active:translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-[#2D6A4F]`}
                >
                  {cardInner}
                </button>
              ) : (
                <div
                  key={i}
                  className={`bg-white/90 border-2 ${style.border} rounded-2xl p-3 text-center shadow-xs`}
                >
                  {cardInner}
                </div>
              );
            })}
          </div>
          {canTapCards && (
            <p className="text-[10px] sm:text-xs font-bold text-[#2D6A4F] text-center mt-1.5">
              {isKhmer ? 'ចុចក្រុមមួយដើម្បីឆ្លើយ' : 'Tap a group to answer'}
            </p>
          )}
        </div>
      );
    }

    case 'food_chain':
      return (
        <div className="w-full pt-1 select-none">
          <div className="text-xs sm:text-sm font-black text-[#1B4332] mb-2 flex items-center gap-1.5">
            <Sprout className="w-4 h-4 text-[#2D6A4F]" />
            <span>{isKhmer ? 'ខ្សែច្រវាក់អាហារ៖' : 'Ecosystem Food Chain:'}</span>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 justify-center flex-wrap py-1">
            <div className="flex flex-col items-center bg-white/90 border-2 border-emerald-300 p-2 sm:p-2.5 rounded-2xl min-w-[70px] sm:min-w-[80px] shadow-xs">
              <Sprout className="w-7 h-7 text-emerald-600 mb-1" />
              <span className="text-[10px] sm:text-xs font-black text-emerald-900 mt-1">
                {v.hide_target_word ? '???' : isKhmer ? 'អ្នកផលិត' : 'Producer'}
              </span>
            </div>

            <ArrowRight className="w-5 h-5 text-emerald-600 animate-pulse shrink-0" />

            <div className="flex flex-col items-center bg-white/90 border-2 border-amber-300 p-2 sm:p-2.5 rounded-2xl min-w-[70px] sm:min-w-[80px] shadow-xs">
              <div className="w-7 h-7 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center font-black text-[10px] mb-1">
                {isKhmer ? 'រុក្ខជាតិ' : 'HERB'}
              </div>
              <span className="text-[10px] sm:text-xs font-black text-amber-900 mt-1">
                {isKhmer ? 'អ្នកស៊ីរុក្ខជាតិ' : 'Herbivore'}
              </span>
            </div>

            <ArrowRight className="w-5 h-5 text-amber-600 animate-pulse shrink-0" />

            <div className="flex flex-col items-center bg-white/90 border-2 border-rose-300 p-2 sm:p-2.5 rounded-2xl min-w-[70px] sm:min-w-[80px] shadow-xs">
              <div className="w-7 h-7 rounded-lg bg-rose-100 text-rose-800 flex items-center justify-center font-black text-[10px] mb-1">
                {isKhmer ? 'សាច់' : 'APEX'}
              </div>
              <span className="text-[10px] sm:text-xs font-black text-rose-900 mt-1">
                {isKhmer ? 'អ្នកស៊ីសាច់' : 'Apex Predator'}
              </span>
            </div>
          </div>
        </div>
      );

    case 'plant_diagram':
      return (
        <div className="w-full pt-1 select-none">
          <div className="text-xs sm:text-sm font-black text-[#1B4332] mb-2 flex items-center gap-1.5">
            <Sprout className="w-4 h-4 text-[#2D6A4F]" />
            <span>{isKhmer ? 'ផ្នែកផ្សេងៗនៃរុក្ខជាតិ៖' : 'Plant Anatomy:'}</span>
          </div>
          <div className="flex flex-col items-center gap-1.5 max-w-xs mx-auto py-1">
            <div className="w-full py-1.5 px-3 bg-pink-100/90 border-2 border-pink-300 rounded-xl text-center text-xs font-black text-pink-900 shadow-xs flex items-center justify-between">
              <span>{isKhmer ? 'ផ្កា' : 'Flower'}</span>
              <span className="text-[10px] text-pink-700 font-bold">
                {isKhmer ? 'បន្តពូជ' : 'Reproduction'}
              </span>
            </div>
            <div className="w-full py-1.5 px-3 bg-emerald-100/90 border-2 border-emerald-300 rounded-xl text-center text-xs font-black text-emerald-900 shadow-xs flex items-center justify-between">
              <span>{isKhmer ? 'ស្លឹក' : 'Leaves'}</span>
              <span className="text-[10px] text-emerald-700 font-bold">
                {isKhmer ? 'ធ្វើរស្មីសំយោគ' : 'Photosynthesis'}
              </span>
            </div>
            <div className="w-1.5 h-4 bg-amber-600 rounded" />
            <div className="w-full py-1.5 px-3 bg-amber-100/90 border-2 border-amber-300 rounded-xl text-center text-xs font-black text-amber-900 shadow-xs flex items-center justify-between">
              <span>{isKhmer ? 'ដើម' : 'Stem'}</span>
              <span className="text-[10px] text-amber-700 font-bold">
                {isKhmer ? 'ដឹកនាំទឹក និងសារធាតុ' : 'Transports water and nutrients'}
              </span>
            </div>
            <div className="w-1.5 h-3 bg-orange-600 rounded" />
            <div className="w-full py-1.5 px-3 bg-orange-100/90 border-2 border-orange-300 rounded-xl text-center text-xs font-black text-orange-900 shadow-xs flex items-center justify-between">
              <span>{isKhmer ? 'ឫស' : 'Roots'}</span>
              <span className="text-[10px] text-orange-700 font-bold">
                {isKhmer ? 'ស្រូបយកទឹក និងជី' : 'Absorbs water and nutrients'}
              </span>
            </div>
          </div>
        </div>
      );

    case 'circuit':
    case 'circuit_simulator':
      return <InteractiveCircuitWidget v={v} isKhmer={isKhmer} />;

    case 'equation_balance':
    case 'balance_scale':
      return <EquationBalanceWidget v={v} isKhmer={isKhmer} />;

    case 'tape_diagram':
      return <TapeDiagramWidget v={v} isKhmer={isKhmer} />;

    case 'geometry_angle':
      return <GeometryAngleWidget v={v} isKhmer={isKhmer} />;

    default:
      return null;
  }
}

/* ── Interactive Sub-Widgets ── */

function InteractiveCircuitWidget({ v, isKhmer }: { v: Record<string, any>; isKhmer: boolean }) {
  const [isSwitchClosed, setIsSwitchClosed] = useState(Boolean(v.switch_closed));

  return (
    <div className="w-full pt-1 select-none">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <Zap className="w-4 h-4 text-amber-600" />
          <span className="text-xs font-black text-[#1B4332]">
            {isKhmer ? 'សៀគ្វីអគ្គិសនី៖' : 'Electric Circuit:'}
          </span>
        </div>

        <button
          onClick={() => setIsSwitchClosed(!isSwitchClosed)}
          className={`px-2.5 py-0.5 rounded-lg text-[11px] font-black border transition-all shadow-xs cursor-pointer ${
            isSwitchClosed
              ? 'bg-emerald-600 text-white border-emerald-700'
              : 'bg-rose-100 text-rose-800 border-rose-300'
          }`}
        >
          {isKhmer
            ? isSwitchClosed ? 'កុងតាក់បិទ' : 'កុងតាក់បើក'
            : isSwitchClosed ? 'Switch: ON' : 'Switch: OFF'}
        </button>
      </div>

      <div className="relative bg-slate-900 rounded-2xl p-4 flex items-center justify-around border-2 border-slate-700 overflow-hidden shadow-sm">
        {/* Battery */}
        <div className="flex flex-col items-center">
          <BatteryMedium className="w-8 h-8 text-emerald-400" />
          <span className="text-[9px] font-black text-emerald-400 mt-0.5">
            {isKhmer ? 'ថ្មពិល' : 'Battery'}
          </span>
        </div>

        {/* Animated Current Wires */}
        <div className={`h-1 flex-1 mx-2 transition-all duration-500 ${isSwitchClosed ? 'bg-amber-400 shadow-[0_0_8px_#F59E0B]' : 'bg-slate-600'}`} />

        {/* Switch */}
        <div className="flex flex-col items-center cursor-pointer" onClick={() => setIsSwitchClosed(!isSwitchClosed)}>
          {isSwitchClosed ? (
            <ToggleRight className="w-8 h-8 text-emerald-400" />
          ) : (
            <ToggleLeft className="w-8 h-8 text-slate-400" />
          )}
          <span className="text-[9px] font-black text-sky-300 mt-0.5">
            {isKhmer ? 'កុងតាក់' : 'Switch'}
          </span>
        </div>

        <div className={`h-1 flex-1 mx-2 transition-all duration-500 ${isSwitchClosed ? 'bg-amber-400 shadow-[0_0_8px_#F59E0B]' : 'bg-slate-600'}`} />

        {/* Light Bulb */}
        <div className="flex flex-col items-center">
          <div className={`relative flex items-center justify-center transition-transform ${isSwitchClosed ? 'scale-115' : 'scale-100'}`}>
            <Lightbulb className={`w-8 h-8 ${isSwitchClosed ? 'text-amber-300 fill-amber-300' : 'text-slate-500'}`} />
            {isSwitchClosed && (
              <span className="absolute -inset-2 rounded-full bg-yellow-400/30 blur-md pointer-events-none animate-pulse" />
            )}
          </div>
          <span className={`text-[9px] font-black mt-0.5 ${isSwitchClosed ? 'text-yellow-300' : 'text-slate-400'}`}>
            {isKhmer
              ? isSwitchClosed ? 'អំពូលភ្លឺ' : 'អំពូលរលត់'
              : isSwitchClosed ? 'Bulb: ON' : 'Bulb: OFF'}
          </span>
        </div>
      </div>
    </div>
  );
}

function EquationBalanceWidget({ v, isKhmer }: { v: Record<string, any>; isKhmer: boolean }) {
  const leftWeights = v.left_weights ?? 5;
  const rightWeights = v.right_weights ?? 15;
  const unknownCount = v.unknown_count ?? 2;

  return (
    <div className="w-full pt-1 select-none">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-black text-[#1B4332] flex items-center gap-1.5">
          <Scale className="w-4 h-4 text-[#2D6A4F]" />
          <span>{isKhmer ? 'ជញ្ជីងសមីការ៖' : 'Equation Balance:'}</span>
        </span>
        <span className="text-[11px] font-black text-emerald-800 bg-white/80 px-2 py-0.5 rounded-md border border-emerald-300">
          {unknownCount}x + {leftWeights} = {rightWeights}
        </span>
      </div>

      <div className="bg-white/85 rounded-2xl border-2 border-slate-200 p-3 relative shadow-xs">
        <div className="flex items-end justify-around h-24 border-b-4 border-slate-700 pb-1">
          {/* Left Pan */}
          <div className="flex flex-col items-center bg-emerald-50 border-2 border-emerald-300 p-2 rounded-xl min-w-[90px] shadow-xs">
            <span className="text-[9px] font-black text-emerald-800 mb-0.5">
              {isKhmer ? 'ថាសឆ្វេង' : 'Left side'}
            </span>
            <div className="flex gap-1 items-center">
              {Array.from({ length: unknownCount }).map((_, i) => (
                <span key={i} className="w-5 h-5 bg-emerald-600 text-white rounded-md flex items-center justify-center text-[10px] font-black shadow-xs">
                  x
                </span>
              ))}
              <span className="text-xs font-black text-gray-500">+</span>
              <span className="px-1.5 py-0.5 bg-amber-400 text-slate-900 rounded-md text-[10px] font-black shadow-xs">
                {leftWeights}
              </span>
            </div>
          </div>

          {/* Scale Fulcrum */}
          <div className="flex flex-col items-center">
            <span className="text-[10px] font-black text-slate-700 bg-slate-200 px-1.5 py-0.5 rounded-full mb-0.5">=</span>
            <div className="w-3 h-10 bg-slate-700 rounded-t-md" />
          </div>

          {/* Right Pan */}
          <div className="flex flex-col items-center bg-amber-50 border-2 border-amber-300 p-2 rounded-xl min-w-[90px] shadow-xs">
            <span className="text-[9px] font-black text-amber-800 mb-0.5">
              {isKhmer ? 'ថាសស្តាំ' : 'Right side'}
            </span>
            <span className="px-2 py-0.5 bg-amber-400 text-slate-900 rounded-md text-xs font-black shadow-xs">
              {rightWeights}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function TapeDiagramWidget({ v, isKhmer }: { v: Record<string, any>; isKhmer: boolean }) {
  const parts = (v.parts as number[]) || [3, 2];
  const total = parts.reduce((a, b) => a + b, 0);

  return (
    <div className="w-full pt-1 select-none">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-black text-[#1B4332] flex items-center gap-1.5">
          <Ruler className="w-4 h-4 text-[#2D6A4F]" />
          <span>{isKhmer ? 'គំរូរបារប្រភាគ៖' : 'Tape Model:'}</span>
        </span>
        <span className="text-[11px] font-black text-indigo-800 bg-white/80 px-2 py-0.5 rounded-md border border-indigo-300">
          {isKhmer ? `សរុប = ${total}` : `Total = ${total}`}
        </span>
      </div>

      <div className="flex rounded-xl overflow-hidden border-2 border-indigo-400 h-10 shadow-xs">
        {parts.map((p, i) => (
          <div
            key={i}
            style={{ width: `${(p / total) * 100}%` }}
            className={`flex items-center justify-center font-black text-xs border-r-2 last:border-r-0 border-white/50 ${
              i % 2 === 0 ? 'bg-indigo-500 text-white' : 'bg-sky-400 text-slate-900'
            }`}
          >
            {p}
          </div>
        ))}
      </div>
    </div>
  );
}

function GeometryAngleWidget({ v, isKhmer }: { v: Record<string, any>; isKhmer: boolean }) {
  const angleA = v.angle_a ?? 60;
  const angleB = v.angle_b ?? 70;
  const unknownAngle = v.unknown ?? '?';

  return (
    <div className="w-full pt-1 select-none">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-black text-[#1B4332] flex items-center gap-1.5">
          <Triangle className="w-4 h-4 text-[#2D6A4F]" />
          <span>
            {isKhmer ? 'មុំត្រីកោណ (សរុប = 180°)៖' : 'Triangle Angles (Sum = 180°):'}
          </span>
        </span>
      </div>

      <div className="flex items-center justify-center p-2 bg-white/80 rounded-xl border-2 border-emerald-200">
        <svg viewBox="0 0 200 110" className="w-44 h-24">
          <polygon points="100,10 20,95 180,95" fill="#E8F5E9" stroke="#1B4332" strokeWidth="2.5" />
          <text x="100" y="32" textAnchor="middle" fontSize="11" fontWeight="900" fill="#1B4332">
            {angleA}°
          </text>
          <text x="45" y="90" textAnchor="middle" fontSize="11" fontWeight="900" fill="#1B4332">
            {angleB}°
          </text>
          <text x="155" y="90" textAnchor="middle" fontSize="13" fontWeight="900" fill="#E63946">
            x = {unknownAngle}
          </text>
        </svg>
      </div>
    </div>
  );
}

