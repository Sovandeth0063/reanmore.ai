import { useState } from 'react';
import { Sparkles, RefreshCw, Circle, Star, Square, Disc } from 'lucide-react';

interface Props {
  groups: number[];
  itemType?: 'apple' | 'orange' | 'star' | 'pencil' | 'cookie';
  titleKhmer?: string;
  titleEng?: string;
}

const ITEM_ICONS = {
  apple: { nameKhmer: 'ផ្លែប៉ោម', nameEng: 'Apples', color: '#E63946', bg: 'bg-red-50 border-red-200', icon: Circle, iconClass: 'fill-red-500 text-red-600' },
  orange: { nameKhmer: 'ផ្លែក្រូច', nameEng: 'Oranges', color: '#F77F00', bg: 'bg-orange-50 border-orange-200', icon: Circle, iconClass: 'fill-orange-500 text-orange-600' },
  star: { nameKhmer: 'ផ្កាយ', nameEng: 'Stars', color: '#FCBF49', bg: 'bg-amber-50 border-amber-200', icon: Star, iconClass: 'fill-amber-400 text-amber-500' },
  pencil: { nameKhmer: 'ខ្មៅដៃ', nameEng: 'Pencils', color: '#457B9D', bg: 'bg-blue-50 border-blue-200', icon: Square, iconClass: 'fill-blue-500 text-blue-600' },
  cookie: { nameKhmer: 'នំឃុកឃី', nameEng: 'Cookies', color: '#8D5B4C', bg: 'bg-amber-50 border-amber-300', icon: Disc, iconClass: 'fill-amber-700 text-amber-800' },
};

export function ObjectGroupsWidget({ groups, itemType = 'apple', titleKhmer, titleEng }: Props) {
  const [countedItems, setCountedItems] = useState<Record<string, number>>({});
  const [currentTotalCount, setCurrentTotalCount] = useState(0);

  const itemInfo = ITEM_ICONS[itemType] || ITEM_ICONS.apple;

  const handleTapItem = (groupIdx: number, itemIdx: number) => {
    const key = `${groupIdx}_${itemIdx}`;
    if (countedItems[key]) {
      // Un-count
      const newMap = { ...countedItems };
      delete newMap[key];
      setCountedItems(newMap);
      setCurrentTotalCount(Object.keys(newMap).length);
    } else {
      // Count next
      const nextNum = currentTotalCount + 1;
      setCountedItems(prev => ({ ...prev, [key]: nextNum }));
      setCurrentTotalCount(nextNum);
    }
  };

  const handleResetCount = () => {
    setCountedItems({});
    setCurrentTotalCount(0);
  };

  return (
    <div className="w-full pt-1 select-none">
      {(titleKhmer || titleEng) && (
        <div className="text-xs font-bold text-center text-[#1B4332] mb-1.5">
          {titleKhmer || titleEng}
        </div>
      )}
      {/* Visual Baskets Container */}
      <div className="flex gap-3 sm:gap-4 justify-center items-stretch flex-wrap pt-1">
        {groups.map((count, gi) => (
          <div
            key={gi}
            className={`flex flex-col items-center justify-between p-3 sm:p-4 rounded-2xl border-2 border-dashed border-[#2D6A4F] bg-gradient-to-b from-emerald-50/70 to-white min-w-[90px] sm:min-w-[110px] relative shadow-sm`}
          >
            {/* Basket Badge */}
            <span className="text-[10px] font-black text-emerald-900 bg-emerald-200/80 px-2 py-0.5 rounded-full border border-emerald-300 mb-2">
              ក្រុមទី {gi + 1}
            </span>

            {/* Apple Items Grid */}
            <div className="grid grid-cols-3 gap-1.5 sm:gap-2 my-auto p-1.5 justify-items-center">
              {Array.from({ length: count }).map((_, i) => {
                const key = `${gi}_${i}`;
                const countNumber = countedItems[key];
                const isCounted = Boolean(countNumber);

                const Icon = itemInfo.icon;
                return (
                  <button
                    key={i}
                    onClick={() => handleTapItem(gi, i)}
                    className={`
                      w-8 h-8 sm:w-9 sm:h-9 rounded-xl flex items-center justify-center
                      transition-all duration-200 transform hover:scale-110 active:scale-95 relative cursor-pointer
                      ${isCounted
                        ? 'bg-emerald-100 border-2 border-emerald-500 shadow-md ring-2 ring-emerald-400/40 scale-105'
                        : 'bg-white/90 border border-gray-200 hover:bg-emerald-50 shadow-sm'
                      }
                    `}
                    title={`Tap to count ${itemInfo.nameEng}`}
                  >
                    <Icon className={`w-4 h-4 sm:w-5 sm:h-5 ${itemInfo.iconClass}`} />
                    
                    {/* Count Bubble Badge */}
                    {isCounted && (
                      <span className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-emerald-700 text-white font-black text-[9px] flex items-center justify-center border border-white shadow animate-bounce">
                        {countNumber}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Group Total Sub-Label */}
            <div className="mt-2 pt-1 border-t border-emerald-200/60 w-full text-center">
              <span className="text-xs sm:text-sm font-black text-[#1B4332]">
                {count} <span className="text-[10px] font-bold text-gray-500">{itemInfo.nameKhmer}</span>
              </span>
            </div>
          </div>
        ))}

        {/* Plus / Equals Flow to Total Box */}
        <div className="flex flex-col items-center justify-center p-3 rounded-2xl border-2 border-amber-300 bg-amber-50/80 min-w-[85px] sm:min-w-[100px]">
          <span className="text-[10px] font-black text-amber-900 bg-amber-200 px-2 py-0.5 rounded-full border border-amber-400 mb-2">
            សរុប (Total)
          </span>

          <div className="w-10 h-10 sm:w-12 sm:h-12 bg-white rounded-2xl border-2 border-amber-400 border-dashed flex items-center justify-center shadow-inner my-auto">
            {currentTotalCount > 0 ? (
              <span className="text-xl sm:text-2xl font-black text-amber-800 flex items-center gap-0.5">
                {currentTotalCount}
                <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              </span>
            ) : (
              <span className="text-xl sm:text-2xl font-black text-amber-400">?</span>
            )}
          </div>

          {currentTotalCount > 0 ? (
            <button
              type="button"
              onClick={handleResetCount}
              className="text-[10px] font-black text-amber-900 hover:text-amber-950 mt-2 text-center flex items-center gap-1 bg-amber-200/80 px-2 py-0.5 rounded-lg border border-amber-400 transition-colors cursor-pointer shadow-2xs"
            >
              <RefreshCw className="w-2.5 h-2.5" /> រាប់ឡើងវិញ
            </button>
          ) : (
            <span className="text-[10px] font-bold text-amber-800 mt-2 text-center">
              រាប់ទាំងអស់
            </span>
          )}
        </div>
      </div>

    </div>
  );
}

