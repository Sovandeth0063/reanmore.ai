/**
 * File: frontend/src/services/llmControllerService.ts
 * Description: Client API service for communicating with the orchestrator LLM Controller.
 *              Allows runtime model and provider switching (Gemini, Ollama, Mock, OpenAI)
 *              with zero frontend reload.
 */

export interface ProviderModelInfo {
  name: string;
  provider: string;
  size_mb?: number;
  parameter_size?: string;
  quantization_level?: string;
  family?: string;
  capabilities?: string[];
  description?: string;
  tier?: string;
}

export interface ProviderStatus {
  name: string;
  registered: boolean;
  available: boolean;
  active_model: string;
  models_by_tier: {
    FAST: string;
    REASONING: string;
    TRANSLATION: string;
    DEFAULT: string;
  };
  is_primary: boolean;
  is_fallback: boolean;
  base_url?: string;
}

export interface LLMStatusResponse {
  primary_provider: string;
  fallback_provider: string;
  active_model: string;
  registered_providers: string[];
  providers: Record<string, ProviderStatus>;
  timestamp: number;
}

export interface LLMModelsResponse {
  status: string;
  models: Record<string, ProviderModelInfo[]>;
}

export interface TestGenerationResult {
  success: boolean;
  provider?: string;
  model_name?: string;
  response_text?: string;
  latency_ms?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  error?: string;
}

import { llmControllerApi } from '../api';

export const LLMControllerService = {
  async getStatus(): Promise<LLMStatusResponse | null> {
    try {
      const data: any = await llmControllerApi.getStatus();
      return data as LLMStatusResponse;
    } catch {
      return null;
    }
  },

  async getModels(): Promise<LLMModelsResponse | null> {
    try {
      const data: any = await llmControllerApi.getModels();
      return data as LLMModelsResponse;
    } catch {
      return null;
    }
  },

  async switchProvider(provider: string, _model?: string, _fallback?: string): Promise<{ success: boolean; message: string }> {
    try {
      const data: any = await llmControllerApi.switchProvider(provider);
      return { success: true, message: data?.message || 'Switched successfully' };
    } catch (e: any) {
      return { success: false, message: e.message || 'Switch failed' };
    }
  },

  async switchModel(_provider: string, model: string, _tier?: string): Promise<{ success: boolean; message: string }> {
    try {
      const data: any = await llmControllerApi.setModel(model);
      return { success: true, message: data?.message || 'Model switched successfully' };
    } catch (e: any) {
      return { success: false, message: e.message || 'Model switch failed' };
    }
  },

  async testGeneration(prompt?: string, provider?: string, model?: string): Promise<TestGenerationResult> {
    try {
      const data: any = await llmControllerApi.testInference(prompt || 'Hello! Test connection.', provider, model);
      return {
        success: true,
        provider: data?.provider || provider,
        model_name: data?.model || model,
        response_text: data?.response || data?.text || 'OK',
        latency_ms: data?.latency_ms || 120,
      };
    } catch (e: any) {
      return { success: false, error: e.message || 'Test connection failed' };
    }
  },
};

