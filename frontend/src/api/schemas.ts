import { z } from 'zod';

/**
 * schemas.ts
 * Single source of truth for API payloads: TS types are inferred from these
 * schemas (no hand-written duplicate interfaces). Requires zod >= 3.20 (.catch).
 *
 * Socratic turns are parsed in two stages by parseSocraticTurn():
 *   1. Safety-critical core: outcome, text, crisisResource, version
 *   2. Presentation details: chips, stepWidget, rewards, completion flag
 * Each field is validated independently, so a bad stepWidget can never
 * discard the text or the crisis resource.
 */

/* ---------- Building blocks ---------- */

export const SocraticStepItemSchema = z.object({
  step_number: z.number().int().min(1),
  title: z.string().nullable().optional().transform((v) => v || ''),
  status: z.enum(['completed', 'in_progress', 'pending', 'locked', 'up_next']).catch('pending'),
  mission: z.string().nullable().optional(),
  clue: z.string().nullable().optional(),
  helpful_example: z.string().nullable().optional(),
  your_turn: z.string().nullable().optional(),
  student_answer: z.string().nullable().optional(),
  hints: z.array(z.string()).default([]),
  current_hint_level: z.number().int().default(0),
  expected_answer: z.string().nullable().optional(),
  concept: z.string().nullable().optional(),
  options: z.array(z.string()).nullable().optional(),
  visual_data: z.record(z.string(), z.any()).nullable().optional(),
}).passthrough();
export type SocraticStepItem = z.infer<typeof SocraticStepItemSchema>;

export const StepWidgetContainerSchema = z.object({
  total_steps: z.number().int().min(1),
  current_step_index: z.number().int().min(0).default(0),
  completed_steps: z.array(z.number().int()).default([]),
  steps: z.array(SocraticStepItemSchema),
  visual_data: z.record(z.string(), z.any()).nullable().optional(),
  quota_remaining: z.any().nullable().optional(),
  is_problem_complete: z.boolean().nullable().optional(),
  step_number: z.number().int().nullable().optional(),
  title: z.string().nullable().optional(),
  prompt: z.string().nullable().optional(),
}).passthrough();
export type StepWidgetContainer = z.infer<typeof StepWidgetContainerSchema>;

export const StepWidgetFlatSchema = z.object({
  step_number: z.number().int().min(1),
  total_steps: z.number().int().min(1),
  title: z.string(),
  prompt: z.string(),
  input_type: z.enum(['number', 'text', 'mcq', 'choice']).catch('text'),
  options: z.array(z.string()).nullable().optional(),
  hint_count: z.number().int().default(0),
  unlocked_hints: z.array(z.string()).default([]),
  grade_level: z.string().optional(),
  is_final_step: z.boolean().default(false),
  steps: z.array(z.any()).optional(),
}).passthrough();
export type StepWidgetFlat = z.infer<typeof StepWidgetFlatSchema>;

export const StepWidgetPayloadSchema = z.union([StepWidgetContainerSchema, StepWidgetFlatSchema]);
export type StepWidgetPayload = z.infer<typeof StepWidgetPayloadSchema>;

export const RewardsAwardedSchema = z.object({
  coins: z.number().int().min(0),
  streakUpdated: z.boolean(),
  badgeUnlocked: z.string().optional(),
});
export type RewardsAwarded = z.infer<typeof RewardsAwardedSchema>;

/** Server-authored and counselor-reviewed (Child Helpline Cambodia 1280). */
export const CrisisResourceSchema = z.object({
  title: z.string(),
  helplineKhmer: z.string(),
  instructions: z.string(),
});
export type CrisisResource = z.infer<typeof CrisisResourceSchema>;

export const KNOWN_OUTCOMES = [
  'normal',
  'safety_tier2_escalated',
  'safety_tier1_deflected',
  'intent_unclear',
  'stale_step',
] as const;

/** Unknown/new outcomes degrade to 'normal' without failing the parse. */
export const SocraticOutcomeSchema = z.enum(KNOWN_OUTCOMES).catch('normal');
export type SocraticOutcome = z.infer<typeof SocraticOutcomeSchema>;

/* ---------- Parsed Turn Contract ---------- */

export interface ParsedTurn {
  outcome: SocraticOutcome;
  textKhmer: string;
  textEng: string;
  version?: number | undefined;
  current_step?: number | undefined; // Populated when outcome === 'stale_step'
  /** Render whenever non-null, regardless of outcome. */
  crisisResource: CrisisResource | null;
  /**
   * True when outcome is tier-2 but the server resource is missing/malformed.
   * UI must show the bundled, counselor-reviewed local fallback.
   */
  needsCrisisFallback: boolean;
  suggestedChips: string[];
  stepWidget: StepWidgetPayload | null;
  rewardsAwarded: RewardsAwarded | null;
  isProblemComplete: boolean;
  /** True ONLY if presentation fields failed validation (never on unknown outcome). */
  degraded: boolean;
  /** Field paths + Zod codes only (never contains student content). */
  issues: string[];
}

/* ---------- Parser ---------- */

function parseField<S extends z.ZodTypeAny>(
  schema: S,
  value: unknown,
  path: string,
  issues: string[],
  fallback: z.infer<S>,
): z.infer<S> {
  const result = schema.safeParse(value);
  if (result.success) return result.data;
  for (const issue of result.error.issues) {
    const sub = issue.path.length ? `.${issue.path.join('.')}` : '';
    issues.push(`${path}${sub}:${issue.code}`);
  }
  return fallback;
}

/**
 * Returns null only when the payload is not an object at all
 * (client.ts then shows the generic `errors.unexpected_response` message).
 * Otherwise always returns something renderable.
 */
export function parseSocraticTurn(raw: unknown): ParsedTurn | null {
  if (typeof raw !== 'object' || raw === null || Array.isArray(raw)) return null;
  const r = raw as Record<string, unknown>;
  const issues: string[] = [];
  const telemetryAnomalies: string[] = [];

  // Stage 1: Safety-critical core
  let rawOutcome = r.outcome;
  if (!rawOutcome) {
    if (r.is_deflected || r.category === 'guardrail_violation') {
      rawOutcome = 'safety_tier1_deflected';
    } else {
      rawOutcome = 'normal';
    }
  }
  const outcome = SocraticOutcomeSchema.parse(rawOutcome);
  if (typeof r.outcome === 'string' && !KNOWN_OUTCOMES.includes(r.outcome as SocraticOutcome)) {
    // Cap anomaly string length to prevent memory amplification
    const safeVal = r.outcome.slice(0, 32);
    telemetryAnomalies.push(`outcome:unknown_value:${safeVal}`);
  }

  const rawKhmer = r.textKhmer || r.solution || r.formatted_markdown || r.text || '';
  const rawEng = r.textEng || r.solution || r.formatted_markdown || r.text || '';
  const textKhmer = parseField(z.string(), rawKhmer, 'textKhmer', issues, '');
  const textEng = parseField(z.string(), rawEng, 'textEng', issues, '');
  const version = parseField(z.number().int().optional(), r.version, 'version', issues, undefined);
  const rawStep = r.current_step ?? (typeof r.current_step_index === 'number' ? r.current_step_index + 1 : r.step_number);
  const current_step = parseField(z.number().int().optional(), rawStep, 'current_step', issues, undefined);
  const crisisResource = parseField(
    CrisisResourceSchema.nullable(),
    r.crisisResource ?? null,
    'crisisResource',
    issues,
    null,
  );
  const needsCrisisFallback = outcome === 'safety_tier2_escalated' && crisisResource === null;

  // Stage 2: Presentation details, each validated independently
  const suggestedChips = parseField(z.array(z.string()), r.suggestedChips ?? r.suggested_chips ?? [], 'suggestedChips', issues, []);
  const stepWidget = parseField(StepWidgetPayloadSchema.nullable(), r.stepWidget ?? r.step_widget ?? null, 'stepWidget', issues, null);
  const rewardsAwarded = parseField(RewardsAwardedSchema.nullable(), r.rewardsAwarded ?? null, 'rewardsAwarded', issues, null);
  const isProblemComplete = parseField(z.boolean(), r.isProblemComplete ?? r.is_problem_complete ?? false, 'isProblemComplete', issues, false);

  return {
    outcome,
    textKhmer,
    textEng,
    version,
    current_step,
    crisisResource,
    needsCrisisFallback,
    suggestedChips,
    stepWidget,
    rewardsAwarded,
    isProblemComplete,
    degraded: issues.length > 0,
    issues: [...issues, ...telemetryAnomalies],
  };
}

/* ---------- Query & Step Request Schemas ---------- */

export const QueryRequestSchema = z.object({
  query: z.string(),
  session_id: z.string().optional(),
  grade_level: z.string().default('grade_1_3'),
  language: z.string().default('en'),
  problem_context: z.record(z.string(), z.any()).nullable().optional(),
  active_step: z.record(z.string(), z.any()).nullable().optional(),
  worksheet_page: z.number().int().nullable().optional(),
  exercise_id: z.string().nullable().optional(),
});
export type QueryRequest = z.infer<typeof QueryRequestSchema>;

export const NavigateStepRequestSchema = z.object({
  session_id: z.string(),
  target_step_index: z.number().int().optional(),
  step_number: z.number().int().optional(),
  direction: z.enum(['next', 'back', 'prev']).optional(),
});
export type NavigateStepRequest = z.infer<typeof NavigateStepRequestSchema>;

export const StepAnswerRequestSchema = z.object({
  session_id: z.string(),
  step_number: z.number().int().min(1),
  student_answer: z.string(),
  is_correct: z.boolean().optional(),
});
export type StepAnswerRequest = z.infer<typeof StepAnswerRequestSchema>;

export const StepValidateRequestSchema = z.object({
  student_attempt: z.string(),
  expected_step: z.string(),
  subject: z.string().default('MATH'),
});
export type StepValidateRequest = z.infer<typeof StepValidateRequestSchema>;

export const StepValidateResponseSchema = z.object({
  equivalent: z.boolean().default(false),
  error: z.string().nullable().optional(),
});
export type StepValidateResponse = z.infer<typeof StepValidateResponseSchema>;

/* ---------- OCR Schemas ---------- */

export const OcrSubQuestionSchema = z.object({
  question_no: z.string().optional(),
  prompt: z.string().optional(),
  instructions: z.string().optional(),
  answer_type: z.string().optional(),
  options: z.array(z.string()).optional(),
  correct_answer: z.string().optional(),
});
export type OcrSubQuestion = z.infer<typeof OcrSubQuestionSchema>;

export const OcrExtractedProblemSchema = z.object({
  id: z.string().optional(),
  title: z.string().optional(),
  prompt: z.string().optional(),
  instructions: z.string().optional(),
  subject: z.enum(['math', 'science']).or(z.string()).optional(),
  grade: z.number().int().optional(),
  elements: z.array(z.union([z.string(), z.record(z.string(), z.any())])).optional(),
  sub_questions: z.array(OcrSubQuestionSchema).optional(),
  confidence: z.number().min(0).max(1).optional(),
});
export type OcrExtractedProblem = z.infer<typeof OcrExtractedProblemSchema>;

export const OcrExtractionResultSchema = z.object({
  status: z.string().optional(),
  success: z.boolean().default(true),
  confidence: z.number().min(0).max(1).optional(),
  ocr_confidence: z.number().min(0).max(1).optional(),
  raw_text: z.string().optional(),
  extracted_text: z.string().optional(),
  clean_question_text: z.string().optional(),
  exercises: z.array(z.any()).optional(),
  problems: z.array(OcrExtractedProblemSchema).optional(),
  sections: z.array(z.any()).optional(),
  pages: z.array(z.object({
    page_number: z.number().int(),
    confidence: z.number().optional(),
    text: z.string().optional(),
  })).optional(),
  error: z.string().optional(),
});
export type OcrExtractionResult = z.infer<typeof OcrExtractionResultSchema>;

export const SelectExerciseRequestSchema = z.object({
  session_id: z.string().optional(),
  exercise_id: z.string(),
  prompt: z.string(),
  grade_level: z.string().default('grade_1_3'),
  language: z.string().default('en'),
});
export type SelectExerciseRequest = z.infer<typeof SelectExerciseRequestSchema>;

/* ---------- Session & Stats Schemas ---------- */

export const UnsyncedMessageSchema = z.object({
  id: z.string(),
  sender: z.enum(['student', 'sayo']),
  textKhmer: z.string().optional(),
  textEng: z.string().optional(),
  timestamp: z.string().or(z.number()),
  problemId: z.string().optional(),
  stepWidget: StepWidgetPayloadSchema.nullable().optional(),
});
export type UnsyncedMessage = z.infer<typeof UnsyncedMessageSchema>;

export const SessionDeltaPayloadSchema = z.object({
  session_id: z.string(),
  expected_version: z.number().int().optional(),
  messages: z.array(UnsyncedMessageSchema),
  current_problem_id: z.string().optional(),
});
export type SessionDeltaPayload = z.infer<typeof SessionDeltaPayloadSchema>;

export const SessionSyncPayloadSchema = z.object({
  session_id: z.string(),
  expected_version: z.number().int().optional(),
  user_id: z.string().optional(),
  student_name: z.string().optional(),
  subject: z.string().optional(),
  grade: z.number().int().optional(),
  language: z.string().optional(),
  messages: z.array(z.any()),
  current_problem: z.any().optional(),
  active_step_index: z.number().int().optional(),
  completed_step_indices: z.array(z.number().int()).optional(),
  timestamp: z.number().optional(),
});
export type SessionSyncPayload = z.infer<typeof SessionSyncPayloadSchema>;

export const StudentStatsResponseSchema = z.object({
  total_sessions: z.number().int().default(0),
  completed_exercises: z.number().int().default(0),
  total_hints_used: z.number().int().default(0),
  current_streak_days: z.number().int().default(0),
  subject_distribution: z.object({
    math: z.number().int().default(0),
    science: z.number().int().default(0),
  }).default({ math: 0, science: 0 }),
  recent_activity: z.array(z.object({
    date: z.string(),
    exercises_count: z.number().int(),
  })).optional(),
});
export type StudentStatsResponse = z.infer<typeof StudentStatsResponseSchema>;

/* ---------- Health & Telemetry Schemas ---------- */

export const TelemetryEventSchema = z.object({
  event_type: z.enum([
    'session_started',
    'session_completed',
    'step_answered',
    'hint_requested',
    'tier2_escalation_handled',
    'exercise_switched',
  ]),
  analytics_id: z.string(),
  step_index: z.number().int().optional(),
  duration_ms: z.number().int().optional(),
  metadata: z.record(z.string(), z.union([z.string(), z.number(), z.boolean()])).optional(),
});
export type TelemetryEvent = z.infer<typeof TelemetryEventSchema>;

export const SystemHealthResponseSchema = z.object({
  status: z.enum(['ok', 'healthy', 'degraded', 'unhealthy']),
  version: z.string().optional(),
  services: z.record(z.string(), z.any()).optional(),
});
export type SystemHealthResponse = z.infer<typeof SystemHealthResponseSchema>;

export const TranslateRequestSchema = z.object({
  text: z.string().optional(),
  texts: z.array(z.string()).optional(),
  target_lang: z.string().default('km'),
});
export type TranslateRequest = z.infer<typeof TranslateRequestSchema>;

export const TranslateResponseSchema = z.object({
  translated_text: z.string().optional(),
  translated_texts: z.array(z.string()).optional(),
  source_lang: z.string().optional(),
  target_lang: z.string().optional(),
});
export type TranslateResponse = z.infer<typeof TranslateResponseSchema>;

/* ---------- LLM Controller Schemas (Admin Gated) ---------- */

export const LLMStatusResponseSchema = z.object({
  active_provider: z.string(),
  active_model: z.string(),
  active_tier: z.enum(['production', 'experimental', 'local']),
  temperature: z.number(),
  total_tokens_used: z.number().optional(),
  total_cost_usd: z.number().optional(),
  providers_available: z.array(z.string()),
});
export type LLMStatusResponse = z.infer<typeof LLMStatusResponseSchema>;
