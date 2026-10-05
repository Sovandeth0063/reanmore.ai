import { request, sendKeepalive } from './client';
import {
  SessionSyncPayload,
  SessionDeltaPayload,
  UnsyncedMessage,
} from './schemas';

// Serialized queue for CAS session synchronization
let syncQueuePromise = Promise.resolve<any>(null);
let localExpectedVersion = 0;

export function updateLocalSessionVersion(version?: number) {
  if (typeof version === 'number' && version >= localExpectedVersion) {
    localExpectedVersion = version;
  }
}

export function getLocalSessionVersion(): number {
  return localExpectedVersion;
}

/**
 * Session Synchronization & Persistence API Client
 */
export const sessionApi = {
  /**
   * Start a new session and receive a 128-bit unguessable session_id.
   */
  async startSession(payload?: {
    student_name?: string;
    grade?: number;
    subject?: string;
    language?: string;
  }): Promise<{ session_id: string; version: number }> {
    const res = await request<{ session_id: string; version?: number }>('/session/start', {
      method: 'POST',
      body: JSON.stringify(payload || {}),
      timeoutMs: 10_000,
    });
    updateLocalSessionVersion(res.version || 1);
    return { session_id: res.session_id, version: res.version || 1 };
  },

  /**
   * Synchronize active session state to Redis & PostgreSQL via a serialized CAS queue.
   */
  syncSession(payload: SessionSyncPayload): Promise<{ status: string; version: number }> {
    syncQueuePromise = syncQueuePromise.catch(() => null).then(async () => {
      const payloadWithVersion = {
        ...payload,
        expected_version: localExpectedVersion,
      };

      try {
        const res = await request<{ status: string; version?: number }>('/session/sync', {
          method: 'POST',
          body: JSON.stringify(payloadWithVersion),
          timeoutMs: 15_000,
          idempotencyKey: `sync_${payload.session_id}_${localExpectedVersion}`,
        });
        updateLocalSessionVersion(res.version);
        return { status: res.status || 'success', version: localExpectedVersion };
      } catch (err: any) {
        if (err?.code === 'VERSION_CONFLICT') {
          // Version conflict (409): Pull authoritative session from backend
          const authoritative = await sessionApi.getSession(payload.session_id);
          if (authoritative?.version) {
            updateLocalSessionVersion(authoritative.version);
          }
        }
        throw err;
      }
    });

    return syncQueuePromise;
  },

  /**
   * Send unacknowledged pending delta on pagehide / visibilitychange using fetch keepalive.
   * Sends up to 10 pending messages; excludes step_index (server authoritative).
   */
  flushSessionDeltaBeacon(
    sessionId: string,
    pendingMessages: UnsyncedMessage[],
    currentProblemId?: string
  ): boolean {
    let cappedMessages = pendingMessages.slice(-10);
    const MAX_BEACON_BYTES = 48 * 1024;
    while (cappedMessages.length > 1) {
      const payloadString = JSON.stringify(cappedMessages);
      if (new Blob([payloadString]).size <= MAX_BEACON_BYTES) {
        break;
      }
      cappedMessages = cappedMessages.slice(1);
    }

    const deltaPayload: SessionDeltaPayload = {
      session_id: sessionId,
      expected_version: localExpectedVersion,
      messages: cappedMessages,
      current_problem_id: currentProblemId,
    };

    return sendKeepalive('/session/sync-delta', deltaPayload, sessionId);
  },

  /**
   * Fetch active session state by ID.
   */
  async getSession(sessionId: string): Promise<any> {
    const res = await request<any>(`/session/${sessionId}`, {
      method: 'GET',
      timeoutMs: 10_000,
    });
    if (res?.version) {
      updateLocalSessionVersion(res.version);
    }
    return res;
  },

  /**
   * List sessions owned by the active student token.
   */
  async getMySessions(): Promise<any[]> {
    return request<any[]>('/sessions', {
      method: 'GET',
      timeoutMs: 10_000,
    });
  },

  /**
   * Explicitly close an active session (marks completed, keeps data for parent report).
   */
  async closeSession(sessionId: string): Promise<{ status: string }> {
    return request<{ status: string }>('/session/close', {
      method: 'POST',
      body: JSON.stringify({ session_id: sessionId }),
      timeoutMs: 10_000,
    });
  },

  /**
   * Permanently purge a session from database.
   */
  async deleteSession(sessionId: string): Promise<{ status: string }> {
    return request<{ status: string }>(`/session/${sessionId}`, {
      method: 'DELETE',
      timeoutMs: 10_000,
    });
  },
};
