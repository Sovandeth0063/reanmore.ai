/**
 * client.ts
 * Enterprise-grade HTTP Client for ReanMore Frontend.
 *
 * Capabilities:
 * - Machine-code-first ApiError dispatching
 * - Centralized XHR upload helper (xhrUpload) with real onProgress
 * - Centralized fetch keepalive helper (sendKeepalive) for exit delta beaconing
 * - AbortController registry for query/read cancellation (mutations are non-abortable)
 * - Header injection (X-Request-ID, X-Session-ID, X-API-Version: 1)
 * - Exponential backoff retry for GETs and idempotent POSTs honoring Retry-After
 */

export type ApiErrorCode =
  | 'NETWORK_ERROR'
  | 'TIMEOUT'
  | 'ABORTED'
  | 'RATE_LIMITED'           // 429 (Token bucket exhausted)
  | 'SERVER_BUSY'             // 503 (High traffic queue full)
  | 'PIN_LOCKED'              // 429 (Anti-brute force delay countdown)
  | 'CONSENT_REQUIRED'        // 403 (Cloud sync or research linking not consented)
  | 'TIER2_LOCKED'            // 423 (Device locked in crisis counselor mode)
  | 'DEVICE_REVOKED'          // 401 (Device token invalidated by admin; prompt then wipe)
  | 'ENROLLMENT_INVALID'      // 403 (Invalid or expired classroom enrollment code)
  | 'REQUEST_IN_PROGRESS'     // 409 (Duplicate key in-flight; retry shortly)
  | 'VERSION_CONFLICT'        // 409 (CAS sync mismatch)
  | 'CLIENT_OUTDATED'         // 426 (X-API-Version below min_supported_version)
  | 'SESSION_EXPIRED'         // 404 (Session expired/not found)
  | 'UNAUTHORIZED'            // 401 (Invalid/expired parent or admin token)
  | 'FORBIDDEN'               // 403 (Insufficient role or PIN locked)
  | 'PAYLOAD_TOO_LARGE'       // 413 (Upload exceeds 10MB)
  | 'UNSUPPORTED_MEDIA'       // 415 (Invalid MIME/magic bytes)
  | 'VALIDATION_FAILED'       // 422 (Pydantic validation error)
  | 'UNEXPECTED_RESPONSE'     // Non-object payload from server
  | 'SERVER_UNAVAILABLE';     // 502/504

export interface ApiError {
  isApiError: true;
  status: number;
  code: ApiErrorCode;
  message: string;
  retryAfterSeconds?: number | undefined;
  requestId?: string | undefined;
  fieldErrors?: Array<{ field: string; message: string }> | undefined;
  i18nKey: string;
}

export function isApiError(err: unknown): err is ApiError {
  return typeof err === 'object' && err !== null && (err as any).isApiError === true;
}

export interface RequestOptions extends RequestInit {
  timeoutMs?: number | undefined;
  idempotencyKey?: string | undefined;
  abortKey?: string | undefined;
  maxRetries?: number | undefined;
  token?: string | undefined; // In-memory Bearer token (Admin or Parent JWT)
  sessionId?: string | undefined;
  language?: string | undefined;
  grade?: number | undefined;
}

export interface XhrUploadOptions {
  timeoutMs?: number | undefined;
  token?: string | undefined;
  sessionId?: string | undefined;
  onProgress?: ((percent: number) => void) | undefined;
  abortSignal?: AbortSignal | undefined;
}

const DEFAULT_BASE_URL = '/api';
const CURRENT_API_VERSION = '1';

// Keyed in-flight abort controllers
const abortRegistry = new Map<string, AbortController>();

// In-memory token storage (Admin or Parent session)
let inMemoryAuthToken: string | null = null;
let currentActiveSessionId: string | null = null;

export function setClientAuthToken(token: string | null) {
  inMemoryAuthToken = token;
}

export function setClientActiveSessionId(sessionId: string | null) {
  currentActiveSessionId = sessionId;
}

function generateRequestId(): string {
  return 'req_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 9);
}

function mapStatusToCode(status: number): ApiErrorCode {
  switch (status) {
    case 401: return 'UNAUTHORIZED';
    case 403: return 'FORBIDDEN';
    case 404: return 'SESSION_EXPIRED';
    case 409: return 'VERSION_CONFLICT';
    case 413: return 'PAYLOAD_TOO_LARGE';
    case 415: return 'UNSUPPORTED_MEDIA';
    case 422: return 'VALIDATION_FAILED';
    case 423: return 'TIER2_LOCKED';
    case 426: return 'CLIENT_OUTDATED';
    case 429: return 'RATE_LIMITED';
    case 503: return 'SERVER_BUSY';
    case 502:
    case 504: return 'SERVER_UNAVAILABLE';
    default: return status >= 500 ? 'SERVER_UNAVAILABLE' : 'NETWORK_ERROR';
  }
}

function mapCodeToI18nKey(code: ApiErrorCode): string {
  switch (code) {
    case 'RATE_LIMITED': return 'errors.rate_limited';
    case 'SERVER_BUSY': return 'errors.server_busy';
    case 'PIN_LOCKED': return 'errors.pin_locked';
    case 'CONSENT_REQUIRED': return 'errors.consent_required';
    case 'TIER2_LOCKED': return 'errors.tier2_locked';
    case 'DEVICE_REVOKED': return 'errors.device_revoked';
    case 'ENROLLMENT_INVALID': return 'errors.enrollment_invalid';
    case 'CLIENT_OUTDATED': return 'errors.client_outdated';
    case 'REQUEST_IN_PROGRESS': return 'errors.request_in_progress';
    case 'VERSION_CONFLICT': return 'errors.version_conflict';
    case 'SESSION_EXPIRED': return 'errors.session_expired';
    case 'PAYLOAD_TOO_LARGE': return 'errors.payload_too_large';
    case 'UNSUPPORTED_MEDIA': return 'errors.unsupported_media';
    case 'SERVER_UNAVAILABLE': return 'errors.server_unavailable';
    case 'TIMEOUT': return 'errors.timeout';
    default: return 'errors.network_offline';
  }
}

async function parseErrorResponse(res: Response, requestId: string): Promise<ApiError> {
  let bodyCode: string | undefined;
  let bodyMsg: string = res.statusText || 'Request failed';
  let fieldErrors: Array<{ field: string; message: string }> | undefined;
  let retryAfterSeconds: number | undefined;

  const retryHeader = res.headers.get('Retry-After');
  if (retryHeader) {
    const sec = parseInt(retryHeader, 10);
    if (!isNaN(sec) && sec > 0) retryAfterSeconds = sec;
  }

  try {
    const json = await res.json();
    if (json && typeof json === 'object') {
      if (typeof json.code === 'string') bodyCode = json.code;
      if (typeof json.detail === 'string') bodyMsg = json.detail;
      else if (typeof json.message === 'string') bodyMsg = json.message;
      else if (typeof json.error === 'string') bodyMsg = json.error;
      else if (Array.isArray(json.detail)) {
        // FastAPI 422 validation array
        bodyCode = 'VALIDATION_FAILED';
        const errs = json.detail.map((d: any) => ({
          field: Array.isArray(d.loc) ? d.loc.join('.') : 'body',
          message: d.msg || 'Invalid field value',
        }));
        fieldErrors = errs;
        bodyMsg = errs.map((f: { field: string; message: string }) => `${f.field}: ${f.message}`).join('; ');
      }
    }
  } catch {
    // Body was not JSON
  }

  // Machine-code-first mapping
  const code: ApiErrorCode = (bodyCode as ApiErrorCode) || mapStatusToCode(res.status);

  return {
    isApiError: true,
    status: res.status,
    code,
    message: bodyMsg,
    ...(retryAfterSeconds ? { retryAfterSeconds } : {}),
    requestId,
    ...(fieldErrors ? { fieldErrors } : {}),
    i18nKey: mapCodeToI18nKey(code),
  };
}

/**
 * Primary HTTP request client.
 */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const {
    timeoutMs = 40_000,
    idempotencyKey,
    abortKey,
    maxRetries = 0,
    token = inMemoryAuthToken,
    sessionId = currentActiveSessionId,
    headers = {},
    ...fetchOpts
  } = options;

  const requestId = generateRequestId();
  const url = path.startsWith('http') ? path : `${DEFAULT_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;

  // Abort previous in-flight request if abortKey is specified
  if (abortKey) {
    const prev = abortRegistry.get(abortKey);
    if (prev) {
      prev.abort();
      abortRegistry.delete(abortKey);
    }
  }

  const controller = new AbortController();
  if (abortKey) {
    abortRegistry.set(abortKey, controller);
  }

  const mergedHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Request-ID': requestId,
    'X-API-Version': CURRENT_API_VERSION,
    'X-Request-Budget-Ms': Math.max(0, timeoutMs - 2000).toString(),
    ...(sessionId ? { 'X-Session-ID': sessionId } : {}),
    ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}),
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(headers as Record<string, string>),
  };

  let attempts = 0;
  const isIdempotentMethod = fetchOpts.method === 'GET' || fetchOpts.method === 'HEAD' || Boolean(idempotencyKey);
  const effectiveMaxRetries = isIdempotentMethod ? maxRetries : 0;

  while (true) {
    attempts++;
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const res = await fetch(url, {
        ...fetchOpts,
        headers: mergedHeaders,
        signal: controller.signal,
      });

      clearTimeout(timer);
      if (abortKey) abortRegistry.delete(abortKey);

      if (!res.ok) {
        const apiErr = await parseErrorResponse(res, requestId);

        // Handle 409 REQUEST_IN_PROGRESS retry backoff
        if (apiErr.code === 'REQUEST_IN_PROGRESS' && attempts <= 3) {
          const waitMs = (apiErr.retryAfterSeconds || 1) * 1000;
          await new Promise(resolve => setTimeout(resolve, waitMs));
          continue;
        }

        // Retryable 429 or 503 with backoff on idempotent requests
        if ((apiErr.status === 429 || apiErr.status === 503) && attempts <= effectiveMaxRetries) {
          const waitMs = (apiErr.retryAfterSeconds || Math.pow(2, attempts)) * 1000;
          await new Promise(resolve => setTimeout(resolve, waitMs));
          continue;
        }

        throw apiErr;
      }

      // Successful response
      const json = await res.json();
      return json as T;

    } catch (err: any) {
      clearTimeout(timer);
      if (abortKey) abortRegistry.delete(abortKey);

      if (isApiError(err)) {
        throw err;
      }

      if (err.name === 'AbortError') {
        throw {
          isApiError: true,
          status: 0,
          code: 'TIMEOUT',
          message: `Request timed out after ${timeoutMs / 1000}s`,
          requestId,
          i18nKey: 'errors.timeout',
        } as ApiError;
      }

      // Network disconnect / offline
      if (attempts <= effectiveMaxRetries) {
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempts)));
        continue;
      }

      throw {
        isApiError: true,
        status: 0,
        code: 'NETWORK_ERROR',
        message: err.message || 'Network connection failed',
        requestId,
        i18nKey: 'errors.network_offline',
      } as ApiError;
    }
  }
}

/**
 * XHR Upload Helper with real onProgress tracking.
 * Shares full interceptor parity with standard request client.
 */
export function xhrUpload<T>(
  path: string,
  formData: FormData,
  options: XhrUploadOptions = {}
): Promise<T> {
  const {
    timeoutMs = 90_000,
    token = inMemoryAuthToken,
    sessionId = currentActiveSessionId,
    onProgress,
    abortSignal,
  } = options;

  const requestId = generateRequestId();
  const url = path.startsWith('http') ? path : `${DEFAULT_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.timeout = timeoutMs;

    // Injected headers
    xhr.setRequestHeader('Accept', 'application/json');
    xhr.setRequestHeader('X-Request-ID', requestId);
    xhr.setRequestHeader('X-API-Version', CURRENT_API_VERSION);
    xhr.setRequestHeader('X-Request-Budget-Ms', Math.max(0, timeoutMs - 2000).toString());
    if (sessionId) xhr.setRequestHeader('X-Session-ID', sessionId);
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);

    if (onProgress && xhr.upload) {
      xhr.upload.onprogress = (e: ProgressEvent) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100);
          onProgress(percent);
        }
      };
    }

    if (abortSignal) {
      abortSignal.addEventListener('abort', () => xhr.abort());
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const json = JSON.parse(xhr.responseText);
          resolve(json as T);
        } catch {
          reject({
            isApiError: true,
            status: xhr.status,
            code: 'UNEXPECTED_RESPONSE',
            message: 'Invalid JSON from upload service',
            requestId,
            i18nKey: 'errors.unexpected_response',
          } as ApiError);
        }
      } else {
        let code: ApiErrorCode = mapStatusToCode(xhr.status);
        let msg = xhr.statusText || 'Upload failed';
        try {
          const json = JSON.parse(xhr.responseText);
          if (json.code) code = json.code;
          if (json.detail) msg = json.detail;
        } catch {
          // Non JSON
        }
        reject({
          isApiError: true,
          status: xhr.status,
          code,
          message: msg,
          requestId,
          i18nKey: mapCodeToI18nKey(code),
        } as ApiError);
      }
    };

    xhr.onerror = () => {
      reject({
        isApiError: true,
        status: 0,
        code: 'NETWORK_ERROR',
        message: 'Upload network connection failed',
        requestId,
        i18nKey: 'errors.network_offline',
      } as ApiError);
    };

    xhr.ontimeout = () => {
      reject({
        isApiError: true,
        status: 0,
        code: 'TIMEOUT',
        message: `Upload timed out after ${timeoutMs / 1000}s`,
        requestId,
        i18nKey: 'errors.timeout',
      } as ApiError);
    };

    xhr.onabort = () => {
      reject({
        isApiError: true,
        status: 0,
        code: 'ABORTED',
        message: 'Upload aborted by user',
        requestId,
        i18nKey: 'errors.aborted',
      } as ApiError);
    };

    xhr.send(formData);
  });
}

/**
 * SendKeepalive helper for pagehide / visibilitychange exit delta beaconing.
 */
export function sendKeepalive(path: string, payload: unknown, sessionId?: string): boolean {
  const url = path.startsWith('http') ? path : `${DEFAULT_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
  const targetSession = sessionId || currentActiveSessionId;

  try {
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': generateRequestId(),
        'X-API-Version': CURRENT_API_VERSION,
        ...(targetSession ? { 'X-Session-ID': targetSession } : {}),
      },
      body: JSON.stringify(payload),
      keepalive: true,
    }).catch(() => {});
    return true;
  } catch {
    return false;
  }
}
