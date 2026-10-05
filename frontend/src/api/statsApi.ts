import { request } from './client';
import {
  StudentStatsResponse,
  StudentStatsResponseSchema,
} from './schemas';

/**
 * Gamification, Daily Streaks, and Parent Analytics API Client
 */
export const statsApi = {
  /**
   * Fetch student stats (exercises completed, hints used, subject distribution).
   * Supports optional parent JWT token when accessing via Parent Report.
   */
  async getStats(parentToken?: string): Promise<StudentStatsResponse> {
    const raw = await request<unknown>('/stats', {
      method: 'GET',
      timeoutMs: 10_000,
      token: parentToken,
    });

    const parsed = StudentStatsResponseSchema.safeParse(raw);
    if (parsed.success) {
      return parsed.data;
    }

    return {
      total_sessions: 0,
      completed_exercises: 0,
      total_hints_used: 0,
      current_streak_days: 0,
      subject_distribution: { math: 0, science: 0 },
    };
  },

  /**
   * Fetch current daily streak data.
   */
  async getStreak(): Promise<{ streak_days: number; last_active_date?: string }> {
    return request<{ streak_days: number; last_active_date?: string }>('/streak', {
      method: 'GET',
      timeoutMs: 10_000,
    });
  },

  /**
   * Verify parent PIN to obtain a signed Parent JWT token.
   */
  async verifyParentPin(pin: string): Promise<{ success: boolean; token?: string; error?: string }> {
    return request<{ success: boolean; token?: string; error?: string }>('/auth/parent/verify', {
      method: 'POST',
      body: JSON.stringify({ pin }),
      timeoutMs: 8_000,
    });
  },

  /**
   * Setup initial parent PIN.
   */
  async setupParentPin(pin: string): Promise<{ success: boolean; error?: string }> {
    return request<{ success: boolean; error?: string }>('/auth/parent/setup', {
      method: 'POST',
      body: JSON.stringify({ pin }),
      timeoutMs: 8_000,
    });
  },
};
