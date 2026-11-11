import { supabase } from "./supabaseClient";
import { ApiError, executeApiRequest } from "./apiClientCore";

// All NEXORA data access goes through FastAPI. Never query NEXORA tables from the browser.

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);

export { ApiError };

/**
 * Call a FastAPI endpoint with the current Supabase access token as a Bearer token.
 * The token is read at call time, so a refreshed token is always used.
 */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  return executeApiRequest<T>(path, init, {
    baseUrl: API_BASE_URL,
    getToken: async () => {
      const { data } = await supabase.auth.getSession();
      return data.session?.access_token;
    },
  });
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
