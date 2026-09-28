/**
 * NumberLineWidget.tsx
 * Renders a number line with optional arrows/jumps.
 * Never reveals the answer — shows visual scaffold only.
 */

interface Props {
  start: number;
  target?: number;
  jumps?: number[];
  showJumps?: boolean;
}

export function NumberLineWidget({ start, target, jumps, showJumps }: Props) {
  const end = target ?? (jumps ? start + jumps.reduce((a, b) => a + b, 0) : start + 10);
  const min = Math.min(start, end, target ?? end);
  const max = Math.max(start, end, target ?? end);
  const range = max - min;
  const step = range <= 20 ? 1 : range <= 50 ? 5 : 10;

  const ticks: number[] = [];
  for (let v = Math.floor(min / step) * step; v <= Math.ceil(max / step) * step; v += step) {
    ticks.push(v);
  }

  const toPercent = (v: number) =>
    ((v - ticks[0]) / (ticks[ticks.length - 1] - ticks[0])) * 100;

  return (
    <div className="w-full bg-white/70 rounded-2xl border-2 border-emerald-200 p-4 mb-3">
      <div className="text-xs font-bold text-emerald-700 mb-3">📏 Number Line</div>
      <div className="relative h-12 mx-4">
        {/* baseline */}
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-emerald-400 rounded" />

        {/* ticks */}
        {ticks.map(v => (
          <div
            key={v}
            className="absolute flex flex-col items-center"
            style={{ left: `${toPercent(v)}%`, transform: 'translateX(-50%)' }}
          >
            <div className="w-0.5 h-3 bg-emerald-500" style={{ marginTop: '14px' }} />
            <span className="text-[10px] font-bold text-emerald-700 mt-0.5">{v}</span>
          </div>
        ))}

        {/* start dot */}
        <div
          className="absolute w-4 h-4 bg-blue-500 rounded-full border-2 border-white shadow"
          style={{ left: `${toPercent(start)}%`, top: '50%', transform: 'translate(-50%, -50%)' }}
          title={`Start: ${start}`}
        />

        {/* target dot (hidden — question mark) */}
        {target !== undefined && (
          <div
            className="absolute w-5 h-5 bg-amber-400 rounded-full border-2 border-white shadow flex items-center justify-center"
            style={{ left: `${toPercent(target)}%`, top: '50%', transform: 'translate(-50%, -50%)' }}
          >
            <span className="text-[10px] font-black text-amber-900">?</span>
          </div>
        )}

        {/* jump arrows */}
        {showJumps && jumps && jumps.map((j, i) => {
          const from = start + jumps.slice(0, i).reduce((a, b) => a + b, 0);
          const to = from + j;
          const midPct = (toPercent(from) + toPercent(to)) / 2;
          return (
            <div
              key={i}
              className="absolute text-[10px] font-bold text-indigo-600"
              style={{ left: `${midPct}%`, top: '0px', transform: 'translateX(-50%)' }}
            >
              {j > 0 ? `+${j}` : j}
            </div>
          );
        })}
      </div>
      <p className="text-xs text-emerald-600 mt-2 text-center">
        Start at <strong>{start}</strong>. Where do you need to reach?
      </p>
    </div>
  );
}

