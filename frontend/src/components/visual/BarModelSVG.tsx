import React from 'react';
import { VisualSpec } from '../../types/visual';

interface BarModelSVGProps {
  spec: VisualSpec;
}

/**
 * Pure SVG Singapore Part-Whole Bar Model for word problems.
 * Compares whole (total) with known and unknown (?) parts.
 */
export const BarModelSVG: React.FC<BarModelSVGProps> = ({ spec }) => {
  const whole = spec.params?.whole;
  const parts: (number | null)[] = spec.params?.parts || [null, null];
  const itemLabel = spec.params?.item_label || 'items';

  const svgWidth = 420;
  const svgHeight = 110;

  const barWidth = 320;
  const barHeight = 32;
  const startX = 50;
  const startY = 45;

  // Calculate proportional widths of parts if known, otherwise split evenly
  const knownSum = parts.reduce<number>((acc, p) => acc + (p ?? 0), 0);
  const effectiveWhole = whole ?? (knownSum > 0 ? knownSum : 10);

  let currentX = startX;

  return (
    <svg
      viewBox={`0 0 ${svgWidth} ${svgHeight}`}
      className="w-full max-w-lg h-auto mx-auto"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={spec.alt_text}
    >
      <defs>
        <linearGradient id="knownPartGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#3B82F6" />
          <stop offset="100%" stopColor="#1D4ED8" />
        </linearGradient>
      </defs>

      {/* Top Bracket for Whole / Total */}
      <g className="total-bracket">
        <path
          d={`M ${startX} 28 L ${startX} 22 L ${startX + barWidth} 22 L ${startX + barWidth} 28`}
          fill="none"
          stroke="#1E3A8A"
          strokeWidth="2"
        />
        <text
          x={startX + barWidth / 2}
          y="16"
          textAnchor="middle"
          fontSize="12"
          fontWeight="800"
          fill="#1E3A8A"
        >
          {whole !== null && whole !== undefined ? `Total: ${whole} ${itemLabel}` : `Total: ? ${itemLabel}`}
        </text>
      </g>

      {/* Partitioned Part-Whole Tape */}
      {parts.map((partVal, pIdx) => {
        // Proportion
        const partProportion = partVal !== null && effectiveWhole > 0
          ? Math.max(0.2, Math.min(0.8, partVal / effectiveWhole))
          : 1 / parts.length;
        const partW = pIdx === parts.length - 1 ? (startX + barWidth - currentX) : barWidth * partProportion;
        const thisX = currentX;
        currentX += partW;

        const isUnknown = partVal === null || partVal === undefined;

        return (
          <g key={pIdx} className="bar-part">
            {isUnknown ? (
              // Unknown part: amber dashed box with ?
              <g>
                <rect
                  x={thisX}
                  y={startY}
                  width={partW}
                  height={barHeight}
                  rx="4"
                  fill="#FEF3C7"
                  stroke="#D97706"
                  strokeWidth="2"
                  strokeDasharray="4 3"
                />
                <text
                  x={thisX + partW / 2}
                  y={startY + barHeight / 2 + 5}
                  textAnchor="middle"
                  fontSize="16"
                  fontWeight="900"
                  fill="#B45309"
                >
                  ?
                </text>
                <text
                  x={thisX + partW / 2}
                  y={startY + barHeight + 16}
                  textAnchor="middle"
                  fontSize="10"
                  fontWeight="700"
                  fill="#92400E"
                >
                  What's left?
                </text>
              </g>
            ) : (
              // Known part: blue filled box with quantity
              <g>
                <rect
                  x={thisX}
                  y={startY}
                  width={partW}
                  height={barHeight}
                  rx="4"
                  fill="url(#knownPartGrad)"
                  stroke="#1E40AF"
                  strokeWidth="1.5"
                />
                <text
                  x={thisX + partW / 2}
                  y={startY + barHeight / 2 + 5}
                  textAnchor="middle"
                  fontSize="13"
                  fontWeight="800"
                  fill="#FFFFFF"
                >
                  {partVal}
                </text>
                <text
                  x={thisX + partW / 2}
                  y={startY + barHeight + 16}
                  textAnchor="middle"
                  fontSize="10"
                  fontWeight="600"
                  fill="#1E40AF"
                >
                  Part {pIdx + 1}
                </text>
              </g>
            )}
          </g>
        );
      })}
    </svg>
  );
};

export default BarModelSVG;
