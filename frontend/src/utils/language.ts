import { Language } from '../types';

/**
 * Returns Khmer text if language is 'km', otherwise English text.
 */
export function t(_lang: Language, _khmer: string, english: string): string {
  return english;
}

/**
 * Strips bilingual parenthetical content when in single-language mode.
 * Example: "ការបូក ឬ ការគុណ (Addition or Multiplication)" -> "Addition or Multiplication"
 */
export function cleanBilingualOption(option: string, _lang?: Language): string {
  if (!option) return '';
  
  // Matches "Khmer text (English text)"
  const match = option.match(/^(.+?)\s*[\(\（]([^)\）]+)[\)\）]$/);
  if (match) {
    return match[2].trim();
  }
  return option;
}

/**
 * Returns user display name based on current language selection.
 * Example: "សុជា (Sochea)" -> km: "សុជា", en: "Sochea"
 */
export function getDisplayName(name: string, isKhmer: boolean = false): string {
  if (!name) return '';
  const match = name.match(/^(.+?)\s*[\(\（]([^)\）]+)[\)\）]$/);
  if (match) {
    return isKhmer ? match[1].trim() : match[2].trim();
  }
  return name;
}

