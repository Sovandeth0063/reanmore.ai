import React from 'react';
import { VisualSpec } from '../../types/visual';

interface NumberLineSVGProps {
  spec: VisualSpec;
}

/**
 * Pure SVG Number Line model for subtraction within 20 / hopping back to 10.
 * Renders axis ticks, quadratic Bézier jump arcs, and target milestone badges.
 */
export const NumberLineSVG: React.FC<NumberLineSVGProps> = ({ spec }) => {
  const start = spec.params?.start ?? 14;
  const hops: { from: number; to: number; label?: string }[] = spec.params?.hops || [];

  // Determine span of the number line
  const allPoints = [start, ...hops.map((h) => h.from), ...hops.map((h) => h.to)];
  const minVal = Math.max(0, Math.min(...allPoints) - 2);
  const maxVal = Math.max(...allPoints) + 2;
  const range = maxVal - minVal || 10;

  // Viewport
  const svgWidth = 440;
  const svgHeight = 110;
  const paddingX = 35;
  const axisY = 75;
  const usableWidth = svgWidth - paddingX * 2;

  const getX = (val: number) => {
    return paddingX + ((val - minVal) / range) * usableWidth;
  };

  // Generate tick values
  const ticks: number[] = [];
  for (let v = minVal; v <= maxVal; v += (range > 15 ? 2 : 1)) {
    ticks.push(v);
  }

  return (
    <svg
      viewBox={`0 0 ${svgWidth} ${svgHeight}`}
      className="w-full max-w-lg h-auto mx-auto"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={spec.alt_text}
    >
      <defs>
        <marker
          id="arrowHead"
          viewBox="0 0 10 10"
          refX="5"
          refY="5"
          markerWidth="5"
          markerHeight="5"
          orient="auto-start-reverse"
        >
          <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#1E3A8A" />
        </marker>
        <marker
          id="hopArrow"
          viewBox="0 0 10 10"
          refX="5"
          refY="5"
          markerWidth="6"
          markerHeight="6"
          orient="auto-start-reverse"
        >
          <path d="M 0 1 L 9 5 L 0 9 z" fill="#DC2626" />
        </marker>
      </defs>

      {/* Main Axis Line */}
      <line
        x1={paddingX - 15}
        y1={axisY}
        x2={svgWidth - paddingX + 15}
        y2={axisY}
        stroke="#1E3A8A"
        strokeWidth="2.5"
        strokeLinecap="round"
        markerEnd="url(#arrowHead)"
        markerStart="url(#arrowHead)"
      />

      {/* Ticks and Number Labels */}
      {ticks.map((tVal) => {
        const x = getX(tVal);
        const isTen = tVal === 10;
        const isStart = tVal === start;

        return (
          <g key={tVal}>
            <line
              x1={x}
              y1={axisY - (isTen || isStart ? 8 : 5)}
              x2={x}
              y2={axisY + (isTen || isStart ? 8 : 5)}
              stroke={isTen ? '#16A34A' : '#1E3A8A'}
              strokeWidth={isTen || isStart ? '2.5' : '1.5'}
            />
            <text
              x={x}
              y={axisY + 20}
              textAnchor="middle"
              fontSize={isTen || isStart ? '12' : '10'}
              fontWeight={isTen || isStart ? '800' : '600'}
              fill={isTen ? '#16A34A' : '#1E3A8A'}
            >
              {tVal}
            </text>
            {isTen && (
              <circle cx={x} cy={axisY} r="4" fill="#16A34A" />
            )}
          </g>
        );
      })}

      {/* Jump Arcs */}
      {hops.map((hop, hIdx) => {
        const fromX = getX(hop.from);
        const toX = getX(hop.to);
        const midX = (fromX + toX) / 2;
        const arcHeight = Math.min(42, Math.abs(fromX - toX) * 0.45);
        const peakY = axisY - arcHeight;

        return (
          <g key={hIdx}>
            {/* Arc Path */}
            <path
              d={`M ${fromX} ${axisY - 2} Q ${midX} ${peakY - 10} ${toX} ${axisY - 2}`}
              fill="none"
              stroke="#DC2626"
              strokeWidth="2.5"
              markerEnd="url(#hopArrow)"
            />

            {/* Hop Label */}
            {hop.label && (
              <g>
                <rect
                  x={midX - 16}
                  y={peakY - 24}
                  width="32"
                  height="16"
                  rx="6"
                  fill="#FEE2E2"
                  stroke="#DC2626"
                  strokeWidth="1"
                />
                <text
                  x={midX}
                  y={peakY - 12}
                  textAnchor="middle"
                  fontSize="10"
                  fontWeight="800"
                  fill="#991B1B"
                >
                  {hop.label}
                </text>
              </g>
            )}
          </g>
        );
      })}
    </svg>
  );
};

export default NumberLineSVG;
