/** Matches the backend error envelope: { error: { code, message, details } }. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown[];

  constructor(status: number, code: string, message: string, details: unknown[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export interface ApiRequestDeps {
  baseUrl: string;
  getToken: () => Promise<string | undefined>;
  fetchImpl?: typeof fetch;
}

/**
 * Core HTTP request execution with Bearer auth injection and standard error
 * envelope parsing. Shared by `apiFetch` and unit tests.
 */
export async function executeApiRequest<T>(
  path: string,
  init: RequestInit,
  deps: ApiRequestDeps,
): Promise<T> {
  const token = await deps.getToken();

  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body !== undefined && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const normalizedBase = deps.baseUrl.replace(/\/+$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const doFetch = deps.fetchImpl ?? fetch;

  const res = await doFetch(`${normalizedBase}${normalizedPath}`, {
    ...init,
    headers,
  });

  if (res.status === 204) return undefined as T;

  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const err = body?.error;
    throw new ApiError(
      res.status,
      err?.code ?? "HTTP_ERROR",
      err?.message ?? `Request failed with status ${res.status}`,
      Array.isArray(err?.details) ? err.details : [],
    );
  }
  return body as T;
}

