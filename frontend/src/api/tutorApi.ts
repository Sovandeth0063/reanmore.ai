import { request } from './client';
import {
  QueryRequest,
  NavigateStepRequest,
  StepAnswerRequest,
  StepValidateRequest,
  StepValidateResponse,
  StepValidateResponseSchema,
  parseSocraticTurn,
  ParsedTurn,
} from './schemas';

/**
 * Socratic Tutoring & Stepper API Client
 */
export const tutorApi = {
  /**
   * Submit a student prompt or turn to the 4-Part Socratic Card LangGraph.
   * Keyed with an abort controller: rapid consecutive queries abort previous in-flight turns.
   */
  async query(payload: QueryRequest): Promise<ParsedTurn> {
    const raw = await request<unknown>('/query', {
      method: 'POST',
      body: JSON.stringify(payload),
      abortKey: 'socratic_turn',
      timeoutMs: 30_000,
    });

    const parsed = parseSocraticTurn(raw);
    if (!parsed) {
      throw {
        isApiError: true,
        status: 200,
        code: 'UNEXPECTED_RESPONSE',
        message: 'Server returned a malformed Socratic turn payload',
        i18nKey: 'errors.unexpected_response',
      };
    }
    return parsed;
  },

  /**
   * Navigate between steps (forward, back, or clicking specific step dots).
   */
  async navigateStep(payload: NavigateStepRequest): Promise<ParsedTurn> {
    const raw = await request<unknown>('/step/navigate', {
      method: 'POST',
      body: JSON.stringify(payload),
      timeoutMs: 15_000,
    });

    const parsed = parseSocraticTurn(raw);
    if (!parsed) {
      throw {
        isApiError: true,
        status: 200,
        code: 'UNEXPECTED_RESPONSE',
        message: 'Server returned a malformed step navigation payload',
        i18nKey: 'errors.unexpected_response',
      };
    }
    return parsed;
  },

  /**
   * Submit student's answer for the active step.
   * Mutating call: non-abortable, requires an Idempotency-Key UUID.
   */
  async submitStepAnswer(
    payload: StepAnswerRequest,
    idempotencyKey: string
  ): Promise<ParsedTurn> {
    const raw = await request<unknown>('/step/answer', {
      method: 'POST',
      body: JSON.stringify(payload),
      idempotencyKey,
      timeoutMs: 25_000,
      maxRetries: 2,
    });

    const parsed = parseSocraticTurn(raw);
    if (!parsed) {
      throw {
        isApiError: true,
        status: 200,
        code: 'UNEXPECTED_RESPONSE',
        message: 'Server returned a malformed step answer payload',
        i18nKey: 'errors.unexpected_response',
      };
    }

    // Fallback to getSession if stale_step arrives without a valid current_step
    if (parsed.outcome === 'stale_step' && (typeof parsed.current_step !== 'number' || parsed.current_step < 1)) {
      try {
        const session = await request<any>(`/session/${payload.session_id}`, {
          method: 'GET',
          timeoutMs: 8_000,
        });
        if (typeof session?.active_step_index === 'number') {
          parsed.current_step = session.active_step_index;
        } else if (typeof session?.problem_step_index === 'number') {
          parsed.current_step = session.problem_step_index;
        }
      } catch {
        // Fallback silently if session call fails
      }
    }

    return parsed;
  },

  /**
   * Server-side validation of math or science expressions without leaking answers to the client.
   */
  async validateStep(payload: StepValidateRequest): Promise<StepValidateResponse> {
    const raw = await request<unknown>('/step/validate', {
      method: 'POST',
      body: JSON.stringify(payload),
      timeoutMs: 10_000,
    });

    const result = StepValidateResponseSchema.safeParse(raw);
    if (result.success) {
      return result.data;
    }

    return { equivalent: false, error: 'Validation response schema mismatch' };
  },

  /**
   * Verify teacher/supervisor 6-digit PIN and obtain a single-use 60s resume token.
   */
  async verifySupervisor(supervisorId: string, pin: string): Promise<{ resume_token: string; expires_in: number }> {
    return request<{ resume_token: string; expires_in: number }>('/auth/supervisor/verify', {
      method: 'POST',
      body: JSON.stringify({ supervisor_id: supervisorId, pin }),
      timeoutMs: 10_000,
    });
  },

  /**
   * Supervisor resumes normal Socratic tutoring after Tier 2 crisis intervention.
   */
  async resumeTier2(
    sessionId: string,
    resumeToken: string,
    resolutionNote?: string
  ): Promise<ParsedTurn> {
    const raw = await request<unknown>('/socratic/resume', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        resume_token: resumeToken,
        resolution_note: resolutionNote || 'In-person counseling provided by teacher/supervisor',
      }),
      timeoutMs: 15_000,
    });

    const parsed = parseSocraticTurn(raw);
    if (!parsed) {
      throw {
        isApiError: true,
        status: 200,
        code: 'UNEXPECTED_RESPONSE',
        message: 'Server returned a malformed resume turn payload',
        i18nKey: 'errors.unexpected_response',
      };
    }
    return parsed;
  },
};
