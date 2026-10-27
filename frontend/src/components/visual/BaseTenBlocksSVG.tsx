import React from 'react';
import { VisualSpec } from '../../types/visual';

interface BaseTenBlocksSVGProps {
  spec: VisualSpec;
}

/**
 * Pure SVG Base-Ten Blocks model for 2-digit regrouping / borrowing.
 * Renders tens rods (amber) and unit ones cubes (indigo) with regrouping badges.
 */
export const BaseTenBlocksSVG: React.FC<BaseTenBlocksSVGProps> = ({ spec }) => {
  const tens = spec.params?.tens ?? 2;
  const ones = spec.params?.ones ?? 5;
  const isRegroup = spec.params?.regroup ?? false;

  const svgWidth = 420;
  const svgHeight = 110;

  // Dimensions
  const rodWidth = 12;
  const rodHeight = 60;
  const unitSize = 10;
  const rodSpacing = 16;
  const unitSpacing = 14;

  const tensStartX = 30;
  const tensStartY = 20;

  const onesStartX = Math.max(180, tensStartX + tens * rodSpacing + 30);
  const onesStartY = 20;

  return (
    <svg
      viewBox={`0 0 ${svgWidth} ${svgHeight}`}
      className="w-full max-w-lg h-auto mx-auto"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={spec.alt_text}
    >
      <defs>
        <linearGradient id="tenRodGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#F59E0B" />
          <stop offset="100%" stopColor="#D97706" />
        </linearGradient>
        <linearGradient id="unitCubeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6366F1" />
          <stop offset="100%" stopColor="#4F46E5" />
        </linearGradient>
      </defs>

      {/* Tens Section Container */}
      <g className="tens-column">
        <text
          x={tensStartX + (tens * rodSpacing) / 2}
          y="14"
          textAnchor="middle"
          fontSize="11"
          fontWeight="800"
          fill="#B45309"
        >
          {tens} Tens ({tens * 10})
        </text>

        {Array.from({ length: tens }).map((_, tIdx) => {
          const rx = tensStartX + tIdx * rodSpacing;
          return (
            <g key={tIdx} className="ten-rod">
              <rect
                x={rx}
                y={tensStartY}
                width={rodWidth}
                height={rodHeight}
                rx="2"
                fill="url(#tenRodGrad)"
                stroke="#B45309"
                strokeWidth="1"
              />
              {/* Internal segment lines indicating 10 units */}
              {Array.from({ length: 9 }).map((_, sIdx) => (
                <line
                  key={sIdx}
                  x1={rx}
                  y1={tensStartY + (sIdx + 1) * (rodHeight / 10)}
                  x2={rx + rodWidth}
                  y2={tensStartY + (sIdx + 1) * (rodHeight / 10)}
                  stroke="#92400E"
                  strokeWidth="0.8"
                />
              ))}
            </g>
          );
        })}
      </g>

      {/* Divider */}
      <line
        x1={onesStartX - 15}
        y1="15"
        x2={onesStartX - 15}
        y2="90"
        stroke="#E2E8F0"
        strokeWidth="1.5"
        strokeDasharray="3 3"
      />

      {/* Ones Section Container */}
      <g className="ones-column">
        <text
          x={onesStartX + 50}
          y="14"
          textAnchor="middle"
          fontSize="11"
          fontWeight="800"
          fill="#4338CA"
        >
          {ones} Ones
        </text>

        {Array.from({ length: ones }).map((_, oIdx) => {
          // Arrange units in 2 rows
          const row = Math.floor(oIdx / 8);
          const col = oIdx % 8;
          const ux = onesStartX + col * unitSpacing;
          const uy = onesStartY + 10 + row * (unitSize + 6);

          return (
            <rect
              key={oIdx}
              x={ux}
              y={uy}
              width={unitSize}
              height={unitSize}
              rx="2"
              fill="url(#unitCubeGrad)"
              stroke="#3730A3"
              strokeWidth="1"
            />
          );
        })}
      </g>

      {/* Regrouping Indicator Badge */}
      {isRegroup && (
        <g>
          <rect
            x={svgWidth / 2 - 60}
            y={svgHeight - 18}
            width="120"
            height="16"
            rx="8"
            fill="#FEF3C7"
            stroke="#D97706"
            strokeWidth="1"
          />
          <text
            x={svgWidth / 2}
            y={svgHeight - 6}
            textAnchor="middle"
            fontSize="9"
            fontWeight="800"
            fill="#92400E"
          >
            Trade 10 Ones ⇄ 1 Ten
          </text>
        </g>
      )}
    </svg>
  );
};

export default BaseTenBlocksSVG;
