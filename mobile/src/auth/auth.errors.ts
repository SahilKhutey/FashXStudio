export type AuthErrorCode =
  | "NETWORK_UNAVAILABLE"
  | "REQUEST_TIMEOUT"
  | "AUTHENTICATION_FAILED"
  | "ACCOUNT_UNVERIFIED"
  | "VERIFICATION_CODE_INVALID"
  | "VERIFICATION_CODE_EXPIRED"
  | "PASSWORD_POLICY_VIOLATION"
  | "RATE_LIMITED"
  | "AUTH_SERVICE_UNAVAILABLE"
  | "SESSION_EXPIRED"
  | "UNKNOWN_ERROR";

export class AuthError extends Error {
  override readonly name = "AuthError";

  constructor(
    public readonly code: AuthErrorCode,
    message: string,
    public readonly retryable: boolean,
  ) {
    super(message);
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

const USER_MESSAGES: Record<AuthErrorCode, string> = {
  NETWORK_UNAVAILABLE: "Check your internet connection and try again.",
  REQUEST_TIMEOUT: "The request took too long. Please try again.",
  AUTHENTICATION_FAILED: "Unable to sign in with those details.",
  ACCOUNT_UNVERIFIED: "Please verify your account to continue.",
  VERIFICATION_CODE_INVALID: "The verification code is incorrect.",
  VERIFICATION_CODE_EXPIRED: "Your code has expired. Request a new one.",
  PASSWORD_POLICY_VIOLATION:
    "Password does not meet the minimum security requirements.",
  RATE_LIMITED: "Too many attempts. Please wait before trying again.",
  AUTH_SERVICE_UNAVAILABLE: "Authentication is temporarily unavailable.",
  SESSION_EXPIRED: "Your session has expired. Please sign in again.",
  UNKNOWN_ERROR: "Something went wrong. Please try again.",
};

export function toAuthUserMessage(error: unknown): string {
  if (error instanceof AuthError) {
    return USER_MESSAGES[error.code];
  }
  return USER_MESSAGES.UNKNOWN_ERROR;
}
