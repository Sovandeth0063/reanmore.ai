import React from 'react';
import { VisualSpec } from '../../types/visual';
import { TenFrameSVG } from './TenFrameSVG';
import { NumberLineSVG } from './NumberLineSVG';
import { BaseTenBlocksSVG } from './BaseTenBlocksSVG';
import { ArrayGridSVG } from './ArrayGridSVG';
import { FractionBarSVG } from './FractionBarSVG';
import { BarModelSVG } from './BarModelSVG';

interface VisualRendererProps {
  spec?: VisualSpec | null;
  className?: string;
}

/**
 * Pure SVG Visual Model Renderer component.
 * Dispatches to the 6 deterministic elementary visual models:
 * - ten_frame (Make-a-ten)
 * - number_line (Hop back to 10)
 * - base_ten_blocks (Regrouping / Borrowing)
 * - array_grid (Multiplication tables)
 * - fraction_bar (Equivalent fractions)
 * - bar_model (Part-whole word problems)
 */
export const VisualRenderer: React.FC<VisualRendererProps> = ({ spec, className = '' }) => {
  if (!spec || !spec.type) {
    return null;
  }

  const renderModelSvg = () => {
    switch (spec.type) {
      case 'ten_frame':
        return <TenFrameSVG spec={spec} />;
      case 'number_line':
        return <NumberLineSVG spec={spec} />;
      case 'base_ten_blocks':
        return <BaseTenBlocksSVG spec={spec} />;
      case 'array_grid':
        return <ArrayGridSVG spec={spec} />;
      case 'fraction_bar':
        return <FractionBarSVG spec={spec} />;
      case 'bar_model':
        return <BarModelSVG spec={spec} />;
      default:
        return (
          <div className="py-4 text-center text-xs text-amber-700">
            {spec.alt_text || 'Visual Model Scaffolding'}
          </div>
        );
    }
  };

  const modelFriendlyNames: Record<string, string> = {
    ten_frame: 'Ten-Frame (Make a 10)',
    number_line: 'Number Line (Count Back)',
    base_ten_blocks: 'Base-Ten Blocks (Regrouping)',
    array_grid: 'Array Grid (Equal Groups)',
    fraction_bar: 'Fraction Bar (Equivalence)',
    bar_model: 'Bar Model (Part-Whole)'
  };

  return (
    <div
      className={`visual-renderer-container p-3 sm:p-4 bg-gradient-to-b from-amber-50/70 to-emerald-50/40 rounded-2xl border-2 border-emerald-600/30 shadow-[2px_2px_0px_rgba(5,150,105,0.2)] my-3 transition-all ${className}`}
      role="img"
      aria-label={spec.alt_text}
    >
      {/* Header bar */}
      <div className="flex items-center justify-between flex-wrap gap-1.5 mb-2.5 pb-1.5 border-b border-emerald-600/15">
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-black text-emerald-900 tracking-wide uppercase">
            🎨 {modelFriendlyNames[spec.type] || spec.type.replace('_', ' ')}
          </span>
        </div>
        {spec.mode === 'example' && (
          <span className="bg-amber-100 text-amber-800 border border-amber-300 font-bold px-2 py-0.5 rounded-full text-[10px] tracking-wider uppercase">
            🍎 Parallel Worked Example
          </span>
        )}
        {spec.mode === 'reveal' && (
          <span className="bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold px-2 py-0.5 rounded-full text-[10px] tracking-wider uppercase">
            🎉 Solution Revealed
          </span>
        )}
      </div>

      {/* SVG Canvas */}
      <div className="flex justify-center items-center py-1 overflow-x-auto">
        {renderModelSvg()}
      </div>

      {/* Footer labels */}
      {spec.labels && spec.labels.length > 0 && (
        <div className="flex flex-wrap gap-1.5 justify-center mt-2.5 pt-2 border-t border-emerald-600/10 text-[11px] text-emerald-950 font-semibold">
          {spec.labels.map((label, idx) => (
            <span
              key={idx}
              className="bg-white/90 px-2.5 py-0.5 rounded-lg border border-emerald-200/80 shadow-xs"
            >
              {label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default VisualRenderer;
