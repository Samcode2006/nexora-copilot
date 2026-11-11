import { supabase } from "./supabaseClient";

// All NEXORA data access goes through FastAPI. Never query NEXORA tables from the browser.

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);

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

/**
 * Call a FastAPI endpoint with the current Supabase access token as a Bearer token.
 * The token is read at call time, so a refreshed token is always used.
 */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;

  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body !== undefined && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`, {
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

export type Profile = {
  id: string;
  email: string | null;
  full_name: string | null;
  batch_year: number | null;
  cgpa: string | null;
  backlogs: number | null;
  branch: string | null;
  created_at: string;
  updated_at: string;
};

export const getMyProfile = () => apiFetch<Profile>("/api/v1/profile/me");
