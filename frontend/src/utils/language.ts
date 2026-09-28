import { Language } from '../types';

/**
 * Returns Khmer text if language is 'km', otherwise English text.
 */
export function t(lang: Language, khmer: string, english: string): string {
  return lang === 'km' ? khmer : english;
}

/**
 * Strips bilingual parenthetical content when in single-language mode.
 * Example: "ការបូក ឬ ការគុណ (Addition or Multiplication)"
 *   -> km: "ការបូក ឬ ការគុណ"
 *   -> en: "Addition or Multiplication"
 */
export function cleanBilingualOption(option: string, lang: Language): string {
  if (!option) return '';
  
  // Matches "Khmer text (English text)"
  const match = option.match(/^(.+?)\s*[\(\（]([^)\）]+)[\)\）]$/);
  if (match) {
    return lang === 'km' ? match[1].trim() : match[2].trim();
  }
  return option;
}

/**
 * Returns user display name based on current language selection.
 * Example: "សុជា (Sochea)" -> km: "សុជា", en: "Sochea"
 */
export function getDisplayName(name: string, isKhmer: boolean): string {
  if (!name) return '';
  const match = name.match(/^(.+?)\s*[\(\（]([^)\）]+)[\)\）]$/);
  if (match) {
    return isKhmer ? match[1].trim() : match[2].trim();
  }
  return name;
}

