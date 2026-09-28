/**
 * CalendarWidget.tsx
 * Renders an August 2026 calendar for time/date exercises.
 * Interactive (highlight target date) without revealing final answer.
 */
import { useState } from 'react';

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTH_NAME = 'August 2026';
// August 2026 starts on Saturday (day 6)
const START_DAY = 6;
const TOTAL_DAYS = 31;

interface Props {
  startDate?: number;
  allowCircle?: boolean;
}

export function CalendarWidget({ startDate, allowCircle }: Props) {
  const [selected, setSelected] = useState<number | null>(null);

  const cells: (number | null)[] = [];
  for (let i = 0; i < START_DAY; i++) cells.push(null);
  for (let d = 1; d <= TOTAL_DAYS; d++) cells.push(d);

  return (
    <div className="w-full bg-white/70 rounded-2xl border-2 border-amber-200 p-3 mb-3">
      <div className="text-xs font-bold text-amber-700 mb-2 text-center">📅 {MONTH_NAME}</div>
      <div className="grid grid-cols-7 gap-0.5">
        {DAYS.map(d => (
          <div key={d} className="text-center text-[10px] font-black text-amber-700 py-0.5">{d}</div>
        ))}
        {cells.map((day, i) => {
          const isStart = day === startDate;
            const isSelected = day === selected;
          const isToday = day === null;
          return (
            <div
              key={i}
              onClick={() => allowCircle && day && setSelected(day)}
              className={[
                'text-center text-xs py-1 rounded-lg font-bold transition-all',
                isToday ? '' : 'cursor-pointer',
                isStart ? 'bg-blue-400 text-white ring-2 ring-blue-600' :
                isSelected ? 'bg-amber-400 text-white ring-2 ring-amber-600' :
                'hover:bg-amber-100 text-gray-700'
              ].join(' ')}
            >
              {day || ''}
            </div>
          );
        })}
      </div>
      {allowCircle && (
        <p className="text-xs text-amber-600 mt-2 text-center">Tap a date to select it.</p>
      )}
      {startDate && (
        <p className="text-xs text-blue-600 mt-1 text-center">
          🔵 Starting date: <strong>{startDate}</strong>
        </p>
      )}
    </div>
  );
}

