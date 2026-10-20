import React from 'react';
import { VisualSpec } from '../../types/visual';

interface FractionBarSVGProps {
  spec: VisualSpec;
}

/**
 * Pure SVG Fraction Bar model for equivalent fractions.
 * Renders partitioned horizontal bars with shaded slices and equivalence alignment.
 */
export const FractionBarSVG: React.FC<FractionBarSVGProps> = ({ spec }) => {
  const num = Math.max(0, spec.params?.numerator ?? 1);
  const den = Math.max(1, spec.params?.denominator ?? 2);
  const targetDen = spec.params?.target_denominator;

  const svgWidth = 420;
  const svgHeight = targetDen ? 120 : 85;

  const barWidth = 320;
  const barHeight = 28;
  const startX = 30;
  const startY1 = 20;
  const startY2 = 65;

  const sliceWidth1 = barWidth / den;

  return (
    <svg
      viewBox={`0 0 ${svgWidth} ${svgHeight}`}
      className="w-full max-w-lg h-auto mx-auto"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={spec.alt_text}
    >
      <defs>
        <linearGradient id="fractionShadeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#10B981" />
          <stop offset="100%" stopColor="#059669" />
        </linearGradient>
      </defs>

      {/* Bar 1 (Original Fraction) */}
      <g className="fraction-bar-1">
        {/* Outer Frame */}
        <rect
          x={startX}
          y={startY1}
          width={barWidth}
          height={barHeight}
          rx="6"
          fill="#F3F4F6"
          stroke="#065F46"
          strokeWidth="2"
        />

        {/* Shaded Slices */}
        {Array.from({ length: Math.min(num, den) }).map((_, idx) => (
          <rect
            key={idx}
            x={startX + idx * sliceWidth1}
            y={startY1}
            width={sliceWidth1}
            height={barHeight}
            fill="url(#fractionShadeGrad)"
            stroke="#047857"
            strokeWidth="1"
          />
        ))}

        {/* Partition Division Lines */}
        {Array.from({ length: den - 1 }).map((_, idx) => (
          <line
            key={idx}
            x1={startX + (idx + 1) * sliceWidth1}
            y1={startY1}
            x2={startX + (idx + 1) * sliceWidth1}
            y2={startY1 + barHeight}
            stroke="#065F46"
            strokeWidth="1.5"
          />
        ))}

        {/* Fraction Label Badge */}
        <text
          x={startX + barWidth + 30}
          y={startY1 + barHeight / 2 + 5}
          textAnchor="middle"
          fontSize="14"
          fontWeight="800"
          fill="#065F46"
        >
          {num}/{den}
        </text>
      </g>

      {/* Bar 2 (Target Comparison Fraction Bar if present) */}
      {targetDen && (
        <g className="fraction-bar-2">
          {(() => {
            const sliceWidth2 = barWidth / targetDen;
            const targetNum = Math.round((num / den) * targetDen);

            return (
              <>
                <rect
                  x={startX}
                  y={startY2}
                  width={barWidth}
                  height={barHeight}
                  rx="6"
                  fill="#F3F4F6"
                  stroke="#1E40AF"
                  strokeWidth="2"
                />

                {/* Shaded Slices for target bar */}
                {Array.from({ length: targetNum }).map((_, idx) => (
                  <rect
                    key={idx}
                    x={startX + idx * sliceWidth2}
                    y={startY2}
                    width={sliceWidth2}
                    height={barHeight}
                    fill="#60A5FA"
                    stroke="#1E40AF"
                    strokeWidth="1"
                  />
                ))}

                {/* Partition Lines */}
                {Array.from({ length: targetDen - 1 }).map((_, idx) => (
                  <line
                    key={idx}
                    x1={startX + (idx + 1) * sliceWidth2}
                    y1={startY2}
                    x2={startX + (idx + 1) * sliceWidth2}
                    y2={startY2 + barHeight}
                    stroke="#1E40AF"
                    strokeWidth="1"
                    strokeDasharray="2 2"
                  />
                ))}

                {/* Alignment comparison lines */}
                <line
                  x1={startX + num * sliceWidth1}
                  y1={startY1 + barHeight}
                  x2={startX + num * sliceWidth1}
                  y2={startY2}
                  stroke="#DC2626"
                  strokeWidth="1.5"
                  strokeDasharray="3 3"
                />

                {/* Target Fraction Badge */}
                <text
                  x={startX + barWidth + 30}
                  y={startY2 + barHeight / 2 + 5}
                  textAnchor="middle"
                  fontSize="14"
                  fontWeight="800"
                  fill="#1E40AF"
                >
                  ?/{targetDen}
                </text>
              </>
            );
          })()}
        </g>
      )}
    </svg>
  );
};

export default FractionBarSVG;
