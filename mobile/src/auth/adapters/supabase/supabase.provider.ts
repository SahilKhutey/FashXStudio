import { supabase } from "../../../lib/supabase";
import { AuthError } from "../../auth.errors";
import type { AuthProvider } from "../../auth.provider";
import {
  maskEmail,
  type AuthOperationResult,
  type AuthSession,
  type LoginInput,
  type RecoveryCompleteInput,
  type RecoveryStartInput,
  type RegisterInput,
  type VerifyAccountInput,
} from "../../auth.types";

type ProviderErrorLike = {
  message?: string;
  status?: number;
  name?: string;
};

function mapSupabaseError(err: unknown): AuthError {
  if (err instanceof AuthError) {
    return err;
  }

  const e = (typeof err === "object" && err !== null ? err : {}) as ProviderErrorLike;
  const msg = (e.message ?? "").toLowerCase();
  const status = e.status ?? 0;

  if (msg.includes("network") || msg.includes("fetch failed") || msg.includes("failed to fetch")) {
    return new AuthError("NETWORK_UNAVAILABLE", "Network unavailable", true);
  }
  if (msg.includes("timeout") || e.name === "AbortError") {
    return new AuthError("REQUEST_TIMEOUT", "Authentication request timed out", true);
  }
  if (status === 429 || msg.includes("rate limit") || msg.includes("too many")) {
    return new AuthError("RATE_LIMITED", "Too many authentication requests", true);
  }
  if (msg.includes("email not confirmed") || msg.includes("not verified")) {
    return new AuthError("ACCOUNT_UNVERIFIED", "Account unverified", false);
  }
  if (msg.includes("expired") && (msg.includes("otp") || msg.includes("code") || msg.includes("token"))) {
    return new AuthError("VERIFICATION_CODE_EXPIRED", "Verification code expired", false);
  }
  if (msg.includes("otp") || msg.includes("token has expired or is invalid") || msg.includes("invalid code")) {
    return new AuthError("VERIFICATION_CODE_INVALID", "Invalid verification code", false);
  }
  if (msg.includes("password") && (msg.includes("weak") || msg.includes("length") || msg.includes("character"))) {
    return new AuthError("PASSWORD_POLICY_VIOLATION", "Weak password", false);
  }
  if (status >= 500) {
    return new AuthError("AUTH_SERVICE_UNAVAILABLE", "Auth service unavailable", true);
  }
  if (status === 400 || status === 401 || msg.includes("invalid login")) {
    return new AuthError("AUTHENTICATION_FAILED", "Authentication failed", false);
  }
  return new AuthError("UNKNOWN_ERROR", "Authentication error", false);
}

export class SupabaseAuthProvider implements AuthProvider {
  async register(input: RegisterInput): Promise<AuthOperationResult> {
    const email = input.email.trim().toLowerCase();
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password: input.password,
        options: {
          data: { full_name: input.name.trim() },
        },
      });
      if (error) {
        throw mapSupabaseError(error);
      }
      if (data.session) {
        return { status: "AUTHENTICATED" };
      }
      return {
        status: "VERIFICATION_REQUIRED",
        email,
        destination: maskEmail(email),
      };
    } catch (err) {
      throw mapSupabaseError(err);
    }
  }

  async login(input: LoginInput): Promise<AuthOperationResult> {
    const email = input.email.trim().toLowerCase();
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password: input.password,
      });
      if (error) {
        const mapped = mapSupabaseError(error);
        if (mapped.code === "ACCOUNT_UNVERIFIED") {
          return {
            status: "VERIFICATION_REQUIRED",
            email,
            destination: maskEmail(email),
          };
        }
        throw mapped;
      }
      if (!data.session) {
        return {
          status: "VERIFICATION_REQUIRED",
          email,
          destination: maskEmail(email),
        };
      }
      return { status: "AUTHENTICATED" };
    } catch (err) {
      throw mapSupabaseError(err);
    }
  }

  async confirmRegistration(input: VerifyAccountInput): Promise<void> {
    const email = input.email.trim().toLowerCase();
    try {
      const { error } = await supabase.auth.verifyOtp({
        email,
        token: input.code.trim(),
        type: "signup",
      });
      if (error) {
        throw mapSupabaseError(error);
      }
    } catch (err) {
      throw mapSupabaseError(err);
    }
  }

  async resendVerificationCode(email: string): Promise<void> {
    const normalized = email.trim().toLowerCase();
    try {
      const { error } = await supabase.auth.resend({
        type: "signup",
        email: normalized,
      });
      if (error) {
        throw mapSupabaseError(error);
      }
    } catch (err) {
      throw mapSupabaseError(err);
    }
  }

  async startRecovery(input: RecoveryStartInput): Promise<void> {
    const email = input.email.trim().toLowerCase();
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email);
      if (error) {
        throw mapSupabaseError(error);
      }
    } catch (err) {
      throw mapSupabaseError(err);
    }
  }

  async completeRecovery(input: RecoveryCompleteInput): Promise<void> {
    const email = input.email.trim().toLowerCase();
    try {
      const { error: verifyError } = await supabase.auth.verifyOtp({
        email,
        token: input.code.trim(),
        type: "recovery",
      });
      if (verifyError) {
        throw mapSupabaseError(verifyError);
      }
      const { error: updateError } = await supabase.auth.updateUser({
        password: input.newPassword,
      });
      if (updateError) {
        throw mapSupabaseError(updateError);
      }
    } catch (err) {
      throw mapSupabaseError(err);
    }
  }

  async getCurrentSession(): Promise<AuthSession | null> {
    try {
      const { data, error } = await supabase.auth.getSession();
      if (error || !data.session) {
        return null;
      }
      return {
        user: {
          subject: data.session.user.id,
          email: data.session.user.email,
        },
        accessToken: data.session.access_token,
        expiresAt: data.session.expires_at ?? 0,
      };
    } catch (err) {
      throw mapSupabaseError(err);
    }
  }

  async getAccessToken(): Promise<string | null> {
    const session = await this.getCurrentSession();
    return session?.accessToken ?? null;
  }

  async refreshSession(): Promise<AuthSession> {
    try {
      const { data, error } = await supabase.auth.refreshSession();
      if (error || !data.session) {
        throw new AuthError("SESSION_EXPIRED", "Session expired", false);
      }
      return {
        user: {
          subject: data.session.user.id,
          email: data.session.user.email,
        },
        accessToken: data.session.access_token,
        expiresAt: data.session.expires_at ?? 0,
      };
    } catch (err) {
      throw mapSupabaseError(err);
    }
  }

  async logout(): Promise<void> {
    await supabase.auth.signOut();
  }
}

export const supabaseAuthProvider = new SupabaseAuthProvider();
