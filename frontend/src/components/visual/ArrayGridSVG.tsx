import React from 'react';
import { VisualSpec } from '../../types/visual';

interface ArrayGridSVGProps {
  spec: VisualSpec;
}

/**
 * Pure SVG Array Grid model for elementary multiplication tables.
 * Renders rows x columns of items with clear group brackets.
 */
export const ArrayGridSVG: React.FC<ArrayGridSVGProps> = ({ spec }) => {
  const rows = Math.max(1, Math.min(12, spec.params?.rows ?? 3));
  const cols = Math.max(1, Math.min(12, spec.params?.cols ?? 4));

  const svgWidth = 400;
  const svgHeight = 110;

  const dotSpacing = Math.min(22, 220 / Math.max(rows, cols));
  const dotRadius = Math.max(4, Math.min(8, dotSpacing * 0.35));

  const startX = 140;
  const startY = 25;

  return (
    <svg
      viewBox={`0 0 ${svgWidth} ${svgHeight}`}
      className="w-full max-w-lg h-auto mx-auto"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={spec.alt_text}
    >
      <defs>
        <radialGradient id="arrayDotGrad" cx="35%" cy="35%" r="65%">
          <stop offset="0%" stopColor="#818CF8" />
          <stop offset="100%" stopColor="#4F46E5" />
        </radialGradient>
      </defs>

      {/* Row Count Dimension Bracket */}
      <g className="row-bracket">
        <path
          d={`M ${startX - 15} ${startY} L ${startX - 22} ${startY} L ${startX - 22} ${startY + (rows - 1) * dotSpacing} L ${startX - 15} ${startY + (rows - 1) * dotSpacing}`}
          fill="none"
          stroke="#4F46E5"
          strokeWidth="1.5"
        />
        <text
          x={startX - 30}
          y={startY + ((rows - 1) * dotSpacing) / 2 + 4}
          textAnchor="end"
          fontSize="11"
          fontWeight="800"
          fill="#3730A3"
        >
          {rows} rows
        </text>
      </g>

      {/* Column Count Dimension Bracket */}
      <g className="col-bracket">
        <path
          d={`M ${startX} ${startY - 10} L ${startX} ${startY - 16} L ${startX + (cols - 1) * dotSpacing} ${startY - 16} L ${startX + (cols - 1) * dotSpacing} ${startY - 10}`}
          fill="none"
          stroke="#4F46E5"
          strokeWidth="1.5"
        />
        <text
          x={startX + ((cols - 1) * dotSpacing) / 2}
          y={startY - 20}
          textAnchor="middle"
          fontSize="10"
          fontWeight="800"
          fill="#3730A3"
        >
          {cols} in each row
        </text>
      </g>

      {/* Array Dots */}
      {Array.from({ length: rows }).map((_, rIdx) => {
        const cy = startY + rIdx * dotSpacing;
        return (
          <g key={rIdx} className="array-row">
            {Array.from({ length: cols }).map((_, cIdx) => {
              const cx = startX + cIdx * dotSpacing;
              return (
                <circle
                  key={cIdx}
                  cx={cx}
                  cy={cy}
                  r={dotRadius}
                  fill="url(#arrayDotGrad)"
                  stroke="#3730A3"
                  strokeWidth="1"
                  className="transition-transform duration-200 hover:scale-125"
                />
              );
            })}
          </g>
        );
      })}

      {/* Total Expression Badge */}
      <g>
        <rect
          x={startX + (cols * dotSpacing) + 25}
          y={startY + ((rows - 1) * dotSpacing) / 2 - 12}
          width="80"
          height="24"
          rx="12"
          fill="#EEF2FF"
          stroke="#6366F1"
          strokeWidth="1"
        />
        <text
          x={startX + (cols * dotSpacing) + 65}
          y={startY + ((rows - 1) * dotSpacing) / 2 + 4}
          textAnchor="middle"
          fontSize="11"
          fontWeight="800"
          fill="#4338CA"
        >
          {rows} × {cols}
        </text>
      </g>
    </svg>
  );
};

export default ArrayGridSVG;
