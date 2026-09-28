/**
 * PlaceValueWidget.tsx
 * Shows place-value blocks (hundreds, tens, ones) without revealing the answer.
 */

interface Props {
  number: number;
}

export function PlaceValueWidget({ number }: Props) {
  const hundreds = Math.floor(number / 100);
  const tens = Math.floor((number % 100) / 10);
  const ones = number % 10;

  return (
    <div className="w-full bg-white/70 rounded-2xl border-2 border-purple-200 p-4 mb-3">
      <div className="text-xs font-bold text-purple-700 mb-3">🧱 Place Value — {number}</div>
      <div className="flex gap-3 justify-center flex-wrap">
        <div className="flex flex-col items-center gap-1">
          <span className="text-xs font-bold text-purple-600">Hundreds</span>
          <div className="flex flex-wrap gap-0.5 max-w-[80px] justify-center">
            {Array.from({ length: hundreds }).map((_, i) => (
              <div key={i} className="w-8 h-8 bg-purple-400 rounded border border-purple-600 text-white text-[10px] flex items-center justify-center font-black">100</div>
            ))}
            {hundreds === 0 && <div className="w-8 h-8 bg-gray-100 rounded border border-gray-300 text-gray-400 text-[10px] flex items-center justify-center">0</div>}
          </div>
          <span className="text-lg font-black text-purple-700">{hundreds}</span>
        </div>
        <div className="flex flex-col items-center gap-1">
          <span className="text-xs font-bold text-blue-600">Tens</span>
          <div className="flex flex-col gap-0.5 items-center">
            {Array.from({ length: Math.min(tens, 9) }).map((_, i) => (
              <div key={i} className="w-4 h-8 bg-blue-400 rounded border border-blue-600" />
            ))}
            {tens === 0 && <div className="w-4 h-8 bg-gray-100 rounded border border-gray-300" />}
          </div>
          <span className="text-lg font-black text-blue-700">{tens}</span>
        </div>
        <div className="flex flex-col items-center gap-1">
          <span className="text-xs font-bold text-green-600">Ones</span>
          <div className="flex flex-wrap gap-0.5 max-w-[40px] justify-center">
            {Array.from({ length: Math.min(ones, 9) }).map((_, i) => (
              <div key={i} className="w-3.5 h-3.5 bg-green-400 rounded-full border border-green-600" />
            ))}
            {ones === 0 && <div className="w-3.5 h-3.5 bg-gray-100 rounded-full border border-gray-300" />}
          </div>
          <span className="text-lg font-black text-green-700">{ones}</span>
        </div>
      </div>
      <p className="text-xs text-purple-600 mt-3 text-center">
        What are the hundreds, tens, and ones in <strong>{number}</strong>?
      </p>
    </div>
  );
}

