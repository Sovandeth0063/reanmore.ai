import { request } from './client';
import { SystemHealthResponse, SystemHealthResponseSchema } from './schemas';

/**
 * System Health & Microservice Monitoring API Client
 */
export const healthApi = {
  /**
   * Get coarse health status (safe for student view).
   */
  async getHealth(): Promise<{ status: 'ok' | 'degraded' | 'unhealthy' }> {
    try {
      const raw = await request<{ status: string }>('/health', {
        method: 'GET',
        timeoutMs: 5_000,
      });
      return { status: (raw.status === 'ok' || raw.status === 'healthy') ? 'ok' : 'degraded' };
    } catch {
      return { status: 'unhealthy' };
    }
  },

  /**
   * Get detailed microservice status (requires in-memory admin token).
   */
  async getDetailedServices(adminToken: string): Promise<SystemHealthResponse> {
    const raw = await request<unknown>('/services', {
      method: 'GET',
      token: adminToken,
      timeoutMs: 8_000,
    });

    const parsed = SystemHealthResponseSchema.safeParse(raw);
    return parsed.success ? parsed.data : { status: 'degraded' };
  },
};
