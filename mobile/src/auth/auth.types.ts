export type AuthStateStatus =
  | "INITIALIZING"
  | "UNAUTHENTICATED"
  | "REGISTERING"
  | "VERIFICATION_REQUIRED"
  | "AUTHENTICATING"
  | "AUTHENTICATED"
  | "REFRESHING"
  | "RECOVERY_PENDING"
  | "RESETTING_PASSWORD"
  | "NETWORK_ERROR"
  | "SESSION_EXPIRED"
  | "LOGGING_OUT";

export type RegisterInput = {
  name: string;
  email: string;
  password: string;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type VerifyAccountInput = {
  email: string;
  code: string;
};

export type RecoveryStartInput = {
  email: string;
};

export type RecoveryCompleteInput = {
  email: string;
  code: string;
  newPassword: string;
};

export type AuthOperationResult =
  | { status: "AUTHENTICATED" }
  | { status: "VERIFICATION_REQUIRED"; email: string; destination: string }
  | { status: "ADDITIONAL_CHALLENGE_REQUIRED"; challengeId: string };

export type SessionUser = {
  subject: string;
  email?: string;
};

export type AuthSession = {
  user: SessionUser;
  accessToken: string;
  expiresAt: number;
};

export function maskEmail(email: string): string {
  const trimmed = email.trim().toLowerCase();
  const atIdx = trimmed.indexOf("@");
  if (atIdx <= 1) {
    return trimmed ? `***${trimmed.slice(atIdx)}` : "***";
  }
  const local = trimmed.slice(0, atIdx);
  const domain = trimmed.slice(atIdx);
  return `${local[0]}***${local[local.length - 1]}${domain}`;
}
