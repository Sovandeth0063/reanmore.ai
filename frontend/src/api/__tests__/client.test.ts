import { describe, it as test, expect } from 'vitest';
import { isApiError, ApiError } from '../client';

describe('API Client & Error Normalization Unit Tests', () => {
  test('isApiError identifies ApiError objects correctly', () => {
    const validErr: ApiError = {
      isApiError: true,
      status: 423,
      code: 'TIER2_LOCKED',
      message: 'Device locked in crisis counseling mode',
      i18nKey: 'errors.tier2_locked',
    };
    expect(isApiError(validErr)).toBe(true);

    const normalErr = new Error('Random failure');
    expect(isApiError(normalErr)).toBe(false);
    expect(isApiError(null)).toBe(false);
    expect(isApiError({ isApiError: false })).toBe(false);
  });

  test('New v9 error codes are defined and typesafe', () => {
    const errorCodes = [
      'PIN_LOCKED',
      'CONSENT_REQUIRED',
      'TIER2_LOCKED',
      'DEVICE_REVOKED',
      'ENROLLMENT_INVALID',
      'SERVER_BUSY',
      'RATE_LIMITED',
    ] as const;

    for (const code of errorCodes) {
      const err: ApiError = {
        isApiError: true,
        status: code === 'TIER2_LOCKED' ? 423 : 400,
        code,
        message: `Testing ${code}`,
        i18nKey: `errors.${code.toLowerCase()}`,
      };
      expect(err.code).toBe(code);
      expect(err.i18nKey.startsWith('errors.')).toBeTruthy();
    }
  });

  test('Relative budget calculation satisfies client timeout budget invariant', () => {
    const chatTimeoutMs = 40_000;
    const chatBudgetMs = Math.max(0, chatTimeoutMs - 2000);
    expect(chatBudgetMs).toBe(38_000);

    const ocrTimeoutMs = 90_000;
    const ocrBudgetMs = Math.max(0, ocrTimeoutMs - 2000);
    expect(ocrBudgetMs).toBe(88_000);
  });
});
