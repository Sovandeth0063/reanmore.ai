/**
 * VisualSpec schema types for deterministic SVG visual explanations.
 * Matches backend VisualSpec schema in Architecture v2.1 Section 8.1.
 */

export type VisualType =
  | 'ten_frame'
  | 'number_line'
  | 'base_ten_blocks'
  | 'array_grid'
  | 'fraction_bar'
  | 'bar_model';

export type VisualMode = 'current' | 'example' | 'reveal';

export interface VisualHighlight {
  from_frame?: number;
  to_frame?: number;
  move?: number;
  indices?: number[];
  color?: string;
}

export interface VisualSpec {
  schema_version: number;
  type: VisualType;
  mode: VisualMode;
  answer_safe: boolean;
  params: Record<string, any>;
  highlights?: VisualHighlight[];
  labels?: string[];
  alt_text: string;
}
