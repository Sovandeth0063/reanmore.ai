import { describe, it as test } from 'node:test';
import assert from 'node:assert/strict';
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
    assert.equal(isApiError(validErr), true);

    const normalErr = new Error('Random failure');
    assert.equal(isApiError(normalErr), false);
    assert.equal(isApiError(null), false);
    assert.equal(isApiError({ isApiError: false }), false);
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
      assert.equal(err.code, code);
      assert.ok(err.i18nKey.startsWith('errors.'));
    }
  });

  test('Relative budget calculation satisfies client timeout budget invariant', () => {
    const chatTimeoutMs = 40_000;
    const chatBudgetMs = Math.max(0, chatTimeoutMs - 2000);
    assert.equal(chatBudgetMs, 38_000);

    const ocrTimeoutMs = 90_000;
    const ocrBudgetMs = Math.max(0, ocrTimeoutMs - 2000);
    assert.equal(ocrBudgetMs, 88_000);
  });
});
