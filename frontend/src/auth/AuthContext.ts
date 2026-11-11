import { createContext, useContext } from "react";
import type { Session, User } from "@supabase/supabase-js";

export type AuthResult = { error: string | null; needsEmailConfirmation?: boolean };

export interface AuthContextValue {
  session: Session | null;
  user: User | null;
  /** True until the initial session has been restored from storage. */
  loading: boolean;
  signUp(email: string, password: string): Promise<AuthResult>;
  signIn(email: string, password: string): Promise<AuthResult>;
  signOut(): Promise<AuthResult>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
