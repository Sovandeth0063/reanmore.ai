/**
 * features.ts
 * Temporary feature flags for safe stepwise migration of API domains.
 *
 * NOTE: Security removals (client-side Gemini keys, client-side answer evaluation)
 * are permanent and non-reversible via flags.
 */

export const FEATURES = {
  /** Enables unified Socratic tutor API client */
  ENABLE_API_TUTOR: true,

  /** Defaults to false until BE-11 prompt-injection sanitizer is active */
  ENABLE_API_OCR: false,

  /** Enables CAS session sync and keepalive delta beacon */
  ENABLE_API_SESSION: true,

  /** Enables token-scoped stats and streak API */
  ENABLE_API_STATS: true,

  /** Dynamic translation path */
  ENABLE_API_TRANSLATE: true,
} as const;
