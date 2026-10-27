/**
 * API Data Contracts & Types
 * Matching FastAPI / Pydantic schemas across Orchestrator, OCR, and Microservices.
 */

// ─────────────────────────────────────────────────────────────────────────────
// Socratic Tutoring & Stepper Payload Types
// ─────────────────────────────────────────────────────────────────────────────

export interface SocraticCard {
  card_type: 'observation' | 'question' | 'encouragement' | 'hint';
  title?: string;
  content: string;
  options?: string[];
  metadata?: Record<string, any>;
}

export interface SocraticStepItem {
  step_number: number;
  title: string;
  status: 'completed' | 'in_progress' | 'pending' | 'locked' | 'up_next';
  mission?: string;
  clue?: string;
  helpful_example?: string;
  your_turn?: string;
  student_answer?: string | null;
  hints?: string[];
  current_hint_level?: number;
  expected_answer?: string | null;
  concept?: string | null;
  options?: string[];
  visual_data?: Record<string, any> | null;
}

export interface StepWidgetPayload {
  // Container structure (multi-step workflow)
  total_steps: number;
  current_step_index?: number;
  completed_steps?: number[];
  steps?: SocraticStepItem[];
  // Flat single-step properties (for backwards compatibility)
  step_number?: number;
  title?: string;
  prompt?: string;
  input_type?: 'number' | 'text' | 'mcq' | 'choice';
  options?: string[];
  hint_count?: number;
  unlocked_hints?: string[];
  grade_level?: string;
  is_final_step?: boolean;
  visual_data?: Record<string, any> | null;
}

export interface QueryRequest {
  query: string;
  session_id?: string;
  grade_level?: 'grade_1_3' | 'grade_4_6' | string;
  language?: 'km' | 'en' | string;
  problem_context?: Record<string, any> | null;
  active_step?: Record<string, any> | null;
  worksheet_page?: number | null;
  exercise_id?: string | null;
}

export interface QueryResponse {
  category: string;
  solution: string;
  steps: Array<Record<string, any>>;
  source: string;
  current_step_index: number;
  hint_count: number;
  practice_mode: boolean;
  grade_level: string;
  session_id: string;
  language: string;
  step_widget?: StepWidgetPayload | null;
  formatted_markdown?: string | null;
  is_problem_complete?: boolean;
  is_deflected?: boolean;
  pipeline_trace?: Record<string, any> | null;
  suggested_chips?: string[];
  degrade_to_tap_first?: boolean;
}

export interface NavigateStepRequest {
  session_id: string;
  target_step_index?: number;
  step_number?: number;
  direction?: 'next' | 'back' | 'prev';
}

export interface NavigateStepResponse {
  status: string;
  session_id: string;
  current_step_index: number;
  step_widget?: StepWidgetPayload;
  message?: string;
}

export interface StepAnswerRequest {
  session_id: string;
  step_number: number;
  student_answer: string;
  is_correct?: boolean;
}

export interface StepAnswerResponse {
  status: string;
  is_correct: boolean;
  session_id: string;
  step_number: number;
  feedback?: string;
  feedback_khmer?: string;
  next_step_widget?: StepWidgetPayload;
  is_problem_complete?: boolean;
}

export interface StepValidateRequest {
  student_attempt: string;
  expected_step: string;
  subject?: 'math' | 'science' | string;
}

export interface StepValidateResponse {
  is_correct: boolean;
  message?: string;
  equivalence_score?: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// OCR & Worksheet Types
// ─────────────────────────────────────────────────────────────────────────────

export interface OcrSubQuestion {
  question_no?: string;
  prompt?: string;
  instructions?: string;
  answer_type?: string;
  options?: string[];
  correct_answer?: string;
}

export interface OcrExtractedProblem {
  id?: string;
  title?: string;
  prompt?: string;
  instructions?: string;
  subject?: 'math' | 'science' | string;
  grade?: number;
  elements?: Array<string | { text?: string; type?: string }>;
  sub_questions?: OcrSubQuestion[];
  confidence?: number;
}

export interface OcrExtractionResult {
  status?: string;
  success?: boolean;
  confidence?: number;
  ocr_confidence?: number;
  raw_text?: string;
  extracted_text?: string;
  clean_question_text?: string;
  exercises?: any[];
  problems?: OcrExtractedProblem[];
  sections?: any[];
  pages?: Array<{
    page_number: number;
    confidence?: number;
    text?: string;
  }>;
  error?: string;
}

export interface SelectExerciseRequest {
  session_id?: string;
  exercise_id: string;
  prompt: string;
  grade_level?: 'grade_1_3' | 'grade_4_6' | string;
  language?: 'km' | 'en' | string;
}

// ─────────────────────────────────────────────────────────────────────────────
// LLM Engine Controller Types
// ─────────────────────────────────────────────────────────────────────────────

export interface LLMStatusResponse {
  active_provider: string;
  active_model: string;
  active_tier: 'production' | 'experimental' | 'local';
  temperature: number;
  total_tokens_used?: number;
  total_cost_usd?: number;
  providers_available: string[];
}

export interface LLMModelInfo {
  id: string;
  name: string;
  provider: string;
  tier: 'production' | 'experimental' | 'local';
  input_cost_per_1m?: number;
  output_cost_per_1m?: number;
  context_window?: number;
  recommended_for?: string;
}

export interface SwitchProviderRequest {
  provider: string;
  model?: string;
}

export interface SetModelRequest {
  model: string;
}

export interface TestInferenceRequest {
  prompt: string;
  system_instruction?: string;
  provider?: string;
  model?: string;
}

export interface TestInferenceResponse {
  response: string;
  provider: string;
  model: string;
  latency_ms: number;
  tokens_prompt?: number;
  tokens_completion?: number;
  cost_usd?: number;
}

// ─────────────────────────────────────────────────────────────────────────────
// Session, Telemetry, and Health Types
// ─────────────────────────────────────────────────────────────────────────────

export interface SessionSyncPayload {
  session_id: string;
  user_id?: string;
  student_name?: string;
  subject?: string;
  grade?: number;
  language?: string;
  messages: any[];
  current_problem?: any;
  active_step_index?: number;
  completed_step_indices?: number[];
  timestamp?: number;
}

export interface StudentStatsResponse {
  total_sessions: number;
  completed_exercises: number;
  total_hints_used: number;
  current_streak_days: number;
  subject_distribution: {
    math: number;
    science: number;
  };
  recent_activity?: Array<{
    date: string;
    exercises_count: number;
  }>;
}

export interface ServiceHealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  response_time_ms: number;
  last_checked: string;
  circuit_breaker_state?: 'closed' | 'open' | 'half_open';
}

export interface SystemHealthResponse {
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  readiness: 'ready' | 'not_ready';
  services: Record<string, ServiceHealthStatus>;
}

export interface TranslateRequest {
  text?: string;
  texts?: string[];
  target_language?: 'km' | 'en' | string;
  target_lang?: 'km' | 'en' | string;
}

export interface TranslateResponse {
  translated_text?: string;
  translated_texts?: string[];
  source_lang?: string;
  target_lang?: string;
}
