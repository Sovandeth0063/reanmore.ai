import { request, sendKeepalive } from './client';
import { TelemetryEvent } from './schemas';

let isTelemetryConsentGranted = false;
const eventQueue: TelemetryEvent[] = [];
let flushTimeout: any = null;

export function setTelemetryConsent(granted: boolean) {
  isTelemetryConsentGranted = granted;
}

export function getTelemetryConsent(): boolean {
  return isTelemetryConsentGranted;
}

/**
 * Generate a deterministic one-way derived analytics ID from session ID
 * so the raw session_id bearer credential is never transmitted in telemetry.
 */
export function deriveAnalyticsId(sessionId: string): string {
  let hash = 0;
  for (let i = 0; i < sessionId.length; i++) {
    hash = (hash << 5) - hash + sessionId.charCodeAt(i);
    hash |= 0;
  }
  return 'ana_' + Math.abs(hash).toString(36);
}

/**
 * Telemetry and Learning Study Analytics API Client
 */
export const telemetryApi = {
  /**
   * Log an allowlisted telemetry event.
   * Only transmits metadata if parent/school consent is granted.
   */
  logEvent(event: Omit<TelemetryEvent, 'analytics_id'> & { sessionId: string }) {
    if (!isTelemetryConsentGranted) return;

    const fullEvent: TelemetryEvent = {
      event_type: event.event_type,
      analytics_id: deriveAnalyticsId(event.sessionId),
      ...(typeof event.step_index === 'number' ? { step_index: event.step_index } : {}),
      ...(typeof event.duration_ms === 'number' ? { duration_ms: event.duration_ms } : {}),
      ...(event.metadata ? { metadata: event.metadata } : {}),
    };

    eventQueue.push(fullEvent);

    if (!flushTimeout) {
      flushTimeout = setTimeout(() => {
        telemetryApi.flush();
      }, 5_000);
    }
  },

  /**
   * Flush queued events to backend.
   */
  async flush(): Promise<void> {
    if (flushTimeout) {
      clearTimeout(flushTimeout);
      flushTimeout = null;
    }

    if (eventQueue.length === 0 || !isTelemetryConsentGranted) return;
    const eventsToSend = eventQueue.splice(0, eventQueue.length);

    try {
      await request('/telemetry/event', {
        method: 'POST',
        body: JSON.stringify({ events: eventsToSend }),
        timeoutMs: 8_000,
      });
    } catch {
      // Non-blocking for telemetry
    }
  },

  /**
   * Flush remaining events on page exit via sendKeepalive.
   */
  flushOnExit(): boolean {
    if (eventQueue.length === 0 || !isTelemetryConsentGranted) return false;
    const eventsToSend = eventQueue.splice(0, eventQueue.length);
    return sendKeepalive('/telemetry/event', { events: eventsToSend });
  },
};
