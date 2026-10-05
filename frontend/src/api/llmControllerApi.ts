import { request } from './client';
import { LLMStatusResponse, LLMStatusResponseSchema } from './schemas';

/**
 * LLM Engine Controller API Client (Admin Token Gated)
 */
export const llmControllerApi = {
  /**
   * Get active provider status, temperature, and metrics.
   */
  async getStatus(adminToken?: string): Promise<LLMStatusResponse> {
    const raw = await request<unknown>('/llm/status', {
      method: 'GET',
      token: adminToken,
      timeoutMs: 8_000,
    });

    const parsed = LLMStatusResponseSchema.safeParse(raw);
    if (parsed.success) return parsed.data;

    return {
      active_provider: 'gemini',
      active_model: 'gemini-2.5-flash',
      active_tier: 'production',
      temperature: 0.2,
      providers_available: ['gemini', 'openai', 'ollama', 'mock'],
    };
  },

  /**
   * Get available models and tiers.
   */
  async getModels(adminToken?: string): Promise<any[]> {
    return request<any[]>('/llm/models', {
      method: 'GET',
      token: adminToken,
      timeoutMs: 8_000,
    });
  },

  /**
   * Switch active LLM provider.
   */
  async switchProvider(provider: string, adminToken?: string): Promise<any> {
    return request<any>('/llm/switch', {
      method: 'POST',
      body: JSON.stringify({ provider }),
      token: adminToken,
      timeoutMs: 10_000,
    });
  },

  /**
   * Set specific model ID.
   */
  async setModel(model: string, adminToken?: string): Promise<any> {
    return request<any>('/llm/model', {
      method: 'POST',
      body: JSON.stringify({ model }),
      token: adminToken,
      timeoutMs: 10_000,
    });
  },

  /**
   * Test inference on a specific model.
   */
  async testInference(
    prompt: string,
    provider?: string,
    model?: string,
    adminToken?: string
  ): Promise<any> {
    return request<any>('/llm/test', {
      method: 'POST',
      body: JSON.stringify({ prompt, provider, model }),
      token: adminToken,
      timeoutMs: 25_000,
    });
  },
};
