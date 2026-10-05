import { request } from './client';
import { TranslateResponseSchema } from './schemas';

// In-memory LRU cache for dynamic translations
const translationCache = new Map<string, string>();

/**
 * Translation API Client (for dynamic user text only)
 */
export const translateApi = {
  /**
   * Translate dynamic student text (e.g. user queries or dynamic hints).
   * Static UI strings should always come from static i18n JSON files.
   */
  async translateText(text: string, targetLang: 'km' | 'en' = 'km'): Promise<string> {
    if (!text || !text.trim()) return text;
    const cacheKey = `${targetLang}:${text.trim()}`;
    if (translationCache.has(cacheKey)) {
      return translationCache.get(cacheKey)!;
    }

    try {
      const raw = await request<unknown>('/translate', {
        method: 'POST',
        body: JSON.stringify({ text, target_lang: targetLang }),
        timeoutMs: 10_000,
      });

      const parsed = TranslateResponseSchema.safeParse(raw);
      const translated = parsed.success ? (parsed.data.translated_text || text) : text;
      translationCache.set(cacheKey, translated);
      return translated;
    } catch {
      return text;
    }
  },

  /**
   * Batch translate multiple dynamic texts.
   */
  async translateBatch(texts: string[], targetLang: 'km' | 'en' = 'km'): Promise<string[]> {
    if (!texts || texts.length === 0) return texts;

    try {
      const raw = await request<unknown>('/translate', {
        method: 'POST',
        body: JSON.stringify({ texts, target_lang: targetLang }),
        timeoutMs: 15_000,
      });

      const parsed = TranslateResponseSchema.safeParse(raw);
      if (parsed.success && parsed.data.translated_texts) {
        return parsed.data.translated_texts;
      }
      return texts;
    } catch {
      return texts;
    }
  },
};
