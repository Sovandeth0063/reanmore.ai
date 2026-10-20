import React from 'react';
import { VisualSpec } from '../../types/visual';

interface TenFrameSVGProps {
  spec: VisualSpec;
}

/**
 * Pure SVG Ten-Frame model for addition within 20 / making a ten.
 * Renders 2x5 grids with interactive circular counters and transfer arrows.
 */
export const TenFrameSVG: React.FC<TenFrameSVGProps> = ({ spec }) => {
  const frames: { filled: number }[] = spec.params?.frames || [{ filled: 0 }];
  const colorScheme = spec.params?.color || 'apple';

  const counterColor = colorScheme === 'apple' ? '#EF4444' : '#6366F1';
  const counterHighlight = colorScheme === 'apple' ? '#FCA5A5' : '#A5B4FC';

  // Dimensions
  const frameWidth = 170;
  const frameHeight = 72;
  const cellWidth = frameWidth / 5;
  const cellHeight = frameHeight / 2;
  const totalSvgWidth = frames.length * (frameWidth + 30) + 20;

  return (
    <svg
      viewBox={`0 0 ${Math.max(400, totalSvgWidth)} 110`}
      className="w-full max-w-lg h-auto mx-auto"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={spec.alt_text}
    >
      <defs>
        <radialGradient id="counterGlow" cx="35%" cy="35%" r="65%">
          <stop offset="0%" stopColor={counterHighlight} />
          <stop offset="100%" stopColor={counterColor} />
        </radialGradient>
        <marker
          id="transferArrow"
          viewBox="0 0 10 10"
          refX="5"
          refY="5"
          markerWidth="6"
          markerHeight="6"
          orient="auto-start-reverse"
        >
          <path d="M 0 1 L 9 5 L 0 9 z" fill="#D97706" />
        </marker>
        <filter id="subtleShadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="1" dy="1.5" stdDeviation="1" floodColor="#000000" floodOpacity="0.15" />
        </filter>
      </defs>

      {frames.map((frame, frameIdx) => {
        const startX = 20 + frameIdx * (frameWidth + 35);
        const startY = 18;
        const filledCount = Math.max(0, Math.min(10, frame.filled || 0));

        return (
          <g key={frameIdx} className="ten-frame-group">
            {/* Outer Box */}
            <rect
              x={startX}
              y={startY}
              width={frameWidth}
              height={frameHeight}
              rx="10"
              fill="#FFFFFF"
              stroke="#065F46"
              strokeWidth="2.5"
              filter="url(#subtleShadow)"
            />

            {/* Grid dividers */}
            {/* Horizontal centerline */}
            <line
              x1={startX}
              y1={startY + cellHeight}
              x2={startX + frameWidth}
              y2={startY + cellHeight}
              stroke="#065F46"
              strokeWidth="1.5"
            />
            {/* Vertical column lines */}
            {[1, 2, 3, 4].map((col) => (
              <line
                key={col}
                x1={startX + col * cellWidth}
                y1={startY}
                x2={startX + col * cellWidth}
                y2={startY + frameHeight}
                stroke="#065F46"
                strokeWidth="1.5"
              />
            ))}

            {/* Counters */}
            {Array.from({ length: 10 }).map((_, cellIdx) => {
              const row = cellIdx < 5 ? 0 : 1;
              const col = cellIdx % 5;
              const cx = startX + col * cellWidth + cellWidth / 2;
              const cy = startY + row * cellHeight + cellHeight / 2;
              const isFilled = cellIdx < filledCount;

              if (!isFilled) {
                return (
                  <circle
                    key={cellIdx}
                    cx={cx}
                    cy={cy}
                    r="4"
                    fill="#E5E7EB"
                  />
                );
              }

              return (
                <circle
                  key={cellIdx}
                  cx={cx}
                  cy={cy}
                  r="13"
                  fill="url(#counterGlow)"
                  stroke="#991B1B"
                  strokeWidth="1"
                  filter="url(#subtleShadow)"
                  className="transition-transform duration-300 hover:scale-110"
                />
              );
            })}

            {/* Frame label badge */}
            <text
              x={startX + frameWidth / 2}
              y={startY + frameHeight + 16}
              textAnchor="middle"
              fontSize="11"
              fontWeight="700"
              fill="#065F46"
            >
              {filledCount} / 10
            </text>
          </g>
        );
      })}

      {/* Transfer Arrow Highlights */}
      {spec.highlights?.map((hl, hIdx) => {
        if (hl.from_frame === undefined || hl.to_frame === undefined) return null;
        const fromX = 20 + hl.from_frame * (frameWidth + 35) + 30;
        const toX = 20 + hl.to_frame * (frameWidth + 35) + frameWidth - 20;

        return (
          <g key={hIdx}>
            <path
              d={`M ${fromX} 14 Q ${(fromX + toX) / 2} -4 ${toX} 14`}
              fill="none"
              stroke="#D97706"
              strokeWidth="2.5"
              strokeDasharray="4 3"
              markerEnd="url(#transferArrow)"
            />
            {hl.move && (
              <text
                x={(fromX + toX) / 2}
                y="10"
                textAnchor="middle"
                fontSize="10"
                fontWeight="800"
                fill="#B45309"
              >
                Move {hl.move}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
};

export default TenFrameSVG;
